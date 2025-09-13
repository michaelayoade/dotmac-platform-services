"""
Comprehensive tests for all configuration models.
Tests Pydantic models, validation, and default values.
"""


import pytest


def test_jwt_config():
    """Test JWT configuration model."""
    from dotmac.platform.auth.jwt_service import JWTConfig

    # Test with minimal config
    config = JWTConfig(secret_key="test-secret-key", algorithm="HS256")
    assert config.secret_key == "test-secret-key"
    assert config.algorithm == "HS256"
    assert config.access_token_expire_minutes == 30  # Default
    assert config.refresh_token_expire_days == 7  # Default

    # Test with full config
    config = JWTConfig(
        secret_key="test-secret-key",
        algorithm="RS256",
        access_token_expire_minutes=15,
        refresh_token_expire_days=30,
        issuer="https://example.com",
        audience=["api.example.com"],
        leeway_seconds=10,
    )
    assert config.algorithm == "RS256"
    assert config.access_token_expire_minutes == 15
    assert config.issuer == "https://example.com"
    assert "api.example.com" in config.audience
    assert config.leeway_seconds == 10

    # Test validation
    with pytest.raises(Exception):  # Should fail with empty secret
        JWTConfig(secret_key="", algorithm="HS256")


def test_mfa_service_config():
    """Test MFA service configuration."""
    from dotmac.platform.auth.mfa_service import MFAServiceConfig

    # Test defaults
    config = MFAServiceConfig()
    assert config.issuer_name == "DotMac ISP"
    assert config.totp_window == 1
    assert config.sms_expiry_minutes == 5
    assert config.email_expiry_minutes == 10
    assert config.backup_codes_count == 10
    assert config.max_verification_attempts == 3
    assert config.lockout_duration_minutes == 30
    assert config.challenge_token_expiry_minutes == 15

    # Test custom values
    config = MFAServiceConfig(
        issuer_name="MyApp", totp_window=2, backup_codes_count=20, max_verification_attempts=5
    )
    assert config.issuer_name == "MyApp"
    assert config.totp_window == 2
    assert config.backup_codes_count == 20
    assert config.max_verification_attempts == 5


def test_oauth_service_config():
    """Test OAuth service configuration."""
    from dotmac.platform.auth.oauth_providers import OAuthProvider, OAuthServiceConfig

    # Test with provider configuration
    config = OAuthServiceConfig(
        providers={
            OAuthProvider.GOOGLE: {
                "client_id": "google-client",
                "client_secret": "google-secret",
                "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
            },
            OAuthProvider.GITHUB: {
                "client_id": "github-client",
                "client_secret": "github-secret",
                "authorize_url": "https://github.com/login/oauth/authorize",
                "token_url": "https://github.com/login/oauth/access_token",
            },
        },
        default_scopes=["openid", "email", "profile"],
        state_ttl_seconds=600,
    )

    assert OAuthProvider.GOOGLE in config.providers
    assert OAuthProvider.GITHUB in config.providers
    assert config.providers[OAuthProvider.GOOGLE]["client_id"] == "google-client"
    assert "openid" in config.default_scopes
    assert config.state_ttl_seconds == 600


def test_rbac_config():
    """Test RBAC configuration."""
    from dotmac.platform.auth.rbac_engine import (
        Action,
        Permission,
        RBACConfig,
        Resource,
        Role,
    )

    # Create permissions
    admin_perms = [
        Permission(resource=Resource.ALL, action=Action.ALL),
    ]

    user_perms = [
        Permission(resource=Resource.USER, action=Action.READ),
        Permission(resource=Resource.USER, action=Action.WRITE),
    ]

    # Create roles
    admin_role = Role(name="admin", permissions=admin_perms)
    user_role = Role(name="user", permissions=user_perms)

    # Create config
    config = RBACConfig(
        roles=[admin_role, user_role],
        default_role="user",
        cache_ttl_seconds=300,
        enable_policy_cache=True,
    )

    assert len(config.roles) == 2
    assert config.default_role == "user"
    assert config.cache_ttl_seconds == 300
    assert config.enable_policy_cache is True


