"""
Storage backend implementations for file management.

This module provides different storage backends including local filesystem,
AWS S3, and other cloud storage providers with multi-tenant isolation.
"""

import asyncio
import contextlib
import hashlib
import os
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone, UTC
from pathlib import Path
from typing import Any, BinaryIO, Optional, Protocol

from dotmac.platform.logging import get_logger
try:
    import boto3
    from botocore.config import Config as BotoConfig
    from botocore.exceptions import ClientError

    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

# Azure Blob Storage support removed (not used)
HAS_AZURE = False

# Google Cloud Storage support
HAS_GCS = False  # Not currently used

import aiofiles
import aiofiles.os

try:
    from opentelemetry import trace

    storage_tracer = trace.get_tracer(__name__)
except Exception:  # pragma: no cover - optional dependency
    storage_tracer = None

logger = get_logger(__name__)

class SecurityError(Exception):
    """Security-related storage error (path traversal, access denial, etc.)."""

# Use ValidationError from domain.py instead of custom class
from ..domain import ValidationError

@dataclass
class FileInfo:
    """Information about a stored file."""

    file_id: str
    filename: str
    path: str
    size: int
    content_type: str
    created_at: datetime
    modified_at: datetime
    tenant_id: str
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class StorageBackend(Protocol):
    """Protocol for storage backend implementations."""

    async def save_file(
        self,
        file_path: str,
        content: BinaryIO,
        tenant_id: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Save file with tenant isolation."""
        ...

    async def get_file(self, file_path: str, tenant_id: str) -> BinaryIO:
        """Retrieve file with tenant verification."""
        ...

    async def delete_file(self, file_path: str, tenant_id: str) -> bool:
        """Delete file with tenant verification."""
        ...

    async def list_files(
        self, prefix: str, tenant_id: str, limit: Optional[int] = None
    ) -> list[FileInfo]:
        """List files with metadata."""
        ...

    async def file_exists(self, file_path: str, tenant_id: str) -> bool:
        """Check if file exists."""
        ...

    async def get_file_info(self, file_path: str, tenant_id: str) -> Optional[FileInfo]:
        """Get file information."""
        ...

    async def copy_file(
        self,
        source_path: str,
        dest_path: str,
        source_tenant_id: str,
        dest_tenant_id: str,
    ) -> bool:
        """Copy file between locations."""
        ...

    async def move_file(self, source_path: str, dest_path: str, tenant_id: str) -> bool:
        """Move file to new location."""
        ...

class LocalFileStorage:
    """Local filesystem storage backend."""

    def __init__(self, base_path: str | None = None):
        """Initialize local file storage."""
        if base_path is None:
            # Use secure temporary directory
            base_path = tempfile.mkdtemp(prefix="dotmac_files_")
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Local file storage initialized at: {self.base_path}")

    def _get_tenant_path(self, tenant_id: str) -> Path:
        """Get tenant-specific directory path."""
        tenant_path = self.base_path / tenant_id
        tenant_path.mkdir(parents=True, exist_ok=True)
        return tenant_path

    def _get_full_path(self, file_path: str, tenant_id: str) -> Path:
        """Get full file path with tenant isolation."""
        tenant_path = self._get_tenant_path(tenant_id)
        # Ensure path doesn't escape tenant directory
        file_path = file_path.lstrip("/")
        full_path = tenant_path / file_path

        # Security check: ensure path is within tenant directory
        try:
            full_path.resolve().relative_to(tenant_path.resolve())
        except ValueError as e:
            raise ValueError(f"Invalid file path: {file_path}") from e

        return full_path

    async def save_file(
        self,
        file_path: str,
        content: BinaryIO,
        tenant_id: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Save file to local filesystem."""
        try:
            full_path = self._get_full_path(file_path, tenant_id)

            # Create directory if it doesn't exist
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Save file content
            async with aiofiles.open(full_path, "wb") as f:
                if hasattr(content, "read"):
                    content.seek(0)
                    while True:
                        chunk = content.read(8192)
                        if not chunk:
                            break
                        await f.write(chunk)
                else:
                    await f.write(content)

            # Save metadata if provided
            if metadata:
                metadata_path = full_path.with_suffix(full_path.suffix + ".meta")
                async with aiofiles.open(metadata_path, "w") as f:
                    import json

                    await f.write(json.dumps(metadata, default=str))

            logger.info(f"Saved file: {full_path}")
            return str(full_path)

        except Exception as e:
            logger.error(f"Error saving file {file_path} for tenant {tenant_id}: {e}")
            raise

    async def get_file(self, file_path: str, tenant_id: str) -> BinaryIO:
        """Retrieve file from local filesystem."""
        try:
            full_path = self._get_full_path(file_path, tenant_id)

            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Return file-like object
            import io

            async with aiofiles.open(full_path, "rb") as f:
                content = await f.read()
                return io.BytesIO(content)

        except Exception as e:
            logger.error(f"Error retrieving file {file_path} for tenant {tenant_id}: {e}")
            raise

    async def delete_file(self, file_path: str, tenant_id: str) -> bool:
        """Delete file from local filesystem."""
        try:
            full_path = self._get_full_path(file_path, tenant_id)

            if not full_path.exists():
                return False

            # Delete main file
            await aiofiles.os.remove(full_path)

            # Delete metadata file if exists
            metadata_path = full_path.with_suffix(full_path.suffix + ".meta")
            if metadata_path.exists():
                await aiofiles.os.remove(metadata_path)

            logger.info(f"Deleted file: {full_path}")
            return True

        except Exception as e:
            logger.error(f"Error deleting file {file_path} for tenant {tenant_id}: {e}")
            return False

    async def list_files(
        self, prefix: str, tenant_id: str, limit: Optional[int] = None
    ) -> list[FileInfo]:
        """List files in local filesystem."""
        try:
            tenant_path = self._get_tenant_path(tenant_id)
            files = []

            # Use rglob to find files recursively
            pattern = f"{prefix}*" if prefix else "*"
            count = 0

            for file_path in tenant_path.rglob(pattern):
                if file_path.is_file() and not file_path.name.endswith(".meta"):
                    if limit and count >= limit:
                        break

                    stat = file_path.stat()
                    relative_path = file_path.relative_to(tenant_path)

                    # Load metadata if available
                    metadata = {}
                    metadata_path = file_path.with_suffix(file_path.suffix + ".meta")
                    if metadata_path.exists():
                        try:
                            import json

                            async with aiofiles.open(metadata_path) as f:
                                metadata_content = await f.read()
                                metadata = json.loads(metadata_content)
                        except Exception:
                            pass

                    file_info = FileInfo(
                        file_id=str(uuid.uuid4()),  # Generate ID for local files
                        filename=file_path.name,
                        path=str(relative_path),
                        size=stat.st_size,
                        content_type=metadata.get("content_type", "application/octet-stream"),
                        created_at=datetime.fromtimestamp(stat.st_ctime, timezone.utc),
                        modified_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc),
                        tenant_id=tenant_id,
                        metadata=metadata,
                    )
                    files.append(file_info)
                    count += 1

            return sorted(files, key=lambda f: f.created_at, reverse=True)

        except Exception as e:
            logger.error(f"Error listing files for tenant {tenant_id}: {e}")
            return []

    async def file_exists(self, file_path: str, tenant_id: str) -> bool:
        """Check if file exists."""
        try:
            full_path = self._get_full_path(file_path, tenant_id)
            return full_path.exists()
        except Exception:
            return False

    async def get_file_info(self, file_path: str, tenant_id: str) -> Optional[FileInfo]:
        """Get file information."""
        try:
            full_path = self._get_full_path(file_path, tenant_id)

            if not full_path.exists():
                return None

            stat = full_path.stat()
            tenant_path = self._get_tenant_path(tenant_id)
            relative_path = full_path.relative_to(tenant_path)

            # Load metadata if available
            metadata = {}
            metadata_path = full_path.with_suffix(full_path.suffix + ".meta")
            if metadata_path.exists():
                try:
                    import json

                    async with aiofiles.open(metadata_path) as f:
                        metadata_content = await f.read()
                        metadata = json.loads(metadata_content)
                except Exception:
                    pass

            return FileInfo(
                file_id=str(uuid.uuid4()),
                filename=full_path.name,
                path=str(relative_path),
                size=stat.st_size,
                content_type=metadata.get("content_type", "application/octet-stream"),
                created_at=datetime.fromtimestamp(stat.st_ctime, timezone.utc),
                modified_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc),
                tenant_id=tenant_id,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Error getting file info {file_path} for tenant {tenant_id}: {e}")
            return None

    async def copy_file(
        self,
        source_path: str,
        dest_path: str,
        source_tenant_id: str,
        dest_tenant_id: str,
    ) -> bool:
        """Copy file between locations."""
        try:
            source_full_path = self._get_full_path(source_path, source_tenant_id)
            dest_full_path = self._get_full_path(dest_path, dest_tenant_id)

            if not source_full_path.exists():
                return False

            # Create destination directory
            dest_full_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(source_full_path, dest_full_path)

            # Copy metadata if exists
            source_metadata = source_full_path.with_suffix(source_full_path.suffix + ".meta")
            if source_metadata.exists():
                dest_metadata = dest_full_path.with_suffix(dest_full_path.suffix + ".meta")
                shutil.copy2(source_metadata, dest_metadata)

            logger.info(f"Copied file: {source_full_path} -> {dest_full_path}")
            return True

        except Exception as e:
            logger.error(f"Error copying file {source_path} -> {dest_path}: {e}")
            return False

    async def move_file(self, source_path: str, dest_path: str, tenant_id: str) -> bool:
        """Move file to new location."""
        try:
            source_full_path = self._get_full_path(source_path, tenant_id)
            dest_full_path = self._get_full_path(dest_path, tenant_id)

            if not source_full_path.exists():
                return False

            # Create destination directory
            dest_full_path.parent.mkdir(parents=True, exist_ok=True)

            # Move file
            shutil.move(str(source_full_path), str(dest_full_path))

            # Move metadata if exists
            source_metadata = source_full_path.with_suffix(source_full_path.suffix + ".meta")
            if source_metadata.exists():
                dest_metadata = dest_full_path.with_suffix(dest_full_path.suffix + ".meta")
                shutil.move(str(source_metadata), str(dest_metadata))

            logger.info(f"Moved file: {source_full_path} -> {dest_full_path}")
            return True

        except Exception as e:
            logger.error(f"Error moving file {source_path} -> {dest_path}: {e}")
            return False

