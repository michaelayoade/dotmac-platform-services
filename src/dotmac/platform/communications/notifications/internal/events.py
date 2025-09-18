"""
Standalone event system for notifications
Replaces dependency on dotmac.websockets.core.events
"""

import asyncio

from collections.abc import Callable
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

class EventPriority(str, Enum):
    """Event priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class WebSocketEvent(BaseModel):
    """WebSocket event model"""

    event_id: str
    event_type: str
    payload: dict[str, Any]
    priority: EventPriority = EventPriority.NORMAL
    created_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None

class EventManager:
    """Standalone event manager for notifications"""

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}
        self._event_history: list[WebSocketEvent] = []

    def register_handler(self, event_type: str, handler: Callable):
        """Register an event handler"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def emit_event(self, event: WebSocketEvent) -> bool:
        """Emit an event to registered handlers"""
        try:
            self._event_history.append(event)

            handlers = self._handlers.get(event.event_type, [])
            if not handlers:
                logger.warning(f"No handlers registered for event type: {event.event_type}")
                return False

            # Execute handlers
            tasks = []
            for handler in handlers:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(handler(event))
                else:
                    # Wrap sync handlers
                    tasks.append(asyncio.create_task(asyncio.to_thread(handler, event)))

            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                # Log any exceptions but don't fail the event
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"Handler {i} failed for event {event.event_id}: {result}")

            return True

        except Exception as e:
            logger.error(f"Failed to emit event {event.event_id}: {e}")
            return False

    async def create_notification_event(
        self,
        notification_id: str,
        status: str,
        channel: str,
        recipient: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> WebSocketEvent:
        """Create a notification-specific event"""
        return WebSocketEvent(
            event_id=str(uuid4()),
            event_type="notification_status",
            payload={
                "notification_id": notification_id,
                "status": status,
                "channel": channel,
                "recipient": recipient,
                "timestamp": datetime.now(UTC).isoformat(),
            },
            priority=EventPriority.NORMAL,
            created_at=datetime.now(UTC),
            metadata=metadata or {},
        )
