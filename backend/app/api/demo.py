"""DEMO-ONLY tampering simulation API (SIH demonstration support).

DANGER — DEMO/TEST FEATURE, NOT A PRODUCTION CAPABILITY:
Endpoints here intentionally modify the *stored file bytes* of an existing
document version WITHOUT creating a new version, WITHOUT touching the
database (stored SHA-256 stays untouched) and WITHOUT touching blockchain
records. This exists solely so the real integrity/blockchain verification
flow can be demonstrated detecting an actual file modification.

Safety properties:
* Gated to the development/demo environment: every endpoint returns 404
  unless ``settings.DEBUG`` is enabled.
* Reuses the exact same authentication + case-level authorization chain as
  the documents API (``get_current_user`` + ``get_authorized_document``) —
  no new permission surface.
* Only the requested document's current version object is modified.
* The pristine original bytes are preserved under a sibling backup object
  so "restore" puts back the EXACT original bytes.
* The verification endpoints under /api/documents/{id}/integrity and
  /api/blockchain/{id}/verify remain the single source of truth — this
  module never computes or fakes verification results.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_authorized_document, get_current_user
from app.core.config import get_settings
from app.db.database import get_db
from app.models.document_version import DocumentVersion
from app.models.user import User
from app.storage import StorageError, StorageService, get_storage

router = APIRouter()
logger = logging.getLogger("sih26190.api.demo")

# Sibling object key that holds the pristine original bytes while the demo
# tamper is active. Deleted again on restore.
_BACKUP_SUFFIX = ".tathya-demo-original"

# Human-readable marker appended to the stored bytes. A unique token per
# tamper guarantees the SHA-256 actually changes on every invocation.
_TAMPER_MARKER = b"\n[TATHYA-DEMO] This file was intentionally modified for the integrity demonstration.\n[TATHYA-DEMO-TOKEN %s]\n"


def _require_debug() -> None:
    """Demo endpoints exist only in the development/demo environment."""
    if not get_settings().DEBUG:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")


def _current_version_or_409(db: Session, document) -> DocumentVersion:
    """Resolve the document's current version (same rule as integrity API)."""
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


def _get_or_none(storage: StorageService, object_key: str) -> bytes | None:
    try:
        return storage.get(object_key)
    except StorageError:
        return None

@router.post(
    "/{document_id}/tamper",
    summary="DEMO ONLY: modify the stored file so real verification detects it",
)
def simulate_tampering(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage),
) -> dict:
    _require_debug()
    document = get_authorized_document(document_id, current_user, db)
    version = _current_version_or_409(db, document)

    backup_key = f"{version.object_key}{_BACKUP_SUFFIX}"
    try:
        original = storage.get(version.object_key)
    except StorageError:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "File storage is unavailable"
        ) from None

    # Idempotence: if a tamper is already active, keep the FIRST pristine
    # backup so restore always returns the exact original bytes.
    if _get_or_none(storage, backup_key) is None:
        storage.save(backup_key, original, "application/octet-stream")

    tampered = original + (_TAMPER_MARKER % uuid.uuid4().hex.encode())
    storage.save(
        version.object_key, tampered, version.mime_type or "application/octet-stream"
    )
    logger.warning(
        "DEMO tampering simulated on document %s (version %s) by %s — "
        "DB hash and blockchain record intentionally left untouched",
        document.id,
        version.version_number,
        current_user.username,
    )
    return {
        "message": (
            "Demo tampering applied to the stored file. The database hash and "
            "blockchain record were NOT modified — run the existing "
            "integrity/blockchain verification to detect the change."
        ),
        "tampered": True,
    }

@router.post(
    "/{document_id}/restore",
    summary="DEMO ONLY: restore the exact original file bytes",
)
def restore_original(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage),
) -> dict:
    _require_debug()
    document = get_authorized_document(document_id, current_user, db)
    version = _current_version_or_409(db, document)

    backup_key = f"{version.object_key}{_BACKUP_SUFFIX}"
    pristine = _get_or_none(storage, backup_key)
    if pristine is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "No demo tampering is currently active for this document",
        )

    storage.save(
        version.object_key, pristine, version.mime_type or "application/octet-stream"
    )
    storage.delete(backup_key)
    logger.warning(
        "DEMO restore applied on document %s (version %s) by %s — original "
        "bytes restored exactly",
        document.id,
        version.version_number,
        current_user.username,
    )
    return {
        "message": (
            "Original file bytes restored exactly. Verification should report "
            "VERIFIED again."
        ),
        "tampered": False,
    }
