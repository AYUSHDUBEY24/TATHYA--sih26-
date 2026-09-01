"""AuditLog model — append-only trail of security/document activities."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

# JSONB on PostgreSQL, plain JSON elsewhere (SQLite tests/dev).
AuditMetadata = JSONB().with_variant(JSON(), "sqlite")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Actor may be unknown (e.g. failed login for a non-existent user).
    # SET NULL keeps the historical row if the user is ever removed.
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)

    # Plain column (no FK) on purpose: the audit trail must survive case
    # deletion and is never cleaned up with the entities it references.
    case_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)

    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # SUCCESS / FAILURE / DENIED (see AuditResult in the audit service).
    result: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Stored under the DB column "metadata" (attribute "meta" avoids clashing
    # with SQLAlchemy's DeclarativeBase.metadata).
    meta: Mapped[dict] = mapped_column(
        "metadata", AuditMetadata, nullable=False, default=dict
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
