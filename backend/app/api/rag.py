"""RAG retrieval API (Phase 9A) — internal, permission-aware chunk retrieval.

Exposes retrieval ONLY (no LLM/answer generation — that's Phase 9B). The
endpoint exists so the retrieval + authorization path can be tested via HTTP
during Phase 9A.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.services.audit_service import AuditAction, client_ip, log_audit
from app.services.retrieval_service import retrieve_chunks

router = APIRouter()
logger = logging.getLogger("sih26190.api.retrieval")


def _hit_to_dict(hit) -> dict:
    return {
        "chunk_id": str(hit.chunk_id),
        "document_id": str(hit.document_id),
        "version_id": str(hit.version_id),
        "case_id": str(hit.case_id),
        "chunk_index": hit.chunk_index,
        "chunk_text": hit.chunk_text,
        "page_start": hit.page_start,
        "page_end": hit.page_end,
        "score": round(hit.score, 6),
        "file_name": hit.file_name,
    }


@router.get(
    "",
    summary="Retrieve the most relevant authorized chunks for a query (RAG retrieval)",
)
def retrieve(
    request: Request,
    q: str = Query(..., min_length=1, max_length=500, description="Query"),
    top_k: int = Query(default=5, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    query = q.strip()
    if not query:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Query must not be empty"
        )

    result = retrieve_chunks(db, query, current_user, top_k=top_k)

    log_audit(
        db,
        AuditAction.RAG_RETRIEVAL,
        actor=current_user,
        entity_type="RAG_QUERY",
        entity_id=None,
        ip_address=client_ip(request),
        data={
            "query": query[:300],
            "provider": result.provider,
            "candidates": result.total_candidates,
            "returned": len(result.results),
        },
        commit=True,  # read-only operation
    )
    return {
        "query": result.query,
        "provider": result.provider,
        "dimension": result.dimension,
        "total_candidates": result.total_candidates,
        "results": [_hit_to_dict(hit) for hit in result.results],
    }
