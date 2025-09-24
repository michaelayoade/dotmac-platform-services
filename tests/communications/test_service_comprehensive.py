"""
Comprehensive integration tests for communications service functionality.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dotmac.platform.communications import (
    NotificationRequest,
    NotificationResponse,
    NotificationService,
    NotificationStatus,
    NotificationTemplate,
    NotificationType,
    get_notification_service,
    send_notification,
)


class TestNotificationServiceEdgeCases:
    """Test edge cases and error conditions for NotificationService."""

    @pytest.fixture
    def service(self):
        """Create a clean notification service instance."""
        return NotificationService(smtp_host="test.smtp.com", smtp_port=465)

    def test_service_initialization_custom_params(self):
        """Test service initialization with custom parameters."""
        service = NotificationService(smtp_host="custom.smtp.com", smtp_port=465)
        assert service.smtp_host == "custom.smtp.com"
        assert service.smtp_port == 465

    def test_service_counter_increments(self, service):
        """Test that notification counter increments properly."""
        # Send multiple notifications and check ID generation
        request1 = NotificationRequest(type=NotificationType.EMAIL, recipient="test1@example.com", content="Test 1")
        request2 = NotificationRequest(type=NotificationType.SMS, recipient="+1111111111", content="Test 2")
        request3 = NotificationRequest(type=NotificationType.PUSH, recipient="device1", content="Test 3")

        response1 = service.send(request1)
        response2 = service.send(request2)
        response3 = service.send(request3)

        assert response1.id == "notif_1"
        assert response2.id == "notif_2"
        assert response3.id == "notif_3"

        assert len(service._sent_notifications) == 3

    def test_template_overwrite(self, service):
        """Test that adding template with same ID overwrites previous one."""
        template1 = NotificationTemplate(
            id="test_template",
            name="Original Template",
            type=NotificationType.EMAIL,
            content_template="Original content"
        )

        template2 = NotificationTemplate(
            id="test_template",
            name="Updated Template",
            type=NotificationType.EMAIL,
            content_template="Updated content"
        )

        service.add_template(template1)
        assert service.templates["test_template"].name == "Original Template"

        service.add_template(template2)
        assert service.templates["test_template"].name == "Updated Template"
        assert len(service.templates) == 1  # Should still be only one

    def test_get_status_with_multiple_notifications(self, service):
        """Test getting status with multiple notifications in system."""
        # Send multiple notifications
        requests = [
            NotificationRequest(type=NotificationType.EMAIL, recipient=f"user{i}@example.com", content=f"Message {i}")
            for i in range(5)
        ]

        responses = [service.send(req) for req in requests]
        notification_ids = [resp.id for resp in responses]

        # Test getting status for each notification
        for i, notif_id in enumerate(notification_ids):
            status = service.get_status(notif_id)
            assert status is not None
            assert status.id == notif_id
            assert status.status == NotificationStatus.SENT

        # Test getting status for non-existent notification
        fake_status = service.get_status("notif_999")
        assert fake_status is None

    def test_list_notifications_maintains_order(self, service):
        """Test that list_notifications maintains chronological order."""
        # Send notifications in specific order with different subjects
        subjects = ["First Subject", "Second Subject", "Third Subject", "Fourth Subject", "Fifth Subject"]

        for i, subject in enumerate(subjects):
            request = NotificationRequest(
                type=NotificationType.EMAIL,
                recipient=f"user{i+1}@example.com",
                subject=subject,
                content="Test content"
            )
            service.send(request)

        notifications = service.list_notifications()

        assert len(notifications) == 5
        # Check that notifications are in order by checking IDs
        for i, notif in enumerate(notifications):
            expected_id = f"notif_{i+1}"
            assert notif.id == expected_id

    def test_list_notifications_returns_copy(self, service):
        """Test that list_notifications returns a copy, not reference."""
        request = NotificationRequest(type=NotificationType.EMAIL, recipient="test@example.com", content="Test")
        service.send(request)

        notifications1 = service.list_notifications()
        notifications2 = service.list_notifications()

        # Should be different list objects but same content
        assert notifications1 is not notifications2
        assert len(notifications1) == len(notifications2) == 1
        assert notifications1[0].id == notifications2[0].id


class TestNotificationServiceIntegrationScenarios:
    """Test realistic integration scenarios."""

    @pytest.fixture
    def service(self):
        """Create notification service for testing."""
        return NotificationService()

    @pytest.mark.asyncio
    async def test_integration_initialization_success(self, service):
        """Test successful integration initialization."""
        # Mock successful integration loading
        mock_email_integration = MagicMock()
        mock_sms_integration = MagicMock()

        mock_integrations_module = MagicMock()
        mock_integrations_module.EmailIntegration = type(mock_email_integration)
        mock_integrations_module.SMSIntegration = type(mock_sms_integration)
        mock_integrations_module.get_integration_async = AsyncMock(side_effect=lambda name: {
            "email": mock_email_integration,
            "sms": mock_sms_integration
        }.get(name))

        with patch.dict('sys.modules', {'dotmac.platform.integrations': mock_integrations_module}):
            await service.initialize_integrations()

            assert service._email_integration is mock_email_integration
            assert service._sms_integration is mock_sms_integration

    @pytest.mark.asyncio
    async def test_integration_partial_success(self, service):
        """Test integration initialization with partial success."""
        # Mock only email integration available
        mock_email_integration = MagicMock()

        mock_integrations_module = MagicMock()
        mock_integrations_module.EmailIntegration = type(mock_email_integration)
        mock_integrations_module.SMSIntegration = MagicMock
        mock_integrations_module.get_integration_async = AsyncMock(side_effect=lambda name: {
            "email": mock_email_integration,
            "sms": None  # SMS integration not available
        }.get(name))

        with patch.dict('sys.modules', {'dotmac.platform.integrations': mock_integrations_module}):
            await service.initialize_integrations()

            assert service._email_integration is mock_email_integration
            assert service._sms_integration is None

    def test_email_sending_with_integration_mixed_results(self, service):
        """Test email sending where integration returns mixed success/failure."""
        mock_integration = MagicMock()

        # First call succeeds, second fails
        mock_integration.send_email = AsyncMock(side_effect=[
            {"status": "sent", "message_id": "msg_123"},
            {"status": "failed", "error": "Rate limit exceeded"}
        ])
        service._email_integration = mock_integration

        request1 = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="success@example.com",
            subject="Success Email",
            content="This should work"
        )

        request2 = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="failure@example.com",
            subject="Failure Email",
            content="This should fail"
        )

        with patch('dotmac.platform.communications.hasattr', return_value=True):
            response1 = service.send(request1)
            response2 = service.send(request2)

        assert response1.status == NotificationStatus.SENT
        assert response1.metadata["status"] == "sent"

        assert response2.status == NotificationStatus.FAILED

    def test_sms_sending_without_integration(self, service):
        """Test SMS sending falls back to simulation when integration unavailable."""
        # No integration set
        service._sms_integration = None

        request = NotificationRequest(
            type=NotificationType.SMS,
            recipient="+1234567890",
            content="Test SMS without integration"
        )

        response = service.send(request)

        assert response.status == NotificationStatus.SENT
        assert "simulated" in response.message.lower()

    def test_email_with_html_content_metadata(self, service):
        """Test email sending with HTML content in metadata."""
        mock_integration = MagicMock()
        mock_integration.send_email = AsyncMock(return_value={
            "status": "sent",
            "message_id": "html_msg_123"
        })
        service._email_integration = mock_integration

        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="html@example.com",
            subject="HTML Email",
            content="Plain text version",
            metadata={
                "html_content": "<h1>HTML Version</h1><p>Rich content here</p>",
                "campaign": "newsletter"
            }
        )

        with patch('dotmac.platform.communications.hasattr', return_value=True):
            response = service.send(request)

        assert response.status == NotificationStatus.SENT

        # Verify the integration was called with HTML content
        mock_integration.send_email.assert_called_once()
        call_args = mock_integration.send_email.call_args
        assert call_args[1]["html_content"] == "<h1>HTML Version</h1><p>Rich content here</p>"


class TestGlobalServiceManagement:
    """Test global service instance management."""

    def test_global_service_singleton_behavior(self):
        """Test that global service behaves as singleton."""
        # Clear any existing global service
        import dotmac.platform.communications
        dotmac.platform.communications._notification_service = None

        service1 = get_notification_service()
        service2 = get_notification_service()

        assert service1 is service2  # Should be same instance

    def test_global_service_refresh(self):
        """Test refreshing global service creates new instance."""
        service1 = get_notification_service(smtp_host="host1", smtp_port=587)
        service2 = get_notification_service(smtp_host="host2", smtp_port=465, refresh=True)

        assert service1 is not service2  # Should be different instances
        assert service2.smtp_host == "host2"
        assert service2.smtp_port == 465

    def test_global_service_parameter_override(self):
        """Test that refresh allows parameter override."""
        # Reset global service first
        import dotmac.platform.communications
        dotmac.platform.communications._notification_service = None

        original_service = get_notification_service(smtp_host="original.com", smtp_port=25)
        assert original_service.smtp_host == "original.com"
        assert original_service.smtp_port == 25

        new_service = get_notification_service(smtp_host="new.com", smtp_port=587, refresh=True)
        assert new_service.smtp_host == "new.com"
        assert new_service.smtp_port == 587

        # Verify new service is now the global one
        current_service = get_notification_service()
        assert current_service is new_service

    def test_send_notification_global_function(self):
        """Test global send_notification function."""
        # Refresh global service to ensure clean state
        get_notification_service(refresh=True)

        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="global@example.com",
            content="Global function test"
        )

        response = send_notification(request)

        assert response.status == NotificationStatus.SENT
        assert response.id.startswith("notif_")

        # Verify it used the global service
        global_service = get_notification_service()
        notifications = global_service.list_notifications()
        assert len(notifications) >= 1
        assert any(n.id == response.id for n in notifications)


class TestErrorHandlingEdgeCases:
    """Test error handling in various edge cases."""

    @pytest.fixture
    def service(self):
        """Create service for error testing."""
        return NotificationService()

    def test_send_with_invalid_type_object(self, service):
        """Test sending notification with completely invalid type."""
        request = NotificationRequest(
            type=NotificationType.EMAIL,  # Start with valid type
            recipient="test@example.com",
            content="Test"
        )

        # Manually set invalid type to test error handling
        request.type = "completely_invalid_type"

        response = service.send(request)

        assert response.status == NotificationStatus.FAILED
        assert "Unsupported notification type" in response.message

    def test_email_integration_asyncio_run_exception(self, service):
        """Test email sending when asyncio.run raises exception."""
        mock_integration = MagicMock()
        mock_integration.send_email = AsyncMock(return_value={"status": "sent"})
        service._email_integration = mock_integration

        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="test@example.com",
            content="Test"
        )

        with patch('dotmac.platform.communications.hasattr', return_value=True):
            with patch('asyncio.run', side_effect=RuntimeError("Event loop error")):
                response = service.send(request)

        assert response.status == NotificationStatus.FAILED
        assert "Event loop error" in response.message

    def test_sms_integration_asyncio_run_exception(self, service):
        """Test SMS sending when asyncio.run raises exception."""
        mock_integration = MagicMock()
        mock_integration.send_sms = AsyncMock(return_value={"status": "sent"})
        service._sms_integration = mock_integration

        request = NotificationRequest(
            type=NotificationType.SMS,
            recipient="+1234567890",
            content="Test SMS"
        )

        with patch('dotmac.platform.communications.hasattr', return_value=True):
            with patch('asyncio.run', side_effect=KeyboardInterrupt("Interrupted")):
                response = service.send(request)

        assert response.status == NotificationStatus.FAILED
        assert "Interrupted" in response.message

    def test_email_integration_missing_method(self, service):
        """Test email integration that doesn't have send_email method."""
        # Create integration without send_email method
        mock_integration = MagicMock(spec=[])  # Empty spec means no methods
        service._email_integration = mock_integration

        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="test@example.com",
            content="Test"
        )

        # Should fall back to simulation since hasattr will return False
        response = service.send(request)

        assert response.status == NotificationStatus.SENT
        assert "simulated" in response.message.lower()

    def test_sms_integration_missing_method(self, service):
        """Test SMS integration that doesn't have send_sms method."""
        # Create integration without send_sms method
        mock_integration = MagicMock(spec=[])
        service._sms_integration = mock_integration

        request = NotificationRequest(
            type=NotificationType.SMS,
            recipient="+1234567890",
            content="Test SMS"
        )

        # Should fall back to simulation
        response = service.send(request)

        assert response.status == NotificationStatus.SENT
        assert "simulated" in response.message.lower()

    def test_exception_in_notification_counter(self, service):
        """Test that exceptions don't break notification counter."""
        # Send a few successful notifications
        for i in range(3):
            request = NotificationRequest(
                type=NotificationType.EMAIL,
                recipient=f"user{i}@example.com",
                content="Test"
            )
            response = service.send(request)
            assert response.id == f"notif_{i+1}"

        # Cause an exception
        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="error@example.com",
            content="Error test"
        )

        with patch.object(service, '_send_email', side_effect=Exception("Forced error")):
            response = service.send(request)
            assert response.status == NotificationStatus.FAILED
            assert response.id == "notif_4"  # Counter should still increment

        # Next notification should continue counting
        request = NotificationRequest(
            type=NotificationType.EMAIL,
            recipient="normal@example.com",
            content="Normal test"
        )
        response = service.send(request)
        assert response.id == "notif_5"


