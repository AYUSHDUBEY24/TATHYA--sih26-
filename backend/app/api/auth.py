"""Authentication endpoints: register, login, me, logout."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.audit_service import AuditAction, AuditResult, client_ip, log_audit

router = APIRouter()

# Single generic message for any credential failure — never reveals whether
# the email or the password was wrong (docs/security.md).
GENERIC_CREDENTIALS_ERROR = "Incorrect email or password."


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user (prototype: role selectable for RBAC demo)",
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    if db.scalar(select(User).where(User.email == payload.email.lower())) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    if db.scalar(select(User).where(User.username == payload.username)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")

    role = db.scalar(select(Role).where(Role.name == payload.role))
    if role is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown role")

    user = User(
        email=payload.email.lower(),
        username=payload.username,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role_id=role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse, summary="Login and receive a JWT")
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if (
        user is None
        or not verify_password(payload.password, user.password_hash)
        or not user.is_active
    ):
        # Audit the failed attempt (never log the password itself).
        log_audit(
            db,
            AuditAction.LOGIN_FAILED,
            actor_id=user.id if user else None,
            entity_type="USER",
            entity_id=user.id if user else None,
            result=AuditResult.FAILURE,
            ip_address=client_ip(request),
            data={"email": payload.email},
            commit=True,  # failure path — nothing else is committed
        )
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, GENERIC_CREDENTIALS_ERROR)

    token = create_access_token(user.id, user.role.name)
    log_audit(
        db,
        AuditAction.LOGIN,
        actor=user,
        entity_type="USER",
        entity_id=user.id,
        ip_address=client_ip(request),
        commit=True,  # login writes nothing else
    )
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse, summary="Current authenticated user")
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/logout", response_model=MessageResponse, summary="Logout (client discards JWT)")
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    # JWTs are stateless — there is no server session to destroy. The client
    # discards the token. (Token revocation/blacklisting is out of scope for
    # this prototype phase.)
    log_audit(
        db,
        AuditAction.LOGOUT,
        actor=current_user,
        entity_type="USER",
        entity_id=current_user.id,
        ip_address=client_ip(request),
        commit=True,
    )
    return MessageResponse(message="Successfully logged out")
