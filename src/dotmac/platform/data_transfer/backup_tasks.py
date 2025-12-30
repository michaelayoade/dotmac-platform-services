"""
Backup Celery Tasks.

Background tasks for scheduled database backups.

Note: Per the implementation plan, API endpoints should be added
AFTER proving manual restore works end-to-end.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import structlog

from dotmac.platform.celery_app import celery_app as app
from dotmac.platform.settings import settings

logger = structlog.get_logger(__name__)


def _run_async(coro: Any) -> Any:
    """Helper to run async code from sync Celery tasks."""
    import asyncio

    try:
        return asyncio.run(coro)
    except RuntimeError as exc:
        if "asyncio.run() cannot be called" not in str(exc):
            raise
        loop = asyncio.new_event_loop()
        policy = asyncio.get_event_loop_policy()
        try:
            previous_loop = policy.get_event_loop()
        except RuntimeError:
            previous_loop = None
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)
        finally:
            asyncio.set_event_loop(previous_loop)
            loop.close()


@app.task(name="backup.create_platform_backup")
def create_platform_backup_task() -> dict[str, Any]:
    """
    Create a full platform database backup.

    This is the main scheduled backup task that runs daily.
    Stores backup in MinIO with automatic cleanup of old backups.

    Returns:
        Backup result with path and metadata
    """
    from .backup_service import BackupService

    async def _backup():
        service = BackupService()
        return await service.create_backup(tenant_id=None)

    try:
        result = _run_async(_backup())

        logger.info(
            "backup.scheduled.completed",
            backup_path=result["backup_path"],
            file_size_bytes=result["file_size_bytes"],
        )

        return result

    except Exception as e:
        logger.error("backup.scheduled.failed", error=str(e))
        return {"error": str(e), "success": False}


@app.task(name="backup.create_tenant_backup")
def create_tenant_backup_task(tenant_id: str) -> dict[str, Any]:
    """
    Create a backup for a specific tenant.

    Args:
        tenant_id: The tenant to backup

    Returns:
        Backup result with path and metadata
    """
    from .backup_service import BackupService

    async def _backup():
        service = BackupService()
        return await service.create_backup(tenant_id=tenant_id)

    try:
        result = _run_async(_backup())

        logger.info(
            "backup.tenant.completed",
            tenant_id=tenant_id,
            backup_path=result["backup_path"],
            file_size_bytes=result["file_size_bytes"],
        )

        return result

    except Exception as e:
        logger.error("backup.tenant.failed", tenant_id=tenant_id, error=str(e))
        return {"error": str(e), "success": False, "tenant_id": tenant_id}


@app.task(name="backup.cleanup_old_backups")
def cleanup_old_backups_task(retention_days: int = 30) -> dict[str, Any]:
    """
    Cleanup backups older than retention period.

    Args:
        retention_days: Number of days to retain backups (default: 30)

    Returns:
        Cleanup statistics
    """
    from .backup_service import BackupService

    async def _cleanup():
        service = BackupService()
        stats = {"checked": 0, "deleted": 0, "retained": 0, "errors": 0}

        cutoff_date = datetime.now(UTC) - timedelta(days=retention_days)

        # Cleanup platform backups
        platform_backups = await service.list_backups(tenant_id=None)

        for backup in platform_backups:
            stats["checked"] += 1
            created_at_str = backup.get("created_at")

            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(
                        created_at_str.replace("Z", "+00:00")
                    )

                    if created_at < cutoff_date:
                        if await service.delete_backup(backup["backup_path"]):
                            stats["deleted"] += 1
                        else:
                            stats["errors"] += 1
                    else:
                        stats["retained"] += 1
                except Exception as e:
                    logger.warning(
                        "backup.cleanup.parse_error",
                        backup_path=backup.get("backup_path"),
                        error=str(e),
                    )
                    stats["retained"] += 1
            else:
                stats["retained"] += 1

        return stats

    try:
        result = _run_async(_cleanup())

        logger.info(
            "backup.cleanup.completed",
            retention_days=retention_days,
            **result,
        )

        return result

    except Exception as e:
        logger.error("backup.cleanup.failed", error=str(e))
        return {"error": str(e), "success": False}


@app.task(name="backup.validate_backup")
def validate_backup_task(backup_path: str) -> dict[str, Any]:
    """
    Validate a backup file without restoring.

    Performs a dry-run restore to verify backup integrity.

    Args:
        backup_path: Path to backup in storage

    Returns:
        Validation result
    """
    from .backup_service import BackupService

    async def _validate():
        service = BackupService()
        return await service.restore_backup(backup_path=backup_path, dry_run=True)

    try:
        result = _run_async(_validate())

        logger.info(
            "backup.validation.completed",
            backup_path=backup_path,
            valid=result.get("valid", True),
        )

        return result

    except Exception as e:
        logger.error("backup.validation.failed", backup_path=backup_path, error=str(e))
        return {"error": str(e), "valid": False, "backup_path": backup_path}


# Scheduled tasks are NOT automatically enabled
# Enable in production by configuring celery beat
#
# Example celery beat schedule entry:
# {
#     "backup-database-daily": {
#         "task": "backup.create_platform_backup",
#         "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
#     },
#     "backup-cleanup-weekly": {
#         "task": "backup.cleanup_old_backups",
#         "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3 AM
#         "kwargs": {"retention_days": 30},
#     },
# }
#
# IMPORTANT: Test manual backup/restore before enabling scheduled backups.
# See docs for restore runbook.


__all__ = [
    "create_platform_backup_task",
    "create_tenant_backup_task",
    "cleanup_old_backups_task",
    "validate_backup_task",
]
