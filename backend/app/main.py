"""
SIH26190 — FastAPI application entry point.

Phase 1 (Foundation): configuration, database infrastructure, health endpoint.
Phase 2 (Authentication + RBAC): users/roles/departments models, JWT auth,
register/login/me/logout and backend-enforced role restrictions.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.audit import router as audit_router
from app.api.ai import router as ai_router
from app.api.blockchain import router as blockchain_router
from app.api.auth import router as auth_router
from app.api.cases import router as cases_router
from app.api.documents import router as documents_router
from app.api.documents import versions_router
from app.api.health import router as health_router
from app.api.rag import router as rag_router
from app.api.search import router as search_router
from app.api.users import router as users_router
from app.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sih26190")

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize the DB schema and seed baseline data (graceful if DB down)."""
    try:
        from app import seed
        from app.db.database import Base, engine
        from app.storage import get_storage

        Base.metadata.create_all(bind=engine)
        seed.seed_default_data()
        # Best-effort bucket setup (MinIO backend only) — never blocks startup.
        try:
            get_storage().ensure_bucket()
        except Exception as exc:  # noqa: BLE001 — optional service
            logger.warning("Storage bucket setup skipped (%s)", exc)
        logger.info("Database schema initialised and baseline data seeded")
    except Exception as exc:  # noqa: BLE001 — startup must never crash on DB
        logger.warning("Database unavailable at startup (%s) — schema init skipped", exc)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
    openapi_url="/openapi.json",
    docs_url="/docs",
    lifespan=lifespan,
)

# Local-development CORS so the Next.js frontend can call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/users", tags=["users"])
app.include_router(cases_router, prefix="/api/cases", tags=["cases"])
app.include_router(documents_router, prefix="/api/documents", tags=["documents"])
app.include_router(versions_router, prefix="/api/versions", tags=["documents"])
app.include_router(audit_router, prefix="/api/audit", tags=["audit"])
app.include_router(search_router, prefix="/api/search", tags=["search"])
app.include_router(rag_router, prefix="/api/retrieval", tags=["rag"])
app.include_router(ai_router, prefix="/api/ai", tags=["ai"])
app.include_router(blockchain_router, prefix="/api/blockchain", tags=["blockchain"])


@app.get("/")
def root() -> dict:
    """Simple welcome payload."""
    return {"project": settings.PROJECT_NAME, "docs": "/docs", "health": "/health"}
