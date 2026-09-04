"""DocumentText model — extracted searchable text per document version (Phase 8).

Stores only text + extraction metadata; document bytes always live in object
storage (MinIO), never in PostgreSQL/SQLite.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class DocumentText(Base):
    __tablename__ = "document_texts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # One extraction record per immutable version (logical ref, same pattern as
    # documents.current_version_id — avoids cross-table FK cascades).
    version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, nullable=False, unique=True, index=True
    )

    # Extracted text (may be NULL when extraction produced nothing usable).
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # How the text was obtained: PYMUPDF / OCR / PLAIN_TEXT / NONE.
    extraction_method: Mapped[str] = mapped_column(String(20), nullable=False)
    # COMPLETED / EMPTY / UNSUPPORTED_TYPE / OCR_UNAVAILABLE / FAILED
    extraction_status: Mapped[str] = mapped_column(String(30), nullable=False)

    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Safe, short description when extraction did not complete (no paths/secrets).
    error_message: Mapped[str | None] = mapped_column(String(300), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    document: Mapped["Document"] = relationship()  # noqa: F821
