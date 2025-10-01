"""
Audit log retention and archiving service.

Manages automatic cleanup and archiving of audit logs based on retention policies.
"""

import json
import gzip
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from pathlib import Path
import asyncio

import structlog
from sqlalchemy import select, delete, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AuditActivity, ActivitySeverity
from ..db import get_async_db
from ..settings import settings


logger = structlog.get_logger(__name__)


class AuditRetentionPolicy:
    """Configuration for audit log retention."""

    def __init__(
        self,
        retention_days: int = 90,
        archive_enabled: bool = True,
        archive_location: str = "/var/audit/archive",
        batch_size: int = 1000,
        severity_retention: Optional[Dict[str, int]] = None,
    ):
        """
        Initialize retention policy.

        Args:
            retention_days: Default days to retain audit logs
            archive_enabled: Whether to archive before deletion
            archive_location: Where to store archived logs
            batch_size: Number of records to process at once
            severity_retention: Custom retention by severity level
        """
        self.retention_days = retention_days
        self.archive_enabled = archive_enabled
        self.archive_location = Path(archive_location)
        self.batch_size = batch_size

        # Custom retention by severity (e.g., keep CRITICAL longer)
        self.severity_retention = severity_retention or {
            ActivitySeverity.LOW: 30,
            ActivitySeverity.MEDIUM: 60,
            ActivitySeverity.HIGH: 90,
            ActivitySeverity.CRITICAL: 365,
        }


