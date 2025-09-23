"""
File storage service with multiple backend support.

Provides a unified interface for file storage operations with support for:
- Local filesystem storage
- MinIO/S3 storage
- In-memory storage for testing
"""

import hashlib
import json
import os
import uuid
from datetime import datetime, UTC
from io import BytesIO
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Tuple

import structlog
from pydantic import BaseModel, Field

from ..settings import settings
from .minio_storage import MinIOStorage, get_storage

logger = structlog.get_logger(__name__)


class StorageBackend:
    """Storage backend types."""
    LOCAL = "local"
    S3 = "s3"
    MINIO = "minio"
    MEMORY = "memory"  # For testing


class FileMetadata(BaseModel):
    """File metadata."""

    file_id: str = Field(..., description="Unique file identifier")
    file_name: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    path: Optional[str] = Field(None, description="Storage path")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    checksum: Optional[str] = Field(None, description="File checksum")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "file_id": self.file_id,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "content_type": self.content_type,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "path": self.path,
            "metadata": self.metadata,
            "checksum": self.checksum,
            "tenant_id": self.tenant_id,
        }


class LocalFileStorage:
    """Local filesystem storage backend."""

    def __init__(self, base_path: Optional[str] = None):
        """Initialize local storage."""
        self.base_path = Path(base_path or settings.storage.local_path or "/tmp/dotmac-storage")
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.metadata_path = self.base_path / ".metadata"
        self.metadata_path.mkdir(exist_ok=True)
        logger.info(f"Local storage initialized at {self.base_path}")

    def _get_file_path(self, file_id: str, tenant_id: Optional[str] = None) -> Path:
        """Get full file path."""
        if tenant_id:
            return self.base_path / tenant_id / file_id
        return self.base_path / file_id

    def _get_metadata_path(self, file_id: str) -> Path:
        """Get metadata file path."""
        return self.metadata_path / f"{file_id}.json"

    def _save_metadata(self, file_id: str, metadata: FileMetadata) -> None:
        """Save file metadata."""
        metadata_file = self._get_metadata_path(file_id)
        with open(metadata_file, 'w') as f:
            json.dump(metadata.to_dict(), f, default=str)

    def _load_metadata(self, file_id: str) -> Optional[FileMetadata]:
        """Load file metadata."""
        metadata_file = self._get_metadata_path(file_id)
        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, 'r') as f:
                data = json.load(f)
                return FileMetadata(
                    file_id=data["file_id"],
                    file_name=data["file_name"],
                    file_size=data["file_size"],
                    content_type=data["content_type"],
                    created_at=datetime.fromisoformat(data["created_at"]),
                    updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
                    path=data.get("path"),
                    metadata=data.get("metadata", {}),
                    checksum=data.get("checksum"),
                    tenant_id=data.get("tenant_id"),
                )
        except Exception as e:
            logger.error(f"Failed to load metadata for {file_id}: {e}")
            return None

    async def store(
        self,
        file_data: bytes,
        file_name: str,
        content_type: str,
        path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
    ) -> str:
        """Store a file."""
        file_id = str(uuid.uuid4())

        # Calculate checksum
        checksum = hashlib.sha256(file_data).hexdigest()

        # Save file
        file_path = self._get_file_path(file_id, tenant_id)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'wb') as f:
            f.write(file_data)

        # Create and save metadata
        file_metadata = FileMetadata(
            file_id=file_id,
            file_name=file_name,
            file_size=len(file_data),
            content_type=content_type,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            path=path,
            metadata=metadata or {},
            checksum=checksum,
            tenant_id=tenant_id,
        )
        self._save_metadata(file_id, file_metadata)

        logger.info(f"Stored file {file_id} ({file_name}) - {len(file_data)} bytes")
        return file_id

    async def retrieve(self, file_id: str, tenant_id: Optional[str] = None) -> Tuple[Optional[bytes], Optional[dict]]:
        """Retrieve a file."""
        file_path = self._get_file_path(file_id, tenant_id)

        if not file_path.exists():
            logger.warning(f"File not found: {file_id}")
            return None, None

        # Load file data
        with open(file_path, 'rb') as f:
            file_data = f.read()

        # Load metadata
        metadata = self._load_metadata(file_id)

        if metadata:
            return file_data, metadata.to_dict()
        else:
            # Return basic metadata if metadata file is missing
            return file_data, {
                "file_id": file_id,
                "file_size": len(file_data),
            }

    async def delete(self, file_id: str, tenant_id: Optional[str] = None) -> bool:
        """Delete a file."""
        file_path = self._get_file_path(file_id, tenant_id)
        metadata_path = self._get_metadata_path(file_id)

        deleted = False

        if file_path.exists():
            file_path.unlink()
            deleted = True

        if metadata_path.exists():
            metadata_path.unlink()

        if deleted:
            logger.info(f"Deleted file {file_id}")

        return deleted

    async def list_files(
        self,
        path: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        tenant_id: Optional[str] = None,
    ) -> List[FileMetadata]:
        """List files."""
        files = []

        # Get all metadata files
        metadata_files = list(self.metadata_path.glob("*.json"))

        # Sort by modification time (newest first)
        metadata_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        # Apply pagination
        start = offset
        end = offset + limit

        for metadata_file in metadata_files[start:end]:
            file_id = metadata_file.stem
            metadata = self._load_metadata(file_id)

            if metadata:
                # Filter by tenant if specified
                if tenant_id and metadata.tenant_id != tenant_id:
                    continue

                # Filter by path if specified
                if path and metadata.path and not metadata.path.startswith(path):
                    continue

                files.append(metadata)

        return files

    async def get_metadata(self, file_id: str) -> Optional[dict]:
        """Get file metadata."""
        metadata = self._load_metadata(file_id)
        return metadata.to_dict() if metadata else None


