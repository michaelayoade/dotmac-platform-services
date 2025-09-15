"""
Access control models and data structures.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4


class PermissionType(Enum):
    """Permission type enumeration."""

    ALLOW = "allow"
    DENY = "deny"
    CONDITIONAL = "conditional"


class ResourceType(Enum):
    """Resource type enumeration."""

    PLUGIN = "plugin"
    API = "api"
    DATA = "data"
    SYSTEM = "system"
    TENANT = "tenant"
    USER = "user"
    FILE = "file"
    NETWORK = "network"
    DATABASE = "database"


class ActionType(Enum):
    """Action type enumeration."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    MANAGE = "manage"
    INSTALL = "install"
    CONFIGURE = "configure"
    MONITOR = "monitor"


@dataclass
class Permission:
    """Individual permission definition."""

    permission_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""

    # Permission details
    resource_type: ResourceType = ResourceType.PLUGIN
    resource_id: Optional[str] = None  # Specific resource or wildcard
    action: ActionType = ActionType.READ
    permission_type: PermissionType = PermissionType.ALLOW

    # Conditions
    conditions: dict[str, Any] = field(default_factory=dict)
    time_restrictions: dict[str, Any] = field(default_factory=dict)

    # Metadata
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    # Status
    active: bool = True

    def is_expired(self) -> bool:
        """Check if permission is expired."""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def matches_resource(self, resource_type: ResourceType, resource_id: str) -> bool:
        """Check if permission matches resource."""
        if self.resource_type != resource_type:
            return False

        if self.resource_id is None or self.resource_id == "*":
            return True

        return self.resource_id == resource_id

    def evaluate_conditions(self, context: dict[str, Any]) -> bool:
        """Evaluate conditional permissions."""
        if self.permission_type != PermissionType.CONDITIONAL:
            return True

        # Evaluate time restrictions
        if self.time_restrictions:
            current_time = datetime.now(timezone.utc)

            if "start_time" in self.time_restrictions:
                start_time = datetime.fromisoformat(self.time_restrictions["start_time"])
                if current_time < start_time:
                    return False

            if "end_time" in self.time_restrictions:
                end_time = datetime.fromisoformat(self.time_restrictions["end_time"])
                if current_time > end_time:
                    return False

        # Evaluate custom conditions
        for condition_key, condition_value in self.conditions.items():
            context_value = context.get(condition_key)

            if isinstance(condition_value, dict):
                # Complex condition evaluation
                if "equals" in condition_value:
                    if context_value != condition_value["equals"]:
                        return False

                if "in" in condition_value:
                    if context_value not in condition_value["in"]:
                        return False

                if "greater_than" in condition_value:
                    if not context_value or context_value <= condition_value["greater_than"]:
                        return False
            else:
                # Simple equality check
                if context_value != condition_value:
                    return False

        return True


@dataclass
class Role:
    """Role definition with permissions."""

    role_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""

    # Role hierarchy
    parent_roles: list[str] = field(default_factory=list)
    child_roles: list[str] = field(default_factory=list)

    # Permissions
    permissions: list[str] = field(default_factory=list)  # Permission IDs

    # Scope
    tenant_scoped: bool = True
    system_role: bool = False

    # Metadata
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    active: bool = True


@dataclass
class AccessControlEntry:
    """Access control entry linking subjects to permissions."""

    ace_id: str = field(default_factory=lambda: str(uuid4()))

    # Subject (who)
    subject_type: str = ""  # "user", "group", "service", "tenant"
    subject_id: str = ""

    # Object (what)
    resource_type: ResourceType = ResourceType.PLUGIN
    resource_id: str = ""

    # Permission (how)
    permissions: list[str] = field(default_factory=list)  # Permission IDs
    roles: list[str] = field(default_factory=list)  # Role IDs

    # Grant details
    granted_by: str = ""
    granted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    # Conditions
    conditions: dict[str, Any] = field(default_factory=dict)

    # Status
    active: bool = True

    def is_expired(self) -> bool:
        """Check if ACE is expired."""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at


@dataclass
class AccessRequest:
    """Access request for permission evaluation."""

    request_id: str = field(default_factory=lambda: str(uuid4()))

    # Subject making request
    subject_type: str = ""
    subject_id: str = ""
    tenant_id: Optional[UUID] = None

    # Resource being accessed
    resource_type: ResourceType = ResourceType.PLUGIN
    resource_id: str = ""

    # Action being performed
    action: ActionType = ActionType.READ

    # Context
    context: dict[str, Any] = field(default_factory=dict)

    # Request metadata
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class AccessDecision:
    """Access control decision result."""

    request_id: str = ""
    decision: str = ""  # "allow", "deny", "error"
    reason: str = ""

    # Matched rules
    matched_permissions: list[str] = field(default_factory=list)
    matched_roles: list[str] = field(default_factory=list)
    matched_aces: list[str] = field(default_factory=list)

    # Decision metadata
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    evaluation_time_ms: float = 0.0

    # Additional info
    details: dict[str, Any] = field(default_factory=dict)
