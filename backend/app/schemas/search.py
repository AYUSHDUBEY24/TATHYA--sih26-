"""Search schemas (Phase 8)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SearchHit(BaseModel):
    """One authorized matching document (metadata only — no raw text dump)."""

    model_config = ConfigDict(from_attributes=True)

    document_id: UUID
    case_id: UUID
    case_number: str
    case_title: str
    file_name: str
    document_type: str
    classification: str
    description: str | None = None
    uploader_username: str | None = None
    current_version_number: int | None = None
    created_at: datetime
    # How the current version's text was extracted (PYMUPDF/OCR/…), if known.
    extraction_method: str | None = None
    extraction_status: str | None = None
    # Short window of extracted text around the first match (authorized docs
    # only — the whole row is only returned for documents the user may access).
    snippet: str | None = None
    # True when the match came from extracted document text (not just metadata).
    matched_text: bool = False


class SearchResponse(BaseModel):
    query: str
    total: int
    limit: int
    offset: int
    results: list[SearchHit]
