"""Consumer runner with retry and backoff logic."""

import asyncio

import random
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Optional

from .bus import EventBus, EventHandler
from .message import Event

from dotmac.platform.observability.unified_logging import get_logger
__all__ = [
    "ConsumerOptions",
    "BackoffPolicy",
    "RetryPolicy",
    "run_consumer",
    "create_retry_wrapper",
]

logger = get_logger(__name__)

@dataclass
class BackoffPolicy:
    """Backoff policy for retries."""

    base_ms: int = 100
    multiplier: float = 2.0
    jitter_ms: int = 50
    max_delay_ms: int = 30000  # 30 seconds

    def calculate_delay(self, retry_count: int) -> float:
        """
        Calculate backoff delay for a retry attempt.

        Args:
            retry_count: Number of retries so far (0-based)

        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay_ms = self.base_ms * (self.multiplier**retry_count)

        # Apply maximum
        delay_ms = min(delay_ms, self.max_delay_ms)

        # Add jitter to avoid thundering herd
        # Note: Using random for non-cryptographic jitter in retry delays is acceptable
        if self.jitter_ms > 0:
            jitter = random.randint(-self.jitter_ms, self.jitter_ms)  # nosec B311
            delay_ms += jitter

        # Ensure non-negative
        delay_ms = max(delay_ms, 0)

        return delay_ms / 1000.0  # Convert to seconds

@dataclass
class RetryPolicy:
    """Retry policy configuration."""

    max_retries: int = 5
    backoff: BackoffPolicy = None
    retry_on_exceptions: tuple[type[Exception], ...] = (Exception,)

    def __post_init__(self) -> None:
        if self.backoff is None:
            self.backoff = BackoffPolicy()

    def should_retry(self, exception: Exception, retry_count: int) -> bool:
        """
        Check if an exception should trigger a retry.

        Args:
            exception: The exception that occurred
            retry_count: Current retry count

        Returns:
            True if should retry, False otherwise
        """
        if retry_count >= self.max_retries:
            return False

        return isinstance(exception, self.retry_on_exceptions)

@dataclass
class ConsumerOptions:
    """Options for the consumer runner."""

    max_retries: int = 5
    backoff_base_ms: int = 100
    backoff_multiplier: float = 2.0
    backoff_jitter_ms: int = 50
    backoff_max_delay_ms: int = 30000
    dlq_topic: Optional[str] = None  # Default: "{topic}.DLQ"
    retry_delay: Optional[int] = None  # Legacy parameter for backward compatibility

    # Callbacks
    on_retry: Optional[Callable[[Event, int, Exception], Awaitable[None]]] = None
    on_dlq: Optional[Callable[[Event, Exception], Awaitable[None]]] = None
    on_success: Optional[Callable[[Event], Awaitable[None]]] = None

    def get_retry_policy(self) -> RetryPolicy:
        """Get retry policy from options."""
        backoff = BackoffPolicy(
            base_ms=self.backoff_base_ms,
            multiplier=self.backoff_multiplier,
            jitter_ms=self.backoff_jitter_ms,
            max_delay_ms=self.backoff_max_delay_ms,
        )

        return RetryPolicy(
            max_retries=self.max_retries,
            backoff=backoff,
        )

    def get_dlq_topic(self, original_topic: str) -> str:
        """Get DLQ topic name."""
        if self.dlq_topic:
            return self.dlq_topic
        return f"{original_topic}.DLQ"

class RetryableHandler:
    """Wrapper that adds retry logic to an event handler."""

    def __init__(
        self,
        original_handler: EventHandler,
        bus: EventBus,
        options: ConsumerOptions,
    ):
        self.original_handler = original_handler
        self.bus = bus
        self.options = options
        self.retry_policy = options.get_retry_policy()

    async def __call__(self, event: Event) -> None:
        """Handle event with retry logic."""
        retry_count = 0

        while True:
            try:
                # Try to handle the event
                await self.original_handler(event)

                # Success callback
                if self.options.on_success:
                    try:
                        await self.options.on_success(event)
                    except Exception as e:
                        logger.warning(f"Success callback failed: {e}")

                # Success - no retry needed
                logger.debug(f"Successfully handled event {event.id} after {retry_count} retries")
                return

            except Exception as e:

                # Check if we should retry
                if not self.retry_policy.should_retry(e, retry_count):
                    logger.error(
                        f"Event {event.id} failed after {retry_count} retries, sending to DLQ: {e}"
                    )
                    await self._send_to_dlq(event, e)
                    return

                # Retry callback
                if self.options.on_retry:
                    try:
                        await self.options.on_retry(event, retry_count + 1, e)
                    except Exception as callback_error:
                        logger.warning(f"Retry callback failed: {callback_error}")

                # Calculate backoff delay
                delay = self.retry_policy.backoff.calculate_delay(retry_count)

                logger.warning(
                    f"Event {event.id} failed (attempt {retry_count + 1}/{self.retry_policy.max_retries}), "
                    f"retrying in {delay:.3f}s: {e}"
                )

                # Wait before retry
                await asyncio.sleep(delay)
                retry_count += 1

    async def _send_to_dlq(self, event: Event, error: Exception) -> None:
        """Send event to Dead Letter Queue."""
        try:
            dlq_topic = self.options.get_dlq_topic(event.topic)

            # Create DLQ event with error information
            dlq_headers = (event.headers or {}).copy()
            dlq_headers.update(
                {
                    "x-original-topic": event.topic,
                    "x-retry-count": str(self.retry_policy.max_retries),
                    "x-error": str(error),
                    "x-error-type": type(error).__name__,
                    "x-dlq-timestamp": str(int(time.time())),
                }
            )

            dlq_event = Event(
                topic=dlq_topic,
                payload=event.payload,
                key=event.key,
                headers=dlq_headers,
                tenant_id=event.tenant_id,
                metadata=event.metadata,
            )

            # Publish to DLQ
            await self.bus.publish(dlq_event)

            logger.info(f"Sent event {event.id} to DLQ topic '{dlq_topic}'")

            # DLQ callback
            if self.options.on_dlq:
                try:
                    await self.options.on_dlq(event, error)
                except Exception as callback_error:
                    logger.warning(f"DLQ callback failed: {callback_error}")

        except Exception as dlq_error:
            logger.error(f"Failed to send event {event.id} to DLQ: {dlq_error}")

async def run_consumer(
    bus: EventBus,
    topic: str,
    handler: EventHandler,
    options: Optional[ConsumerOptions] = None,
    **subscribe_kwargs: Any,
) -> None:
    """
    Run a consumer with retry and DLQ functionality.

    This is a convenience function that wraps the handler with retry logic
    and subscribes to the topic.

    Args:
        bus: Event bus to consume from
        topic: Topic to consume from
        handler: Event handler function
        options: Consumer options (uses defaults if None)
        **subscribe_kwargs: Additional arguments for bus.subscribe()
    """
    if options is None:
        options = ConsumerOptions()

    # Create retryable handler
    retryable_handler = RetryableHandler(handler, bus, options)

    # Subscribe with the wrapped handler
    await bus.subscribe(topic, retryable_handler, **subscribe_kwargs)

def create_retry_wrapper(
    handler: EventHandler,
    bus: EventBus,
    options: Optional[ConsumerOptions] = None,
) -> RetryableHandler:
    """
    Create a retry wrapper for an event handler.

    This allows you to add retry logic to any handler without using run_consumer.

    Args:
        handler: Original event handler
        bus: Event bus (for DLQ publishing)
        options: Consumer options (uses defaults if None)

    Returns:
        Wrapped handler with retry logic
    """
    if options is None:
        options = ConsumerOptions()

    return RetryableHandler(handler, bus, options)

# Convenience functions for common retry patterns

def create_simple_retry_options(
    max_retries: int = 3,
    base_delay_ms: int = 1000,
    dlq_topic: Optional[str] = None,
) -> ConsumerOptions:
    """Create simple retry options."""
    return ConsumerOptions(
        max_retries=max_retries,
        backoff_base_ms=base_delay_ms,
        backoff_multiplier=1.0,  # Fixed delay
        backoff_jitter_ms=0,  # No jitter
        dlq_topic=dlq_topic,
    )

def create_exponential_retry_options(
    max_retries: int = 5,
    base_delay_ms: int = 100,
    max_delay_ms: int = 30000,
    dlq_topic: Optional[str] = None,
) -> ConsumerOptions:
    """Create exponential backoff retry options."""
    return ConsumerOptions(
        max_retries=max_retries,
        backoff_base_ms=base_delay_ms,
        backoff_multiplier=2.0,
        backoff_jitter_ms=50,
        backoff_max_delay_ms=max_delay_ms,
        dlq_topic=dlq_topic,
    )
