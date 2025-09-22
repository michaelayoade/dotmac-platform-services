"""
Tests for the simplified Celery-based events system.
"""

import pytest
from unittest.mock import Mock, patch

from dotmac.platform.communications.events import publish_event, event_handler, Event


class TestCeleryEvents:
    """Test the simplified Celery events system."""

    def test_event_creation(self):
        """Test Event dataclass creation."""
        event = Event(
            topic="test.topic",
            payload={"key": "value"}
        )

        assert event.topic == "test.topic"
        assert event.payload == {"key": "value"}
        assert event.event_id is not None
        assert event.timestamp is not None
        assert event.tenant_id is None

    def test_event_with_tenant(self):
        """Test Event creation with tenant ID."""
        event = Event(
            topic="test.topic",
            payload={"key": "value"},
            tenant_id="tenant-123"
        )

        assert event.tenant_id == "tenant-123"

    @patch('dotmac.platform.tasks.app')
    def test_publish_event(self, mock_app):
        """Test event publishing."""
        # Mock the Celery app
        mock_result = Mock()
        mock_result.id = "task-123"
        mock_app.send_task.return_value = mock_result

        # Publish an event
        event_id = publish_event("user.created", {"user_id": 123})

        # Verify Celery task was sent
        mock_app.send_task.assert_called_once()
        call_args = mock_app.send_task.call_args

        assert call_args[0][0] == "events.user.created"  # Task name
        assert call_args[1]["kwargs"]["payload"] == {"user_id": 123}
        assert call_args[1]["routing_key"] == "user.created"
        assert event_id is not None

    @patch('dotmac.platform.tasks.app')
    def test_publish_event_with_tenant(self, mock_app):
        """Test event publishing with tenant ID."""
        mock_result = Mock()
        mock_result.id = "task-123"
        mock_app.send_task.return_value = mock_result

        event_id = publish_event("user.created", {"user_id": 123}, tenant_id="tenant-456")

        call_args = mock_app.send_task.call_args
        assert call_args[1]["kwargs"]["tenant_id"] == "tenant-456"

    def test_event_handler_decorator(self):
        """Test the event handler decorator."""

        @event_handler("test.event")
        def test_handler(event):
            return f"Handled {event.topic}"

        # Check that the handler has the Celery task attached
        assert hasattr(test_handler, '_celery_task')
        assert hasattr(test_handler, '_topic')
        assert test_handler._topic == "test.event"

    def test_event_handler_with_options(self):
        """Test event handler with custom retry options."""

        @event_handler("test.event", max_retries=5, retry_delay=10)
        def test_handler_with_options(event):
            return "handled"

        # The decorator should have been applied
        assert test_handler_with_options._topic == "test.event"

    @patch('dotmac.platform.communications.events.events.logger')
    def test_handler_execution(self, mock_logger):
        """Test that handler can process events."""

        @event_handler("test.execution")
        def execution_handler(event):
            assert event.topic == "test.execution"
            assert event.payload["test"] == "data"
            return "success"

        # Simulate Celery task execution
        task = execution_handler._celery_task

        # Mock the self parameter (Celery task instance)
        mock_self = Mock()

        result = task(
            mock_self,
            event_id="test-id",
            payload={"test": "data"},
            timestamp="2023-01-01T00:00:00+00:00",
            tenant_id=None
        )

        assert result == "success"

    @patch('dotmac.platform.communications.events.events.logger')
    def test_handler_retry_on_failure(self, mock_logger):
        """Test that handler retries on failure."""

        @event_handler("test.failure")
        def failing_handler(event):
            raise ValueError("Test error")

        task = failing_handler._celery_task
        mock_self = Mock()

        # The task should call retry on failure
        with pytest.raises(Exception):
            task(
                mock_self,
                event_id="test-id",
                payload={"test": "data"},
                timestamp="2023-01-01T00:00:00+00:00"
            )

        # Verify retry was called
        mock_self.retry.assert_called_once()

    def test_integration_example(self):
        """Test a complete integration example."""
        results = []

        @event_handler("user.registered")
        def send_welcome_email(event):
            user_id = event.payload["user_id"]
            email = event.payload["email"]
            results.append(f"Welcome email sent to {email} for user {user_id}")
            return "email_sent"

        @event_handler("user.registered")
        def update_analytics(event):
            user_id = event.payload["user_id"]
            results.append(f"Analytics updated for user {user_id}")
            return "analytics_updated"

        # Both handlers should be registered for the same topic
        assert send_welcome_email._topic == "user.registered"
        assert update_analytics._topic == "user.registered"

        # Test that handlers can process the same event
        event_data = {
            "event_id": "test-123",
            "payload": {"user_id": 456, "email": "test@example.com"},
            "timestamp": "2023-01-01T00:00:00+00:00",
            "tenant_id": None
        }

        # Simulate both handlers processing the event
        mock_self = Mock()
        send_welcome_email._celery_task(mock_self, **event_data)
        update_analytics._celery_task(mock_self, **event_data)

        assert len(results) == 2
        assert "Welcome email sent to test@example.com for user 456" in results
        assert "Analytics updated for user 456" in results