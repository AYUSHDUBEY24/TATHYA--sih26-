"""Case management schemas (Pydantic v2)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Documented case statuses — intentionally simple, no extra workflow states.
CaseStatus = Literal[
    "OPEN",
    "UNDER_INVESTIGATION",
    "UNDER_REVIEW",
    "CHARGESHEET_FILED",
    "COURT_STAGE",
    "CLOSED",
    "ARCHIVED",
]


class CaseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str | None = None
    crime_type: str = Field(min_length=2, max_length=100)
    police_station: str = Field(min_length=2, max_length=150)
    status: CaseStatus = "OPEN"
    # Optional: assign an investigating officer at creation time. Must reference
    # a user with the INVESTIGATING_OFFICER role.
    assigned_io_id: UUID | None = None
    # Optional explicit case number (e.g. imported case); auto-generated if omitted.
    case_number: str | None = Field(default=None, min_length=3, max_length=30)


class CaseUpdate(BaseModel):
    """Partial update — only provided fields are changed."""

    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = None
    crime_type: str | None = Field(default=None, min_length=2, max_length=100)
    police_station: str | None = Field(default=None, min_length=2, max_length=150)
    status: CaseStatus | None = None
    # Explicitly send null to unassign the IO; omit to leave unchanged.
    assigned_io_id: UUID | None = None


class UserBrief(BaseModel):
    """Minimal public user info (no email exposure in case payloads)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    full_name: str | None


class CaseMemberOut(BaseModel):
    id: UUID
    user_id: UUID
    username: str
    full_name: str | None
    role_in_case: str
    joined_at: datetime


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_number: str
    title: str
    description: str | None
    crime_type: str
    police_station: str
    status: str
    created_by: UUID
    assigned_io: UserBrief | None
    created_at: datetime
    updated_at: datetime


class CaseDetailResponse(CaseResponse):
    members: list[CaseMemberOut]
    # Server-computed flag the frontend may use for UI affordances only —
    # all authorization is enforced server-side regardless.
    can_manage: bool


class CaseMemberAdd(BaseModel):
    # Identify the new member either by user_id or by email.
    user_id: UUID | None = None
    email: EmailStr | None = None
    role_in_case: str | None = Field(default=None, min_length=2, max_length=50)
