"""DocumentChunk model — RAG chunks per document version (Phase 9A).

One chunk row per immutable version. Stores the chunk text, its position in the
document, optional page references, and the embedding vector as a JSON array
(portable across SQLite and PostgreSQL). 

Document bytes stay in object storage; extracted text stays in document_texts;
this table holds only derived, regenerable chunks + their embeddings.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Logical ref to the immutable version (same pattern as document_texts).
    version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, nullable=False, index=True
    )

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Optional page references (best-effort; NULL when unavailable).
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Embedding vector stored as a JSON float array. Portable across SQLite and
    # PostgreSQL. For production PostgreSQL deployments a native pgvector column
    # can be added via migration; the retrieval service reads this JSON.
    embedding: Mapped[str | None] = mapped_column(Text, nullable=True)

    # INDEXED / FAILED / SKIPPED (no usable text) — processing state for the
    # version+chunk pipeline, exposed via the processing status API.
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="INDEXED")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    document: Mapped["Document"] = relationship()  # noqa: F821
