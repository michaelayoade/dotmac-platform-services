"""
RADIUS protocol types and data structures.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, IntEnum
from typing import Any, Optional, Union
from uuid import uuid4


class RADIUSPacketType(IntEnum):
    """RADIUS packet types according to RFC 2865."""

    ACCESS_REQUEST = 1
    ACCESS_ACCEPT = 2
    ACCESS_REJECT = 3
    ACCOUNTING_REQUEST = 4
    ACCOUNTING_RESPONSE = 5
    ACCESS_CHALLENGE = 11
    STATUS_SERVER = 12
    STATUS_CLIENT = 13
    DISCONNECT_REQUEST = 40  # RFC 3576 (CoA)
    DISCONNECT_ACK = 41
    DISCONNECT_NAK = 42
    COA_REQUEST = 43
    COA_ACK = 44
    COA_NAK = 45


class RADIUSAttributeType(IntEnum):
    """Standard RADIUS attributes according to RFC 2865."""

    USER_NAME = 1
    USER_PASSWORD = 2
    CHAP_PASSWORD = 3
    NAS_IP_ADDRESS = 4
    NAS_PORT = 5
    SERVICE_TYPE = 6
    FRAMED_PROTOCOL = 7
    FRAMED_IP_ADDRESS = 8
    FRAMED_IP_NETMASK = 9
    FRAMED_ROUTING = 10
    FILTER_ID = 11
    FRAMED_MTU = 12
    FRAMED_COMPRESSION = 13
    LOGIN_IP_HOST = 14
    LOGIN_SERVICE = 15
    LOGIN_TCP_PORT = 16
    REPLY_MESSAGE = 18
    CALLBACK_NUMBER = 19
    CALLBACK_ID = 20
    FRAMED_ROUTE = 22
    FRAMED_IPX_NETWORK = 23
    STATE = 24
    CLASS = 25
    VENDOR_SPECIFIC = 26
    SESSION_TIMEOUT = 27
    IDLE_TIMEOUT = 28
    TERMINATION_ACTION = 29
    CALLED_STATION_ID = 30
    CALLING_STATION_ID = 31
    NAS_IDENTIFIER = 32
    PROXY_STATE = 33
    LOGIN_LAT_SERVICE = 34
    LOGIN_LAT_NODE = 35
    LOGIN_LAT_GROUP = 36
    FRAMED_APPLETALK_LINK = 37
    FRAMED_APPLETALK_NETWORK = 38
    FRAMED_APPLETALK_ZONE = 39
    ACCT_STATUS_TYPE = 40
    ACCT_DELAY_TIME = 41
    ACCT_INPUT_OCTETS = 42
    ACCT_OUTPUT_OCTETS = 43
    ACCT_SESSION_ID = 44
    ACCT_AUTHENTIC = 45
    ACCT_SESSION_TIME = 46
    ACCT_INPUT_PACKETS = 47
    ACCT_OUTPUT_PACKETS = 48
    ACCT_TERMINATE_CAUSE = 49
    ACCT_MULTI_SESSION_ID = 50
    ACCT_LINK_COUNT = 51
    ACCT_INPUT_GIGAWORDS = 52
    ACCT_OUTPUT_GIGAWORDS = 53
    EVENT_TIMESTAMP = 55
    EGRESS_VLANID = 56
    INGRESS_FILTERS = 57
    EGRESS_VLAN_NAME = 58
    USER_PRIORITY_TABLE = 59
    CHAP_CHALLENGE = 60
    NAS_PORT_TYPE = 61
    PORT_LIMIT = 62
    LOGIN_LAT_PORT = 63


class RADIUSServiceType(IntEnum):
    """RADIUS Service-Type attribute values."""

    LOGIN = 1
    FRAMED = 2
    CALLBACK_LOGIN = 3
    CALLBACK_FRAMED = 4
    OUTBOUND = 5
    ADMINISTRATIVE = 6
    NAS_PROMPT = 7
    AUTHENTICATE_ONLY = 8
    CALLBACK_NAS_PROMPT = 9
    CALL_CHECK = 10
    CALLBACK_ADMINISTRATIVE = 11


class RADIUSSessionStatus(str, Enum):
    """RADIUS session status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    TERMINATED = "terminated"


class AcctStatusType(IntEnum):
    """Accounting Status-Type values."""

    START = 1
    STOP = 2
    INTERIM_UPDATE = 3
    ACCOUNTING_ON = 7
    ACCOUNTING_OFF = 8


class AcctTerminateCause(IntEnum):
    """Accounting Terminate-Cause values."""

    USER_REQUEST = 1
    LOST_CARRIER = 2
    LOST_SERVICE = 3
    IDLE_TIMEOUT = 4
    SESSION_TIMEOUT = 5
    ADMIN_RESET = 6
    ADMIN_REBOOT = 7
    PORT_ERROR = 8
    NAS_ERROR = 9
    NAS_REQUEST = 10
    NAS_REBOOT = 11
    PORT_UNNEEDED = 12
    PORT_PREEMPTED = 13
    PORT_SUSPENDED = 14
    SERVICE_UNAVAILABLE = 15
    CALLBACK = 16
    USER_ERROR = 17
    HOST_REQUEST = 18


