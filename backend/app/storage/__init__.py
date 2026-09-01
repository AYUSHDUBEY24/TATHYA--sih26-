"""Object storage abstraction — MinIO is the real backend."""

from app.storage.base import StorageError, StorageService
from app.storage.memory import InMemoryStorage
from app.storage.minio_service import MinioStorage

# The memory backend must be a process-wide singleton so that data uploaded in
# one request is visible in the next (MinIO persists server-side by itself).
_memory_instance: InMemoryStorage | None = None


def get_storage() -> StorageService:
    """
    FastAPI dependency returning the configured storage backend.

    STORAGE_BACKEND=minio (default) → real MinIO client (lazy-connected).
    STORAGE_BACKEND=memory          → in-memory stub for tests/local demos.

    Tests override this dependency via ``app.dependency_overrides``.
    """
    global _memory_instance

    from app.core.config import get_settings

    backend = get_settings().STORAGE_BACKEND
    if backend == "memory":
        if _memory_instance is None:
            _memory_instance = InMemoryStorage()
        return _memory_instance
    if backend != "minio":
        raise RuntimeError(f"Unknown STORAGE_BACKEND: {backend!r}")
    return MinioStorage()


__all__ = [
    "StorageError",
    "StorageService",
    "InMemoryStorage",
    "MinioStorage",
    "get_storage",
]