class AuditRetentionService:
    """Service for managing audit log retention and archiving."""

    def __init__(self, policy: Optional[AuditRetentionPolicy] = None):
        """Initialize retention service with policy."""
        self.policy = policy or AuditRetentionPolicy()

        # Ensure archive directory exists
        if self.policy.archive_enabled:
            self.policy.archive_location.mkdir(parents=True, exist_ok=True)

    async def cleanup_old_logs(
        self,
        dry_run: bool = False,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Clean up old audit logs based on retention policy.

        Args:
            dry_run: If True, don't actually delete, just report what would be deleted
            tenant_id: Optionally limit to specific tenant

        Returns:
            Summary of cleanup operation
        """
        async with get_async_db() as session:
            results = {
                "total_deleted": 0,
                "total_archived": 0,
                "by_severity": {},
                "errors": [],
            }

            # Process each severity level with its retention period
            for severity, retention_days in self.policy.severity_retention.items():
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

                try:
                    # Build query for old records
                    query = select(AuditActivity).where(
                        and_(
                            AuditActivity.severity == severity,
                            AuditActivity.timestamp < cutoff_date,
                        )
                    )

                    if tenant_id:
                        query = query.where(AuditActivity.tenant_id == tenant_id)

                    # Count records to be processed
                    count_query = select(func.count()).select_from(query.subquery())
                    count_result = await session.execute(count_query)
                    total_count = count_result.scalar()

                    if total_count == 0:
                        continue

                    logger.info(
                        "Processing audit logs for cleanup",
                        severity=severity,
                        retention_days=retention_days,
                        records_found=total_count,
                        dry_run=dry_run,
                    )

                    if not dry_run:
                        # Archive if enabled
                        if self.policy.archive_enabled:
                            archived_count = await self._archive_logs(
                                session, query, severity, cutoff_date
                            )
                            results["total_archived"] += archived_count

                        # Delete old records
                        delete_query = delete(AuditActivity).where(
                            and_(
                                AuditActivity.severity == severity,
                                AuditActivity.timestamp < cutoff_date,
                            )
                        )
                        if tenant_id:
                            delete_query = delete_query.where(
                                AuditActivity.tenant_id == tenant_id
                            )

                        result = await session.execute(delete_query)
                        deleted_count = result.rowcount
                        await session.commit()

                        results["total_deleted"] += deleted_count
                        results["by_severity"][severity] = deleted_count

                        logger.info(
                            "Cleaned up audit logs",
                            severity=severity,
                            deleted_count=deleted_count,
                            archived=self.policy.archive_enabled,
                        )
                    else:
                        results["by_severity"][severity] = total_count
                        results["total_deleted"] += total_count

                except Exception as e:
                    error_msg = f"Error processing {severity} logs: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    results["errors"].append(error_msg)

            return results

    async def _archive_logs(
        self,
        session: AsyncSession,
        query,
        severity: str,
        cutoff_date: datetime,
    ) -> int:
        """
        Archive audit logs before deletion.

        Args:
            session: Database session
            query: Query for records to archive
            severity: Severity level being archived
            cutoff_date: Date before which records are archived

        Returns:
            Number of records archived
        """
        archived_count = 0

        # Create archive file name
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        archive_file = self.policy.archive_location / f"audit_{severity}_{timestamp}.jsonl.gz"

        try:
            # Process in batches
            offset = 0
            with gzip.open(archive_file, 'wt', encoding='utf-8') as f:
                while True:
                    batch_query = query.offset(offset).limit(self.policy.batch_size)
                    result = await session.execute(batch_query)
                    records = result.scalars().all()

                    if not records:
                        break

                    for record in records:
                        # Convert to dict for archiving
                        record_dict = {
                            "id": str(record.id),
                            "activity_type": record.activity_type,
                            "severity": record.severity,
                            "user_id": record.user_id,
                            "tenant_id": record.tenant_id,
                            "timestamp": record.timestamp.isoformat(),
                            "resource_type": record.resource_type,
                            "resource_id": record.resource_id,
                            "action": record.action,
                            "description": record.description,
                            "details": record.details,
                            "ip_address": record.ip_address,
                            "user_agent": record.user_agent,
                            "request_id": record.request_id,
                        }

                        # Write as JSON lines
                        f.write(json.dumps(record_dict) + '\n')
                        archived_count += 1

                    offset += self.policy.batch_size

            logger.info(
                "Archived audit logs",
                severity=severity,
                archive_file=str(archive_file),
                archived_count=archived_count,
            )

        except Exception as e:
            logger.error(
                "Failed to archive audit logs",
                severity=severity,
                error=str(e),
                exc_info=True,
            )
            # Remove partial archive file
            if archive_file.exists():
                archive_file.unlink()
            raise

        return archived_count

    async def restore_from_archive(
        self,
        archive_file: str,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Restore audit logs from archive file.

        Args:
            archive_file: Path to archive file
            tenant_id: Optionally filter to specific tenant

        Returns:
            Summary of restoration
        """
        file_path = Path(archive_file)
        if not file_path.exists():
            raise FileNotFoundError(f"Archive file not found: {archive_file}")

        results = {
            "total_restored": 0,
            "skipped": 0,
            "errors": [],
        }

        async with get_async_db() as session:
            try:
                with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                    batch = []

                    for line in f:
                        try:
                            record_dict = json.loads(line)

                            # Filter by tenant if specified
                            if tenant_id and record_dict.get("tenant_id") != tenant_id:
                                results["skipped"] += 1
                                continue

                            # Convert back to model
                            from uuid import UUID
                            activity = AuditActivity(
                                id=UUID(record_dict["id"]) if isinstance(record_dict["id"], str) else record_dict["id"],
                                activity_type=record_dict["activity_type"],
                                severity=record_dict["severity"],
                                user_id=record_dict["user_id"],
                                tenant_id=record_dict["tenant_id"],
                                timestamp=datetime.fromisoformat(record_dict["timestamp"]),
                                resource_type=record_dict["resource_type"],
                                resource_id=record_dict["resource_id"],
                                action=record_dict["action"],
                                description=record_dict["description"],
                                details=record_dict["details"],
                                ip_address=record_dict["ip_address"],
                                user_agent=record_dict["user_agent"],
                                request_id=record_dict["request_id"],
                            )

                            batch.append(activity)

                            # Insert in batches
                            if len(batch) >= self.policy.batch_size:
                                session.add_all(batch)
                                await session.commit()
                                results["total_restored"] += len(batch)
                                batch = []

                        except Exception as e:
                            error_msg = f"Error restoring record: {str(e)}"
                            logger.error(error_msg, record=line[:100])
                            results["errors"].append(error_msg)

                    # Insert remaining batch
                    if batch:
                        session.add_all(batch)
                        await session.commit()
                        results["total_restored"] += len(batch)

                logger.info(
                    "Restored audit logs from archive",
                    archive_file=archive_file,
                    total_restored=results["total_restored"],
                    skipped=results["skipped"],
                )

            except Exception as e:
                error_msg = f"Failed to restore from archive: {str(e)}"
                logger.error(error_msg, exc_info=True)
                results["errors"].append(error_msg)

        return results

    async def get_retention_statistics(
        self,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get statistics about audit logs and retention.

        Args:
            tenant_id: Optionally filter to specific tenant

        Returns:
            Statistics about current audit logs
        """
        async with get_async_db() as session:
            stats = {
                "total_records": 0,
                "by_severity": {},
                "oldest_record": None,
                "newest_record": None,
                "records_to_delete": {},
            }

            # Get total count
            count_query = select(func.count()).select_from(AuditActivity)
            if tenant_id:
                count_query = count_query.where(AuditActivity.tenant_id == tenant_id)

            count_result = await session.execute(count_query)
            stats["total_records"] = count_result.scalar()

            # Get count by severity
            severity_query = (
                select(AuditActivity.severity, func.count())
                .group_by(AuditActivity.severity)
            )
            if tenant_id:
                severity_query = severity_query.where(
                    AuditActivity.tenant_id == tenant_id
                )

            severity_result = await session.execute(severity_query)
            stats["by_severity"] = dict(severity_result.all())

            # Get date range
            date_query = select(
                func.min(AuditActivity.timestamp),
                func.max(AuditActivity.timestamp),
            )
            if tenant_id:
                date_query = date_query.where(AuditActivity.tenant_id == tenant_id)

            date_result = await session.execute(date_query)
            oldest, newest = date_result.one()

            if oldest:
                stats["oldest_record"] = oldest.isoformat()
            if newest:
                stats["newest_record"] = newest.isoformat()

            # Calculate records to be deleted
            for severity, retention_days in self.policy.severity_retention.items():
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

                delete_count_query = select(func.count()).select_from(AuditActivity).where(
                    and_(
                        AuditActivity.severity == severity,
                        AuditActivity.timestamp < cutoff_date,
                    )
                )
                if tenant_id:
                    delete_count_query = delete_count_query.where(
                        AuditActivity.tenant_id == tenant_id
                    )

                delete_count_result = await session.execute(delete_count_query)
                count_to_delete = delete_count_result.scalar()

                if count_to_delete > 0:
                    stats["records_to_delete"][severity] = {
                        "count": count_to_delete,
                        "older_than": cutoff_date.isoformat(),
                    }

            return stats


# Scheduled task for automatic cleanup
async def cleanup_audit_logs_task():
    """
    Scheduled task to run audit log cleanup.

    This should be scheduled to run daily via cron or task scheduler.
    """
    try:
        # Load policy from settings
        policy = AuditRetentionPolicy(
            retention_days=getattr(settings, 'audit_retention_days', 90),
            archive_enabled=getattr(settings, 'audit_archive_enabled', True),
            archive_location=getattr(settings, 'audit_archive_location', '/var/audit/archive'),
        )

        service = AuditRetentionService(policy)

        # Get statistics before cleanup
        stats_before = await service.get_retention_statistics()
        logger.info("Audit retention statistics before cleanup", stats=stats_before)

        # Perform cleanup
        results = await service.cleanup_old_logs()
        logger.info("Audit log cleanup completed", results=results)

        # Get statistics after cleanup
        stats_after = await service.get_retention_statistics()
        logger.info("Audit retention statistics after cleanup", stats=stats_after)

        return results

    except Exception as e:
        logger.error("Failed to run audit log cleanup", error=str(e), exc_info=True)
        raise


if __name__ == "__main__":
    # Manual run of cleanup task
    asyncio.run(cleanup_audit_logs_task())