@dataclass
class RADIUSAttribute:
    """RADIUS attribute container."""

    type: Union[RADIUSAttributeType, int]
    value: Union[str, int, bytes]
    vendor_id: Optional[int] = None

    def __post_init__(self):
        """Validate attribute after initialization."""
        if isinstance(self.type, int) and self.type not in RADIUSAttributeType:
            # Allow unknown attribute types for vendor-specific attributes
            pass


@dataclass
class RADIUSPacket:
    """RADIUS packet container."""

    packet_type: RADIUSPacketType
    packet_id: int
    authenticator: bytes
    attributes: list[RADIUSAttribute] = field(default_factory=list)

    def get_attribute(
        self, attr_type: Union[RADIUSAttributeType, int]
    ) -> Optional[RADIUSAttribute]:
        """Get first attribute of specified type."""
        for attr in self.attributes:
            if attr.type == attr_type:
                return attr
        return None

    def get_attributes(
        self, attr_type: Union[RADIUSAttributeType, int]
    ) -> list[RADIUSAttribute]:
        """Get all attributes of specified type."""
        return [attr for attr in self.attributes if attr.type == attr_type]

    def add_attribute(
        self,
        attr_type: Union[RADIUSAttributeType, int],
        value: Any,
        vendor_id: Optional[int] = None,
    ):
        """Add attribute to packet."""
        self.attributes.append(RADIUSAttribute(attr_type, value, vendor_id))


@dataclass
class RADIUSResponse:
    """RADIUS operation response."""

    success: bool
    message: str
    packet: Optional[RADIUSPacket] = None
    attributes: dict[str, Any] = field(default_factory=dict)
    error_code: Optional[str] = None

    @classmethod
    def success_response(
        cls, message: str, packet: Optional[RADIUSPacket] = None, **attributes
    ) -> "RADIUSResponse":
        """Create successful response."""
        return cls(success=True, message=message, packet=packet, attributes=attributes)

    @classmethod
    def error_response(
        cls, message: str, error_code: str, packet: Optional[RADIUSPacket] = None
    ) -> "RADIUSResponse":
        """Create error response."""
        return cls(success=False, message=message, packet=packet, error_code=error_code)


@dataclass
class RADIUSUser:
    """RADIUS user account information."""

    username: str
    password: Optional[str] = None
    password_hash: Optional[str] = None
    is_active: bool = True
    groups: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def check_password(self, password: str) -> bool:
        """Check if provided password is correct."""
        if self.password:
            return self.password == password
        # In production, implement proper password hashing verification
        return False


@dataclass
class RADIUSSession:
    """Active RADIUS session information."""

    session_id: str = field(default_factory=lambda: str(uuid4()))
    username: str = ""
    nas_ip: str = ""
    nas_port: Optional[int] = None
    nas_port_type: Optional[int] = None
    calling_station_id: str = ""
    called_station_id: str = ""
    framed_ip: Optional[str] = None
    framed_netmask: Optional[str] = None
    service_type: Optional[RADIUSServiceType] = None
    session_timeout: Optional[int] = None
    idle_timeout: Optional[int] = None
    status: RADIUSSessionStatus = RADIUSSessionStatus.PENDING
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_update: datetime = field(default_factory=lambda: datetime.now(UTC))
    input_octets: int = 0
    output_octets: int = 0
    input_packets: int = 0
    output_packets: int = 0
    session_time: int = 0
    terminate_cause: Optional[AcctTerminateCause] = None

    def update_accounting(
        self,
        input_octets: int = 0,
        output_octets: int = 0,
        input_packets: int = 0,
        output_packets: int = 0,
    ):
        """Update session accounting information."""
        self.input_octets += input_octets
        self.output_octets += output_octets
        self.input_packets += input_packets
        self.output_packets += output_packets
        self.last_update = datetime.now(UTC)
        self.session_time = int((self.last_update - self.start_time).total_seconds())


@dataclass
class RADIUSClient:
    """RADIUS client (NAS) configuration."""

    name: str
    ip_address: str
    shared_secret: str
    nas_type: str = "other"
    ports: int = 0
    vendor: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class RADIUSServerConfig:
    """RADIUS server configuration."""

    auth_port: int = 1812
    acct_port: int = 1813
    coa_port: int = 3799
    bind_address: str = "0.0.0.0"  # nosec B104 - RADIUS servers need to bind to all interfaces
    max_packet_size: int = 4096
    timeout: int = 5
    retries: int = 3
    default_secret: str = "testing123"
    enable_coa: bool = True
    enable_accounting: bool = True
    log_level: str = "INFO"


class RADIUSException(Exception):
    """Base RADIUS exception."""


class RADIUSAuthenticationError(RADIUSException):
    """RADIUS authentication failed."""

    def __init__(self, username: str, reason: str = "Authentication failed"):
        self.username = username
        self.reason = reason
        super().__init__(
            f"RADIUS authentication failed for user '{username}': {reason}"
        )


class RADIUSAuthorizationError(RADIUSException):
    """RADIUS authorization failed."""


class RADIUSAccountingError(RADIUSException):
    """RADIUS accounting error."""


class RADIUSCoAError(RADIUSException):
    """RADIUS CoA (Change of Authorization) error."""


class RADIUSTimeoutError(RADIUSException):
    """RADIUS request timeout."""
