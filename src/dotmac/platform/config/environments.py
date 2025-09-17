"""
Environment-specific configurations for DotMac Business Services.

Provides pre-configured settings for different deployment environments.
"""


import os
from functools import lru_cache
from typing import Optional

from .base import (

    APIGatewayConfig,
    BaseConfig,
    CacheConfig,
    DatabaseConfig,
    LoggingConfig,
    ObservabilityConfig,
    RedisConfig,
    SecurityConfig,
    WorkflowConfig,
)
from dotmac.platform.observability.unified_logging import get_logger

from .secure import get_config_manager

logger = get_logger(__name__)

class DevelopmentConfig(BaseConfig):
    """Development environment configuration."""

    def __init__(self, **kwargs):
        """Initialize development configuration."""
        # Development defaults
        defaults = {
            "environment": "development",
            "debug": True,
            "host": "localhost",
            "port": 8000,
            "workers": 1,
        }
        defaults.update(kwargs)

        # Initialize base config
        super().__init__(**defaults)

        # Development-specific settings
        self.logging = LoggingConfig(
            level="DEBUG",
            format="console",
            include_caller=True,
        )

        self.cache = CacheConfig(
            backend="memory",
            max_entries=100,
        )

        self.security = SecurityConfig(
            secret_key="development-secret-key-do-not-use-in-production" + "x" * 20,
            jwt_expiration_minutes=60,
            max_login_attempts=10,
        )

        self.database = DatabaseConfig(
            url=os.getenv("DATABASE_URL", "sqlite:///./dev.db"),
            echo=True,
            pool_size=5,
        )

        self.redis = RedisConfig(
            url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            pool_size=5,
        )

        self.observability = ObservabilityConfig(
            enabled=True,
            environment="development",
            metrics_enabled=True,
            tracing_enabled=False,
            trace_sample_rate=1.0,
        )

        self.api_gateway = APIGatewayConfig(
            rate_limit_enabled=False,
            circuit_breaker_enabled=False,
            request_timeout=60,
        )

        self.workflow = WorkflowConfig(
            engine="simple",
            default_timeout=300,
            max_retries=1,
        )

class TestingConfig(BaseConfig):
    """Testing environment configuration."""

    def __init__(self, **kwargs):
        """Initialize testing configuration."""
        # Testing defaults
        defaults = {
            "environment": "testing",
            "debug": True,
            "host": "127.0.0.1",
            "port": 8001,
            "workers": 1,
        }
        defaults.update(kwargs)

        # Initialize base config
        super().__init__(**defaults)

        # Testing-specific settings
        self.logging = LoggingConfig(
            level="WARNING",
            format="console",
        )

        self.cache = CacheConfig(
            backend="memory",
            max_entries=50,
        )

        self.security = SecurityConfig(
            secret_key="testing-secret-key-for-unit-tests-only" + "x" * 25,
            jwt_expiration_minutes=5,
            max_login_attempts=3,
        )

        self.database = DatabaseConfig(
            url="sqlite:///:memory:",
            echo=False,
            pool_size=1,
        )

        self.redis = None  # Disable Redis for testing

        self.observability = ObservabilityConfig(
            enabled=False,
        )

        self.api_gateway = APIGatewayConfig(
            rate_limit_enabled=False,
            circuit_breaker_enabled=False,
        )

        self.workflow = WorkflowConfig(
            engine="simple",
            default_timeout=10,
            max_retries=0,
        )

        # Disable all features by default for testing
        self.features = {feature: False for feature in self.features.keys()}

class StagingConfig(BaseConfig):
    """Staging environment configuration."""

    def __init__(self, **kwargs):
        """Initialize staging configuration."""
        # Staging defaults
        defaults = {
            "environment": "staging",
            "debug": False,
            "host": "0.0.0.0",
            "port": 8000,
            "workers": 2,
        }
        defaults.update(kwargs)

        # Initialize base config
        super().__init__(**defaults)

        # Get secure config manager
        config_manager = get_config_manager()

        # Staging-specific settings
        self.logging = LoggingConfig(
            level="INFO",
            format="json",
            include_timestamp=True,
            log_file="/var/log/dotmac/business-services.log",
        )

        self.cache = CacheConfig(
            backend="redis",
            url=config_manager.get_secret_sync(
                "redis/staging/url",
                env_fallback="STAGING_REDIS_URL",
                default="redis://localhost:6379/1",
            ),
            default_timeout=600,
        )

        self.security = SecurityConfig(
            secret_key=config_manager.get_secret_sync(
                "security/staging/secret_key", env_fallback="STAGING_SECRET_KEY", required=True
            ),
            jwt_expiration_minutes=30,
            enable_mfa=True,
        )

        self.database = DatabaseConfig(
            url=config_manager.get_secret_sync(
                "database/staging/url", env_fallback="STAGING_DATABASE_URL", required=True
            ),
            echo=False,
            pool_size=20,
            max_overflow=10,
        )

        self.redis = RedisConfig(
            url=config_manager.get_secret_sync(
                "redis/staging/url", env_fallback="STAGING_REDIS_URL", required=True
            ),
            pool_size=20,
        )

        self.observability = ObservabilityConfig(
            enabled=True,
            environment="staging",
            metrics_enabled=True,
            tracing_enabled=True,
            trace_sample_rate=0.5,
            signoz_enabled=True,
            signoz_endpoint=os.getenv("STAGING_SIGNOZ_ENDPOINT"),
        )

        self.api_gateway = APIGatewayConfig(
            rate_limit_enabled=True,
            rate_limit_requests=500,
            rate_limit_window=60,
            circuit_breaker_enabled=True,
            circuit_breaker_failure_threshold=10,
            circuit_breaker_recovery_timeout=30,
        )

        self.workflow = WorkflowConfig(
            engine="temporal",
            temporal_host=os.getenv("STAGING_TEMPORAL_HOST", "staging-temporal:7233"),
            temporal_namespace="staging",
            temporal_worker_count=2,
        )