class MemoryFileStorage:
    """In-memory storage backend for testing."""

    def __init__(self):
        """Initialize memory storage."""
        self.files: Dict[str, bytes] = {}
        self.metadata: Dict[str, FileMetadata] = {}
        logger.info("Memory storage initialized")

    async def store(
        self,
        file_data: bytes,
        file_name: str,
        content_type: str,
        path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
    ) -> str:
        """Store a file in memory."""
        file_id = str(uuid.uuid4())

        # Calculate checksum
        checksum = hashlib.sha256(file_data).hexdigest()

        # Store file data
        self.files[file_id] = file_data

        # Store metadata
        file_metadata = FileMetadata(
            file_id=file_id,
            file_name=file_name,
            file_size=len(file_data),
            content_type=content_type,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            path=path,
            metadata=metadata or {},
            checksum=checksum,
            tenant_id=tenant_id,
        )
        self.metadata[file_id] = file_metadata

        logger.info(f"Stored file {file_id} ({file_name}) in memory - {len(file_data)} bytes")
        return file_id

    async def retrieve(self, file_id: str, tenant_id: Optional[str] = None) -> Tuple[Optional[bytes], Optional[dict]]:
        """Retrieve a file from memory."""
        file_data = self.files.get(file_id)
        metadata = self.metadata.get(file_id)

        if file_data and metadata:
            return file_data, metadata.to_dict()

        return None, None

    async def delete(self, file_id: str, tenant_id: Optional[str] = None) -> bool:
        """Delete a file from memory."""
        deleted = False

        if file_id in self.files:
            del self.files[file_id]
            deleted = True

        if file_id in self.metadata:
            del self.metadata[file_id]

        return deleted

    async def list_files(
        self,
        path: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        tenant_id: Optional[str] = None,
    ) -> List[FileMetadata]:
        """List files in memory."""
        files = list(self.metadata.values())

        # Filter by tenant
        if tenant_id:
            files = [f for f in files if f.tenant_id == tenant_id]

        # Filter by path
        if path:
            files = [f for f in files if f.path and f.path.startswith(path)]

        # Sort by creation date (newest first)
        files.sort(key=lambda f: f.created_at, reverse=True)

        # Apply pagination
        return files[offset:offset + limit]

    async def get_metadata(self, file_id: str) -> Optional[dict]:
        """Get file metadata."""
        metadata = self.metadata.get(file_id)
        return metadata.to_dict() if metadata else None


