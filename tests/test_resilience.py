"""Tests for resilience module."""

import pytest
from dotmac.platform.resilience import CircuitBreaker, CircuitBreakerState, RetryPolicy


class TestResilience:
    def test_circuit_breaker_state(self):
        """Test circuit breaker state initialization."""
        # Test CircuitBreakerState enum
        assert CircuitBreakerState.CLOSED == "closed"
        assert CircuitBreakerState.OPEN == "open"
        assert CircuitBreakerState.HALF_OPEN == "half_open"

        # Test CircuitBreaker class
        cb = CircuitBreaker(failure_threshold=5, recovery_timeout=30.0)
        assert cb.failure_threshold == 5
        assert cb.recovery_timeout == 30.0
        assert cb.current_state() == CircuitBreakerState.CLOSED

    def test_retry_policy(self):
        """Test retry policy enum."""
        assert RetryPolicy.EXPONENTIAL_BACKOFF == "exponential_backoff"
        assert RetryPolicy.NONE == "none"
