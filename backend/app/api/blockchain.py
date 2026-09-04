"""
Blockchain endpoints (Phase 7) — register, status, and verify document hashes.

The blockchain is ONLY an integrity-anchor layer. Endpoints are JWT-protected
and every operation re-authorizes access to the underlying document/case.
Hashes are always server-computed; the client can never choose an arbitrary
hash. File contents are never returned.
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_authorized_document, get_current_user
from app.core.config import get_settings
from app.core.hashing import sha256_hex
from app.db.database import get_db
from app.models.blockchain_record import BlockchainRecord
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.user import User
from app.schemas.document import (
    BlockchainStatusResponse,
    BlockchainVerifyResponse,
    BlockchainVerifyStatus,
)
from app.services import audit_service
from app.services.audit_service import AuditAction, AuditResult, client_ip
from app.storage import StorageError, StorageService, get_storage

logger = logging.getLogger("sih26190.api.blockchain")

router = APIRouter()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _get_version_for_request(
    document: Document, version_number: int | None, db: Session
) -> DocumentVersion:
    """Resolve the requested version (defaults to current) or raise 404/409."""
    if version_number is not None:
        version = db.scalar(
            select(DocumentVersion).where(
                DocumentVersion.document_id == document.id,
                DocumentVersion.version_number == version_number,
            )
        )
        if version is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                f"Version {version_number} not found for this document",
            )
        return version

    if document.current_version_id is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Document has no current version"
        )
    version = db.get(DocumentVersion, document.current_version_id)
    if version is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Current version record is missing"
        )
    return version


def _get_or_none_record(version_id: UUID, db: Session) -> BlockchainRecord | None:
    return db.scalar(
        select(BlockchainRecord).where(
            BlockchainRecord.document_version_id == version_id
        )
    )


def _record_to_status(
    document: Document, record: BlockchainRecord | None
) -> BlockchainStatusResponse:
    if record is None:
        return BlockchainStatusResponse(
            document_id=document.id,
            status="NOT_ANCHORED",
        )
    version_number = None
    if record.document_version is not None:
        version_number = record.document_version.version_number
    return BlockchainStatusResponse(
        document_id=document.id,
        version_id=record.document_version_id,
        version_number=version_number,
        blockchain_key=record.blockchain_key,
        status=record.status,
        transaction_hash=record.transaction_hash,
        block_number=record.block_number,
        anchored_at=record.anchored_at,
        error_message=record.error_message,
    )


@router.post(
    "/register",
    response_model=BlockchainStatusResponse,
    summary="Anchor a document version hash on the blockchain",
)
def register_on_blockchain(
    request: Request,
    document_id: UUID,
    version_number: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BlockchainStatusResponse:
    settings = get_settings()
    document = get_authorized_document(document_id, current_user, db)
    version = _get_version_for_request(document, version_number, db)

    if not settings.BLOCKCHAIN_ENABLED:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Blockchain anchoring is disabled",
        )

    # Idempotency: if a CONFIRMED record already exists, return it.
    existing = _get_or_none_record(version.id, db)
    if existing is not None and existing.status == "CONFIRMED":
        return _record_to_status(document, existing)

    from app.services.blockchain_service import (
        BlockchainError,
        get_blockchain_service,
    )

    blockchain_key = f"{document.id}:{version.version_number}"

    # Create or reuse the application-side record.
    record = existing
    if record is None:
        record = BlockchainRecord(
            document_version_id=version.id,
            document_hash=version.hash,
            blockchain_key=blockchain_key,
            status="PENDING",
        )
        db.add(record)
        db.commit()
        db.refresh(record)
    else:
        record.status = "PENDING"
        record.error_message = None
        db.commit()

    # Attempt the on-chain registration.
    try:
        service = get_blockchain_service()
        result = service.register_hash(blockchain_key, version.hash)
    except BlockchainError as exc:
        record.status = "FAILED"
        record.error_message = str(exc)[:500]
        db.commit()
        audit_service.log_audit(
            db,
            AuditAction.BLOCKCHAIN_REGISTRATION_FAILED,
            actor=current_user,
            entity_type="BLOCKCHAIN",
            entity_id=record.id,
            case_id=document.case_id,
            result=AuditResult.FAILURE,
            ip_address=client_ip(request),
            data={"key": blockchain_key, "error": str(exc)[:500]},
            commit=True,
        )
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"Blockchain registration failed: {exc}",
        ) from exc

    # Success: update the record with the on-chain proof.
    record.transaction_hash = result["tx_hash"]
    record.block_number = result["block_number"]
    record.anchored_at = result["timestamp"]
    record.status = "CONFIRMED"
    record.error_message = None
    db.commit()
    db.refresh(record)

    audit_service.log_audit(
        db,
        AuditAction.BLOCKCHAIN_REGISTERED,
        actor=current_user,
        entity_type="BLOCKCHAIN",
        entity_id=record.id,
        case_id=document.case_id,
        ip_address=client_ip(request),
        data={
            "key": blockchain_key,
            "tx_hash": result["tx_hash"],
            "block_number": result["block_number"],
        },
        commit=True,
    )
    return _record_to_status(document, record)


@router.get(
    "/{document_id}/verify",
    response_model=BlockchainVerifyResponse,
    summary="Three-layer integrity verification (file / DB / blockchain)",
)
def blockchain_verify(
    request: Request,
    document_id: UUID,
    version_number: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage),
) -> BlockchainVerifyResponse:
    settings = get_settings()
    document = get_authorized_document(document_id, current_user, db)
    version = _get_version_for_request(document, version_number, db)

    # Layer 1 — current file bytes vs stored DB hash.
    try:
        data = storage.get(version.object_key)
    except StorageError:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "File storage is unavailable"
        ) from None
    file_hash = sha256_hex(data)
    if file_hash != version.hash:
        audit_service.log_audit(
            db,
            AuditAction.INTEGRITY_FAILED,
            actor=current_user,
            entity_type="DOCUMENT",
            entity_id=document.id,
            case_id=document.case_id,
            result=AuditResult.FAILURE,
            ip_address=client_ip(request),
            data={
                "layer": "file",
                "version": version.version_number,
                "stored_hash": version.hash,
                "current_hash": file_hash,
            },
            commit=True,
        )
        return BlockchainVerifyResponse(
            status=BlockchainVerifyStatus.FILE_INTEGRITY_FAILURE,
            document_id=document.id,
            version=version.version_number,
            file_hash=file_hash,
            stored_hash=version.hash,
        )

    # Layer 2 — stored DB hash vs blockchain-anchored hash.
    blockchain_key = f"{document.id}:{version.version_number}"
    record = _get_or_none_record(version.id, db)

    if record is None or record.status != "CONFIRMED":
        return BlockchainVerifyResponse(
            status=BlockchainVerifyStatus.NOT_ANCHORED,
            document_id=document.id,
            version=version.version_number,
            file_hash=file_hash,
            stored_hash=version.hash,
            blockchain_key=blockchain_key,
        )

    if not settings.BLOCKCHAIN_ENABLED:
        return BlockchainVerifyResponse(
            status=BlockchainVerifyStatus.BLOCKCHAIN_UNAVAILABLE,
            document_id=document.id,
            version=version.version_number,
            file_hash=file_hash,
            stored_hash=version.hash,
            blockchain_key=blockchain_key,
            transaction_hash=record.transaction_hash,
        )

    from app.services.blockchain_service import (
        BlockchainError,
        get_blockchain_service,
    )

    try:
        service = get_blockchain_service()
        anchor = service.get_anchor(blockchain_key)
    except BlockchainError:
        return BlockchainVerifyResponse(
            status=BlockchainVerifyStatus.BLOCKCHAIN_UNAVAILABLE,
            document_id=document.id,
            version=version.version_number,
            file_hash=file_hash,
            stored_hash=version.hash,
            blockchain_key=blockchain_key,
            transaction_hash=record.transaction_hash,
        )

    if anchor is None:
        return BlockchainVerifyResponse(
            status=BlockchainVerifyStatus.NOT_ANCHORED,
            document_id=document.id,
            version=version.version_number,
            file_hash=file_hash,
            stored_hash=version.hash,
            blockchain_key=blockchain_key,
            transaction_hash=record.transaction_hash,
        )

    onchain_hash = anchor["hash"].lower().replace("0x", "")
    db_hash = version.hash.lower()
    if onchain_hash != db_hash:
        audit_service.log_audit(
            db,
            AuditAction.BLOCKCHAIN_MISMATCH,
            actor=current_user,
            entity_type="BLOCKCHAIN",
            entity_id=record.id,
            case_id=document.case_id,
            result=AuditResult.FAILURE,
            ip_address=client_ip(request),
            data={
                "key": blockchain_key,
                "db_hash": db_hash,
                "blockchain_hash": onchain_hash,
            },
            commit=True,
        )
        return BlockchainVerifyResponse(
            status=BlockchainVerifyStatus.BLOCKCHAIN_MISMATCH,
            document_id=document.id,
            version=version.version_number,
            file_hash=file_hash,
            stored_hash=version.hash,
            blockchain_hash=onchain_hash,
            blockchain_key=blockchain_key,
            transaction_hash=record.transaction_hash,
        )

    # All three layers match.
    verified_at = datetime.now(timezone.utc)
    audit_service.log_audit(
        db,
        AuditAction.BLOCKCHAIN_VERIFIED,
        actor=current_user,
        entity_type="BLOCKCHAIN",
        entity_id=record.id,
        case_id=document.case_id,
        ip_address=client_ip(request),
        data={"key": blockchain_key, "tx_hash": record.transaction_hash},
        commit=True,
    )
    return BlockchainVerifyResponse(
        status=BlockchainVerifyStatus.VERIFIED,
        document_id=document.id,
        version=version.version_number,
        file_hash=file_hash,
        stored_hash=version.hash,
        blockchain_hash=onchain_hash,
        blockchain_key=blockchain_key,
        transaction_hash=record.transaction_hash,
        verified_at=verified_at,
    )
@router.get(
    "/{document_id}/status",
    response_model=BlockchainStatusResponse,
    summary="Blockchain anchor status for a document's version",
)
def blockchain_status(
    document_id: UUID,
    version_number: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BlockchainStatusResponse:
    document = get_authorized_document(document_id, current_user, db)
    version = _get_version_for_request(document, version_number, db)
    record = _get_or_none_record(version.id, db)
    return _record_to_status(document, record)
    if record is None:
        return BlockchainStatusResponse(
            document_id=document.id,
            status="NOT_ANCHORED",
        )
    version_number = None
    if record.document_version is not None:
        version_number = record.document_version.version_number
    return BlockchainStatusResponse(
        document_id=document.id,
        version_id=record.document_version_id,
        version_number=version_number,
        blockchain_key=record.blockchain_key,
        status=record.status,
        transaction_hash=record.transaction_hash,
        block_number=record.block_number,
        anchored_at=record.anchored_at,
        error_message=record.error_message,
    )