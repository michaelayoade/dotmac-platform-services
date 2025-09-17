"""
DotMac Security - Comprehensive Security Services

Unified security layer providing:
- Access control and RBAC
- Audit logging and monitoring
- Tenant isolation and multi-tenancy security
- Plugin sandboxing and validation
- Enterprise authentication integration
"""

from .access_control import (
    AccessControlEntry,
    AccessControlManager,
    AccessDecision,
    AccessRequest,
    ActionType,
    Permission,
    PermissionType,
    ResourceType,
    Role,
    check_access,
    require_permission,
)

# Audit System
from .audit import (
    AuditActor,
    AuditContext,
    AuditEvent,
    AuditEventType,
    AuditLogger,
    AuditMiddleware,
    AuditOutcome,
    AuditResource,
    AuditSeverity,
    AuditStore,
    InMemoryAuditStore,
    get_audit_logger,
    log_security_event,
    record_audit_event,
)

# Plugin Security
from .sandbox import (
    PluginPermissions,
    PluginSandbox,
    ResourceLimits,
    SecurityScanner,
    create_secure_environment,
    validate_plugin,
)

# Tenant Isolation
from .tenant_isolation import (
    RLSPolicyManager,
    TenantContext,
    TenantSecurityEnforcer,
    TenantSecurityManager,
    TenantSecurityMiddleware,
)

# Validation
from .validation import (
    SecurityValidator,
    check_sql_injection,
    check_xss,
    sanitize_data,
    validate_input,
)

__version__ = "1.0.0"

__all__ = [
    # Access Control
    "AccessControlManager",
    "Permission",
    "Role",
    "AccessControlEntry",
    "AccessRequest",
    "AccessDecision",
    "PermissionType",
    "ResourceType",
    "ActionType",
    "require_permission",
    "check_access",
    # Audit System
    "AuditLogger",
    "AuditEvent",
    "AuditActor",
    "AuditResource",
    "AuditContext",
    "AuditEventType",
    "AuditSeverity",
    "AuditOutcome",
    "AuditStore",
    "InMemoryAuditStore",
    "AuditMiddleware",
    "log_security_event",
    "get_audit_logger",
    "record_audit_event",
    # Tenant Isolation
    "TenantSecurityManager",
    "TenantSecurityEnforcer",
    "RLSPolicyManager",
    "TenantSecurityMiddleware",
    "TenantContext",
    # Plugin Security
    "PluginSandbox",
    "PluginPermissions",
    "ResourceLimits",
    "SecurityScanner",
    "validate_plugin",
    "create_secure_environment",
    # Validation
    "SecurityValidator",
    "validate_input",
    "sanitize_data",
    "check_sql_injection",
    "check_xss",
]
