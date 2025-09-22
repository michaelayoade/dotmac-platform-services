"""
DotMac Events - Direct Celery implementation.

Replaces 2500+ lines of complex event bus code with simple Celery tasks.
No wrappers, no adapters, just direct Celery usage.

Example usage:

    from dotmac.platform.communications.events import publish_event, event_handler

    # Publish an event
    publish_event("user.created", {"user_id": 123, "name": "John"})

    # Handle events with decorator
    @event_handler("user.created")
    def handle_user_created(user_id, name):
        print(f"User {name} (ID: {user_id}) was created")

Benefits:
- Uses Celery directly (industry standard)
- Built-in retry, monitoring, scaling
- 95%+ code reduction
- No custom abstractions
"""

from .events import publish_event, event_handler, Event

__all__ = ["publish_event", "event_handler", "Event"]