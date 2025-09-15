"""
VOLTHA types and data structures for fiber network management.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, IntEnum
from typing import Any, Optional
from uuid import uuid4


class DeviceStatus(str, Enum):
    """Device operational status."""

    UNKNOWN = "unknown"
    PREPROVISIONED = "preprovisioned"
    ENABLED = "enabled"
    DISABLED = "disabled"
    DELETED = "deleted"


class DeviceType(str, Enum):
    """VOLTHA device types."""

    OLT = "olt"
    ONU = "onu"
    LOGICAL_DEVICE = "logical_device"


class AdminState(str, Enum):
    """Administrative state of device."""

    UNKNOWN = "unknown"
    PREPROVISIONED = "preprovisioned"
    ENABLED = "enabled"
    DISABLED = "disabled"
    DOWNLOADING_IMAGE = "downloading_image"
    DELETED = "deleted"


class OperStatus(str, Enum):
    """Operational status of device."""

    UNKNOWN = "unknown"
    DISCOVERED = "discovered"
    ACTIVATING = "activating"
    TESTING = "testing"
    ACTIVE = "active"
    FAILED = "failed"


class ConnectStatus(str, Enum):
    """Connection status of device."""

    UNKNOWN = "unknown"
    UNREACHABLE = "unreachable"
    REACHABLE = "reachable"


class PortType(IntEnum):
    """Port types."""

    UNKNOWN = 0
    ETHERNET_NNI = 1
    ETHERNET_UNI = 2
    PON_OLT = 3
    PON_ONU = 4
    VENET_OLT = 5
    VENET_ONU = 6


class FlowDirection(str, Enum):
    """Flow direction."""

    UPSTREAM = "upstream"
    DOWNSTREAM = "downstream"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class VOLTHAPort:
    """VOLTHA port information."""

    port_no: int
    label: str
    type: PortType
    admin_state: AdminState = AdminState.UNKNOWN
    oper_status: OperStatus = OperStatus.UNKNOWN
    device_id: str = ""
    peers: list[dict[str, Any]] = field(default_factory=list)
    rx_packets: int = 0
    rx_bytes: int = 0
    rx_errors: int = 0
    tx_packets: int = 0
    tx_bytes: int = 0
    tx_errors: int = 0


@dataclass
class VOLTHAFlow:
    """VOLTHA flow configuration."""

    id: str = field(default_factory=lambda: str(uuid4()))
    device_id: str = ""
    flow_id: int = 0
    table_id: int = 0
    priority: int = 1000
    match_fields: dict[str, Any] = field(default_factory=dict)
    instructions: list[dict[str, Any]] = field(default_factory=list)
    flags: int = 0
    cookie: int = 0
    direction: FlowDirection = FlowDirection.DOWNSTREAM


@dataclass
class VOLTHADevice:
    """Base VOLTHA device."""

    id: str = field(default_factory=lambda: str(uuid4()))
    type: str = ""
    vendor: str = ""
    model: str = ""
    hardware_version: str = ""
    firmware_version: str = ""
    software_version: str = ""
    serial_number: str = ""
    mac_address: str = ""
    ipv4_address: str = ""
    host_and_port: str = ""
    admin_state: AdminState = AdminState.UNKNOWN
    oper_status: OperStatus = OperStatus.UNKNOWN
    connect_status: ConnectStatus = ConnectStatus.UNKNOWN
    reason: str = ""
    parent_id: str = ""
    parent_port_no: int = 0
    vendor_id: str = ""
    proxy_address: dict[str, Any] = field(default_factory=dict)
    ports: list[VOLTHAPort] = field(default_factory=list)
    flows: list[VOLTHAFlow] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class OLTDevice(VOLTHADevice):
    """Optical Line Terminal (OLT) device."""

    device_type: str = field(default="olt", init=False)
    dp_id: int = 0
    expected_onu_count: int = 0
    actual_onu_count: int = 0
    pon_ports: list[int] = field(default_factory=list)
    nni_ports: list[int] = field(default_factory=list)

    def get_pon_port_count(self) -> int:
        """Get number of PON ports."""
        return len([p for p in self.ports if p.type == PortType.PON_OLT])

    def get_nni_port_count(self) -> int:
        """Get number of NNI ports."""
        return len([p for p in self.ports if p.type == PortType.ETHERNET_NNI])


@dataclass
class ONUDevice(VOLTHADevice):
    """Optical Network Unit (ONU) device."""

    device_type: str = field(default="onu", init=False)
    olt_device_id: str = ""
    pon_port_no: int = 0
    onu_id: int = 0
    uni_ports: list[int] = field(default_factory=list)
    allocated_bandwidth_upstream: int = 0
    allocated_bandwidth_downstream: int = 0
    service_ports: list[dict[str, Any]] = field(default_factory=list)

    def get_uni_port_count(self) -> int:
        """Get number of UNI ports."""
        return len([p for p in self.ports if p.type == PortType.ETHERNET_UNI])


@dataclass
class VOLTHAAlarm:
    """VOLTHA alarm information."""

    id: str = field(default_factory=lambda: str(uuid4()))
    type: str = ""
    category: str = ""
    severity: str = ""
    state: str = ""
    description: str = ""
    device_id: str = ""
    logical_device_id: str = ""
    raised_ts: datetime = field(default_factory=lambda: datetime.now(UTC))
    changed_ts: datetime = field(default_factory=lambda: datetime.now(UTC))
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class VOLTHAEvent:
    """VOLTHA event information."""

    id: str = field(default_factory=lambda: str(uuid4()))
    type: str = ""
    category: str = ""
    sub_category: str = ""
    description: str = ""
    device_id: str = ""
    raised_ts: datetime = field(default_factory=lambda: datetime.now(UTC))
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class VOLTHAResponse:
    """VOLTHA operation response."""

    success: bool
    message: str
    data: Optional[Any] = None
    error_code: Optional[str] = None
    device_id: Optional[str] = None

    @classmethod
    def success_response(
        cls, message: str, data: Any = None, device_id: Optional[str] = None
    ) -> "VOLTHAResponse":
        """Create successful response."""
        return cls(success=True, message=message, data=data, device_id=device_id)

    @classmethod
    def error_response(
        cls, message: str, error_code: str, device_id: Optional[str] = None
    ) -> "VOLTHAResponse":
        """Create error response."""
        return cls(
            success=False, message=message, error_code=error_code, device_id=device_id
        )


@dataclass
class VOLTHAConfig:
    """VOLTHA configuration."""

    core_endpoint: str = "localhost:50057"
    ofagent_endpoint: str = "localhost:6653"
    kafka_endpoint: str = "localhost:9092"
    etcd_endpoint: str = "localhost:2379"
    timeout: int = 30
    retry_count: int = 3
    enable_tls: bool = False
    ca_cert_file: Optional[str] = None
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    log_level: str = "INFO"


class VOLTHAException(Exception):
    """Base VOLTHA exception."""


class VOLTHAConnectionError(VOLTHAException):
    """VOLTHA connection error."""


class VOLTHADeviceError(VOLTHAException):
    """VOLTHA device operation error."""

    def __init__(self, device_id: str, message: str):
        self.device_id = device_id
        self.message = message
        super().__init__(f"Device {device_id}: {message}")


class VOLTHAFlowError(VOLTHAException):
    """VOLTHA flow operation error."""


class VOLTHATimeoutError(VOLTHAException):
    """VOLTHA operation timeout."""
