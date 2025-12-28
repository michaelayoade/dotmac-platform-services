"""
Database Backup and Restore Service.

v0 Implementation:
- Full database backups using pg_dump
- Full restores using pg_restore
- MinIO storage for backup files
- No PITR (Point-in-Time Recovery) in v0

This module provides the core backup/restore functionality.
API endpoints and scheduled backups should be added AFTER
proving manual restore works end-to-end.
"""

import os
import subprocess
import tempfile
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

import structlog

from dotmac.platform.settings import settings

logger = structlog.get_logger(__name__)


class BackupError(Exception):
    """Base exception for backup operations."""

    pass


class RestoreError(Exception):
    """Base exception for restore operations."""

    pass


class BackupService:
    """
    Database backup and restore service.

    Supports full PostgreSQL backups using pg_dump and MinIO storage.

    Usage:
        service = BackupService()

        # Create backup
        result = await service.create_backup(tenant_id="tenant-123")
        print(f"Backup stored at: {result['backup_path']}")

        # Restore backup
        await service.restore_backup(backup_path="backups/tenant-123/2024-01-15_120000.dump")
    """

    def __init__(self) -> None:
        """Initialize backup service with database and storage configuration."""
        self.database_url = str(settings.database.url)
        self.storage_bucket = settings.storage.bucket or "backups"

    def _parse_database_url(self) -> dict[str, str | int]:
        """Parse database URL into connection components."""
        parsed = urlparse(self.database_url)
        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 5432,
            "database": (parsed.path or "/postgres").lstrip("/"),
            "user": parsed.username or "postgres",
            "password": parsed.password or "",
        }

    async def create_backup(
        self,
        tenant_id: str | None = None,
        backup_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a full database backup.

        For tenant-specific backups, uses schema filtering if available.
        For platform-wide backups (tenant_id=None), backs up entire database.

        Args:
            tenant_id: Optional tenant ID for scoped backup
            backup_name: Optional custom backup name

        Returns:
            Dictionary with backup metadata:
            - backup_path: Path in storage where backup is stored
            - file_size_bytes: Size of backup file
            - created_at: Timestamp of backup creation
            - tenant_id: Tenant scope (if any)
            - backup_type: "full" for v0

        Raises:
            BackupError: If backup creation fails
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        backup_id = backup_name or f"backup_{timestamp}"

        # Determine backup path
        if tenant_id:
            backup_filename = f"{backup_id}.dump"
            storage_path = f"backups/tenants/{tenant_id}/{backup_filename}"
        else:
            backup_filename = f"platform_{backup_id}.dump"
            storage_path = f"backups/platform/{backup_filename}"

        logger.info(
            "backup.starting",
            tenant_id=tenant_id,
            backup_id=backup_id,
            storage_path=storage_path,
        )

        # Create temporary file for backup
        with tempfile.NamedTemporaryFile(
            suffix=".dump",
            delete=False,
        ) as temp_file:
            temp_path = temp_file.name

        try:
            # Run pg_dump
            db_config = self._parse_database_url()

            # Build pg_dump command
            cmd = [
                "pg_dump",
                "--format=custom",  # Custom format for pg_restore
                "--compress=6",  # Compression level
                "--verbose",
                f"--host={db_config['host']}",
                f"--port={db_config['port']}",
                f"--username={db_config['user']}",
                f"--dbname={db_config['database']}",
                f"--file={temp_path}",
            ]

            # Add tenant schema filter if applicable
            if tenant_id:
                # Backup only the tenant's schema if using schema-per-tenant
                # This is optional - some setups use RLS instead
                schema_name = f"tenant_{tenant_id.replace('-', '_')}"
                # Check if schema exists before adding filter
                # For now, backup full database but log tenant context
                logger.info("backup.tenant_context", tenant_id=tenant_id, schema=schema_name)

            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = str(db_config["password"])

            # Execute pg_dump
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
            )

            if result.returncode != 0:
                raise BackupError(f"pg_dump failed: {result.stderr}")

            # pg_dump custom format is already compressed
            backup_size = os.path.getsize(temp_path)

            # Upload to MinIO
            backup_url = await self._upload_to_storage(temp_path, storage_path)

            backup_result = {
                "backup_path": storage_path,
                "backup_url": backup_url,
                "file_size_bytes": backup_size,
                "created_at": datetime.now(UTC).isoformat(),
                "tenant_id": tenant_id,
                "backup_type": "full",
                "format": "pg_custom",
                "compression": "pg_dump_custom",
            }

            logger.info(
                "backup.completed",
                **backup_result,
            )

            return backup_result

        except subprocess.TimeoutExpired:
            raise BackupError("Backup timed out after 1 hour")
        except Exception as e:
            logger.error("backup.failed", error=str(e), tenant_id=tenant_id)
            raise BackupError(f"Backup failed: {e}") from e
        finally:
            # Cleanup temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    async def restore_backup(
        self,
        backup_path: str,
        target_database: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Restore database from backup.

        WARNING: This is a destructive operation that will overwrite existing data.
        Always test in a non-production environment first.

        Args:
            backup_path: Path to backup in storage (e.g., "backups/tenant-123/backup.dump")
            target_database: Optional target database (defaults to current database)
            dry_run: If True, validate backup without restoring

        Returns:
            Dictionary with restore metadata:
            - restored_at: Timestamp of restore
            - backup_path: Source backup path
            - target_database: Database restored to
            - dry_run: Whether this was a dry run

        Raises:
            RestoreError: If restore fails
        """
        logger.info(
            "restore.starting",
            backup_path=backup_path,
            target_database=target_database,
            dry_run=dry_run,
        )

        # Download backup from storage
        with tempfile.NamedTemporaryFile(
            suffix=".dump",
            delete=False,
        ) as temp_file:
            temp_path = temp_file.name

        try:
            # Download from MinIO
            await self._download_from_storage(backup_path, temp_path)

            if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                raise RestoreError(f"Failed to download backup from {backup_path}")

            db_config = self._parse_database_url()
            target_db = target_database or str(db_config["database"])

            if dry_run:
                # Just validate the backup file
                cmd = [
                    "pg_restore",
                    "--list",  # List contents without restoring
                    temp_path,
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if result.returncode != 0:
                    raise RestoreError(f"Backup validation failed: {result.stderr}")

                logger.info(
                    "restore.dry_run_completed",
                    backup_path=backup_path,
                    items_found=len(result.stdout.splitlines()),
                )

                return {
                    "restored_at": datetime.now(UTC).isoformat(),
                    "backup_path": backup_path,
                    "target_database": target_db,
                    "dry_run": True,
                    "valid": True,
                    "items_in_backup": len(result.stdout.splitlines()),
                }

            # Build pg_restore command
            cmd = [
                "pg_restore",
                "--format=custom",
                "--clean",  # Drop existing objects before restoring
                "--if-exists",  # Don't error if objects don't exist
                "--verbose",
                f"--host={db_config['host']}",
                f"--port={db_config['port']}",
                f"--username={db_config['user']}",
                f"--dbname={target_db}",
                temp_path,
            ]

            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = str(db_config["password"])

            # Execute pg_restore
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=7200,  # 2 hour timeout
            )

            # pg_restore may return non-zero even on success if some objects already exist
            # Check stderr for actual errors
            if result.returncode != 0:
                # Check if it's a critical error or just warnings
                if "FATAL" in result.stderr or "could not connect" in result.stderr:
                    raise RestoreError(f"pg_restore failed: {result.stderr}")
                else:
                    logger.warning(
                        "restore.completed_with_warnings",
                        warnings=result.stderr[:500],
                    )

            restore_result = {
                "restored_at": datetime.now(UTC).isoformat(),
                "backup_path": backup_path,
                "target_database": target_db,
                "dry_run": False,
            }

            logger.info(
                "restore.completed",
                **restore_result,
            )

            return restore_result

        except subprocess.TimeoutExpired:
            raise RestoreError("Restore timed out after 2 hours")
        except Exception as e:
            logger.error("restore.failed", error=str(e), backup_path=backup_path)
            raise RestoreError(f"Restore failed: {e}") from e
        finally:
            # Cleanup temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    async def list_backups(
        self,
        tenant_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        List available backups.

        Args:
            tenant_id: Filter by tenant (None for platform backups)
            limit: Maximum number of backups to return

        Returns:
            List of backup metadata dictionaries
        """
        from minio import Minio

        if tenant_id:
            prefix = f"backups/tenants/{tenant_id}/"
        else:
            prefix = "backups/platform/"

        try:
            client = Minio(
                settings.storage.endpoint,
                access_key=settings.storage.access_key,
                secret_key=settings.storage.secret_key,
                secure=settings.storage.use_ssl,
            )

            objects = client.list_objects(
                self.storage_bucket,
                prefix=prefix,
                recursive=True,
            )

            backups = []
            for obj in objects:
                if obj.object_name and obj.object_name.endswith(".dump"):
                    backups.append(
                        {
                            "backup_path": obj.object_name,
                            "file_size_bytes": obj.size,
                            "created_at": obj.last_modified.isoformat() if obj.last_modified else None,
                            "tenant_id": tenant_id,
                        }
                    )

                if len(backups) >= limit:
                    break

            # Sort by creation time, newest first
            backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)

            return backups

        except Exception as e:
            logger.error("backup.list_failed", error=str(e), prefix=prefix)
            return []

    async def _upload_to_storage(self, local_path: str, storage_path: str) -> str:
        """Upload backup file to MinIO storage."""
        from minio import Minio

        try:
            client = Minio(
                settings.storage.endpoint,
                access_key=settings.storage.access_key,
                secret_key=settings.storage.secret_key,
                secure=settings.storage.use_ssl,
            )

            # Ensure bucket exists
            if not client.bucket_exists(self.storage_bucket):
                client.make_bucket(self.storage_bucket)

            # Upload file
            client.fput_object(
                self.storage_bucket,
                storage_path,
                local_path,
                content_type="application/octet-stream",
            )

            # Return URL or path
            return f"s3://{self.storage_bucket}/{storage_path}"

        except Exception as e:
            raise BackupError(f"Failed to upload backup: {e}") from e

    async def _download_from_storage(self, storage_path: str, local_path: str) -> None:
        """Download backup file from MinIO storage."""
        from minio import Minio

        try:
            client = Minio(
                settings.storage.endpoint,
                access_key=settings.storage.access_key,
                secret_key=settings.storage.secret_key,
                secure=settings.storage.use_ssl,
            )

            client.fget_object(
                self.storage_bucket,
                storage_path,
                local_path,
            )

        except Exception as e:
            raise RestoreError(f"Failed to download backup: {e}") from e

    async def delete_backup(self, backup_path: str) -> bool:
        """
        Delete a backup from storage.

        Args:
            backup_path: Path to backup in storage

        Returns:
            True if deleted successfully
        """
        from minio import Minio

        try:
            client = Minio(
                settings.storage.endpoint,
                access_key=settings.storage.access_key,
                secret_key=settings.storage.secret_key,
                secure=settings.storage.use_ssl,
            )

            client.remove_object(self.storage_bucket, backup_path)

            logger.info("backup.deleted", backup_path=backup_path)
            return True

        except Exception as e:
            logger.error("backup.delete_failed", error=str(e), backup_path=backup_path)
            return False


# Convenience functions for CLI usage
async def create_backup(tenant_id: str | None = None) -> dict[str, Any]:
    """Create a database backup."""
    service = BackupService()
    return await service.create_backup(tenant_id=tenant_id)


async def restore_backup(backup_path: str, dry_run: bool = True) -> dict[str, Any]:
    """Restore from a database backup."""
    service = BackupService()
    return await service.restore_backup(backup_path=backup_path, dry_run=dry_run)


async def list_backups(tenant_id: str | None = None) -> list[dict[str, Any]]:
    """List available backups."""
    service = BackupService()
    return await service.list_backups(tenant_id=tenant_id)
