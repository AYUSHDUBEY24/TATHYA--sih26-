"""BlockchainRecord model — application-side anchor record for a document version."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class BlockchainRecord(Base):
    __tablename__ = "blockchain_records"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    document_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_versions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    document_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Unique key used on-chain: "<document_id>:<version_number>".
    blockchain_key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)

    transaction_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    block_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    anchored_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # PENDING / CONFIRMED / FAILED
    status: Mapped[str] = mapped_column(
        String(20), default="PENDING", nullable=False, index=True
    )
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    document_version: Mapped["DocumentVersion"] = relationship(  # noqa: F821
        back_populates="blockchain_record"
    )