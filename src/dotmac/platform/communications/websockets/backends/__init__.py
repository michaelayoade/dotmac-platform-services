"""
Scaling backends for WebSocket gateway.
"""

from .base import ScalingBackend
from .local import LocalBackend

try:
    from .redis import RedisScalingBackend
except ImportError:
    RedisScalingBackend = None

__all__ = [
    "ScalingBackend",
    "LocalBackend",
    "RedisScalingBackend",  # May be None if Redis not available
]
