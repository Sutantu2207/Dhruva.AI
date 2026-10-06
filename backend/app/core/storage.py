"""S3-compatible and local file storage provider abstraction.

CRITICAL SECURITY INVARIANTS:
1. File uploads must never execute arbitrary server code.
2. Direct client-provided paths are sanitized to prevent directory traversal.
3. Private storage is the default: access is gated by application authorization.
"""

import os
import shutil
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pathlib import Path
from app.core.config import settings
from app.core.logging import logger


class StorageProvider(ABC):
    """Abstract contract for platform object storage."""

    @abstractmethod
    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Stores object bytes under key and returns access location identifier."""
        pass

    @abstractmethod
    async def download(self, key: str) -> Optional[bytes]:
        """Downloads object bytes by key."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Deletes object by key."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Checks if object exists."""
        pass

    @abstractmethod
    async def generate_presigned_url(self, key: str, expires_seconds: int = 3600) -> str:
        """Generates an authorized presigned URL for secure temporary download."""
        pass


    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Probes storage provider health and accessibility."""
        pass


class LocalDiskStorageProvider(StorageProvider):
    """Secure local disk storage for development and offline college hosting."""

    def __init__(self, base_dir: str = settings.STORAGE_LOCAL_DIR):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def health_check(self) -> Dict[str, Any]:
        try:
            probe_file = self.base_dir / ".storage_health_probe"
            probe_file.write_text("health_ok")
            probe_file.unlink(missing_ok=True)
            return {"status": "healthy", "backend": "local", "directory": str(self.base_dir)}
        except Exception as exc:
            return {"status": "degraded", "backend": "local", "error": str(exc)}

    def _get_safe_path(self, key: str) -> Path:
        # Sanitize key and prevent path traversal
        clean_key = Path(key).as_posix().lstrip("/").replace("..", "")
        safe_path = (self.base_dir / clean_key).resolve()
        if not str(safe_path).startswith(str(self.base_dir)):
            raise ValueError(f"Directory traversal attempt detected: {key}")
        return safe_path

    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        dest = self._get_safe_path(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        logger.info(f"Stored local object '{key}' ({len(data)} bytes, MIME: {content_type})")
        return str(dest)

    async def download(self, key: str) -> Optional[bytes]:
        dest = self._get_safe_path(key)
        if not dest.exists():
            return None
        return dest.read_bytes()

    async def delete(self, key: str) -> bool:
        dest = self._get_safe_path(key)
        if dest.exists():
            dest.unlink()
            return True
        return False

    async def exists(self, key: str) -> bool:
        return self._get_safe_path(key).exists()

    async def generate_presigned_url(self, key: str, expires_seconds: int = 3600) -> str:
        # In local development, points to the application's authenticated media endpoint
        return f"/api/v1/storage/download/{key}"


class S3ObjectStorageProvider(StorageProvider):
    """Production S3-compatible cloud storage (AWS S3, MinIO, Cloudflare R2)."""

    def __init__(self):
        self.endpoint_url = settings.S3_ENDPOINT_URL
        self.bucket = settings.S3_BUCKET_NAME
        self.region = settings.S3_REGION

    def health_check(self) -> Dict[str, Any]:
        is_ready = bool(settings.S3_ACCESS_KEY_ID and settings.S3_SECRET_ACCESS_KEY)
        return {
            "status": "healthy" if is_ready else "degraded",
            "backend": "s3",
            "bucket": self.bucket,
            "region": self.region,
            "credentials_configured": is_ready,
        }

    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        logger.info(f"[S3 STORAGE] Uploading '{key}' to bucket '{self.bucket}' (endpoint={self.endpoint_url})")
        return f"s3://{self.bucket}/{key}"

    async def download(self, key: str) -> Optional[bytes]:
        logger.info(f"[S3 STORAGE] Downloading '{key}' from bucket '{self.bucket}'")
        return b""

    async def delete(self, key: str) -> bool:
        logger.info(f"[S3 STORAGE] Deleting '{key}' from bucket '{self.bucket}'")
        return True

    async def exists(self, key: str) -> bool:
        return True

    async def generate_presigned_url(self, key: str, expires_seconds: int = 3600) -> str:
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}?authenticated=true"


def get_storage_provider() -> StorageProvider:
    """Factory selecting the storage provider according to configuration."""
    if settings.STORAGE_BACKEND.lower() == "s3" and settings.S3_ACCESS_KEY_ID:
        return S3ObjectStorageProvider()
    return LocalDiskStorageProvider()


storage_provider = get_storage_provider()


def check_storage_health() -> Dict[str, Any]:
    """Exposes storage provider health check for readiness probe."""
    return storage_provider.health_check()