class MinIOFileStorage:
    """MinIO/S3 storage backend wrapper."""

    def __init__(self, minio_client: Optional[MinIOStorage] = None):
        """Initialize MinIO storage."""
        self.client = minio_client or get_storage()
        self.metadata_store = {}  # In production, use database or MinIO metadata
        logger.info("MinIO storage initialized")

    async def store(
        self,
        file_data: bytes,
        file_name: str,
        content_type: str,
        path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
    ) -> str:
        """Store a file in MinIO."""
        file_id = str(uuid.uuid4())
        tenant_id = tenant_id or "default"

        # Create path
        if path:
            full_path = f"{path}/{file_id}/{file_name}"
        else:
            full_path = f"{file_id}/{file_name}"

        # Store in MinIO
        content = BytesIO(file_data)
        object_name = self.client.save_file(
            file_path=full_path,
            content=content,
            tenant_id=tenant_id,
            content_type=content_type,
        )

        # Store metadata (in production, use database)
        checksum = hashlib.sha256(file_data).hexdigest()
        file_metadata = FileMetadata(
            file_id=file_id,
            file_name=file_name,
            file_size=len(file_data),
            content_type=content_type,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            path=path,
            metadata=metadata or {},
            checksum=checksum,
            tenant_id=tenant_id,
        )
        self.metadata_store[file_id] = file_metadata

        logger.info(f"Stored file {file_id} ({file_name}) in MinIO - {len(file_data)} bytes")
        return file_id

    async def retrieve(self, file_id: str, tenant_id: Optional[str] = None) -> Tuple[Optional[bytes], Optional[dict]]:
        """Retrieve a file from MinIO."""
        tenant_id = tenant_id or "default"

        # Get metadata
        metadata = self.metadata_store.get(file_id)
        if not metadata:
            return None, None

        # Construct path
        if metadata.path:
            full_path = f"{metadata.path}/{file_id}/{metadata.file_name}"
        else:
            full_path = f"{file_id}/{metadata.file_name}"

        try:
            # Retrieve from MinIO
            file_data = self.client.get_file(full_path, tenant_id)
            return file_data, metadata.to_dict()
        except FileNotFoundError:
            logger.warning(f"File not found in MinIO: {file_id}")
            return None, None

    async def delete(self, file_id: str, tenant_id: Optional[str] = None) -> bool:
        """Delete a file from MinIO."""
        tenant_id = tenant_id or "default"

        # Get metadata
        metadata = self.metadata_store.get(file_id)
        if not metadata:
            return False

        # Construct path
        if metadata.path:
            full_path = f"{metadata.path}/{file_id}/{metadata.file_name}"
        else:
            full_path = f"{file_id}/{metadata.file_name}"

        # Delete from MinIO
        success = self.client.delete_file(full_path, tenant_id)

        if success:
            del self.metadata_store[file_id]
            logger.info(f"Deleted file {file_id} from MinIO")

        return success

    async def list_files(
        self,
        path: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        tenant_id: Optional[str] = None,
    ) -> List[FileMetadata]:
        """List files in MinIO."""
        tenant_id = tenant_id or "default"

        # In production, query from database
        files = list(self.metadata_store.values())

        # Filter by tenant
        if tenant_id:
            files = [f for f in files if f.tenant_id == tenant_id]

        # Filter by path
        if path:
            files = [f for f in files if f.path and f.path.startswith(path)]

        # Sort by creation date (newest first)
        files.sort(key=lambda f: f.created_at, reverse=True)

        # Apply pagination
        return files[offset:offset + limit]

    async def get_metadata(self, file_id: str) -> Optional[dict]:
        """Get file metadata."""
        metadata = self.metadata_store.get(file_id)
        return metadata.to_dict() if metadata else None


