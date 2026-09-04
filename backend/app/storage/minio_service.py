"""Real MinIO-backed storage service (production backend)."""

from io import BytesIO

import urllib3
from minio import Minio
from minio.error import S3Error
from urllib3.exceptions import MaxRetryError

from app.core.config import get_settings
from app.storage.base import StorageError

# Bounded timeouts + few retries: a down/unreachable MinIO must fail fast and
# surface as StorageError (-> designed 502/rollback paths), never hang the
# request thread for minutes on default unbounded retries.
_HTTP_TIMEOUT = urllib3.Timeout(connect=3.0, read=15.0)
_HTTP_RETRIES = urllib3.Retry(
    total=2,
    backoff_factor=0.2,
    status_forcelist=[500, 502, 503, 504],
)


class MinioStorage:
    """
    MinIO implementation of StorageService.

    The client is created lazily on first use so that application startup and
    tests never require a running MinIO server. Files live in a private
    bucket; access is always proxied through the backend — public URLs are
    never generated.
    """

    def __init__(self) -> None:
        self._client: Minio | None = None
        self._bucket_ready = False

    def _get_client(self) -> Minio:
        if self._client is None:
            settings = get_settings()
            self._client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
                http_client=urllib3.PoolManager(
                    timeout=_HTTP_TIMEOUT, retries=_HTTP_RETRIES
                ),
            )
        return self._client

    def ensure_bucket(self) -> None:
        if self._bucket_ready:
            return
        client = self._get_client()
        bucket = get_settings().MINIO_BUCKET
        try:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
            self._bucket_ready = True
        except S3Error as exc:
            raise StorageError(f"MinIO bucket setup failed: {exc.code}") from exc

    def save(self, object_key: str, data: bytes, content_type: str) -> None:
        try:
            self.ensure_bucket()
            self._get_client().put_object(
                get_settings().MINIO_BUCKET,
                object_key,
                BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
        except S3Error as exc:
            raise StorageError(f"MinIO save failed: {exc.code}") from exc
        except (MaxRetryError, OSError) as exc:
            raise StorageError(f"MinIO unreachable during save: {exc}") from exc

    def get(self, object_key: str) -> bytes:
        try:
            response = self._get_client().get_object(
                get_settings().MINIO_BUCKET, object_key
            )
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()
        except S3Error as exc:
            raise StorageError(f"MinIO get failed: {exc.code}") from exc
        except (MaxRetryError, OSError) as exc:
            raise StorageError(f"MinIO unreachable during get: {exc}") from exc

    def delete(self, object_key: str) -> None:
        try:
            self._get_client().remove_object(
                get_settings().MINIO_BUCKET, object_key
            )
        except S3Error as exc:
            raise StorageError(f"MinIO delete failed: {exc.code}") from exc
        except (MaxRetryError, OSError) as exc:
            raise StorageError(f"MinIO unreachable during delete: {exc}") from exc