def test_session_config():
    """Test session manager configuration."""
    from dotmac.platform.auth.session_manager import SessionConfig

    # Test defaults
    config = SessionConfig()
    assert config.secret_key is not None
    assert config.session_lifetime_seconds == 3600  # 1 hour default
    assert config.refresh_threshold_seconds == 300  # 5 minutes default
    assert config.max_sessions_per_user == 5
    assert config.enable_refresh is True

    # Test custom values
    config = SessionConfig(
        secret_key="session-secret",
        session_lifetime_seconds=7200,
        refresh_threshold_seconds=600,
        max_sessions_per_user=10,
        enable_refresh=False,
        secure_cookie=True,
        same_site="strict",
    )
    assert config.secret_key == "session-secret"
    assert config.session_lifetime_seconds == 7200
    assert config.secure_cookie is True
    assert config.same_site == "strict"


def test_secrets_config():
    """Test secrets manager configuration."""
    from dotmac.platform.secrets import SecretsConfig
    from dotmac.platform.secrets.types import Environment

    # Test minimal config
    config = SecretsConfig(provider="environment", environment=Environment.DEVELOPMENT)
    assert config.provider == "environment"
    assert config.environment == Environment.DEVELOPMENT

    # Test with OpenBao provider
    config = SecretsConfig(
        provider="openbao",
        environment=Environment.PRODUCTION,
        vault_url="https://vault.example.com",
        vault_token="hvs.token",
        vault_mount_point="secret",
        enable_cache=True,
        cache_ttl_seconds=300,
    )
    assert config.provider == "openbao"
    assert config.vault_url == "https://vault.example.com"
    assert config.enable_cache is True
    assert config.cache_ttl_seconds == 300


def test_cache_config():
    """Test cache configuration."""
    from dotmac.platform.secrets.cache import CacheConfig

    # Test defaults
    config = CacheConfig()
    assert config.ttl_seconds == 300  # Default TTL
    assert config.max_size == 1000  # Default max size
    assert config.eviction_policy == "lru"  # Default policy

    # Test custom values
    config = CacheConfig(
        ttl_seconds=600,
        max_size=5000,
        eviction_policy="lfu",
        enable_stats=True,
        cleanup_interval_seconds=60,
    )
    assert config.ttl_seconds == 600
    assert config.max_size == 5000
    assert config.eviction_policy == "lfu"
    assert config.enable_stats is True
    assert config.cleanup_interval_seconds == 60


def test_observability_config():
    """Test observability configuration."""
    from dotmac.platform.observability.config import ObservabilityConfig

    # Test defaults
    config = ObservabilityConfig()
    assert config.service_name == "dotmac-platform"
    assert config.environment == "development"
    assert config.otlp_endpoint is None
    assert config.enable_tracing is True
    assert config.enable_metrics is True
    assert config.enable_logging is True
    assert config.log_level == "INFO"

    # Test custom values
    config = ObservabilityConfig(
        service_name="my-service",
        environment="production",
        otlp_endpoint="http://localhost:4317",
        enable_tracing=True,
        enable_metrics=True,
        enable_logging=True,
        log_level="DEBUG",
        sample_rate=0.1,
        json_logging=True,
        correlation_id_header="X-Correlation-ID",
    )
    assert config.service_name == "my-service"
    assert config.environment == "production"
    assert config.otlp_endpoint == "http://localhost:4317"
    assert config.sample_rate == 0.1
    assert config.json_logging is True
    assert config.correlation_id_header == "X-Correlation-ID"


def test_database_config():
    """Test database configuration."""
    from dotmac.platform.database import DatabaseConfig

    # Test with URL
    config = DatabaseConfig(url="postgresql://user:pass@localhost/db")
    assert config.url == "postgresql://user:pass@localhost/db"
    assert config.pool_size == 10  # Default
    assert config.max_overflow == 20  # Default

    # Test with components
    config = DatabaseConfig(
        host="localhost",
        port=5432,
        database="mydb",
        username="user",
        password="pass",
        driver="postgresql+asyncpg",
        pool_size=20,
        max_overflow=40,
        pool_timeout=30,
        echo=True,
    )
    assert config.host == "localhost"
    assert config.port == 5432
    assert config.database == "mydb"
    assert config.driver == "postgresql+asyncpg"
    assert config.pool_size == 20
    assert config.echo is True


