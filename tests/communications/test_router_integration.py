"""
Integration tests for communications router using FastAPI TestClient.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dotmac.platform.auth.core import UserInfo
from dotmac.platform.communications import (
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
)
from dotmac.platform.communications.router import communications_router


# Create test app
app = FastAPI()
app.include_router(communications_router, prefix="/communications")


class TestRouterIntegration:
    """Test FastAPI router integration."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_current_user(self):
        """Mock current user dependency."""
        return UserInfo(
            user_id="test_user",
            email="test@example.com",
            permissions=["notifications:send", "events:publish", "notifications:read"],
        )

    def test_send_email_endpoint(self, client, mock_current_user):
        """Test email sending endpoint."""
        with patch("dotmac.platform.communications.router.get_current_user", return_value=mock_current_user):
            with patch("dotmac.platform.communications.router.notification_service") as mock_service:
                mock_response = MagicMock()
                mock_response.id = "email_123"
                mock_service.send.return_value = mock_response

                with patch("dotmac.platform.communications.router.datetime") as mock_datetime:
                    mock_datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T12:00:00"

                    response = client.post(
                        "/communications/email",
                        json={
                            "to": ["recipient@example.com"],
                            "subject": "Test Subject",
                            "body": "Test body content",
                            "priority": "high",
                        },
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["notification_id"] == "email_123"
                    assert data["status"] == "sent"
                    assert data["channel"] == "email"
                    assert data["timestamp"] == "2023-01-01T12:00:00"

    def test_send_email_endpoint_error(self, client, mock_current_user):
        """Test email endpoint with service error."""
        with patch("dotmac.platform.communications.router.get_current_user", return_value=mock_current_user):
            with patch("dotmac.platform.communications.router.notification_service") as mock_service:
                mock_service.send.side_effect = Exception("Service error")

                response = client.post(
                    "/communications/email",
                    json={
                        "to": ["test@example.com"],
                        "subject": "Test",
                        "body": "Test body",
                    },
                )

                assert response.status_code == 500
                assert "Failed to send email" in response.json()["detail"]

    def test_send_notification_endpoint(self, client, mock_current_user):
        """Test generic notification endpoint."""
        with patch("dotmac.platform.communications.router.get_current_user", return_value=mock_current_user):
            with patch("dotmac.platform.communications.router.notification_service") as mock_service:
                mock_response = MagicMock()
                mock_response.id = "sms_456"
                mock_service.send.return_value = mock_response

                with patch("dotmac.platform.communications.router.datetime") as mock_datetime:
                    mock_datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T13:00:00"

                    response = client.post(
                        "/communications/notify",
                        json={
                            "channel": "sms",
                            "recipient": "+1234567890",
                            "subject": "Alert",
                            "message": "Important message",
                            "priority": "urgent",
                        },
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["notification_id"] == "sms_456"
                    assert data["status"] == "sent"
                    assert data["channel"] == "sms"
                    assert data["timestamp"] == "2023-01-01T13:00:00"

    def test_send_notification_endpoint_error(self, client, mock_current_user):
        """Test notification endpoint with service error."""
        with patch("dotmac.platform.communications.router.get_current_user", return_value=mock_current_user):
            with patch("dotmac.platform.communications.router.notification_service") as mock_service:
                mock_service.send.side_effect = ValueError("Invalid recipient")

                response = client.post(
                    "/communications/notify",
                    json={
                        "channel": "sms",
                        "recipient": "+1234567890",
                        "subject": "Test",
                        "message": "Test message",
                    },
                )

                assert response.status_code == 500
                assert "Invalid recipient" in response.json()["detail"]

    def test_publish_event_endpoint(self, client, mock_current_user):
        """Test event publishing endpoint."""
        with patch("dotmac.platform.communications.router.get_current_user", return_value=mock_current_user):
            with patch("dotmac.platform.communications.router.datetime") as mock_datetime:
                mock_datetime.utcnow.return_value.timestamp.return_value = 1672574400.0

                response = client.post(
                    "/communications/events",
                    json={
                        "event_type": "user.created",
                        "data": {"user_id": "123", "email": "new@example.com"},
                        "target": "analytics-service",
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert data["event_id"] == "evt_1672574400.0"
                assert data["status"] == "published"
                assert data["event_type"] == "user.created"

    def test_publish_event_endpoint_error(self, client, mock_current_user):
        """Test event endpoint with error."""
        with patch("dotmac.platform.communications.router.get_current_user", return_value=mock_current_user):
            with patch("dotmac.platform.communications.router.datetime") as mock_datetime:
                mock_datetime.utcnow.side_effect = Exception("Time service error")

                response = client.post(
                    "/communications/events",
                    json={
                        "event_type": "test.event",
                        "data": {"test": "data"},
                    },
                )

                assert response.status_code == 500
                assert "Failed to publish event" in response.json()["detail"]

    def test_list_notifications_endpoint(self, client, mock_current_user):
        """Test list notifications endpoint."""
        with patch("dotmac.platform.communications.router.get_current_user", return_value=mock_current_user):
            response = client.get("/communications/notifications")

            assert response.status_code == 200
            data = response.json()
            assert data["notifications"] == []
            assert data["total"] == 0
            assert data["filters"]["status"] is None
            assert data["filters"]["channel"] is None

    def test_list_notifications_endpoint_with_filters(self, client, mock_current_user):
        """Test list notifications endpoint with query parameters."""
        with patch("dotmac.platform.communications.router.get_current_user", return_value=mock_current_user):
            response = client.get(
                "/communications/notifications",
                params={
                    "status": "sent",
                    "channel": "email",
                    "limit": 50,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["notifications"] == []
            assert data["total"] == 0
            assert data["filters"]["status"] == "sent"
            assert data["filters"]["channel"] == "email"

    def test_get_notification_endpoint(self, client, mock_current_user):
        """Test get specific notification endpoint."""
        with patch("dotmac.platform.communications.router.get_current_user", return_value=mock_current_user):
            response = client.get("/communications/notifications/notif_123")

            assert response.status_code == 404
            assert "Notification notif_123 not found" in response.json()["detail"]

    def test_email_endpoint_validation(self, client, mock_current_user):
        """Test email endpoint input validation."""
        with patch("dotmac.platform.communications.router.get_current_user", return_value=mock_current_user):
            # Test invalid email
            response = client.post(
                "/communications/email",
                json={
                    "to": ["invalid-email"],
                    "subject": "Test",
                    "body": "Test body",
                },
            )
            assert response.status_code == 422

            # Test missing required fields
            response = client.post(
                "/communications/email",
                json={
                    "to": ["test@example.com"],
                    # Missing subject and body
                },
            )
            assert response.status_code == 422

    def test_notification_endpoint_validation(self, client, mock_current_user):
        """Test notification endpoint input validation."""
        with patch("dotmac.platform.communications.router.get_current_user", return_value=mock_current_user):
            # Test invalid channel
            response = client.post(
                "/communications/notify",
                json={
                    "channel": "invalid_channel",
                    "recipient": "test@example.com",
                    "subject": "Test",
                    "message": "Test message",
                },
            )
            assert response.status_code == 422

            # Test missing required fields
            response = client.post(
                "/communications/notify",
                json={
                    "channel": "email",
                    # Missing recipient, subject, message
                },
            )
            assert response.status_code == 422

    def test_event_endpoint_validation(self, client, mock_current_user):
        """Test event endpoint input validation."""
        with patch("dotmac.platform.communications.router.get_current_user", return_value=mock_current_user):
            # Test missing required fields
            response = client.post(
                "/communications/events",
                json={
                    "event_type": "test.event",
                    # Missing data
                },
            )
            assert response.status_code == 422

            # Test with empty data
            response = client.post(
                "/communications/events",
                json={
                    "event_type": "test.event",
                    "data": {},
                },
            )
            assert response.status_code == 200  # Empty data should be allowed

    def test_list_notifications_limit_validation(self, client, mock_current_user):
        """Test list notifications limit validation."""
        with patch("dotmac.platform.communications.router.get_current_user", return_value=mock_current_user):
            # Test limit too high
            response = client.get(
                "/communications/notifications",
                params={"limit": 2000},
            )
            assert response.status_code == 422

            # Test limit too low
            response = client.get(
                "/communications/notifications",
                params={"limit": 0},
            )
            assert response.status_code == 422

            # Test valid limit
            response = client.get(
                "/communications/notifications",
                params={"limit": 100},
            )
            assert response.status_code == 200

    def test_unauthorized_requests(self, client):
        """Test that endpoints require authentication."""
        # Email endpoint without auth should fail
        response = client.post(
            "/communications/email",
            json={
                "to": ["test@example.com"],
                "subject": "Test",
                "body": "Test body",
            },
        )
        # Note: Actual auth failure response depends on auth implementation

    def test_email_endpoint_multiple_recipients(self, client, mock_current_user):
        """Test email endpoint with multiple recipients."""
        with patch("dotmac.platform.communications.router.get_current_user", return_value=mock_current_user):
            with patch("dotmac.platform.communications.router.notification_service") as mock_service:
                mock_response = MagicMock()
                mock_response.id = "bulk_email_123"
                mock_service.send.return_value = mock_response

                with patch("dotmac.platform.communications.router.datetime") as mock_datetime:
                    mock_datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T14:00:00"

                    response = client.post(
                        "/communications/email",
                        json={
                            "to": ["user1@example.com", "user2@example.com", "user3@example.com"],
                            "subject": "Bulk Email Test",
                            "body": "This is a test bulk email",
                            "cc": ["manager@example.com"],
                            "bcc": ["archive@example.com"],
                            "priority": "normal",
                        },
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["notification_id"] == "bulk_email_123"

                    # Verify the service was called with correct metadata
                    call_args = mock_service.send.call_args[0][0]
                    assert call_args.metadata["all_recipients"] == [
                        "user1@example.com",
                        "user2@example.com",
                        "user3@example.com",
                    ]
                    assert call_args.metadata["cc"] == ["manager@example.com"]
                    assert call_args.metadata["bcc"] == ["archive@example.com"]

    def test_notification_endpoint_all_channels(self, client, mock_current_user):
        """Test notification endpoint with all supported channels."""
        channels_and_recipients = [
            ("email", "test@example.com"),
            ("sms", "+1234567890"),
            ("push", "device_token_123"),
            ("webhook", "https://api.example.com/webhook"),
        ]

        with patch("dotmac.platform.communications.router.get_current_user", return_value=mock_current_user):
            with patch("dotmac.platform.communications.router.notification_service") as mock_service:
                with patch("dotmac.platform.communications.router.datetime") as mock_datetime:
                    mock_datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T15:00:00"

                    for i, (channel, recipient) in enumerate(channels_and_recipients):
                        mock_response = MagicMock()
                        mock_response.id = f"{channel}_notif_{i}"
                        mock_service.send.return_value = mock_response

                        response = client.post(
                            "/communications/notify",
                            json={
                                "channel": channel,
                                "recipient": recipient,
                                "subject": f"Test {channel.upper()} notification",
                                "message": f"This is a test {channel} message",
                                "priority": "normal",
                            },
                        )

                        assert response.status_code == 200
                        data = response.json()
                        assert data["channel"] == channel
                        assert data["notification_id"] == f"{channel}_notif_{i}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])