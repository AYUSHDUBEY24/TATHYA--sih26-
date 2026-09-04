"""Authorized document search API (Phase 8).

GET /api/search?q=<query> — keyword/full-text matching over document metadata
and extracted text, strictly filtered to the requesting user's authorized
cases (same visibility rules as the documents list: ADMIN → all, others →
assigned IO or case membership). Search can never surface a document from a
case the user cannot access — authorization is applied in the SQL itself.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.case import Case
from app.models.case_member import CaseMember
from app.models.document import Document
from app.models.document_text import DocumentText
from app.models.user import User
from app.schemas.search import SearchHit, SearchResponse
from app.services.audit_service import AuditAction, client_ip, log_audit

router = APIRouter()
logger = logging.getLogger("sih26190.api.search")

_MAX_SNIPPET_LEN = 220


def _make_snippet(text: str | None, terms: list[str]) -> str | None:
    """Build a short lowercase-insensitive window around the first term hit."""
    if not text:
        return None
    lowered = text.lower()
    position = -1
    for term in terms:
        position = lowered.find(term.lower())
        if position != -1:
            break
    if position == -1:
        # Matched metadata only — still show the beginning of the text.
        position = 0
    start = max(0, position - 60)
    end = min(len(text), start + _MAX_SNIPPET_LEN)
    snippet = text[start:end].replace("\n", " ").strip()
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{snippet}{suffix}"


@router.get(
    "",
    response_model=SearchResponse,
    summary="Search authorized documents by name, metadata, and extracted text",
)
def search_documents(
    request: Request,
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    case_id: UUID | None = Query(default=None, description="Optional case scope"),
    document_type: str | None = Query(default=None, description="Optional type filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SearchResponse:
    query = q.strip()
    if not query:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Search query must not be empty"
        )

    # --- Authorization candidate set (mirrors list_documents) ---------------
    stmt = (
        select(Document, Case, DocumentText)
        .join(Case, Document.case_id == Case.id)
        .outerjoin(DocumentText, DocumentText.version_id == Document.current_version_id)
        .where(Document.status == "ACTIVE")
    )
    if current_user.role.name != "ADMIN":
        member_case_ids = select(CaseMember.case_id).where(
            CaseMember.user_id == current_user.id
        )
        authorized_cases = select(Case.id).where(
            (Case.assigned_io_id == current_user.id) | (Case.id.in_(member_case_ids))
        )
        stmt = stmt.where(Document.case_id.in_(authorized_cases))

    # --- Optional scope filters (still authorization-checked) ---------------
    if case_id is not None:
        stmt = stmt.where(Document.case_id == case_id)
    if document_type:
        stmt = stmt.where(Document.document_type == document_type)

    # --- Keyword/full-text matching ------------------------------------------
    # Every whitespace-separated term must match at least one searchable field
    # (AND semantics across terms, OR across fields within a term). ilike()
    # compiles to case-insensitive LIKE on both PostgreSQL and SQLite, so the
    # suite runs without a live PostgreSQL server.
    terms = [t for t in query.split() if t]
    searchable_columns = (
        Document.file_name,
        Document.description,
        Document.document_type,
        Case.case_number,
        Case.title,
        DocumentText.extracted_text,
    )
    for term in terms:
        pattern = f"%{term}%"
        stmt = stmt.where(or_(*[col.ilike(pattern) for col in searchable_columns]))

    # --- Total count, then one page ------------------------------------------
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = int(db.scalar(count_stmt) or 0)

    rows = db.execute(stmt.order_by(Document.created_at.desc()).offset(offset).limit(limit)).all()

    # Resolve uploader usernames for the page only (≤ limit rows).
    uploader_ids = {doc.uploaded_by for doc, _, _ in rows}
    uploader_names: dict = {}
    if uploader_ids:
        uploader_names = dict(
            db.execute(
                select(User.id, User.username).where(User.id.in_(uploader_ids))
            ).all()
        )

    results = [
        SearchHit(
            document_id=doc.id,
            case_id=doc.case_id,
            case_number=case.case_number,
            case_title=case.title,
            file_name=doc.file_name,
            document_type=doc.document_type,
            classification=doc.classification,
            description=doc.description,
            uploader_username=uploader_names.get(doc.uploaded_by),
            current_version_number=doc.current_version_number,
            created_at=doc.created_at,
            extraction_method=text_row.extraction_method if text_row else None,
            extraction_status=text_row.extraction_status if text_row else None,
            snippet=_make_snippet(text_row.extracted_text if text_row else None, terms),
            matched_text=bool(
                text_row
                and text_row.extracted_text
                and any(t.lower() in text_row.extracted_text.lower() for t in terms)
            ),
        )
        for doc, case, text_row in rows
    ]

    log_audit(
        db,
        AuditAction.SEARCH_QUERIED,
        actor=current_user,
        entity_type="SEARCH",
        entity_id=None,
        case_id=case_id,
        ip_address=client_ip(request),
        data={"query": query[:200], "total": total, "limit": limit, "offset": offset},
        commit=True,  # read-only operation
    )
    return SearchResponse(
        query=query, total=total, limit=limit, offset=offset, results=results
    )

