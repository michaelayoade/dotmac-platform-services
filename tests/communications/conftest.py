"""Test configuration and fixtures for dotmac-communications tests."""

import asyncio
from typing import Any
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def communications_config() -> dict[str, Any]:
    """Provide test configuration for communications service."""
    return {
        "notifications": {
            "retry_attempts": 2,
            "retry_delay": 1,  # Fast retry for tests
            "delivery_timeout": 10,
            "track_delivery": True,
        },
        "websockets": {
            "connection_timeout": 30,
            "heartbeat_interval": 10,
            "max_connections_per_tenant": 100,
            "message_size_limit": 1024,
            "enable_compression": False,  # Disable for simpler tests
        },
        "events": {
            "default_adapter": "memory",
            "retry_policy": "simple",
            "max_retries": 2,
            "dead_letter_enabled": True,
            "event_ttl": 300,
        },
        "redis": {
            "host": "localhost",
            "port": 6379,
            "db": 1,  # Use different DB for tests
            "connection_pool_size": 2,
        },
    }


@pytest.fixture
def mock_notification_service():
    """Provide mock notification service."""
    mock = MagicMock()
    mock.send_email = MagicMock(return_value={"status": "sent", "id": "test-123"})
    mock.send_sms = MagicMock(return_value={"status": "sent", "id": "test-456"})
    mock.send_push = MagicMock(return_value={"status": "sent", "id": "test-789"})
    return mock


@pytest.fixture
def mock_websocket_manager():
    """Provide mock WebSocket manager."""
    mock = MagicMock()
    mock.connect = MagicMock()
    mock.disconnect = MagicMock()
    mock.broadcast = MagicMock()
    mock.send_to_channel = MagicMock()
    return mock


@pytest.fixture
def mock_event_bus():
    """Provide mock event bus."""
    mock = MagicMock()
    mock.publish = MagicMock()
    mock.subscribe = MagicMock()
    mock.unsubscribe = MagicMock()
    return mock


# Use pytest-asyncio's default event loop fixture; avoid defining our own here


@pytest.fixture
async def async_communications_service(communications_config):
    """Provide async communications service for testing."""
    from dotmac.platform.communications import EmailService, WebSocketManager, EventBus
    from dotmac.platform.communications.config import WebSocketConfig, EventBusConfig

    class MockCommunicationsService:
        def __init__(self):
            self.email = EmailService()
            self.websockets = WebSocketManager(WebSocketConfig())
            self.events = EventBus(EventBusConfig())

        async def cleanup(self):
            pass

    service = MockCommunicationsService()
    yield service

    # Cleanup
    try:
        if hasattr(service, "cleanup"):
            await service.cleanup()
    except Exception:
        pass  # Ignore cleanup errors in tests


@pytest.fixture
def sample_notification_request():
    """Provide sample notification request."""
    return {
        "recipient": "test@example.com",
        "subject": "Test Notification",
        "message": "This is a test notification",
        "template": "test_template",
        "context": {"name": "Test User", "action": "test"},
        "priority": "normal",
        "channels": ["email"],
    }


@pytest.fixture
def sample_event():
    """Provide sample event."""
    return {
        "topic": "user.created",
        "payload": {"user_id": "user-123", "name": "Test User", "email": "test@example.com"},
        "event_id": "event-456",
        "timestamp": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_websocket_message():
    """Provide sample WebSocket message."""
    return {
        "type": "message",
        "channel": "test_channel",
        "data": {"message": "Hello WebSocket!", "from": "test_user"},
        "timestamp": "2024-01-01T00:00:00Z",
    }


# Note: Avoid declaring pytest_plugins in non-top-level conftest (deprecated in pytest 8).
# If plugin loading is needed for the whole suite, declare it in tests/conftest.py.


def pytest_configure(config):
    """Configure pytest with custom marks."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "async: mark test as async test")
    config.addinivalue_line("markers", "redis: mark test as requiring Redis")
    config.addinivalue_line("markers", "slow: mark test as slow running")


# Helper functions for tests
class TestHelpers:
    """Helper functions for tests."""

    @staticmethod
    def assert_valid_notification_response(response):
        """Assert that notification response is valid."""
        required_keys = ["status", "id"]
        for key in required_keys:
            assert key in response, f"Missing key: {key}"

        valid_statuses = ["sent", "pending", "failed", "delivered"]
        assert response["status"] in valid_statuses
        assert isinstance(response["id"], str)
        assert len(response["id"]) > 0

    @staticmethod
    def assert_valid_event(event):
        """Assert that event is valid."""
        required_keys = ["topic", "payload"]
        for key in required_keys:
            assert key in event, f"Missing key: {key}"

        assert isinstance(event["topic"], str)
        assert len(event["topic"]) > 0
        assert isinstance(event["payload"], dict)

    @staticmethod
    def create_mock_websocket():
        """Create mock WebSocket connection."""
        mock_ws = MagicMock()
        mock_ws.send = MagicMock()
        mock_ws.receive = MagicMock()
        mock_ws.close = MagicMock()
        mock_ws.closed = False
        return mock_ws


# Make helpers available to tests
@pytest.fixture
def test_helpers():
    """Provide test helper functions."""
    return TestHelpers()
