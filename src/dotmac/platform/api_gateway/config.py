"""Unified configuration for API Gateway."""


from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum

from .interfaces import RateLimiter, VersionStrategy
from .validation import ValidationLevel, RequestValidator
from dotmac.platform.observability.unified_logging import get_logger

logger = get_logger(__name__)

class GatewayMode(str, Enum):
    """Gateway operation modes."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class SecurityConfig:
    """Security configuration."""

    enable_auth: bool = True
    enable_rbac: bool = True
    auth_header: str = "Authorization"
    api_key_header: str = "X-API-Key"
    allowed_origins: List[str] = field(default_factory=lambda: ["*"])
    allowed_methods: List[str] = field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "PATCH"]
    )
    allowed_headers: List[str] = field(default_factory=lambda: ["*"])
    max_age: int = 3600
    enable_csrf: bool = False
    trusted_hosts: List[str] = field(default_factory=lambda: ["*"])

@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""

    enabled: bool = True
    default_limit: int = 100  # requests per window
    window_seconds: int = 60
    burst_size: int = 10
    strategy: str = "sliding_window"  # fixed_window, sliding_window, token_bucket
    by_user: bool = True
    by_ip: bool = True
    by_api_key: bool = False
    redis_url: Optional[str] = None  # For distributed rate limiting
    custom_limits: Dict[str, int] = field(default_factory=dict)  # route -> limit

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""

    enabled: bool = True
    failure_threshold: int = 5
    timeout_seconds: int = 60
    recovery_timeout: int = 30
    half_open_requests: int = 3
    excluded_status_codes: List[int] = field(default_factory=lambda: [404, 401, 403])

@dataclass
class ObservabilityConfig:
    """Observability configuration for OpenTelemetry and SigNoz."""

    # Core settings
    enabled: bool = True
    metrics_enabled: bool = True
    tracing_enabled: bool = True
    logging_enabled: bool = True
    logging_level: str = "INFO"

    # SLO configuration
    slo_target: float = 99.9  # % availability target
    error_budget_window: int = 3600  # seconds

    # OpenTelemetry configuration
    service_name: str = "api-gateway"
    service_version: str = "1.0.0"
    environment: str = "development"
    otlp_endpoint: str = "localhost:4317"  # SigNoz OTLP collector endpoint
    otlp_headers: str = ""  # Headers like "signoz-access-token=YOUR_TOKEN"
    otlp_insecure: bool = True  # Use insecure connection for local dev
    otlp_protocol: str = "grpc"  # grpc or http/protobuf

    # Sampling and export
    trace_sample_rate: float = 0.1  # 10% sampling
    metrics_export_interval: int = 60  # seconds

    # Request/Response logging
    log_requests: bool = True
    log_responses: bool = False
    log_errors: bool = True
    detailed_errors: bool = False  # Show detailed errors in responses

    # Instrumentation
    instrument_httpx: bool = True
    instrument_redis: bool = True

    # Additional configuration
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    resource_attributes: Dict[str, str] = field(default_factory=dict)
    use_platform_telemetry: bool = True
    instrument_asgi: bool = False  # leave False when using custom middleware
    platform_telemetry_endpoint: Optional[str] = None

@dataclass
class ValidationConfig:
    """Validation configuration."""

    enabled: bool = True
    default_level: ValidationLevel = ValidationLevel.STRICT
    validate_requests: bool = True
    validate_responses: bool = False
    schema_registry_path: Optional[str] = None
    auto_register_schemas: bool = True

@dataclass
class CacheConfig:
    """Cache configuration."""

    enabled: bool = True
    default_ttl: int = 300  # 5 minutes
    max_size: int = 1000
    strategy: str = "lru"  # lru, lfu, ttl
    redis_url: Optional[str] = None
    cache_control_header: bool = True
    vary_headers: List[str] = field(default_factory=lambda: ["Accept", "Authorization"])

@dataclass
class ServiceMeshConfig:
    """Service mesh integration configuration."""

    enabled: bool = False
    mesh_type: str = "istio"  # istio, linkerd, consul
    service_name: str = "api-gateway"
    namespace: str = "default"
    enable_mtls: bool = True
    enable_retries: bool = True
    retry_attempts: int = 3
    retry_timeout: int = 1000  # ms

@dataclass
class GatewayConfig:
    """Unified API Gateway configuration."""

    # Basic settings
    mode: GatewayMode = GatewayMode.DEVELOPMENT
    name: str = "DotMac API Gateway"
    version: str = "1.0.0"
    base_path: str = "/api"
    port: int = 8000
    workers: int = 4

    # Component configs
    security: SecurityConfig = field(default_factory=SecurityConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    service_mesh: ServiceMeshConfig = field(default_factory=ServiceMeshConfig)

    # Strategy instances (to be injected)
    version_strategy: Optional[VersionStrategy] = None
    rate_limiter: Optional[RateLimiter] = None
    request_validator: Optional[RequestValidator] = None

    # Platform service integration
    use_platform_services: bool = True
    platform_services_config: Dict[str, Any] = field(default_factory=dict)

    # Custom middleware
    custom_middleware: List[Any] = field(default_factory=list)

    # Feature flags
    features: Dict[str, bool] = field(
        default_factory=lambda: {
            "request_transformation": True,
            "response_transformation": True,
            "request_logging": True,
            "metrics_collection": True,
            "distributed_tracing": True,
            "api_versioning": True,
            "content_negotiation": True,
            "compression": True,
            "request_id_tracking": True,
            "graphql_endpoint": True,
            "openapi_docs": True,
        }
    )

    @classmethod
    def for_development(cls) -> "GatewayConfig":
        """Create development configuration."""
        return cls(
            mode=GatewayMode.DEVELOPMENT,
            security=SecurityConfig(enable_auth=False, enable_rbac=False, enable_csrf=False),
            rate_limit=RateLimitConfig(enabled=False),
            circuit_breaker=CircuitBreakerConfig(enabled=False),
            observability=ObservabilityConfig(
                logging_level="DEBUG", trace_sample_rate=1.0  # 100% sampling in dev
            ),
            validation=ValidationConfig(default_level=ValidationLevel.LENIENT),
        )

    @classmethod
    def for_production(cls) -> "GatewayConfig":
        """Create production configuration."""
        return cls(
            mode=GatewayMode.PRODUCTION,
            workers=8,
            security=SecurityConfig(
                enable_auth=True,
                enable_rbac=True,
                enable_csrf=True,
                allowed_origins=["https://api.dotmac.com"],
            ),
            rate_limit=RateLimitConfig(enabled=True, default_limit=1000, window_seconds=60),
            circuit_breaker=CircuitBreakerConfig(enabled=True),
            observability=ObservabilityConfig(
                logging_level="WARNING",
                trace_sample_rate=0.01,  # 1% sampling
                environment="production",
                otlp_endpoint="otel-collector.production.svc.cluster.local:4317",
                otlp_insecure=False,
                detailed_errors=False,
                slo_target=99.95,  # Higher SLO for production
            ),
            validation=ValidationConfig(default_level=ValidationLevel.STRICT),
            cache=CacheConfig(enabled=True, default_ttl=3600),  # 1 hour
        )

    def validate(self) -> List[str]:
        """Validate configuration consistency."""
        errors = []

        # Check rate limiting config
        if (
            self.rate_limit.enabled
            and self.rate_limit.strategy == "redis"
            and not self.rate_limit.redis_url
        ):
            errors.append("Redis URL required for distributed rate limiting")

        # Check cache config
        if self.cache.enabled and self.cache.strategy == "redis" and not self.cache.redis_url:
            errors.append("Redis URL required for Redis cache")

        # Check observability
        if self.observability.tracing_enabled and self.observability.trace_sample_rate <= 0:
            errors.append("Trace sample rate must be > 0")

        # Check service mesh
        if self.service_mesh.enabled and not self.service_mesh.service_name:
            errors.append("Service name required for service mesh")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "mode": self.mode.value,
            "name": self.name,
            "version": self.version,
            "base_path": self.base_path,
            "port": self.port,
            "workers": self.workers,
            "security": {
                "auth_enabled": self.security.enable_auth,
                "rbac_enabled": self.security.enable_rbac,
                "allowed_origins": self.security.allowed_origins,
            },
            "rate_limit": {
                "enabled": self.rate_limit.enabled,
                "limit": self.rate_limit.default_limit,
                "window": self.rate_limit.window_seconds,
            },
            "circuit_breaker": {
                "enabled": self.circuit_breaker.enabled,
                "threshold": self.circuit_breaker.failure_threshold,
            },
            "observability": {
                "metrics": self.observability.metrics_enabled,
                "tracing": self.observability.tracing_enabled,
                "logging": self.observability.logging_enabled,
            },
            "features": self.features,
        }

class ConfigManager:
    """Manages gateway configuration."""

    def __init__(self, config: Optional[GatewayConfig] = None):
        self.config = config or GatewayConfig()
        self._listeners = []

    def update(self, **kwargs: Any) -> None:
        """Update configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self._notify_listeners()

    def register_listener(self, callback: Callable[[GatewayConfig], None]) -> None:
        """Register config change listener."""
        self._listeners.append(callback)

    def _notify_listeners(self) -> None:
        """Notify all listeners of config change."""
        for listener in self._listeners:
            try:
                listener(self.config)
            except Exception as e:
                logger.error(f"Error notifying listener: {e}")

    def load_from_env(self) -> None:
        """Load configuration from environment variables."""
        import os

        logger.info("Loading configuration from environment variables")

        # Update from environment
        if os.getenv("GATEWAY_MODE"):
            self.config.mode = GatewayMode(os.getenv("GATEWAY_MODE"))

        port = os.getenv("GATEWAY_PORT")
        if port:
            self.config.port = int(port)

        workers = os.getenv("GATEWAY_WORKERS")
        if workers:
            self.config.workers = int(workers)

        # Security
        auth_enabled = os.getenv("GATEWAY_AUTH_ENABLED")
        if auth_enabled:
            self.config.security.enable_auth = auth_enabled.lower() == "true"

        # Rate limiting
        rate_limit = os.getenv("GATEWAY_RATE_LIMIT")
        if rate_limit:
            self.config.rate_limit.default_limit = int(rate_limit)

        logger.debug(f"Configuration loaded: mode={self.config.mode}, port={self.config.port}")
        self._notify_listeners()
