"""Evidence / chain-of-custody schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

ALLOWED_ASSET_TYPES = (
    "LAPTOP",
    "MOBILE_PHONE",
    "USB_DRIVE",
    "DOCUMENT",
    "STORAGE_DEVICE",
    "OTHER",
)
ALLOWED_ASSET_STATUSES = (
    "REGISTERED",
    "IN_CUSTODY",
    "UNDER_EXAMINATION",
    "STORED",
    "RELEASED",
)
ALLOWED_TRANSFER_ACTIONS = (
    "REGISTERED",
    "COLLECTED",
    "TRANSFERRED",
    "EXAMINED",
    "STORED",
    "RELEASED",
)


class EvidenceAssetCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)
    asset_type: str
    description: str | None = Field(default=None, max_length=2000)
    status: str = "REGISTERED"
    current_holder: str = Field(min_length=1, max_length=255)


class AssetTransferCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    action: str
    from_party: str | None = Field(default=None, max_length=255)
    to_party: str | None = Field(default=None, max_length=255)
    purpose: str | None = Field(default=None, max_length=500)
    # Optional explicit event time (defaults to now server-side).
    occurred_at: datetime | None = None


class AssetTransferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    action: str
    from_party: str | None
    to_party: str | None
    purpose: str | None
    occurred_at: datetime
    actor_id: uuid.UUID
    actor_name: str


class EvidenceAssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    asset_tag: str
    name: str
    asset_type: str
    description: str | None
    status: str
    current_holder: str
    registered_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class EvidenceAssetDetail(EvidenceAssetOut):
    transfers: list[AssetTransferOut]


class ChainOfCustodyResponse(BaseModel):
    asset: EvidenceAssetOut
    case_number: str
    case_title: str
    transfers: list[AssetTransferOut]
