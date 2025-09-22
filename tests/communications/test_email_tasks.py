"""
Comprehensive tests for email task notification functionality.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest

from dotmac.platform.communications.notifications.task_notifications import (
    EmailProvider,
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    NotificationTemplate,
    SlackProvider,
    TaskNotificationService,
    WebhookProvider,
    _NotificationEnvelope as NotificationRequest,
)


class TestNotificationRequest:
    """Test notification request model."""

    @pytest.mark.unit
    def test_notification_request_initialization(self):
        """Test notification request initialization."""
        request = NotificationRequest(
            notification_id="test-123",
            channel=NotificationChannel.EMAIL,
            recipient="test@example.com",
        )

        assert request.notification_id == "test-123"
        assert request.channel == NotificationChannel.EMAIL
        assert request.recipient == "test@example.com"
        assert request.template_id is None
        assert request.subject is None
        assert request.body is None
        assert request.content_type == "text/plain"
        assert request.priority == NotificationPriority.NORMAL
        assert request.context == {}
        assert request.metadata == {}
        assert request.max_retries == 3
        assert request.retry_delay == 60.0
        assert request.expires_at is None
        assert request.status == NotificationStatus.PENDING
        assert request.attempts == 0
        assert request.last_attempt is None
        assert request.sent_at is None
        assert request.error is None

    @pytest.mark.unit
    def test_notification_request_to_dict(self):
        """Test notification request serialization."""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        request = NotificationRequest(
            notification_id="test-456",
            channel=NotificationChannel.WEBHOOK,
            recipient="https://example.com/webhook",
            subject="Test Subject",
            body="Test Body",
            priority=NotificationPriority.HIGH,
            expires_at=expires_at,
        )

        data = request.to_dict()

        assert data["notification_id"] == "test-456"
        assert data["channel"] == "webhook"
        assert data["recipient"] == "https://example.com/webhook"
        assert data["subject"] == "Test Subject"
        assert data["body"] == "Test Body"
        assert data["priority"] == "high"
        assert data["expires_at"] == expires_at.isoformat()

    @pytest.mark.unit
    def test_notification_request_from_dict(self):
        """Test notification request deserialization."""
        data = {
            "notification_id": "test-789",
            "channel": "email",
            "recipient": "user@example.com",
            "subject": "Test Subject",
            "body": "Test Body",
            "priority": "urgent",
            "status": "sent",
            "attempts": 1,
            "expires_at": "2023-12-31T23:59:59+00:00",
        }

        request = NotificationRequest.from_dict(data)

        assert request.notification_id == "test-789"
        assert request.channel == NotificationChannel.EMAIL
        assert request.recipient == "user@example.com"
        assert request.subject == "Test Subject"
        assert request.priority == NotificationPriority.URGENT
        assert request.status == NotificationStatus.SENT
        assert request.attempts == 1
        assert isinstance(request.expires_at, datetime)


class TestNotificationTemplate:
    """Test notification template functionality."""

    @pytest.mark.unit
    def test_notification_template_initialization(self):
        """Test notification template initialization."""
        template = NotificationTemplate(
            template_id="test-template",
            name="Test Template",
            channel=NotificationChannel.EMAIL,
            subject_template="Subject: {{ task_id }}",
            body_template="Task {{ task_id }} is {{ status }}",
        )

        assert template.template_id == "test-template"
        assert template.name == "Test Template"
        assert template.channel == NotificationChannel.EMAIL
        assert template.subject_template == "Subject: {{ task_id }}"
        assert template.body_template == "Task {{ task_id }} is {{ status }}"
        assert template.content_type == "text/plain"
        assert template.variables == set()
        assert template.metadata == {}

    @pytest.mark.unit
    def test_notification_template_render_success(self):
        """Test successful template rendering."""
        template = NotificationTemplate(
            template_id="success-template",
            name="Success Template",
            channel=NotificationChannel.EMAIL,
            subject_template="Task Complete: {{ task_id }}",
            body_template="Task {{ task_id }} completed successfully in {{ duration }}s",
            variables={"task_id", "duration"},
        )

        context = {"task_id": "task-123", "duration": 45.2}

        rendered = template.render(context)

        assert rendered["subject"] == "Task Complete: task-123"
        assert rendered["body"] == "Task task-123 completed successfully in 45.2s"
        assert rendered["content_type"] == "text/plain"

    @pytest.mark.unit
    def test_notification_template_render_error_handling(self):
        """Test template rendering error handling."""
        template = NotificationTemplate(
            template_id="error-template",
            name="Error Template",
            channel=NotificationChannel.EMAIL,
            subject_template="Task: {{ task_name }}",
            body_template="Status: {{ invalid_variable.nonexistent_attr }}",
        )

        context = {"task_name": "test-task"}

        # Should not raise exception, but return fallback content
        rendered = template.render(context)

        assert "test-task" in rendered["subject"]
        assert "Notification: test-task" in rendered["subject"]
        assert "test-task" in rendered["body"] or "test-task" in str(rendered["body"])
        assert rendered["content_type"] == "text/plain"


class TestWebhookProvider:
    """Test webhook notification provider."""

    @pytest.fixture
    def webhook_provider(self):
        """Create webhook provider instance."""
        return WebhookProvider()

    @pytest.mark.unit
    def test_webhook_provider_initialization(self):
        """Test webhook provider initialization."""
        provider = WebhookProvider()
        assert provider.timeout == 30
        assert provider.verify_ssl is True

        # Test with custom values
        provider = WebhookProvider(timeout=60, verify_ssl=False)
        assert provider.timeout == 60
        assert provider.verify_ssl is False

    @pytest.mark.unit
    def test_webhook_provider_get_channel(self, webhook_provider):
        """Test webhook provider channel."""
        assert webhook_provider.get_channel() == NotificationChannel.WEBHOOK

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_webhook_provider_validate_recipient_valid(self, webhook_provider):
        """Test webhook provider recipient validation - valid URLs."""
        valid_urls = [
            "https://example.com/webhook",
            "http://localhost:8000/webhook",
            "https://api.service.com/notifications/webhook",
            "http://192.168.1.100:3000/hook",
        ]

        for url in valid_urls:
            is_valid = await webhook_provider.validate_recipient(url)
            assert is_valid is True, f"URL {url} should be valid"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_webhook_provider_validate_recipient_invalid(self, webhook_provider):
        """Test webhook provider recipient validation - invalid URLs."""
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",
            "mailto:test@example.com",
            "",
            "//example.com",
            "https://",
        ]

        for url in invalid_urls:
            is_valid = await webhook_provider.validate_recipient(url)
            assert is_valid is False, f"URL {url} should be invalid"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_webhook_provider_send_notification_success(self, webhook_provider):
        """Test successful webhook notification sending."""
        request = NotificationRequest(
            notification_id="webhook-123",
            channel=NotificationChannel.WEBHOOK,
            recipient="https://example.com/webhook",
            subject="Test Subject",
            body="Test Body",
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.status_code = 200

            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await webhook_provider.send_notification(request)

            assert result is True
            mock_client_instance.post.assert_called_once()

            # Verify POST call arguments
            call_args = mock_client_instance.post.call_args
            assert call_args[0][0] == "https://example.com/webhook"

            json_payload = call_args[1]["json"]
            assert json_payload["notification_id"] == "webhook-123"
            assert json_payload["subject"] == "Test Subject"
            assert json_payload["body"] == "Test Body"

            headers = call_args[1]["headers"]
            assert headers["Content-Type"] == "application/json"
            assert headers["X-Notification-ID"] == "webhook-123"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_webhook_provider_send_notification_http_error(self, webhook_provider):
        """Test webhook notification with HTTP error."""
        request = NotificationRequest(
            notification_id="webhook-456",
            channel=NotificationChannel.WEBHOOK,
            recipient="https://example.com/webhook",
        )

        with patch("httpx.AsyncClient") as mock_client:
            import httpx

            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(
                side_effect=httpx.HTTPStatusError("404 Not Found", request=Mock(), response=Mock())
            )
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await webhook_provider.send_notification(request)

            assert result is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_webhook_provider_send_notification_request_error(self, webhook_provider):
        """Test webhook notification with request error."""
        request = NotificationRequest(
            notification_id="webhook-789",
            channel=NotificationChannel.WEBHOOK,
            recipient="https://unreachable.example.com/webhook",
        )

        with patch("httpx.AsyncClient") as mock_client:
            import httpx

            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(
                side_effect=httpx.RequestError("Connection failed")
            )
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await webhook_provider.send_notification(request)

            assert result is False


class TestEmailProvider:
    """Test email notification provider."""

    @pytest.fixture
    def email_provider(self):
        """Create email provider instance."""
        return EmailProvider(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password="password123",
            from_address="notifications@example.com",
        )

    @pytest.mark.unit
    def test_email_provider_initialization(self):
        """Test email provider initialization."""
        provider = EmailProvider(
            smtp_host="smtp.test.com",
            smtp_port=465,
            username="user@test.com",
            password="secret",
            use_tls=False,
            from_address="noreply@test.com",
        )

        assert provider.smtp_host == "smtp.test.com"
        assert provider.smtp_port == 465
        assert provider.username == "user@test.com"
        assert provider.password == "secret"
        assert provider.use_tls is False
        assert provider.from_address == "noreply@test.com"

    @pytest.mark.unit
    def test_email_provider_get_channel(self, email_provider):
        """Test email provider channel."""
        assert email_provider.get_channel() == NotificationChannel.EMAIL

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_email_provider_validate_recipient_valid(self, email_provider):
        """Test email provider recipient validation - valid emails."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "first.last+tag@subdomain.example.org",
            "user123@test-domain.com",
            "email@123.123.123.123",  # IP address domains
        ]

        for email in valid_emails:
            is_valid = await email_provider.validate_recipient(email)
            assert is_valid is True, f"Email {email} should be valid"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_email_provider_validate_recipient_invalid(self, email_provider):
        """Test email provider recipient validation - invalid emails."""
        invalid_emails = [
            "not-an-email",
            "@domain.com",
            "user@",
            "user..double.dot@domain.com",
            "user @domain.com",  # Space in email
            "",
            "user@domain",  # Missing TLD
            "user@.com",  # Missing domain
        ]

        for email in invalid_emails:
            is_valid = await email_provider.validate_recipient(email)
            assert is_valid is False, f"Email {email} should be invalid"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_email_provider_send_notification_via_tasks(self, email_provider):
        """Test email notification sending via background tasks."""
        email_provider.send_via_tasks = True

        request = NotificationRequest(
            notification_id="email-123",
            channel=NotificationChannel.EMAIL,
            recipient="user@example.com",
            subject="Test Subject",
            body="Test Body",
            content_type="text/html",
        )

        with patch("dotmac.platform.communications.notifications.task_notifications.submit_background_task") as mock_submit:
            mock_submit.return_value = None  # Successful submission

            result = await email_provider.send_notification(request)

            assert result is True
            mock_submit.assert_called_once()

            # Verify task submission arguments
            call_args = mock_submit.call_args
            assert call_args[0][0] == "dotmac.platform.tasks.email.send_email"
            assert call_args[0][1] == "user@example.com"  # recipient
            assert call_args[0][2] == "Test Subject"  # subject

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_email_provider_send_notification_via_smtp(self, email_provider):
        """Test email notification sending via SMTP."""
        email_provider.send_via_tasks = False

        request = NotificationRequest(
            notification_id="email-456",
            channel=NotificationChannel.EMAIL,
            recipient="user@example.com",
            subject="Test Subject",
            body="Test Body",
        )

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = Mock()

            result = await email_provider.send_notification(request)

            assert result is True

            # Verify SMTP calls
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with(
                email_provider.username, email_provider.password
            )
            mock_server.send_message.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_email_provider_send_notification_smtp_error(self, email_provider):
        """Test email notification SMTP error handling."""
        email_provider.send_via_tasks = False

        request = NotificationRequest(
            notification_id="email-789",
            channel=NotificationChannel.EMAIL,
            recipient="user@example.com",
            subject="Test Subject",
            body="Test Body",
        )

        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.side_effect = Exception("SMTP connection failed")

            result = await email_provider.send_notification(request)

            assert result is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_email_provider_fallback_to_smtp(self, email_provider):
        """Test fallback from task system to SMTP."""
        email_provider.send_via_tasks = True

        request = NotificationRequest(
            notification_id="email-fallback",
            channel=NotificationChannel.EMAIL,
            recipient="user@example.com",
            subject="Test Subject",
            body="Test Body",
        )

        with patch("dotmac.platform.communications.notifications.task_notifications.submit_background_task") as mock_submit:
            from dotmac.platform.tasks import app as celery_app

            mock_submit.side_effect = TaskDispatchError("Task system unavailable")

            with patch("smtplib.SMTP") as mock_smtp:
                mock_server = Mock()
                mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
                mock_smtp.return_value.__exit__ = Mock()

                result = await email_provider.send_notification(request)

                assert result is True
                mock_server.send_message.assert_called_once()


