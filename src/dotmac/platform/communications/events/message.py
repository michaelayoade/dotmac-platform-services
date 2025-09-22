"""
Legacy message types for backward compatibility.
Most functionality moved to events.py for simplicity.
"""

# Re-export Event from the main events module
from .events import Event

__all__ = ["Event"]

# Note: EventMetadata, MessageCodec, and other complex types
# have been removed in favor of simple Celery task arguments