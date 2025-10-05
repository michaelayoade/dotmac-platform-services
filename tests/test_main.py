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
    @pytest.mark.asyncio
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
    @pytest.mark.asyncio
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
    @pytest.mark.asyncio
    async def test_lifespan_secrets_loading_error_dev(
        self,
        mock_print,
        mock_settings,
        mock_setup_telemetry,
        mock_init_db,
        mock_load_secrets,
        mock_health_checker,
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
    @pytest.mark.asyncio
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


class TestMissingCoverage:
    """Tests to cover missing lines and branches."""

    def test_rate_limit_handler(self):
        """Test rate limit handler function."""
        from dotmac.platform.main import rate_limit_handler
        from fastapi import Request

        # Create mock request and mock exception
        request = MagicMock(spec=Request)
        exc = MagicMock()  # Mock exception instead of creating real RateLimitExceeded

        # Mock the _rate_limit_exceeded_handler to return a response
        with patch("dotmac.platform.main._rate_limit_exceeded_handler") as mock_handler:
            mock_response = MagicMock()
            mock_handler.return_value = mock_response

            # Call rate limit handler - should not raise
            result = rate_limit_handler(request, exc)

            # Should return a response (the _rate_limit_exceeded_handler return value)
            assert result is mock_response
            mock_handler.assert_called_once_with(request, exc)

    @pytest.mark.asyncio
    @patch("dotmac.platform.main.HealthChecker")
    @patch("dotmac.platform.main.load_secrets_from_vault_sync")
    @patch("dotmac.platform.main.init_db")
    @patch("dotmac.platform.main.setup_telemetry")
    @patch("dotmac.platform.main.settings")
    @patch("builtins.print")
    @pytest.mark.asyncio
    async def test_lifespan_degraded_startup_dev(
        self,
        mock_print,
        mock_settings,
        mock_setup_telemetry,
        mock_init_db,
        mock_load_secrets,
        mock_health_checker,
    ):
        """Test lifespan with optional services failed in dev (line 86)."""
        mock_settings.environment = "development"

        # Mock health checker with optional services failed
        mock_checker_instance = MagicMock()
        mock_optional_check = MagicMock()
        mock_optional_check.name = "Redis"
        mock_optional_check.is_healthy = False
        mock_optional_check.required = False
        mock_optional_check.status.value = "unhealthy"
        mock_optional_check.message = "Connection failed"

        mock_checker_instance.run_all_checks.return_value = (False, [mock_optional_check])
        mock_health_checker.return_value = mock_checker_instance

        test_app = MagicMock(spec=FastAPI)

        # Should not raise in development with optional services failed
        async with lifespan(test_app):
            pass

        # Verify warning was logged (line 86 coverage)
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Optional services unavailable: Redis" in str(call) for call in print_calls)

    @pytest.mark.asyncio
    @patch("dotmac.platform.main.HealthChecker")
    @patch("dotmac.platform.main.load_secrets_from_vault_sync")
    @patch("dotmac.platform.main.init_db")
    @patch("dotmac.platform.main.setup_telemetry")
    @patch("dotmac.platform.main.settings")
    @patch("builtins.print")
    @pytest.mark.asyncio
    async def test_lifespan_database_init_failure(
        self,
        mock_print,
        mock_settings,
        mock_setup_telemetry,
        mock_init_db,
        mock_load_secrets,
        mock_health_checker,
    ):
        """Test lifespan when database init fails (lines 109-111)."""
        mock_settings.environment = "development"

        # Mock health checker success
        mock_checker_instance = MagicMock()
        mock_checker_instance.run_all_checks.return_value = (True, [])
        mock_health_checker.return_value = mock_checker_instance

        # Mock database init failure
        mock_init_db.side_effect = Exception("Database connection failed")

        test_app = MagicMock(spec=FastAPI)

        # Should not raise in development, just log the error
        async with lifespan(test_app):
            pass

        # Verify print was called with error message
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Database initialization failed" in str(call) for call in print_calls)

    @patch("dotmac.platform.main.register_routers")
    @patch("dotmac.platform.main.get_limiter")
    @patch("dotmac.platform.main.settings")
    def test_create_application_cors_enabled(
        self, mock_settings, mock_get_limiter, mock_register_routers
    ):
        """Test application creation with CORS enabled (line 141->152)."""
        # Enable CORS in settings
        mock_settings.app_version = "1.0.0"
        mock_settings.environment = "development"
        mock_settings.cors.enabled = True
        mock_settings.cors.origins = ["*"]
        mock_settings.cors.credentials = True
        mock_settings.cors.methods = ["*"]
        mock_settings.cors.headers = ["*"]
        mock_settings.cors.max_age = 600
        mock_settings.observability.enable_metrics = False

        # Mock the rate limiter
        mock_get_limiter.return_value = MagicMock()

        test_app = create_application()

        # Should have CORS middleware - check for it in any middleware
        # Check the middleware.cls directly, not type(middleware.cls)
        has_cors = any(
            "cors" in str(middleware.cls).lower() for middleware in test_app.user_middleware
        )
        assert has_cors

    @patch("dotmac.platform.main.settings")
    def test_create_application_metrics_enabled(self, mock_settings):
        """Test application creation with metrics enabled (lines 210->216)."""
        mock_settings.app_version = "1.0.0"
        mock_settings.environment = "development"
        mock_settings.cors.enabled = False
        mock_settings.observability.enable_metrics = True

        with patch("prometheus_client.make_asgi_app") as mock_make_asgi:
            mock_make_asgi.return_value = MagicMock()

            test_app = create_application()

            # Should have mounted metrics endpoint
            mock_make_asgi.assert_called_once()

    @patch("dotmac.platform.main.HealthChecker")
    @patch("dotmac.platform.main.load_secrets_from_vault_sync")
    @patch("dotmac.platform.main.init_db")
    @patch("dotmac.platform.main.setup_telemetry")
    def test_liveness_endpoint(
        self, mock_setup_telemetry, mock_init_db, mock_load_secrets, mock_health_checker
    ):
        """Test /health/live endpoint (line 175)."""
        # Mock HealthChecker
        mock_checker_instance = MagicMock()
        mock_checker_instance.run_all_checks.return_value = (True, [])
        mock_health_checker.return_value = mock_checker_instance

        with TestClient(app) as client:
            response = client.get("/health/live")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "alive"
            assert "timestamp" in data

    @patch("dotmac.platform.main.HealthChecker")
    @patch("dotmac.platform.main.load_secrets_from_vault_sync")
    @patch("dotmac.platform.main.init_db")
    @patch("dotmac.platform.main.setup_telemetry")
    def test_api_info_endpoint(
        self, mock_setup_telemetry, mock_init_db, mock_load_secrets, mock_health_checker
    ):
        """Test /api endpoint (line 207)."""
        # Mock HealthChecker
        mock_checker_instance = MagicMock()
        mock_checker_instance.run_all_checks.return_value = (True, [])
        mock_health_checker.return_value = mock_checker_instance

        with TestClient(app) as client:
            response = client.get("/api")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)

    @patch("dotmac.platform.main.HealthChecker")
    @patch("dotmac.platform.main.load_secrets_from_vault_sync")
    @patch("dotmac.platform.main.init_db")
    @patch("dotmac.platform.main.setup_telemetry")
    def test_readiness_endpoint_health_ready(
        self, mock_setup_telemetry, mock_init_db, mock_load_secrets, mock_health_checker
    ):
        """Test /health/ready endpoint."""
        # Mock HealthChecker for both lifespan and endpoint
        mock_checker_instance = MagicMock()
        mock_checker_instance.run_all_checks.return_value = (True, [])
        mock_checker_instance.get_summary.return_value = {
            "healthy": True,
            "services": {"Database": "healthy"},
            "failed_services": [],
        }
        mock_health_checker.return_value = mock_checker_instance

        with TestClient(app) as client:
            response = client.get("/health/ready")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"
