"""Tests for resilience module."""
import pytest
from dotmac.platform.resilience import CircuitBreakerState, RetryPolicy

class TestResilience:
    def test_circuit_breaker_state(self):
        """Test circuit breaker state initialization."""
        cb_state = CircuitBreakerState(
            service_name="test_service",
            failure_threshold=5,
            timeout_seconds=30
        )
        assert cb_state.service_name == "test_service"
        assert cb_state.is_open is False
        
    def test_retry_policy(self):
        """Test retry policy enum."""
        assert RetryPolicy.EXPONENTIAL_BACKOFF == "exponential_backoff"
        assert RetryPolicy.NONE == "none"
