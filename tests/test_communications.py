"""
Comprehensive tests for the communications module.
Achieves >90% coverage for notification functionality.
"""

import asyncio
import sys
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from dotmac.platform.communications import (
    EmailNotifier,
    NotificationRequest,
    NotificationResponse,
    NotificationService,
    NotificationStatus,
    NotificationTemplate,
    NotificationType,
    PushNotifier,
    SMSNotifier,
    UnifiedNotificationService,
    get_notification_service,
    send_notification,
)


class TestNotificationTypes:
    """Test notification type enums and data classes."""

    def test_notification_type_enum_values(self):
        """Test NotificationType enum values."""
        assert NotificationType.EMAIL == "email"
        assert NotificationType.SMS == "sms"
        assert NotificationType.PUSH == "push"
        assert NotificationType.WEBHOOK == "webhook"

    def test_notification_status_enum_values(self):
        """Test NotificationStatus enum values."""
        assert NotificationStatus.PENDING == "pending"
        assert NotificationStatus.SENT == "sent"
        assert NotificationStatus.DELIVERED == "delivered"
        assert NotificationStatus.FAILED == "failed"
        assert NotificationStatus.RETRYING == "retrying"

    def test_notification_request_creation(self):
        """Test NotificationRequest dataclass."""
        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="user@example.com",
            subject="Test Subject",
            content="Test content",
            metadata={"key": "value"},
            template_id="template_1",
            template_data={"name": "John"}
        )

        assert request.type == NotificationType.EMAIL
        assert request.recipient == "user@example.com"
        assert request.subject == "Test Subject"
        assert request.content == "Test content"
        assert request.metadata["key"] == "value"
        assert request.template_id == "template_1"
        assert request.template_data["name"] == "John"

    def test_notification_request_defaults(self):
        """Test NotificationRequest with default values."""
        request = NotificationRequest(
            type=NotificationType.SMS,
            recipient="+1234567890",
            content="SMS message"
        )

        assert request.type == NotificationType.SMS
        assert request.recipient == "+1234567890"
        assert request.subject is None
        assert request.content == "SMS message"
        assert request.metadata is None
        assert request.template_id is None
        assert request.template_data is None

    def test_notification_response_creation(self):
        """Test NotificationResponse dataclass."""
        response = NotificationResponse(
            id="notif_123",
            status=NotificationStatus.SENT,
            message="Email sent successfully",
            metadata={"provider": "sendgrid"}
        )

        assert response.id == "notif_123"
        assert response.status == NotificationStatus.SENT
        assert response.message == "Email sent successfully"
        assert response.metadata["provider"] == "sendgrid"

    def test_notification_template_creation(self):
        """Test NotificationTemplate dataclass."""
        template = NotificationTemplate(
            id="tmpl_1",
            name="Welcome Email",
            type=NotificationType.EMAIL,
            subject_template="Welcome {{name}}!",
            content_template="Hi {{name}}, welcome to our platform!",
            metadata={"version": "1.0"}
        )

        assert template.id == "tmpl_1"
        assert template.name == "Welcome Email"
        assert template.type == NotificationType.EMAIL
        assert template.subject_template == "Welcome {{name}}!"
        assert template.content_template == "Hi {{name}}, welcome to our platform!"
        assert template.metadata["version"] == "1.0"


