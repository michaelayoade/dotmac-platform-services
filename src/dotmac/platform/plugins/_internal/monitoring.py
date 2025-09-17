"""
No-op monitoring service implementation for optional dependency.
"""


from typing import Any, Optional

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

class NoOpMonitoringService:
    """No-op monitoring service that logs operations."""

    def __init__(self):
        logger.debug("Initialized no-op monitoring service")

    def record_metric(self, name: str, value: float, tags: Optional[dict[str, str]] = None) -> None:
        """Record a metric (no-op)."""
        logger.debug(f"Record metric: {name}={value} tags={tags} (no-op)")

    def increment_counter(self, name: str, tags: Optional[dict[str, str]] = None) -> None:
        """Increment a counter (no-op)."""
        logger.debug(f"Increment counter: {name} tags={tags} (no-op)")

    def record_timing(
        self, name: str, duration_ms: float, tags: Optional[dict[str, str]] = None
    ) -> None:
        """Record timing (no-op)."""
        logger.debug(f"Record timing: {name}={duration_ms}ms tags={tags} (no-op)")

    def set_gauge(self, name: str, value: float, tags: Optional[dict[str, str]] = None) -> None:
        """Set gauge value (no-op)."""
        logger.debug(f"Set gauge: {name}={value} tags={tags} (no-op)")

def get_monitoring() -> NoOpMonitoringService:
    """Get the monitoring service instance."""
    return NoOpMonitoringService()
