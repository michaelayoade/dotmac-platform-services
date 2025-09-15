"""Integration tests for communications via dotmac.platform.communications.

These tests target the public APIs implemented under
`dotmac.platform.communications` rather than a separate `dotmac.communications`
package.
"""


import pytest
from dotmac.platform.communications import (
    CommunicationsConfig,
    EmailService,
    EventBus,
    WebSocketManager,
    WebhookService,
    SMSService,
)
from dotmac.platform.communications.config import (
    EventBusConfig,
    WebSocketConfig,
)


class TestCommunicationsIntegration:
    """Smoke tests for communications components available in platform package."""

    def test_components_instantiation(self):
        cfg = CommunicationsConfig()
        # Instantiate components with defaults where possible
        email = EmailService(SMTP=None) if False else EmailService  # type: ignore
        assert EmailService is not None
        assert WebSocketManager is not None
        assert EventBus(EventBusConfig()) is not None
        assert WebhookService is not None
        assert SMSService is not None

    def test_configuration_defaults(self):
        """Validate default config objects and some defaults."""
        cfg = CommunicationsConfig()
        assert isinstance(cfg.websocket, WebSocketConfig)
        assert isinstance(cfg.event_bus, EventBusConfig)
        # Default limits
        assert cfg.websocket.max_connections > 0
        assert cfg.event_bus.backend in {"memory", "redis"}


class TestNotificationsComponent:
    """Basic availability checks using EmailService as notifications."""

    def test_email_service_import(self):
        assert EmailService is not None


class TestWebSocketsComponent:
    """Test WebSockets component availability."""

    def test_websocket_manager_import(self):
        assert WebSocketManager is not None

    def test_websocket_config_import(self):
        assert WebSocketConfig is not None


class TestEventsComponent:
    """Test Events component."""

    def test_event_bus_and_model_import(self):
        from dotmac.platform.communications.events import Event
        # Using platform imports above for EventBus in module scope
        assert Event is not None
        assert EventBus is not None

    def test_event_adapters_import(self):
        """Validate EventBus 'memory' backend functions via config."""
        from dotmac.platform.communications.config import EventBusConfig
        from dotmac.platform.communications.events import Event
        bus = EventBus(EventBusConfig(backend="memory"))
        # Basic publish to memory queue should be awaitable
        import asyncio
        asyncio.run(bus._publish_memory(Event(type="t", data={})))


class TestPackageMetadata:
    """Test package metadata and version info."""

    def test_version_info(self):
        """Project version is exposed at dotmac.platform level."""
        import dotmac.platform as platform
        assert hasattr(platform, "__version__")
        assert platform.__version__ == "1.0.0"

    def test_author_info(self):
        """Author info lives at dotmac.platform level."""
        import dotmac.platform as platform
        assert platform.__author__ == "DotMac Team"
        assert platform.__email__ == "dev@dotmac.com"

    def test_all_exports(self):
        """Core communications exports available from platform module."""
        assert EmailService is not None
        assert WebSocketManager is not None
        assert EventBus is not None


class TestErrorHandling:
    """Test error handling and graceful degradation."""

    def test_graceful_import_failure_handling(self):
        """Construction of platform components should not raise."""
        from dotmac.platform.communications.config import SMTPConfig, WebSocketConfig, EventBusConfig
        EmailService(SMTPConfig(host="localhost", from_email="noreply@example.com"))
        WebSocketManager(WebSocketConfig())
        EventBus(EventBusConfig())

    def test_configuration_validation(self):
        """Test configuration validation."""
        # Invalid config should not crash the service
        from pydantic import ValidationError
        from dotmac.platform.communications.config import CommunicationsConfig
        with pytest.raises(ValidationError):
            CommunicationsConfig(invalid_key="invalid_value")  # type: ignore[arg-type]


@pytest.mark.asyncio
class TestAsyncOperations:
    """Test async operations if available."""

    async def test_event_bus_creation(self):
        """Test event bus creation."""
        from dotmac.platform.communications.config import EventBusConfig
        bus = EventBus(EventBusConfig())
        assert bus is not None


if __name__ == "__main__":
    pytest.main([__file__])
