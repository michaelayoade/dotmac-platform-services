"""
Notification Service Models

Simple models that map to existing omnichannel service structures.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class NotificationStatus(str, Enum):
    """Notification delivery status"""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationPriority(str, Enum):
    """Notification priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationType(str, Enum):
    """Types of notifications and channels"""

    # Channel types
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"

    # Notification types
    TRANSACTIONAL = "transactional"
    MARKETING = "marketing"
    SYSTEM_ALERT = "system_alert"
    SERVICE_UPDATE = "service_update"
    BILLING_NOTICE = "billing_notice"
    SECURITY_ALERT = "security_alert"


class NotificationRequest(BaseModel):
    """Unified notification request"""

    tenant_id: Optional[str] = None
    notification_type: NotificationType
    recipients: list[str] = Field(default_factory=list)
    channels: list[str] = Field(default=["email"])  # Will map to ChannelType
    subject: Optional[str] = None
    body: Optional[str] = None
    template_id: Optional[str] = None
    template_data: Optional[dict[str, Any]] = None
    priority: NotificationPriority = NotificationPriority.NORMAL
    metadata: Optional[dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # Legacy/alternative field names for backward compatibility
    recipient: Optional[str] = None
    message: Optional[str] = None

    def model_post_init(self, __context):
        """Handle legacy field names."""
        if self.recipient and not self.recipients:
            self.recipients = [self.recipient]
        if self.message and not self.body:
            self.body = self.message


class NotificationResponse(BaseModel):
    """Unified notification response"""

    success: bool = True  # Default to True for backward compatibility
    notification_id: Optional[str] = None
    status: NotificationStatus
    message: Optional[str] = None
    recipient: Optional[str] = None  # Backward compatibility
    channel_results: dict[str, Any] = Field(default_factory=dict)
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BulkNotificationRequest(BaseModel):
    """Bulk notification request"""

    notifications: list[NotificationRequest]
    batch_size: Optional[int] = 100
    max_concurrent: Optional[int] = 10


class BulkNotificationResponse(BaseModel):
    """Bulk notification response"""

    total_notifications: int
    successful: int
    failed: int
    results: list[NotificationResponse]
    metadata: Optional[dict[str, Any]] = None


class NotificationTemplate(BaseModel):
    """Simple template model for caching"""

    template_id: Optional[str] = None  # Make optional for backward compatibility
    name: str
    subject_template: Optional[str] = None
    body_template: Optional[str] = None
    channels: list[str] = Field(default_factory=list)  # Make optional with default
    template_data_schema: Optional[dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Backward compatibility aliases
    subject: Optional[str] = None
    body: Optional[str] = None

    def model_post_init(self, __context):
        """Handle legacy field names."""
        if self.subject and not self.subject_template:
            self.subject_template = self.subject
        if self.body and not self.body_template:
            self.body_template = self.body
