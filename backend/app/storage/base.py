"""Storage service interface."""

from typing import Protocol


class StorageError(Exception):
    """Raised when the storage backend cannot complete an operation."""


class StorageService(Protocol):
    """Minimal object-storage interface used by the documents feature."""

    def save(self, object_key: str, data: bytes, content_type: str) -> None:
        """Store an object. Raises StorageError on failure."""
        ...

    def get(self, object_key: str) -> bytes:
        """Retrieve an object's bytes. Raises StorageError if unavailable."""
        ...

    def delete(self, object_key: str) -> None:
        """Remove an object. Raises StorageError on failure."""
        ...

    def ensure_bucket(self) -> None:
        """Create the target bucket if it does not exist (idempotent)."""
        ...
