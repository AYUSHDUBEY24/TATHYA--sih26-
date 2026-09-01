"""Audit trail API — ADMIN only, read-only, filterable."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.document import AuditLogResponse

router = APIRouter()


@router.get(
    "",
    response_model=list[AuditLogResponse],
    summary="Query the audit trail (ADMIN only; read-only, append-oriented)",
)
def query_audit(
    action: str | None = None,
    actor_id: UUID | None = None,
    case_id: UUID | None = None,
    entity_id: UUID | None = None,
    result: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    _current_user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> list[AuditLogResponse]:
    """
    Filterable audit query. There is deliberately NO create/update/delete API:
    the audit trail is append-oriented and immutable through the application.
    """
    stmt = (
        select(AuditLog, User.username)
        .outerjoin(User, AuditLog.actor_id == User.id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    if action is not None:
        stmt = stmt.where(AuditLog.action == action)
    if actor_id is not None:
        stmt = stmt.where(AuditLog.actor_id == actor_id)
    if case_id is not None:
        stmt = stmt.where(AuditLog.case_id == case_id)
    if entity_id is not None:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if result is not None:
        stmt = stmt.where(AuditLog.result == result)
    if date_from is not None:
        stmt = stmt.where(AuditLog.created_at >= date_from)
    if date_to is not None:
        stmt = stmt.where(AuditLog.created_at <= date_to)

    rows = db.execute(stmt).all()
    return [
        AuditLogResponse(
            id=entry.id,
            actor_id=entry.actor_id,
            actor_username=username,
            action=entry.action,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            case_id=entry.case_id,
            ip_address=entry.ip_address,
            result=entry.result,
            metadata=entry.meta,
            created_at=entry.created_at,
        )
        for entry, username in rows
    ]
