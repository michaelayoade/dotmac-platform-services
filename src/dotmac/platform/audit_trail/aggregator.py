"""
Audit Trail Aggregator for centralized audit logging.

Collects audit events from all services and provides query capabilities.
"""

import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.core.decorators import standard_exception_handler
from dotmac.platform.observability.unified_logging import get_logger
from dotmac.platform.tasks import task

from .models import AuditCategory, AuditEvent, AuditLevel
from .storage import AuditStorage

logger = get_logger(__name__)


class AuditAggregator:
    """
    Centralized audit trail aggregator.

    Features:
    - Multi-source audit collection
    - Real-time and batch processing
    - Compliance reporting
    - Anomaly detection
    - Retention management
    """

    def __init__(
        self,
        storage: Optional[AuditStorage] = None,
        batch_size: int = 100,
        flush_interval: int = 5,
    ):
        """Initialize audit aggregator."""
        self.storage = storage or AuditStorage()
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._buffer: list[AuditEvent] = []
        self._flush_task: Optional[asyncio.Task] = None
        self._stats = {
            "events_processed": 0,
            "events_dropped": 0,
            "batch_flushes": 0,
            "errors": 0,
        }

    async def start(self):
        """Start the audit aggregator."""
        if not self._flush_task:
            self._flush_task = asyncio.create_task(self._periodic_flush())
            logger.info("Audit aggregator started")

    async def stop(self):
        """Stop the audit aggregator."""
        if self._flush_task:
            self._flush_task.cancel()
            await self._flush_buffer()
            logger.info("Audit aggregator stopped")

    @standard_exception_handler
    async def log_event(
        self,
        category: AuditCategory,
        action: str,
        level: AuditLevel = AuditLevel.INFO,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        service_name: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> str:
        """Log an audit event."""
        event = AuditEvent(
            id=str(uuid4()),
            timestamp=datetime.now(timezone.utc),
            category=category,
            action=action,
            level=level,
            user_id=user_id,
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            service_name=service_name,
            correlation_id=correlation_id or str(uuid4()),
        )

        # Add to buffer
        self._buffer.append(event)
        self._stats["events_processed"] += 1

        # Flush if buffer is full
        if len(self._buffer) >= self.batch_size:
            await self._flush_buffer()

        # Send critical events immediately
        if level in [AuditLevel.CRITICAL, AuditLevel.ALERT]:
            await self._send_alert(event)

        return event.id

    @standard_exception_handler
    async def query_events(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        category: Optional[AuditCategory] = None,
        level: Optional[AuditLevel] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        service_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AuditEvent], int]:
        """Query audit events with filters."""
        return await self.storage.query_events(
            tenant_id=tenant_id,
            user_id=user_id,
            category=category,
            level=level,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            service_name=service_name,
            start_time=start_time,
            end_time=end_time,
            correlation_id=correlation_id,
            limit=limit,
            offset=offset,
        )

    @standard_exception_handler
    async def get_user_activity(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get user activity summary."""
        start_time = datetime.now(timezone.utc) - timedelta(days=days)

        events, total = await self.query_events(
            user_id=user_id,
            tenant_id=tenant_id,
            start_time=start_time,
            limit=1000,
        )

        # Analyze activity
        activity_by_category = {}
        activity_by_action = {}
        activity_by_day = {}
        resource_access = {}

        for event in events:
            # By category
            cat = event.category.value
            activity_by_category[cat] = activity_by_category.get(cat, 0) + 1

            # By action
            activity_by_action[event.action] = activity_by_action.get(event.action, 0) + 1

            # By day
            day = event.timestamp.date().isoformat()
            activity_by_day[day] = activity_by_day.get(day, 0) + 1

            # Resource access
            if event.resource_type:
                resource_key = f"{event.resource_type}:{event.resource_id}"
                resource_access[resource_key] = resource_access.get(resource_key, 0) + 1

        return {
            "user_id": user_id,
            "period_days": days,
            "total_events": total,
            "activity_by_category": activity_by_category,
            "activity_by_action": activity_by_action,
            "activity_by_day": activity_by_day,
            "resource_access": dict(sorted(resource_access.items(), key=lambda x: x[1], reverse=True)[:10]),
            "first_activity": events[-1].timestamp.isoformat() if events else None,
            "last_activity": events[0].timestamp.isoformat() if events else None,
        }

    @standard_exception_handler
    async def get_security_events(
        self,
        tenant_id: Optional[str] = None,
        hours: int = 24,
    ) -> list[AuditEvent]:
        """Get recent security-related events."""
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        events, _ = await self.query_events(
            tenant_id=tenant_id,
            category=AuditCategory.SECURITY,
            start_time=start_time,
            limit=500,
        )

        # Also get critical events from other categories
        critical_events, _ = await self.query_events(
            tenant_id=tenant_id,
            level=AuditLevel.CRITICAL,
            start_time=start_time,
            limit=500,
        )

        # Combine and sort by timestamp
        all_events = list(set(events + critical_events))
        all_events.sort(key=lambda x: x.timestamp, reverse=True)

        return all_events

    @standard_exception_handler
    async def generate_compliance_report(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
        compliance_type: str = "gdpr",
    ) -> dict[str, Any]:
        """Generate compliance report for audit trail."""
        # Get all events in period
        events, total = await self.query_events(
            tenant_id=tenant_id,
            start_time=start_date,
            end_time=end_date,
            limit=10000,
        )

        report = {
            "tenant_id": tenant_id,
            "report_type": compliance_type,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_events": total,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        if compliance_type == "gdpr":
            # GDPR specific analysis
            data_access_events = [e for e in events if e.category == AuditCategory.DATA_ACCESS]
            data_modification_events = [e for e in events if e.category == AuditCategory.DATA_MODIFICATION]
            consent_events = [e for e in events if "consent" in e.action.lower()]

            report["gdpr_metrics"] = {
                "data_access_count": len(data_access_events),
                "data_modification_count": len(data_modification_events),
                "consent_events": len(consent_events),
                "unique_users_accessed": len(set(e.user_id for e in data_access_events if e.user_id)),
                "data_deletion_requests": len([e for e in events if "delete" in e.action.lower()]),
                "data_export_requests": len([e for e in events if "export" in e.action.lower()]),
            }

        elif compliance_type == "sox":
            # SOX specific analysis
            financial_events = [e for e in events if e.category == AuditCategory.FINANCIAL]
            system_changes = [e for e in events if e.category == AuditCategory.SYSTEM]

            report["sox_metrics"] = {
                "financial_transactions": len(financial_events),
                "system_changes": len(system_changes),
                "unauthorized_access_attempts": len([e for e in events if "unauthorized" in e.action.lower()]),
                "privilege_escalations": len([e for e in events if "privilege" in e.action.lower()]),
            }

        return report

    @standard_exception_handler
    async def detect_anomalies(
        self,
        tenant_id: Optional[str] = None,
        window_hours: int = 1,
    ) -> list[dict[str, Any]]:
        """Detect anomalous patterns in audit trail."""
        anomalies = []
        current_time = datetime.now(timezone.utc)
        window_start = current_time - timedelta(hours=window_hours)

        # Get recent events
        events, _ = await self.query_events(
            tenant_id=tenant_id,
            start_time=window_start,
            limit=1000,
        )

        # Check for suspicious patterns
        user_activity = {}
        ip_activity = {}
        failed_attempts = {}

        for event in events:
            # Track user activity
            if event.user_id:
                if event.user_id not in user_activity:
                    user_activity[event.user_id] = []
                user_activity[event.user_id].append(event)

            # Track IP activity
            if event.ip_address:
                if event.ip_address not in ip_activity:
                    ip_activity[event.ip_address] = []
                ip_activity[event.ip_address].append(event)

            # Track failed attempts
            if "failed" in event.action.lower() or "denied" in event.action.lower():
                key = f"{event.user_id or 'unknown'}:{event.ip_address or 'unknown'}"
                failed_attempts[key] = failed_attempts.get(key, 0) + 1

        # Detect anomalies
        for user_id, user_events in user_activity.items():
            # Unusual activity volume
            if len(user_events) > 100:  # Threshold
                anomalies.append({
                    "type": "high_activity_volume",
                    "user_id": user_id,
                    "event_count": len(user_events),
                    "window_hours": window_hours,
                })

            # Unusual access patterns
            unique_resources = set(f"{e.resource_type}:{e.resource_id}" for e in user_events if e.resource_type)
            if len(unique_resources) > 50:  # Threshold
                anomalies.append({
                    "type": "unusual_resource_access",
                    "user_id": user_id,
                    "unique_resources": len(unique_resources),
                })

        # Check for brute force attempts
        for key, count in failed_attempts.items():
            if count > 5:  # Threshold
                user_id, ip_address = key.split(":")
                anomalies.append({
                    "type": "potential_brute_force",
                    "user_id": user_id if user_id != "unknown" else None,
                    "ip_address": ip_address if ip_address != "unknown" else None,
                    "failed_attempts": count,
                })

        return anomalies

    async def _flush_buffer(self):
        """Flush event buffer to storage."""
        if not self._buffer:
            return

        try:
            events_to_flush = self._buffer[:]
            self._buffer.clear()

            await self.storage.store_events(events_to_flush)
            self._stats["batch_flushes"] += 1

            logger.debug(f"Flushed {len(events_to_flush)} audit events")

        except Exception as e:
            logger.error(f"Failed to flush audit buffer: {e}")
            self._stats["errors"] += 1
            self._stats["events_dropped"] += len(events_to_flush)

    async def _periodic_flush(self):
        """Periodically flush buffer."""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_buffer()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}")

    async def _send_alert(self, event: AuditEvent):
        """Send alert for critical events."""
        # Send to notification service
        try:
            from dotmac.platform.communications import send_notification

            await send_notification(
                channel="security_alerts",
                subject=f"Critical Audit Event: {event.action}",
                message={
                    "event_id": event.id,
                    "category": event.category.value,
                    "action": event.action,
                    "level": event.level.value,
                    "user_id": event.user_id,
                    "tenant_id": event.tenant_id,
                    "details": event.details,
                },
                priority="high",
            )
        except Exception as e:
            logger.error(f"Failed to send audit alert: {e}")

    @standard_exception_handler
    async def cleanup_old_events(self, retention_days: int = 90):
        """Clean up old audit events."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        deleted_count = await self.storage.delete_events_before(cutoff_date)
        logger.info(f"Cleaned up {deleted_count} old audit events")
        return deleted_count

    def get_stats(self) -> dict[str, Any]:
        """Get aggregator statistics."""
        return {
            **self._stats,
            "buffer_size": len(self._buffer),
            "is_running": self._flush_task is not None and not self._flush_task.done(),
        }


# Global instance
_aggregator: Optional[AuditAggregator] = None


async def get_audit_aggregator() -> AuditAggregator:
    """Get global audit aggregator instance."""
    global _aggregator

    if _aggregator is None:
        _aggregator = AuditAggregator()
        await _aggregator.start()

    return _aggregator


# Background task for archival
@task(queue="low_priority")
async def archive_old_audit_events():
    """Archive old audit events to long-term storage."""
    aggregator = await get_audit_aggregator()
    await aggregator.cleanup_old_events()