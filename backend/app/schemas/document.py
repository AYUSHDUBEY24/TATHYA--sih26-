"""Document + audit schemas (Pydantic v2)."""

from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.case import UserBrief

DocumentType = Literal[
    "FIR",
    "POLICE_REPORT",
    "INVESTIGATION_REPORT",
    "WITNESS_STATEMENT",
    "EVIDENCE_RECORD",
    "FORENSIC_REPORT",
    "CHARGE_SHEET",
    "COURT_FILING",
    "LEGAL_NOTICE",
    "JUDGMENT",
    "OTHER",
]

Classification = Literal["PUBLIC", "INTERNAL", "RESTRICTED", "CONFIDENTIAL"]


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    file_name: str
    document_type: str
    classification: str
    description: str | None
    status: str
    size_bytes: int
    content_type: str
    uploader: UserBrief | None
    created_at: datetime
    updated_at: datetime
    # Phase 5: current version + integrity info (null for legacy rows).
    current_version_number: int | None = None
    current_hash: str | None = None
    # Server-computed convenience flag (UI affordance only — enforcement is
    # always server-side on the DELETE endpoint).
    can_delete: bool = False


class DeletedDocumentResponse(DocumentResponse):
    """A soft-deleted document plus who deleted it and when.

    Both fields come from the real DOCUMENT_DELETED audit entry — nothing is
    inferred or fabricated.
    """

    deleted_by: str | None = None
    deleted_at: datetime | None = None


class DocumentVersionResponse(BaseModel):
    """Version metadata (internal object keys are never exposed)."""

    id: UUID
    document_id: UUID
    version_number: int
    file_name: str
    hash: str
    file_size: int
    mime_type: str
    change_note: str | None
    created_at: datetime
    uploader: UserBrief | None


class IntegrityStatus(str, Enum):
    VERIFIED = "VERIFIED"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"


class IntegrityResponse(BaseModel):
    status: IntegrityStatus
    document_id: UUID
    version: int
    stored_hash: str
    current_hash: str
    verified_at: datetime | None = None


class AuditLogResponse(BaseModel):
    """Audit trail entry (read-only projection)."""

    id: UUID
    actor_id: UUID | None = None
    actor_username: str | None = None
    action: str
    entity_type: str | None = None
    entity_id: UUID | None = None
    case_id: UUID | None = None
    ip_address: str | None = None
    result: str
    metadata: dict = {}
    created_at: datetime


# --- Blockchain (Phase 7) ---

class BlockchainStatus(str, Enum):
    NOT_ANCHORED = "NOT_ANCHORED"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"


class BlockchainVerifyStatus(str, Enum):
    VERIFIED = "VERIFIED"
    FILE_INTEGRITY_FAILURE = "FILE_INTEGRITY_FAILURE"
    BLOCKCHAIN_MISMATCH = "BLOCKCHAIN_MISMATCH"
    BLOCKCHAIN_UNAVAILABLE = "BLOCKCHAIN_UNAVAILABLE"
    NOT_ANCHORED = "NOT_ANCHORED"


class BlockchainStatusResponse(BaseModel):
    document_id: UUID
    version_id: UUID | None = None
    version_number: int | None = None
    blockchain_key: str | None = None
    status: str
    transaction_hash: str | None = None
    block_number: int | None = None
    anchored_at: datetime | None = None
    error_message: str | None = None


class BlockchainVerifyResponse(BaseModel):
    status: BlockchainVerifyStatus
    document_id: UUID
    version: int
    file_hash: str
    stored_hash: str
    blockchain_hash: str | None = None
    blockchain_key: str | None = None
    transaction_hash: str | None = None
    verified_at: datetime | None = None