class ProductionConfig(BaseConfig):
    """Production environment configuration."""

    def __init__(self, **kwargs):
        """Initialize production configuration."""
        # Production defaults
        defaults = {
            "environment": "production",
            "debug": False,
            "host": "0.0.0.0",
            "port": 8000,
            "workers": 4,
        }
        defaults.update(kwargs)

        # Initialize base config
        super().__init__(**defaults)

        # Get secure config manager
        config_manager = get_config_manager()

        # Production-specific settings
        self.logging = LoggingConfig(
            level="WARNING",
            format="json",
            include_timestamp=True,
            log_file="/var/log/dotmac/business-services.log",
            max_bytes=52428800,  # 50MB
            backup_count=10,
        )

        self.cache = CacheConfig(
            backend="redis",
            url=config_manager.get_secret_sync(
                "redis/production/url", env_fallback="REDIS_URL", required=True
            ),
            default_timeout=3600,
            max_entries=10000,
        )

        self.security = SecurityConfig(
            secret_key=config_manager.get_secret_sync(
                "security/production/secret_key", env_fallback="SECRET_KEY", required=True
            ),
            jwt_expiration_minutes=15,
            refresh_token_expiration_days=30,
            password_min_length=12,
            max_login_attempts=3,
            lockout_duration_minutes=30,
            enable_mfa=True,
        )

        self.database = DatabaseConfig(
            url=config_manager.get_secret_sync(
                "database/production/url", env_fallback="DATABASE_URL", required=True
            ),
            echo=False,
            pool_size=50,
            max_overflow=20,
            connect_timeout=10,
            command_timeout=30,
            enable_row_level_security=True,
        )

        self.redis = RedisConfig(
            url=config_manager.get_secret_sync(
                "redis/production/url", env_fallback="REDIS_URL", required=True
            ),
            pool_size=50,
            max_connections=100,
            health_check_interval=30,
        )

        self.observability = ObservabilityConfig(
            enabled=True,
            environment="production",
            service_name="dotmac-business-services",
            metrics_enabled=True,
            tracing_enabled=True,
            trace_sample_rate=0.01,  # 1% sampling in production
            signoz_enabled=True,
            signoz_endpoint=config_manager.get_secret_sync(
                "observability/signoz/endpoint", env_fallback="SIGNOZ_ENDPOINT", required=True
            ),
            signoz_access_token=config_manager.get_secret_sync(
                "observability/signoz/token", env_fallback="SIGNOZ_ACCESS_TOKEN", required=True
            ),
            custom_tags={
                "region": os.getenv("AWS_REGION", "us-east-1"),
                "deployment": os.getenv("DEPLOYMENT_ID", "main"),
            },
        )

        self.api_gateway = APIGatewayConfig(
            rate_limit_enabled=True,
            rate_limit_requests=1000,
            rate_limit_window=60,
            circuit_breaker_enabled=True,
            circuit_breaker_failure_threshold=5,
            circuit_breaker_recovery_timeout=60,
            max_request_size=52428800,  # 50MB
            request_timeout=30,
            service_discovery_enabled=True,
            service_registry_url=os.getenv("SERVICE_REGISTRY_URL"),
            versioning_enabled=True,
            supported_versions=["v1", "v2"],
        )

        self.workflow = WorkflowConfig(
            engine="temporal",
            temporal_host=config_manager.get_secret_sync(
                "temporal/production/host", env_fallback="TEMPORAL_HOST", default="temporal:7233"
            ),
            temporal_namespace="production",
            temporal_task_queue="business-services-production",
            temporal_worker_count=8,
            default_timeout=7200,
            max_retries=5,
            retry_backoff=2.0,
            enable_saga=True,
        )

        # Production features
        self.multi_tenancy_enabled = True
        self.tenant_isolation_level = "row"

@lru_cache
def get_config(environment: Optional[str] = None) -> BaseConfig:
    """
    Get configuration for the specified environment.

    Args:
        environment: Environment name (development, testing, staging, production)
                    If not provided, uses ENVIRONMENT env var or defaults to development

    Returns:
        Configuration instance for the environment

    Raises:
        ValueError: If environment is not recognized
    """
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development").lower()

    config_map = {
        "development": DevelopmentConfig,
        "dev": DevelopmentConfig,
        "testing": TestingConfig,
        "test": TestingConfig,
        "staging": StagingConfig,
        "stage": StagingConfig,
        "production": ProductionConfig,
        "prod": ProductionConfig,
    }

    config_class = config_map.get(environment)
    if not config_class:
        raise ValueError(
            f"Unknown environment: {environment}. " f"Must be one of: {list(config_map.keys())}"
        )

    logger.info(f"Loading configuration for environment: {environment}")
    return config_class()

# Create a singleton config instance
_current_config: Optional[BaseConfig] = None

def get_current_config() -> BaseConfig:
    """
    Get the current active configuration.

    Returns:
        Current configuration instance
    """
    global _current_config
    if _current_config is None:
        _current_config = get_config()
    return _current_config

def set_current_config(config: BaseConfig) -> None:
    """
    Set the current active configuration.

    Args:
        config: Configuration instance to set as current
    """
    global _current_config
    _current_config = config
    logger.info(f"Configuration set for environment: {config.environment}")
