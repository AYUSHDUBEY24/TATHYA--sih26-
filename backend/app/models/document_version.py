"""DocumentVersion model — immutable version history with SHA-256 hashes."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_docver_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Immutable per-version object key:
    #   case/{case_id}/doc-{document_id}/v{version_number}/{safe_file_name}
    object_key: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)

    # SHA-256 (lowercase hex) of the exact stored bytes for this version.
    hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)

    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    change_note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    document: Mapped["Document"] = relationship(  # noqa: F821
        back_populates="versions"
    )
    uploader: Mapped["User"] = relationship()  # noqa: F821
    blockchain_record: Mapped["BlockchainRecord | None"] = relationship(  # noqa: F821
        back_populates="document_version", uselist=False
    )
