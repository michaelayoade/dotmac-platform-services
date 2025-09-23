"""
File storage module with multiple backend support.
"""

from .minio_storage import FileInfo, MinIOStorage, get_storage
from .router import file_storage_router, storage_router
from .service import (
    FileMetadata,
    FileStorageService,
    LocalFileStorage,
    MemoryFileStorage,
    MinIOFileStorage,
    StorageBackend,
    get_storage_service,
)

__all__ = [
    # MinIO specific
    "MinIOStorage",
    "FileInfo",
    "get_storage",
    # Service and backends
    "StorageBackend",
    "FileMetadata",
    "FileStorageService",
    "LocalFileStorage",
    "MemoryFileStorage",
    "MinIOFileStorage",
    "get_storage_service",
    # Router
    "file_storage_router",
    "storage_router",
]
