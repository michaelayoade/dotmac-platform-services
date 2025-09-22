"""
Comprehensive tests for the main platform __init__.py module.
Targets the 29.59% coverage gap in platform/__init__.py
"""

import os
from unittest.mock import Mock, patch

import pytest


def test_version_info():
    """Test version information exports."""
    from dotmac.platform import __author__, __email__, __version__, get_version

    assert __version__ == "1.0.0"
    assert __author__ == "DotMac Team"
    assert __email__ == "dev@dotmac.com"

    # Test version function
    version = get_version()
    assert version == "1.0.0"
    assert version == __version__


def test_service_registry():
    """Test service registry functionality."""
    from dotmac.platform import (
        _services_registry,
        get_available_services,
        get_service,
        is_service_available,
        register_service,
    )

    # Clear registry for clean test
    _services_registry.clear()

    # Test empty registry
    assert get_available_services() == []
    assert not is_service_available("test_service")
    assert get_service("test_service") is None

    # Test service registration
    test_service = Mock()
    test_service.name = "test_service"

    register_service("test_service", test_service)

    # Test service retrieval
    assert is_service_available("test_service")
    retrieved = get_service("test_service")
    assert retrieved is test_service
    assert retrieved.name == "test_service"

    # Test available services
    services = get_available_services()
    assert "test_service" in services
    assert len(services) == 1

    # Test multiple services
    another_service = Mock()
    register_service("another_service", another_service)

    services = get_available_services()
    assert len(services) == 2
    assert "test_service" in services
    assert "another_service" in services

    # Clean up
    _services_registry.clear()


def test_platform_config_initialization():
    """Test PlatformConfig initialization and environment loading."""
    from dotmac.platform import PlatformConfig

    # Test with clean environment
    with patch.dict(os.environ, {}, clear=True):
        config = settings.Platform.model_copy()

        # Test default values
        assert config._config["auth"]["jwt_algorithm"] == "HS256"
        assert config._config["auth"]["access_token_expire_minutes"] == 15
        assert config._config["auth"]["refresh_token_expire_days"] == 30
        assert config._config["auth"]["session_backend"] == "memory"
        assert config._config["auth"]["redis_url"] == "redis://localhost:6379"

        assert config._config["secrets"]["vault_mount_point"] == "secret"
        assert config._config["secrets"]["auto_rotation"] is False

        assert config._config["observability"]["service_name"] == "dotmac-service"
        assert config._config["observability"]["log_level"] == "INFO"
        assert config._config["observability"]["correlation_id_header"] == "X-Correlation-ID"
        assert config._config["observability"]["tracing_enabled"] is True
        assert config._config["observability"]["metrics_enabled"] is True


def test_platform_config_environment_override():
    """Test PlatformConfig with environment variable overrides."""
    from dotmac.platform import PlatformConfig

    env_vars = {
        "DOTMAC_JWT_SECRET_KEY": "env-secret-key",
        "DOTMAC_JWT_ALGORITHM": "RS256",
        "DOTMAC_JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "60",
        "DOTMAC_JWT_REFRESH_TOKEN_EXPIRE_DAYS": "7",
        "DOTMAC_SESSION_BACKEND": "redis",
        "DOTMAC_REDIS_URL": "redis://redis.example.com:6379",
        "DOTMAC_VAULT_URL": "https://vault.example.com",
        "DOTMAC_VAULT_TOKEN": "hvs.token123",
        "DOTMAC_VAULT_MOUNT_POINT": "kv",
        "DOTMAC_ENCRYPTION_KEY": "encryption-key-123",
        "DOTMAC_SECRETS_AUTO_ROTATION": "true",
        "DOTMAC_SERVICE_NAME": "my-service",
        "DOTMAC_OTLP_ENDPOINT": "http://jaeger:14268",
        "DOTMAC_LOG_LEVEL": "DEBUG",
        "DOTMAC_CORRELATION_ID_HEADER": "X-Request-ID",
        "DOTMAC_TRACING_ENABLED": "false",
        "DOTMAC_METRICS_ENABLED": "false",
    }

    with patch.dict(os.environ, env_vars):
        config = settings.Platform.model_copy()

        # Test auth config overrides
        assert config._config["auth"]["jwt_secret_key"] == "env-secret-key"
        assert config._config["auth"]["jwt_algorithm"] == "RS256"
        assert config._config["auth"]["access_token_expire_minutes"] == 60
        assert config._config["auth"]["refresh_token_expire_days"] == 7
        assert config._config["auth"]["session_backend"] == "redis"
        assert config._config["auth"]["redis_url"] == "redis://redis.example.com:6379"

        # Test secrets config overrides
        assert config._config["secrets"]["vault_url"] == "https://vault.example.com"
        assert config._config["secrets"]["vault_token"] == "hvs.token123"
        assert config._config["secrets"]["vault_mount_point"] == "kv"
        assert config._config["secrets"]["encryption_key"] == "encryption-key-123"
        assert config._config["secrets"]["auto_rotation"] is True

        # Test observability config overrides
        assert config._config["observability"]["service_name"] == "my-service"
        assert config._config["observability"]["otlp_endpoint"] == "http://jaeger:14268"
        assert config._config["observability"]["log_level"] == "DEBUG"
        assert config._config["observability"]["correlation_id_header"] == "X-Request-ID"
        assert config._config["observability"]["tracing_enabled"] is False
        assert config._config["observability"]["metrics_enabled"] is False


