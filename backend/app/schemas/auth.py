"""Authentication schemas (Pydantic v2)."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(
        min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$"
    )
    password: str = Field(min_length=8, max_length=72)  # bcrypt 72-byte limit
    full_name: str | None = Field(default=None, max_length=255)
    # NOTE (prototype): role is selectable at registration so the RBAC demo
    # (different roles, restricted access) can be shown without an admin UI.
    # In a real deployment only ADMIN would assign roles.
    role: str = "INVESTIGATING_OFFICER"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    username: str
    full_name: str | None
    is_active: bool
    role: RoleOut
    department: DepartmentOut | None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    message: str