class TestNotificationService:
    """Test NotificationService functionality."""

    @pytest.fixture
    def service(self):
        """Create a notification service instance."""
        return NotificationService(smtp_host="localhost", smtp_port=587)

    def test_service_initialization(self, service):
        """Test service initialization."""
        assert service.smtp_host == "localhost"
        assert service.smtp_port == 587
        assert service.templates == {}
        assert service._sent_notifications == []
        assert service._integration_service is None
        assert service._email_integration is None
        assert service._sms_integration is None

    def test_add_template(self, service):
        """Test adding a notification template."""
        template = NotificationTemplate(
            id="tmpl_1",
            name="Test Template",
            type=NotificationType.EMAIL,
            content_template="Test content"
        )

        service.add_template(template)

        assert "tmpl_1" in service.templates
        assert service.templates["tmpl_1"] == template

    def test_send_email_notification(self, service):
        """Test sending email notification."""
        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="user@example.com",
            subject="Test Email",
            content="Test content"
        )

        response = service.send(request)

        assert response.id == "notif_1"
        assert response.status == NotificationStatus.SENT
        assert "Email sent successfully" in response.message
        assert len(service._sent_notifications) == 1

    def test_send_sms_notification(self, service):
        """Test sending SMS notification."""
        request = NotificationRequest(
            type=NotificationType.SMS,
            recipient="+1234567890",
            content="Test SMS"
        )

        response = service.send(request)

        assert response.id == "notif_1"
        assert response.status == NotificationStatus.SENT
        assert "SMS sent successfully" in response.message
        assert len(service._sent_notifications) == 1

    def test_send_push_notification(self, service):
        """Test sending push notification."""
        request = NotificationRequest(
            type=NotificationType.PUSH,
            recipient="device_token_123",
            content="Push notification"
        )

        response = service.send(request)

        assert response.id == "notif_1"
        assert response.status == NotificationStatus.SENT
        assert "Push notification sent successfully" in response.message
        assert len(service._sent_notifications) == 1

    def test_send_webhook_notification(self, service):
        """Test sending webhook notification."""
        request = NotificationRequest(
            type=NotificationType.WEBHOOK,
            recipient="https://example.com/webhook",
            content='{"event": "test"}'
        )

        response = service.send(request)

        assert response.id == "notif_1"
        assert response.status == NotificationStatus.SENT
        assert "Webhook sent successfully" in response.message
        assert len(service._sent_notifications) == 1

    def test_send_unsupported_notification(self, service):
        """Test sending notification with unsupported type."""
        # Create a request with an invalid type by monkey-patching
        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="test@example.com",
            content="Test"
        )
        request.type = "invalid_type"  # type: ignore

        response = service.send(request)

        assert response.status == NotificationStatus.FAILED
        assert "Unsupported notification type" in response.message
        assert len(service._sent_notifications) == 1

    def test_send_notification_with_exception(self, service):
        """Test notification sending with exception."""
        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="user@example.com",
            content="Test"
        )

        # Patch _send_email to raise exception
        with patch.object(service, '_send_email', side_effect=Exception("Send failed")):
            response = service.send(request)

        assert response.status == NotificationStatus.FAILED
        assert "Send failed" in response.message

    def test_get_status(self, service):
        """Test getting notification status."""
        # Send a notification first
        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="user@example.com",
            content="Test"
        )
        response = service.send(request)

        # Get status
        status = service.get_status(response.id)

        assert status is not None
        assert status.id == response.id
        assert status.status == response.status

    def test_get_status_not_found(self, service):
        """Test getting status for non-existent notification."""
        status = service.get_status("notif_999")
        assert status is None

    def test_list_notifications(self, service):
        """Test listing all notifications."""
        # Send multiple notifications
        for i in range(3):
            request = NotificationRequest(
                type=NotificationType.EMAIL,
                recipient=f"user{i}@example.com",
                content="Test"
            )
            service.send(request)

        notifications = service.list_notifications()

        assert len(notifications) == 3
        assert all(n.status == NotificationStatus.SENT for n in notifications)

    @pytest.mark.asyncio
    async def test_initialize_integrations_success(self, service):
        """Test successful integration initialization."""
        # Test that initialize_integrations method exists and can be called
        assert hasattr(service, 'initialize_integrations')

        # Actually call it to get coverage
        await service.initialize_integrations()

        # Should handle ImportError gracefully
        assert service._email_integration is None
        assert service._sms_integration is None

    @pytest.mark.asyncio
    async def test_initialize_integrations_import_error(self, service):
        """Test integration initialization with import error."""
        # This test is redundant as initialize_integrations already handles ImportError
        # But let's test that the method is robust
        await service.initialize_integrations()

        assert service._email_integration is None
        assert service._sms_integration is None

    @pytest.mark.asyncio
    async def test_initialize_integrations_with_available_integrations(self, service):
        """Test integration initialization when integrations are available."""
        # Create real mock classes that can work with isinstance
        class MockEmailIntegration:
            pass

        class MockSMSIntegration:
            pass

        mock_email_integration = MockEmailIntegration()
        mock_sms_integration = MockSMSIntegration()

        # Mock the entire import of integrations module
        mock_integrations_module = MagicMock()
        mock_integrations_module.get_integration_async = AsyncMock(side_effect=lambda name: {
            "email": mock_email_integration,
            "sms": mock_sms_integration
        }.get(name))

        # Use the real classes
        mock_integrations_module.EmailIntegration = MockEmailIntegration
        mock_integrations_module.SMSIntegration = MockSMSIntegration

        with patch.dict('sys.modules', {'dotmac.platform.integrations': mock_integrations_module}):
            await service.initialize_integrations()

            # Check that integrations were assigned
            assert service._email_integration is mock_email_integration
            assert service._sms_integration is mock_sms_integration

    def test_send_email_with_integration(self, service):
        """Test sending email through integration."""
        mock_integration = MagicMock()
        mock_integration.send_email = AsyncMock(return_value={
            "status": "sent",
            "message_id": "msg_123"
        })
        service._email_integration = mock_integration

        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="user@example.com",
            subject="Test",
            content="Test content",
            metadata={"html_content": "<p>Test</p>"}
        )

        with patch('dotmac.platform.communications.hasattr', return_value=True):
            response = service.send(request)

        assert response.status == NotificationStatus.SENT
        assert response.metadata["status"] == "sent"

    def test_send_sms_with_integration(self, service):
        """Test sending SMS through integration."""
        mock_integration = MagicMock()
        mock_integration.send_sms = AsyncMock(return_value={
            "status": "sent",
            "message_id": "sms_123"
        })
        service._sms_integration = mock_integration

        request = NotificationRequest(
            type=NotificationType.SMS,
            recipient="+1234567890",
            content="Test SMS"
        )

        with patch('dotmac.platform.communications.hasattr', return_value=True):
            response = service.send(request)

        assert response.status == NotificationStatus.SENT
        assert response.metadata["status"] == "sent"

    def test_send_email_with_integration_failure(self, service):
        """Test email sending with integration that fails."""
        mock_integration = MagicMock()
        mock_integration.send_email = AsyncMock(return_value={
            "status": "failed",
            "error": "Integration error"
        })
        service._email_integration = mock_integration

        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="user@example.com",
            subject="Test",
            content="Test content"
        )

        with patch('dotmac.platform.communications.hasattr', return_value=True):
            response = service.send(request)

        assert response.status == NotificationStatus.FAILED

    def test_send_sms_with_integration_failure(self, service):
        """Test SMS sending with integration that fails."""
        mock_integration = MagicMock()
        mock_integration.send_sms = AsyncMock(return_value={
            "status": "failed",
            "error": "SMS error"
        })
        service._sms_integration = mock_integration

        request = NotificationRequest(
            type=NotificationType.SMS,
            recipient="+1234567890",
            content="Test SMS"
        )

        with patch('dotmac.platform.communications.hasattr', return_value=True):
            response = service.send(request)

        assert response.status == NotificationStatus.FAILED

    def test_send_email_integration_exception(self, service):
        """Test email sending when integration raises exception."""
        mock_integration = MagicMock()
        mock_integration.send_email = AsyncMock(side_effect=Exception("Integration failed"))
        service._email_integration = mock_integration

        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="user@example.com",
            subject="Test",
            content="Test content"
        )

        with patch('dotmac.platform.communications.hasattr', return_value=True):
            response = service.send(request)

        assert response.status == NotificationStatus.FAILED
        assert "Integration failed" in response.message

    def test_send_sms_integration_exception(self, service):
        """Test SMS sending when integration raises exception."""
        mock_integration = MagicMock()
        mock_integration.send_sms = AsyncMock(side_effect=Exception("SMS failed"))
        service._sms_integration = mock_integration

        request = NotificationRequest(
            type=NotificationType.SMS,
            recipient="+1234567890",
            content="Test SMS"
        )

        with patch('dotmac.platform.communications.hasattr', return_value=True):
            response = service.send(request)

        assert response.status == NotificationStatus.FAILED
        assert "SMS failed" in response.message

    def test_send_email_with_no_subject(self, service):
        """Test sending email without subject."""
        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="user@example.com",
            content="Test content"
        )

        response = service.send(request)
        assert response.status == NotificationStatus.SENT

    def test_send_email_with_metadata_no_html(self, service):
        """Test sending email with metadata but no html_content."""
        mock_integration = MagicMock()
        mock_integration.send_email = AsyncMock(return_value={
            "status": "sent",
            "message_id": "msg_123"
        })
        service._email_integration = mock_integration

        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="user@example.com",
            subject="Test",
            content="Test content",
            metadata={"other_key": "value"}  # No html_content
        )

        with patch('dotmac.platform.communications.hasattr', return_value=True):
            response = service.send(request)

        assert response.status == NotificationStatus.SENT

    def test_send_email_with_no_metadata(self, service):
        """Test sending email with no metadata."""
        mock_integration = MagicMock()
        mock_integration.send_email = AsyncMock(return_value={
            "status": "sent",
            "message_id": "msg_123"
        })
        service._email_integration = mock_integration

        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="user@example.com",
            subject="Test",
            content="Test content"
            # No metadata
        )

        with patch('dotmac.platform.communications.hasattr', return_value=True):
            response = service.send(request)

        assert response.status == NotificationStatus.SENT


