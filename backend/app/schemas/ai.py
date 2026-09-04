"""AI assistant schemas (Phase 9B).

Payloads carry question + citations only. Document text itself never appears in
a request/response schema beyond short excerpts inside citations (all of which
are already authorized by the retrieval layer).
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AIQueryRequest(BaseModel):
    """Authenticated AI query — the question the assistant must answer."""

    question: str = Field(min_length=1, max_length=2000)
    # Optional narrow-scope filter; authorization is STILL enforced server-side
    # (a case_id the user cannot access yields no candidates, never an error).
    case_id: UUID | None = None


class AICitation(BaseModel):
    """One source actually supplied to the LLM (never invented by the model)."""

    model_config = ConfigDict(from_attributes=True)

    document_id: UUID
    file_name: str | None = None
    version: int | None = None
    chunk_id: UUID | None = None
    page_start: int | None = None
    page_end: int | None = None
    excerpt: str | None = None
    score: float | None = None


class AIQueryResponse(BaseModel):
    """Result of an AI query.

    ``status``:
      * ``answered`` — a real LLM answer was generated from authorized context.
      * ``insufficient_context`` — no authorized/relevant chunks found (no LLM
        call was made; the assistant says so instead of guessing).
      * ``provider_unavailable`` — no LLM provider configured or it failed.
    """

    status: str
    answer: str
    sources: list[AICitation]
    provider: str = "fallback"