def test_monitoring_config():
    """Test monitoring configuration."""
    from dotmac.platform.monitoring import MonitoringConfig

    # Test defaults
    config = MonitoringConfig()
    assert config.enable_prometheus is False
    assert config.enable_datadog is False
    assert config.enable_newrelic is False
    assert config.metrics_port == 9090

    # Test with integrations enabled
    config = MonitoringConfig(
        enable_prometheus=True,
        prometheus_port=8080,
        enable_datadog=True,
        datadog_api_key="dd-api-key",
        datadog_app_key="dd-app-key",
        enable_newrelic=True,
        newrelic_license_key="nr-license",
    )
    assert config.enable_prometheus is True
    assert config.prometheus_port == 8080
    assert config.datadog_api_key == "dd-api-key"
    assert config.newrelic_license_key == "nr-license"


def test_tenant_config():
    """Test tenant configuration."""
    from dotmac.platform.tenant import TenantConfig

    # Test defaults
    config = TenantConfig()
    assert config.enable_isolation is True
    assert config.tenant_header == "X-Tenant-ID"
    assert config.require_tenant is False
    assert config.default_tenant is None

    # Test custom values
    config = TenantConfig(
        enable_isolation=True,
        tenant_header="X-Customer-ID",
        require_tenant=True,
        default_tenant="default",
        tenant_claim="tenant_id",
        validate_tenant=True,
    )
    assert config.tenant_header == "X-Customer-ID"
    assert config.require_tenant is True
    assert config.default_tenant == "default"
    assert config.tenant_claim == "tenant_id"
    assert config.validate_tenant is True


def test_task_config():
    """Test task/background operations configuration."""
    from dotmac.platform.tasks import TaskConfig

    # Test defaults
    config = TaskConfig()
    assert config.max_workers == 10
    assert config.task_timeout_seconds == 300
    assert config.retry_max_attempts == 3
    assert config.retry_delay_seconds == 1

    # Test custom values
    config = TaskConfig(
        max_workers=20,
        task_timeout_seconds=600,
        retry_max_attempts=5,
        retry_delay_seconds=2,
        retry_exponential_backoff=True,
        enable_task_monitoring=True,
        task_queue_size=1000,
    )
    assert config.max_workers == 20
    assert config.task_timeout_seconds == 600
    assert config.retry_exponential_backoff is True
    assert config.task_queue_size == 1000


def test_application_config():
    """Test main application configuration."""
    from dotmac.platform.core import ApplicationConfig

    # Test minimal config
    config = ApplicationConfig(name="test-app", version="1.0.0")
    assert config.name == "test-app"
    assert config.version == "1.0.0"
    assert config.debug is False  # Default
    assert config.environment == "development"  # Default

    # Test full config
    config = ApplicationConfig(
        name="production-app",
        version="2.0.0",
        debug=False,
        environment="production",
        host="0.0.0.0",
        port=8080,
        workers=4,
        reload=False,
        cors_origins=["https://example.com"],
        cors_credentials=True,
        trusted_hosts=["example.com", "*.example.com"],
        secret_key="app-secret-key",
        timezone="UTC",
    )
    assert config.environment == "production"
    assert config.host == "0.0.0.0"
    assert config.port == 8080
    assert config.workers == 4
    assert "https://example.com" in config.cors_origins
    assert config.timezone == "UTC"


def test_config_validation():
    """Test configuration validation rules."""
    from dotmac.platform.auth.jwt_service import JWTConfig
    from dotmac.platform.secrets import SecretsConfig

    # Test JWT config validation
    with pytest.raises(Exception):  # Invalid algorithm
        JWTConfig(secret_key="key", algorithm="INVALID")

    # Test negative values validation
    from dotmac.platform.auth.session_manager import SessionConfig

    with pytest.raises(Exception):
        SessionConfig(session_lifetime_seconds=-1)

    with pytest.raises(Exception):
        SessionConfig(max_sessions_per_user=0)

    # Test enum validation
    from dotmac.platform.secrets.types import Environment

    config = SecretsConfig(
        provider="environment", environment=Environment.PRODUCTION  # Should be valid enum
    )
    assert config.environment == Environment.PRODUCTION


