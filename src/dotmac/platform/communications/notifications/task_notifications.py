"""
Comprehensive Task Notification and Webhook System

Provides flexible notification delivery for task completion events:
- Multiple notification channels (webhook, email, SMS, Slack, etc.)
- Reliable delivery with retry logic and dead letter queues
- Template-based notification formatting
- Notification history and delivery tracking
- Bulk notification processing
- Rate limiting and throttling
"""

import asyncio
import json
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

import httpx
from dotmac.platform.observability.logging import get_logger
from dotmac.platform.observability.unified_logging import get_logger

from dotmac.platform.tasks import TaskDispatchError, submit_background_task
from jinja2 import Template
from redis.asyncio import Redis as AsyncRedis

from .models import NotificationRequest as ExternalNotificationRequest

# Define missing Task-related classes locally
class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

class TaskError(Exception):
    """Task execution error."""

    pass

@dataclass
class TaskResult:
    """Result of task execution."""

    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    retry_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)

logger = get_logger(__name__)

class NotificationChannel(str, Enum):
    """Supported notification channels."""

    WEBHOOK = "webhook"
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    DISCORD = "discord"
    TEAMS = "teams"
    PUSH = "push"

class NotificationStatus(str, Enum):
    """Notification delivery status."""

    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    RETRY = "retry"
    EXPIRED = "expired"

