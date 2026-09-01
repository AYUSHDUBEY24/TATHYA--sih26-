"""Document model — metadata for case-scoped files stored in MinIO."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # One of the controlled types in app/core/files.py (validated in schemas).
    document_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    classification: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    # Deterministic, case/document-scoped key inside the private bucket:
    #   case/{case_id}/doc-{document_id}/{sanitized_file_name}
    # Never exposed as a public URL — downloads are proxied by the backend.
    object_key: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    # ACTIVE / DELETED (soft delete — keeps history for later phases).
    status: Mapped[str] = mapped_column(
        String(20), default="ACTIVE", nullable=False, index=True
    )

    # --- Phase 5: current-version pointer + integrity hash ---
    # Logical reference to document_versions.id (deliberately NOT a DB-level
    # FK to avoid a circular FK cascade between documents and versions).
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    current_version_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # SHA-256 of the current version's stored bytes (denormalized for fast
    # status display); the authoritative per-version hash lives on the version.
    current_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    case: Mapped["Case"] = relationship()  # noqa: F821
    uploader: Mapped["User"] = relationship()  # noqa: F821
    versions: Mapped[list["DocumentVersion"]] = relationship(  # noqa: F821
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentVersion.version_number",
    )
