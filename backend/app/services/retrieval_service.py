"""Permission-aware semantic retrieval service (Phase 9A).

Retrieves the top-k most similar document chunks for a query, strictly within
the set of documents the requesting user is authorized to access. The
authorization filter is applied IN THE SQL candidate set — we never pull all
chunks and filter afterward.

Embeddings are stored as JSON float arrays on DocumentChunk.embedding so the
test environment (SQLite, which has no pgvector) and PostgreSQL deployments
share the same retrieval code path. The FALLBACK_DIM hashing scheme gives
deterministic cosine-like similarity even without a real embedding model.
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import user_can_access_case
from app.models.case import Case
from app.models.case_member import CaseMember
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.document_text import DocumentText
from app.models.user import User
from app.services.embedding_service import FALLBACK_DIM, embed_texts

logger = logging.getLogger("sih26190.retrieval")

# Minimum cosine similarity for a chunk to count as a relevant result. Near-zero
# vector noise (unrelated authorized documents score ~0.02-0.06 with the fallback
# provider) is filtered out; genuine keyword/semantic matches score well above
# this floor (0.15+). Keeps retrieval from returning noise just because the
# document happens to be authorized.
MIN_SIMILARITY = 0.1


@dataclass
class RetrievalHit:
    """One authorized similar chunk."""

    chunk_id: UUID
    document_id: UUID
    version_id: UUID
    case_id: UUID
    chunk_index: int
    chunk_text: str
    page_start: int | None = None
    page_end: int | None = None
    score: float = 0.0
    file_name: str | None = None


@dataclass
class RetrievalResult:
    query: str
    provider: str
    dimension: int
    # Authorized chunks scoring above MIN_SIMILARITY (relevant candidates).
    total_candidates: int
    results: list[RetrievalHit] = field(default_factory=list)


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    """Cosine similarity between two equal-length vectors (pure Python)."""
    if not left or not right or len(left) != len(right):
        return 0.0
    dot_product = sum(a * b for a, b in zip(left, right))
    magnitude_left = math.sqrt(sum(a * a for a in left)) or 1.0
    magnitude_right = math.sqrt(sum(b * b for b in right)) or 1.0
    return dot_product / (magnitude_left * magnitude_right)


def retrieve_chunks(
    db: Session,
    query: str,
    current_user: User,
    *,
    top_k: int = 5,
    case_id: UUID | None = None,
) -> RetrievalResult:
    """
    Authorised semantic retrieval.

    1. Embed the query with the shared provider.
    2. Build the authorized candidate set (SQL-level filter, mirroring the
       documents list and search endpoints).
    3. Score candidates with cosine similarity against stored embeddings.
    4. Return the top-k hits.
    """
    outcome = embed_texts([query]) if query.strip() else None
    if outcome is None or not outcome.vector:
        return RetrievalResult(
            query=query,
            provider="none",
            dimension=0,
            total_candidates=0,
        )
    query_vector = outcome.vector[0]

    # --- Authorized candidate set (mirrors list_documents) -------------------
    stmt = (
        select(DocumentChunk, Document, DocumentText)
        .join(Document, DocumentChunk.document_id == Document.id)
        .join(DocumentText, DocumentText.version_id == DocumentChunk.version_id)
        .where(Document.status == "ACTIVE")
        .where(DocumentChunk.embedding.isnot(None))
    )
    if current_user.role.name != "ADMIN":
        member_case_ids = select(CaseMember.case_id).where(
            CaseMember.user_id == current_user.id
        )
        authorized_cases = select(Case.id).where(
            (Case.assigned_io_id == current_user.id) | (Case.id.in_(member_case_ids))
        )
        stmt = stmt.where(Document.case_id.in_(authorized_cases))

    if case_id is not None:
        # Still subject to the authorization clause above — case_id only
        # narrows within the authorized set.
        stmt = stmt.where(Document.case_id == case_id)

    rows = db.execute(stmt).all()

    # --- Score, filter noise, and rank -------------------------------------
    hits: list[RetrievalHit] = []
    for chunk, document, _text in rows:
        vector = _decode_embedding(chunk.embedding)
        if not vector or len(vector) != len(query_vector):
            continue
        score = _cosine_similarity(query_vector, vector)
        if score < MIN_SIMILARITY:
            continue
        hits.append(
            RetrievalHit(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                version_id=chunk.version_id,
                case_id=document.case_id,
                chunk_index=chunk.chunk_index,
                chunk_text=chunk.chunk_text,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                score=score,
                file_name=document.file_name,
            )
        )

    hits.sort(key=lambda hit: hit.score, reverse=True)
    return RetrievalResult(
        query=query,
        provider=outcome.provider,
        dimension=outcome.dimension,
        # Number of authorized chunks scoring above MIN_SIMILARITY (relevant
        # candidates), not every row scanned — near-zero noise is excluded.
        total_candidates=len(hits),
        results=hits[:top_k],
    )


def _decode_embedding(raw: str | None) -> list[float] | None:
    """Decode a stored JSON float array, tolerating a single nested structure."""
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if isinstance(parsed, list) and parsed and isinstance(parsed[0], list):
        # Flatten a nested [[...]] wrapper.
        parsed = [value for sublist in parsed for value in sublist]
    return [float(v) for v in parsed] if isinstance(parsed, list) else None

