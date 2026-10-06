"""Storage abstraction for Learning Resources and Media Assets.

Supports:
- Local filesystem storage adapter (default for hermetic testing & dev)
- S3-compatible object store adapter (when configured)
- Signed URL generation, checksum computation, mime-type detection, size validation.
"""

from abc import ABC, abstractmethod
import hashlib
import mimetypes
import os
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import uuid

# Allowed file extensions and maximum upload sizes (50MB default limit)
DEFAULT_MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_MIME_PREFIXES = {
    "application/pdf",
    "application/json",
    "application/zip",
    "text/",
    "image/",
    "video/",
    "audio/",
}


class StorageFileMetadata:
    def __init__(
        self,
        storage_key: str,
        filename: str,
        size_bytes: int,
        mime_type: str,
        checksum: str,
    ):
        self.storage_key = storage_key
        self.filename = filename
        self.size_bytes = size_bytes
        self.mime_type = mime_type
        self.checksum = checksum

    def to_dict(self) -> Dict[str, Any]:
        return {
            "storage_key": self.storage_key,
            "filename": self.filename,
            "size_bytes": self.size_bytes,
            "mime_type": self.mime_type,
            "checksum": self.checksum,
        }


class StorageAdapter(ABC):
    """Abstract storage interface for object & file persistence."""

    @abstractmethod
    async def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: Optional[str] = None,
        prefix: str = "resources",
    ) -> StorageFileMetadata:
        """Stores file bytes and returns metadata."""
        pass

    @abstractmethod
    async def get_file_bytes(self, storage_key: str) -> bytes:
        """Retrieves raw file bytes."""
        pass

    @abstractmethod
    async def delete_file(self, storage_key: str) -> bool:
        """Deletes file by key."""
        pass

    @abstractmethod
    async def generate_signed_url(self, storage_key: str, expires_in_seconds: int = 3600) -> str:
        """Generates a signed or protected access URL."""
        pass


class LocalStorageAdapter(StorageAdapter):
    """Local disk storage adapter for development and offline testing."""

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path(os.environ.get("LOCAL_STORAGE_PATH", "./media_storage"))
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: Optional[str] = None,
        prefix: str = "resources",
    ) -> StorageFileMetadata:
        if len(file_bytes) > DEFAULT_MAX_UPLOAD_SIZE:
            raise ValueError(f"File size exceeds maximum allowed limit of {DEFAULT_MAX_UPLOAD_SIZE // (1024*1024)} MB")

        # Determine mime type
        mime = content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"

        # Compute SHA256 checksum
        checksum = hashlib.sha256(file_bytes).hexdigest()

        # Generate unique storage key
        ext = Path(filename).suffix
        unique_name = f"{uuid.uuid4().hex}{ext}"
        target_dir = self.base_dir / prefix
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / unique_name

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        storage_key = f"{prefix}/{unique_name}"
        return StorageFileMetadata(
            storage_key=storage_key,
            filename=filename,
            size_bytes=len(file_bytes),
            mime_type=mime,
            checksum=checksum,
        )

    async def get_file_bytes(self, storage_key: str) -> bytes:
        file_path = self.base_dir / storage_key
        if not file_path.is_file():
            raise FileNotFoundError(f"Storage file not found: {storage_key}")
        with open(file_path, "rb") as f:
            return f.read()

    async def delete_file(self, storage_key: str) -> bool:
        file_path = self.base_dir / storage_key
        if file_path.is_file():
            file_path.unlink()
            return True
        return False

    async def generate_signed_url(self, storage_key: str, expires_in_seconds: int = 3600) -> str:
        # In local storage, return an authenticated media serving endpoint
        return f"/api/v1/resources/media/{storage_key}"


class S3StorageAdapter(StorageAdapter):
    """S3-compatible object store adapter for AWS S3, MinIO, Cloudflare R2."""

    def __init__(self, bucket_name: str, endpoint_url: Optional[str] = None):
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url
        try:
            import boto3
            self._boto3 = boto3
        except ImportError:
            self._boto3 = None

    def _ensure_boto3(self):
        if self._boto3 is None:
            raise RuntimeError("boto3 package is not installed. S3StorageAdapter requires boto3.")

    async def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: Optional[str] = None,
        prefix: str = "resources",
    ) -> StorageFileMetadata:
        self._ensure_boto3()
        if len(file_bytes) > DEFAULT_MAX_UPLOAD_SIZE:
            raise ValueError(f"File size exceeds maximum allowed limit of {DEFAULT_MAX_UPLOAD_SIZE // (1024*1024)} MB")

        mime = content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
        checksum = hashlib.sha256(file_bytes).hexdigest()
        ext = Path(filename).suffix
        storage_key = f"{prefix}/{uuid.uuid4().hex}{ext}"

        client = self._boto3.client("s3", endpoint_url=self.endpoint_url)
        client.put_object(
            Bucket=self.bucket_name,
            Key=storage_key,
            Body=file_bytes,
            ContentType=mime,
            Metadata={"checksum": checksum, "original_filename": filename},
        )

        return StorageFileMetadata(
            storage_key=storage_key,
            filename=filename,
            size_bytes=len(file_bytes),
            mime_type=mime,
            checksum=checksum,
        )

    async def get_file_bytes(self, storage_key: str) -> bytes:
        self._ensure_boto3()
        client = self._boto3.client("s3", endpoint_url=self.endpoint_url)
        resp = client.get_object(Bucket=self.bucket_name, Key=storage_key)
        return resp["Body"].read()

    async def delete_file(self, storage_key: str) -> bool:
        self._ensure_boto3()
        client = self._boto3.client("s3", endpoint_url=self.endpoint_url)
        client.delete_object(Bucket=self.bucket_name, Key=storage_key)
        return True

    async def generate_signed_url(self, storage_key: str, expires_in_seconds: int = 3600) -> str:
        self._ensure_boto3()
        client = self._boto3.client("s3", endpoint_url=self.endpoint_url)
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": storage_key},
            ExpiresIn=expires_in_seconds,
        )


def get_storage_adapter() -> StorageAdapter:
    """Factory resolving configured storage adapter (defaults to local filesystem for safety)."""
    backend = os.environ.get("STORAGE_BACKEND", "local").lower()
    bucket = os.environ.get("S3_BUCKET_NAME")
    if backend == "s3" and bucket:
        return S3StorageAdapter(
            bucket_name=bucket,
            endpoint_url=os.environ.get("S3_ENDPOINT_URL"),
        )
    return LocalStorageAdapter()
