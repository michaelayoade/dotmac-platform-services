
import warnings
from typing import Any

from fastapi import FastAPI

from .config import ObservabilityConfig
from .manager import ObservabilityManager

from dotmac.platform.observability.unified_logging import get_logger
__all__ = [
    # Manager class
    "ObservabilityManager",
    # Core functions
    "add_observability_middleware",
    "get_logger",
    "get_observability_service",
    "initialize_observability_service",
    "is_observability_service_available",
    # Configuration (critical for app startup)
    "ObservabilityConfig",
    "create_default_config",
    "Environment",
    "ExporterConfig",
    "ExporterType",
    "OTelConfig",
    # Bootstrap functions
    "initialize_otel",
    "shutdown_otel",
    "OTelBootstrap",
    # Metrics system
    "initialize_metrics_registry",
    "initialize_tenant_metrics",
    "MetricsRegistry",
    "TenantMetrics",
    # Health checks
    "check_otel_health",
    "check_metrics_registry_health",
]

# Optional modules with graceful fallbacks
try:
    from .bootstrap import (
        OTelBootstrap,
        create_child_span,
        get_current_span_context,
        initialize_otel,
        shutdown_otel,
    )

    _bootstrap_available = True
except ImportError as e:
    warnings.warn(f"OpenTelemetry bootstrap not available: {e}", stacklevel=2)
    OTelBootstrap = initialize_otel = shutdown_otel = None  # type: ignore
    get_current_span_context = create_child_span = None  # type: ignore
    _bootstrap_available = False

_config_available = False
try:
    # Import only what exists in config.py
    from .config import (
        Environment,
        ExporterConfig,
        ExporterType,
        OTelConfig,
        create_default_config,
    )

    _config_available = True
except ImportError as e:
    warnings.warn(f"Observability config not available: {e}", stacklevel=2)
    OTelConfig = Environment = None  # type: ignore
    ExporterType = ExporterConfig = create_default_config = None  # type: ignore

try:
    from .metrics import (
        BusinessMetricSpec,
        BusinessMetricType,
        MetricDefinition,
        MetricsRegistry,
        MetricType,
        SLOEvaluation,
        TenantContext,
        TenantMetrics,
        initialize_metrics_registry,
        initialize_tenant_metrics,
    )

    _metrics_available = True
except ImportError as e:
    warnings.warn(f"Metrics system not available: {e}", stacklevel=2)
    MetricsRegistry = TenantMetrics = MetricDefinition = MetricType = None  # type: ignore
    BusinessMetricSpec = BusinessMetricType = TenantContext = None  # type: ignore
    SLOEvaluation = initialize_metrics_registry = initialize_tenant_metrics = None  # type: ignore
    _metrics_available = False

try:
    from .logging import (
        CorrelationIDFilter,
        LogContext,
        LogLevel,
        StructuredLogger,
        init_structured_logging,
    )

    _logging_available = True
except ImportError as e:
    warnings.warn(f"Structured logging not available: {e}", stacklevel=2)
    StructuredLogger = LogContext = LogLevel = CorrelationIDFilter = None  # type: ignore
    init_structured_logging = None  # type: ignore
    _logging_available = False

try:
    from .tracing import SpanProcessor, TraceExporter, TracingManager, get_tracer

    _tracing_available = True
except ImportError as e:
    warnings.warn(f"Tracing system not available: {e}", stacklevel=2)
    TracingManager = SpanProcessor = TraceExporter = None  # type: ignore
    get_tracer = None  # type: ignore
    _tracing_available = False

try:
    from .health import (
        HealthCheck,
        HealthStatus,
        ObservabilityHealth,
        check_metrics_registry_health,
        check_otel_health,
        check_tenant_metrics_health,
        create_health_endpoint_handler,
        get_observability_health,
    )

    _health_available = True
except ImportError as e:
    warnings.warn(f"Health checks not available: {e}", stacklevel=2)
    HealthCheck = HealthStatus = ObservabilityHealth = None  # type: ignore
    check_otel_health = check_metrics_registry_health = None  # type: ignore
    check_tenant_metrics_health = create_health_endpoint_handler = None  # type: ignore
    get_observability_health = None  # type: ignore
    _health_available = False

try:
    from .dashboards import (
        DashboardProvisioner,
        DashboardProvisioningResult,
        SigNozDashboard,
        provision_platform_dashboards,
    )

    _dashboards_available = True