class TestSlackProvider:
    """Test Slack notification provider."""

    @pytest.fixture
    def slack_provider(self):
        """Create Slack provider instance."""
        return SlackProvider(bot_token="xoxb-test-token")

    @pytest.mark.unit
    def test_slack_provider_initialization(self):
        """Test Slack provider initialization."""
        provider = SlackProvider(bot_token="xoxb-12345-token")
        assert provider.bot_token == "xoxb-12345-token"

        # Test without bot token
        provider = SlackProvider()
        assert provider.bot_token is None

    @pytest.mark.unit
    def test_slack_provider_get_channel(self, slack_provider):
        """Test Slack provider channel."""
        assert slack_provider.get_channel() == NotificationChannel.SLACK

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_slack_provider_validate_recipient_valid(self, slack_provider):
        """Test Slack provider recipient validation - valid recipients."""
        valid_recipients = [
            "https://hooks.slack.com/services/T123/B456/xyz789",
            "#general",
            "#team-notifications",
            "@username",
            "@john.doe",
        ]

        for recipient in valid_recipients:
            is_valid = await slack_provider.validate_recipient(recipient)
            assert is_valid is True, f"Recipient {recipient} should be valid"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_slack_provider_validate_recipient_invalid(self, slack_provider):
        """Test Slack provider recipient validation - invalid recipients."""
        invalid_recipients = [
            "not-a-slack-target",
            "https://example.com/webhook",  # Not a Slack webhook
            "general",  # Missing #
            "username",  # Missing @
            "",
            "https://hooks.slack.com/invalid",  # Invalid Slack webhook format
        ]

        for recipient in invalid_recipients:
            is_valid = await slack_provider.validate_recipient(recipient)
            assert is_valid is False, f"Recipient {recipient} should be invalid"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_slack_provider_send_webhook_message(self, slack_provider):
        """Test Slack webhook message sending."""
        request = NotificationRequest(
            notification_id="slack-webhook-123",
            channel=NotificationChannel.SLACK,
            recipient="https://hooks.slack.com/services/T123/B456/xyz789",
            subject="Test Subject",
            body="Test Body",
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status = Mock()

            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await slack_provider.send_notification(request)

            assert result is True
            mock_client_instance.post.assert_called_once()

            # Verify payload structure
            call_args = mock_client_instance.post.call_args
            payload = call_args[1]["json"]
            assert payload["text"] == "Test Subject"
            assert "blocks" in payload
            assert payload["blocks"][0]["type"] == "section"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_slack_provider_send_bot_message(self, slack_provider):
        """Test Slack bot API message sending."""
        request = NotificationRequest(
            notification_id="slack-bot-456",
            channel=NotificationChannel.SLACK,
            recipient="#general",
            subject="Test Subject",
            body="Test Body",
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status = Mock()

            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await slack_provider.send_notification(request)

            assert result is True

            # Verify bot API call
            call_args = mock_client_instance.post.call_args
            assert call_args[0][0] == "https://slack.com/api/chat.postMessage"

            headers = call_args[1]["headers"]
            assert headers["Authorization"] == "Bearer xoxb-test-token"

            payload = call_args[1]["json"]
            assert payload["channel"] == "#general"
            assert "Test Subject" in payload["text"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_slack_provider_send_bot_message_no_token(self):
        """Test Slack bot message without token."""
        provider = SlackProvider()  # No token

        request = NotificationRequest(
            notification_id="slack-no-token",
            channel=NotificationChannel.SLACK,
            recipient="#general",
            subject="Test Subject",
            body="Test Body",
        )

        result = await provider.send_notification(request)
        assert result is False


class TestTaskNotificationService:
    """Test comprehensive task notification service."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_redis.keys = AsyncMock(return_value=[])
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()
        mock_redis.delete = AsyncMock()
        mock_redis.close = AsyncMock()
        return mock_redis

    @pytest.fixture
    def notification_service(self, mock_redis):
        """Create notification service with mock Redis."""
        service = TaskNotificationService(service_id="test-service", max_concurrent=10)
        service._redis = mock_redis
        return service

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_notification_service_initialization(self):
        """Test notification service initialization."""
        service = TaskNotificationService(
            redis_url="redis://test:6379",
            service_id="test-service-123",
            key_prefix="test_notifications",
            max_concurrent=25,
        )

        assert service.redis_url == "redis://test:6379"
        assert service.service_id == "test-service-123"
        assert service.key_prefix == "test_notifications"
        assert service.max_concurrent == 25
        assert service._is_running is False
        assert len(service._providers) == 0
        assert len(service._templates) == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_notification_service_register_provider(self, notification_service):
        """Test registering notification providers."""
        webhook_provider = WebhookProvider()
        email_provider = EmailProvider("smtp.test.com")

        notification_service.register_provider(webhook_provider)
        notification_service.register_provider(email_provider)

        assert NotificationChannel.WEBHOOK in notification_service._providers
        assert NotificationChannel.EMAIL in notification_service._providers
        assert notification_service._providers[NotificationChannel.WEBHOOK] is webhook_provider
        assert notification_service._providers[NotificationChannel.EMAIL] is email_provider

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_notification_service_register_template(self, notification_service):
        """Test registering notification templates."""
        template = NotificationTemplate(
            template_id="test-template",
            name="Test Template",
            channel=NotificationChannel.EMAIL,
            subject_template="Subject: {{ task_id }}",
            body_template="Body: {{ status }}",
        )

        notification_service.register_template(template)

        assert "test-template" in notification_service._templates
        assert notification_service._templates["test-template"] is template

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_send_notification_success(self, notification_service, mock_redis):
        """Test successful notification sending."""
        # Register provider
        webhook_provider = WebhookProvider()
        notification_service.register_provider(webhook_provider)

        # Mock provider validation and Redis operations
        webhook_provider.validate_recipient = AsyncMock(return_value=True)
        mock_redis.set = AsyncMock()

        notification_id = await notification_service.send_notification(
            channel=NotificationChannel.WEBHOOK,
            recipient="https://example.com/webhook",
            subject="Test Subject",
            body="Test Body",
        )

        assert notification_id is not None
        assert "webhook" in notification_id

        # Verify notification was queued
        assert notification_service._pending_notifications.qsize() == 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_send_notification_no_provider(self, notification_service):
        """Test sending notification without registered provider."""
        notification_id = await notification_service.send_notification(
            channel=NotificationChannel.EMAIL, recipient="test@example.com", subject="Test Subject"
        )

        assert notification_id is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_send_notification_invalid_recipient(self, notification_service):
        """Test sending notification with invalid recipient."""
        webhook_provider = WebhookProvider()
        webhook_provider.validate_recipient = AsyncMock(return_value=False)
        notification_service.register_provider(webhook_provider)

        notification_id = await notification_service.send_notification(
            channel=NotificationChannel.WEBHOOK,
            recipient="invalid-recipient",
            subject="Test Subject",
        )

        assert notification_id is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_send_notification_with_template(self, notification_service, mock_redis):
        """Test sending notification with template."""
        # Register provider and template
        email_provider = EmailProvider("smtp.test.com")
        email_provider.validate_recipient = AsyncMock(return_value=True)
        notification_service.register_provider(email_provider)

        template = NotificationTemplate(
            template_id="task-complete",
            name="Task Complete",
            channel=NotificationChannel.EMAIL,
            subject_template="Task {{ task_id }} Complete",
            body_template="Task {{ task_id }} finished with status {{ status }}",
        )
        notification_service.register_template(template)

        context = {"task_id": "task-123", "status": "success"}

        notification_id = await notification_service.send_notification(
            channel=NotificationChannel.EMAIL,
            recipient="user@example.com",
            template_id="task-complete",
            context=context,
        )

        assert notification_id is not None

        # Check that template was applied
        queued_request = await notification_service._pending_notifications.get()
        assert queued_request.subject == "Task task-123 Complete"
        assert "task-123" in queued_request.body
        assert "success" in queued_request.body

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_rate_limiting(self, notification_service):
        """Test notification rate limiting."""
        # Register provider
        webhook_provider = WebhookProvider()
        webhook_provider.validate_recipient = AsyncMock(return_value=True)
        notification_service.register_provider(webhook_provider)

        recipient = "https://example.com/webhook"

        # Send notifications up to the limit
        successful_sends = 0
        for i in range(15):  # Try to send more than the limit (10)
            notification_id = await notification_service.send_notification(
                channel=NotificationChannel.WEBHOOK, recipient=recipient, subject=f"Test {i}"
            )
            if notification_id:
                successful_sends += 1

        # Should be rate limited after 10 notifications
        assert successful_sends == 10

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_delivery_stats(self, notification_service):
        """Test getting delivery statistics."""
        # Set up some stats
        notification_service._stats = {
            "total_sent": 150,
            "total_failed": 10,
            "total_retries": 25,
            "channel_stats": {
                "webhook": {"sent": 100, "failed": 5},
                "email": {"sent": 50, "failed": 5},
            },
        }

        stats = await notification_service.get_delivery_stats()

        assert stats["total_sent"] == 150
        assert stats["total_failed"] == 10
        assert stats["total_retries"] == 25
        assert "webhook" in stats["channel_stats"]
        assert "email" in stats["channel_stats"]
        assert "pending_notifications" in stats
        assert "service_status" in stats
        assert "registered_channels" in stats

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_default_templates(self, notification_service, mock_redis):
        """Test creating default notification templates."""
        mock_redis.set = AsyncMock()

        await notification_service.create_default_templates()

        # Should create several default templates
        assert len(notification_service._templates) >= 3
        assert "task_success" in notification_service._templates
        assert "task_failure" in notification_service._templates
        assert "email_task_success" in notification_service._templates

        # Verify template content
        success_template = notification_service._templates["task_success"]
        assert success_template.channel == NotificationChannel.WEBHOOK
        assert "task_id" in success_template.subject_template

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_notification_workflow(self, mock_redis):
        """Test complete notification workflow."""
        service = TaskNotificationService(service_id="test-workflow")
        service._redis = mock_redis

        # Initialize with providers
        webhook_provider = WebhookProvider()
        email_provider = EmailProvider("smtp.test.com")

        # Mock successful operations
        webhook_provider.send_notification = AsyncMock(return_value=True)
        email_provider.send_notification = AsyncMock(return_value=True)
        webhook_provider.validate_recipient = AsyncMock(return_value=True)
        email_provider.validate_recipient = AsyncMock(return_value=True)

        service.register_provider(webhook_provider)
        service.register_provider(email_provider)

        # Create and register template
        template = NotificationTemplate(
            template_id="workflow-test",
            name="Workflow Test",
            channel=NotificationChannel.EMAIL,
            subject_template="Task {{ task_id }} Complete",
            body_template="Task {{ task_id }} completed successfully",
        )
        service.register_template(template)

        # Send notifications
        webhook_id = await service.send_notification(
            channel=NotificationChannel.WEBHOOK,
            recipient="https://example.com/webhook",
            subject="Webhook Test",
            body="Webhook body",
        )

        email_id = await service.send_notification(
            channel=NotificationChannel.EMAIL,
            recipient="user@example.com",
            template_id="workflow-test",
            context={"task_id": "test-task-123"},
        )

        assert webhook_id is not None
        assert email_id is not None
        assert service._pending_notifications.qsize() == 2

        # Process one notification
        notification = await service._pending_notifications.get()
        await service._process_notification(notification)

        # Verify stats were updated
        assert service._stats["total_sent"] == 1

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_notification_service_lifecycle(self, mock_redis):
        """Test notification service startup and shutdown."""
        service = TaskNotificationService(service_id="lifecycle-test")
        service._redis = mock_redis

        with patch(
            "dotmac.platform.communications.notifications.task_notifications.AsyncRedis.from_url",
            return_value=mock_redis,
        ):
            # Test initialization
            await service.initialize()
        assert service._redis is not None

        # Test startup
        await service.start()
        assert service._is_running is True
        assert service._processor_task is not None
        assert service._retry_task is not None
        assert service._cleanup_task is not None

        # Allow background tasks to run briefly
        await asyncio.sleep(0.1)

        # Test shutdown
        await service.stop()
        assert service._is_running is False

        # Verify tasks were cancelled or finished
        assert service._processor_task.cancelled() or service._processor_task.done()
        assert service._retry_task.cancelled() or service._retry_task.done()
        assert service._cleanup_task.cancelled() or service._cleanup_task.done()
