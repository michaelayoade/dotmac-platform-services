"""
SSH automation types and data structures.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Optional


class ConnectionStatus(str, Enum):
    """SSH connection status."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    TIMEOUT = "timeout"


class DeviceType(str, Enum):
    """Network device types."""

    ROUTER = "router"
    SWITCH = "switch"
    FIREWALL = "firewall"
    ACCESS_POINT = "access_point"
    OLT = "olt"
    ONU = "onu"
    SERVER = "server"
    UNKNOWN = "unknown"


class ProvisioningStatus(str, Enum):
    """Device provisioning status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLBACK = "rollback"
    ROLLBACK_COMPLETED = "rollback_completed"


class CommandType(str, Enum):
    """SSH command types."""

    SHOW = "show"
    CONFIG = "config"
    EXEC = "exec"
    INTERACTIVE = "interactive"


@dataclass
class DeviceCredentials:
    """Device authentication credentials."""

    username: str
    password: Optional[str] = None
    private_key: Optional[str] = None
    private_key_path: Optional[str] = None
    passphrase: Optional[str] = None
    enable_password: Optional[str] = None

    def has_key_auth(self) -> bool:
        """Check if key-based authentication is configured."""
        return bool(self.private_key or self.private_key_path)

    def has_password_auth(self) -> bool:
        """Check if password authentication is configured."""
        return bool(self.password)


@dataclass
class SSHConnectionConfig:
    """SSH connection configuration."""

    host: str
    port: int = 22
    timeout: int = 30
    keepalive: int = 60
    max_retries: int = 3
    retry_delay: int = 5
    use_agent: bool = True
    compression: bool = True
    banner_timeout: int = 15
    auth_timeout: int = 10
    channel_timeout: int = 10


@dataclass
class SSHCommand:
    """SSH command specification."""

    command: str
    command_type: CommandType = CommandType.EXEC
    timeout: int = 30
    expect_prompt: Optional[str] = None
    strip_prompt: bool = True
    strip_command: bool = True
    normalize: bool = True
    use_textfsm: bool = False
    textfsm_template: Optional[str] = None
    delay_factor: float = 1.0
    max_loops: int = 500

    def __post_init__(self):
        """Validate command after initialization."""
        if not self.command.strip():
            raise ValueError("Command cannot be empty")


@dataclass
class SSHResponse:
    """SSH command response."""

    command: str
    output: str
    success: bool
    error_message: Optional[str] = None
    execution_time: float = 0.0
    exit_code: Optional[int] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    structured_output: Optional[dict[str, Any]] = None

    @property
    def lines(self) -> list[str]:
        """Get output as list of lines."""
        return self.output.splitlines() if self.output else []

    def to_dict(self) -> dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "command": self.command,
            "output": self.output,
            "success": self.success,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "exit_code": self.exit_code,
            "timestamp": self.timestamp.isoformat(),
            "structured_output": self.structured_output,
        }


@dataclass
class SSHConnection:
    """SSH connection information."""

    connection_id: str
    host: str
    port: int
    username: str
    device_type: DeviceType = DeviceType.UNKNOWN
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_used: datetime = field(default_factory=lambda: datetime.now(UTC))
    connection_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def update_last_used(self):
        """Update last used timestamp."""
        self.last_used = datetime.now(UTC)
        self.connection_count += 1

    def record_error(self, error: str):
        """Record connection error."""
        self.error_count += 1
        self.last_error = error
        self.status = ConnectionStatus.ERROR


@dataclass
class ProvisioningStep:
    """Individual provisioning step."""

    name: str
    command: SSHCommand
    required: bool = True
    rollback_command: Optional[SSHCommand] = None
    condition: Optional[Callable[[SSHResponse], bool]] = None
    retry_count: int = 0
    description: str = ""


@dataclass
class ProvisioningTemplate:
    """Device provisioning template."""

    name: str
    device_type: DeviceType
    description: str = ""
    version: str = "1.0"
    steps: list[ProvisioningStep] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    requirements: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def add_step(self, step: ProvisioningStep):
        """Add provisioning step."""
        self.steps.append(step)

    def get_step(self, name: str) -> Optional[ProvisioningStep]:
        """Get step by name."""
        for step in self.steps:
            if step.name == name:
                return step
        return None

    def render_template(self, variables: dict[str, Any]) -> "ProvisioningTemplate":
        """Render template with variables."""
        # This would implement Jinja2 template rendering
        # For now, return copy with merged variables
        rendered = ProvisioningTemplate(
            name=self.name,
            device_type=self.device_type,
            description=self.description,
            version=self.version,
            steps=self.steps.copy(),
            variables={**self.variables, **variables},
            requirements=self.requirements.copy(),
            tags=self.tags.copy(),
        )
        return rendered


@dataclass
class DeviceConfig:
    """Device configuration specification."""

    device_id: str
    hostname: str
    ip_address: str
    device_type: DeviceType
    credentials: DeviceCredentials
    connection_config: SSHConnectionConfig = field(default_factory=SSHConnectionConfig)
    vendor: str = ""
    model: str = ""
    os_version: str = ""
    management_vlan: Optional[int] = None
    location: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def connection_string(self) -> str:
        """Get connection string representation."""
        return f"{self.credentials.username}@{self.ip_address}:{self.connection_config.port}"


@dataclass
class ProvisioningJob:
    """Device provisioning job."""

    job_id: str
    device_config: DeviceConfig
    template: ProvisioningTemplate
    status: ProvisioningStatus = ProvisioningStatus.PENDING
    current_step: Optional[str] = None
    completed_steps: list[str] = field(default_factory=list)
    failed_steps: list[str] = field(default_factory=list)
    step_results: dict[str, SSHResponse] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def mark_started(self):
        """Mark job as started."""
        self.status = ProvisioningStatus.IN_PROGRESS
        self.started_at = datetime.now(UTC)

    def mark_completed(self):
        """Mark job as completed."""
        self.status = ProvisioningStatus.COMPLETED
        self.completed_at = datetime.now(UTC)

    def mark_failed(self, error: str):
        """Mark job as failed."""
        self.status = ProvisioningStatus.FAILED
        self.completed_at = datetime.now(UTC)
        self.error_message = error

    def add_step_result(self, step_name: str, result: SSHResponse):
        """Add step execution result."""
        self.step_results[step_name] = result
        if result.success:
            if step_name not in self.completed_steps:
                self.completed_steps.append(step_name)
        else:
            if step_name not in self.failed_steps:
                self.failed_steps.append(step_name)

    @property
    def progress_percentage(self) -> float:
        """Get job progress percentage."""
        if not self.template.steps:
            return 0.0
        return (len(self.completed_steps) / len(self.template.steps)) * 100


@dataclass
class SSHPoolConfig:
    """SSH connection pool configuration."""

    max_connections: int = 10
    idle_timeout: int = 300  # 5 minutes
    cleanup_interval: int = 60  # 1 minute
    max_connection_age: int = 3600  # 1 hour
    connection_timeout: int = 30
    enable_keepalive: bool = True
    keepalive_interval: int = 60


class SSHException(Exception):
    """Base SSH exception."""


class SSHConnectionError(SSHException):
    """SSH connection error."""

    def __init__(self, host: str, port: int, message: str):
        self.host = host
        self.port = port
        self.message = message
        super().__init__(f"SSH connection to {host}:{port} failed: {message}")


class SSHAuthenticationError(SSHException):
    """SSH authentication error."""

    def __init__(
        self, host: str, username: str, message: str = "Authentication failed"
    ):
        self.host = host
        self.username = username
        self.message = message
        super().__init__(f"SSH authentication for {username}@{host} failed: {message}")


class SSHCommandError(SSHException):
    """SSH command execution error."""

    def __init__(self, command: str, message: str, output: str = ""):
        self.command = command
        self.message = message
        self.output = output
        super().__init__(f"SSH command '{command}' failed: {message}")


class SSHTimeoutError(SSHException):
    """SSH operation timeout."""

    def __init__(self, operation: str, timeout: int):
        self.operation = operation
        self.timeout = timeout
        super().__init__(f"SSH {operation} timed out after {timeout} seconds")


class ProvisioningError(SSHException):
    """Device provisioning error."""

    def __init__(self, job_id: str, step_name: str, message: str):
        self.job_id = job_id
        self.step_name = step_name
        self.message = message
        super().__init__(
            f"Provisioning job {job_id} failed at step '{step_name}': {message}"
        )
