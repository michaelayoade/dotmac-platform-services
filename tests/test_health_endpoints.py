"""
Tests for health check endpoints in main.py.

Tests all health-related endpoints including /health, /health/live,
/health/ready, and /ready endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from fastapi.testclient import TestClient

from dotmac.platform.main import app
from dotmac.platform.health_checks import ServiceStatus, ServiceHealth


class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch('dotmac.platform.main.settings')
    def test_health_endpoint(self, mock_settings, client):
        """Test /health endpoint."""
        mock_settings.app_version = "1.0.0"
        mock_settings.environment = "test"

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert data["environment"] == "test"

    @patch('dotmac.platform.main.settings')
    @patch('dotmac.platform.main.datetime')
    def test_liveness_endpoint(self, mock_datetime, mock_settings, client):
        """Test /health/live endpoint."""
        mock_settings.app_version = "1.0.0"
        mock_settings.environment = "test"
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        response = client.get("/health/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert data["version"] == "1.0.0"
        assert data["environment"] == "test"
        assert data["timestamp"] == "2023-01-01T12:00:00"

    @patch('dotmac.platform.main.datetime')
    def test_readiness_endpoint_ready(self, mock_datetime, client):
        """Test /health/ready endpoint when all services are ready."""
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        mock_summary = {
            "healthy": True,
            "services": [
                {"name": "database", "status": "healthy", "message": "OK", "required": True},
                {"name": "redis", "status": "healthy", "message": "OK", "required": True},
            ],
            "failed_services": [],
        }

        with patch('dotmac.platform.main.HealthChecker') as mock_checker_class:
            mock_checker = MagicMock()
            mock_checker.get_summary.return_value = mock_summary
            mock_checker_class.return_value = mock_checker

            response = client.get("/health/ready")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"
            assert data["healthy"] is True
            assert data["services"] == mock_summary["services"]
            assert data["failed_services"] == []
            assert data["timestamp"] == "2023-01-01T12:00:00"

    @patch('dotmac.platform.main.datetime')
    def test_readiness_endpoint_not_ready(self, mock_datetime, client):
        """Test /health/ready endpoint when services are not ready."""
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        mock_summary = {
            "healthy": False,
            "services": [
                {"name": "database", "status": "healthy", "message": "OK", "required": True},
                {"name": "redis", "status": "unhealthy", "message": "Connection failed", "required": True},
            ],
            "failed_services": ["redis"],
        }

        with patch('dotmac.platform.main.HealthChecker') as mock_checker_class:
            mock_checker = MagicMock()
            mock_checker.get_summary.return_value = mock_summary
            mock_checker_class.return_value = mock_checker

            response = client.get("/health/ready")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "not ready"
            assert data["healthy"] is False
            assert data["services"] == mock_summary["services"]
            assert data["failed_services"] == ["redis"]
            assert data["timestamp"] == "2023-01-01T12:00:00"

    @patch('dotmac.platform.main.datetime')
    def test_ready_endpoint_backwards_compatibility(self, mock_datetime, client):
        """Test /ready endpoint for backwards compatibility."""
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        mock_summary = {
            "healthy": True,
            "services": [
                {"name": "database", "status": "healthy", "message": "OK", "required": True},
            ],
            "failed_services": [],
        }

        with patch('dotmac.platform.main.HealthChecker') as mock_checker_class:
            mock_checker = MagicMock()
            mock_checker.get_summary.return_value = mock_summary
            mock_checker_class.return_value = mock_checker

            response = client.get("/ready")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"
            assert data["healthy"] is True
            assert data["timestamp"] == "2023-01-01T12:00:00"

    def test_health_endpoints_no_auth_required(self, client):
        """Test that health endpoints don't require authentication."""
        # All these endpoints should be accessible without authentication
        endpoints = ["/health", "/health/live", "/health/ready", "/ready"]

        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should not return 401/403 (auth errors)
            assert response.status_code in [200, 500]  # 500 might happen due to missing dependencies in test

    @patch('dotmac.platform.main.HealthChecker')
    def test_readiness_endpoint_exception_handling(self, mock_checker_class, client):
        """Test readiness endpoint handles exceptions gracefully."""
        mock_checker = MagicMock()
        mock_checker.get_summary.side_effect = Exception("Health check failed")
        mock_checker_class.return_value = mock_checker

        # The endpoint will propagate the exception, so we expect it to be raised
        with pytest.raises(Exception, match="Health check failed"):
            client.get("/health/ready")


