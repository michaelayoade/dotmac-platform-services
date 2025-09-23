"""
Simple communications module for basic notification functionality.

This module provides minimal notification capabilities for the platform.
For production use, integrate with external services like SendGrid, Twilio, etc.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)

if TYPE_CHECKING:
    from ..integrations import EmailIntegration, SMSIntegration


class NotificationType(str, Enum):
    """Notification types."""

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"


# Alias for compatibility
NotificationChannel = NotificationType


class NotificationPriority(str, Enum):
    """Notification priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(str, Enum):
    """Notification delivery status."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class NotificationRequest:
    """Notification request."""

    type: NotificationType
    recipient: str
    subject: Optional[str] = None
    content: str = ""
    metadata: Optional[Dict[str, Any]] = None
    template_id: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None


@dataclass
class NotificationResponse:
    """Notification response."""

    id: str
    status: NotificationStatus
    message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class NotificationTemplate:
    """Notification template."""

    id: str
    name: str
    type: NotificationType
    subject_template: Optional[str] = None
    content_template: str = ""
    metadata: Optional[Dict[str, Any]] = None


class NotificationService:
    """Basic notification service implementation."""

    def __init__(self, smtp_host: str = "localhost", smtp_port: int = 587):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.templates: Dict[str, NotificationTemplate] = {}
        self._sent_notifications: List[NotificationResponse] = []
        self._integration_service = None
        self._email_integration: Optional["EmailIntegration"] = None
        self._sms_integration: Optional["SMSIntegration"] = None

    async def initialize_integrations(self):
        """Initialize integration service if available."""
        try:
            from ..integrations import EmailIntegration, SMSIntegration, get_integration_async

            # Get integrations and cast to correct types
            email_integration = await get_integration_async("email")
            if email_integration and isinstance(email_integration, EmailIntegration):
                self._email_integration = email_integration

            sms_integration = await get_integration_async("sms")
            if sms_integration and isinstance(sms_integration, SMSIntegration):
                self._sms_integration = sms_integration
            logger.info(
                "Initialized integrations",
                email_available=self._email_integration is not None,
                sms_available=self._sms_integration is not None,
            )
        except ImportError:
            logger.info("Integrations module not available, using basic implementations")

    def add_template(self, template: NotificationTemplate) -> None:
        """Add a notification template."""
        self.templates[template.id] = template
        logger.info("Added notification template", template_id=template.id, type=template.type)

    def send(self, request: NotificationRequest) -> NotificationResponse:
        """Send a notification."""
        notification_id = f"notif_{len(self._sent_notifications) + 1}"

        try:
            if request.type == NotificationType.EMAIL:
                response = self._send_email(notification_id, request)
            elif request.type == NotificationType.SMS:
                response = self._send_sms(notification_id, request)
            elif request.type == NotificationType.PUSH:
                response = self._send_push(notification_id, request)
            elif request.type == NotificationType.WEBHOOK:
                response = self._send_webhook(notification_id, request)
            else:
                response = NotificationResponse(
                    id=notification_id,
                    status=NotificationStatus.FAILED,
                    message=f"Unsupported notification type: {request.type}",
                )

            self._sent_notifications.append(response)
            return response
        except Exception as e:
            logger.error("Failed to send notification", error=str(e), type=request.type)
            response = NotificationResponse(
                id=notification_id, status=NotificationStatus.FAILED, message=str(e)
            )
            self._sent_notifications.append(response)
            return response

    def _send_email(
        self, notification_id: str, request: NotificationRequest
    ) -> NotificationResponse:
        """Send email notification."""
        try:
            # Try to use integration service first
            if self._email_integration is not None:
                import asyncio

                # Check if the email integration has send_email method
                if hasattr(self._email_integration, "send_email"):
                    result = asyncio.run(
                        self._email_integration.send_email(
                            to=request.recipient,
                            subject=request.subject or "Notification",
                            content=request.content,
                            html_content=(
                                request.metadata.get("html_content") if request.metadata else None
                            ),
                        )
                    )

                    return NotificationResponse(
                        id=notification_id,
                        status=(
                            NotificationStatus.SENT
                            if result.get("status") == "sent"
                            else NotificationStatus.FAILED
                        ),
                        message=result.get("message", "Email sent via integration"),
                        metadata=result,
                    )

            # Fallback to simulation
            logger.info(
                "Simulating email send",
                notification_id=notification_id,
                recipient=request.recipient,
                subject=request.subject,
            )

            return NotificationResponse(
                id=notification_id,
                status=NotificationStatus.SENT,
                message="Email sent successfully (simulated)",
            )
        except Exception as e:
            return NotificationResponse(
                id=notification_id,
                status=NotificationStatus.FAILED,
                message=f"Email send failed: {str(e)}",
            )

    def _send_sms(self, notification_id: str, request: NotificationRequest) -> NotificationResponse:
        """Send SMS notification."""
        try:
            # Try to use integration service first
            if self._sms_integration is not None:
                import asyncio

                # Check if the SMS integration has send_sms method
                if hasattr(self._sms_integration, "send_sms"):
                    result = asyncio.run(
                        self._sms_integration.send_sms(
                            to=request.recipient, message=request.content
                        )
                    )

                    return NotificationResponse(
                        id=notification_id,
                        status=(
                            NotificationStatus.SENT
                            if result.get("status") == "sent"
                            else NotificationStatus.FAILED
                        ),
                        message=result.get("message", "SMS sent via integration"),
                        metadata=result,
                    )

            # Fallback to simulation
            logger.info(
                "Simulating SMS send", notification_id=notification_id, recipient=request.recipient
            )

            return NotificationResponse(
                id=notification_id,
                status=NotificationStatus.SENT,
                message="SMS sent successfully (simulated)",
            )
        except Exception as e:
            return NotificationResponse(
                id=notification_id,
                status=NotificationStatus.FAILED,
                message=f"SMS send failed: {str(e)}",
            )

    def _send_push(
        self, notification_id: str, request: NotificationRequest
    ) -> NotificationResponse:
        """Send push notification."""
        # Simulate push notification - integrate with FCM, APNs, etc. in production
        logger.info(
            "Simulating push notification",
            notification_id=notification_id,
            recipient=request.recipient,
        )

        return NotificationResponse(
            id=notification_id,
            status=NotificationStatus.SENT,
            message="Push notification sent successfully (simulated)",
        )

    def _send_webhook(
        self, notification_id: str, request: NotificationRequest
    ) -> NotificationResponse:
        """Send webhook notification."""
        # Simulate webhook sending - use httpx or requests in production
        logger.info(
            "Simulating webhook send", notification_id=notification_id, recipient=request.recipient
        )

        return NotificationResponse(
            id=notification_id,
            status=NotificationStatus.SENT,
            message="Webhook sent successfully (simulated)",
        )

    def get_status(self, notification_id: str) -> Optional[NotificationResponse]:
        """Get notification status."""
        for notification in self._sent_notifications:
            if notification.id == notification_id:
                return notification
        return None

    def list_notifications(self) -> List[NotificationResponse]:
        """List all sent notifications."""
        return self._sent_notifications.copy()


# Global instance
_notification_service: Optional[NotificationService] = None


def get_notification_service(
    smtp_host: str = "localhost", smtp_port: int = 587, refresh: bool = False
) -> NotificationService:
    """Get or create the global notification service."""
    global _notification_service
    if _notification_service is None or refresh:
        _notification_service = NotificationService(smtp_host, smtp_port)
    return _notification_service


def send_notification(request: NotificationRequest) -> NotificationResponse:
    """Send a notification using the global service."""
    service = get_notification_service()
    return service.send(request)


# Aliases for backward compatibility
UnifiedNotificationService = NotificationService
EmailNotifier = NotificationService
SMSNotifier = NotificationService
PushNotifier = NotificationService


__all__ = [
    "NotificationService",
    "UnifiedNotificationService",
    "EmailNotifier",
    "SMSNotifier",
    "PushNotifier",
    "NotificationRequest",
    "NotificationResponse",
    "NotificationTemplate",
    "NotificationType",
    "NotificationChannel",
    "NotificationPriority",
    "NotificationStatus",
    "get_notification_service",
    "send_notification",
]
