"""Secure document endpoints — storage in MinIO, access via case authorization.

Phase 5: immutable version history + SHA-256 integrity verification.
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import (
    get_authorized_case,
    get_authorized_document,
    get_current_user,
    user_can_access_case,
    user_can_delete_document,
)
from app.core.config import get_settings
from app.core.files import (
    ALLOWED_CONTENT_TYPES,
    CLASSIFICATIONS,
    DOCUMENT_TYPES,
    sanitize_filename,
    signature_matches,
)
from app.core.hashing import sha256_hex
from app.db.database import get_db
from app.models.case import Case
from app.models.case_member import CaseMember
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.case import UserBrief
from app.schemas.document import (
    DocumentResponse,
    DocumentVersionResponse,
    IntegrityResponse,
    IntegrityStatus,
)
from app.storage import StorageError, StorageService, get_storage
from app.services.audit_service import AuditAction, AuditResult, client_ip, log_audit

router = APIRouter()
# Top-level version routes (/api/versions/{id}[/download]) — version access is
# always re-authorized through the version's parent document/case.
versions_router = APIRouter()


def _read_and_validate_file(file: UploadFile) -> tuple[bytes, str, str]:
    """
    Shared upload validation: size cap, MIME whitelist, magic-byte check,
    filename sanitisation. Returns (content, content_type, safe_file_name).
    """
    max_bytes = get_settings().MAX_UPLOAD_SIZE_MB * 1024 * 1024
    content = file.file.read(max_bytes + 1)
    if not content:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Empty file")
    if len(content) > max_bytes:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File too large"
        )

    declared_type = file.content_type or "application/octet-stream"
    if declared_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Unsupported file type"
        )
    if not signature_matches(declared_type, content[:16]):
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "File content does not match the declared file type",
        )

    return content, declared_type, sanitize_filename(file.filename or "upload.bin")


def _version_object_key(
    case_id: UUID, document_id: UUID, version_number: int, file_name: str
) -> str:
    """Deterministic, immutable per-version object key."""
    return f"case/{case_id}/doc-{document_id}/v{version_number}/{file_name}"


def _to_response(doc: Document, current_user: User, db: Session) -> DocumentResponse:
    """Build the response payload, including the server-computed can_delete."""
    uploader = db.get(User, doc.uploaded_by)
    return DocumentResponse(
        id=doc.id,
        case_id=doc.case_id,
        file_name=doc.file_name,
        document_type=doc.document_type,
        classification=doc.classification,
        description=doc.description,
        status=doc.status,
        size_bytes=doc.size_bytes,
        content_type=doc.content_type,
        uploader=UserBrief.model_validate(uploader) if uploader else None,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        current_version_number=doc.current_version_number,
        current_hash=doc.current_hash,
        can_delete=user_can_delete_document(current_user, doc, db),
    )


def _version_to_response(
    version: DocumentVersion, db: Session
) -> DocumentVersionResponse:
    uploader = db.get(User, version.uploaded_by)
    return DocumentVersionResponse(
        id=version.id,
        document_id=version.document_id,
        version_number=version.version_number,
        file_name=version.file_name,
        hash=version.hash,
        file_size=version.file_size,
        mime_type=version.mime_type,
        change_note=version.change_note,
        created_at=version.created_at,
        uploader=UserBrief.model_validate(uploader) if uploader else None,
    )


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document to an authorized case",
)
def upload_document(
    request: Request,
    file: UploadFile = File(...),
    case_id: UUID = Form(...),
    document_type: str = Form(...),
    classification: str = Form(...),
    description: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage),
) -> DocumentResponse:
    # 1) Authorization — case access implies upload ("WRITE") permission.
    case = get_authorized_case(case_id, current_user, db)

    # 2) Field validation (controlled vocabularies).
    if document_type not in DOCUMENT_TYPES:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Unsupported document type"
        )
    if classification not in CLASSIFICATIONS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Unsupported classification"
        )

    # 3) File validation — size cap, MIME whitelist, magic-byte check.
    content, declared_type, safe_name = _read_and_validate_file(file)

    # 4) Document + version-1 rows (hash covers the exact stored bytes).
    document = Document(
        case_id=case.id,
        file_name=safe_name,
        document_type=document_type,
        classification=classification,
        description=description or None,
        uploaded_by=current_user.id,
        object_key="",  # set below
        content_type=declared_type,
        size_bytes=len(content),
        status="ACTIVE",
    )
    db.add(document)
    db.flush()

    version = DocumentVersion(
        document_id=document.id,
        version_number=1,
        file_name=safe_name,
        object_key=_version_object_key(case.id, document.id, 1, safe_name),
        hash=sha256_hex(content),
        file_size=len(content),
        mime_type=declared_type,
        uploaded_by=current_user.id,
        change_note=None,
    )
    db.add(version)
    db.flush()

    document.object_key = version.object_key
    document.current_version_id = version.id
    document.current_version_number = 1
    document.current_hash = version.hash
    db.flush()

    log_audit(
        db,
        AuditAction.DOCUMENT_UPLOADED,
        actor=current_user,
        entity_type="DOCUMENT",
        entity_id=document.id,
        case_id=case.id,
        ip_address=client_ip(request),
        data={
            "file_name": safe_name,
            "size_bytes": len(content),
            "document_type": document_type,
            "version": 1,
        },
    )

    # 5) Storage; a failure rolls back document AND version rows.
    try:
        storage.save(version.object_key, content, declared_type)
    except StorageError:
        db.rollback()
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "File storage is unavailable"
        ) from None

    db.commit()
    db.refresh(document)
    return _to_response(document, current_user, db)


@router.get("", response_model=list[DocumentResponse], summary="List visible documents")
def list_documents(
    case_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DocumentResponse]:
    stmt = select(Document).where(Document.status == "ACTIVE")
    if case_id is not None:
        # Authorize the case itself (404 if unauthorized — no existence leak).
        case = get_authorized_case(case_id, current_user, db)
        stmt = stmt.where(Document.case_id == case.id)
    elif current_user.role.name != "ADMIN":
        # Restrict to documents inside authorized cases.
        member_case_ids = select(CaseMember.case_id).where(
            CaseMember.user_id == current_user.id
        )
        authorized_cases = select(Case.id).where(
            (Case.assigned_io_id == current_user.id)
            | (Case.id.in_(member_case_ids))
        )
        stmt = stmt.where(Document.case_id.in_(authorized_cases))
    stmt = stmt.order_by(Document.created_at.desc())
    docs = db.scalars(stmt).all()
    return [_to_response(d, current_user, db) for d in docs]


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Document metadata",
)
def get_document(
    document_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    document = get_authorized_document(document_id, current_user, db)
    log_audit(
        db,
        AuditAction.DOCUMENT_VIEWED,
        actor=current_user,
        entity_type="DOCUMENT",
        entity_id=document.id,
        case_id=document.case_id,
        ip_address=client_ip(request),
        data={"file_name": document.file_name},
        commit=True,  # read-only operation
    )
    return _to_response(document, current_user, db)


@router.get(
    "/{document_id}/download",
    summary="Download a document (proxied through the backend)",
)
def download_document(
    document_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage),
) -> Response:
    document = get_authorized_document(document_id, current_user, db)
    try:
        data = storage.get(document.object_key)
    except StorageError:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "File storage is unavailable"
        ) from None
    log_audit(
        db,
        AuditAction.DOCUMENT_DOWNLOADED,
        actor=current_user,
        entity_type="DOCUMENT",
        entity_id=document.id,
        case_id=document.case_id,
        ip_address=client_ip(request),
        data={"file_name": document.file_name, "size_bytes": document.size_bytes},
        commit=True,  # read-only operation
    )
    # Never expose internal object keys or bucket URLs — stream bytes only.
    return Response(
        content=data,
        media_type=document.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{document.file_name}"'
        },
    )


@router.delete(
    "/{document_id}",
    response_model=MessageResponse,
    summary="Soft-delete a document (ADMIN, case manager, or uploader)",
)
def delete_document(
    document_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage),
) -> MessageResponse:
    document = get_authorized_document(document_id, current_user, db)
    if not user_can_delete_document(current_user, document, db):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Insufficient permissions to delete this document",
        )
    # Soft delete: keep the DB row (and storage object) for later phases.
    document.status = "DELETED"
    log_audit(
        db,
        AuditAction.DOCUMENT_DELETED,
        actor=current_user,
        entity_type="DOCUMENT",
        entity_id=document.id,
        case_id=document.case_id,
        ip_address=client_ip(request),
        data={"file_name": document.file_name, "soft_delete": True},
    )
    db.commit()
    return MessageResponse(message="Document deleted")


# --------------------------------------------------------------------------
# Versioning + integrity (Phase 5)
# --------------------------------------------------------------------------


@router.post(
    "/{document_id}/versions",
    response_model=DocumentVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new version of a document (same authorization as upload)",
)
def create_document_version(
    request: Request,
    document_id: UUID,
    file: UploadFile = File(...),
    change_note: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage),
) -> DocumentVersionResponse:
    document = get_authorized_document(document_id, current_user, db)

    content, declared_type, safe_name = _read_and_validate_file(file)

    next_number = (
        db.scalar(
            select(func.max(DocumentVersion.version_number)).where(
                DocumentVersion.document_id == document.id
            )
        )
        or 0
    ) + 1

    version = DocumentVersion(
        document_id=document.id,
        version_number=next_number,
        file_name=safe_name,
        object_key=_version_object_key(
            document.case_id, document.id, next_number, safe_name
        ),
        hash=sha256_hex(content),
        file_size=len(content),
        mime_type=declared_type,
        uploaded_by=current_user.id,
        change_note=change_note or None,
    )
    db.add(version)
    db.flush()

    # Current-version pointers follow the latest version; historical objects
    # and rows are never modified.
    document.object_key = version.object_key
    document.current_version_id = version.id
    document.current_version_number = next_number
    document.current_hash = version.hash
    document.file_name = safe_name
    db.flush()

    log_audit(
        db,
        AuditAction.DOCUMENT_VERSION_CREATED,
        actor=current_user,
        entity_type="DOCUMENT",
        entity_id=document.id,
        case_id=document.case_id,
        ip_address=client_ip(request) if request else None,
        data={"version": next_number, "file_name": safe_name, "change_note": change_note},
    )

    try:
        storage.save(version.object_key, content, declared_type)
    except StorageError:
        db.rollback()
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "File storage is unavailable"
        ) from None

    db.commit()
    db.refresh(version)
    return _version_to_response(version, db)


@router.get(
    "/{document_id}/versions",
    response_model=list[DocumentVersionResponse],
    summary="Version history (authorized users only)",
)
def list_document_versions(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DocumentVersionResponse]:
    document = get_authorized_document(document_id, current_user, db)
    versions = db.scalars(
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document.id)
        .order_by(DocumentVersion.version_number.desc())
    ).all()
    return [_version_to_response(v, db) for v in versions]


@router.get(
    "/{document_id}/integrity",
    response_model=IntegrityResponse,
    summary="Verify SHA-256 integrity of the current version",
)
def verify_document_integrity(
    document_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage),
) -> IntegrityResponse:
    document = get_authorized_document(document_id, current_user, db)

    if document.current_version_id is None:
        # Legacy Phase 4 record without any version row.
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Document has no current version to verify"
        )
    version = db.get(DocumentVersion, document.current_version_id)
    if version is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Current version record is missing"
        )

    try:
        data = storage.get(version.object_key)
    except StorageError:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "File storage is unavailable"
        ) from None

    # Recompute over the exact stored bytes and compare — never repair.
    current_hash = sha256_hex(data)
    verified = current_hash == version.hash
    log_audit(
        db,
        AuditAction.INTEGRITY_VERIFIED if verified else AuditAction.INTEGRITY_FAILED,
        actor=current_user,
        entity_type="DOCUMENT",
        entity_id=document.id,
        case_id=document.case_id,
        result=AuditResult.SUCCESS if verified else AuditResult.FAILURE,
        ip_address=client_ip(request),
        data={
            "version": version.version_number,
            "stored_hash": version.hash,
            "current_hash": current_hash,
        },
        commit=True,  # read-only verification
    )
    return IntegrityResponse(
        status=IntegrityStatus.VERIFIED if verified else IntegrityStatus.INTEGRITY_FAILURE,
        document_id=document.id,
        version=version.version_number,
        stored_hash=version.hash,
        current_hash=current_hash,
        verified_at=datetime.now(timezone.utc) if verified else None,
    )


@versions_router.get(
    "/{version_id}",
    response_model=DocumentVersionResponse,
    summary="Version metadata (authorized via the version's document/case)",
)
def get_version(
    version_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentVersionResponse:
    version = _get_authorized_version(version_id, current_user, db)
    return _version_to_response(version, db)


@versions_router.get(
    "/{version_id}/download",
    summary="Download a historical version (proxied through the backend)",
)
def download_version(
    version_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage),
) -> Response:
    version = _get_authorized_version(version_id, current_user, db)
    try:
        data = storage.get(version.object_key)
    except StorageError:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Stored version could not be retrieved from file storage",
        ) from None
    return Response(
        content=data,
        media_type=version.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{version.file_name}"'
        },
    )


def _get_authorized_version(
    version_id: UUID, current_user: User, db: Session
) -> DocumentVersion:
    """Authorize a version through its parent document's case (404 on denial)."""
    version = db.get(DocumentVersion, version_id)
    if version is None:
        log_audit(
            db,
            AuditAction.ACCESS_DENIED,
            actor=current_user,
            entity_type="DOCUMENT_VERSION",
            entity_id=None,
            result=AuditResult.DENIED,
            commit=True,
        )
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Version not found")
    document = db.get(Document, version.document_id)
    if document is None or document.status != "ACTIVE":
        log_audit(
            db,
            AuditAction.ACCESS_DENIED,
            actor=current_user,
            entity_type="DOCUMENT_VERSION",
            entity_id=version.id,
            case_id=document.case_id if document else None,
            result=AuditResult.DENIED,
            commit=True,
        )
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Version not found")
    case = db.get(Case, document.case_id)
    if case is None or not user_can_access_case(current_user, case, db):
        log_audit(
            db,
            AuditAction.ACCESS_DENIED,
            actor=current_user,
            entity_type="DOCUMENT_VERSION",
            entity_id=version.id,
            case_id=document.case_id,
            result=AuditResult.DENIED,
            commit=True,
        )
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Version not found")
    return version