class FileStorageService:
    """Unified file storage service with backend selection."""

    def __init__(self, backend: str = StorageBackend.LOCAL):
        """Initialize storage service with specified backend."""
        self.backend_type = backend

        # Initialize appropriate backend
        if backend == StorageBackend.LOCAL:
            self.backend = LocalFileStorage()
        elif backend == StorageBackend.MEMORY:
            self.backend = MemoryFileStorage()
        elif backend == StorageBackend.MINIO or backend == StorageBackend.S3:
            # Try to use MinIO backend
            try:
                # Check if MinIO/S3 dependencies are available
                from .minio_storage import MinIOStorage
                self.backend = MinIOFileStorage()
                logger.info(f"Successfully initialized MinIO/S3 backend")
            except Exception as e:
                logger.warning(f"Failed to initialize MinIO backend: {e}")
                logger.warning("Falling back to local storage")
                self.backend = LocalFileStorage()
                self.backend_type = StorageBackend.LOCAL
        else:
            # Default to local storage
            logger.warning(f"Unknown backend {backend}, using local storage")
            self.backend = LocalFileStorage()

        logger.info(f"FileStorageService initialized with {self.backend_type} backend")

    async def store_file(
        self,
        file_data: bytes,
        file_name: str,
        content_type: str,
        path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
    ) -> str:
        """Store a file and return its ID."""
        return await self.backend.store(
            file_data=file_data,
            file_name=file_name,
            content_type=content_type,
            path=path,
            metadata=metadata,
            tenant_id=tenant_id,
        )

    async def retrieve_file(self, file_id: str, tenant_id: Optional[str] = None) -> Tuple[Optional[bytes], Optional[dict]]:
        """Retrieve a file by ID."""
        return await self.backend.retrieve(file_id, tenant_id)

    async def delete_file(self, file_id: str, tenant_id: Optional[str] = None) -> bool:
        """Delete a file by ID."""
        return await self.backend.delete(file_id, tenant_id)

    async def list_files(
        self,
        path: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        tenant_id: Optional[str] = None,
    ) -> List[FileMetadata]:
        """List files."""
        return await self.backend.list_files(
            path=path,
            limit=limit,
            offset=offset,
            tenant_id=tenant_id,
        )

    async def get_file_metadata(self, file_id: str) -> Optional[dict]:
        """Get file metadata."""
        return await self.backend.get_metadata(file_id)

    async def update_file_metadata(
        self,
        file_id: str,
        metadata_updates: Dict[str, Any],
        tenant_id: Optional[str] = None,
    ) -> bool:
        """Update file metadata."""
        # Get existing metadata
        current_metadata = await self.backend.get_metadata(file_id)
        if not current_metadata:
            return False

        # Update metadata
        if "metadata" in current_metadata:
            current_metadata["metadata"].update(metadata_updates)
        else:
            current_metadata["metadata"] = metadata_updates

        current_metadata["updated_at"] = datetime.now(UTC).isoformat()

        # In production, save to database
        # For now, update in-memory if applicable
        if hasattr(self.backend, 'metadata_store'):
            file_meta = self.backend.metadata_store.get(file_id)
            if file_meta:
                file_meta.metadata.update(metadata_updates)
                file_meta.updated_at = datetime.now(UTC)
        elif hasattr(self.backend, 'metadata'):
            file_meta = self.backend.metadata.get(file_id)
            if file_meta:
                file_meta.metadata.update(metadata_updates)
                file_meta.updated_at = datetime.now(UTC)

        return True


# Global service instance
_storage_service: Optional[FileStorageService] = None


def get_storage_service() -> FileStorageService:
    """Get the global storage service instance."""
    global _storage_service
    if _storage_service is None:
        # Determine backend from settings.storage.provider
        provider = settings.storage.provider.lower()

        # Map provider to backend
        if provider == "minio":
            backend = StorageBackend.MINIO
        elif provider == "s3":
            backend = StorageBackend.S3
        elif provider == "local":
            backend = StorageBackend.LOCAL
        else:
            # Default to local if unknown provider
            backend = StorageBackend.LOCAL

        logger.info(f"Initializing storage service with {backend} backend (provider: {provider})")
        _storage_service = FileStorageService(backend=backend)
    return _storage_service