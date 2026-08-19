import os
import shutil
import uuid
import tempfile
from abc import ABC, abstractmethod
from typing import Optional
from backend.app.config import settings

class StorageBackend(ABC):
    """
    Abstract storage backend interface.
    Supports both local file system and Cloudflare R2 / AWS S3.
    Swapping storage implementations requires only configuring STORAGE_TYPE in settings.
    """

    @abstractmethod
    def save(self, data: bytes, relative_path: str, content_type: str = "application/octet-stream") -> str:
        """Save binary data and return accessible URL/path."""
        pass

    @abstractmethod
    def save_atomic(self, data: bytes, relative_path: str, content_type: str = "application/json") -> str:
        """
        Save binary data atomically so readers never observe a partial or corrupted state.
        """
        pass

    @abstractmethod
    def get(self, relative_path: str) -> Optional[bytes]:
        """Read binary data for a given relative path."""
        pass

    @abstractmethod
    def exists(self, relative_path: str) -> bool:
        """Check if a file exists."""
        pass

    @abstractmethod
    def delete(self, relative_path: str) -> bool:
        """Delete a file."""
        pass

    @abstractmethod
    def get_url(self, relative_path: str) -> str:
        """Return the public or API URL to access the file."""
        pass


class LocalStorageBackend(StorageBackend):
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = os.path.abspath(base_dir or settings.LOCAL_STORAGE_DIR)
        os.makedirs(self.base_dir, exist_ok=True)

    def _resolve_path(self, relative_path: str) -> str:
        clean_rel = relative_path.lstrip("/").replace("\\", "/")
        full_path = os.path.abspath(os.path.join(self.base_dir, clean_rel))
        # Prevent directory traversal
        if not full_path.startswith(self.base_dir):
            raise ValueError(f"Path traversal detected for '{relative_path}'")
        return full_path

    def save(self, data: bytes, relative_path: str, content_type: str = "application/octet-stream") -> str:
        full_path = self._resolve_path(relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(data)
        return self.get_url(relative_path)

    def save_atomic(self, data: bytes, relative_path: str, content_type: str = "application/json") -> str:
        """
        Atomic write implementation for POSIX / local storage.
        1. Writes to a temporary file in the same directory/partition.
        2. Flushes and executes fsync to guarantee data is on disk.
        3. Uses atomic os.replace() to rename temp file to target.
        If process crashes at any point prior to os.replace, the active file remains untouched.
        """
        full_path = self._resolve_path(relative_path)
        dir_name = os.path.dirname(full_path)
        os.makedirs(dir_name, exist_ok=True)

        temp_filename = f".tmp_{uuid.uuid4().hex}_{os.path.basename(full_path)}"
        temp_path = os.path.join(dir_name, temp_filename)

        try:
            with open(temp_path, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, full_path)
        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

        return self.get_url(relative_path)

    def get(self, relative_path: str) -> Optional[bytes]:
        try:
            full_path = self._resolve_path(relative_path)
            if not os.path.exists(full_path):
                return None
            with open(full_path, "rb") as f:
                return f.read()
        except Exception:
            return None

    def exists(self, relative_path: str) -> bool:
        try:
            full_path = self._resolve_path(relative_path)
            return os.path.exists(full_path)
        except Exception:
            return False

    def delete(self, relative_path: str) -> bool:
        try:
            full_path = self._resolve_path(relative_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
            return False
        except Exception:
            return False

    def get_url(self, relative_path: str) -> str:
        clean_rel = relative_path.lstrip("/").replace("\\", "/")
        return f"/api/storage/{clean_rel}"


class R2StorageBackend(StorageBackend):
    """
    Cloudflare R2 / S3-compatible storage backend.
    In R2 / S3, PUT operations are inherently atomic (read-after-write consistency).
    """
    def __init__(self):
        import boto3
        from botocore.config import Config

        self.bucket = settings.S3_BUCKET_NAME
        self.public_base_url = settings.S3_PUBLIC_BASE_URL.rstrip("/")
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL or None,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY or None,
            region_name=settings.S3_REGION_NAME or "auto",
            config=Config(signature_version="s3v4")
        )

    def save(self, data: bytes, relative_path: str, content_type: str = "application/octet-stream") -> str:
        clean_rel = relative_path.lstrip("/").replace("\\", "/")
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=clean_rel,
            Body=data,
            ContentType=content_type
        )
        return self.get_url(clean_rel)

    def save_atomic(self, data: bytes, relative_path: str, content_type: str = "application/json") -> str:
        # S3 / R2 PUT operations are natively atomic
        return self.save(data, relative_path, content_type)

    def get(self, relative_path: str) -> Optional[bytes]:
        clean_rel = relative_path.lstrip("/").replace("\\", "/")
        try:
            resp = self.s3_client.get_object(Bucket=self.bucket, Key=clean_rel)
            return resp["Body"].read()
        except Exception:
            return None

    def exists(self, relative_path: str) -> bool:
        clean_rel = relative_path.lstrip("/").replace("\\", "/")
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=clean_rel)
            return True
        except Exception:
            return False

    def delete(self, relative_path: str) -> bool:
        clean_rel = relative_path.lstrip("/").replace("\\", "/")
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=clean_rel)
            return True
        except Exception:
            return False

    def get_url(self, relative_path: str) -> str:
        clean_rel = relative_path.lstrip("/").replace("\\", "/")
        if self.public_base_url:
            return f"{self.public_base_url}/{clean_rel}"
        return f"https://{self.bucket}.r2.cloudflarestorage.com/{clean_rel}"


_storage_instance: Optional[StorageBackend] = None

def get_storage() -> StorageBackend:
    global _storage_instance
    if _storage_instance is None:
        if settings.STORAGE_TYPE in ["r2", "s3"]:
            _storage_instance = R2StorageBackend()
        else:
            _storage_instance = LocalStorageBackend()
    return _storage_instance
