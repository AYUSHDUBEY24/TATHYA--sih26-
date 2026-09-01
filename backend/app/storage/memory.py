"""
In-memory storage stub — FOR TESTS AND LOCAL DEMOS ONLY.

This is not a production storage technology; it exists so the test suite and
Docker-less local verification can exercise the full document flow. Production
always uses MinIO (STORAGE_BACKEND=minio).
"""


from app.storage.base import StorageError


class InMemoryStorage:
    """Dictionary-backed StorageService (data is lost on restart)."""

    def __init__(self) -> None:
        self._objects: dict[str, tuple[bytes, str]] = {}

    def save(self, object_key: str, data: bytes, content_type: str) -> None:
        self._objects[object_key] = (data, content_type)

    def get(self, object_key: str) -> bytes:
        try:
            return self._objects[object_key][0]
        except KeyError:
            raise StorageError(f"Object not found: {object_key}") from None

    def delete(self, object_key: str) -> None:
        self._objects.pop(object_key, None)

    def ensure_bucket(self) -> None:  # nothing to do
        return None

    # Test-only helper (not part of StorageService).
    def contains(self, object_key: str) -> bool:
        return object_key in self._objects
