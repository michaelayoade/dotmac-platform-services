"""
Configuration classes for WebSocket gateway.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class LogLevel(str, Enum):
    """Log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class BackendType(str, Enum):
    """Scaling backend types."""

    LOCAL = "local"
    REDIS = "redis"


@dataclass
class RedisConfig:
    """Redis connection configuration."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    username: Optional[str] = None
    ssl: bool = False

    # Connection pool settings
    max_connections: int = 100
    retry_on_timeout: bool = True
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0

    # Channel settings
    channel_prefix: str = "ws"
    message_ttl_seconds: int = 300

    def to_url(self) -> str:
        """Generate Redis URL."""
        if self.password:
            auth = f"{self.username or ''}:{self.password}@"
        else:
            auth = ""

        protocol = "rediss" if self.ssl else "redis"
        return f"{protocol}://{auth}{self.host}:{self.port}/{self.db}"


@dataclass
class AuthConfig:
    """Authentication configuration."""

    enabled: bool = True

    # JWT settings
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_token_expire_minutes: int = 60

    # Token validation
    require_token: bool = True
    token_header: str = "Authorization"
    token_query_param: str = "token"

    # User resolution
    user_resolver_url: Optional[str] = None
    user_cache_ttl_seconds: int = 300

    # Permissions
    require_permissions: list[str] = field(default_factory=list)


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""

    enabled: bool = True

    # Connection limits
    max_connections_per_ip: int = 10
    max_connections_per_user: int = 5
    max_connections_per_tenant: int = 100

    # Message rate limits
    messages_per_minute: int = 60
    burst_size: int = 10

    # Cleanup
    cleanup_interval_seconds: int = 60


@dataclass
class SessionConfig:
    """Session management configuration."""

    # Session timeouts
    idle_timeout_seconds: int = 300  # 5 minutes
    max_session_duration_seconds: int = 28800  # 8 hours

    # Heartbeat/ping
    ping_interval_seconds: int = 30
    ping_timeout_seconds: int = 10

    # Session cleanup
    cleanup_interval_seconds: int = 60

    # Storage
    store_session_metadata: bool = True
    metadata_ttl_seconds: int = 3600


@dataclass
class ObservabilityConfig:
    """Observability configuration."""

    enabled: bool = True

    # Metrics
    export_metrics: bool = True
    metrics_port: int = 9090
    metrics_path: str = "/metrics"

    # Tracing
    export_traces: bool = False
    trace_sample_rate: float = 0.1

    # Health checks
    health_check_enabled: bool = True
    health_check_interval_seconds: int = 30

    # Service info
    service_name: str = "dotmac-websockets"
    service_version: str = "1.0.0"


@dataclass
class WebSocketConfig:
    """Main WebSocket gateway configuration."""

    # Server settings
    host: str = "0.0.0.0"  # nosec B104 - intentional binding for container deployment
    port: int = 8765
    path: str = "/ws"

    # WebSocket settings
    max_size: int = 1024 * 1024  # 1MB
    max_queue: int = 32
    read_limit: int = 2**16
    write_limit: int = 2**16

    # Compression
    compression: Optional[str] = "deflate"  # None, "deflate", "permessage-deflate"

    # Backend configuration
    backend_type: BackendType = BackendType.LOCAL
    redis_config: Optional[RedisConfig] = None

    # Feature configurations
    auth_config: AuthConfig = field(default_factory=AuthConfig)
    rate_limit_config: RateLimitConfig = field(default_factory=RateLimitConfig)
    session_config: SessionConfig = field(default_factory=SessionConfig)
    observability_config: ObservabilityConfig = field(default_factory=ObservabilityConfig)

    # Logging
    log_level: LogLevel = LogLevel.INFO

    # Multi-tenancy
    tenant_isolation_enabled: bool = True
    default_tenant_id: str = "default"

    # Additional settings
    extra_headers: dict[str, str] = field(default_factory=dict)
    allowed_origins: list[str] = field(default_factory=lambda: ["*"])

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.backend_type == BackendType.REDIS and not self.redis_config:
            self.redis_config = RedisConfig()

        # Validate auth config
        if self.auth_config.enabled and self.auth_config.require_token:
            if not self.auth_config.jwt_secret_key:
                raise ValueError("JWT secret key is required when authentication is enabled")

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> "WebSocketConfig":
        """Create configuration from dictionary."""
        # Handle nested configurations
        if "redis_config" in config_dict and isinstance(config_dict["redis_config"], dict):
            config_dict["redis_config"] = RedisConfig(**config_dict["redis_config"])

        if "auth_config" in config_dict and isinstance(config_dict["auth_config"], dict):
            config_dict["auth_config"] = AuthConfig(**config_dict["auth_config"])

        if "rate_limit_config" in config_dict and isinstance(
            config_dict["rate_limit_config"], dict
        ):
            config_dict["rate_limit_config"] = RateLimitConfig(**config_dict["rate_limit_config"])

        if "session_config" in config_dict and isinstance(config_dict["session_config"], dict):
            config_dict["session_config"] = SessionConfig(**config_dict["session_config"])

        if "observability_config" in config_dict and isinstance(
            config_dict["observability_config"], dict
        ):
            config_dict["observability_config"] = ObservabilityConfig(
                **config_dict["observability_config"]
            )

        return cls(**config_dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        result = {}

        for key, value in self.__dict__.items():
            if hasattr(value, "__dict__"):
                # Handle nested dataclasses
                result[key] = {k: v for k, v in value.__dict__.items()}
            else:
                result[key] = value

        return result


# Default configurations for common use cases
def create_development_config(**overrides) -> WebSocketConfig:
    """Create configuration optimized for development."""
    config = WebSocketConfig(
        log_level=LogLevel.DEBUG,
        backend_type=BackendType.LOCAL,
        auth_config=AuthConfig(enabled=False),
        rate_limit_config=RateLimitConfig(max_connections_per_ip=100, messages_per_minute=120),
        observability_config=ObservabilityConfig(export_traces=True, trace_sample_rate=1.0),
    )

    # Apply overrides
    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)

    return config


def create_production_config(
    redis_host: str = "redis", jwt_secret: Optional[str] = None, **overrides
) -> WebSocketConfig:
    """Create configuration optimized for production."""
    if not jwt_secret:
        raise ValueError("JWT secret is required for production")

    config = WebSocketConfig(
        log_level=LogLevel.INFO,
        backend_type=BackendType.REDIS,
        redis_config=RedisConfig(host=redis_host, max_connections=200),
        auth_config=AuthConfig(enabled=True, jwt_secret_key=jwt_secret, require_token=True),
        rate_limit_config=RateLimitConfig(
            max_connections_per_ip=20, max_connections_per_user=10, messages_per_minute=60
        ),
        observability_config=ObservabilityConfig(
            export_metrics=True, export_traces=False, trace_sample_rate=0.01
        ),
    )

    # Apply overrides
    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)

    return config