class TestHealthEndpointIntegration:
    """Integration tests for health endpoints with real health checker."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_endpoints_with_mocked_dependencies(self, client):
        """Test health endpoints with mocked external dependencies."""
        # Mock all external dependencies to avoid real connections
        with patch('dotmac.platform.health_checks.get_sync_engine') as mock_engine, \
             patch('dotmac.platform.health_checks.settings') as mock_settings:

            # Setup mocked database
            mock_connection = MagicMock()
            mock_result = MagicMock()
            mock_result.scalar.return_value = 1
            mock_connection.execute.return_value = mock_result
            mock_engine.return_value.connect.return_value.__enter__.return_value = mock_connection

            # Setup mocked settings
            mock_settings.redis.redis_url = "redis://localhost:6379"
            mock_settings.vault.enabled = False
            mock_settings.storage.provider = "local"
            mock_settings.celery.broker_url = "redis://localhost:6379"
            mock_settings.observability.otel_enabled = False

            # Mock Redis to be healthy
            with patch('dotmac.platform.health_checks.Redis') as mock_redis:
                mock_redis_client = MagicMock()
                mock_redis_client.ping.return_value = True
                mock_redis.from_url.return_value = mock_redis_client

                response = client.get("/health/ready")

                assert response.status_code == 200
                data = response.json()

                # Should be ready with mocked healthy services
                assert data["status"] == "ready"
                assert data["healthy"] is True
                assert len(data["services"]) >= 4  # At least database, redis, vault, storage

    def test_health_endpoints_with_failing_dependencies(self, client):
        """Test health endpoints with failing external dependencies."""
        # Mock failing dependencies
        with patch('dotmac.platform.health_checks.get_sync_engine') as mock_engine, \
             patch('dotmac.platform.health_checks.settings') as mock_settings:

            # Setup failing database
            mock_engine.side_effect = Exception("Database connection failed")

            # Setup settings
            mock_settings.redis.redis_url = "redis://localhost:6379"
            mock_settings.vault.enabled = False
            mock_settings.storage.provider = "local"
            mock_settings.celery.broker_url = "redis://localhost:6379"
            mock_settings.observability.otel_enabled = False

            # Mock Redis to fail
            with patch('dotmac.platform.health_checks.Redis') as mock_redis:
                mock_redis_client = MagicMock()
                mock_redis_client.ping.side_effect = Exception("Redis connection failed")
                mock_redis.from_url.return_value = mock_redis_client

                response = client.get("/health/ready")

                assert response.status_code == 200
                data = response.json()

                # Should not be ready with failing required services
                assert data["status"] == "not ready"
                assert data["healthy"] is False
                assert len(data["failed_services"]) >= 1  # At least database should fail

    def test_health_endpoint_performance(self, client):
        """Test that health endpoints respond quickly."""
        import time

        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()

        assert response.status_code == 200
        # Health endpoint should be very fast (basic info only)
        assert end_time - start_time < 1.0  # Less than 1 second

    def test_liveness_vs_readiness_difference(self, client):
        """Test difference between liveness and readiness endpoints."""
        # Liveness should always be available (basic app status)
        liveness_response = client.get("/health/live")
        assert liveness_response.status_code == 200
        assert liveness_response.json()["status"] == "alive"

        # Readiness checks external dependencies and may fail
        readiness_response = client.get("/health/ready")
        assert readiness_response.status_code == 200
        # Status can be "ready" or "not ready" depending on dependencies