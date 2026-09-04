"""Document processing service — extraction + chunking + embeddings (Phase 8+9A).

Bridges the upload/version flow (app.api.documents), the extraction service,
the chunking service, and the embedding/retrieval services. Reads nothing
itself, receives the stored bytes, extracts text, chunks, embeds, and persists
DocumentText + DocumentChunk rows. Best-effort by design — an extraction,
chunking, or embedding failure never breaks document upload/versioning.
"""

from __future__ import annotations

import json
import logging

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_text import DocumentText
from app.models.document_version import DocumentVersion
from app.models.user import User
from app.services.audit_service import AuditAction, AuditResult, client_ip, log_audit
from app.services.chunking_service import chunk_text
from app.services.extraction_service import (
    STATUS_COMPLETED,
    STATUS_FAILED,
    extract_text,
)

logger = logging.getLogger("sih26190.processing")


def process_document_version(
    db: Session,
    document: Document,
    version: DocumentVersion,
    content: bytes,
    *,
    actor: User,
    request=None,
) -> DocumentText | None:
    """
    Extract text, chunk, and embed a freshly committed version.

    Called AFTER the document/version rows are committed, mirroring the
    Phase 7 blockchain anchor pattern: failures are audited and logged, never
    propagated. Returns the persisted DocumentText row (or None on failure).
    """
    try:
        outcome = extract_text(content, version.mime_type)
    except Exception as exc:  # noqa: BLE001 — extraction_service never raises,
        # but this guard keeps processing truly non-blocking.
        logger.warning("Text extraction crashed for %s: %s", version.id, exc)
        log_audit(
            db,
            AuditAction.DOCUMENT_TEXT_EXTRACTION_FAILED,
            actor=actor,
            entity_type="DOCUMENT",
            entity_id=document.id,
            case_id=document.case_id,
            result=AuditResult.FAILURE,
            ip_address=client_ip(request) if request else None,
            data={"version": version.version_number, "error": "unexpected"},
            commit=True,
        )
        return None

    try:
        record = DocumentText(
            document_id=document.id,
            version_id=version.id,
            extracted_text=outcome.text,
            extraction_method=outcome.method,
            extraction_status=outcome.status,
            page_count=outcome.page_count,
            error_message=outcome.error_message,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
    except Exception as exc:  # noqa: BLE001 — persistence must not break upload
        logger.warning("Could not persist extracted text for %s: %s", version.id, exc)
        db.rollback()
        return None

    success = outcome.status == STATUS_COMPLETED and outcome.searchable
    log_audit(
        db,
        AuditAction.DOCUMENT_TEXT_EXTRACTED if success else AuditAction.DOCUMENT_TEXT_EXTRACTION_FAILED,
        actor=actor,
        entity_type="DOCUMENT",
        entity_id=document.id,
        case_id=document.case_id,
        result=AuditResult.SUCCESS if success else AuditResult.FAILURE,
        ip_address=client_ip(request) if request else None,
        data={
            "version": version.version_number,
            "method": outcome.method,
            "status": outcome.status,
            "page_count": outcome.page_count,
            "text_chars": len(outcome.text) if outcome.text else 0,
        },
        commit=True,  # standalone event — nothing else commits it afterwards
    )
    if not success and outcome.status != STATUS_FAILED:
        logger.info(
            "Text extraction for %s v%d ended with status %s",
            document.id,
            version.version_number,
            outcome.status,
        )

    # --- Phase 9A: chunk + embed only when usable text exists ---------------
    if success and outcome.text and outcome.text.strip():
        try:
            _chunk_and_embed(db, document, version, outcome.text, outcome.page_count)
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning("Chunking/embedding failed for %s: %s", version.id, exc)

    return record


def _chunk_and_embed(
    db: Session,
    document: Document,
    version: DocumentVersion,
    text: str,
    page_count: int | None,
) -> None:
    """Chunk text, embed chunks, persist DocumentChunk rows. Never raises."""
    from app.models.document_chunk import DocumentChunk
    from app.services.embedding_service import embed_texts

    chunk_result = chunk_text(text, page_count=page_count)
    if not chunk_result.chunks:
        return

    texts = [c.text for c in chunk_result.chunks]
    embedding_outcome = embed_texts(texts)

    rows = []
    for chunk, vector in zip(chunk_result.chunks, embedding_outcome.vector):
        rows.append(
            DocumentChunk(
                document_id=document.id,
                version_id=version.id,
                chunk_index=chunk.index,
                chunk_text=chunk.text,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                embedding=json.dumps(vector),
                status="INDEXED",
            )
        )
    db.add_all(rows)
    db.commit()

