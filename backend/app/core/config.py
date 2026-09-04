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

    # --- Blockchain (Phase 7) — local Hardhat network ONLY ---
    # All secrets via env vars. Defaults target a local Hardhat node started
    # with `npx hardhat node` (the well-known first account private key).
    BLOCKCHAIN_RPC_URL: str = "http://127.0.0.1:8545"
    BLOCKCHAIN_CHAIN_ID: int = 31337
    BLOCKCHAIN_CONTRACT_ADDRESS: str = ""
    BLOCKCHAIN_PRIVATE_KEY: str = (
        "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    )
    # When False, blockchain anchoring is skipped entirely (docs remain usable).
    BLOCKCHAIN_ENABLED: bool = True

    # --- Embeddings / RAG (Phase 9A) ---
    # "fallback" uses the deterministic offline embedding (no API key needed).
    EMBEDDINGS_PROVIDER: str = "fallback"

    # --- LLM / answer synthesis (Phase 9B) ---
    # LLM_PROVIDER: "fallback" (no external calls) or "openai"/"openai-compatible"
    # (any OpenAI-compatible /chat/completions endpoint). When no real provider
    # is configured the assistant reports "provider unavailable" instead of
    # fabricating answers.
    LLM_PROVIDER: str = "fallback"
    OPENAI_API_KEY: str | None = None
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_API_BASE: str = "https://api.openai.com/v1"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
