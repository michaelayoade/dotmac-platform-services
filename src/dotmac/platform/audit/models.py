"""
Audit models and data structures for security events.
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class AuditEventType(Enum):
    """Types of security audit events that can be tracked."""

    # Authentication events
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_FAILED = "auth.failed"
    AUTH_TOKEN_REFRESH = "auth.token_refresh"
    AUTH_PASSWORD_CHANGE = "auth.password_change"
    AUTH_MFA_ENABLED = "auth.mfa_enabled"
    AUTH_MFA_DISABLED = "auth.mfa_disabled"

    # Authorization events
    AUTHZ_PERMISSION_GRANTED = "authz.permission_granted"
    AUTHZ_PERMISSION_DENIED = "authz.permission_denied"
    AUTHZ_ROLE_ASSIGNED = "authz.role_assigned"
    AUTHZ_ROLE_REMOVED = "authz.role_removed"

    # Data access events
    DATA_CREATE = "data.create"
    DATA_READ = "data.read"
    DATA_UPDATE = "data.update"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"
    DATA_IMPORT = "data.import"

    # System events
    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"
    SYSTEM_CONFIG_CHANGE = "system.config_change"
    SYSTEM_BACKUP = "system.backup"
    SYSTEM_RESTORE = "system.restore"

    # Security events
    SECURITY_INTRUSION_DETECTED = "security.intrusion_detected"
    SECURITY_VULNERABILITY_FOUND = "security.vulnerability_found"
    SECURITY_POLICY_VIOLATION = "security.policy_violation"
    SECURITY_CERTIFICATE_RENEWED = "security.certificate_renewed"
    SECURITY_ACCESS_GRANTED = "security.access_granted"
    SECURITY_ACCESS_DENIED = "security.access_denied"

    # Plugin security events
    PLUGIN_INSTALLED = "plugin.installed"
    PLUGIN_REMOVED = "plugin.removed"
    PLUGIN_SANDBOXED = "plugin.sandboxed"
    PLUGIN_SECURITY_VIOLATION = "plugin.security_violation"


class AuditSeverity(Enum):
    """Severity levels for audit events."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditOutcome(Enum):
    """Outcome of audited operations."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


@dataclass
class AuditContext:
    """Context information for audit events."""

    # Request context
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None

    # Network context
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    forwarded_for: Optional[str] = None

    # Application context
    service_name: Optional[str] = None
    service_version: Optional[str] = None
    environment: Optional[str] = None

    # Geographic context
    country: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None


@dataclass
class AuditActor:
    """Actor (user, system, or service) performing the audited action."""

    # Identity information
    actor_id: str
    actor_type: str  # user, system, service, api_key
    actor_name: Optional[str] = None

    # User-specific information
    username: Optional[str] = None
    email: Optional[str] = None
    roles: list[str] = field(default_factory=list)

    # Session information
    session_id: Optional[str] = None
    tenant_id: Optional[str] = None

    # System/service information
    service_account: Optional[str] = None
    api_key_id: Optional[str] = None


@dataclass
class AuditResource:
    """Resource being accessed or modified in the audit event."""

    # Resource identification
    resource_id: Optional[str] = None
    resource_type: str = "unknown"
    resource_name: Optional[str] = None

    # Resource metadata
    parent_resource_id: Optional[str] = None
    resource_attributes: dict[str, Any] = field(default_factory=dict)

    # Data sensitivity
    classification: Optional[str] = None  # public, internal, confidential, restricted
    contains_pii: bool = False


@dataclass
class AuditEvent:
    """Complete audit event record."""

    # Event identification
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: AuditEventType = AuditEventType.DATA_READ
    event_name: Optional[str] = None

    # Timing
    timestamp: float = field(default_factory=time.time)
    duration_ms: Optional[float] = None

    # Event details
    severity: AuditSeverity = AuditSeverity.LOW
    outcome: AuditOutcome = AuditOutcome.SUCCESS
    message: str = ""
    description: Optional[str] = None

    # Event participants
    actor: Optional[AuditActor] = None
    resource: Optional[AuditResource] = None
    context: Optional[AuditContext] = None

    # Event data
    before_state: Optional[dict[str, Any]] = None
    after_state: Optional[dict[str, Any]] = None
    changes: Optional[dict[str, Any]] = None

    # Additional metadata
    tags: dict[str, str] = field(default_factory=dict)
    custom_attributes: dict[str, Any] = field(default_factory=dict)

    # Risk and compliance
    risk_score: Optional[int] = None  # 0-100
    compliance_frameworks: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Post-initialization processing."""
        if not self.event_name:
            self.event_name = self.event_type.value

    def to_dict(self) -> dict[str, Any]:
        """Convert audit event to dictionary for storage/transmission."""

        def serialize_dataclass(obj):
            if hasattr(obj, "__dataclass_fields__"):
                return {k: serialize_dataclass(v) for k, v in obj.__dict__.items() if v is not None}
            elif isinstance(obj, Enum):
                return obj.value
            elif isinstance(obj, list):
                return [serialize_dataclass(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: serialize_dataclass(v) for k, v in obj.items()}
            else:
                return obj

        return serialize_dataclass(self)

    def to_json(self) -> str:
        """Convert audit event to JSON string."""
        return json.dumps(self.to_dict(), default=str, separators=(",", ":"))