def test_platform_config_access_methods():
    """Test PlatformConfig access methods."""
    from dotmac.platform import PlatformConfig

    config = settings.Platform.model_copy()

    # Test direct config access
    assert "auth" in config._config
    assert "secrets" in config._config
    assert "observability" in config._config

    # Test nested access
    auth_config = config._config["auth"]
    assert "jwt_algorithm" in auth_config
    assert "jwt_secret_key" in auth_config

    secrets_config = config._config["secrets"]
    assert "vault_url" in secrets_config
    assert "auto_rotation" in secrets_config

    obs_config = config._config["observability"]
    assert "service_name" in obs_config
    assert "tracing_enabled" in obs_config


def test_platform_config_boolean_parsing():
    """Test boolean environment variable parsing."""
    from dotmac.platform import PlatformConfig

    # Test various boolean representations
    test_cases = [
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("false", False),
        ("False", False),
        ("FALSE", False),
        ("1", False),  # Only "true" should be True
        ("0", False),
        ("yes", False),  # Only "true" should be True
        ("no", False),
    ]

    for env_value, expected in test_cases:
        env_vars = {
            "DOTMAC_SECRETS_AUTO_ROTATION": env_value,
            "DOTMAC_TRACING_ENABLED": env_value,
            "DOTMAC_METRICS_ENABLED": env_value,
        }

        with patch.dict(os.environ, env_vars):
            config = settings.Platform.model_copy()

            assert config._config["secrets"]["auto_rotation"] is expected
            assert config._config["observability"]["tracing_enabled"] is expected
            assert config._config["observability"]["metrics_enabled"] is expected


def test_platform_config_integer_parsing():
    """Test integer environment variable parsing."""
    from dotmac.platform import PlatformConfig

    env_vars = {
        "DOTMAC_JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "120",
        "DOTMAC_JWT_REFRESH_TOKEN_EXPIRE_DAYS": "14",
    }

    with patch.dict(os.environ, env_vars):
        config = settings.Platform.model_copy()

        assert config._config["auth"]["access_token_expire_minutes"] == 120
        assert config._config["auth"]["refresh_token_expire_days"] == 14
        assert isinstance(config._config["auth"]["access_token_expire_minutes"], int)
        assert isinstance(config._config["auth"]["refresh_token_expire_days"], int)


def test_platform_config_invalid_integers():
    """Test handling of invalid integer environment variables."""
    from dotmac.platform import PlatformConfig

    env_vars = {
        "DOTMAC_JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "invalid",
        "DOTMAC_JWT_REFRESH_TOKEN_EXPIRE_DAYS": "not_a_number",
    }

    with patch.dict(os.environ, env_vars):
        # Should handle invalid integers gracefully (likely with defaults or errors)
        try:
            config = settings.Platform.model_copy()
            # If it doesn't raise an error, check that it has some sensible value
            assert isinstance(config._config["auth"]["access_token_expire_minutes"], int)
            assert isinstance(config._config["auth"]["refresh_token_expire_days"], int)
        except ValueError:
            # It's also acceptable to raise a ValueError for invalid integers
            pass


