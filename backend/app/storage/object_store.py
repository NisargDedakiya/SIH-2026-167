from abc import ABC, abstractmethod
import io
import os
from pathlib import Path
from typing import Optional
from app.core.config import get_settings
from app.core.logging import logger
from app.storage.exceptions import StorageObjectNotFoundError

settings = get_settings()


class ObjectStore(ABC):
    """Abstract object storage interface."""

    @abstractmethod
    async def upload_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Upload raw bytes to storage key."""
        raise NotImplementedError

    @abstractmethod
    async def download_bytes(self, key: str) -> bytes:
        """Download raw bytes from storage key."""
        raise NotImplementedError

    @abstractmethod
    async def delete_object(self, key: str) -> bool:
        """Delete object at storage key."""
        raise NotImplementedError

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in storage."""
        raise NotImplementedError


class LocalObjectStore(ObjectStore):
    """Filesystem-based object store for development and offline testing."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized LocalObjectStore at {self.base_path}")

    def _resolve_path(self, key: str) -> Path:
        # Strip leading slashes to prevent root-escape
        clean_key = key.lstrip("/\\")
        target_path = (self.base_path / clean_key).resolve()
        if not str(target_path).startswith(str(self.base_path)):
            raise ValueError(f"Path traversal detected: {key}")
        return target_path

    async def upload_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        file_path = self._resolve_path(key)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(data)
        return key

    async def download_bytes(self, key: str) -> bytes:
        file_path = self._resolve_path(key)
        if not file_path.exists():
            raise StorageObjectNotFoundError(f"Storage key not found: {key}", object_key=key)
        with open(file_path, "rb") as f:
            return f.read()

    async def delete_object(self, key: str) -> bool:
        file_path = self._resolve_path(key)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    async def exists(self, key: str) -> bool:
        return self._resolve_path(key).exists()


class MinIOObjectStore(ObjectStore):
    """MinIO / S3-compatible object storage provider."""

    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str, secure: bool = False):
        from minio import Minio
        self.endpoint = endpoint
        self.bucket = bucket
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info(f"Created MinIO bucket: {self.bucket}")
        except Exception as e:
            logger.warning(f"Could not connect to MinIO during startup ({e}). Operations may fail if MinIO is offline.")

    async def upload_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        stream = io.BytesIO(data)
        self.client.put_object(
            bucket_name=self.bucket,
            object_name=key,
            data=stream,
            length=len(data),
            content_type=content_type
        )
        return key

    async def download_bytes(self, key: str) -> bytes:
        try:
            response = self.client.get_object(self.bucket, key)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()
        except Exception as e:
            err_str = str(e)
            if "NoSuchKey" in err_str or getattr(e, "code", "") in ("NoSuchKey", "ResourceNotFound"):
                raise StorageObjectNotFoundError(f"Storage key not found: {key}", object_key=key) from e
            raise

    async def delete_object(self, key: str) -> bool:
        self.client.remove_object(self.bucket, key)
        return True

    async def exists(self, key: str) -> bool:
        try:
            self.client.stat_object(self.bucket, key)
            return True
        except Exception:
            return False


_global_store: Optional[ObjectStore] = None

def get_object_store() -> ObjectStore:
    """Singleton getter for configured object store."""
    global _global_store
    if _global_store is not None:
        return _global_store

    if settings.STORAGE_BACKEND.lower() == "minio":
        try:
            _global_store = MinIOObjectStore(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                bucket=settings.MINIO_BUCKET,
                secure=settings.MINIO_SECURE
            )
            return _global_store
        except Exception as e:
            logger.warning(f"MinIO failed initialization: {e}. Falling back to LocalObjectStore.")

    _global_store = LocalObjectStore(base_path=settings.LOCAL_STORAGE_PATH)
    return _global_store
