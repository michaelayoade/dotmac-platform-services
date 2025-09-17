"""
DotMac Comprehensive Notification System

This package provides a complete notification system with:
- Multi-channel delivery (email, SMS, push, webhook, Slack)
- Task notification system with retry logic and templates
- Push notification service with WebSocket integration
- Rate limiting and delivery tracking
- Template-based notification formatting

Components:
- Core unified notification service
- Push notification service with WebSocket events
- Task notification system for background processes
- Comprehensive models and configuration
"""

from .models import (
    BulkNotificationRequest,
    BulkNotificationResponse,
    NotificationPriority,
    NotificationRequest,
    NotificationResponse,
    NotificationStatus,
    NotificationTemplate,
    NotificationType,
)
from .service import UnifiedNotificationService

__all__ = [
    "UnifiedNotificationService",
    "NotificationRequest",
    "NotificationResponse",
    "BulkNotificationRequest",
    "BulkNotificationResponse",
    "NotificationTemplate",
    "NotificationStatus",
    "NotificationPriority",
    "NotificationType",
]
