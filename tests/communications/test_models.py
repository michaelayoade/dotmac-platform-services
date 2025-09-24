"""
Comprehensive tests for communications data models and enums.
"""

import pytest
from pydantic import ValidationError

from dotmac.platform.communications import (
    NotificationChannel,
    NotificationPriority,
    NotificationRequest,
    NotificationResponse,
    NotificationStatus,
    NotificationTemplate,
    NotificationType,
)


class TestEnums:
    """Test communication enums."""

    def test_notification_type_values(self):
        """Test NotificationType enum values."""
        assert NotificationType.EMAIL == "email"
        assert NotificationType.SMS == "sms"
        assert NotificationType.PUSH == "push"
        assert NotificationType.WEBHOOK == "webhook"

    def test_notification_type_is_string_enum(self):
        """Test that NotificationType is a string enum."""
        notification_type = NotificationType.EMAIL
        assert isinstance(notification_type, str)
        assert notification_type == "email"
        assert notification_type.value == "email"

    def test_notification_channel_alias(self):
        """Test NotificationChannel alias."""
        # NotificationChannel should be an alias for NotificationType
        assert NotificationChannel.EMAIL == NotificationType.EMAIL
        assert NotificationChannel.SMS == NotificationType.SMS
        assert NotificationChannel.PUSH == NotificationType.PUSH
        assert NotificationChannel.WEBHOOK == NotificationType.WEBHOOK

    def test_notification_priority_values(self):
        """Test NotificationPriority enum values."""
        assert NotificationPriority.LOW == "low"
        assert NotificationPriority.NORMAL == "normal"
        assert NotificationPriority.HIGH == "high"
        assert NotificationPriority.URGENT == "urgent"

    def test_notification_priority_is_string_enum(self):
        """Test that NotificationPriority is a string enum."""
        priority = NotificationPriority.HIGH
        assert isinstance(priority, str)
        assert priority == "high"

    def test_notification_status_values(self):
        """Test NotificationStatus enum values."""
        assert NotificationStatus.PENDING == "pending"
        assert NotificationStatus.SENT == "sent"
        assert NotificationStatus.DELIVERED == "delivered"
        assert NotificationStatus.FAILED == "failed"
        assert NotificationStatus.RETRYING == "retrying"

    def test_notification_status_is_string_enum(self):
        """Test that NotificationStatus is a string enum."""
        status = NotificationStatus.DELIVERED
        assert isinstance(status, str)
        assert status == "delivered"


class TestNotificationRequest:
    """Test NotificationRequest dataclass."""

    def test_notification_request_full_creation(self):
        """Test NotificationRequest creation with all fields."""
        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="user@example.com",
            subject="Test Subject",
            content="Test content with details",
            metadata={"priority": "high", "campaign": "welcome"},
            template_id="welcome_email",
            template_data={"user_name": "John Doe", "company": "ACME Corp"},
        )

        assert request.type == NotificationType.EMAIL
        assert request.recipient == "user@example.com"
        assert request.subject == "Test Subject"
        assert request.content == "Test content with details"
        assert request.metadata == {"priority": "high", "campaign": "welcome"}
        assert request.template_id == "welcome_email"
        assert request.template_data == {"user_name": "John Doe", "company": "ACME Corp"}

    def test_notification_request_minimal_creation(self):
        """Test NotificationRequest with minimal required fields."""
        request = NotificationRequest(
            type=NotificationType.SMS,
            recipient="+1234567890",
        )

        assert request.type == NotificationType.SMS
        assert request.recipient == "+1234567890"
        assert request.subject is None
        assert request.content == ""  # Default empty string
        assert request.metadata is None
        assert request.template_id is None
        assert request.template_data is None

    def test_notification_request_with_content_only(self):
        """Test NotificationRequest with content but no subject."""
        request = NotificationRequest(
            type=NotificationType.PUSH,
            recipient="device_token_123",
            content="Push notification message",
        )

        assert request.type == NotificationType.PUSH
        assert request.recipient == "device_token_123"
        assert request.subject is None
        assert request.content == "Push notification message"

    def test_notification_request_different_types(self):
        """Test NotificationRequest with different notification types."""
        test_cases = [
            (NotificationType.EMAIL, "user@example.com"),
            (NotificationType.SMS, "+1234567890"),
            (NotificationType.PUSH, "device_token"),
            (NotificationType.WEBHOOK, "https://api.example.com/webhook"),
        ]

        for notif_type, recipient in test_cases:
            request = NotificationRequest(
                type=notif_type,
                recipient=recipient,
                content=f"Test {notif_type.value} content",
            )
            assert request.type == notif_type
            assert request.recipient == recipient

    def test_notification_request_complex_metadata(self):
        """Test NotificationRequest with complex metadata."""
        complex_metadata = {
            "campaign": {
                "id": "camp_123",
                "name": "Summer Sale",
                "tags": ["promotion", "seasonal"],
            },
            "analytics": {"track_opens": True, "track_clicks": True},
            "personalization": {"segment": "premium_users", "ab_test": "variant_b"},
            "scheduling": {"timezone": "UTC", "preferred_time": "09:00"},
        }

        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="premium@example.com",
            subject="Exclusive Summer Sale!",
            content="Check out our amazing summer deals...",
            metadata=complex_metadata,
        )

        assert request.metadata == complex_metadata
        assert request.metadata["campaign"]["id"] == "camp_123"
        assert request.metadata["analytics"]["track_opens"] is True


