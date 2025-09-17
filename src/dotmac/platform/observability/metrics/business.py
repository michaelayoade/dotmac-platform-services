"""
Business metrics and SLO monitoring for tenant-scoped operations.
"""


from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from .registry import MetricDefinition, MetricsRegistry, MetricType

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

class BusinessMetricType(str, Enum):
    """Types of business metrics."""

    SUCCESS_RATE = "success_rate"
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    AVAILABILITY = "availability"
    CUSTOM = "custom"

@dataclass
class BusinessMetricSpec:
    """Specification for a business metric with SLO targets."""

    name: str
    metric_type: BusinessMetricType
    description: str
    slo_target: float  # Target value (e.g., 0.95 for 95% success rate)
    alert_threshold: float  # Alert if below this threshold

    # Metric configuration
    labels: list[str] | None = None
    unit: str | None = None
    evaluation_window: int = 300  # seconds (5 minutes)

    # SLO configuration
    error_budget_period: int = 86400  # 24 hours in seconds
    critical_threshold: float | None = None  # Critical alert threshold

    def __post_init__(self) -> None:
        """Validate business metric spec."""
        if self.labels is None:
            self.labels = ["tenant_id", "service"]

        # For latency and error_rate metrics, lower is better, so thresholds are inverted
        is_lower_better = self.metric_type in (
            BusinessMetricType.LATENCY,
            BusinessMetricType.ERROR_RATE,
        )

        if self.critical_threshold is None:
            if is_lower_better:
                # For latency/error_rate: critical should be higher (worse) than alert threshold
                self.critical_threshold = self.alert_threshold * 1.5
            else:
                # For success rates/availability: critical should be lower (worse) than alert threshold
                self.critical_threshold = self.alert_threshold * 0.9

        # Validate thresholds based on metric type
        if is_lower_better:
            # For latency/error_rate: SLO target should be lower (better) than alert threshold
            if self.slo_target >= self.alert_threshold:
                raise ValueError("SLO target must be lower than alert threshold")

            # For latency/error_rate: alert threshold should be lower (better) than critical threshold
            if self.alert_threshold >= self.critical_threshold:
                raise ValueError("Alert threshold must be lower than critical threshold")
        else:
            # For success rates/availability: SLO target should be higher (better) than alert threshold
            if self.slo_target <= self.alert_threshold:
                raise ValueError("SLO target must be higher than alert threshold")

            # For success rates/availability: alert threshold should be higher (better) than critical threshold
            if self.alert_threshold <= self.critical_threshold:
                raise ValueError("Alert threshold must be higher than critical threshold")

@dataclass
class TenantContext:
    """Context information for tenant-scoped metrics."""

    tenant_id: str
    service: str = "unknown"
    region: str | None = None
    environment: str | None = None
    additional_labels: dict[str, str] | None = None

    def to_labels(self) -> dict[str, str]:
        """Convert to metric labels."""
        labels = {
            "tenant_id": self.tenant_id,
            "service": self.service,
        }

        if self.region:
            labels["region"] = self.region
        if self.environment:
            labels["environment"] = self.environment
        if self.additional_labels:
            labels.update(self.additional_labels)

        return labels

@dataclass
class SLOEvaluation:
    """Result of SLO evaluation for a business metric."""

    metric_name: str
    tenant_context: TenantContext
    current_value: float
    slo_target: float
    alert_threshold: float
    critical_threshold: float

    # Status
    is_healthy: bool
    is_warning: bool
    is_critical: bool

    # Error budget
    error_budget_consumed: float  # Percentage of error budget consumed
    error_budget_remaining: float  # Percentage remaining

    # Evaluation metadata
    evaluation_window: int
    sample_count: int
    evaluation_time: datetime = field(default_factory=datetime.utcnow)

