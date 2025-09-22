"""
Simple event system using Celery directly.
Replaces complex event bus with ~100 lines of code.
"""

import uuid
from datetime import datetime, UTC
from dataclasses import dataclass
from typing import Any, Callable, Optional

from celery import shared_task
from dotmac.platform.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Event:
    """Simplified event structure."""
    topic: str
    payload: dict[str, Any]
    event_id: str = None
    timestamp: datetime = None
    tenant_id: Optional[str] = None

    def __post_init__(self):
        if self.event_id is None:
            self.event_id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)


def publish_event(topic: str, payload: dict[str, Any], tenant_id: Optional[str] = None) -> str:
    """
    Publish an event using Celery.

    Args:
        topic: Event topic (becomes Celery task name)
        payload: Event data
        tenant_id: Optional tenant isolation

    Returns:
        Event ID for tracking
    """
    event = Event(topic=topic, payload=payload, tenant_id=tenant_id)

    # Send as Celery task with topic as task name
    task_name = f"events.{topic}"

    try:
        from dotmac.platform.tasks import app
        result = app.send_task(
            task_name,
            kwargs={
                'event_id': event.event_id,
                'payload': event.payload,
                'timestamp': event.timestamp.isoformat(),
                'tenant_id': event.tenant_id,
            },
            routing_key=topic,
        )
        logger.info(f"Published event {event.event_id} to topic '{topic}' as task {result.id}")
        return event.event_id

    except Exception as e:
        logger.error(f"Failed to publish event to topic '{topic}': {e}")
        raise


def event_handler(topic: str, max_retries: int = 3, retry_delay: int = 5):
    """
    Decorator to register a Celery task for handling events.

    Args:
        topic: Event topic to handle
        max_retries: Max retry attempts
        retry_delay: Delay between retries (seconds)
    """
    def decorator(func: Callable):
        task_name = f"events.{topic}"

        @shared_task(
            name=task_name,
            bind=True,
            autoretry_for=(Exception,),
            retry_kwargs={'max_retries': max_retries, 'countdown': retry_delay}
        )
        def celery_task(self, **kwargs):
            """Celery task that calls the handler function."""
            try:
                event_id = kwargs.get('event_id')
                payload = kwargs.get('payload', {})
                timestamp = kwargs.get('timestamp')
                tenant_id = kwargs.get('tenant_id')

                logger.debug(f"Processing event {event_id} on topic '{topic}'")

                # Create event object
                event = Event(
                    topic=topic,
                    payload=payload,
                    event_id=event_id,
                    timestamp=datetime.fromisoformat(timestamp.replace('Z', '+00:00')),
                    tenant_id=tenant_id,
                )

                # Call the handler
                result = func(event)

                logger.info(f"Successfully processed event {event_id} with handler '{func.__name__}'")
                return result

            except Exception as e:
                logger.error(f"Handler '{func.__name__}' failed for event {event_id}: {e}")
                raise self.retry(exc=e)

        # Store the Celery task reference
        func._celery_task = celery_task
        func._topic = topic

        return func

    return decorator


# That's it! ~100 lines replaces 2500+ lines of complex event bus code