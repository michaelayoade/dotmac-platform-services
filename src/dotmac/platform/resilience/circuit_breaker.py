"""Compatibility circuit breaker utilities used by tests.

This module provides a lightweight circuit breaker implementation that mirrors
the interface exposed by the API gateway and legacy resilience layer. It keeps
track of the failure count and exposes simple helper methods used by unit
tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from time import monotonic
from typing import Optional


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """Minimal circuit breaker implementation suitable for tests."""

    failure_threshold: int = 5
    recovery_timeout: float = 30.0

    _state: CircuitBreakerState = CircuitBreakerState.CLOSED
    _failure_count: int = 0
    _opened_at: Optional[float] = None

    def allow_request(self) -> bool:
        """Return whether a request should be allowed."""
        if self._state == CircuitBreakerState.OPEN:
            if self._opened_at is None:
                return False
            if monotonic() - self._opened_at >= self.recovery_timeout:
                self._state = CircuitBreakerState.HALF_OPEN
            else:
                return False
        return True

    def record_success(self) -> None:
        """Reset the breaker on success."""
        self._failure_count = 0
        self._state = CircuitBreakerState.CLOSED
        self._opened_at = None

    def record_failure(self) -> None:
        """Record a failure and trip the breaker if necessary."""
        self._failure_count += 1
        if self._failure_count >= self.failure_threshold:
            self._trip()

    def current_state(self) -> CircuitBreakerState:
        """Return current breaker state."""
        return self._state

    def _trip(self) -> None:
        self._state = CircuitBreakerState.OPEN
        self._opened_at = monotonic()


__all__ = ["CircuitBreaker", "CircuitBreakerState"]
