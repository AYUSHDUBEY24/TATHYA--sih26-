"""
Application configuration.

All settings are loaded from environment variables (or a `.env` file). A `.env`
in the backend directory or in the repository root is picked up automatically.
Never hardcode secrets in code — see `.env.example` at the repository root.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    PROJECT_NAME: str = "SIH26190 Secure Document Management System"
    DEBUG: bool = True

    # --- CORS (frontend origin) ---
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # --- PostgreSQL ---
    # SQLAlchemy connection string. Defaults match docker/docker-compose.yml.
    # For quick local development without Docker you may use SQLite:
    #   DATABASE_URL=sqlite:///./sih_dev.db
    DATABASE_URL: str = "postgresql+psycopg://sih:sih_local_dev@localhost:5432/sih26190"

    # --- Authentication / JWT (Phase 2) ---
    # MUST be overridden with a real random secret in any non-local environment.
    # (>=32 bytes so HS256 has a proper HMAC key length.)
    SECRET_KEY: str = (
        "change-me-before-phase-2-0123456789abcdef-LOCAL-DEV-ONLY"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Object storage (Phase 4) ---
    # "minio" is the real backend; "memory" is an in-memory stub intended ONLY
    # for tests / quick local demos without Docker. Never use "memory" beyond
    # local development.
    STORAGE_BACKEND: str = "minio"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "sih_local_dev"
    MINIO_BUCKET: str = "sih26190-documents"
    MINIO_SECURE: bool = False

    # --- Upload limits (Phase 4) ---
    MAX_UPLOAD_SIZE_MB: int = 50


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