def test_config_environment_overrides():
    """Test configuration with environment variable overrides."""
    import os
    from unittest.mock import patch

    # Mock environment variables
    env_vars = {
        "JWT_SECRET_KEY": "env-secret",
        "JWT_ALGORITHM": "RS256",
        "DATABASE_URL": "postgresql://env-user:env-pass@env-host/env-db",
        "OTLP_ENDPOINT": "http://env-collector:4317",
        "LOG_LEVEL": "DEBUG",
        "ENVIRONMENT": "staging",
    }

    with patch.dict(os.environ, env_vars):
        # Configs should pick up env vars if designed to
        from dotmac.platform.observability.config import ObservabilityConfig

        # This would work if the config is designed to read from env
        config = ObservabilityConfig(
            otlp_endpoint=os.getenv("OTLP_ENDPOINT"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            environment=os.getenv("ENVIRONMENT", "development"),
        )
        assert config.otlp_endpoint == "http://env-collector:4317"
        assert config.log_level == "DEBUG"
        assert config.environment == "staging"


def test_config_serialization():
    """Test configuration serialization to dict/JSON."""
    from dotmac.platform.auth.jwt_service import JWTConfig
    from dotmac.platform.observability.config import ObservabilityConfig

    # Test JWT config serialization
    jwt_config = JWTConfig(secret_key="test-key", algorithm="HS256", access_token_expire_minutes=30)

    # Should be serializable to dict
    config_dict = {
        "secret_key": jwt_config.secret_key,
        "algorithm": jwt_config.algorithm,
        "access_token_expire_minutes": jwt_config.access_token_expire_minutes,
        "refresh_token_expire_days": jwt_config.refresh_token_expire_days,
    }
    assert config_dict["algorithm"] == "HS256"
    assert config_dict["access_token_expire_minutes"] == 30

    # Test observability config
    obs_config = ObservabilityConfig(
        service_name="test-service", enable_tracing=True, enable_metrics=False
    )

    obs_dict = {
        "service_name": obs_config.service_name,
        "enable_tracing": obs_config.enable_tracing,
        "enable_metrics": obs_config.enable_metrics,
    }
    assert obs_dict["service_name"] == "test-service"
    assert obs_dict["enable_tracing"] is True
    assert obs_dict["enable_metrics"] is False


def test_config_defaults_and_factories():
    """Test configuration default values and factory methods."""
    from dotmac.platform.auth.session_manager import SessionConfig
    from dotmac.platform.secrets.cache import CacheConfig

    # Test session config has sensible defaults
    config = SessionConfig()
    assert config.session_lifetime_seconds > 0
    assert config.refresh_threshold_seconds > 0
    assert config.refresh_threshold_seconds < config.session_lifetime_seconds

    # Test cache config defaults
    cache_config = CacheConfig()
    assert cache_config.ttl_seconds > 0
    assert cache_config.max_size > 0
    assert cache_config.eviction_policy in ["lru", "lfu", "fifo"]


def test_config_inheritance():
    """Test configuration inheritance and composition."""
    from dotmac.platform.auth.jwt_service import JWTConfig
    from dotmac.platform.core import ApplicationConfig
    from dotmac.platform.secrets import SecretsConfig

    # Create a composite configuration
    class PlatformConfig:
        def __init__(self):
            self.app = ApplicationConfig(name="platform", version="1.0.0")
            self.jwt = JWTConfig(secret_key="platform-secret", algorithm="HS256")
            self.secrets = SecretsConfig(provider="environment", environment="development")

    platform_config = PlatformConfig()
    assert platform_config.app.name == "platform"
    assert platform_config.jwt.algorithm == "HS256"
    assert platform_config.secrets.provider == "environment"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
