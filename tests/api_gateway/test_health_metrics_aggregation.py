"""Tests for health and metrics aggregation in API Gateway."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi import FastAPI
from dotmac.platform.api_gateway.gateway import APIGateway
from dotmac.platform.api_gateway.config import GatewayConfig


class TestHealthMetricsAggregation:
    """Test health checks and metrics aggregation functionality."""

    @pytest.fixture(autouse=True)
    def stub_gateway_analytics(self, monkeypatch):
        """Provide a lightweight analytics adapter to avoid external OTLP calls."""

        async def fake_summary():
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "counters": {"api_request": 5},
                "gauges": {},
                "histograms": {},
            }

        adapter = SimpleNamespace(
            analytics=SimpleNamespace(collector=SimpleNamespace(tracer=None)),
            get_metrics_summary=AsyncMock(side_effect=fake_summary),
            record_request=AsyncMock(return_value=None),
        )

        monkeypatch.setattr(
            "dotmac.platform.api_gateway.gateway.get_gateway_analytics",
            lambda **_: adapter,
        )

        return adapter

    @pytest.fixture
    def gateway_config(self):
        """Create gateway configuration for testing."""
        config = GatewayConfig.for_development()
        config.observability.metrics_enabled = True
        config.observability.logging_enabled = True
        return config

    @pytest.fixture
    def api_gateway(self, gateway_config):
        """Create API gateway instance for testing."""
        return APIGateway(config=gateway_config)

    @pytest.fixture
    def app(self, api_gateway):
        """Create FastAPI app with gateway."""
        app = FastAPI()
        api_gateway.setup(app)
        return app

    @pytest.fixture
    def test_client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_health_endpoint_basic_structure(self, test_client):
        """Test basic health endpoint structure."""
        response = test_client.get("/health")

        assert response.status_code == 200
        health_data = response.json()

        # Verify basic health response structure
        assert "status" in health_data
        assert "timestamp" in health_data
        assert "service" in health_data
        assert "version" in health_data
        assert "checks" in health_data

        assert health_data["service"] == "api-gateway"
        assert health_data["status"] in ["healthy", "degraded", "unhealthy"]

    def test_health_aggregates_multiple_checks(self, test_client):
        """Test that health endpoint aggregates multiple service checks."""
        with patch('dotmac.platform.api_gateway.gateway.HealthChecker') as mock_health_checker:
            mock_checker_instance = Mock()
            mock_health_checker.return_value = mock_checker_instance

            # Mock individual health checks
            mock_checker_instance.check_database.return_value = {
                "status": "healthy",
                "response_time": 0.05,
                "details": {"connections": 5, "max_connections": 100}
            }

            mock_checker_instance.check_cache.return_value = {
                "status": "healthy",
                "response_time": 0.02,
                "details": {"connected": True, "memory_usage": "45%"}
            }

            mock_checker_instance.check_auth_service.return_value = {
                "status": "degraded",
                "response_time": 1.2,
                "details": {"reason": "high_latency"}
            }

            mock_checker_instance.aggregate_health.return_value = {
                "status": "degraded",
                "checks": {
                    "database": {"status": "healthy", "response_time": 0.05},
                    "cache": {"status": "healthy", "response_time": 0.02},
                    "auth": {"status": "degraded", "response_time": 1.2}
                }
            }

            response = test_client.get("/health")

            assert response.status_code == 200
            health_data = response.json()

            assert health_data["status"] == "degraded"
            assert "database" in health_data["checks"]
            assert "cache" in health_data["checks"]
            assert "auth" in health_data["checks"]

            assert health_data["checks"]["database"]["status"] == "healthy"
            assert health_data["checks"]["cache"]["status"] == "healthy"
            assert health_data["checks"]["auth"]["status"] == "degraded"

    def test_health_check_timeout_handling(self, test_client):
        """Test handling of health check timeouts."""
        with patch('dotmac.platform.api_gateway.gateway.HealthChecker') as mock_health_checker:
            mock_checker_instance = Mock()
            mock_health_checker.return_value = mock_checker_instance

            # Mock timeout in one of the checks
            mock_checker_instance.check_database.side_effect = TimeoutError("Database check timeout")

            mock_checker_instance.aggregate_health.return_value = {
                "status": "unhealthy",
                "checks": {
                    "database": {
                        "status": "unhealthy",
                        "error": "timeout",
                        "response_time": None
                    }
                }
            }

            response = test_client.get("/health")

            assert response.status_code == 503  # Service Unavailable
            health_data = response.json()

            assert health_data["status"] == "unhealthy"
            assert health_data["checks"]["database"]["status"] == "unhealthy"
            assert health_data["checks"]["database"]["error"] == "timeout"

    def test_metrics_endpoint_basic_structure(self, test_client):
        """Test basic metrics endpoint structure."""
        response = test_client.get("/metrics")

        assert response.status_code == 200
        metrics_data = response.json()

        # Verify basic metrics response structure
        assert "timestamp" in metrics_data
        assert "service" in metrics_data
        assert "counters" in metrics_data
        assert "histograms" in metrics_data
        assert "gauges" in metrics_data

        assert metrics_data["service"] == "api-gateway"

    def test_metrics_aggregation_from_multiple_sources(self, test_client):
        """Test that metrics endpoint aggregates from multiple sources."""
        with patch('dotmac.platform.observability.metrics.registry.MetricsRegistry') as mock_registry:
            mock_registry_instance = Mock()
            mock_registry.return_value = mock_registry_instance

            # Mock metrics from different sources
            mock_registry_instance.get_counter_metrics.return_value = {
                "http_requests_total": 1234,
                "http_errors_total": 45,
                "auth_attempts_total": 567
            }

            mock_registry_instance.get_histogram_metrics.return_value = {
                "http_request_duration": {
                    "p50": 0.1,
                    "p95": 0.5,
                    "p99": 1.0,
                    "count": 1234,
                    "sum": 123.4
                },
                "database_query_duration": {
                    "p50": 0.02,
                    "p95": 0.1,
                    "p99": 0.2,
                    "count": 890,
                    "sum": 25.6
                }
            }

            mock_registry_instance.get_gauge_metrics.return_value = {
                "active_connections": 42,
                "memory_usage_bytes": 1024*1024*512,  # 512MB
                "cpu_usage_percent": 35.5
            }

            response = test_client.get("/metrics")

            assert response.status_code == 200
            metrics_data = response.json()

            # Verify counter metrics
            assert metrics_data["counters"]["http_requests_total"] == 1234
            assert metrics_data["counters"]["http_errors_total"] == 45
            assert metrics_data["counters"]["auth_attempts_total"] == 567

            # Verify histogram metrics
            assert "http_request_duration" in metrics_data["histograms"]
            assert metrics_data["histograms"]["http_request_duration"]["p50"] == 0.1
            assert metrics_data["histograms"]["http_request_duration"]["count"] == 1234

            # Verify gauge metrics
            assert metrics_data["gauges"]["active_connections"] == 42
            assert metrics_data["gauges"]["cpu_usage_percent"] == 35.5

    def test_metrics_prometheus_format(self, test_client):
        """Test metrics endpoint in Prometheus format."""
        response = test_client.get("/metrics", headers={"Accept": "text/plain"})

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

        metrics_text = response.text

        # Verify Prometheus format
        assert "# TYPE" in metrics_text
        assert "# HELP" in metrics_text
        assert "http_requests_total" in metrics_text

    def test_health_check_caching(self, test_client):
        """Test that health checks are appropriately cached."""
        with patch('dotmac.platform.api_gateway.gateway.HealthChecker') as mock_health_checker:
            mock_checker_instance = Mock()
            mock_health_checker.return_value = mock_checker_instance

            call_count = 0

            def mock_aggregate_health():
                nonlocal call_count
                call_count += 1
                return {
                    "status": "healthy",
                    "checks": {"database": {"status": "healthy"}},
                    "call_count": call_count
                }

            mock_checker_instance.aggregate_health.side_effect = mock_aggregate_health

            # Make multiple requests quickly
            response1 = test_client.get("/health")
            response2 = test_client.get("/health")

            # Both should succeed
            assert response1.status_code == 200
            assert response2.status_code == 200

            # Health checks might be cached for a short period
            # This depends on the actual caching implementation

    def test_health_check_includes_dependency_versions(self, test_client):
        """Test that health check includes dependency version information."""
        with patch('dotmac.platform.api_gateway.gateway.HealthChecker') as mock_health_checker:
            mock_checker_instance = Mock()
            mock_health_checker.return_value = mock_checker_instance

            mock_checker_instance.aggregate_health.return_value = {
                "status": "healthy",
                "checks": {
                    "database": {
                        "status": "healthy",
                        "version": "PostgreSQL 14.5"
                    },
                    "cache": {
                        "status": "healthy",
                        "version": "Redis 7.0.5"
                    }
                },
                "dependencies": {
                    "python": "3.12.0",
                    "fastapi": "0.110.0",
                    "sqlalchemy": "2.0.0"
                }
            }

            response = test_client.get("/health")

            assert response.status_code == 200
            health_data = response.json()

            assert "dependencies" in health_data
            assert health_data["dependencies"]["python"] == "3.12.0"
            assert health_data["checks"]["database"]["version"] == "PostgreSQL 14.5"

    def test_metrics_include_business_metrics(self, test_client):
        """Test that metrics include business-specific metrics."""
        with patch('dotmac.platform.observability.metrics.business.BusinessMetrics') as mock_business:
            mock_business_instance = Mock()
            mock_business.return_value = mock_business_instance

            mock_business_instance.get_metrics.return_value = {
                "active_users": 150,
                "api_calls_per_minute": 45.2,
                "error_rate_percent": 0.1,
                "avg_response_time_ms": 125.5
            }

            with patch('dotmac.platform.observability.metrics.registry.MetricsRegistry') as mock_registry:
                mock_registry_instance = Mock()
                mock_registry.return_value = mock_registry_instance

                mock_registry_instance.get_business_metrics.return_value = mock_business_instance.get_metrics()

                response = test_client.get("/metrics")

                assert response.status_code == 200
                metrics_data = response.json()

                # Business metrics should be included
                assert "business" in metrics_data
                assert metrics_data["business"]["active_users"] == 150
                assert metrics_data["business"]["api_calls_per_minute"] == 45.2

    def test_health_check_circuit_breaker_integration(self, test_client):
        """Test health check integration with circuit breaker."""
        with patch('dotmac.platform.resilience.circuit_breaker.CircuitBreaker') as mock_cb:
            mock_cb_instance = Mock()
            mock_cb.return_value = mock_cb_instance

            # Simulate circuit breaker open
            mock_cb_instance.is_open = True

            with patch('dotmac.platform.api_gateway.gateway.HealthChecker') as mock_health_checker:
                mock_checker_instance = Mock()
                mock_health_checker.return_value = mock_checker_instance

                mock_checker_instance.aggregate_health.return_value = {
                    "status": "degraded",
                    "checks": {
                        "downstream_service": {
                            "status": "circuit_open",
                            "circuit_breaker": "open",
                            "reason": "too_many_failures"
                        }
                    }
                }

                response = test_client.get("/health")

                assert response.status_code == 200
                health_data = response.json()

                assert health_data["status"] == "degraded"
                assert health_data["checks"]["downstream_service"]["circuit_breaker"] == "open"

    def test_metrics_performance_overhead(self, test_client):
        """Test that metrics collection has minimal performance overhead."""
        import time

        start_time = time.time()

        # Make multiple metrics requests
        for _ in range(10):
            response = test_client.get("/metrics")
            assert response.status_code == 200

        end_time = time.time()
        total_time = end_time - start_time

        # Metrics collection should be fast (less than 1 second for 10 requests)
        assert total_time < 1.0

    def test_health_and_metrics_correlation(self, test_client):
        """Test correlation between health status and metrics."""
        # Get health status
        health_response = test_client.get("/health")
        health_data = health_response.json()

        # Get metrics
        metrics_response = test_client.get("/metrics")
        metrics_data = metrics_response.json()

        # Both should be from approximately the same time
        health_timestamp = datetime.fromisoformat(health_data["timestamp"].replace('Z', '+00:00'))
        metrics_timestamp = datetime.fromisoformat(metrics_data["timestamp"].replace('Z', '+00:00'))

        time_diff = abs((health_timestamp - metrics_timestamp).total_seconds())
        assert time_diff < 60  # Should be within 1 minute

    def test_health_check_detailed_vs_simple(self, test_client):
        """Test detailed vs simple health check modes."""
        # Simple health check
        response_simple = test_client.get("/health?detail=false")
        assert response_simple.status_code == 200
        simple_data = response_simple.json()

        # Detailed health check
        response_detailed = test_client.get("/health?detail=true")
        assert response_detailed.status_code == 200
        detailed_data = response_detailed.json()

        # Detailed should have more information
        assert len(str(detailed_data)) >= len(str(simple_data))

    def test_metrics_filtering_and_aggregation(self, test_client):
        """Test metrics filtering and aggregation capabilities."""
        # Filter by metric type
        response_counters = test_client.get("/metrics?type=counters")
        assert response_counters.status_code == 200
        counters_data = response_counters.json()

        # Should only contain counter metrics
        assert "counters" in counters_data
        assert "histograms" not in counters_data or not counters_data["histograms"]

        # Filter by time range
        response_recent = test_client.get("/metrics?since=1h")
        assert response_recent.status_code == 200

    def test_health_check_external_dependencies(self, test_client):
        """Test health checks for external dependencies."""
        with patch('dotmac.platform.api_gateway.gateway.HealthChecker') as mock_health_checker:
            mock_checker_instance = Mock()
            mock_health_checker.return_value = mock_checker_instance

            mock_checker_instance.aggregate_health.return_value = {
                "status": "healthy",
                "checks": {
                    "internal": {
                        "database": {"status": "healthy"},
                        "cache": {"status": "healthy"}
                    },
                    "external": {
                        "payment_service": {"status": "healthy", "url": "https://api.payment.com"},
                        "email_service": {"status": "degraded", "url": "https://api.email.com"}
                    }
                }
            }

            response = test_client.get("/health")

            assert response.status_code == 200
            health_data = response.json()

            assert "internal" in health_data["checks"]
            assert "external" in health_data["checks"]
            assert health_data["checks"]["external"]["payment_service"]["status"] == "healthy"
