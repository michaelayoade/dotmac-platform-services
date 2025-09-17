"""
Unified Notification Service (adapter/stub)

Provides a thin orchestration layer over the unified notification models.
This implementation is intentionally minimal to avoid pulling heavy
dependencies during unit tests. It can be extended to integrate with the
platform's omnichannel delivery services and plugin system.
"""

from __future__ import annotations

import uuid

from .models import (
    BulkNotificationRequest,
    BulkNotificationResponse,
    NotificationRequest,
    NotificationResponse,
    NotificationStatus,
)


class UnifiedNotificationService:
    """Lightweight notification service facade.

    Methods return successful responses immediately. In production, this class
    should delegate to the platform's omnichannel delivery engines and
    persistence/audit layers.
    """

    def send(self, request: NotificationRequest) -> NotificationResponse:
        notification_id = str(uuid.uuid4())
        return NotificationResponse(
            success=True,
            notification_id=notification_id,
            status=NotificationStatus.SENT,
            channel_results={channel: {"status": "queued"} for channel in request.channels},
            metadata=request.metadata,
        )

    def send_bulk(self, request: BulkNotificationRequest) -> BulkNotificationResponse:
        results: list[NotificationResponse] = []
        successful = 0

        for n in request.notifications:
            resp = self.send(n)
            results.append(resp)
            if resp.success:
                successful += 1

        return BulkNotificationResponse(
            total_notifications=len(request.notifications),
            successful=successful,
            failed=len(request.notifications) - successful,
            results=results,
        )
