"""EventBus interface and core exceptions."""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any, Optional

from .message import Event

__all__ = [
    "EventBus",
    "EventHandler",
    "EventBusError",
    "PublishError",
    "ConsumeError",
    "TimeoutError",
    "NotSupportedError",
]


# Type aliases
EventHandler = Callable[[Event], Awaitable[None]]


class EventBusError(Exception):
    """Base exception for all event bus errors."""

    pass


class PublishError(EventBusError):
    """Raised when publishing an event fails."""

    def __init__(
        self, message: str, event: Optional[Event] = None, cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.event = event
        self.cause = cause


class ConsumeError(EventBusError):
    """Raised when consuming events fails."""

    def __init__(
        self, message: str, topic: Optional[str] = None, cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.topic = topic
        self.cause = cause


class TimeoutError(EventBusError):
    """Raised when an operation times out."""

    pass


class NotSupportedError(EventBusError):
    """Raised when an operation is not supported by the adapter."""

    pass


class EventBus(ABC):
    """
    Abstract base class for event bus implementations.

    The EventBus provides a transport-agnostic interface for publishing
    and subscribing to events. Concrete implementations handle the
    specifics of different message brokers (Redis, Kafka, in-memory, etc.).
    """

    @abstractmethod
    async def publish(
        self,
        event: Event,
        *,
        partition_key: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Publish an event to the bus.

        Args:
            event: The event to publish
            partition_key: Optional key for partitioning (adapter-dependent)
            headers: Additional headers to add to the event

        Raises:
            PublishError: If the event could not be published
        """
        ...

    @abstractmethod
    async def subscribe(
        self,
        topic: str,
        handler: EventHandler,
        *,
        group: str = "default",
        concurrency: int = 1,
        auto_offset_reset: str = "latest",
        **kwargs: Any,
    ) -> None:
        """
        Subscribe to events on a topic.

        Args:
            topic: Topic to subscribe to
            handler: Async function to handle events
            group: Consumer group name
            concurrency: Number of concurrent handlers
            auto_offset_reset: Where to start consuming ("earliest" or "latest")
            **kwargs: Additional adapter-specific options

        Raises:
            ConsumeError: If subscription could not be established
        """
        ...

    async def request(
        self,
        subject: str,
        payload: dict[str, Any],
        timeout: float = 5.0,
    ) -> dict[str, Any]:
        """
        Send a request and wait for a response (request-reply pattern).

        This is an optional method that not all adapters support.

        Args:
            subject: Subject/topic to send the request to
            payload: Request payload
            timeout: Maximum time to wait for response

        Returns:
            Response payload

        Raises:
            NotSupportedError: If the adapter doesn't support request-reply
            TimeoutError: If no response is received within timeout
        """
        raise NotSupportedError("Request-reply pattern not supported by this adapter")

    @abstractmethod
    async def close(self) -> None:
        """
        Close the event bus and cleanup resources.

        This should gracefully shut down all consumers and release
        any connections or resources held by the adapter.
        """
        ...

    # Convenience methods

    async def publish_dict(
        self,
        topic: str,
        payload: dict[str, Any],
        *,
        key: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
        tenant_id: Optional[str] = None,
        partition_key: Optional[str] = None,
    ) -> None:
        """
        Publish a simple dictionary payload as an event.

        This is a convenience method that creates an Event from the parameters.
        """
        event = Event(
            topic=topic,
            payload=payload,
            key=key,
            headers=headers,
            tenant_id=tenant_id,
        )

        await self.publish(event, partition_key=partition_key)

    # Context manager support

    async def __aenter__(self) -> "EventBus":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    # String representation

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}()"
