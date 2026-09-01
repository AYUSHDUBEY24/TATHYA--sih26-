"""User listing — ADMIN only (minimal RBAC-protected endpoint for Phase 2)."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.database import get_db
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import UserResponse
from app.schemas.case import UserBrief

router = APIRouter()


@router.get(
    "",
    response_model=list[UserResponse],
    summary="List users (ADMIN only)",
)
def list_users(
    _current_user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at)).all())


@router.get(
    "/officers",
    response_model=list[UserBrief],
    summary="List investigating officers (for case assignment; ADMIN/IO only)",
)
def list_investigating_officers(
    _current_user: User = Depends(require_roles("ADMIN", "INVESTIGATING_OFFICER")),
    db: Session = Depends(get_db),
) -> list[User]:
    return list(
        db.scalars(
            select(User)
            .join(Role, User.role_id == Role.id)
            .where(Role.name == "INVESTIGATING_OFFICER")
            .order_by(User.username)
        ).all()
    )
