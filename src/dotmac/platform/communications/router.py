"""
Communications API router.

Provides REST endpoints for email, notifications, and events.
"""

from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field

from dotmac.platform.auth.core import UserInfo, get_current_user
from dotmac.platform.communications import (
    NotificationChannel,
    NotificationPriority,
    NotificationService,
    NotificationStatus,
)

logger = structlog.get_logger(__name__)

# Create router
communications_router = APIRouter()
comms_router = communications_router  # Alias for backward compatibility

# Service instance
notification_service = NotificationService()


# Request/Response Models
class EmailRequest(BaseModel):
    """Email sending request."""

    to: List[EmailStr] = Field(..., description="Recipient email addresses")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body (HTML supported)")
    cc: Optional[List[EmailStr]] = Field(None, description="CC recipients")
    bcc: Optional[List[EmailStr]] = Field(None, description="BCC recipients")
    priority: NotificationPriority = Field(
        default=NotificationPriority.NORMAL, description="Email priority"
    )


class NotificationRequest(BaseModel):
    """Generic notification request."""

    channel: NotificationChannel = Field(..., description="Notification channel")
    recipient: str = Field(..., description="Recipient identifier")
    subject: str = Field(..., description="Notification subject")
    message: str = Field(..., description="Notification message")
    priority: NotificationPriority = Field(
        default=NotificationPriority.NORMAL, description="Priority level"
    )
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class NotificationResponse(BaseModel):
    """Notification response."""

    notification_id: str = Field(..., description="Notification ID")
    status: NotificationStatus = Field(..., description="Notification status")
    channel: NotificationChannel = Field(..., description="Channel used")
    timestamp: str = Field(..., description="Timestamp")


class EventRequest(BaseModel):
    """Event publishing request."""

    event_type: str = Field(..., description="Event type")
    data: dict = Field(..., description="Event data")
    target: Optional[str] = Field(None, description="Target service/component")


# Endpoints
@communications_router.post("/email", response_model=NotificationResponse)
async def send_email(
    request: EmailRequest,
    current_user: UserInfo = Depends(get_current_user),
) -> NotificationResponse:
    """
    Send an email notification.
    """
    try:
        # Create notification request
        from dotmac.platform.communications import NotificationRequest as CommNotificationRequest

        notif_request = CommNotificationRequest(
            type=NotificationChannel.EMAIL,
            recipient=request.to[0] if request.to else "",
            subject=request.subject,
            content=request.body,
            metadata={
                "cc": request.cc,
                "bcc": request.bcc,
                "all_recipients": request.to,
                "priority": request.priority.value,
                "sender_id": current_user.user_id,
            },
        )

        result = notification_service.send(notif_request)
        notification_id = result.id

        return NotificationResponse(
            notification_id=notification_id,
            status=NotificationStatus.SENT,
            channel=NotificationChannel.EMAIL,
            timestamp=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email",
        )


@communications_router.post("/notify", response_model=NotificationResponse)
async def send_notification(
    request: NotificationRequest,
    current_user: UserInfo = Depends(get_current_user),
) -> NotificationResponse:
    """
    Send a notification through specified channel.
    """
    try:
        from dotmac.platform.communications import NotificationRequest as CommNotificationRequest

        notif_request = CommNotificationRequest(
            type=request.channel,
            recipient=request.recipient,
            subject=request.subject,
            content=request.message,
            metadata={
                **(request.metadata or {}),
                "priority": request.priority.value,
                "sender_id": current_user.user_id,
            },
        )

        result = notification_service.send(notif_request)
        notification_id = result.id

        return NotificationResponse(
            notification_id=notification_id,
            status=NotificationStatus.SENT,
            channel=request.channel,
            timestamp=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}",
        )


@communications_router.post("/events")
async def publish_event(
    request: EventRequest,
    current_user: UserInfo = Depends(get_current_user),
) -> dict:
    """
    Publish an event to the event bus.
    """
    try:
        # Here you would integrate with your event bus (e.g., Celery, RabbitMQ, Kafka)
        event_id = f"evt_{datetime.utcnow().timestamp()}"

        logger.info(
            "Event published",
            event_id=event_id,
            event_type=request.event_type,
            user_id=current_user.user_id,
        )

        return {
            "event_id": event_id,
            "status": "published",
            "event_type": request.event_type,
        }
    except Exception as e:
        logger.error(f"Failed to publish event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to publish event",
        )


@communications_router.get("/notifications")
async def list_notifications(
    status: Optional[NotificationStatus] = Query(None, description="Filter by status"),
    channel: Optional[NotificationChannel] = Query(None, description="Filter by channel"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    current_user: UserInfo = Depends(get_current_user),
) -> dict:
    """
    List notifications for the current user.
    """
    # This would typically fetch from a database
    return {
        "notifications": [],
        "total": 0,
        "filters": {
            "status": status,
            "channel": channel,
        },
    }


@communications_router.get("/notifications/{notification_id}")
async def get_notification(
    notification_id: str,
    current_user: UserInfo = Depends(get_current_user),
) -> dict:
    """
    Get details of a specific notification.
    """
    # This would typically fetch from a database
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Notification {notification_id} not found",
    )


# Add missing import
from datetime import datetime

# Export router
__all__ = ["communications_router", "comms_router"]