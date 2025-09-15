"""
Network monitoring types and data structures.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Optional, Union


class HealthStatus(str, Enum):
    """Health check status."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class MetricType(str, Enum):
    """Metric data types."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MonitoringProtocol(str, Enum):
    """Monitoring protocols."""

    SNMP = "snmp"
    SSH = "ssh"
    HTTP = "http"
    HTTPS = "https"
    ICMP = "icmp"
    TCP = "tcp"
    UDP = "udp"


class CheckType(str, Enum):
    """Health check types."""

    PING = "ping"
    PORT = "port"
    SERVICE = "service"
    RESOURCE = "resource"
    CUSTOM = "custom"


@dataclass
class MonitoringTarget:
    """Monitoring target specification."""

    id: str
    name: str
    host: str
    device_type: str = "unknown"
    protocols: list[MonitoringProtocol] = field(default_factory=list)
    tags: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    check_interval: int = 60  # seconds
    timeout: int = 30
    retry_count: int = 3

    def has_protocol(self, protocol: MonitoringProtocol) -> bool:
        """Check if target supports protocol."""
        return protocol in self.protocols


@dataclass
class SNMPConfig:
    """SNMP configuration."""

    community: str = "public"
    version: str = "2c"  # 1, 2c, 3
    port: int = 161
    timeout: int = 5
    retries: int = 3
    # SNMPv3 specific
    username: Optional[str] = None
    auth_protocol: Optional[str] = None  # MD5, SHA
    auth_password: Optional[str] = None
    priv_protocol: Optional[str] = None  # DES, AES
    priv_password: Optional[str] = None


@dataclass
class MonitoringConfig:
    """Monitoring system configuration."""

    check_interval: int = 60
    alert_check_interval: int = 30
    metric_retention: int = 86400  # 24 hours
    max_concurrent_checks: int = 50
    enable_alerting: bool = True
    enable_metrics: bool = True
    enable_health_checks: bool = True
    log_level: str = "INFO"


@dataclass
class Metric:
    """Individual metric data point."""

    name: str
    value: Union[int, float]
    metric_type: MetricType
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    tags: dict[str, str] = field(default_factory=dict)
    unit: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert metric to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "type": self.metric_type.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "unit": self.unit,
            "description": self.description,
        }


@dataclass
class DeviceMetrics:
    """Device metrics collection."""

    device_id: str
    device_name: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Network metrics
    interfaces: list[dict[str, Any]] = field(default_factory=list)
    bandwidth_utilization: dict[str, float] = field(default_factory=dict)
    packet_counts: dict[str, int] = field(default_factory=dict)
    error_counts: dict[str, int] = field(default_factory=dict)

    # System metrics
    cpu_utilization: Optional[float] = None
    memory_utilization: Optional[float] = None
    temperature: Optional[float] = None
    power_consumption: Optional[float] = None

    # Custom metrics
    custom_metrics: list[Metric] = field(default_factory=list)

    def add_metric(self, metric: Metric):
        """Add custom metric."""
        self.custom_metrics.append(metric)

    def get_interface_metric(
        self, interface_name: str, metric_name: str
    ) -> Optional[Any]:
        """Get specific interface metric."""
        for interface in self.interfaces:
            if interface.get("name") == interface_name:
                return interface.get(metric_name)
        return None


@dataclass
class HealthCheck:
    """Health check specification."""

    name: str
    check_type: CheckType
    target: str
    enabled: bool = True
    interval: int = 60
    timeout: int = 30
    retries: int = 3
    parameters: dict[str, Any] = field(default_factory=dict)

    # Thresholds
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None

    # Custom check function
    custom_check: Optional[Callable] = None

    def __post_init__(self):
        """Validate health check configuration."""
        if self.check_type == CheckType.CUSTOM and not self.custom_check:
            raise ValueError("Custom health check requires custom_check function")


@dataclass
class HealthCheckResult:
    """Health check execution result."""

    check_name: str
    target: str
    status: HealthStatus
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    execution_time: float = 0.0
    metrics: dict[str, Any] = field(default_factory=dict)
    error_details: Optional[str] = None

    def is_healthy(self) -> bool:
        """Check if result indicates healthy state."""
        return self.status == HealthStatus.HEALTHY

    def is_critical(self) -> bool:
        """Check if result indicates critical state."""
        return self.status == HealthStatus.CRITICAL

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "check_name": self.check_name,
            "target": self.target,
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "execution_time": self.execution_time,
            "metrics": self.metrics,
            "error_details": self.error_details,
        }


@dataclass
class AlertRule:
    """Alert rule configuration."""

    name: str
    description: str
    condition: str  # Expression to evaluate
    severity: AlertSeverity
    enabled: bool = True

    # Evaluation
    evaluation_interval: int = 60
    evaluation_window: int = 300  # 5 minutes

    # Actions
    notification_channels: list[str] = field(default_factory=list)
    auto_resolve: bool = True
    auto_resolve_timeout: int = 300

    # Metadata
    tags: dict[str, str] = field(default_factory=dict)
    runbook_url: Optional[str] = None

    def evaluate(self, metrics: dict[str, Any]) -> bool:
        """Evaluate alert condition against metrics."""
        # This would implement expression evaluation
        # For now, return False as placeholder
        return False


@dataclass
class Alert:
    """Active alert."""

    id: str
    rule_name: str
    target: str
    severity: AlertSeverity
    message: str
    status: str = "firing"  # firing, resolved

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    resolved_at: Optional[datetime] = None

    # Context
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)

    # Escalation
    escalation_level: int = 0
    notification_sent: bool = False

    def resolve(self):
        """Mark alert as resolved."""
        self.status = "resolved"
        self.resolved_at = datetime.now(UTC)
        self.updated_at = self.resolved_at

    def escalate(self):
        """Escalate alert severity."""
        self.escalation_level += 1
        self.updated_at = datetime.now(UTC)

    @property
    def duration(self) -> float:
        """Get alert duration in seconds."""
        end_time = self.resolved_at or datetime.now(UTC)
        return (end_time - self.created_at).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "id": self.id,
            "rule_name": self.rule_name,
            "target": self.target,
            "severity": self.severity.value,
            "message": self.message,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "duration": self.duration,
            "labels": self.labels,
            "annotations": self.annotations,
            "escalation_level": self.escalation_level,
        }


@dataclass
class NetworkTopology:
    """Network topology information."""

    devices: dict[str, dict[str, Any]] = field(default_factory=dict)
    connections: list[dict[str, Any]] = field(default_factory=list)
    subnets: list[dict[str, Any]] = field(default_factory=list)
    discovered_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def add_device(self, device_id: str, device_info: dict[str, Any]):
        """Add device to topology."""
        self.devices[device_id] = device_info

    def add_connection(
        self,
        source: str,
        target: str,
        connection_type: str,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """Add connection between devices."""
        connection = {
            "source": source,
            "target": target,
            "type": connection_type,
            "metadata": metadata or {},
        }
        self.connections.append(connection)

    def get_device_connections(self, device_id: str) -> list[dict[str, Any]]:
        """Get all connections for a device."""
        connections = []
        for conn in self.connections:
            if conn["source"] == device_id or conn["target"] == device_id:
                connections.append(conn)
        return connections


class MonitoringException(Exception):
    """Base monitoring exception."""


class HealthCheckError(MonitoringException):
    """Health check execution error."""

    def __init__(self, check_name: str, target: str, message: str):
        self.check_name = check_name
        self.target = target
        self.message = message
        super().__init__(f"Health check '{check_name}' failed for {target}: {message}")


class MetricCollectionError(MonitoringException):
    """Metric collection error."""

    def __init__(self, target: str, metric_name: str, message: str):
        self.target = target
        self.metric_name = metric_name
        self.message = message
        super().__init__(
            f"Metric collection failed for {target}.{metric_name}: {message}"
        )


class SNMPError(MonitoringException):
    """SNMP operation error."""

    def __init__(self, host: str, oid: str, message: str):
        self.host = host
        self.oid = oid
        self.message = message
        super().__init__(f"SNMP error for {host} OID {oid}: {message}")


class AlertingError(MonitoringException):
    """Alerting system error."""
