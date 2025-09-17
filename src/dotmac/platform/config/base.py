"""
Base configuration classes for DotMac Business Services.

Provides validated configuration models using Pydantic v2.
"""


from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from dotmac.platform.observability.unified_logging import get_logger
from dotmac.platform.licensing.config import LicensingConfig
logger = get_logger(__name__)

class CacheConfig(BaseModel):
    """Cache configuration."""

    backend: str = Field(default="memory", pattern=r"^(memory|redis)$")
    url: Optional[str] = Field(default=None)
    default_timeout: int = Field(default=300, ge=1)
    max_entries: int = Field(default=1000, ge=1)
    key_prefix: str = Field(default="business:")

    @field_validator("url", mode="after")
    @classmethod
    def validate_cache_url(cls, v: Optional[str], info: Any) -> Optional[str]:
        """Validate cache URL when backend is redis."""
        if hasattr(info, "data") and info.data.get("backend") == "redis" and not v:
            msg = "Redis backend requires cache URL"
            raise ValueError(msg)
        return v

class SecurityConfig(BaseModel):
    """Security configuration."""

    secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_minutes: int = Field(default=15, ge=1, le=1440)
    refresh_token_expiration_days: int = Field(default=7, ge=1, le=30)
    password_min_length: int = Field(default=8, ge=6, le=128)
    max_login_attempts: int = Field(default=5, ge=1, le=20)
    lockout_duration_minutes: int = Field(default=15, ge=1, le=1440)
    enable_mfa: bool = Field(default=False)
    api_key_length: int = Field(default=32, ge=16, le=64)

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key strength."""
        if len(v) < 32:
            msg = "Secret key must be at least 32 characters long"
            raise ValueError(msg)
        if v == "changeme" or v.lower() in ["secret", "password", "key"]:
            msg = "Secret key must not be a common value"
            raise ValueError(msg)
        return v

class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    format: str = Field(default="json", pattern=r"^(json|console)$")
    include_timestamp: bool = Field(default=True)
    include_caller: bool = Field(default=False)
    max_string_length: int = Field(default=1000, ge=100, le=10000)
    log_file: Optional[str] = Field(default=None)
    max_bytes: int = Field(default=10485760, ge=1048576)  # 10MB default
    backup_count: int = Field(default=5, ge=1, le=20)

class DatabaseConfig(BaseSettings):
    """Database-specific configuration."""

    model_config = SettingsConfigDict(env_prefix="DB_")

    url: str = Field(..., description="Database connection URL")
    pool_size: int = Field(default=10, ge=1, le=100, description="Connection pool size")
    max_overflow: int = Field(default=20, ge=0, le=100, description="Maximum pool overflow")
    echo: bool = Field(default=False, description="Enable SQL query logging")
    connect_timeout: int = Field(
        default=30, ge=1, le=300, description="Connection timeout in seconds"
    )
    command_timeout: int = Field(default=60, ge=1, le=600, description="Command timeout in seconds")
    migration_timeout: int = Field(
        default=300, ge=30, le=1800, description="Migration timeout in seconds"
    )
    enable_row_level_security: bool = Field(
        default=True, description="Enable RLS for multi-tenancy"
    )
    schema_name: Optional[str] = Field(default=None, description="Database schema name")

    @field_validator("url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://", "sqlite://")):
            msg = "Database URL must be postgresql:// or sqlite://"
            raise ValueError(msg)
        return v

class RedisConfig(BaseSettings):
    """Redis-specific configuration."""

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    pool_size: int = Field(default=10, ge=1, le=100, description="Connection pool size")
    socket_timeout: int = Field(default=30, ge=1, le=300, description="Socket timeout in seconds")
    socket_connect_timeout: int = Field(
        default=30, ge=1, le=300, description="Connection timeout in seconds"
    )
    retry_on_timeout: bool = Field(default=True, description="Retry on timeout")
    max_connections: int = Field(default=50, ge=1, le=1000, description="Maximum connections")
    decode_responses: bool = Field(default=True, description="Decode responses to strings")
    health_check_interval: int = Field(default=30, ge=10, description="Health check interval")

    @field_validator("url")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        """Validate Redis URL format."""
        if not v.startswith("redis://"):
            msg = "Redis URL must start with redis://"
            raise ValueError(msg)
        return v

class ObservabilityConfig(BaseModel):
    """Observability and monitoring configuration."""

    enabled: bool = Field(default=True)
    service_name: str = Field(default="dotmac-business-services")
    environment: str = Field(default="development")

    # Metrics
    metrics_enabled: bool = Field(default=True)
    metrics_port: int = Field(default=8000, ge=1024, le=65535)
    metrics_path: str = Field(default="/metrics")

    # Tracing
    tracing_enabled: bool = Field(default=True)
    tracing_endpoint: Optional[str] = Field(default=None)
    trace_sample_rate: float = Field(default=0.1, ge=0.0, le=1.0)

    # SigNoz integration
    signoz_enabled: bool = Field(default=False)
    signoz_endpoint: Optional[str] = Field(default=None)
    signoz_access_token: Optional[str] = Field(default=None)

    # Custom tags
    custom_tags: dict[str, str] = Field(default_factory=dict)

    @field_validator("signoz_endpoint", mode="after")
    @classmethod
    def validate_signoz_config(cls, v: Optional[str], info: Any) -> Optional[str]:
        """Validate SigNoz configuration."""
        if hasattr(info, "data") and info.data.get("signoz_enabled") and not v:
            msg = "SigNoz endpoint required when SigNoz is enabled"
            raise ValueError(msg)
        return v

class APIGatewayConfig(BaseModel):
    """API Gateway configuration."""

    # Rate limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests: int = Field(default=100, ge=1)
    rate_limit_window: int = Field(default=60, ge=1)  # seconds

    # Circuit breaker
    circuit_breaker_enabled: bool = Field(default=True)
    circuit_breaker_failure_threshold: int = Field(default=5, ge=1)
    circuit_breaker_recovery_timeout: int = Field(default=60, ge=1)
    circuit_breaker_expected_exception: Optional[str] = Field(default=None)

    # Request validation
    max_request_size: int = Field(default=10485760, ge=1024)  # 10MB
    request_timeout: int = Field(default=30, ge=1)

    # Service discovery
    service_discovery_enabled: bool = Field(default=False)
    service_registry_url: Optional[str] = Field(default=None)

    # API versioning
    versioning_enabled: bool = Field(default=True)
    default_version: str = Field(default="v1")
    supported_versions: list[str] = Field(default_factory=lambda: ["v1"])

class WorkflowConfig(BaseModel):
    """Workflow engine configuration."""

    engine: str = Field(default="temporal", pattern=r"^(temporal|celery|simple)$")

    # Temporal settings
    temporal_host: str = Field(default="localhost:7233")
    temporal_namespace: str = Field(default="default")
    temporal_task_queue: str = Field(default="business-services")
    temporal_worker_count: int = Field(default=4, ge=1, le=20)

    # Celery settings
    celery_broker_url: Optional[str] = Field(default=None)
    celery_result_backend: Optional[str] = Field(default=None)
    celery_task_serializer: str = Field(default="json")

    # Workflow settings
    default_timeout: int = Field(default=3600, ge=60)  # seconds
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_backoff: float = Field(default=2.0, ge=1.0)
    enable_saga: bool = Field(default=True)

class BaseConfig(BaseSettings):
    """Base configuration for DotMac Business Services."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )

    # Application settings
    app_name: str = Field(default="DotMac Business Services")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    environment: str = Field(default="development")

    # Server settings
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1024, le=65535)
    workers: int = Field(default=4, ge=1)

    # Component configurations
    cache: CacheConfig = Field(default_factory=CacheConfig)
    security: SecurityConfig = Field(
        default_factory=lambda: SecurityConfig(secret_key="change-me-in-production-" + "x" * 32)
    )
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    database: Optional[DatabaseConfig] = Field(default=None)
    redis: Optional[RedisConfig] = Field(default=None)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    api_gateway: APIGatewayConfig = Field(default_factory=APIGatewayConfig)
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig)
    licensing: LicensingConfig = Field(default_factory=LicensingConfig)

    # Feature flags
    features: dict[str, bool] = Field(
        default_factory=lambda: {
            "analytics": True,
            "billing": True,
            "user_management": True,
            "file_storage": True,
            "search": True,
            "audit_logging": True,
            "workflow_engine": True,
            "api_gateway": True,
        }
    )

    # Tenant settings
    multi_tenancy_enabled: bool = Field(default=True)
    default_tenant_id: str = Field(default="default")
    tenant_isolation_level: str = Field(default="database", pattern=r"^(database|schema|row)$")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = ["development", "testing", "staging", "production"]
        if v.lower() not in allowed:
            msg = f"Environment must be one of {allowed}"
            raise ValueError(msg)
        return v.lower()

    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled."""
        return self.features.get(feature, False)

    def get_database_url(self, tenant_id: Optional[str] = None) -> str:
        """Get database URL, potentially with tenant-specific modifications."""
        if not self.database:
            raise ValueError("Database configuration not provided")

        base_url = self.database.url

        if self.multi_tenancy_enabled and tenant_id:
            if self.tenant_isolation_level == "database":
                # Modify URL to use tenant-specific database
                base_url = base_url.replace("/dotmac", f"/dotmac_{tenant_id}")
            elif self.tenant_isolation_level == "schema":
                # Add schema parameter
                separator = "&" if "?" in base_url else "?"
                base_url = f"{base_url}{separator}options=-csearch_path={tenant_id}"

        return base_url

    def get_redis_key_prefix(self, tenant_id: Optional[str] = None) -> str:
        """Get Redis key prefix with optional tenant isolation."""
        prefix = self.cache.key_prefix

        if self.multi_tenancy_enabled and tenant_id:
            prefix = f"tenant:{tenant_id}:{prefix}"

        return prefix