class TestNotificationResponse:
    """Test NotificationResponse dataclass."""

    def test_notification_response_full_creation(self):
        """Test NotificationResponse creation with all fields."""
        response = NotificationResponse(
            id="notif_12345",
            status=NotificationStatus.DELIVERED,
            message="Email delivered successfully to user@example.com",
            metadata={
                "provider": "sendgrid",
                "message_id": "msg_67890",
                "delivery_time": "2023-01-01T12:30:45Z",
                "attempts": 1,
            },
        )

        assert response.id == "notif_12345"
        assert response.status == NotificationStatus.DELIVERED
        assert response.message == "Email delivered successfully to user@example.com"
        assert response.metadata["provider"] == "sendgrid"
        assert response.metadata["message_id"] == "msg_67890"

    def test_notification_response_minimal_creation(self):
        """Test NotificationResponse with minimal required fields."""
        response = NotificationResponse(
            id="notif_minimal",
            status=NotificationStatus.SENT,
        )

        assert response.id == "notif_minimal"
        assert response.status == NotificationStatus.SENT
        assert response.message is None
        assert response.metadata is None

    def test_notification_response_different_statuses(self):
        """Test NotificationResponse with different status values."""
        statuses = [
            NotificationStatus.PENDING,
            NotificationStatus.SENT,
            NotificationStatus.DELIVERED,
            NotificationStatus.FAILED,
            NotificationStatus.RETRYING,
        ]

        for status in statuses:
            response = NotificationResponse(
                id=f"notif_{status.value}",
                status=status,
                message=f"Notification {status.value}",
            )
            assert response.status == status
            assert status.value in response.message

    def test_notification_response_with_error_metadata(self):
        """Test NotificationResponse with error metadata."""
        error_metadata = {
            "error_code": "INVALID_RECIPIENT",
            "error_message": "The recipient email address is invalid",
            "retry_count": 3,
            "last_attempt": "2023-01-01T12:35:00Z",
            "next_retry": None,  # No more retries
        }

        response = NotificationResponse(
            id="notif_error",
            status=NotificationStatus.FAILED,
            message="Failed to deliver notification after 3 attempts",
            metadata=error_metadata,
        )

        assert response.status == NotificationStatus.FAILED
        assert response.metadata["error_code"] == "INVALID_RECIPIENT"
        assert response.metadata["retry_count"] == 3


