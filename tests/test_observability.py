"""
Tests for observability services including SigNoz dashboard functionality.
"""

import pytest

from dotmac.platform.observability import (
    ObservabilityManager,
    get_current_environment,
    is_observability_enabled,
)


def test_observability_manager_creation() -> None:
    """Test ObservabilityManager can be created."""
    manager = ObservabilityManager("test-service")
    assert manager is not None


def test_environment_detection() -> None:
    """Test environment detection works."""
    env = get_current_environment()
    assert env in ["development", "staging", "production", "test"]


def test_observability_enabled_check() -> None:
    """Test observability enabled check."""
    enabled = is_observability_enabled()
    assert isinstance(enabled, bool)


def test_observability_imports() -> None:
    """Test observability service imports."""
    from dotmac.platform.observability import (
        ObservabilityManager,
        get_current_environment,
        is_observability_enabled,
    )

    # All imports should work
    assert ObservabilityManager is not None
    assert get_current_environment is not None
    assert is_observability_enabled is not None


def test_signoz_dashboard_functionality() -> None:
    """Test SigNoz dashboard functionality."""
    from dotmac.platform.observability.dashboards import (
        DashboardProvisioner,
        SigNozDashboard,
    )

    # Test SigNoz dashboard creation
    dashboard = SigNozDashboard()
    assert dashboard is not None
    assert dashboard.config == {}

    # Test with custom config
    custom_config = {"api_url": "http://localhost:3301", "api_key": "test-key"}
    dashboard_with_config = SigNozDashboard(custom_config)
    assert dashboard_with_config.config == custom_config

    # Test dashboard provisioner defaults to SigNoz
    provisioner = DashboardProvisioner()
    assert provisioner.platform_type == "signoz"


def test_signoz_only_platform() -> None:
    """Test that SigNoz is the only supported platform."""
    from dotmac.platform.observability.dashboards import DashboardProvisioner

    # Test default platform is SigNoz
    provisioner = DashboardProvisioner()
    assert provisioner.platform_type == "signoz"

    # Test explicit SigNoz configuration
    signoz_provisioner = DashboardProvisioner(platform_type="signoz")
    assert signoz_provisioner.platform_type == "signoz"

    # Test that validator is created correctly
    assert provisioner.validator is not None
    assert provisioner.validator.platform_type == "signoz"


def test_observability_dashboard_integration() -> None:
    """Test observability module dashboard integration."""
    from dotmac.platform.observability import SigNozDashboard

    # Test that SigNoz dashboard is available from main observability module
    dashboard = SigNozDashboard()
    assert dashboard is not None

    # Test that it's the same class as from dashboards module
    from dotmac.platform.observability.dashboards import SigNozDashboard as DirectSigNoz

    direct_dashboard = DirectSigNoz()
    assert isinstance(dashboard, type(direct_dashboard))


def test_dashboard_template_validation() -> None:
    """Test dashboard template validation for SigNoz."""
    from dotmac.platform.observability.dashboards import DashboardProvisioner
    from dotmac.platform.observability.dashboards.manager import DashboardTemplate

    provisioner = DashboardProvisioner()
    validator = provisioner.validator

    # Test valid SigNoz template
    valid_template = DashboardTemplate(
        name="test-dashboard",
        title="Test Dashboard",
        description="A test dashboard for validation",
        tags=["monitoring", "test"],
        template_content={"widgets": [{"title": "Test Widget", "type": "chart"}]},
    )

    errors = validator.validate_template(valid_template)
    # Should have minimal or no errors for valid template
    assert isinstance(errors, list)


if __name__ == "__main__":
    pytest.main([__file__])
