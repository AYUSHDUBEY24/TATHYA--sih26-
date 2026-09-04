"""
Centralized audit service (Phase 6).

All audit rows are written through :func:`log_audit` so business code never
builds audit rows manually. Rules:

* SUCCESS-path rows join the operation's own transaction (atomic — the audit
  row is persisted by the caller's normal ``db.commit()``).
* FAILURE/DENIED rows (where nothing else is committed) use ``commit=True``.
* An audit write failure is logged as a warning and never breaks the main
  operation (graceful degradation, observable for debugging).
* NEVER pass passwords, tokens/secrets, or file contents as metadata.
"""

import logging
import uuid
from enum import Enum

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User

logger = logging.getLogger("sih26190.audit")


class AuditAction(str, Enum):
    LOGIN = "LOGIN"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    CASE_CREATED = "CASE_CREATED"
    CASE_UPDATED = "CASE_UPDATED"
    CASE_DELETED = "CASE_DELETED"
    CASE_MEMBER_ADDED = "CASE_MEMBER_ADDED"
    CASE_MEMBER_REMOVED = "CASE_MEMBER_REMOVED"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    DOCUMENT_VIEWED = "DOCUMENT_VIEWED"
    DOCUMENT_DOWNLOADED = "DOCUMENT_DOWNLOADED"
    DOCUMENT_DELETED = "DOCUMENT_DELETED"
    DOCUMENT_VERSION_CREATED = "DOCUMENT_VERSION_CREATED"
    INTEGRITY_VERIFIED = "INTEGRITY_VERIFIED"
    INTEGRITY_FAILED = "INTEGRITY_FAILED"
    # Reserved for document-level permission changes (Phase 4+ ACL work).
    PERMISSION_CHANGED = "PERMISSION_CHANGED"
    # Authorization rejections (kept distinct from operation failures).
    ACCESS_DENIED = "ACCESS_DENIED"
    # Blockchain anchoring (Phase 7).
    BLOCKCHAIN_REGISTERED = "BLOCKCHAIN_REGISTERED"
    BLOCKCHAIN_REGISTRATION_FAILED = "BLOCKCHAIN_REGISTRATION_FAILED"
    BLOCKCHAIN_VERIFIED = "BLOCKCHAIN_VERIFIED"
    BLOCKCHAIN_MISMATCH = "BLOCKCHAIN_MISMATCH"
    # Text extraction + search (Phase 8).
    DOCUMENT_TEXT_EXTRACTED = "DOCUMENT_TEXT_EXTRACTED"
    DOCUMENT_TEXT_EXTRACTION_FAILED = "DOCUMENT_TEXT_EXTRACTION_FAILED"
    SEARCH_QUERIED = "SEARCH_QUERIED"
    # RAG retrieval + generation (Phase 9).
    RAG_RETRIEVAL = "RAG_RETRIEVAL"
    RAG_GENERATION = "RAG_GENERATION"
    # AI assistant (Phase 9B).
    AI_QUERY = "AI_QUERY"
    AI_QUERY_FAILED = "AI_QUERY_FAILED"


class AuditResult(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    DENIED = "DENIED"


def client_ip(request: Request | None) -> str | None:
    """Extract the client IP from the request, if available."""
    if request is not None and request.client is not None:
        return request.client.host
    return None


def log_audit(
    db: Session,
    action: AuditAction | str,
    *,
    actor: User | None = None,
    actor_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    case_id: uuid.UUID | None = None,
    result: AuditResult | str = AuditResult.SUCCESS,
    ip_address: str | None = None,
    data: dict | None = None,
    commit: bool = False,
) -> None:
    """
    Record an audit event.

    ``commit=False`` (default): the row is added inside a SAVEPOINT of the
    caller's transaction and is persisted when the caller commits — keeping
    the audit entry atomic with the operation it describes.

    ``commit=True``: used on failure/denial paths where nothing else is
    committed; the audit row is committed immediately.

    Audit write failures are logged (observable) but never raised.
    """
    action_value = action.value if isinstance(action, AuditAction) else str(action)
    result_value = result.value if isinstance(result, AuditResult) else str(result)

    try:
        entry = AuditLog(
            actor_id=actor.id if actor is not None else actor_id,
            action=action_value,
            entity_type=entity_type,
            entity_id=entity_id,
            case_id=case_id,
            ip_address=ip_address,
            result=result_value,
            meta=data or {},
        )
        if commit:
            db.add(entry)
            db.commit()
        else:
            with db.begin_nested():
                db.add(entry)
    except Exception as exc:  # noqa: BLE001 — audit must never break the flow
        logger.warning("Audit write failed for %s: %s", action_value, exc)