class NotificationPriority(str, Enum):
    """Notification priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class NotificationTemplate:
    """Template for notification content."""

    template_id: str
    name: str
    channel: NotificationChannel
    subject_template: str
    body_template: str
    content_type: str = "text/plain"
    variables: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)

    def render(self, context: dict[str, Any]) -> dict[str, str]:
        """Render template with context variables."""
        try:
            subject = Template(self.subject_template).render(**context)
            body = Template(self.body_template).render(**context)

            return {"subject": subject, "body": body, "content_type": self.content_type}

        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return {
                "subject": f"Notification: {context.get('task_name', 'Unknown')}",
                "body": f"Task completed. Raw context: {json.dumps(context, default=str)}",
                "content_type": "text/plain",
            }

@dataclass
class _NotificationEnvelope:
    """Individual notification request."""

    notification_id: str
    channel: NotificationChannel
    recipient: str
    template_id: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    content_type: str = "text/plain"
    priority: NotificationPriority = NotificationPriority.NORMAL
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Delivery configuration
    max_retries: int = 3
    retry_delay: float = 60.0
    expires_at: Optional[datetime] = None

    # Runtime state
    status: NotificationStatus = NotificationStatus.PENDING
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "notification_id": self.notification_id,
            "channel": self.channel.value,
            "recipient": self.recipient,
            "template_id": self.template_id,
            "subject": self.subject,
            "body": self.body,
            "content_type": self.content_type,
            "priority": self.priority.value,
            "context": self.context,
            "metadata": self.metadata,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status.value,
            "attempts": self.attempts,
            "last_attempt": self.last_attempt.isoformat() if self.last_attempt else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NotificationRequest":
        """Create from dictionary."""
        return cls(
            notification_id=data["notification_id"],
            channel=NotificationChannel(data["channel"]),
            recipient=data["recipient"],
            template_id=data.get("template_id"),
            subject=data.get("subject"),
            body=data.get("body"),
            content_type=data.get("content_type", "text/plain"),
            priority=NotificationPriority(data.get("priority", "normal")),
            context=data.get("context", {}),
            metadata=data.get("metadata", {}),
            max_retries=data.get("max_retries", 3),
            retry_delay=data.get("retry_delay", 60.0),
            expires_at=(
                datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
            ),
            status=NotificationStatus(data.get("status", "pending")),
            attempts=data.get("attempts", 0),
            last_attempt=(
                datetime.fromisoformat(data["last_attempt"]) if data.get("last_attempt") else None
            ),
            sent_at=datetime.fromisoformat(data["sent_at"]) if data.get("sent_at") else None,
            error=data.get("error"),
        )


# Use internal model for backward compatibility
NotificationRequest = _NotificationEnvelope


class NotificationChannelProvider(ABC):
    """Abstract base class for notification channel providers."""

    @abstractmethod
    async def send_notification(self, request: NotificationRequest) -> bool:
        """Send notification through this channel."""
        pass

    @abstractmethod
    def get_channel(self) -> NotificationChannel:
        """Get the channel this provider handles."""
        pass

    @abstractmethod
    async def validate_recipient(self, recipient: str) -> bool:
        """Validate recipient format for this channel."""
        pass

class WebhookProvider(NotificationChannelProvider):
    """Webhook notification provider."""

    def __init__(self, timeout: int = 30, verify_ssl: bool = True):
        self.timeout = timeout
        self.verify_ssl = verify_ssl

    def get_channel(self) -> NotificationChannel:
        return NotificationChannel.WEBHOOK

    async def validate_recipient(self, recipient: str) -> bool:
        """Validate webhook URL format."""
        try:
            import urllib.parse

            result = urllib.parse.urlparse(recipient)
            # Only accept HTTP/HTTPS URLs for webhooks
            return bool(
                result.scheme in ("http", "https")
                and result.netloc
                and result.netloc.strip()  # Ensure netloc is not just whitespace
            )
        except Exception:
            return False

    async def send_notification(self, request: NotificationRequest) -> bool:
        """Send webhook notification."""
        try:
            payload = {
                "notification_id": request.notification_id,
                "subject": request.subject,
                "body": request.body,
                "content_type": request.content_type,
                "context": request.context,
                "metadata": request.metadata,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            async with httpx.AsyncClient(verify=self.verify_ssl) as client:
                response = await client.post(
                    request.recipient,
                    json=payload,
                    timeout=self.timeout,
                    headers={
                        "Content-Type": "application/json",
                        "X-Notification-ID": request.notification_id,
                        "X-Notification-Channel": "webhook",
                    },
                )

                response.raise_for_status()

                logger.info(
                    "Webhook notification sent",
                    extra={
                        "notification_id": request.notification_id,
                        "webhook_url": request.recipient,
                        "status_code": response.status_code,
                    },
                )

                return True

        except httpx.RequestError as e:
            logger.error(f"Webhook request failed: {e}")
            return False
        except httpx.HTTPStatusError as e:
            logger.error(f"Webhook HTTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"Webhook notification failed: {e}")
            return False

class EmailProvider(NotificationChannelProvider):
    """Email notification provider."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int = 587,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True,
        from_address: str = "noreply@dotmac.com",
        send_via_tasks: Optional[bool] = None,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.from_address = from_address
        if send_via_tasks is None:
            send_via_tasks = bool(os.getenv("SENDGRID_API_KEY"))
        self.send_via_tasks = send_via_tasks

    def get_channel(self) -> NotificationChannel:
        return NotificationChannel.EMAIL

    async def validate_recipient(self, recipient: str) -> bool:
        """Validate email address format."""
        import re

        # More strict email validation
        # - No consecutive dots
        # - No spaces
        # - No dots at start/end of local part
        # - Domain must have valid format (letters or IP addresses)
        pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9._+%-]*[a-zA-Z0-9])?@([a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$"
        return bool(re.match(pattern, recipient.strip()) and ".." not in recipient)

    async def send_notification(self, request: NotificationRequest) -> bool:
        """Send email notification."""
        if self.send_via_tasks:
            try:
                html_content = request.body if request.content_type == "text/html" else None
                text_content = request.body if request.content_type != "text/html" else None
                attachments = None
                if request.metadata and isinstance(request.metadata, dict):
                    attachments = request.metadata.get("attachments")

                submit_background_task(
                    "dotmac.platform.tasks.email.send_email",
                    request.recipient,
                    request.subject or "Task Notification",
                    html_content or text_content or "",
                    from_email=self.from_address,
                    text_content=text_content if html_content else None,
                    attachments=attachments,
                    metadata={
                        "notification_id": request.notification_id,
                        "channel": "email",
                    },
                )

                logger.info(
                    "Email notification dispatched via task",
                    extra={
                        "notification_id": request.notification_id,
                        "recipient": request.recipient,
                    },
                )
                return True
            except TaskDispatchError as exc:
                logger.error(
                    "Email task dispatch failed; falling back to SMTP",
                    extra={
                        "notification_id": request.notification_id,
                        "recipient": request.recipient,
                        "error": str(exc),
                    },
                )

        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.from_address
            msg["To"] = request.recipient
            msg["Subject"] = request.subject or "Task Notification"

            # Add body
            if request.content_type == "text/html":
                msg.attach(MIMEText(request.body, "html"))
            else:
                msg.attach(MIMEText(request.body, "plain"))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                if self.username and self.password:
                    server.login(self.username, self.password)

                server.send_message(msg)

            logger.info(
                "Email notification sent",
                extra={"notification_id": request.notification_id, "recipient": request.recipient},
            )

            return True

        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            return False

class SlackProvider(NotificationChannelProvider):
    """Slack notification provider."""

    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = bot_token

    def get_channel(self) -> NotificationChannel:
        return NotificationChannel.SLACK

    async def validate_recipient(self, recipient: str) -> bool:
        """Validate Slack channel or webhook URL."""
        import re

        # Support both webhook URLs and channel names
        if recipient.startswith("https://hooks.slack.com/"):
            # Slack webhook validation - must have proper path format
            webhook_pattern = r"^https://hooks\.slack\.com/services/[A-Za-z0-9]{3,}/[A-Za-z0-9]{3,}/[A-Za-z0-9_-]+$"
            return bool(re.match(webhook_pattern, recipient))
        elif recipient.startswith("#") and len(recipient) > 1:
            # Channel name validation
            return bool(re.match(r"^#[a-z0-9_-]+$", recipient))
        elif recipient.startswith("@") and len(recipient) > 1:
            # User mention validation
            return bool(re.match(r"^@[a-zA-Z0-9._-]+$", recipient))
        return False

    async def send_notification(self, request: NotificationRequest) -> bool:
        """Send Slack notification."""
        try:
            if request.recipient.startswith("https://hooks.slack.com/"):
                return await self._send_webhook_message(request)
            else:
                return await self._send_bot_message(request)

        except Exception as e:
            logger.error(f"Slack notification failed: {e}")
            return False

    async def _send_webhook_message(self, request: NotificationRequest) -> bool:
        """Send message via Slack webhook."""
        payload = {
            "text": request.subject,
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*{request.subject}*\n{request.body}"},
                }
            ],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(request.recipient, json=payload, timeout=10)
            response.raise_for_status()
            return True

    async def _send_bot_message(self, request: NotificationRequest) -> bool:
        """Send message via Slack Bot API."""
        if not self.bot_token:
            logger.error("Slack bot token not configured")
            return False

        payload = {"channel": request.recipient, "text": f"{request.subject}\n{request.body}"}

        headers = {"Authorization": f"Bearer {self.bot_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://slack.com/api/chat.postMessage", json=payload, headers=headers, timeout=10
            )
            response.raise_for_status()
            return True

class TaskNotificationService:
    """
    Comprehensive task notification service with multiple channels.

    Features:
    - Multiple notification channels with provider plugins
    - Template-based notification formatting
    - Reliable delivery with retry logic
    - Bulk notification processing
    - Delivery tracking and analytics
    - Rate limiting and throttling
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        service_id: Optional[str] = None,
        key_prefix: str = "dotmac_notifications",
        max_concurrent: int = 50,
        default_retry_delay: float = 60.0,
        default_max_retries: int = 3,
    ):
        self.redis_url = redis_url
        self.service_id = service_id or f"notification-service-{int(time.time())}"
        self.key_prefix = key_prefix
        self.max_concurrent = max_concurrent
        self.default_retry_delay = default_retry_delay
        self.default_max_retries = default_max_retries

        # Redis connection
        self._redis: Optional[AsyncRedis] = None

        # Service state
        self._is_running = False
        self._providers: dict[NotificationChannel, NotificationChannelProvider] = {}
        self._templates: dict[str, NotificationTemplate] = {}
        self._pending_notifications: asyncio.Queue = asyncio.Queue()
        self._rate_limiters: dict[str, list[float]] = {}

        # Background tasks
        self._processor_task: Optional[asyncio.Task] = None
        self._retry_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

        # Statistics
        self._stats = {
            "total_sent": 0,
            "total_failed": 0,
            "total_retries": 0,
            "channel_stats": {},
        }

    async def initialize(self):
        """Initialize notification service."""
        try:
            # Initialize Redis connection
            self._redis = AsyncRedis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=10,
                socket_timeout=30,
                retry_on_timeout=True,
                max_connections=20,
            )

            await self._redis.ping()

            # Load persisted templates
            await self._load_templates()

            # Initialize default providers
            self._register_default_providers()

            logger.info(
                "Notification service initialized",
                extra={
                    "service_id": self.service_id,
                    "providers": list(self._providers.keys()),
                    "templates": len(self._templates),
                },
            )

        except Exception as e:
            logger.error(f"Failed to initialize notification service: {e}")
            raise TaskError(f"Notification service initialization failed: {e}") from e

    async def start(self):
        """Start the notification service."""
        if self._is_running:
            return

        self._is_running = True

        # Start background processors
        self._processor_task = asyncio.create_task(self._notification_processor())
        self._retry_task = asyncio.create_task(self._retry_processor())
        self._cleanup_task = asyncio.create_task(self._cleanup_processor())

        logger.info("Notification service started", extra={"service_id": self.service_id})

    async def stop(self):
        """Stop the notification service."""
        logger.info("Stopping notification service")

        self._is_running = False

        # Cancel background tasks
        tasks = [self._processor_task, self._retry_task, self._cleanup_task]
        for task in tasks:
            if task:
                task.cancel()

        if tasks:
            await asyncio.gather(*[t for t in tasks if t], return_exceptions=True)

        # Close Redis connection
        if self._redis:
            await self._redis.close()

        logger.info("Notification service stopped")

    def register_provider(self, provider: NotificationChannelProvider):
        """Register a notification channel provider."""
        self._providers[provider.get_channel()] = provider
        logger.info(f"Registered provider for {provider.get_channel().value}")

    def register_template(self, template: NotificationTemplate):
        """Register a notification template."""
        self._templates[template.template_id] = template
        logger.info(f"Registered template: {template.template_id}")

    async def send_task_completion_notification(
        self,
        task_result: TaskResult,
        recipients: list[dict[str, Any]],
        template_id: Optional[str] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
    ) -> list[str]:
        """
        Send task completion notifications to multiple recipients.

        Args:
            task_result: Task execution result
            recipients: List of recipient configurations
            template_id: Optional template ID to use
            priority: Notification priority

        Returns:
            List of notification IDs
        """
        try:
            notification_ids = []

            # Build notification context from task result
            context = self._build_task_context(task_result)

            for recipient_config in recipients:
                notification_id = await self.send_notification(
                    channel=NotificationChannel(recipient_config["channel"]),
                    recipient=recipient_config["address"],
                    context=context,
                    template_id=template_id or recipient_config.get("template_id"),
                    priority=priority,
                    metadata={
                        "task_id": task_result.task_id,
                        "task_status": task_result.status.value,
                        "source": "task_completion",
                    },
                )

                if notification_id:
                    notification_ids.append(notification_id)

            return notification_ids

        except Exception as e:
            logger.error(f"Failed to send task completion notifications: {e}")
            return []

    async def send_notification(
        self,
        channel: NotificationChannel,
        recipient: str,
        subject: Optional[str] = None,
        body: Optional[str] = None,
        template_id: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Send a single notification.

        Args:
            channel: Notification channel
            recipient: Recipient address/identifier
            subject: Optional subject line
            body: Optional message body
            template_id: Optional template ID
            context: Template context variables
            priority: Notification priority
            metadata: Additional metadata

        Returns:
            Notification ID if queued successfully
        """
        try:
            # Validate channel provider
            if channel not in self._providers:
                logger.error(f"No provider registered for channel {channel}")
                return None

            provider = self._providers[channel]

            # Validate recipient
            if not await provider.validate_recipient(recipient):
                logger.error(f"Invalid recipient for {channel}: {recipient}")
                return None

            # Check rate limits
            if not await self._check_rate_limit(channel, recipient):
                logger.warning(f"Rate limit exceeded for {channel}:{recipient}")
                return None

            # Create notification request
            notification_id = f"{channel.value}-{int(time.time())}-{hash(recipient) % 10000}"

            request = NotificationRequest(
                notification_id=notification_id,
                channel=channel,
                recipient=recipient,
                template_id=template_id,
                subject=subject,
                body=body,
                priority=priority,
                context=context or {},
                metadata=metadata or {},
                max_retries=self.default_max_retries,
                retry_delay=self.default_retry_delay,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),  # 7 day expiry
            )

            # Validate using external model
            try:
                ExternalNotificationRequest(
                    notification_type="transactional",
                    recipients=[recipient],
                    channels=[channel.value],
                    subject=subject,
                    body=body,
                    template_id=template_id,
                    template_data=context or {},
                    priority=priority,
                    metadata=metadata or {},
                    expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                    recipient=recipient,
                )
            except Exception as e:
                logger.error(f"Failed to validate notification: {e}")
                return None

            # Apply template if specified
            if template_id and template_id in self._templates:
                template = self._templates[template_id]
                rendered = template.render(request.context)
                request.subject = rendered["subject"]
                request.body = rendered["body"]
                request.content_type = rendered["content_type"]

            # Queue for processing
            await self._pending_notifications.put(request)

            # Persist request
            await self._persist_notification(request)

            logger.info(
                "Notification queued",
                extra={
                    "notification_id": notification_id,
                    "channel": channel.value,
                    "recipient": recipient[:50],  # Truncate for logging
                    "priority": priority.value,
                },
            )

            return notification_id

        except Exception as e:
            logger.error(f"Failed to queue notification: {e}")
            return None

    async def get_notification_status(self, notification_id: str) -> Optional[dict[str, Any]]:
        """Get notification delivery status."""
        try:
            notification_key = f"{self.key_prefix}:notification:{notification_id}"
            data = await self._redis.get(notification_key)

            if data:
                return json.loads(data)
            return None

        except Exception as e:
            logger.error(f"Failed to get notification status: {e}")
            return None

    async def get_delivery_stats(self) -> dict[str, Any]:
        """Get comprehensive delivery statistics."""
        try:
            stats = self._stats.copy()

            # Add rate limiter info
            active_rate_limits = sum(1 for timestamps in self._rate_limiters.values() if timestamps)

            # Get queue status
            queue_size = self._pending_notifications.qsize()

            return {
                **stats,
                "active_rate_limits": active_rate_limits,
                "pending_notifications": queue_size,
                "service_status": "running" if self._is_running else "stopped",
                "registered_channels": list(self._providers.keys()),
                "available_templates": list(self._templates.keys()),
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get delivery stats: {e}")
            return {}

    def _build_task_context(self, task_result: TaskResult) -> dict[str, Any]:
        """Build notification context from task result."""
        return {
            "task_id": task_result.task_id,
            "task_status": task_result.status.value,
            "task_result": task_result.result,
            "task_error": task_result.error,
            "execution_time": task_result.execution_time,
            "retry_count": task_result.retry_count,
            "started_at": task_result.started_at.isoformat() if task_result.started_at else None,
            "completed_at": (
                task_result.completed_at.isoformat() if task_result.completed_at else None
            ),
            "metadata": task_result.metadata,
            "is_success": task_result.status == TaskStatus.COMPLETED,
            "is_failure": task_result.status in [TaskStatus.FAILED, TaskStatus.TIMEOUT],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _notification_processor(self):
        """Main notification processing loop."""
        logger.info("Notification processor started")

        try:
            while self._is_running:
                try:
                    # Get pending notification with timeout
                    request = await asyncio.wait_for(self._pending_notifications.get(), timeout=5.0)

                    # Process notification
                    await self._process_notification(request)

                except asyncio.TimeoutError:
                    # No notifications pending, continue loop
                    continue
                except Exception as e:
                    logger.error(f"Notification processing error: {e}")
                    await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info("Notification processor cancelled")

    async def _process_notification(self, request: NotificationRequest):
        """Process a single notification."""
        try:
            # Check expiry
            if request.expires_at and datetime.now(timezone.utc) > request.expires_at:
                request.status = NotificationStatus.EXPIRED
                await self._persist_notification(request)
                return

            # Get provider
            provider = self._providers.get(request.channel)
            if not provider:
                logger.error(f"No provider for channel {request.channel}")
                return

            # Update status
            request.status = NotificationStatus.SENDING
            request.last_attempt = datetime.now(timezone.utc)
            request.attempts += 1

            # Send notification
            success = await provider.send_notification(request)

            if success:
                request.status = NotificationStatus.SENT
                request.sent_at = datetime.now(timezone.utc)
                self._stats["total_sent"] += 1

                # Update channel stats
                channel_key = request.channel.value
                if channel_key not in self._stats["channel_stats"]:
                    self._stats["channel_stats"][channel_key] = {"sent": 0, "failed": 0}
                self._stats["channel_stats"][channel_key]["sent"] += 1

                logger.info(
                    "Notification sent successfully",
                    extra={
                        "notification_id": request.notification_id,
                        "channel": request.channel.value,
                    },
                )

            else:
                # Handle failure
                await self._handle_notification_failure(request)

        except Exception as e:
            logger.error(f"Notification processing failed: {e}")
            request.error = str(e)
            await self._handle_notification_failure(request)

        finally:
            # Persist final state
            await self._persist_notification(request)

    async def _handle_notification_failure(self, request: NotificationRequest):
        """Handle notification delivery failure."""
        if request.attempts >= request.max_retries:
            # Max retries reached
            request.status = NotificationStatus.FAILED
            self._stats["total_failed"] += 1

            # Update channel stats
            channel_key = request.channel.value
            if channel_key not in self._stats["channel_stats"]:
                self._stats["channel_stats"][channel_key] = {"sent": 0, "failed": 0}
            self._stats["channel_stats"][channel_key]["failed"] += 1

            logger.error(
                "Notification failed permanently",
                extra={
                    "notification_id": request.notification_id,
                    "attempts": request.attempts,
                    "error": request.error,
                },
            )

        else:
            # Schedule retry
            request.status = NotificationStatus.RETRY
            self._stats["total_retries"] += 1

            # Calculate retry delay with exponential backoff
            delay = request.retry_delay * (2 ** (request.attempts - 1))
            retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)

            # Store for retry processing
            retry_key = f"{self.key_prefix}:retry:{retry_at.isoformat()}:{request.notification_id}"
            await self._redis.set(
                retry_key,
                json.dumps(request.to_dict()),
                ex=int(delay + 3600),  # TTL with buffer
            )

            logger.info(
                "Notification scheduled for retry",
                extra={
                    "notification_id": request.notification_id,
                    "attempt": request.attempts,
                    "retry_at": retry_at.isoformat(),
                    "delay_seconds": delay,
                },
            )

    async def _retry_processor(self):
        """Process retry notifications."""
        try:
            while self._is_running:
                await self._process_retries()
                await asyncio.sleep(60)  # Check every minute

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Retry processor error: {e}")

    async def _process_retries(self):
        """Process due retry notifications."""
        try:
            now = datetime.now(timezone.utc)
            pattern = f"{self.key_prefix}:retry:*"
            keys = await self._redis.keys(pattern)

            for key in keys:
                try:
                    # Extract retry time from key
                    key_parts = key.split(":")
                    if len(key_parts) >= 4:
                        retry_time_str = ":".join(key_parts[2:4])  # Handle ISO format with colons
                        retry_time = datetime.fromisoformat(retry_time_str)

                        if now >= retry_time:
                            # Load notification data
                            data = await self._redis.get(key)
                            if data:
                                request = NotificationRequest.from_dict(json.loads(data))

                                # Requeue for processing
                                await self._pending_notifications.put(request)

                                # Remove from retry queue
                                await self._redis.delete(key)

                except Exception as e:
                    logger.warning(f"Failed to process retry key {key}: {e}")
                    # Delete corrupted retry entry
                    await self._redis.delete(key)

        except Exception as e:
            logger.error(f"Failed to process retries: {e}")

    async def _cleanup_processor(self):
        """Clean up old notification data."""
        try:
            while self._is_running:
                await self._cleanup_old_notifications()
                await asyncio.sleep(3600)  # Cleanup every hour

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Cleanup processor error: {e}")

    async def _cleanup_old_notifications(self):
        """Clean up old notification records."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=30)

            # Clean up old notifications
            pattern = f"{self.key_prefix}:notification:*"
            keys = await self._redis.keys(pattern)

            deleted_count = 0
            for key in keys:
                try:
                    data = await self._redis.get(key)
                    if data:
                        notification = json.loads(data)

                        # Check if notification is old
                        if notification.get("sent_at"):
                            sent_time = datetime.fromisoformat(notification["sent_at"])
                            if sent_time < cutoff_time:
                                await self._redis.delete(key)
                                deleted_count += 1

                except Exception:
                    # Delete corrupted entries
                    await self._redis.delete(key)
                    deleted_count += 1

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old notifications")

        except Exception as e:
            logger.error(f"Failed to cleanup old notifications: {e}")

    async def _check_rate_limit(self, channel: NotificationChannel, recipient: str) -> bool:
        """Check rate limits for channel/recipient."""
        rate_key = f"{channel.value}:{recipient}"
        now = time.time()

        # Get or create rate limiter
        if rate_key not in self._rate_limiters:
            self._rate_limiters[rate_key] = []

        timestamps = self._rate_limiters[rate_key]

        # Clean old timestamps (last hour)
        timestamps[:] = [t for t in timestamps if now - t < 3600]

        # Check limits (10 per hour for most channels)
        limit = 10
        if channel == NotificationChannel.SMS:
            limit = 5  # Stricter for SMS

        if len(timestamps) >= limit:
            return False

        # Add current timestamp
        timestamps.append(now)
        return True

    async def _persist_notification(self, request: NotificationRequest):
        """Persist notification state to Redis."""
        try:
            notification_key = f"{self.key_prefix}:notification:{request.notification_id}"
            data = json.dumps(request.to_dict())

            # Set TTL based on status
            ttl = 86400 * 7  # 7 days for most notifications
            if request.status == NotificationStatus.FAILED:
                ttl = 86400 * 30  # Keep failed longer for analysis

            await self._redis.set(notification_key, data, ex=ttl)

        except Exception as e:
            logger.error(f"Failed to persist notification: {e}")

    async def _load_templates(self):
        """Load notification templates from Redis."""
        try:
            pattern = f"{self.key_prefix}:template:*"
            keys = await self._redis.keys(pattern)

            for key in keys:
                try:
                    data = await self._redis.get(key)
                    if data:
                        template_data = json.loads(data)
                        template = NotificationTemplate(
                            template_id=template_data["template_id"],
                            name=template_data["name"],
                            channel=NotificationChannel(template_data["channel"]),
                            subject_template=template_data["subject_template"],
                            body_template=template_data["body_template"],
                            content_type=template_data.get("content_type", "text/plain"),
                            variables=set(template_data.get("variables", [])),
                            metadata=template_data.get("metadata", {}),
                        )
                        self._templates[template.template_id] = template

                except Exception as e:
                    logger.warning(f"Failed to load template from {key}: {e}")

            logger.info(f"Loaded {len(self._templates)} notification templates")

        except Exception as e:
            logger.error(f"Failed to load templates: {e}")

    def _register_default_providers(self):
        """Register default notification providers."""
        # Register webhook provider (always available)
        self.register_provider(WebhookProvider())

        # Register other providers based on configuration
        # Email provider would require SMTP configuration
        # Slack provider would require bot token
        # etc.

        logger.info("Default notification providers registered")

    async def create_default_templates(self):
        """Create default notification templates."""
        templates = [
            NotificationTemplate(
                template_id="task_success",
                name="Task Completion Success",
                channel=NotificationChannel.WEBHOOK,
                subject_template="Task Completed: {{ task_id }}",
                body_template="Task {{ task_id }} completed successfully in {{ execution_time }}s",
                variables={"task_id", "execution_time"},
            ),
            NotificationTemplate(
                template_id="task_failure",
                name="Task Completion Failure",
                channel=NotificationChannel.WEBHOOK,
                subject_template="Task Failed: {{ task_id }}",
                body_template="Task {{ task_id }} failed with error: {{ task_error }}",
                variables={"task_id", "task_error"},
            ),
            NotificationTemplate(
                template_id="email_task_success",
                name="Email Task Success",
                channel=NotificationChannel.EMAIL,
                subject_template="Task Completed Successfully - {{ task_id }}",
                body_template="""
                <html>
                <body>
                <h2>Task Completion Report</h2>
                <p><strong>Task ID:</strong> {{ task_id }}</p>
                <p><strong>Status:</strong> {{ task_status }}</p>
                <p><strong>Execution Time:</strong> {{ execution_time }}s</p>
                <p><strong>Completed At:</strong> {{ completed_at }}</p>
                </body>
                </html>
                """,
                content_type="text/html",
                variables={"task_id", "task_status", "execution_time", "completed_at"},
            ),
        ]

        for template in templates:
            await self._persist_template(template)
            self._templates[template.template_id] = template

        logger.info(f"Created {len(templates)} default templates")

    async def _persist_template(self, template: NotificationTemplate):
        """Persist template to Redis."""
        try:
            template_key = f"{self.key_prefix}:template:{template.template_id}"
            data = json.dumps(
                {
                    "template_id": template.template_id,
                    "name": template.name,
                    "channel": template.channel.value,
                    "subject_template": template.subject_template,
                    "body_template": template.body_template,
                    "content_type": template.content_type,
                    "variables": list(template.variables),
                    "metadata": template.metadata,
                }
            )

            await self._redis.set(template_key, data, ex=86400 * 365)  # 1 year TTL

        except Exception as e:
            logger.error(f"Failed to persist template: {e}")
