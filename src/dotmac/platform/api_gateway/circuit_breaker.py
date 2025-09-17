"""Circuit breaker implementation for API Gateway."""

import asyncio
import time
from enum import Enum
from typing import Any, Callable, Dict, Optional

from dotmac.platform.observability.unified_logging import get_logger

logger = get_logger(__name__)

class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreaker:
    """Circuit breaker for fault tolerance."""

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        recovery_timeout: int = 30,
        half_open_max_requests: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.recovery_timeout = recovery_timeout
        self.half_open_max_requests = half_open_max_requests

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.half_open_requests = 0
        self.success_count = 0
        self.last_state_change = time.time()

    async def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute function with circuit breaker protection."""
        current_time = time.time()

        # Check if circuit is OPEN and should try HALF_OPEN
        if self.state == CircuitState.OPEN:
            if current_time - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_requests = 0
                self.last_state_change = current_time
                logger.info("Circuit breaker transitioning to HALF_OPEN")
            else:
                raise Exception(
                    f"Circuit breaker is OPEN, retry after {self.timeout - (current_time - self.last_failure_time):.0f} seconds"
                )

        # Handle HALF_OPEN state
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_requests >= self.half_open_max_requests:
                # Wait for results of pending requests
                await asyncio.sleep(0.1)

                # Check success ratio
                if self.success_count >= self.half_open_max_requests // 2:
                    self._reset()
                    logger.info("Circuit breaker recovered to CLOSED")
                else:
                    self.state = CircuitState.OPEN
                    self.last_failure_time = current_time
                    self.last_state_change = current_time
                    logger.warning("Circuit breaker returning to OPEN")
                    raise Exception("Circuit breaker failed recovery test")

            self.half_open_requests += 1

        # Try to execute the function
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Success - update state
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.half_open_max_requests:
                    self._reset()
                    logger.info("Circuit breaker recovered to CLOSED")
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                if self.failure_count > 0:
                    self.failure_count = max(0, self.failure_count - 1)

            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = current_time

            # Check if we should open the circuit
            if self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                self.last_state_change = current_time
                logger.warning(f"Circuit breaker opening due to {self.failure_count} failures")
            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                self.last_state_change = current_time
                logger.warning("Circuit breaker returning to OPEN after failure in HALF_OPEN")

            raise e

    def _reset(self):
        """Reset circuit breaker to closed state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.half_open_requests = 0
        self.success_count = 0
        self.last_state_change = time.time()

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        current_time = time.time()
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "time_since_last_failure": (
                current_time - self.last_failure_time if self.last_failure_time else None
            ),
            "time_in_current_state": current_time - self.last_state_change,
            "half_open_requests": (
                self.half_open_requests if self.state == CircuitState.HALF_OPEN else None
            ),
            "success_count": self.success_count if self.state == CircuitState.HALF_OPEN else None,
        }

    def is_open(self) -> bool:
        """Check if circuit is open."""
        return self.state == CircuitState.OPEN

    def is_closed(self) -> bool:
        """Check if circuit is closed."""
        return self.state == CircuitState.CLOSED

    def is_half_open(self) -> bool:
        """Check if circuit is half-open."""
        return self.state == CircuitState.HALF_OPEN
