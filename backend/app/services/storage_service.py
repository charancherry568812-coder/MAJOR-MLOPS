"""Object Storage Service (MinIO S3 API with local directory fallback)."""

from __future__ import annotations

import io
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger("StorageService")

try:
    from minio import Minio
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False


class StorageService:
    """S3-compatible Object Storage for Large Datasets and ML Model Artifacts."""

    def __init__(self):
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.bucket = os.getenv("MINIO_BUCKET", "fedbank-artifacts")
        self.local_root = Path(os.getenv("STORAGE_LOCAL_ROOT", "./storage_data")).resolve()
        self.local_root.mkdir(parents=True, exist_ok=True)
        
        self._client = None
        if MINIO_AVAILABLE:
            try:
                client = Minio(
                    self.endpoint,
                    access_key=self.access_key,
                    secret_key=self.secret_key,
                    secure=False,
                )
                if not client.bucket_exists(self.bucket):
                    client.make_bucket(self.bucket)
                self._client = client
                logger.info(f"Connected to MinIO object storage bucket: {self.bucket}")
            except Exception:
                logger.info("MinIO not reachable, using local filesystem object storage.")
                self._client = None

    def put_object(self, object_name: str, data_bytes: bytes, content_type: str = "application/octet-stream") -> str:
        """Store bytes in object storage and return URI."""
        if self._client:
            try:
                self._client.put_object(
                    self.bucket,
                    object_name,
                    io.BytesIO(data_bytes),
                    length=len(data_bytes),
                    content_type=content_type,
                )
                return f"s3://{self.bucket}/{object_name}"
            except Exception as e:
                logger.warning(f"MinIO upload error: {e}, falling back to local file storage.")

        target_path = self.local_root / object_name
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(data_bytes)
        return str(target_path)

    def get_object(self, object_name: str) -> Optional[bytes]:
        """Fetch bytes from object storage."""
        if self._client:
            try:
                resp = self._client.get_object(self.bucket, object_name)
                return resp.read()
            except Exception:
                pass

        target_path = self.local_root / object_name
        if target_path.exists():
            return target_path.read_bytes()
        return None


storage_service = StorageService()
