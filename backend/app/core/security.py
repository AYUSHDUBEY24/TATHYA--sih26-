"""
Security helpers: bcrypt password hashing and JWT creation/validation.

Secrets come from environment configuration only — never hardcoded, never
logged (see docs/security.md).
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import bcrypt
import jwt

from app.core.config import get_settings

settings = get_settings()

_BCRYPT_ROUNDS = 12
_TOKEN_TYPE_ACCESS = "access"


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password with bcrypt (salted, cost 12)."""
    return bcrypt.hashpw(
        plain_password.encode("utf-8"),
        bcrypt.gensalt(rounds=_BCRYPT_ROUNDS),
    ).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Constant-time bcrypt verification. Never raises on malformed hashes."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), password_hash.encode("utf-8")
        )
    except ValueError:
        return False


def create_access_token(user_id: UUID, role_name: str) -> str:
    """
    Create a signed JWT access token.

    The payload carries the user's identity (`sub`) and role (`role`) so that
    authorization decisions can be made from the token and confirmed against
    the database on every request.
    """
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role_name,
        "type": _TOKEN_TYPE_ACCESS,
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Validate signature/expiry and return the payload.

    Raises ``jwt.InvalidTokenError`` (including ``ExpiredSignatureError``)
    on any validation problem.
    """
    payload = jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
    if payload.get("type") != _TOKEN_TYPE_ACCESS:
        raise jwt.InvalidTokenError("Wrong token type")
    return payload
