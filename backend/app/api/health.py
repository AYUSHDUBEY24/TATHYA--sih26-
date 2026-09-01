"""Health check endpoint."""

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.db.database import engine

router = APIRouter()


@router.get("/health")
def health() -> dict:
    """
    Liveness check for the API.

    Also attempts a trivial database round-trip so that, once
    `docker compose up` is running, you can immediately see whether
    PostgreSQL is reachable. A database problem never fails the overall
    health check (graceful degradation).
    """
    settings = get_settings()

    db_status = "unavailable"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:  # noqa: BLE001 — health check must never crash
        pass

    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "debug": settings.DEBUG,
        "database": db_status,
    }