def test_service_lifecycle():
    """Test service lifecycle management."""
    from dotmac.platform import (
        _initialized_services,
        _services_registry,
        get_service,
        is_service_available,
        register_service,
    )

    # Clear registries
    _services_registry.clear()
    _initialized_services.clear()

    # Test service registration and initialization tracking
    service_mock = Mock()
    service_mock.initialize = Mock()
    service_mock.shutdown = Mock()

    register_service("lifecycle_service", service_mock)

    # Test service is registered but not initialized
    assert is_service_available("lifecycle_service")
    assert "lifecycle_service" not in _initialized_services

    # Simulate service initialization
    _initialized_services.add("lifecycle_service")
    assert "lifecycle_service" in _initialized_services

    # Test service retrieval after initialization
    retrieved = get_service("lifecycle_service")
    assert retrieved is service_mock

    # Clean up
    _services_registry.clear()
    _initialized_services.clear()


def test_platform_config_partial_environment():
    """Test PlatformConfig with partial environment configuration."""
    from dotmac.platform import PlatformConfig

    # Set only some environment variables
    env_vars = {
        "DOTMAC_JWT_SECRET_KEY": "partial-secret",
        "DOTMAC_VAULT_URL": "https://partial-vault.com",
        "DOTMAC_LOG_LEVEL": "ERROR",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        config = settings.Platform.model_copy()

        # Overridden values
        assert config._config["auth"]["jwt_secret_key"] == "partial-secret"
        assert config._config["secrets"]["vault_url"] == "https://partial-vault.com"
        assert config._config["observability"]["log_level"] == "ERROR"

        # Default values for non-overridden settings
        assert config._config["auth"]["jwt_algorithm"] == "HS256"
        assert config._config["secrets"]["vault_mount_point"] == "secret"
        assert config._config["observability"]["service_name"] == "dotmac-service"


def test_service_registry_edge_cases():
    """Test service registry edge cases."""
    from dotmac.platform import (
        _services_registry,
        get_available_services,
        get_service,
        is_service_available,
        register_service,
    )

    # Clear registry
    _services_registry.clear()

    # Test None service registration
    register_service("none_service", None)
    assert is_service_available("none_service")
    assert get_service("none_service") is None

    # Test overwriting service
    service1 = Mock(name="service1")
    service2 = Mock(name="service2")

    register_service("overwrite_test", service1)
    assert get_service("overwrite_test") is service1

    register_service("overwrite_test", service2)
    assert get_service("overwrite_test") is service2

    # Test empty string service name
    empty_service = Mock()
    register_service("", empty_service)
    assert is_service_available("")
    assert get_service("") is empty_service
    assert "" in get_available_services()

    # Clean up
    _services_registry.clear()


def test_config_immutability():
    """Test that config can be modified after initialization."""
    from dotmac.platform import PlatformConfig

    config = settings.Platform.model_copy()

    # Test that config dict can be modified (it's not frozen)
    original_log_level = config._config["observability"]["log_level"]
    config._config["observability"]["log_level"] = "CRITICAL"

    assert config._config["observability"]["log_level"] == "CRITICAL"
    assert config._config["observability"]["log_level"] != original_log_level


def test_config_structure_completeness():
    """Test that all expected config sections exist."""
    from dotmac.platform import PlatformConfig

    config = settings.Platform.model_copy()

    # Test all major sections exist
    assert "auth" in config._config
    assert "secrets" in config._config
    assert "observability" in config._config

    # Test auth section completeness
    auth_keys = [
        "jwt_secret_key",
        "jwt_algorithm",
        "access_token_expire_minutes",
        "refresh_token_expire_days",
        "session_backend",
        "redis_url",
    ]
    for key in auth_keys:
        assert key in config._config["auth"], f"Missing auth config key: {key}"

    # Test secrets section completeness
    secrets_keys = [
        "vault_url",
        "vault_token",
        "vault_mount_point",
        "encryption_key",
        "auto_rotation",
    ]
    for key in secrets_keys:
        assert key in config._config["secrets"], f"Missing secrets config key: {key}"

    # Test observability section completeness
    obs_keys = [
        "service_name",
        "otlp_endpoint",
        "log_level",
        "correlation_id_header",
        "tracing_enabled",
        "metrics_enabled",
    ]
    for key in obs_keys:
        assert key in config._config["observability"], f"Missing observability config key: {key}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
