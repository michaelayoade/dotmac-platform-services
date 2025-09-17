"""
Observability configuration management for DotMac Platform Services.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class OpenTelemetryConfig(BaseModel):
    """OpenTelemetry configuration."""

    endpoint: str = Field(default="http://localhost:4317", description="OTLP gRPC endpoint")
    http_endpoint: str = Field(default="http://localhost:4318", description="OTLP HTTP endpoint")
    service_name: str = Field(default="dotmac-platform", description="Service name for telemetry")
    enable_traces: bool = True
    enable_metrics: bool = True
    enable_logs: bool = True
    sample_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    batch_size: int = Field(default=512, gt=0)
    export_timeout_ms: int = Field(default=30000, gt=0)


class SigNozConfig(BaseModel):
    """SigNoz backend configuration."""

    clickhouse_host: str = "localhost"
    clickhouse_port: int = 9000
    clickhouse_database: str = "signoz_traces"
    clickhouse_user: str = "default"
    clickhouse_password: str = ""

    query_service_url: str = "http://localhost:8080"
    frontend_url: str = "http://localhost:3301"
    alertmanager_url: str = "http://localhost:9093"

    retention_days: int = Field(default=30, gt=0)
    enable_dashboards: bool = True
    enable_alerts: bool = True


class MetricsConfig(BaseModel):
    """Metrics collection configuration."""

    prometheus_port: int = 8888
    enable_host_metrics: bool = True
    enable_process_metrics: bool = True
    enable_runtime_metrics: bool = True

    custom_metrics_prefix: str = "dotmac_"
    histogram_buckets: list[float] = Field(
        default_factory=lambda: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
    )


class TracingConfig(BaseModel):
    """Distributed tracing configuration."""

    propagators: list[str] = Field(default_factory=lambda: ["tracecontext", "baggage", "b3"])
    span_processors: list[str] = Field(default_factory=lambda: ["batch"])
    max_span_attributes: int = Field(default=128, gt=0)
    max_event_attributes: int = Field(default=128, gt=0)
    max_link_attributes: int = Field(default=128, gt=0)


class LoggingConfig(BaseModel):
    """Structured logging configuration."""

    level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    format: str = Field(default="json", pattern="^(json|text)$")
    enable_correlation: bool = True
    include_trace_context: bool = True

    # Log export settings
    export_to_otel: bool = True
    export_batch_size: int = Field(default=512, gt=0)
    export_interval_ms: int = Field(default=5000, gt=0)


class ObservabilitySettings(BaseSettings):
    """
    Main observability settings for the platform.

    This can be configured via environment variables or config files.
    """

    # Component configs
    opentelemetry: OpenTelemetryConfig = Field(default_factory=OpenTelemetryConfig)
    signoz: Optional[SigNozConfig] = None  # Optional, can use other backends
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    tracing: TracingConfig = Field(default_factory=TracingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    # Global settings
    enabled: bool = True
    environment: str = Field(default="development", pattern="^(development|staging|production)$")
    deployment_type: str = Field(default="docker", pattern="^(docker|kubernetes|standalone)$")

    # Feature flags
    enable_profiling: bool = False
    enable_continuous_profiling: bool = False
    enable_error_tracking: bool = True
    enable_performance_monitoring: bool = True

    class Config:
        env_prefix = "DOTMAC_OBSERVABILITY_"
        env_nested_delimiter = "__"

    @classmethod
    def for_testing(cls) -> "ObservabilitySettings":
        """Create settings optimized for testing."""
        return cls(
            opentelemetry=OpenTelemetryConfig(
                endpoint="http://localhost:4317",
                sample_rate=0.1,  # Lower sampling for tests
                enable_logs=False,  # Reduce noise in tests
            ),
            metrics=MetricsConfig(enable_host_metrics=False, enable_process_metrics=False),
            logging=LoggingConfig(level="WARNING", export_to_otel=False),
            enable_profiling=False,
            environment="testing",
        )

    @classmethod
    def for_docker(cls) -> "ObservabilitySettings":
        """Create settings for Docker deployment with SigNoz."""
        return cls(
            opentelemetry=OpenTelemetryConfig(
                endpoint="http://signoz-otel-collector:4317", service_name="dotmac-platform"
            ),
            signoz=SigNozConfig(
                clickhouse_host="clickhouse",
                query_service_url="http://signoz-query-service:8080",
                frontend_url="http://localhost:3301",
            ),
            environment="development",
            deployment_type="docker",
        )

    @classmethod
    def for_kubernetes(cls) -> "ObservabilitySettings":
        """Create settings for Kubernetes deployment."""
        return cls(
            opentelemetry=OpenTelemetryConfig(
                endpoint="http://otel-collector.observability:4317", service_name="dotmac-platform"
            ),
            environment="production",
            deployment_type="kubernetes",
            enable_continuous_profiling=True,
        )

    def get_otel_resource_attributes(self) -> Dict[str, Any]:
        """Get OpenTelemetry resource attributes."""
        return {
            "service.name": self.opentelemetry.service_name,
            "service.environment": self.environment,
            "deployment.type": self.deployment_type,
            "telemetry.sdk.language": "python",
            "telemetry.sdk.name": "opentelemetry",
        }

    def should_export_telemetry(self) -> bool:
        """Check if telemetry should be exported."""
        return (
            self.enabled
            and self.environment != "testing"
            and (
                self.opentelemetry.enable_traces
                or self.opentelemetry.enable_metrics
                or self.opentelemetry.enable_logs
            )
        )