except ImportError as e:
    warnings.warn(f"Dashboard provisioning not available: {e}", stacklevel=2)
    DashboardProvisioner = provision_platform_dashboards = None  # type: ignore
    DashboardProvisioningResult = SigNozDashboard = None  # type: ignore
    _dashboards_available = False

try:
    from .middleware import (
        LoggingMiddleware,
        MetricsMiddleware,
        TracingMiddleware,
    )

    _middleware_available = True
except ImportError as e:
    warnings.warn(f"Observability middleware not available: {e}", stacklevel=2)
    MetricsMiddleware = TracingMiddleware = None  # type: ignore
    LoggingMiddleware = None  # type: ignore
    _middleware_available = False

# Service initialization and management
_observability_service_registry: dict[str, Any] = {}

def initialize_observability_service(config: dict[str, Any]) -> None:
    """Initialize observability services with configuration."""
    service_name = config.get("service_name", "dotmac-service")
    environment = config.get("environment", "development")

    # Initialize OpenTelemetry if available
    if _bootstrap_available and _config_available and initialize_otel and create_default_config:
        otel_config = create_default_config(
            service_name=service_name,
            environment=environment,
            otlp_endpoint=config.get("otlp_endpoint"),
        )
        otel_bootstrap = initialize_otel(otel_config)
        _observability_service_registry["otel"] = otel_bootstrap

    # Initialize metrics registry if available
    if _metrics_available and initialize_metrics_registry:
        metrics_registry = initialize_metrics_registry(service_name)
        _observability_service_registry["metrics"] = metrics_registry

        # Initialize tenant metrics
        if initialize_tenant_metrics:
            tenant_metrics = initialize_tenant_metrics(service_name, metrics_registry)
            _observability_service_registry["tenant_metrics"] = tenant_metrics

    # Initialize structured logging if available
    if _logging_available and init_structured_logging:
        log_level = config.get("log_level", "INFO")
        correlation_id_header = config.get("correlation_id_header", "X-Correlation-ID")

        try:
            obs_cfg = ObservabilityConfig(
                service_name=service_name,
                environment=environment,
                log_level=log_level,
                correlation_id_header=correlation_id_header,
                enable_logging=True,
            )
        except Exception:
            obs_cfg = None

        init_structured_logging(config=obs_cfg)
        logger = get_logger(service_name)
        _observability_service_registry["logger"] = logger
    else:
        logger = get_logger(service_name)
        _observability_service_registry["logger"] = logger

    # Initialize tracing manager if available
    if _tracing_available and TracingManager:
        try:
            tracing_cfg = obs_cfg if "obs_cfg" in locals() else ObservabilityConfig(service_name=service_name, environment=environment)  # type: ignore[name-defined]
        except Exception:
            tracing_cfg = None
        tracing_manager = TracingManager(config=tracing_cfg)
        _observability_service_registry["tracing"] = tracing_manager

    # Initialize health: store a simple placeholder or compute lazily elsewhere
    if _health_available and ObservabilityHealth:
        _observability_service_registry["health"] = None

def get_observability_service(name: str) -> Any | None:
    """Get an initialized observability service."""
    return _observability_service_registry.get(name)

def is_observability_service_available(name: str) -> bool:
    """Check if observability service is available."""
    return name in _observability_service_registry

# FastAPI integration helpers
def add_observability_middleware(app: FastAPI, config: dict[str, Any] | None = None):
    """Add observability middleware to FastAPI app."""
    if not isinstance(app, FastAPI):
        raise TypeError("app must be a FastAPI instance")

    if config is None:
        config = {}

    # Add logging middleware
    if _logging_available and LoggingMiddleware is not None:
        app.add_middleware(LoggingMiddleware)

    # Add metrics middleware
    if _metrics_available and MetricsMiddleware is not None:
        app.add_middleware(MetricsMiddleware)

    # Add tracing middleware
    if _tracing_available and TracingMiddleware is not None:
        app.add_middleware(TracingMiddleware)

    return app

# Simple environment helpers expected by tests
def get_current_environment() -> str:
    """Return the current environment string.

    Falls back to 'development' if not set. Accepts common values used in tests.
    """
    import os

    env = os.getenv("ENVIRONMENT") or os.getenv("DOTMAC_ENV") or "development"
    return env.lower()

def is_observability_enabled() -> bool:
    """Return whether observability is enabled via env (default: True)."""
    import os

    val = os.getenv("DOTMAC_OBSERVABILITY_ENABLED", "true").lower()
    return val in {"1", "true", "yes", "on"}