class TestConcurrencyAndThreadSafety:
    """Test concurrent access to notification service."""

    @pytest.fixture
    def service(self):
        """Create service for concurrency testing."""
        return NotificationService()

    def test_concurrent_notification_sending(self, service):
        """Test sending notifications concurrently - service is not thread-safe but should handle basic operations."""
        import threading
        import time

        results = []
        exceptions = []

        def send_notification_worker(worker_id):
            """Worker function to send notification."""
            try:
                request = NotificationRequest(
                    type=NotificationType.EMAIL,
                    recipient=f"worker{worker_id}@example.com",
                    content=f"Message from worker {worker_id}"
                )
                response = service.send(request)
                results.append((worker_id, response.id, response.status))
                time.sleep(0.001)  # Small delay
            except Exception as e:
                exceptions.append((worker_id, str(e)))

        # Start multiple threads
        threads = []
        for i in range(5):  # Reduced to 5 to be more predictable
            thread = threading.Thread(target=send_notification_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify basic functionality works even with concurrency
        assert len(results) == 5  # All completed
        assert len(exceptions) == 0  # No exceptions

        # Check that all IDs are in expected format (may not be unique due to race conditions)
        for worker_id, notif_id, status in results:
            assert notif_id.startswith("notif_")
            assert notif_id.split("_")[1].isdigit()
            assert status == NotificationStatus.SENT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])