"""AI assistant query API (Phase 9B) â€” POST /api/ai/query.

The retrieval layer (Phase 9A) is the security boundary: the endpoint retrieves
ONLY authorized chunks and hands those to the LLM. The LLM service never
touches the database. Citations are built exclusively from the chunks that were
actually supplied to the model â€” never invented, never from unretrieved docs.

Response states:
* ``answered`` â€” LLM generated an answer from authorized context.
* ``insufficient_context`` â€” no authorized/relevant chunks; the assistant says
  so and the LLM is NOT called (anti-hallucination).
* ``provider_unavailable`` (HTTP 503) â€” no provider configured or it failed;
  the client receives a clear error instead of a fabricated answer.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.document_version import DocumentVersion
from app.models.user import User
from app.schemas.ai import AICitation, AIQueryRequest, AIQueryResponse
from app.services import llm_service
from app.services.audit_service import AuditAction, AuditResult, client_ip, log_audit
from app.services.llm_service import LLMUnavailableError, SourceChunk
from app.services.retrieval_service import RetrievalHit, retrieve_chunks

router = APIRouter()
logger = logging.getLogger("sih26190.api.ai")

_TOP_K = 6
_EXCERPT_CHARS = 240
_SAFE_QUERY_LOG = 300
_ANSWER_TRUNCATION = 2000

_NO_CONTEXT_ANSWER = (
    "I couldn't find enough information in the authorized documents to answer "
    "that."
)
_PROVIDER_UNAVAILABLE_MSG = (
    "The AI assistant provider is not configured or is currently unavailable. "
    "No answer was generated."
)
def _version_numbers(db: Session, version_ids: list) -> dict:
    """Map version UUIDs -> their version_number for citation metadata."""
    if not version_ids:
        return {}
    rows = db.execute(
        select(DocumentVersion).where(DocumentVersion.id.in_(version_ids))
    ).scalars()
    return {row.id: row.version_number for row in rows}


def _build_citations(
    hits: list[RetrievalHit], version_numbers: dict
) -> list[AICitation]:
    return [
        AICitation(
            document_id=hit.document_id,
            file_name=hit.file_name,
            version=version_numbers.get(hit.version_id),
            chunk_id=hit.chunk_id,
            page_start=hit.page_start,
            page_end=hit.page_end,
            excerpt=(hit.chunk_text or "")[:_EXCERPT_CHARS],
            score=round(hit.score, 6),
        )
        for hit in hits
    ]


def _build_source_chunks(
    hits: list[RetrievalHit], version_numbers: dict
) -> list[SourceChunk]:
    return [
        SourceChunk(
            text=hit.chunk_text,
            file_name=hit.file_name,
            version_number=version_numbers.get(hit.version_id),
            chunk_index=hit.chunk_index,
            page_start=hit.page_start,
            page_end=hit.page_end,
            document_id=hit.document_id,
        )
        for hit in hits
    ]


def _audit_query(
    db: Session,
    request: Request,
    actor: User,
    *,
    action: AuditAction,
    query: str,
    result: AuditResult,
    status_label: str,
    source_count: int,
    provider: str,
) -> None:
    """One audit event per AI query â€” metadata only, NEVER document contents."""
    log_audit(
        db,
        action,
        actor=actor,
        entity_type="AI_QUERY",
        entity_id=None,
        ip_address=client_ip(request),
        result=result,
        data={
            "query": query[:_SAFE_QUERY_LOG],
            "status": status_label,
            "sources": source_count,
            "provider": provider,
        },
        commit=True,  # read-only operation; standalone event
    )
@router.post("/query", response_model=AIQueryResponse, summary="Ask the AI assistant")
def ai_query(
    payload: AIQueryRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AIQueryResponse:
    query = payload.question.strip()
    if not query:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Question must not be empty"
        )

    # --- Permission-aware retrieval (the security boundary) ------------------
    result = retrieve_chunks(
        db, query, current_user, top_k=_TOP_K, case_id=payload.case_id
    )
    hits: list[RetrievalHit] = result.results

    if not hits:
        # No authorized/relevant context: do NOT call the LLM to guess.
        _audit_query(
            db,
            request,
            current_user,
            query=query,
            action=AuditAction.AI_QUERY,
            result=AuditResult.SUCCESS,
            status_label="insufficient_context",
            source_count=0,
            provider=result.provider,
        )
        return AIQueryResponse(
            status="insufficient_context",
            answer=_NO_CONTEXT_ANSWER,
            sources=[],
            provider=result.provider,
        )

    # --- Build the context handed to the LLM (only authorized chunks) --------
    version_numbers = _version_numbers(db, [h.version_id for h in hits])
    citations = _build_citations(hits, version_numbers)
    source_chunks = _build_source_chunks(hits, version_numbers)

    provider_name = llm_service.get_llm_provider().name
    try:
        answer = llm_service.generate_answer(query, source_chunks)
    except (LLMUnavailableError, Exception) as exc:  # noqa: BLE001 — optional service
        # The LLM is an optional external dependency: provider failure must
        # surface as a clear 503, never crash the endpoint or expose context.
        logger.warning("AI query generation failed: %r", exc)
        _audit_query(
            db,
            request,
            current_user,
            query=query,
            action=AuditAction.AI_QUERY_FAILED,
            result=AuditResult.FAILURE,
            status_label="provider_unavailable",
            source_count=len(citations),
            provider=provider_name,
        )
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, _PROVIDER_UNAVAILABLE_MSG
        ) from None

    _audit_query(
        db,
        request,
        current_user,
        query=query,
        action=AuditAction.AI_QUERY,
        result=AuditResult.SUCCESS,
        status_label="answered",
        source_count=len(citations),
        provider=provider_name,
    )
    return AIQueryResponse(
        status="answered",
        answer=answer[:_ANSWER_TRUNCATION],
        sources=citations,
        provider=provider_name,
    )
