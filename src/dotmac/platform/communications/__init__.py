"""
Open-source, vendor-agnostic communications module for DotMac Platform Services.

Provides generic interfaces for:
- Email (SMTP)
- SMS (Generic HTTP gateway)
- WebSockets (Real-time communication)
- Events (Pub/sub messaging)
- Webhooks (HTTP notifications)

No vendor lock-in, all configuration-based.
"""

from .config import CommunicationsConfig
from .email import EmailService, EmailMessage
from .events import EventBus, Event
from .sms import SMSService, SMSMessage
from .webhooks import WebhookService, WebhookRequest
from .websocket import WebSocketManager

__all__ = [
    # Configuration
    "CommunicationsConfig",
    # Email
    "EmailService",
    "EmailMessage",
    # SMS
    "SMSService",
    "SMSMessage",
    # Events
    "EventBus",
    "Event",
    # Webhooks
    "WebhookService",
    "WebhookRequest",
    # WebSocket
    "WebSocketManager",
]