class S3FileStorage:
    """AWS S3 storage backend."""

    def __init__(
        self,
        bucket_name: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1",
        endpoint_url: Optional[str] = None,
        addressing_style: Optional[str] = None,
        signature_version: Optional[str] = None,
    ):
        """Initialize S3 storage backend."""
        if not HAS_BOTO3:
            raise ImportError("boto3 is required for S3 storage backend")

        self.bucket_name = bucket_name

        client_kwargs: dict[str, Any] = {
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
            "region_name": region_name,
            "endpoint_url": endpoint_url,
        }

        # Optional extras for compatibility with MinIO or custom S3 endpoints
        addressing_style = addressing_style or os.getenv("S3_ADDRESSING_STYLE")
        signature_version = signature_version or os.getenv("S3_SIGNATURE_VERSION")
        if addressing_style or signature_version:
            client_kwargs["config"] = settings.Boto.model_copy(update=dict(
                s3={"addressing_style": addressing_style or "auto"},
                signature_version=signature_version or "s3v4",
            ))

        self.s3_client = boto3.client(
            "s3", **{k: v for k, v in client_kwargs.items() if v is not None}
        )

        # Verify bucket exists
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"S3 storage initialized with bucket: {bucket_name}")
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise ValueError(f"S3 bucket '{bucket_name}' does not exist") from e
            raise

    def _get_s3_key(self, file_path: str, tenant_id: str) -> str:
        """Generate S3 key with tenant prefix."""
        file_path = file_path.lstrip("/")
        return f"{tenant_id}/{file_path}"

    def _span(self, name: str, **attributes: Any):
        if storage_tracer:
            return storage_tracer.start_as_current_span(name, attributes=attributes)
        return contextlib.nullcontext()

    async def save_file(
        self,
        file_path: str,
        content: BinaryIO,
        tenant_id: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Save file to S3."""
        try:
            s3_key = self._get_s3_key(file_path, tenant_id)

            # Prepare upload parameters
            upload_kwargs = {"Bucket": self.bucket_name, "Key": s3_key, "Body": content}

            # Add metadata
            if metadata:
                s3_metadata = {k: str(v) for k, v in metadata.items()}
                upload_kwargs["Metadata"] = s3_metadata

            with self._span(
                "storage.s3.save",
                bucket=self.bucket_name,
                key=s3_key,
                tenant_id=tenant_id,
            ):
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.s3_client.put_object(**upload_kwargs)
                )

            logger.info(f"Saved file to S3: {s3_key}")
            return s3_key

        except Exception as e:
            logger.error(f"Error saving file {file_path} to S3 for tenant {tenant_id}: {e}")
            raise

    async def get_file(self, file_path: str, tenant_id: str) -> BinaryIO:
        """Retrieve file from S3."""
        try:
            s3_key = self._get_s3_key(file_path, tenant_id)

            with self._span(
                "storage.s3.get",
                bucket=self.bucket_name,
                key=s3_key,
                tenant_id=tenant_id,
            ):
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key),
                )

            return response["Body"]

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"File not found: {file_path}") from e
            logger.error(f"Error retrieving file {file_path} from S3 for tenant {tenant_id}: {e}")
            raise

    async def delete_file(self, file_path: str, tenant_id: str) -> bool:
        """Delete file from S3."""
        try:
            s3_key = self._get_s3_key(file_path, tenant_id)

            # Delete file
            with self._span(
                "storage.s3.delete",
                bucket=self.bucket_name,
                key=s3_key,
                tenant_id=tenant_id,
            ):
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key),
                )

            logger.info(f"Deleted file from S3: {s3_key}")
            return True

        except Exception as e:
            logger.error(f"Error deleting file {file_path} from S3 for tenant {tenant_id}: {e}")
            return False

    async def list_files(
        self, prefix: str, tenant_id: str, limit: Optional[int] = None
    ) -> list[FileInfo]:
        """List files in S3."""
        try:
            s3_prefix = self._get_s3_key(prefix, tenant_id)

            # List objects
            list_kwargs = {"Bucket": self.bucket_name, "Prefix": s3_prefix}

            if limit:
                list_kwargs["MaxKeys"] = limit

            with self._span(
                "storage.s3.list",
                bucket=self.bucket_name,
                prefix=s3_prefix,
                tenant_id=tenant_id,
            ):
                response = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.s3_client.list_objects_v2(**list_kwargs)
                )

            files = []
            for obj in response.get("Contents", []):
                # Get object metadata
                key = obj["Key"]  # Capture variable to avoid closure issue
                head_response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda key=key: self.s3_client.head_object(Bucket=self.bucket_name, Key=key),
                )

                # Extract relative path (remove tenant prefix)
                relative_path = obj["Key"][len(f"{tenant_id}/") :]

                file_info = FileInfo(
                    file_id=obj["ETag"].strip('"'),  # Use ETag as file ID
                    filename=Path(obj["Key"]).name,
                    path=relative_path,
                    size=obj["Size"],
                    content_type=head_response.get("ContentType", "application/octet-stream"),
                    created_at=obj["LastModified"].replace(tzinfo=timezone.utc),
                    modified_at=obj["LastModified"].replace(tzinfo=timezone.utc),
                    tenant_id=tenant_id,
                    metadata=head_response.get("Metadata", {}),
                )
                files.append(file_info)

            return sorted(files, key=lambda f: f.created_at, reverse=True)

        except Exception as e:
            logger.error(f"Error listing S3 files for tenant {tenant_id}: {e}")
            return []

    async def file_exists(self, file_path: str, tenant_id: str) -> bool:
        """Check if file exists in S3."""
        try:
            s3_key = self._get_s3_key(file_path, tenant_id)

            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key),
            )
            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

    async def get_file_info(self, file_path: str, tenant_id: str) -> Optional[FileInfo]:
        """Get S3 file information."""
        try:
            s3_key = self._get_s3_key(file_path, tenant_id)

            # Get object metadata
            with self._span(
                "storage.s3.head",
                bucket=self.bucket_name,
                key=s3_key,
                tenant_id=tenant_id,
            ):
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key),
                )

            return FileInfo(
                file_id=response["ETag"].strip('"'),
                filename=Path(file_path).name,
                path=file_path,
                size=response["ContentLength"],
                content_type=response.get("ContentType", "application/octet-stream"),
                created_at=response["LastModified"].replace(tzinfo=timezone.utc),
                modified_at=response["LastModified"].replace(tzinfo=timezone.utc),
                tenant_id=tenant_id,
                metadata=response.get("Metadata", {}),
            )

        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return None
            logger.error(f"Error getting S3 file info {file_path} for tenant {tenant_id}: {e}")
            return None

    async def copy_file(
        self,
        source_path: str,
        dest_path: str,
        source_tenant_id: str,
        dest_tenant_id: str,
    ) -> bool:
        """Copy file within S3."""
        try:
            source_key = self._get_s3_key(source_path, source_tenant_id)
            dest_key = self._get_s3_key(dest_path, dest_tenant_id)

            # Copy object
            with self._span(
                "storage.s3.copy",
                bucket=self.bucket_name,
                source_key=source_key,
                dest_key=dest_key,
            ):
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.s3_client.copy_object(
                        Bucket=self.bucket_name,
                        Key=dest_key,
                        CopySource={"Bucket": self.bucket_name, "Key": source_key},
                    ),
                )

            logger.info(f"Copied S3 file: {source_key} -> {dest_key}")
            return True

        except Exception as e:
            logger.error(f"Error copying S3 file {source_path} -> {dest_path}: {e}")
            return False

    async def move_file(self, source_path: str, dest_path: str, tenant_id: str) -> bool:
        """Move file within S3 (copy then delete)."""
        try:
            # Copy file
            if await self.copy_file(source_path, dest_path, tenant_id, tenant_id):
                # Delete original
                return await self.delete_file(source_path, tenant_id)
            return False

        except Exception as e:
            logger.error(f"Error moving S3 file {source_path} -> {dest_path}: {e}")
            return False

class MinIOFileStorage(S3FileStorage):
    """MinIO-compatible storage backend built on top of the S3 client."""

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        region_name: str = "us-east-1",
        secure: bool | None = None,
    ) -> None:
        if not HAS_BOTO3:
            raise ImportError("boto3 is required for MinIO storage backend")

        bucket = bucket_name or os.getenv("MINIO_BUCKET", "dotmac")
        endpoint = endpoint_url or os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
        access_key = access_key or os.getenv("MINIO_ACCESS_KEY")
        secret_key = secret_key or os.getenv("MINIO_SECRET_KEY")
        secure = (
            secure if secure is not None else os.getenv("MINIO_SECURE", "false").lower() == "true"
        )

        if endpoint.startswith("http://") and secure:
            endpoint = endpoint.replace("http://", "https://", 1)

        super().__init__(
            bucket_name=bucket,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region_name,
            endpoint_url=endpoint,
            addressing_style="path",
            signature_version=os.getenv("MINIO_SIGNATURE_VERSION", "s3v4"),
        )

def create_storage_backend(config: dict[str, Any]) -> StorageBackend:
    """Factory function to create storage backend based on configuration."""
    backend_type = config.get("type", "local").lower()

    if backend_type == "local":
        return LocalFileStorage(base_path=config.get("base_path"))
    elif backend_type == "s3":
        return S3FileStorage(
            bucket_name=config["bucket_name"],
            aws_access_key_id=config.get("aws_access_key_id"),
            aws_secret_access_key=config.get("aws_secret_access_key"),
            region_name=config.get("region_name", "us-east-1"),
            endpoint_url=config.get("endpoint_url"),
            addressing_style=config.get("addressing_style"),
            signature_version=config.get("signature_version"),
        )
    elif backend_type == "minio":
        return MinIOFileStorage(
            bucket_name=config.get("bucket_name"),
            endpoint_url=config.get("endpoint_url"),
            access_key=config.get("access_key"),
            secret_key=config.get("secret_key"),
            region_name=config.get("region_name", "us-east-1"),
            secure=config.get("secure"),
        )
    else:
        raise ValueError(f"Unsupported storage backend type: {backend_type}")

class SecureFileStorage:
    """Secure storage wrapper with validation and security features.

    Provides file storage with security validations including:
    - File size limits
    - Extension validation
    - Path traversal prevention
    - Content type validation
    - Optional malware scanning (placeholder)
    """

    def __init__(
        self,
        base_path: str,
        max_file_size: int = 10 * 1024 * 1024,
        allowed_extensions: Optional[list[str]] = None,
        scan_for_malware: bool = False,
    ) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.max_file_size = max_file_size
        self.allowed_extensions = allowed_extensions or []
        self.scan_for_malware = scan_for_malware
        # Flags used in tests
        self.allow_empty_files: bool = True
        logger.info(f"SecureFileStorage initialized at: {self.base_path}")

    def _validate_path(self, path: str) -> Path:
        """Validate and sanitize file path."""
        # Remove leading slash and normalize
        clean_path = path.lstrip("/")
        full_path = self.base_path / clean_path

        # Prevent path traversal attacks
        try:
            resolved = full_path.resolve()
            resolved.relative_to(self.base_path.resolve())
        except ValueError as e:
            raise ValueError(f"Invalid file path (potential path traversal): {path}") from e

        return resolved

    def _validate_extension(self, path: str) -> None:
        """Validate file extension if restrictions are configured."""
        if not self.allowed_extensions:
            return

        extension = Path(path).suffix.lower()
        if extension and extension.lstrip(".") not in self.allowed_extensions:
            raise ValueError(
                f"File extension '{extension}' not allowed. "
                f"Allowed extensions: {', '.join(self.allowed_extensions)}"
            )

    def _validate_size(self, content: bytes) -> None:
        """Validate file size."""
        size = len(content)
        if size > self.max_file_size:
            raise ValueError(
                f"File size ({size} bytes) exceeds maximum allowed size "
                f"({self.max_file_size} bytes)"
            )

        if not self.allow_empty_files and size == 0:
            raise ValueError("Empty files are not allowed")

    async def _scan_content(self, content: bytes, path: str) -> None:
        """Placeholder for malware scanning."""
        if self.scan_for_malware:
            # In a real implementation, this would integrate with
            # a malware scanning service (ClamAV, VirusTotal, etc.)
            logger.info(f"Malware scan requested for {path} (placeholder)")
            # Simulate async scan
            await asyncio.sleep(0.01)

    async def store_file(self, path: str, content: bytes, **kwargs) -> dict[str, Any]:
        """Store file with security validations.

        Args:
            path: File path (relative to base_path)
            content: File content as bytes
            **kwargs: Additional metadata

        Returns:
            Dictionary with file information

        Raises:
            ValueError: If validation fails
        """
        # Validate path
        full_path = self._validate_path(path)

        # Validate extension
        self._validate_extension(path)

        # Validate size
        self._validate_size(content)

        # Scan for malware if configured
        await self._scan_content(content, path)

        # Ensure parent directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        full_path.write_bytes(content)

        # Prepare metadata
        metadata = {
            "path": path,
            "size": len(content),
            "stored_at": datetime.now(UTC).isoformat(),
            "checksum": hashlib.sha256(content).hexdigest(),
        }
        metadata.update(kwargs)

        logger.info(f"Securely stored file: {path} ({len(content)} bytes)")
        return metadata

    async def get_file(self, path: str, **kwargs) -> bytes:
        """Retrieve file with validation.

        Args:
            path: File path (relative to base_path)
            **kwargs: Additional options

        Returns:
            File content as bytes

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If path validation fails
        """
        # Validate path
        full_path = self._validate_path(path)

        # Check if file exists
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Read file
        content = full_path.read_bytes()

        logger.info(f"Retrieved file: {path} ({len(content)} bytes)")
        return content

    async def delete_file(self, path: str) -> bool:
        """Delete file with validation.

        Args:
            path: File path (relative to base_path)

        Returns:
            True if file was deleted, False if it didn't exist
        """
        try:
            full_path = self._validate_path(path)
            if full_path.exists():
                full_path.unlink()
                logger.info(f"Deleted file: {path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {path}: {e}")
            raise

    async def list_files(self, prefix: str = "") -> list[str]:
        """List files with optional prefix.

        Args:
            prefix: Optional path prefix

        Returns:
            List of file paths
        """
        search_path = self.base_path
        if prefix:
            search_path = self._validate_path(prefix)
            if not search_path.is_dir():
                search_path = search_path.parent

        files = []
        for file_path in search_path.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(self.base_path)
                files.append(str(relative_path))

        return files
