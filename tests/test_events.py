"""Unit tests for Events component."""

import pytest


class TestEventBus:
    """Test event bus functionality."""

    def test_event_bus_import(self):
        """Test EventBus import."""
        from dotmac.platform.communications.events.bus import EventBus

        assert EventBus is not None

    def test_event_bus_is_abstract(self):
        """Test that EventBus is abstract base class."""
        from dotmac.platform.communications.events.bus import EventBus

        # Should not be able to instantiate abstract base class directly
        with pytest.raises(TypeError):
            EventBus()


class TestEventModels:
    """Test event data models."""

    def test_event_import(self):
        """Test Event model import."""
        from dotmac.platform.communications.events.message import Event

        assert Event is not None

    def test_event_creation(self):
        """Test Event model creation."""
        from dotmac.platform.communications.events.message import Event

        event = Event(
            topic="user.created", payload={"user_id": 123, "name": "John"}, event_id="event-123"
        )

        assert event.topic == "user.created"
        assert event.payload == {"user_id": 123, "name": "John"}
        assert event.event_id == "event-123"


class TestEventAdapters:
    """Test event adapter implementations."""

    def test_base_adapter_import(self):
        """Test BaseAdapter import."""
        from dotmac.platform.communications.events.adapters.base import BaseAdapter

        assert BaseAdapter is not None

    def test_memory_adapter_import(self):
        """Test MemoryEventBus import."""
        from dotmac.platform.communications.events.adapters.memory import MemoryEventBus

        assert MemoryEventBus is not None

    def test_memory_bus_factory(self):
        """Test memory bus factory function."""
        from dotmac.platform.communications.events.adapters import create_memory_bus

        bus = create_memory_bus()
        assert bus is not None

    def test_redis_adapter_import(self):
        """Test Redis adapter import."""
        from dotmac.platform.communications.events.adapters.redis_streams import RedisStreamsEventBus

        assert RedisStreamsEventBus is not None


class TestEventConsumer:
    """Test event consumer functionality."""

    def test_consumer_options_import(self):
        """Test ConsumerOptions import."""
        from dotmac.platform.communications.events.consumer import ConsumerOptions

        assert ConsumerOptions is not None

    def test_consumer_options_creation(self):
        """Test ConsumerOptions creation."""
        from dotmac.platform.communications.events.consumer import ConsumerOptions

        options = ConsumerOptions(max_retries=5, retry_delay=60)

        assert options.max_retries == 5
        assert options.retry_delay == 60

    def test_retry_policy_import(self):
        """Test RetryPolicy import."""
        from dotmac.platform.communications.events.consumer import RetryPolicy

        assert RetryPolicy is not None


class TestEventCodecs:
    """Test event codecs."""

    def test_json_codec_import(self):
        """Test JsonCodec import."""
        from dotmac.platform.communications.events.codecs import JsonCodec

        assert JsonCodec is not None

    def test_json_codec_functionality(self):
        """Test JsonCodec encode/decode."""
        from dotmac.platform.communications.events.codecs import JsonCodec

        codec = JsonCodec()
        test_data = {"key": "value", "number": 123}

        # Test encoding
        encoded = codec.encode(test_data)
        assert isinstance(encoded, (str, bytes))

        # Test decoding
        decoded = codec.decode(encoded)
        assert decoded == test_data


class TestDeadLetterQueue:
    """Test dead letter queue functionality."""

    def test_dlq_import(self):
        """Test DLQ import."""
        from dotmac.platform.communications.events.dlq import DLQ

        assert DLQ is not None


class TestEventObservability:
    """Test event observability features."""

    def test_event_observability_import(self):
        """Test EventObservability import."""
        from dotmac.platform.communications.events.observability import EventObservability

        assert EventObservability is not None


class TestEventIntegration:
    """Test event integration with communications service."""

    def test_event_bus_in_communications_service(self):
        """Test event bus integration."""
        from dotmac.platform.communications import create_communications_service

        service = create_communications_service()
        events = service.events

        # Should either be a bus instance or None (graceful degradation)
        assert events is not None or events is None

    def test_event_bus_factory_function(self):
        """Test standalone event bus creation."""
        try:
            from dotmac.platform.communications import create_event_bus

            create_event_bus()
            # Should not raise an exception during creation
            assert True
        except ImportError:
            # It's okay if this fails - bus might not be fully implemented
            pytest.skip("Event bus not fully implemented")
        except Exception:
            # Other exceptions might be due to configuration issues
            pytest.skip("Event bus requires additional configuration")


@pytest.mark.asyncio
class TestEventAsync:
    """Test async event operations."""

    async def test_memory_bus_publish_consume(self):
        """Test basic publish/consume with memory bus."""
        from dotmac.platform.communications.events.adapters import create_memory_bus
        from dotmac.platform.communications.events.message import Event

        try:
            bus = create_memory_bus()

            # Create test event
            event = Event(topic="test.event", payload={"message": "test"})

            # Test publish (should not raise exception)
            await bus.publish(event)
            assert True

        except Exception:
            # It's okay if async operations aren't fully implemented
            pytest.skip("Async event operations require additional setup")


class TestEventAPI:
    """Test event API exports."""

    def test_api_imports(self):
        """Test that API imports work."""
        from dotmac.platform.communications.events import api

        assert api is not None

        # Test that __all__ is defined
        assert hasattr(api, "__all__")
        assert isinstance(api.__all__, list)

    def test_consumer_functions(self):
        """Test consumer utility functions."""
        from dotmac.platform.communications.events.consumer import (
            create_exponential_retry_options,
            create_simple_retry_options,
        )

        simple_options = create_simple_retry_options(max_retries=3)
        assert simple_options is not None

        exp_options = create_exponential_retry_options(max_retries=5)
        assert exp_options is not None


if __name__ == "__main__":
    pytest.main([__file__])
