"""
Unit tests for `dotmac.platform.observability.integration`.

We stub the minimal `dotmac.application.config` types expected by the module
so that we can import and exercise helpers without a real application package.
"""

import sys
from types import ModuleType

import pytest


@pytest.fixture(autouse=True)
def stub_application_config_module(monkeypatch):
    """Provide a stub for dotmac.application.config used by the module under test."""
    # Create stub modules
    app_mod = ModuleType("dotmac.application")
    cfg_mod = ModuleType("dotmac.application.config")

    # Minimal DeploymentMode enum replacement
    class DeploymentMode:
        TENANT_CONTAINER = "tenant_container"
        SINGLE_TENANT = "single_tenant"

    # Minimal PlatformConfig replacement
    class _Ctx:
        def __init__(self, mode, tenant_id=None):
            self.mode = mode
            self.tenant_id = tenant_id

    class PlatformConfig:
        def __init__(self, platform_name: str, deployment_context=None):
            self.platform_name = platform_name
            self.deployment_context = deployment_context

    cfg_mod.DeploymentMode = DeploymentMode
    cfg_mod.PlatformConfig = PlatformConfig

    # Inject into sys.modules under the real names the module imports
    sys.modules.setdefault("dotmac.application", app_mod)
    sys.modules["dotmac.application.config"] = cfg_mod

    yield

    # Cleanup not strictly necessary in test process


def _import_integration():
    # Import after stubbing
    from dotmac.platform.observability import integration as integ

    return integ


@pytest.mark.unit
def test_select_exporters_per_environment():
    integ = _import_integration()
    assert integ._select_exporters("development") == (["console"], ["console"])
    assert integ._select_exporters("staging") == (["otlp", "console"], ["otlp"])
    assert integ._select_exporters("production") == (["otlp"], ["otlp"])


@pytest.mark.unit
def test_get_service_name_modes():
    integ = _import_integration()
    # Build stub types from the injected module
    from dotmac.application.config import DeploymentMode, PlatformConfig

    # no deployment context
    cfg = PlatformConfig(platform_name="svc")
    assert integ._get_service_name(cfg) == "svc"

    # tenant container mode appends tenant id
    ctx = type("Ctx", (), {"mode": DeploymentMode.TENANT_CONTAINER, "tenant_id": "t-123"})()
    cfg2 = PlatformConfig(platform_name="svc", deployment_context=ctx)
    assert integ._get_service_name(cfg2) == "svc-t-123"

    # other mode keeps name
    ctx3 = type("Ctx", (), {"mode": "single_tenant"})()
    cfg3 = PlatformConfig(platform_name="svc", deployment_context=ctx3)
    assert integ._get_service_name(cfg3) == "svc"


@pytest.mark.unit
def test_get_resource_attributes_includes_environment(monkeypatch):
    integ = _import_integration()
    from dotmac.application.config import PlatformConfig

    monkeypatch.setenv("ENVIRONMENT", "staging")
    cfg = PlatformConfig("svc")
    attrs = integ._get_resource_attributes(cfg)
    assert attrs["service.namespace"] == "dotmac"
    assert attrs["deployment.environment"] == "staging"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_setup_observability_minimal_app(monkeypatch):
    """Exercise the happy-path of setup with minimal environment.

    We verify the function returns a mapping and populates app.state keys.
    """
    # Ensure deterministic env
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("APP_VERSION", "0.1.0")
    monkeypatch.setenv("JWT_SECRET", "dev-secret")
    monkeypatch.delenv("SERVICE_SIGNING_SECRET", raising=False)

    integ = _import_integration()
    from dotmac.application.config import PlatformConfig
    from fastapi import FastAPI

    app = FastAPI()
    cfg = PlatformConfig(platform_name="obs-svc")

    components = await integ.setup_observability(app, cfg)
    # Basic shape
    for key in [
        "otel_bootstrap",
        "metrics_registry",
        "tenant_metrics",
        "service_token_manager",
        "tenant_resolver",
        "edge_validator",
        "environment",
        "service_name",
        "service_version",
    ]:
        assert key in components
        # Stored on app.state
        assert hasattr(app.state, key)

    assert components["environment"] == "development"
    assert components["service_name"] == "obs-svc"
    assert components["service_version"] == "0.1.0"
