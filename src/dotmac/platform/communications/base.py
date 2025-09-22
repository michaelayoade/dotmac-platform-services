"""Core models and enums for the communications subsystem.

These lightweight definitions are intentionally self-contained so they can be
imported by tests without pulling in the heavier communications stack.
"""

from __future__ import annotations

from datetime import datetime, UTC
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Supported communication transport types."""

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"


class MessagePriority(str, Enum):
    """Supported message priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class DeliveryStatus(str, Enum):
    """High-level delivery lifecycle states."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"


class Message(BaseModel):
    """Representation of an outbound communication message."""

    message_id: str = Field(default_factory=lambda: str(uuid4()))
    recipient: str | list[str]
    content: str
    subject: str | None = None
    message_type: MessageType = MessageType.EMAIL
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)
    template_variables: dict[str, Any] | None = None
    attachments: list[str] = Field(default_factory=list)
    content_type: str = "text/plain"
    headers: dict[str, str] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    provider_options: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "copy_on_model_validation": False,
        "str_strip_whitespace": False,
    }


class NotificationChannel(BaseModel):
    """Minimal channel definition used for lightweight testing."""

    name: str
    channel_type: MessageType
    endpoint: str
    configuration: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    credentials: dict[str, Any] | None = None
    rate_limit_per_minute: int | None = None
    rate_limit_per_hour: int | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)


class CommunicationResult(BaseModel):
    """Result information returned after attempting delivery."""

    message_id: str
    status: DeliveryStatus
    success: bool
    error_message: str | None = None
    provider_response: dict[str, Any] | None = None
    attempts: int = 0
    retry_after: datetime | None = None
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    channel: MessageType | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "copy_on_model_validation": False,
    }


__all__ = [
    "MessageType",
    "MessagePriority",
    "DeliveryStatus",
    "Message",
    "NotificationChannel",
    "CommunicationResult",
]
