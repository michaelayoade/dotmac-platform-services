"""
Push Notification Service using DRY patterns

Leverages existing RouterFactory patterns and universal communication config
to provide push notifications with delivery guarantees.
"""

import asyncio
import json

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from dotmac.platform.core.decorators import rate_limit, standard_exception_handler
from fastapi import HTTPException
from pydantic import BaseModel, Field

from .internal.communication import UniversalCommunicationService
from .internal.events import EventManager, EventPriority, WebSocketEvent
from .models import NotificationRequest, NotificationResponse, NotificationStatus

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

class PushNotificationConfig(BaseModel):
    """Push notification configuration model."""

    vapid_public_key: Optional[str] = None
    vapid_private_key: Optional[str] = None
    vapid_subject: str = "mailto:admin@dotmac.com"
    default_ttl: int = 86400  # 24 hours
    max_payload_size: int = 4096  # 4KB FCM limit
    retry_attempts: int = 3
    retry_delay: int = 2  # seconds

class PushSubscription(BaseModel):
    """Web push subscription model."""

    subscription_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    tenant_id: Optional[str] = None
    endpoint: str
    p256dh_key: str
    auth_key: str
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class PushNotificationService:
    """
    DRY-compliant push notification service leveraging existing patterns.

    Uses:
    - RouterFactory patterns for API consistency
    - UniversalCommunicationService for channel management
    - WebSocket EventManager for delivery guarantees
    - Standard exception handling patterns
    """

    def __init__(
        self,
        event_manager: EventManager,
        communication_service: UniversalCommunicationService,
        config: Optional[PushNotificationConfig] = None,
    ):
        self.event_manager = event_manager
        self.communication_service = communication_service
        self.config = config or PushNotificationConfig()

        # In-memory storage (can be replaced with Redis/DB)
        self.subscriptions: dict[str, PushSubscription] = {}
        self.user_subscriptions: dict[str, set[str]] = {}  # user_id -> subscription_ids
        self.pending_notifications: list[dict[str, Any]] = []

        # Delivery tracking
        self.delivery_metrics = {
            "sent": 0,
            "delivered": 0,
            "failed": 0,
            "subscriptions_active": 0,
        }

        # Register push notification event handler
        asyncio.create_task(self._register_event_handlers())

    async def _register_event_handlers(self):
        """Register with EventManager to handle push notification events."""
        await self.event_manager.add_event_handler(
            "push_notification", self._handle_push_notification_event
        )
        await self.event_manager.add_event_handler("notification", self._handle_notification_event)

    @standard_exception_handler
    @rate_limit(max_requests=100, time_window_seconds=60)
    async def subscribe(
        self,
        user_id: str,
        subscription_data: dict[str, Any],
        tenant_id: Optional[str] = None,
    ) -> dict[str, str]:
        """
        Subscribe user to push notifications.

        Follows DRY pattern: similar to WebSocket EventManager.subscribe()
        """
        try:
            # Validate subscription data
            required_fields = ["endpoint", "keys"]
            if not all(field in subscription_data for field in required_fields):
                raise HTTPException(
                    status_code=400, detail="Missing required fields: endpoint, keys"
                )

            keys = subscription_data["keys"]
            if not all(key in keys for key in ["p256dh", "auth"]):
                raise HTTPException(status_code=400, detail="Missing required keys: p256dh, auth")

            # Create subscription
            subscription = PushSubscription(
                user_id=user_id,
                tenant_id=tenant_id,
                endpoint=subscription_data["endpoint"],
                p256dh_key=keys["p256dh"],
                auth_key=keys["auth"],
                user_agent=subscription_data.get("userAgent"),
            )

            # Store subscription
            self.subscriptions[subscription.subscription_id] = subscription

            if user_id not in self.user_subscriptions:
                self.user_subscriptions[user_id] = set()
            self.user_subscriptions[user_id].add(subscription.subscription_id)

            self.delivery_metrics["subscriptions_active"] += 1

            # Publish subscription event for analytics
            await self.event_manager.publish_event(
                WebSocketEvent(
                    event_type="push_subscription_created",
                    data={
                        "user_id": user_id,
                        "subscription_id": subscription.subscription_id,
                        "endpoint": subscription.endpoint[:50] + "...",  # Truncated for privacy
                    },
                    tenant_id=tenant_id,
                    user_id=user_id,
                    priority=EventPriority.NORMAL,
                    metadata={"source": "push_service"},
                )
            )

            logger.info(f"Push subscription created for user {user_id}")
            return {"subscription_id": subscription.subscription_id, "status": "subscribed"}

        except Exception as e:
            logger.error(f"Push subscription error: {e}")
            raise HTTPException(status_code=500, detail=f"Subscription failed: {str(e)}") from e

    @standard_exception_handler
    @rate_limit(max_requests=50, time_window_seconds=60)
    async def unsubscribe(
        self, subscription_id: str, user_id: Optional[str] = None
    ) -> dict[str, str]:
        """
        Unsubscribe from push notifications.

        Follows DRY pattern: similar to WebSocket EventManager.unsubscribe()
        """
        if subscription_id not in self.subscriptions:
            raise HTTPException(status_code=404, detail="Subscription not found")

        subscription = self.subscriptions[subscription_id]

        # Verify user owns subscription (if user_id provided)
        if user_id and subscription.user_id != user_id:
            raise HTTPException(status_code=403, detail="Subscription access denied")

        # Remove subscription
        del self.subscriptions[subscription_id]

        if subscription.user_id in self.user_subscriptions:
            self.user_subscriptions[subscription.user_id].discard(subscription_id)
            if not self.user_subscriptions[subscription.user_id]:
                del self.user_subscriptions[subscription.user_id]

        self.delivery_metrics["subscriptions_active"] -= 1

        logger.info(f"Push subscription removed: {subscription_id}")
        return {"subscription_id": subscription_id, "status": "unsubscribed"}

    @standard_exception_handler
    @rate_limit(max_requests=200, time_window_seconds=60)
    async def send_push_notification(
        self,
        user_ids: list[str],
        title: str,
        body: str,
        data: Optional[dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        ttl: Optional[int] = None,
    ) -> NotificationResponse:
        """
        Send push notification to users.

        Leverages UniversalCommunicationService for actual delivery
        and EventManager for delivery guarantees.
        """
        notification_id = str(uuid4())

        try:
            # Find user subscriptions
            target_subscriptions = []
            for user_id in user_ids:
                if user_id in self.user_subscriptions:
                    for sub_id in self.user_subscriptions[user_id]:
                        if sub_id in self.subscriptions and self.subscriptions[sub_id].is_active:
                            target_subscriptions.append(self.subscriptions[sub_id])

            if not target_subscriptions:
                return NotificationResponse(
                    success=False,
                    notification_id=notification_id,
                    status=NotificationStatus.FAILED,
                    message="No active subscriptions found",
                    metadata={"target_users": user_ids},
                )

            # Create push notification payload
            payload = {
                "notification": {
                    "title": title,
                    "body": body,
                    "icon": "/icons/notification-icon.png",
                    "badge": "/icons/badge-icon.png",
                    "tag": notification_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                "data": data or {},
            }

            # Validate payload size
            payload_size = len(json.dumps(payload))
            if payload_size > self.config.max_payload_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"Payload size {payload_size} exceeds limit {self.config.max_payload_size}",
                )

            # Send via UniversalCommunicationService using firebase_push provider
            communication_request = NotificationRequest(
                tenant_id=tenant_id,
                notification_type="transactional",
                recipients=[sub.endpoint for sub in target_subscriptions],
                channels=["push"],
                subject=title,
                body=body,
                template_data=payload,
                metadata={
                    "notification_id": notification_id,
                    "vapid_keys": {
                        "public": self.config.vapid_public_key,
                        "private": self.config.vapid_private_key,
                        "subject": self.config.vapid_subject,
                    },
                    "ttl": ttl or self.config.default_ttl,
                },
            )

            # Use communication service for delivery
            comm_response = await self.communication_service.send_notification(
                communication_request
            )

            # Create WebSocket event for delivery tracking
            delivery_event = WebSocketEvent(
                event_type="push_notification_sent",
                data={
                    "notification_id": notification_id,
                    "title": title,
                    "body": body,
                    "target_count": len(target_subscriptions),
                    "success": comm_response.success,
                },
                tenant_id=tenant_id,
                priority=priority,
                metadata={
                    "source": "push_service",
                    "delivery_method": "fcm",
                },
            )

            # Publish to EventManager for WebSocket clients and delivery guarantees
            await self.event_manager.publish_event(delivery_event)

            # Update metrics
            if comm_response.success:
                self.delivery_metrics["sent"] += len(target_subscriptions)
                status = NotificationStatus.SENT
            else:
                self.delivery_metrics["failed"] += len(target_subscriptions)
                status = NotificationStatus.FAILED

            return NotificationResponse(
                success=comm_response.success,
                notification_id=notification_id,
                status=status,
                message=comm_response.message,
                channel_results=comm_response.channel_results,
                metadata={
                    "target_users": user_ids,
                    "subscription_count": len(target_subscriptions),
                    "payload_size": payload_size,
                },
            )

        except Exception as e:
            logger.error(f"Push notification send error: {e}")
            self.delivery_metrics["failed"] += len(user_ids)

            return NotificationResponse(
                success=False,
                notification_id=notification_id,
                status=NotificationStatus.FAILED,
                message=f"Send failed: {str(e)}",
                metadata={"target_users": user_ids, "error": str(e)},
            )

    async def _handle_push_notification_event(self, event: WebSocketEvent):
        """Handle push notification events from EventManager."""
        try:
            data = event.data

            # Extract notification details
            user_ids = data.get("user_ids", [])
            title = data.get("title", "Notification")
            body = data.get("body", "")
            notification_data = data.get("data", {})

            # Send push notification
            await self.send_push_notification(
                user_ids=user_ids,
                title=title,
                body=body,
                data=notification_data,
                tenant_id=event.tenant_id,
                priority=event.priority,
            )

        except Exception as e:
            logger.error(f"Push notification event handler error: {e}")

    async def _handle_notification_event(self, event: WebSocketEvent):
        """Handle general notification events and convert to push if needed."""
        try:
            # Check if this notification should trigger push
            metadata = event.metadata or {}
            if not metadata.get("enable_push", False):
                return

            data = event.data
            await self.send_push_notification(
                user_ids=[event.user_id] if event.user_id else [],
                title=data.get("title", "Notification"),
                body=data.get("message", ""),
                data=data,
                tenant_id=event.tenant_id,
                priority=event.priority,
            )

        except Exception as e:
            logger.error(f"Notification event handler error: {e}")

    def get_user_subscriptions(self, user_id: str) -> list[dict[str, Any]]:
        """Get all subscriptions for a user."""
        if user_id not in self.user_subscriptions:
            return []

        subscriptions = []
        for sub_id in self.user_subscriptions[user_id]:
            if sub_id in self.subscriptions:
                sub = self.subscriptions[sub_id]
                subscriptions.append(
                    {
                        "subscription_id": sub.subscription_id,
                        "endpoint": sub.endpoint[:50] + "...",  # Truncated for privacy
                        "created_at": sub.created_at.isoformat(),
                        "last_used": sub.last_used.isoformat(),
                        "is_active": sub.is_active,
                    }
                )

        return subscriptions

    def get_metrics(self) -> dict[str, Any]:
        """Get push notification service metrics."""
        return {
            **self.delivery_metrics,
            "total_subscriptions": len(self.subscriptions),
            "active_subscriptions": sum(1 for s in self.subscriptions.values() if s.is_active),
            "users_with_subscriptions": len(self.user_subscriptions),
        }

    async def cleanup_expired_subscriptions(self, days_inactive: int = 30):
        """Clean up inactive subscriptions."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_inactive)
        expired_ids = []

        for sub_id, subscription in self.subscriptions.items():
            if subscription.last_used < cutoff_date:
                expired_ids.append(sub_id)

        for sub_id in expired_ids:
            await self.unsubscribe(sub_id)

        logger.info(f"Cleaned up {len(expired_ids)} expired push subscriptions")
        return len(expired_ids)
