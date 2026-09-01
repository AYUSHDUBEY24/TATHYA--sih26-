"""
Reusable FastAPI dependencies for authentication, RBAC and case-level access.

This module is the SINGLE place where authorization decisions live, so every
endpoint enforces the same backend rules (docs/security.md).
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.case import Case
from app.models.case_member import CaseMember
from app.models.document import Document
from app.models.user import User
from app.services.audit_service import AuditAction, AuditResult, log_audit

# auto_error=False so we can return a clean 401 (not FastAPI's default 403)
# when the Authorization header is missing.
bearer_scheme = HTTPBearer(auto_error=False)

_UNAUTHENTICATED = dict(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from the Bearer JWT, or raise 401."""
    if credentials is None:
        raise HTTPException(**_UNAUTHENTICATED)

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(str(payload.get("sub")))
    except (InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        # Token valid but user deleted/deactivated — treat as unauthenticated.
        raise HTTPException(**_UNAUTHENTICATED)
    return user


def require_roles(*allowed_roles: str):
    """
    Dependency factory: endpoint is restricted to the given role names.

    Usage::

        @router.get("/admin-only")
        def admin_only(user: User = Depends(require_roles("ADMIN"))):
            ...
    """

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this operation",
            )
        return current_user

    return dependency


# --------------------------------------------------------------------------
# Case-level authorization (Phase 3) — reused by all case endpoints.
# --------------------------------------------------------------------------


def user_can_access_case(user: User, case: Case, db: Session) -> bool:
    """
    Visibility rule:
      * ADMIN  → all cases
      * others → assigned investigating officer OR case membership
    """
    if user.role.name == "ADMIN":
        return True
    if case.assigned_io_id == user.id:
        return True
    return (
        db.scalar(
            select(CaseMember.id).where(
                CaseMember.case_id == case.id,
                CaseMember.user_id == user.id,
            )
        )
        is not None
    )


def user_can_manage_case(user: User, case: Case) -> bool:
    """
    Management rule (edit case / manage members):
      * ADMIN, or
      * the case creator, or
      * the assigned investigating officer
    """
    return (
        user.role.name == "ADMIN"
        or case.created_by == user.id
        or case.assigned_io_id == user.id
    )


def get_authorized_case(
    case_id: uuid.UUID, current_user: User, db: Session
) -> Case:
    """
    Return the case if the current user may access it; raise 404 otherwise.

    404 (rather than 403) is intentional for unauthorized access: it does not
    reveal whether a case with the given ID exists.
    """
    case = db.get(Case, case_id)
    if case is None or not user_can_access_case(current_user, case, db):
        # Audit the rejected access attempt (safe: ids only, no contents).
        log_audit(
            db,
            AuditAction.ACCESS_DENIED,
            actor=current_user,
            entity_type="CASE",
            entity_id=case.id if case else None,
            case_id=case.id if case else None,
            result=AuditResult.DENIED,
            commit=True,  # denial path — nothing else is committed
        )
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")
    return case


# --------------------------------------------------------------------------
# Document-level authorization (Phase 4) — checked against CASE access.
# --------------------------------------------------------------------------


def get_authorized_document(
    document_id: uuid.UUID, current_user: User, db: Session
) -> Document:
    """
    Return the (ACTIVE) document if the current user may access it, else 404.

    Access is derived from the document's CASE (membership / assigned IO /
    ADMIN) — changing the document ID in the URL cannot bypass case-level
    authorization. Soft-deleted documents are invisible to everyone.
    """
    document = db.get(Document, document_id)
    if (
        document is None
        or document.status != "ACTIVE"
    ):
        log_audit(
            db,
            AuditAction.ACCESS_DENIED,
            actor=current_user,
            entity_type="DOCUMENT",
            entity_id=document.id if document else None,
            case_id=document.case_id if document else None,
            result=AuditResult.DENIED,
            commit=True,
        )
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    case = db.get(Case, document.case_id)
    if case is None or not user_can_access_case(current_user, case, db):
        log_audit(
            db,
            AuditAction.ACCESS_DENIED,
            actor=current_user,
            entity_type="DOCUMENT",
            entity_id=document.id,
            case_id=document.case_id,
            result=AuditResult.DENIED,
            commit=True,
        )
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return document


def user_can_delete_document(user: User, document: Document, db: Session) -> bool:
    """
    Delete (soft) rule: ADMIN, case manager (creator / assigned IO), or the
    original uploader.
    """
    if user.role.name == "ADMIN":
        return True
    if document.uploaded_by == user.id:
        return True
    case = db.get(Case, document.case_id)
    return case is not None and user_can_manage_case(user, case)
