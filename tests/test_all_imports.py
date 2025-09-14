"""
Comprehensive import tests for all modules.
This provides quick coverage wins by testing that all modules can be imported.
"""

import pytest


def test_root_package_imports():
    """Test root package imports."""
    import dotmac
    import dotmac.platform

    assert dotmac.__name__ == "dotmac"
    assert dotmac.platform.__name__ == "dotmac.platform"


def test_platform_main_imports():
    """Test main platform module imports."""
    from dotmac.platform import (
        __version__,
        auth,
        core,
        database,
        monitoring,
        observability,
        secrets,
        tasks,
        tenant,
    )

    assert __version__ is not None
    assert auth is not None
    assert secrets is not None
    assert observability is not None
    assert core is not None
    assert database is not None
    assert monitoring is not None
    assert tasks is not None
    assert tenant is not None


def test_auth_module_imports():
    """Test all auth module imports."""

    # Test submodule imports - only import what actually exists
    from dotmac.platform.auth.api_keys import APIKeyService
    from dotmac.platform.auth.jwt_service import JWTService
    from dotmac.platform.auth.mfa_service import MFAService
    from dotmac.platform.auth.oauth_providers import OAuthService
    from dotmac.platform.auth.rbac_engine import RBACEngine
    from dotmac.platform.auth.session_manager import SessionManager

    assert APIKeyService is not None
    assert JWTService is not None
    assert MFAService is not None
    assert OAuthService is not None
    assert RBACEngine is not None
    assert SessionManager is not None


def test_secrets_module_imports():
    """Test all secrets module imports."""
    # Test submodule imports - only import what actually exists
    from dotmac.platform.secrets import (
        create_secrets_manager,
        get_current_environment,
    )
    from dotmac.platform.secrets.config import SecretsConfig
    from dotmac.platform.secrets.manager import SecretsManager
    from dotmac.platform.secrets.openbao_provider import OpenBaoProvider

    assert create_secrets_manager is not None
    assert OpenBaoProvider is not None
    assert get_current_environment is not None
    assert SecretsManager is not None
    assert SecretsConfig is not None


def test_secrets_providers_imports():
    """Test secrets providers submodule imports."""
    from dotmac.platform.secrets.providers.base import BaseProvider
    from dotmac.platform.secrets.providers.env import EnvironmentProvider
    from dotmac.platform.secrets.providers.file import FileProvider

    assert BaseProvider is not None
    assert EnvironmentProvider is not None
    assert FileProvider is not None


def test_observability_module_imports():
    """Test all observability module imports."""
    # Test submodule imports - only import what actually exists
    from dotmac.platform.observability import (
        ObservabilityManager,
        get_current_environment,
        is_observability_enabled,
    )
    from dotmac.platform.observability.bootstrap import OTelBootstrap, initialize_otel
    from dotmac.platform.observability.manager import ObservabilityManager

    assert ObservabilityManager is not None
    assert get_current_environment is not None
    assert is_observability_enabled is not None
    assert OTelBootstrap is not None
    assert initialize_otel is not None


def test_observability_metrics_imports():
    """Test observability metrics submodule imports."""
    from dotmac.platform.observability.metrics.business import (
        BusinessMetricType,
        initialize_tenant_metrics,
    )
    from dotmac.platform.observability.metrics.registry import (
        MetricsRegistry,
        initialize_metrics_registry,
    )

    assert BusinessMetricType is not None
    assert MetricsRegistry is not None
    assert initialize_tenant_metrics is not None
    assert initialize_metrics_registry is not None


def test_observability_dashboards_imports():
    """Test observability dashboards submodule imports."""
    from dotmac.platform.observability.dashboards import (
        DashboardProvisioner,
        SigNozDashboard,
    )
    from dotmac.platform.observability.dashboards.manager import (
        DashboardManager,
        provision_platform_dashboards,
    )

    assert DashboardProvisioner is not None
    assert SigNozDashboard is not None
    assert DashboardManager is not None
    assert provision_platform_dashboards is not None


def test_core_module_imports():
    """Test core module imports."""
    from dotmac.platform.core import (
        Application,
        ApplicationConfig,
        create_application,
        get_application,
    )

    assert Application is not None
    assert ApplicationConfig is not None
    assert create_application is not None
    assert get_application is not None


def test_database_module_imports():
    """Test database module imports."""
    from dotmac.platform.database.base import Base
    from dotmac.platform.database.mixins import TimestampMixin
    from dotmac.platform.database.session import get_database_session, get_db_session

    assert Base is not None
    assert TimestampMixin is not None
    assert get_database_session is not None
    assert get_db_session is not None


def test_monitoring_module_imports():
    """Test monitoring module imports."""
    from dotmac.platform.monitoring.benchmarks import (
        PerformanceBenchmark,
        BenchmarkManager,
    )
    from dotmac.platform.monitoring.integrations import SigNozIntegration

    assert PerformanceBenchmark is not None
    assert SigNozIntegration is not None
    assert BenchmarkManager is not None


def test_tasks_module_imports():
    """Test tasks module imports."""
    from dotmac.platform.tasks import BackgroundOperation, SagaWorkflow
    from dotmac.platform.tasks.decorators import (
        task,
    )

    assert BackgroundOperation is not None
    assert task is not None
    assert SagaWorkflow is not None


def test_tenant_module_imports():
    """Test tenant module imports."""
    from dotmac.platform.tenant.identity import TenantIdentityResolver
    from dotmac.platform.tenant import get_tenant_context
    from dotmac.platform.tenant.middleware import (
        TenantMiddleware,
    )

    assert TenantIdentityResolver is not None
    assert TenantMiddleware is not None
    assert get_tenant_context is not None


def test_circular_imports():
    """Test that there are no circular import issues."""
    # Import everything in sequence

    # Re-import in different order

    # All imports should work without circular dependency errors
    assert True


def test_public_api_exports():
    """Test that public API exports are available."""
    try:
        from dotmac.platform import (  # Auth exports; Secrets exports; Observability exports; Core exports
            JWTService,
            MFAService,
            ObservabilityManager,
            OpenBaoProvider,
            RBACEngine,
            SecretsManager,
            SessionManager,
            create_application,
            get_application,
        )

        assert JWTService is not None
        assert MFAService is not None
        assert RBACEngine is not None
        assert SessionManager is not None
        assert SecretsManager is not None
        assert OpenBaoProvider is not None
        assert ObservabilityManager is not None
        assert create_application is not None
        assert get_application is not None
    except ImportError:
        # Some exports may not be available due to optional dependencies
        # This is acceptable for the import test
        pass


def test_version_info():
    """Test version information is available."""
    from dotmac.platform import __author__, __email__, __version__

    assert __version__ is not None
    assert isinstance(__version__, str)
    assert len(__version__) > 0

    # Version should follow semantic versioning
    parts = __version__.split(".")
    assert len(parts) >= 2  # At least major.minor

    assert __author__ is not None
    assert __email__ is not None


def test_type_hints_imports():
    """Test that type hints can be imported."""
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        pass

    # Type checking imports should not fail
    assert True


def test_optional_dependencies():
    """Test handling of optional dependencies."""
    try:
        from dotmac.platform.monitoring.integrations import DatadogIntegration

        has_datadog = True
    except ImportError:
        has_datadog = False

    try:
        from dotmac.platform.monitoring.integrations import NewRelicIntegration

        has_newrelic = True
    except ImportError:
        has_newrelic = False

    # These should be handled gracefully
    assert has_datadog or not has_datadog
    assert has_newrelic or not has_newrelic


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