class TenantMetrics:
    """
    Manager for tenant-scoped business metrics and SLO monitoring.
    """

    def __init__(
        self,
        service_name: str,
        metrics_registry: MetricsRegistry,
        enable_dashboards: bool = False,
        enable_slo_monitoring: bool = True,
    ) -> None:
        self.service_name = service_name
        self.metrics_registry = metrics_registry
        self.enable_dashboards = enable_dashboards
        self.enable_slo_monitoring = enable_slo_monitoring

        # Business metric specifications
        self._business_metrics: dict[str, BusinessMetricSpec] = {}

        # SLO evaluation history
        self._slo_history: dict[str, list[SLOEvaluation]] = {}

        # Register default business metrics
        self._register_default_business_metrics()

        logger.info(f"TenantMetrics initialized for {service_name}")

    def register_business_metric(self, spec: BusinessMetricSpec) -> bool:
        """
        Register a business metric specification.

        Args:
            spec: Business metric specification

        Returns:
            True if successful, False otherwise
        """
        try:
            # Register underlying metrics based on business metric type
            if spec.metric_type == BusinessMetricType.SUCCESS_RATE:
                self._register_success_rate_metrics(spec)
            elif spec.metric_type == BusinessMetricType.LATENCY:
                self._register_latency_metrics(spec)
            elif spec.metric_type == BusinessMetricType.THROUGHPUT:
                self._register_throughput_metrics(spec)
            elif spec.metric_type == BusinessMetricType.ERROR_RATE:
                self._register_error_rate_metrics(spec)
            elif spec.metric_type == BusinessMetricType.AVAILABILITY:
                self._register_availability_metrics(spec)
            else:
                # Custom metric
                self._register_custom_metrics(spec)

            self._business_metrics[spec.name] = spec
            logger.info(f"Registered business metric: {spec.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to register business metric {spec.name}: {e}")
            return False

    def record_business_metric(
        self,
        name: str,
        value: int | float,
        tenant_context: TenantContext,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Record a business metric value.

        Args:
            name: Business metric name
            value: Value to record
            tenant_context: Tenant context
            metadata: Additional metadata
        """
        spec = self._business_metrics.get(name)
        if not spec:
            logger.warning(f"Business metric {name} not registered")
            return

        labels = tenant_context.to_labels()

        try:
            if spec.metric_type == BusinessMetricType.SUCCESS_RATE:
                self._record_success_rate(spec, value, labels, metadata)
            elif spec.metric_type == BusinessMetricType.LATENCY:
                self._record_latency(spec, value, labels, metadata)
            elif spec.metric_type == BusinessMetricType.THROUGHPUT:
                self._record_throughput(spec, value, labels, metadata)
            elif spec.metric_type == BusinessMetricType.ERROR_RATE:
                self._record_error_rate(spec, value, labels, metadata)
            elif spec.metric_type == BusinessMetricType.AVAILABILITY:
                self._record_availability(spec, value, labels, metadata)
            else:
                # Custom metric
                self.metrics_registry.record_metric(name, value, labels)

        except Exception as e:
            logger.error(f"Failed to record business metric {name}: {e}")

    def evaluate_slos(self, tenant_context: TenantContext) -> dict[str, SLOEvaluation]:
        """
        Evaluate SLOs for all business metrics for a tenant.

        Args:
            tenant_context: Tenant context

        Returns:
            Dictionary of SLO evaluations by metric name
        """
        if not self.enable_slo_monitoring:
            return {}

        evaluations = {}

        for metric_name, spec in self._business_metrics.items():
            try:
                evaluation = self._evaluate_single_slo(spec, tenant_context)
                if evaluation:
                    evaluations[metric_name] = evaluation

                    # Store in history
                    if metric_name not in self._slo_history:
                        self._slo_history[metric_name] = []

                    self._slo_history[metric_name].append(evaluation)

                    # Keep only recent evaluations (last 24 hours)
                    cutoff = datetime.utcnow() - timedelta(hours=24)
                    self._slo_history[metric_name] = [
                        e for e in self._slo_history[metric_name] if e.evaluation_time > cutoff
                    ]

            except Exception as e:
                logger.error(f"Failed to evaluate SLO for {metric_name}: {e}")

        return evaluations

    def get_slo_history(self, metric_name: str, hours: int = 24) -> list[SLOEvaluation]:
        """
        Get SLO evaluation history for a metric.

        Args:
            metric_name: Business metric name
            hours: Number of hours of history to return

        Returns:
            List of SLO evaluations
        """
        if metric_name not in self._slo_history:
            return []

        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [e for e in self._slo_history[metric_name] if e.evaluation_time > cutoff]

    def get_business_metrics_info(self) -> dict[str, dict[str, Any]]:
        """Get information about all registered business metrics."""
        return {
            name: {
                "type": spec.metric_type.value,
                "description": spec.description,
                "slo_target": spec.slo_target,
                "alert_threshold": spec.alert_threshold,
                "labels": spec.labels,
            }
            for name, spec in self._business_metrics.items()
        }

    def _register_default_business_metrics(self) -> None:
        """Register default business metrics for common use cases."""
        default_specs = [
            BusinessMetricSpec(
                name="login_success_rate",
                metric_type=BusinessMetricType.SUCCESS_RATE,
                description="User login success rate",
                slo_target=0.99,
                alert_threshold=0.95,
                labels=["tenant_id", "service", "method"],
            ),
            BusinessMetricSpec(
                name="api_request_success_rate",
                metric_type=BusinessMetricType.SUCCESS_RATE,
                description="API request success rate",
                slo_target=0.995,
                alert_threshold=0.99,
                labels=["tenant_id", "service", "endpoint"],
            ),
            BusinessMetricSpec(
                name="service_provisioning_success_rate",
                metric_type=BusinessMetricType.SUCCESS_RATE,
                description="Service provisioning success rate",
                slo_target=0.98,
                alert_threshold=0.95,
                labels=["tenant_id", "service", "provision_type"],
            ),
            BusinessMetricSpec(
                name="api_response_latency",
                metric_type=BusinessMetricType.LATENCY,
                description="API response latency P95",
                slo_target=0.5,  # 500ms
                alert_threshold=1.0,  # 1s
                unit="s",
                labels=["tenant_id", "service", "endpoint"],
            ),
            BusinessMetricSpec(
                name="database_query_latency",
                metric_type=BusinessMetricType.LATENCY,
                description="Database query latency P95",
                slo_target=0.1,  # 100ms
                alert_threshold=0.5,  # 500ms
                unit="s",
                labels=["tenant_id", "service", "operation"],
            ),
        ]

        for spec in default_specs:
            self.register_business_metric(spec)

    def _register_success_rate_metrics(self, spec: BusinessMetricSpec) -> None:
        """Register metrics for success rate business metric."""
        # Total attempts counter
        total_metric = MetricDefinition(
            name=f"{spec.name}_total",
            type=MetricType.COUNTER,
            description=f"Total attempts for {spec.description}",
            labels=spec.labels,
        )
        self.metrics_registry.register_metric(total_metric)

        # Success counter
        success_metric = MetricDefinition(
            name=f"{spec.name}_success",
            type=MetricType.COUNTER,
            description=f"Successful attempts for {spec.description}",
            labels=spec.labels,
        )
        self.metrics_registry.register_metric(success_metric)

    def _register_latency_metrics(self, spec: BusinessMetricSpec) -> None:
        """Register metrics for latency business metric."""
        latency_metric = MetricDefinition(
            name=spec.name,
            type=MetricType.HISTOGRAM,
            description=spec.description,
            labels=spec.labels,
            unit=spec.unit,
        )
        self.metrics_registry.register_metric(latency_metric)

    def _register_throughput_metrics(self, spec: BusinessMetricSpec) -> None:
        """Register metrics for throughput business metric."""
        throughput_metric = MetricDefinition(
            name=spec.name,
            type=MetricType.COUNTER,
            description=spec.description,
            labels=spec.labels,
            unit=spec.unit,
        )
        self.metrics_registry.register_metric(throughput_metric)

    def _register_error_rate_metrics(self, spec: BusinessMetricSpec) -> None:
        """Register metrics for error rate business metric."""
        # Similar to success rate but focused on errors
        total_metric = MetricDefinition(
            name=f"{spec.name}_total",
            type=MetricType.COUNTER,
            description=f"Total requests for {spec.description}",
            labels=spec.labels,
        )
        self.metrics_registry.register_metric(total_metric)

        error_metric = MetricDefinition(
            name=f"{spec.name}_errors",
            type=MetricType.COUNTER,
            description=f"Error count for {spec.description}",
            labels=spec.labels,
        )
        self.metrics_registry.register_metric(error_metric)

    def _register_availability_metrics(self, spec: BusinessMetricSpec) -> None:
        """Register metrics for availability business metric."""
        availability_metric = MetricDefinition(
            name=spec.name,
            type=MetricType.GAUGE,
            description=spec.description,
            labels=spec.labels,
        )
        self.metrics_registry.register_metric(availability_metric)

    def _register_custom_metrics(self, spec: BusinessMetricSpec) -> None:
        """Register metrics for custom business metric."""
        custom_metric = MetricDefinition(
            name=spec.name,
            type=MetricType.GAUGE,  # Default to gauge for custom metrics
            description=spec.description,
            labels=spec.labels,
            unit=spec.unit,
        )
        self.metrics_registry.register_metric(custom_metric)

    def _record_success_rate(
        self,
        spec: BusinessMetricSpec,
        value: float,
        labels: dict[str, str],
        metadata: dict[str, Any] | None,
    ) -> None:
        """Record success rate metric (value should be 1 for success, 0 for failure)."""
        # Record total attempts
        self.metrics_registry.increment_counter(f"{spec.name}_total", 1, labels)

        # Record success if value indicates success
        if value > 0:
            self.metrics_registry.increment_counter(f"{spec.name}_success", 1, labels)

    def _record_latency(
        self,
        spec: BusinessMetricSpec,
        value: float,
        labels: dict[str, str],
        metadata: dict[str, Any] | None,
    ) -> None:
        """Record latency metric."""
        self.metrics_registry.observe_histogram(spec.name, value, labels)

    def _record_throughput(
        self,
        spec: BusinessMetricSpec,
        value: float,
        labels: dict[str, str],
        metadata: dict[str, Any] | None,
    ) -> None:
        """Record throughput metric."""
        self.metrics_registry.increment_counter(spec.name, value, labels)

    def _record_error_rate(
        self,
        spec: BusinessMetricSpec,
        value: float,
        labels: dict[str, str],
        metadata: dict[str, Any] | None,
    ) -> None:
        """Record error rate metric (value should be 1 for error, 0 for success)."""
        # Record total requests
        self.metrics_registry.increment_counter(f"{spec.name}_total", 1, labels)

        # Record error if value indicates error
        if value > 0:
            self.metrics_registry.increment_counter(f"{spec.name}_errors", 1, labels)

    def _record_availability(
        self,
        spec: BusinessMetricSpec,
        value: float,
        labels: dict[str, str],
        metadata: dict[str, Any] | None,
    ) -> None:
        """Record availability metric."""
        self.metrics_registry.set_gauge(spec.name, value, labels)

    def _evaluate_single_slo(
        self,
        spec: BusinessMetricSpec,
        tenant_context: TenantContext,
    ) -> SLOEvaluation | None:
        """Evaluate SLO for a single business metric."""
        # This is a simplified implementation
        # In production, you would query actual metric values from your TSDB

        # For demonstration, generate mock current value
        # In reality, this would query OTEL metrics via your backend
        import random

        is_lower_better = spec.metric_type in (
            BusinessMetricType.LATENCY,
            BusinessMetricType.ERROR_RATE,
        )

        if is_lower_better:
            # For latency/error_rate: simulate around SLO target with variation
            base_value = spec.slo_target
            variation = random.uniform(-0.02, 0.1)  # Sometimes worse latency/error_rate
            current_value = max(0.0, base_value + variation)
        else:
            # For success rates/availability: simulate around SLO target with variation
            base_value = spec.slo_target
            variation = random.uniform(-0.1, 0.05)  # Slightly pessimistic
            current_value = max(0.0, min(1.0, base_value + variation))

        # Evaluate status based on metric type
        if is_lower_better:
            # For latency/error_rate: lower is better
            is_healthy = current_value <= spec.slo_target
            is_warning = current_value > spec.alert_threshold
            is_critical = current_value > spec.critical_threshold

            # Calculate error budget consumption for latency/error_rate
            if spec.slo_target > 0:
                error_budget_consumed = max(
                    0.0, (current_value - spec.slo_target) / spec.slo_target
                )
            else:
                error_budget_consumed = 0.0
        else:
            # For success rates/availability: higher is better
            is_healthy = current_value >= spec.slo_target
            is_warning = current_value < spec.alert_threshold
            is_critical = current_value < spec.critical_threshold

            # Calculate error budget consumption for success rates/availability
            if spec.slo_target > 0:
                error_budget_consumed = max(
                    0.0, (spec.slo_target - current_value) / spec.slo_target
                )
            else:
                error_budget_consumed = 0.0

        error_budget_remaining = max(0.0, 1.0 - error_budget_consumed)

        return SLOEvaluation(
            metric_name=spec.name,
            tenant_context=tenant_context,
            current_value=current_value,
            slo_target=spec.slo_target,
            alert_threshold=spec.alert_threshold,
            critical_threshold=spec.critical_threshold,
            is_healthy=is_healthy,
            is_warning=is_warning,
            is_critical=is_critical,
            error_budget_consumed=error_budget_consumed * 100,  # Percentage
            error_budget_remaining=error_budget_remaining * 100,  # Percentage
            evaluation_window=spec.evaluation_window,
            sample_count=100,  # Mock sample count
        )

def initialize_tenant_metrics(
    service_name: str,
    metrics_registry: MetricsRegistry,
    enable_dashboards: bool = False,
    enable_slo_monitoring: bool = True,
) -> TenantMetrics:
    """
    Initialize tenant metrics manager.

    Args:
        service_name: Name of the service
        metrics_registry: Metrics registry instance
        enable_dashboards: Whether to enable dashboard provisioning
        enable_slo_monitoring: Whether to enable SLO monitoring

    Returns:
        Configured TenantMetrics instance
    """
    return TenantMetrics(
        service_name=service_name,
        metrics_registry=metrics_registry,
        enable_dashboards=enable_dashboards,
        enable_slo_monitoring=enable_slo_monitoring,
    )
