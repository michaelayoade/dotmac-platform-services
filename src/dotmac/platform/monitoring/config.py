"""Monitoring configuration module."""


from pydantic import BaseModel, Field


class MonitoringConfig(BaseModel):
    """Monitoring configuration for various monitoring integrations."""

    # General settings
    metrics_port: int = Field(9090, description="Port for metrics endpoint")

    # Prometheus settings
    enable_prometheus: bool = Field(False, description="Enable Prometheus metrics")
    prometheus_port: int = Field(9090, description="Prometheus metrics port")
    prometheus_path: str = Field("/metrics", description="Prometheus metrics path")

    # Datadog settings
    enable_datadog: bool = Field(False, description="Enable Datadog integration")
    datadog_api_key: str | None = Field(None, description="Datadog API key")
    datadog_app_key: str | None = Field(None, description="Datadog app key")
    datadog_host: str = Field("https://api.datadoghq.com", description="Datadog API host")

    # New Relic settings
    enable_newrelic: bool = Field(False, description="Enable New Relic integration")
    newrelic_license_key: str | None = Field(None, description="New Relic license key")
    newrelic_app_name: str = Field("dotmac-platform", description="New Relic app name")

    # CloudWatch settings
    enable_cloudwatch: bool = Field(False, description="Enable CloudWatch metrics")
    cloudwatch_namespace: str = Field("DotMac/Platform", description="CloudWatch namespace")
    cloudwatch_region: str = Field("us-east-1", description="AWS region for CloudWatch")
