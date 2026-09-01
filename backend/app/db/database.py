"""
SQLAlchemy 2.x database setup.

Phase 1 only establishes the engine/session infrastructure. Models, migrations
and repositories arrive in later phases.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# For local development we use a simple synchronous engine.
# connect_timeout keeps health checks / startup fast when PostgreSQL is
# temporarily unreachable (graceful degradation). It is a psycopg-only option,
# so it is applied only for PostgreSQL URLs.
_connect_args = {"connect_timeout": 3} if settings.DATABASE_URL.startswith("postgresql") else {}

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base class for all ORM models (added in later phases)."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
