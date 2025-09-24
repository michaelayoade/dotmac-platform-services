"""
Comprehensive tests for the communications router module.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from dotmac.platform.auth.core import UserInfo
from dotmac.platform.communications import (
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
)
from dotmac.platform.communications.router import (
    EmailRequest,
    EventRequest,
    NotificationRequest,
    NotificationResponse,
    communications_router,
    get_notification,
    list_notifications,
    publish_event,
    send_email,
    send_notification,
)


class TestRequestModels:
    """Test request and response models."""

    def test_email_request_creation(self):
        """Test EmailRequest model creation."""
        request = EmailRequest(
            to=["user@example.com", "user2@example.com"],
            subject="Test Subject",
            body="<p>Test HTML body</p>",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            priority=NotificationPriority.HIGH,
        )

        assert request.to == ["user@example.com", "user2@example.com"]
        assert request.subject == "Test Subject"
        assert request.body == "<p>Test HTML body</p>"
        assert request.cc == ["cc@example.com"]
        assert request.bcc == ["bcc@example.com"]
        assert request.priority == NotificationPriority.HIGH

    def test_email_request_minimal(self):
        """Test EmailRequest with minimal required fields."""
        request = EmailRequest(
            to=["user@example.com"],
            subject="Subject",
            body="Body",
        )

        assert request.to == ["user@example.com"]
        assert request.subject == "Subject"
        assert request.body == "Body"
        assert request.cc is None
        assert request.bcc is None
        assert request.priority == NotificationPriority.NORMAL

    def test_notification_request_creation(self):
        """Test NotificationRequest model creation."""
        request = NotificationRequest(
            channel=NotificationChannel.SMS,
            recipient="+1234567890",
            subject="SMS Alert",
            message="Important message",
            priority=NotificationPriority.URGENT,
            metadata={"campaign_id": "123"},
        )

        assert request.channel == NotificationChannel.SMS
        assert request.recipient == "+1234567890"
        assert request.subject == "SMS Alert"
        assert request.message == "Important message"
        assert request.priority == NotificationPriority.URGENT
        assert request.metadata == {"campaign_id": "123"}

    def test_notification_request_defaults(self):
        """Test NotificationRequest with default values."""
        request = NotificationRequest(
            channel=NotificationChannel.EMAIL,
            recipient="user@example.com",
            subject="Subject",
            message="Message",
        )

        assert request.priority == NotificationPriority.NORMAL
        assert request.metadata is None

    def test_notification_response_creation(self):
        """Test NotificationResponse model creation."""
        response = NotificationResponse(
            notification_id="notif_123",
            status=NotificationStatus.SENT,
            channel=NotificationChannel.EMAIL,
            timestamp="2023-01-01T12:00:00",
        )

        assert response.notification_id == "notif_123"
        assert response.status == NotificationStatus.SENT
        assert response.channel == NotificationChannel.EMAIL
        assert response.timestamp == "2023-01-01T12:00:00"

    def test_event_request_creation(self):
        """Test EventRequest model creation."""
        request = EventRequest(
            event_type="user.signup",
            data={"user_id": "123", "email": "user@example.com"},
            target="analytics-service",
        )

        assert request.event_type == "user.signup"
        assert request.data == {"user_id": "123", "email": "user@example.com"}
        assert request.target == "analytics-service"

    def test_event_request_minimal(self):
        """Test EventRequest with minimal fields."""
        request = EventRequest(
            event_type="test.event",
            data={"key": "value"},
        )

        assert request.event_type == "test.event"
        assert request.data == {"key": "value"}
        assert request.target is None


class TestSendEmailEndpoint:
    """Test send email endpoint."""

    @pytest.fixture
    def mock_user(self):
        """Create mock user for testing."""
        return UserInfo(
            user_id="user123",
            email="test@example.com",
            tenant_id="tenant1",
            permissions=["email:send"],
        )

    @pytest.mark.asyncio
    async def test_send_email_success(self, mock_user):
        """Test successful email sending."""
        request = EmailRequest(
            to=["recipient@example.com"],
            subject="Test Subject",
            body="Test body content",
            priority=NotificationPriority.HIGH,
        )

        with patch("dotmac.platform.communications.router.notification_service") as mock_service:
            mock_response = MagicMock()
            mock_response.id = "notif_123"
            mock_service.send.return_value = mock_response

            with patch("dotmac.platform.communications.router.datetime") as mock_datetime:
                mock_datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T12:00:00"

                response = await send_email(request, mock_user)

                assert response.notification_id == "notif_123"
                assert response.status == NotificationStatus.SENT
                assert response.channel == NotificationChannel.EMAIL
                assert response.timestamp == "2023-01-01T12:00:00"

    @pytest.mark.asyncio
    async def test_send_email_multiple_recipients(self, mock_user):
        """Test sending email to multiple recipients."""
        request = EmailRequest(
            to=["user1@example.com", "user2@example.com"],
            subject="Bulk Email",
            body="Content for all",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
        )

        with patch("dotmac.platform.communications.router.notification_service") as mock_service:
            mock_response = MagicMock()
            mock_response.id = "notif_456"
            mock_service.send.return_value = mock_response

            with patch("dotmac.platform.communications.router.datetime") as mock_datetime:
                mock_datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T12:00:00"

                response = await send_email(request, mock_user)

                # Check the notification request that was passed to service.send
                call_args = mock_service.send.call_args[0][0]
                assert call_args.recipient == "user1@example.com"  # First recipient used
                assert call_args.metadata["all_recipients"] == ["user1@example.com", "user2@example.com"]
                assert call_args.metadata["cc"] == ["cc@example.com"]
                assert call_args.metadata["bcc"] == ["bcc@example.com"]
                assert call_args.metadata["sender_id"] == "user123"

    @pytest.mark.asyncio
    async def test_send_email_service_failure(self, mock_user):
        """Test email sending when service fails."""
        request = EmailRequest(
            to=["user@example.com"],
            subject="Test",
            body="Test",
        )

        with patch("dotmac.platform.communications.router.notification_service") as mock_service:
            mock_service.send.side_effect = Exception("Service unavailable")

            with pytest.raises(HTTPException) as exc_info:
                await send_email(request, mock_user)

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to send email" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_send_email_empty_recipients(self, mock_user):
        """Test email sending with empty recipients list."""
        request = EmailRequest(
            to=[],
            subject="Test",
            body="Test",
        )

        with patch("dotmac.platform.communications.router.notification_service") as mock_service:
            mock_response = MagicMock()
            mock_response.id = "notif_789"
            mock_service.send.return_value = mock_response

            with patch("dotmac.platform.communications.router.datetime") as mock_datetime:
                mock_datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T12:00:00"

                response = await send_email(request, mock_user)

                # Should handle empty recipients gracefully
                call_args = mock_service.send.call_args[0][0]
                assert call_args.recipient == ""  # Empty string when no recipients


class TestSendNotificationEndpoint:
    """Test send notification endpoint."""

    @pytest.fixture
    def mock_user(self):
        """Create mock user for testing."""
        return UserInfo(
            user_id="user456",
            email="test@example.com",
            tenant_id="tenant1",
            permissions=["notifications:send"],
        )

    @pytest.mark.asyncio
    async def test_send_notification_sms(self, mock_user):
        """Test sending SMS notification."""
        request = NotificationRequest(
            channel=NotificationChannel.SMS,
            recipient="+1234567890",
            subject="Alert",
            message="Important SMS message",
            priority=NotificationPriority.URGENT,
            metadata={"campaign": "promo2023"},
        )

        with patch("dotmac.platform.communications.router.notification_service") as mock_service:
            mock_response = MagicMock()
            mock_response.id = "sms_123"
            mock_service.send.return_value = mock_response

            with patch("dotmac.platform.communications.router.datetime") as mock_datetime:
                mock_datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T13:00:00"

                response = await send_notification(request, mock_user)

                assert response.notification_id == "sms_123"
                assert response.status == NotificationStatus.SENT
                assert response.channel == NotificationChannel.SMS
                assert response.timestamp == "2023-01-01T13:00:00"

                # Verify the call to service
                call_args = mock_service.send.call_args[0][0]
                assert call_args.type == NotificationChannel.SMS
                assert call_args.recipient == "+1234567890"
                assert call_args.subject == "Alert"
                assert call_args.content == "Important SMS message"
                assert call_args.metadata["campaign"] == "promo2023"
                assert call_args.metadata["priority"] == "urgent"
                assert call_args.metadata["sender_id"] == "user456"

    @pytest.mark.asyncio
    async def test_send_notification_push(self, mock_user):
        """Test sending push notification."""
        request = NotificationRequest(
            channel=NotificationChannel.PUSH,
            recipient="device_token_123",
            subject="Push Alert",
            message="Push notification content",
        )

        with patch("dotmac.platform.communications.router.notification_service") as mock_service:
            mock_response = MagicMock()
            mock_response.id = "push_456"
            mock_service.send.return_value = mock_response

            with patch("dotmac.platform.communications.router.datetime") as mock_datetime:
                mock_datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T14:00:00"

                response = await send_notification(request, mock_user)

                assert response.notification_id == "push_456"
                assert response.channel == NotificationChannel.PUSH

    @pytest.mark.asyncio
    async def test_send_notification_webhook(self, mock_user):
        """Test sending webhook notification."""
        request = NotificationRequest(
            channel=NotificationChannel.WEBHOOK,
            recipient="https://api.example.com/webhook",
            subject="Webhook Event",
            message='{"event": "test"}',
        )

        with patch("dotmac.platform.communications.router.notification_service") as mock_service:
            mock_response = MagicMock()
            mock_response.id = "webhook_789"
            mock_service.send.return_value = mock_response

            with patch("dotmac.platform.communications.router.datetime") as mock_datetime:
                mock_datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T15:00:00"

                response = await send_notification(request, mock_user)

                assert response.notification_id == "webhook_789"
                assert response.channel == NotificationChannel.WEBHOOK

    @pytest.mark.asyncio
    async def test_send_notification_no_metadata(self, mock_user):
        """Test sending notification without metadata."""
        request = NotificationRequest(
            channel=NotificationChannel.EMAIL,
            recipient="user@example.com",
            subject="Simple Email",
            message="Simple message",
        )

        with patch("dotmac.platform.communications.router.notification_service") as mock_service:
            mock_response = MagicMock()
            mock_response.id = "simple_123"
            mock_service.send.return_value = mock_response

            with patch("dotmac.platform.communications.router.datetime") as mock_datetime:
                mock_datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T16:00:00"

                response = await send_notification(request, mock_user)

                # Check that metadata was created properly
                call_args = mock_service.send.call_args[0][0]
                assert call_args.metadata["priority"] == "normal"
                assert call_args.metadata["sender_id"] == "user456"

    @pytest.mark.asyncio
    async def test_send_notification_service_failure(self, mock_user):
        """Test notification sending when service fails."""
        request = NotificationRequest(
            channel=NotificationChannel.SMS,
            recipient="+1234567890",
            subject="Test",
            message="Test message",
        )

        with patch("dotmac.platform.communications.router.notification_service") as mock_service:
            mock_service.send.side_effect = ValueError("Invalid recipient")

            with pytest.raises(HTTPException) as exc_info:
                await send_notification(request, mock_user)

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Invalid recipient" in str(exc_info.value.detail)


class TestPublishEventEndpoint:
    """Test publish event endpoint."""

    @pytest.fixture
    def mock_user(self):
        """Create mock user for testing."""
        return UserInfo(
            user_id="user789",
            email="test@example.com",
            tenant_id="tenant1",
            permissions=["events:publish"],
        )

    @pytest.mark.asyncio
    async def test_publish_event_success(self, mock_user):
        """Test successful event publishing."""
        request = EventRequest(
            event_type="user.created",
            data={"user_id": "123", "email": "new@example.com"},
            target="analytics-service",
        )

        with patch("dotmac.platform.communications.router.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value.timestamp.return_value = 1672574400.0

            response = await publish_event(request, mock_user)

            assert response["event_id"] == "evt_1672574400.0"
            assert response["status"] == "published"
            assert response["event_type"] == "user.created"

    @pytest.mark.asyncio
    async def test_publish_event_no_target(self, mock_user):
        """Test publishing event without target."""
        request = EventRequest(
            event_type="system.health",
            data={"status": "healthy", "timestamp": "2023-01-01T12:00:00"},
        )

        with patch("dotmac.platform.communications.router.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value.timestamp.return_value = 1672574460.0

            response = await publish_event(request, mock_user)

            assert response["event_id"] == "evt_1672574460.0"
            assert response["status"] == "published"
            assert response["event_type"] == "system.health"

    @pytest.mark.asyncio
    async def test_publish_event_complex_data(self, mock_user):
        """Test publishing event with complex data structure."""
        request = EventRequest(
            event_type="order.completed",
            data={
                "order_id": "ord_123",
                "customer": {"id": "cust_456", "name": "John Doe"},
                "items": [
                    {"sku": "ITEM001", "quantity": 2, "price": 29.99},
                    {"sku": "ITEM002", "quantity": 1, "price": 49.99},
                ],
                "total": 109.97,
            },
            target="fulfillment-service",
        )

        with patch("dotmac.platform.communications.router.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value.timestamp.return_value = 1672574520.0

            response = await publish_event(request, mock_user)

            assert response["event_type"] == "order.completed"
            assert "evt_" in response["event_id"]

    @pytest.mark.asyncio
    async def test_publish_event_exception(self, mock_user):
        """Test event publishing with exception."""
        request = EventRequest(
            event_type="test.event",
            data={"test": "data"},
        )

        # Mock datetime to raise exception
        with patch("dotmac.platform.communications.router.datetime") as mock_datetime:
            mock_datetime.utcnow.side_effect = Exception("Time service unavailable")

            with pytest.raises(HTTPException) as exc_info:
                await publish_event(request, mock_user)

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to publish event" in str(exc_info.value.detail)


class TestListNotificationsEndpoint:
    """Test list notifications endpoint."""

    @pytest.fixture
    def mock_user(self):
        """Create mock user for testing."""
        return UserInfo(
            user_id="user999",
            email="test@example.com",
            tenant_id="tenant1",
            permissions=["notifications:read"],
        )

    @pytest.mark.asyncio
    async def test_list_notifications_no_filters(self, mock_user):
        """Test listing notifications without filters."""
        response = await list_notifications(current_user=mock_user)

        assert response["notifications"] == []
        assert response["total"] == 0
        # Note: Query objects are returned as-is from FastAPI, not None
        assert response["filters"]["status"] is not None  # Will be Query(None)
        assert response["filters"]["channel"] is not None  # Will be Query(None)

    @pytest.mark.asyncio
    async def test_list_notifications_with_status_filter(self, mock_user):
        """Test listing notifications with status filter."""
        response = await list_notifications(
            status=NotificationStatus.SENT,
            current_user=mock_user,
        )

        assert response["notifications"] == []
        assert response["total"] == 0
        assert response["filters"]["status"] == NotificationStatus.SENT
        assert response["filters"]["channel"] is not None  # Will be Query(None)

    @pytest.mark.asyncio
    async def test_list_notifications_with_channel_filter(self, mock_user):
        """Test listing notifications with channel filter."""
        response = await list_notifications(
            channel=NotificationChannel.EMAIL,
            current_user=mock_user,
        )

        assert response["notifications"] == []
        assert response["total"] == 0
        assert response["filters"]["status"] is not None  # Will be Query(None)
        assert response["filters"]["channel"] == NotificationChannel.EMAIL

    @pytest.mark.asyncio
    async def test_list_notifications_with_all_filters(self, mock_user):
        """Test listing notifications with all filters."""
        response = await list_notifications(
            status=NotificationStatus.DELIVERED,
            channel=NotificationChannel.SMS,
            limit=50,
            current_user=mock_user,
        )

        assert response["notifications"] == []
        assert response["total"] == 0
        assert response["filters"]["status"] == NotificationStatus.DELIVERED
        assert response["filters"]["channel"] == NotificationChannel.SMS

    @pytest.mark.asyncio
    async def test_list_notifications_limit_parameter(self, mock_user):
        """Test listing notifications with limit parameter."""
        # Test that the function accepts different limit values
        response = await list_notifications(
            limit=10,
            current_user=mock_user,
        )

        assert response["notifications"] == []
        assert response["total"] == 0


class TestGetNotificationEndpoint:
    """Test get notification endpoint."""

    @pytest.fixture
    def mock_user(self):
        """Create mock user for testing."""
        return UserInfo(
            user_id="user888",
            email="test@example.com",
            tenant_id="tenant1",
            permissions=["notifications:read"],
        )

    @pytest.mark.asyncio
    async def test_get_notification_not_found(self, mock_user):
        """Test getting notification that doesn't exist."""
        with pytest.raises(HTTPException) as exc_info:
            await get_notification("notif_123", mock_user)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Notification notif_123 not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_notification_various_ids(self, mock_user):
        """Test getting notifications with various ID formats."""
        test_ids = [
            "notif_456",
            "notification_789",
            "12345",
            "uuid-12345-67890",
            "very-long-notification-id-with-many-characters",
        ]

        for notification_id in test_ids:
            with pytest.raises(HTTPException) as exc_info:
                await get_notification(notification_id, mock_user)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert f"Notification {notification_id} not found" in str(exc_info.value.detail)


