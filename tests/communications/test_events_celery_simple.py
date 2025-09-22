"""
Simple tests for the Celery-based events system.
"""

import pytest
from unittest.mock import Mock, patch

from dotmac.platform.communications.events import Event, publish_event, event_handler


class TestCeleryEventsSimple:
    """Simple tests for the Celery events system."""

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

    @patch('dotmac.platform.tasks.app')
    def test_publish_event(self, mock_app):
        """Test event publishing."""
        mock_result = Mock()
        mock_result.id = "task-123"
        mock_app.send_task.return_value = mock_result

        event_id = publish_event("user.created", {"user_id": 123})

        # Verify Celery task was sent
        mock_app.send_task.assert_called_once()
        call_args = mock_app.send_task.call_args

        assert call_args[0][0] == "events.user.created"  # Task name
        assert call_args[1]["kwargs"]["payload"] == {"user_id": 123}
        assert event_id is not None

    def test_event_handler_decorator(self):
        """Test the event handler decorator."""

        @event_handler("test.event")
        def test_handler(event):
            return f"Handled {event.topic}"

        # Check that the handler has the Celery task attached
        assert hasattr(test_handler, '_celery_task')
        assert hasattr(test_handler, '_topic')
        assert test_handler._topic == "test.event"

    def test_multiple_handlers_same_topic(self):
        """Test multiple handlers for the same topic."""

        @event_handler("order.created")
        def send_confirmation_email(event):
            return "email_sent"

        @event_handler("order.created")
        def update_inventory(event):
            return "inventory_updated"

        # Both should be registered for the same topic
        assert send_confirmation_email._topic == "order.created"
        assert update_inventory._topic == "order.created"

    @patch('dotmac.platform.tasks.app')
    def test_publish_event_with_tenant(self, mock_app):
        """Test event publishing with tenant isolation."""
        mock_result = Mock()
        mock_result.id = "task-456"
        mock_app.send_task.return_value = mock_result

        event_id = publish_event("tenant.event", {"data": "test"}, tenant_id="tenant-123")

        call_args = mock_app.send_task.call_args
        assert call_args[1]["kwargs"]["tenant_id"] == "tenant-123"

    def test_handler_registration_example(self):
        """Test a realistic handler registration example."""

        @event_handler("user.registered", max_retries=5, retry_delay=10)
        def process_user_registration(event):
            user_id = event.payload["user_id"]
            email = event.payload["email"]
            # In real code, this would send an email, create records, etc.
            return {"user_id": user_id, "welcome_email_sent": True}

        # Verify handler is properly configured
        assert process_user_registration._topic == "user.registered"
        assert hasattr(process_user_registration, '_celery_task')

        # The actual Celery task should be accessible
        celery_task = process_user_registration._celery_task
        assert celery_task.name == "events.user.registered"