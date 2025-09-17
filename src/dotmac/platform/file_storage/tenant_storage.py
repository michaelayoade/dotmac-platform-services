"""
Tenant-aware storage management for multi-tenant file operations.

This module provides enhanced storage capabilities with tenant isolation,
access control, and quota management.
"""


from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, BinaryIO, Optional

from .backends import FileInfo, StorageBackend

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

@dataclass
class TenantQuota:
    """Tenant storage quota configuration."""

    max_storage_bytes: int
    max_files: int
    allowed_file_types: set[str]
    max_file_size: int

    def __post_init__(self):
        if isinstance(self.allowed_file_types, list):
            self.allowed_file_types = set(self.allowed_file_types)

@dataclass
class TenantUsage:
    """Current tenant storage usage."""

    total_bytes: int
    total_files: int
    files_by_type: dict[str, int]
    largest_file_size: int
    last_updated: datetime

class TenantStorageManager:
    """Multi-tenant storage manager with quotas and access control."""

    def __init__(
        self,
        storage_backend: StorageBackend,
        default_quota: Optional[TenantQuota] = None,
    ):
        """
        Initialize tenant storage manager.

        Args:
            storage_backend: Storage backend implementation
            default_quota: Default quota for tenants
        """
        self.storage = storage_backend
        self.default_quota = default_quota or TenantQuota(
            max_storage_bytes=1024 * 1024 * 1024,  # 1GB
            max_files=10000,
            allowed_file_types={"pdf", "xlsx", "csv", "png", "jpg", "jpeg"},
            max_file_size=100 * 1024 * 1024,  # 100MB
        )

        # In-memory quota and usage cache
        self._tenant_quotas: dict[str, TenantQuota] = {}
        self._tenant_usage: dict[str, TenantUsage] = {}

        logger.info("Tenant storage manager initialized")

    def set_tenant_quota(self, tenant_id: str, quota: TenantQuota):
        """Set quota for specific tenant."""
        self._tenant_quotas[tenant_id] = quota
        logger.info(
            f"Set quota for tenant {tenant_id}: {quota.max_storage_bytes} bytes, {quota.max_files} files"
        )

    def get_tenant_quota(self, tenant_id: str) -> TenantQuota:
        """Get quota for tenant."""
        return self._tenant_quotas.get(tenant_id, self.default_quota)

    async def get_tenant_usage(self, tenant_id: str, refresh: bool = False) -> TenantUsage:
        """Get current usage for tenant."""
        if tenant_id not in self._tenant_usage or refresh:
            await self._calculate_tenant_usage(tenant_id)

        return self._tenant_usage[tenant_id]

    async def _calculate_tenant_usage(self, tenant_id: str):
        """Calculate current storage usage for tenant."""
        try:
            files = await self.storage.list_files("", tenant_id)

            total_bytes = sum(f.size for f in files)
            total_files = len(files)
            largest_file = max(files, key=lambda f: f.size) if files else None
            largest_file_size = largest_file.size if largest_file else 0

            # Count files by type
            files_by_type = {}
            for file in files:
                ext = file.filename.split(".")[-1].lower() if "." in file.filename else "unknown"
                files_by_type[ext] = files_by_type.get(ext, 0) + 1

            usage = TenantUsage(
                total_bytes=total_bytes,
                total_files=total_files,
                files_by_type=files_by_type,
                largest_file_size=largest_file_size,
                last_updated=datetime.now(timezone.utc),
            )

            self._tenant_usage[tenant_id] = usage

        except Exception as e:
            logger.error(f"Error calculating usage for tenant {tenant_id}: {e}")
            # Return empty usage as fallback
            self._tenant_usage[tenant_id] = TenantUsage(
                total_bytes=0,
                total_files=0,
                files_by_type={},
                largest_file_size=0,
                last_updated=datetime.now(timezone.utc),
            )

    async def check_upload_allowed(
        self, tenant_id: str, file_size: int, file_type: str
    ) -> dict[str, Any]:
        """
        Check if file upload is allowed for tenant.

        Returns:
            Dictionary with 'allowed' boolean and 'reason' if not allowed
        """
        quota = self.get_tenant_quota(tenant_id)
        usage = await self.get_tenant_usage(tenant_id)

        # Check file type
        if file_type.lower() not in quota.allowed_file_types:
            return {
                "allowed": False,
                "reason": f'File type "{file_type}" not allowed',
                "allowed_types": list(quota.allowed_file_types),
            }

        # Check file size
        if file_size > quota.max_file_size:
            return {
                "allowed": False,
                "reason": f"File size {file_size} exceeds maximum {quota.max_file_size}",
                "max_file_size": quota.max_file_size,
            }

        # Check total storage
        if usage.total_bytes + file_size > quota.max_storage_bytes:
            return {
                "allowed": False,
                "reason": "Storage quota exceeded",
                "current_usage": usage.total_bytes,
                "quota": quota.max_storage_bytes,
            }

        # Check file count
        if usage.total_files >= quota.max_files:
            return {
                "allowed": False,
                "reason": "File count limit exceeded",
                "current_files": usage.total_files,
                "max_files": quota.max_files,
            }

        return {"allowed": True}

    async def save_file(
        self,
        file_path: str,
        content: BinaryIO,
        tenant_id: str,
        metadata: Optional[dict[str, Any]] = None,
        check_quota: bool = True,
    ) -> str:
        """
        Save file with tenant isolation and quota checking.

        Args:
            file_path: File path within tenant space
            content: File content
            tenant_id: Tenant ID
            metadata: Optional file metadata
            check_quota: Whether to check quota before saving

        Returns:
            Storage path of saved file
        """
        if check_quota:
            # Get file size
            if hasattr(content, "seek") and hasattr(content, "tell"):
                current_pos = content.tell()
                content.seek(0, 2)  # Seek to end
                file_size = content.tell()
                content.seek(current_pos)  # Restore position
            else:
                # Estimate size if can't determine exactly
                file_size = len(content) if hasattr(content, "__len__") else 0

            # Get file type
            file_type = file_path.split(".")[-1] if "." in file_path else "unknown"

            # Check if upload is allowed
            check_result = await self.check_upload_allowed(tenant_id, file_size, file_type)
            if not check_result["allowed"]:
                raise ValueError(f"Upload not allowed: {check_result['reason']}")

        # Save file using storage backend
        result = await self.storage.save_file(file_path, content, tenant_id, metadata)

        # Invalidate usage cache for this tenant
        if tenant_id in self._tenant_usage:
            del self._tenant_usage[tenant_id]

        logger.info(f"Saved file for tenant {tenant_id}: {file_path}")
        return result

    async def get_file(self, file_path: str, tenant_id: str) -> BinaryIO:
        """Get file with tenant isolation."""
        return await self.storage.get_file(file_path, tenant_id)

    async def delete_file(self, file_path: str, tenant_id: str) -> bool:
        """Delete file with tenant isolation."""
        result = await self.storage.delete_file(file_path, tenant_id)

        # Invalidate usage cache for this tenant
        if tenant_id in self._tenant_usage:
            del self._tenant_usage[tenant_id]

        if result:
            logger.info(f"Deleted file for tenant {tenant_id}: {file_path}")

        return result

    async def list_files(
        self,
        prefix: str = "",
        tenant_id: str = "",
        limit: Optional[int] = None,
        file_type: Optional[str] = None,
    ) -> list[FileInfo]:
        """List files with optional filtering."""
        files = await self.storage.list_files(prefix, tenant_id, limit)

        # Filter by file type if specified
        if file_type:
            file_type = file_type.lower()
            files = [f for f in files if f.filename.split(".")[-1].lower() == file_type]

        return files

    async def get_file_info(self, file_path: str, tenant_id: str) -> Optional[FileInfo]:
        """Get file information."""
        return await self.storage.get_file_info(file_path, tenant_id)

    async def file_exists(self, file_path: str, tenant_id: str) -> bool:
        """Check if file exists."""
        return await self.storage.file_exists(file_path, tenant_id)

    async def copy_file(
        self,
        source_path: str,
        dest_path: str,
        source_tenant_id: str,
        dest_tenant_id: str,
        check_quota: bool = True,
    ) -> bool:
        """Copy file between tenants or within tenant."""
        if check_quota and source_tenant_id != dest_tenant_id:
            # Get source file info to check size
            source_info = await self.get_file_info(source_path, source_tenant_id)
            if source_info:
                file_type = (
                    source_info.filename.split(".")[-1]
                    if "." in source_info.filename
                    else "unknown"
                )
                check_result = await self.check_upload_allowed(
                    dest_tenant_id, source_info.size, file_type
                )
                if not check_result["allowed"]:
                    raise ValueError(f"Copy not allowed: {check_result['reason']}")

        result = await self.storage.copy_file(
            source_path, dest_path, source_tenant_id, dest_tenant_id
        )

        # Invalidate usage cache for destination tenant
        if result and dest_tenant_id in self._tenant_usage:
            del self._tenant_usage[dest_tenant_id]

        return result

    async def move_file(self, source_path: str, dest_path: str, tenant_id: str) -> bool:
        """Move file within tenant."""
        return await self.storage.move_file(source_path, dest_path, tenant_id)

    async def cleanup_tenant_files(
        self,
        tenant_id: str,
        older_than_days: int = 30,
        file_types: Optional[list[str]] = None,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        """
        Cleanup old files for a tenant.

        Args:
            tenant_id: Tenant ID
            older_than_days: Delete files older than this many days
            file_types: Optional list of file types to cleanup
            dry_run: If True, only return what would be deleted

        Returns:
            Dictionary with cleanup results
        """
        try:
            files = await self.list_files("", tenant_id)

            # Calculate cutoff date
            from datetime import timedelta

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)

            # Filter files for cleanup
            files_to_delete = []
            for file in files:
                if file.created_at < cutoff_date:
                    if not file_types or any(file.filename.endswith(f".{ft}") for ft in file_types):
                        files_to_delete.append(file)

            result = {
                "tenant_id": tenant_id,
                "total_files_checked": len(files),
                "files_to_delete": len(files_to_delete),
                "total_size_to_free": sum(f.size for f in files_to_delete),
                "dry_run": dry_run,
                "deleted_files": [],
            }

            if not dry_run:
                # Actually delete files
                for file in files_to_delete:
                    try:
                        if await self.delete_file(file.path, tenant_id):
                            result["deleted_files"].append(file.path)
                    except Exception as e:
                        logger.error(f"Error deleting file {file.path}: {e}")

                result["actually_deleted"] = len(result["deleted_files"])

            logger.info(f"Cleanup for tenant {tenant_id}: {result}")
            return result

        except Exception as e:
            logger.error(f"Error during cleanup for tenant {tenant_id}: {e}")
            return {
                "tenant_id": tenant_id,
                "error": str(e),
                "files_to_delete": 0,
                "total_size_to_free": 0,
                "dry_run": dry_run,
                "deleted_files": [],
            }

    async def get_tenant_stats(self, tenant_id: str) -> dict[str, Any]:
        """Get comprehensive tenant statistics."""
        quota = self.get_tenant_quota(tenant_id)
        usage = await self.get_tenant_usage(tenant_id, refresh=True)

        return {
            "tenant_id": tenant_id,
            "quota": {
                "max_storage_bytes": quota.max_storage_bytes,
                "max_files": quota.max_files,
                "max_file_size": quota.max_file_size,
                "allowed_file_types": list(quota.allowed_file_types),
            },
            "usage": {
                "total_bytes": usage.total_bytes,
                "total_files": usage.total_files,
                "files_by_type": usage.files_by_type,
                "largest_file_size": usage.largest_file_size,
                "last_updated": usage.last_updated.isoformat(),
            },
            "utilization": {
                "storage_percent": (
                    (usage.total_bytes / quota.max_storage_bytes * 100)
                    if quota.max_storage_bytes > 0
                    else 0
                ),
                "files_percent": (
                    (usage.total_files / quota.max_files * 100) if quota.max_files > 0 else 0
                ),
            },
        }