class TestRouterIntegration:
    """Test router integration scenarios."""

    def test_router_exists(self):
        """Test that the router is properly created."""
        assert communications_router is not None
        assert hasattr(communications_router, "routes")

    def test_router_aliases(self):
        """Test router aliases."""
        from dotmac.platform.communications.router import comms_router

        assert comms_router is communications_router

    def test_notification_service_instance(self):
        """Test that notification service is created."""
        from dotmac.platform.communications.router import notification_service

        assert notification_service is not None
        assert hasattr(notification_service, "send")

    @pytest.mark.asyncio
    async def test_endpoint_dependency_injection(self):
        """Test that endpoints properly handle dependency injection."""
        # This test verifies that the endpoints are properly set up for DI
        # The actual auth testing is done with mocked users in other tests

        from dotmac.platform.communications.router import (
            get_notification,
            list_notifications,
            publish_event,
            send_email,
            send_notification,
        )

        # Check that functions exist and are async
        assert asyncio.iscoroutinefunction(send_email)
        assert asyncio.iscoroutinefunction(send_notification)
        assert asyncio.iscoroutinefunction(publish_event)
        assert asyncio.iscoroutinefunction(list_notifications)
        assert asyncio.iscoroutinefunction(get_notification)

    def test_imports_and_exports(self):
        """Test that all required imports and exports work."""
        # Test that we can import everything needed
        from dotmac.platform.communications.router import (
            EmailRequest,
            EventRequest,
            NotificationRequest,
            NotificationResponse,
            communications_router,
            comms_router,
        )

        # Test that models are proper Pydantic models
        assert hasattr(EmailRequest, "model_fields")
        assert hasattr(NotificationRequest, "model_fields")
        assert hasattr(NotificationResponse, "model_fields")
        assert hasattr(EventRequest, "model_fields")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])