class TestNotificationTemplate:
    """Test NotificationTemplate dataclass."""

    def test_notification_template_full_creation(self):
        """Test NotificationTemplate creation with all fields."""
        template = NotificationTemplate(
            id="welcome_email_v2",
            name="Welcome Email Template v2",
            type=NotificationType.EMAIL,
            subject_template="Welcome to {{company_name}}, {{user_name}}!",
            content_template="""
            <h1>Welcome {{user_name}}!</h1>
            <p>Thank you for joining {{company_name}}. We're excited to have you!</p>
            <p>Your account details:</p>
            <ul>
                <li>Email: {{user_email}}</li>
                <li>Member since: {{join_date}}</li>
            </ul>
            """,
            metadata={
                "version": "2.1",
                "created_by": "marketing_team",
                "last_updated": "2023-01-01T12:00:00Z",
                "tags": ["onboarding", "welcome", "email"],
                "approval_status": "approved",
            },
        )

        assert template.id == "welcome_email_v2"
        assert template.name == "Welcome Email Template v2"
        assert template.type == NotificationType.EMAIL
        assert "{{company_name}}" in template.subject_template
        assert "{{user_name}}" in template.content_template
        assert template.metadata["version"] == "2.1"

    def test_notification_template_minimal_creation(self):
        """Test NotificationTemplate with minimal required fields."""
        template = NotificationTemplate(
            id="simple_sms",
            name="Simple SMS",
            type=NotificationType.SMS,
        )

        assert template.id == "simple_sms"
        assert template.name == "Simple SMS"
        assert template.type == NotificationType.SMS
        assert template.subject_template is None
        assert template.content_template == ""  # Default empty string
        assert template.metadata is None

    def test_notification_template_different_types(self):
        """Test NotificationTemplate for different notification types."""
        templates = [
            {
                "id": "email_template",
                "type": NotificationType.EMAIL,
                "subject": "Email Subject Template",
                "content": "<p>Email content with {{variable}}</p>",
            },
            {
                "id": "sms_template",
                "type": NotificationType.SMS,
                "subject": None,
                "content": "SMS: {{message}} Reply STOP to opt out.",
            },
            {
                "id": "push_template",
                "type": NotificationType.PUSH,
                "subject": "Push Title",
                "content": "{{title}}: {{body}}",
            },
            {
                "id": "webhook_template",
                "type": NotificationType.WEBHOOK,
                "subject": None,
                "content": '{"event": "{{event_type}}", "data": {{data}}}',
            },
        ]

        for template_data in templates:
            template = NotificationTemplate(
                id=template_data["id"],
                name=f"Test {template_data['type'].value} Template",
                type=template_data["type"],
                subject_template=template_data["subject"],
                content_template=template_data["content"],
            )

            assert template.type == template_data["type"]
            assert template.id == template_data["id"]

    def test_notification_template_with_complex_metadata(self):
        """Test NotificationTemplate with complex metadata."""
        complex_metadata = {
            "template_engine": {
                "type": "jinja2",
                "version": "3.1.2",
                "options": {"autoescape": True, "trim_blocks": True},
            },
            "localization": {
                "supported_languages": ["en", "es", "fr", "de"],
                "default_language": "en",
                "fallback_enabled": True,
            },
            "validation": {
                "required_variables": ["user_name", "company_name"],
                "optional_variables": ["user_email", "join_date"],
                "schema_version": "1.0",
            },
            "usage_stats": {"times_used": 1250, "success_rate": 0.987},
        }

        template = NotificationTemplate(
            id="advanced_template",
            name="Advanced Email Template",
            type=NotificationType.EMAIL,
            subject_template="{{localized_subject}}",
            content_template="{{localized_content}}",
            metadata=complex_metadata,
        )

        assert template.metadata["template_engine"]["type"] == "jinja2"
        assert template.metadata["localization"]["default_language"] == "en"
        assert len(template.metadata["validation"]["required_variables"]) == 2

    def test_notification_template_content_variations(self):
        """Test NotificationTemplate with various content formats."""
        # HTML email template
        html_template = NotificationTemplate(
            id="html_email",
            name="HTML Email",
            type=NotificationType.EMAIL,
            content_template="""
            <!DOCTYPE html>
            <html>
            <body>
                <h1 style="color: blue;">{{title}}</h1>
                <p>{{content}}</p>
                <footer>{{company_footer}}</footer>
            </body>
            </html>
            """,
        )
        assert "<!DOCTYPE html>" in html_template.content_template

        # JSON webhook template
        json_template = NotificationTemplate(
            id="json_webhook",
            name="JSON Webhook",
            type=NotificationType.WEBHOOK,
            content_template='{"timestamp": "{{timestamp}}", "event": "{{event}}", "payload": {{payload_json}}}',
        )
        assert json_template.content_template.startswith("{")

        # Plain text SMS template
        sms_template = NotificationTemplate(
            id="plain_sms",
            name="Plain SMS",
            type=NotificationType.SMS,
            content_template="Hi {{name}}, your order {{order_id}} is ready for pickup!",
        )
        assert "{{name}}" in sms_template.content_template


if __name__ == "__main__":
    pytest.main([__file__, "-v"])