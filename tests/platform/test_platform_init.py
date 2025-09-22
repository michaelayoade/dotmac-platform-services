"""
Unit tests for dotmac.platform package exports and initialization.
"""

import pytest


@pytest.mark.unit
def test_platform_config_env_loading(monkeypatch):
    from dotmac.platform import PlatformConfig

    monkeypatch.setenv("DOTMAC_JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("DOTMAC_SERVICE_NAME", "svc")
    cfg = settings.Platform.model_copy()

    assert cfg.get("auth.jwt_algorithm") == "HS256"
    assert cfg.get("observability.service_name") == "svc"
    assert cfg.get("no.such.key", "default") == "default"


@pytest.mark.unit
def test_registry_register_get_service():
    from dotmac.platform import (
        get_available_services,
        get_service,
        is_service_available,
        register_service,
    )

    register_service("x", object())
    assert is_service_available("x") is True
    assert get_service("x") is not None
    assert "x" in get_available_services()


@pytest.mark.unit
def test_initialize_platform_services_auto_discover(monkeypatch):
    from dotmac.platform import get_initialized_services, initialize_platform_services

    # Provide minimal configs to initialize auth and observability
    initialize_platform_services(
        auth_config={"jwt_secret_key": "s", "jwt_algorithm": "HS256"},
        observability_config={"service_name": "svc"},
        secrets_config={},
        auto_discover=True,
    )

    inited = get_initialized_services()
    # At least observability should initialize; auth may initialize with given config
    assert "observability" in inited


@pytest.mark.unit
def test_create_observability_manager():
    from dotmac.platform import create_observability_manager

    mgr = create_observability_manager(service_name="svc", environment="test")
    assert mgr is not None
