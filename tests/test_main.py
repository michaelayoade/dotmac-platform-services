"""Tests for main module."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dotmac.platform.main import (
    create_application,
    lifespan,
    app,
)


class TestCreateApplication:
    """Test create_application function."""

    def test_create_application(self):
        """Test creating FastAPI application."""
        test_app = create_application()

        assert isinstance(test_app, FastAPI)
        assert test_app.title == "DotMac Platform Services"
        assert test_app.version == "1.0.0"
        assert test_app.docs_url == "/docs"
        assert test_app.redoc_url == "/redoc"

    @patch("dotmac.platform.main.settings")
    def test_create_application_with_settings(self, mock_settings):
        """Test application uses settings."""
        mock_settings.app_name = "Test App"
        mock_settings.app_version = "2.0.0"
        mock_settings.debug = False
        mock_settings.environment = "production"

        test_app = create_application()

        # Title is hardcoded, not from settings
        assert test_app.title == "DotMac Platform Services"
        assert test_app.version == "2.0.0"
        assert test_app.debug is False



class TestLifespan:
    """Test lifespan context manager."""

    @pytest.mark.asyncio
    @patch("dotmac.platform.main.HealthChecker")
    @patch("dotmac.platform.main.load_secrets_from_vault_sync")
    @patch("dotmac.platform.main.init_db")
    @patch("dotmac.platform.main.setup_telemetry")
    @patch("dotmac.platform.main.settings")
    @patch("builtins.print")
    async def test_lifespan_startup_success(
        self,
        mock_print,
        mock_settings,
        mock_setup_telemetry,
        mock_init_db,
        mock_load_secrets,
        mock_health_checker,
    ):
        """Test lifespan startup sequence."""
        mock_settings.environment = "development"
        # Mock HealthChecker
        mock_checker_instance = MagicMock()
        mock_checker_instance.run_all_checks.return_value = (True, [])
        mock_health_checker.return_value = mock_checker_instance

        test_app = MagicMock(spec=FastAPI)

        async with lifespan(test_app) as _:
            # Verify startup sequence
            mock_health_checker.assert_called_once()
            mock_load_secrets.assert_called_once()
            mock_init_db.assert_called_once()
            mock_setup_telemetry.assert_called_once_with(test_app)

        # Verify print statements
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("DotMac Platform Services starting" in str(call) for call in print_calls)
        assert any("Database initialized" in str(call) for call in print_calls)
        assert any("Startup complete" in str(call) for call in print_calls)
        assert any("Shutting down" in str(call) for call in print_calls)

    @pytest.mark.asyncio
    @patch("dotmac.platform.main.HealthChecker")
    @patch("dotmac.platform.main.settings")
    @patch("builtins.print")
    async def test_lifespan_startup_deps_failed_production(
        self, mock_print, mock_settings, mock_health_checker
    ):
        """Test lifespan when dependencies fail in production."""
        mock_settings.environment = "production"
        # Mock HealthChecker with failed checks
        mock_checker_instance = MagicMock()
        mock_check = MagicMock()
        mock_check.name = "Database"
        mock_check.is_healthy = False
        mock_check.required = True
        mock_check.status.value = "unhealthy"
        mock_check.message = "Cannot connect"
        mock_checker_instance.run_all_checks.return_value = (False, [mock_check])
        mock_health_checker.return_value = mock_checker_instance

        test_app = MagicMock(spec=FastAPI)

        with pytest.raises(RuntimeError, match="Required services unavailable"):
            async with lifespan(test_app):
                pass

    @pytest.mark.asyncio
    @patch("dotmac.platform.main.HealthChecker")
    @patch("dotmac.platform.main.load_secrets_from_vault_sync")
    @patch("dotmac.platform.main.init_db")
    @patch("dotmac.platform.main.setup_telemetry")
    @patch("dotmac.platform.main.settings")
    @patch("builtins.print")
    async def test_lifespan_secrets_loading_error_dev(
        self, mock_print, mock_settings, mock_setup_telemetry, mock_init_db, mock_load_secrets, mock_health_checker
    ):
        """Test lifespan continues when secrets loading fails in dev."""
        mock_settings.environment = "development"
        mock_checker_instance = MagicMock()
        mock_checker_instance.run_all_checks.return_value = (True, [])
        mock_health_checker.return_value = mock_checker_instance
        mock_load_secrets.side_effect = Exception("Vault error")

        test_app = MagicMock(spec=FastAPI)

        # Should not raise in development
        async with lifespan(test_app):
            pass

        # Check warning was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Using default secrets (Vault unavailable:" in str(call) for call in print_calls)

    @pytest.mark.asyncio
    @patch("dotmac.platform.main.HealthChecker")
    @patch("dotmac.platform.main.load_secrets_from_vault_sync")
    @patch("dotmac.platform.main.settings")
    async def test_lifespan_secrets_loading_error_production(
        self, mock_settings, mock_load_secrets, mock_health_checker
    ):
        """Test lifespan raises when secrets loading fails in production."""
        mock_settings.environment = "production"
        mock_checker_instance = MagicMock()
        mock_checker_instance.run_all_checks.return_value = (True, [])
        mock_health_checker.return_value = mock_checker_instance
        mock_load_secrets.side_effect = Exception("Vault error")

        test_app = MagicMock(spec=FastAPI)

        with pytest.raises(Exception, match="Vault error"):
            async with lifespan(test_app):
                pass


class TestApplicationEndpoints:
    """Test application endpoints."""

    @patch("dotmac.platform.main.HealthChecker")
    @patch("dotmac.platform.main.load_secrets_from_vault_sync")
    @patch("dotmac.platform.main.init_db")
    @patch("dotmac.platform.main.setup_telemetry")
    def test_health_endpoint(
        self, mock_setup_telemetry, mock_init_db, mock_load_secrets, mock_health_checker
    ):
        """Test /health endpoint."""
        # Mock HealthChecker
        mock_checker_instance = MagicMock()
        mock_checker_instance.run_all_checks.return_value = (True, [])
        mock_health_checker.return_value = mock_checker_instance

        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "environment" in data
            assert "version" in data

    @patch("dotmac.platform.main.HealthChecker")
    @patch("dotmac.platform.main.load_secrets_from_vault_sync")
    @patch("dotmac.platform.main.init_db")
    @patch("dotmac.platform.main.setup_telemetry")
    def test_ready_endpoint_success(
        self, mock_setup_telemetry, mock_init_db, mock_load_secrets, mock_health_checker
    ):
        """Test /ready endpoint when all services are healthy."""
        # Mock HealthChecker for both lifespan and endpoint
        mock_checker_instance = MagicMock()
        mock_checker_instance.run_all_checks.return_value = (True, [])
        mock_checker_instance.get_summary.return_value = {
            "healthy": True,
            "total_services": 5,
            "healthy_services": 5,
            "services": {"Database": "healthy", "Redis": "healthy"},
            "failed_services": [],
        }
        mock_health_checker.return_value = mock_checker_instance

        with TestClient(app) as client:
            response = client.get("/ready")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"
            assert data["healthy"] is True

    @patch("dotmac.platform.main.HealthChecker")
    @patch("dotmac.platform.main.load_secrets_from_vault_sync")
    @patch("dotmac.platform.main.init_db")
    @patch("dotmac.platform.main.setup_telemetry")
    def test_ready_endpoint_not_ready(
        self, mock_setup_telemetry, mock_init_db, mock_load_secrets, mock_health_checker
    ):
        """Test /ready endpoint when services are unhealthy."""
        # Mock HealthChecker for both lifespan and endpoint
        mock_checker_instance = MagicMock()
        mock_checker_instance.run_all_checks.return_value = (True, [])  # For lifespan
        mock_checker_instance.get_summary.return_value = {
            "healthy": False,
            "total_services": 5,
            "healthy_services": 3,
            "services": {"Database": "unhealthy", "Redis": "healthy"},
            "failed_services": ["Database"],
        }
        mock_health_checker.return_value = mock_checker_instance

        with TestClient(app) as client:
            response = client.get("/ready")
            # The endpoint returns 200 even when not ready
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "not ready"
            assert data["healthy"] is False

    @patch("dotmac.platform.main.HealthChecker")
    @patch("dotmac.platform.main.load_secrets_from_vault_sync")
    @patch("dotmac.platform.main.init_db")
    @patch("dotmac.platform.main.setup_telemetry")
    def test_metrics_endpoint(
        self, mock_setup_telemetry, mock_init_db, mock_load_secrets, mock_health_checker
    ):
        """Test /metrics endpoint."""
        # Mock HealthChecker
        mock_checker_instance = MagicMock()
        mock_checker_instance.run_all_checks.return_value = (True, [])
        mock_health_checker.return_value = mock_checker_instance

        with TestClient(app) as client:
            response = client.get("/metrics")
            assert response.status_code == 200

            # Should return Prometheus-formatted metrics
            assert "text/plain" in response.headers["content-type"]
            assert "charset=utf-8" in response.headers["content-type"]
            content = response.text
            assert "# HELP" in content or "# TYPE" in content or len(content) == 0



class TestAppInstance:
    """Test the app instance."""

    def test_app_is_fastapi_instance(self):
        """Test that app is a FastAPI instance."""
        assert isinstance(app, FastAPI)

    def test_app_has_lifespan(self):
        """Test that app has lifespan configured."""
        # The lifespan should be set
        assert app.router.lifespan_context is not None