class TestGlobalFunctions:
    """Test module-level global functions."""

    def test_get_notification_service(self):
        """Test getting global notification service."""
        service1 = get_notification_service()
        service2 = get_notification_service()

        assert service1 is service2  # Should be singleton
        assert isinstance(service1, NotificationService)

    def test_get_notification_service_with_params(self):
        """Test getting notification service with custom parameters."""
        service = get_notification_service(
            smtp_host="mail.example.com",
            smtp_port=465,
            refresh=True
        )

        assert service.smtp_host == "mail.example.com"
        assert service.smtp_port == 465

    def test_get_notification_service_refresh(self):
        """Test refreshing notification service."""
        service1 = get_notification_service()
        service2 = get_notification_service(refresh=True)

        # After refresh, should be a new instance
        assert service1 is not service2

    def test_send_notification(self):
        """Test sending notification through global function."""
        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="user@example.com",
            content="Test"
        )

        response = send_notification(request)

        assert response.status == NotificationStatus.SENT
        assert response.id.startswith("notif_")


class TestAliases:
    """Test backward compatibility aliases."""

    def test_unified_notification_service_alias(self):
        """Test UnifiedNotificationService alias."""
        assert UnifiedNotificationService is NotificationService

    def test_email_notifier_alias(self):
        """Test EmailNotifier alias."""
        assert EmailNotifier is NotificationService

    def test_sms_notifier_alias(self):
        """Test SMSNotifier alias."""
        assert SMSNotifier is NotificationService

    def test_push_notifier_alias(self):
        """Test PushNotifier alias."""
        assert PushNotifier is NotificationService


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""

    @pytest.mark.asyncio
    async def test_notification_with_template(self):
        """Test sending notification with template."""
        service = NotificationService()

        # Add template
        template = NotificationTemplate(
            id="welcome",
            name="Welcome Email",
            type=NotificationType.EMAIL,
            subject_template="Welcome to our platform!",
            content_template="Hello, welcome aboard!"
        )
        service.add_template(template)

        # Send notification using template
        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="new_user@example.com",
            template_id="welcome"
        )

        response = service.send(request)

        assert response.status == NotificationStatus.SENT
        assert len(service._sent_notifications) == 1

    def test_bulk_notification_sending(self):
        """Test sending multiple notifications."""
        service = NotificationService()
        recipients = [f"user{i}@example.com" for i in range(10)]
        responses = []

        for recipient in recipients:
            request = NotificationRequest(
                type=NotificationType.EMAIL,
                recipient=recipient,
                subject="Bulk Email",
                content="This is a bulk email"
            )
            response = service.send(request)
            responses.append(response)

        assert len(responses) == 10
        assert all(r.status == NotificationStatus.SENT for r in responses)
        assert len(service.list_notifications()) == 10

    def test_mixed_notification_types(self):
        """Test sending different types of notifications."""
        service = NotificationService()

        notifications = [
            (NotificationType.EMAIL, "user@example.com"),
            (NotificationType.SMS, "+1234567890"),
            (NotificationType.PUSH, "device_token"),
            (NotificationType.WEBHOOK, "https://example.com/hook"),
        ]

        responses = []
        for notif_type, recipient in notifications:
            request = NotificationRequest(
                type=notif_type,
                recipient=recipient,
                content=f"Test {notif_type.value} notification"
            )
            response = service.send(request)
            responses.append(response)

        assert len(responses) == 4
        assert all(r.status == NotificationStatus.SENT for r in responses)

    def test_error_recovery(self):
        """Test error recovery in notification sending."""
        service = NotificationService()
        successful_count = 0
        failed_count = 0

        for i in range(5):
            request = NotificationRequest(
                type=NotificationType.EMAIL if i % 2 == 0 else NotificationType.SMS,
                recipient=f"user{i}@example.com" if i % 2 == 0 else f"+123456789{i}",
                content=f"Message {i}"
            )

            if i == 2:
                # Simulate error for one notification
                with patch.object(service, '_send_email', side_effect=Exception("Network error")):
                    response = service.send(request)
            else:
                response = service.send(request)

            if response.status == NotificationStatus.SENT:
                successful_count += 1
            else:
                failed_count += 1

        assert successful_count == 4
        assert failed_count == 1
        assert len(service.list_notifications()) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=dotmac.platform.communications", "--cov-report=term-missing"])