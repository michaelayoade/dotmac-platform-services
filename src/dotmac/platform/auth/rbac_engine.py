"""
Simplified RBAC Engine using Casbin

Industry-standard RBAC/ABAC implementation using Casbin for:
- Role-based access control
- Resource permissions
- Multi-tenant support
- Dynamic policy evaluation
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional, cast

import casbin
from casbin_sqlalchemy_adapter import Adapter
from pydantic import BaseModel

from dotmac.platform.logging import get_logger

logger = get_logger(__name__)


# Compatibility enums from original implementation
class Action(str, Enum):
    """Common action enumerations."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    WRITE = "write"
    DELETE = "delete"
    LIST = "list"
    EXECUTE = "execute"
    ALL = "*"


class Resource(str, Enum):
    """Common resource enumerations."""

    USER = "user"
    TENANT = "tenant"
    SERVICE = "service"
    API_KEY = "api_key"
    ROLE = "role"
    PERMISSION = "permission"
    SESSION = "session"
    BILLING = "billing"
    ANALYTICS = "analytics"
    SYSTEM = "system"
    DOCUMENT = "document"
    ALL = "*"


class PolicyEffect(str, Enum):
    """Effect of a policy rule."""

    ALLOW = "allow"
    DENY = "deny"


# Backward-compat enums
class PermissionType(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    EXECUTE = "execute"
    MANAGE = "manage"


class ResourceType(str, Enum):
    USER = "user"
    TENANT = "tenant"
    SERVICE = "service"
    API_KEY = "api_key"
    ROLE = "role"
    PERMISSION = "permission"
    BILLING = "billing"
    ANALYTICS = "analytics"
    SYSTEM = "system"
    DOCUMENT = "document"
    ALL = "*"


@dataclass
class Permission:
    """Represents a single permission."""

    action: str
    resource: str
    conditions: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Normalize permission values."""
        self.action = getattr(self.action, "value", self.action).lower()
        self.resource = getattr(self.resource, "value", self.resource).lower()
        if self.conditions is None:
            self.conditions = {}

    def matches(self, required_action: str, required_resource: str) -> bool:
        """Check if this permission matches requirements."""
        if not required_action or not required_resource:
            return False

        action_match = (
            self.action == "*"
            or self.action == "all"  # Support "all" as wildcard
            or self.action == required_action.lower()
            or required_action == "*"
        )

        resource_match = (
            self.resource == "*"
            or self.resource == "all"  # Support "all" as wildcard
            or self.resource == required_resource.lower()
            or required_resource == "*"
        )

        return action_match and resource_match

    def to_string(self) -> str:
        """Convert to string format."""
        return f"{self.action}:{self.resource}"

    @classmethod
    def from_string(cls, permission_str: str) -> "Permission":
        """Create from string format."""
        parts = permission_str.split(":", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid permission format: {permission_str}")
        return cls(action=parts[0], resource=parts[1])


@dataclass
class Role:
    """Represents a role with permissions."""

    name: str
    permissions: list[Permission] | None = None
    parent_roles: list[str] | None = None
    description: str = ""
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Initialize role fields."""
        if self.permissions is None:
            self.permissions = []
        if self.parent_roles is None:
            self.parent_roles = []
        if self.metadata is None:
            self.metadata = {}

    def has_permission(self, action: str, resource: str) -> bool:
        """Check if role has specific permission."""
        if self.permissions is None:
            return False
        for perm in self.permissions:
            if perm.matches(action, resource):
                return True
        return False

    def add_permission(self, permission: Permission | str) -> None:
        """Add a permission to the role."""
        # Handle both string and Permission object inputs
        if isinstance(permission, str):
            # Parse string format "action:resource"
            if ":" in permission:
                action, resource = permission.split(":", 1)
                perm_obj = Permission(action=action, resource=resource)
            else:
                # Assume it's just an action with wildcard resource
                perm_obj = Permission(action=permission, resource="*")
        else:
            perm_obj = permission

        if self.permissions is None:
            self.permissions = []
        if perm_obj not in self.permissions:
            self.permissions.append(perm_obj)

    def remove_permission(self, permission: Permission | str) -> None:
        """Remove a permission from the role."""
        if isinstance(permission, str):
            # Parse string format
            if ":" in permission:
                action, resource = permission.split(":", 1)
            else:
                action, resource = permission, "*"
        else:
            action, resource = permission.action, permission.resource

        if self.permissions is None:
            return
        self.permissions = [
            p for p in self.permissions if not (p.action == action and p.resource == resource)
        ]


# Casbin model configuration (RBAC with resource roles)
CASBIN_MODEL = """
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act, eft

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow)) && !some(where (p.eft == deny))

[matchers]
m = g(r.sub, p.sub) && (p.obj == "*" || p.obj == r.obj) && (p.act == "*" || p.act == r.act)
"""


class CasbinRBACEngine:
    """Simplified RBAC engine using Casbin."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        policy_path: Optional[str] = None,
        db_url: Optional[str] = None,
    ):
        """Initialize Casbin RBAC engine."""
        # Use provided model or default
        if model_path and Path(model_path).exists():
            self.enforcer = casbin.Enforcer(model_path, policy_path or False)
        else:
            # Use in-memory model
            model = casbin.Model()
            model.load_model_from_text(CASBIN_MODEL)

            if db_url:
                # Use database adapter for persistence
                adapter = Adapter(db_url)
                self.enforcer = casbin.Enforcer(model, adapter)
            else:
                # Use in-memory adapter
                self.enforcer = casbin.Enforcer(model)

        self._init_default_policies()

    def _init_default_policies(self) -> None:
        """Initialize default roles and policies."""
        # Add default roles hierarchy (only if not testing)
        pass  # Keep minimal for tests

    # User-Role Management
    def add_role_for_user(self, user: str, role: str, tenant: Optional[str] = None) -> bool:
        """Assign a role to a user."""
        subject = f"{tenant}:{user}" if tenant else user
        return cast(bool, self.enforcer.add_grouping_policy(subject, role))

    def delete_role_for_user(self, user: str, role: str, tenant: Optional[str] = None) -> bool:
        """Remove a role from a user."""
        subject = f"{tenant}:{user}" if tenant else user
        return cast(bool, self.enforcer.remove_grouping_policy(subject, role))

    def get_roles_for_user(self, user: str, tenant: Optional[str] = None) -> list[str]:
        """Get all roles for a user."""
        subject = f"{tenant}:{user}" if tenant else user
        return cast(list[str], self.enforcer.get_roles_for_user(subject))

    def get_users_for_role(self, role: str) -> list[str]:
        """Get all users with a specific role."""
        return cast(list[str], self.enforcer.get_users_for_role(role))

    def has_role_for_user(self, user: str, role: str, tenant: Optional[str] = None) -> bool:
        """Check if user has a specific role."""
        subject = f"{tenant}:{user}" if tenant else user
        return cast(bool, self.enforcer.has_grouping_policy(subject, role))

    # Permission Management
    def add_permission(self, role: str, resource: str, action: str, effect: str = "allow") -> bool:
        """Add a permission for a role."""
        return cast(bool, self.enforcer.add_policy(role, resource, action, effect))

    def remove_permission(self, role: str, resource: str, action: str) -> bool:
        """Remove a permission from a role."""
        policies = self.enforcer.get_policy()
        for p in policies:
            if p[0] == role and p[1] == resource and p[2] == action:
                return cast(bool, self.enforcer.remove_policy(*p))
        return False

    def get_permissions_for_role(self, role: str) -> list[Permission]:
        """Get all permissions for a role."""
        policies = self.enforcer.get_filtered_policy(0, role)
        return [
            Permission(
                action=p[2], resource=p[1], conditions={"effect": p[3] if len(p) > 3 else "allow"}
            )
            for p in policies
        ]

    # Authorization Checks
    def check_permission(
        self,
        user: str,
        resource: str,
        action: str,
        tenant: Optional[str] = None,
    ) -> bool:
        """Check if user has permission for resource/action."""
        subject = f"{tenant}:{user}" if tenant else user

        # Check with Casbin enforcer
        result = cast(bool, self.enforcer.enforce(subject, resource, action))

        logger.debug(
            "Permission check: user=%s resource=%s action=%s result=%s",
            subject,
            resource,
            action,
            result,
        )

        return result

    def check_permissions_batch(
        self,
        user: str,
        permissions: list[tuple[str, str]],
        tenant: Optional[str] = None,
    ) -> dict[tuple[str, str], bool]:
        """Check multiple permissions at once."""
        subject = f"{tenant}:{user}" if tenant else user
        results = {}

        for resource, action in permissions:
            results[(resource, action)] = cast(
                bool, self.enforcer.enforce(subject, resource, action)
            )

        return results

    # Role Hierarchy
    def add_role_inheritance(self, child_role: str, parent_role: str) -> bool:
        """Make child_role inherit from parent_role."""
        return cast(bool, self.enforcer.add_grouping_policy(child_role, parent_role))

    def remove_role_inheritance(self, child_role: str, parent_role: str) -> bool:
        """Remove role inheritance."""
        return cast(bool, self.enforcer.remove_grouping_policy(child_role, parent_role))

    def get_implicit_roles_for_user(self, user: str, tenant: Optional[str] = None) -> list[str]:
        """Get all roles including inherited ones."""
        subject = f"{tenant}:{user}" if tenant else user
        return cast(list[str], self.enforcer.get_implicit_roles_for_user(subject))

    # Policy Management
    def load_policy(self) -> None:
        """Load policy from storage."""
        self.enforcer.load_policy()

    def save_policy(self) -> None:
        """Save policy to storage."""
        self.enforcer.save_policy()

    def clear_policy(self) -> None:
        """Clear all policies."""
        self.enforcer.clear_policy()

    # Utility Methods
    def get_all_subjects(self) -> list[str]:
        """Get all subjects (users/roles)."""
        return cast(list[str], self.enforcer.get_all_subjects())

    def get_all_objects(self) -> list[str]:
        """Get all objects (resources)."""
        return cast(list[str], self.enforcer.get_all_objects())

    def get_all_actions(self) -> list[str]:
        """Get all actions."""
        return cast(list[str], self.enforcer.get_all_actions())

    def get_all_roles(self) -> list[str]:
        """Get all defined roles."""
        return cast(list[str], self.enforcer.get_all_roles())


# Backward compatibility class
class RBACEngine(CasbinRBACEngine):
    """Backward compatible RBAC engine."""

    def __init__(self, cache_ttl: int = 300, max_cache_size: int = 1000, **kwargs: Any) -> None:
        """Initialize with backward compatible parameters."""
        super().__init__()
        # Backward compatibility - ignore old caching parameters
        # Casbin has its own caching mechanisms

    def can_access(
        self,
        user_roles: list[str],
        required_permission: Permission,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """Check if user roles have required permission."""
        # Convert to Casbin check
        for role in user_roles:
            if self.check_permission(
                role, required_permission.resource, required_permission.action, tenant_id
            ):
                return True

        # Also check by user_id if provided
        if user_id:
            return self.check_permission(
                user_id, required_permission.resource, required_permission.action, tenant_id
            )

        return False

    def add_role(self, role: Role) -> None:
        """Add a role with its permissions."""
        # Add permissions for the role
        if role.permissions is not None:
            for perm in role.permissions:
                self.add_permission(role.name, perm.resource, perm.action)

        # Add parent role relationships
        if role.parent_roles is not None:
            for parent in role.parent_roles:
                self.add_role_inheritance(role.name, parent)

    def get_role(self, role_name: str) -> Optional[Role]:
        """Get role by name."""
        permissions = self.get_permissions_for_role(role_name)

        if not permissions:
            return None

        # Get parent roles
        parent_roles = []
        groupings = self.enforcer.get_grouping_policy()
        for g in groupings:
            if g[0] == role_name:
                parent_roles.append(g[1])

        return Role(name=role_name, permissions=permissions, parent_roles=parent_roles)

    def remove_role(self, role_name: str) -> None:
        """Remove a role."""
        # Remove all policies for this role
        self.enforcer.remove_filtered_policy(0, role_name)

        # Remove all groupings for this role
        self.enforcer.remove_filtered_grouping_policy(0, role_name)
        self.enforcer.remove_filtered_grouping_policy(1, role_name)

    def get_effective_permissions(
        self,
        user_roles: list[str],
        tenant_id: Optional[str] = None,
    ) -> list[Permission]:
        """Get all effective permissions for user roles."""
        all_permissions = []
        processed_roles = set()

        def get_role_permissions(role: str) -> None:
            if role in processed_roles:
                return
            processed_roles.add(role)

            # Get direct permissions
            perms = self.get_permissions_for_role(role)
            all_permissions.extend(perms)

            # Get parent roles and their permissions
            groupings = self.enforcer.get_grouping_policy()
            for g in groupings:
                if g[0] == role:
                    get_role_permissions(g[1])

        for role in user_roles:
            get_role_permissions(role)

        # Deduplicate permissions
        unique_perms = {}
        for perm in all_permissions:
            key = f"{perm.action}:{perm.resource}"
            unique_perms[key] = perm

        return list(unique_perms.values())

    def assign_user_role(self, user_id: str, role_name: str, tenant_id: str | None = None) -> bool:
        """Assign role to user (backward compatibility)."""
        return self.add_role_for_user(user_id, role_name, tenant_id)

    def remove_user_role(self, user_id: str, role_name: str, tenant_id: str | None = None) -> bool:
        """Remove role from user (backward compatibility)."""
        return self.delete_role_for_user(user_id, role_name, tenant_id)


# Create default instance for backward compatibility
default_engine = None


def get_default_rbac_engine() -> RBACEngine:
    """Get default RBAC engine instance."""
    global default_engine
    if default_engine is None:
        default_engine = RBACEngine()
    return default_engine


def create_rbac_engine(**kwargs: Any) -> RBACEngine:
    """Create RBAC engine instance (backward compatibility)."""
    return RBACEngine(**kwargs)


def create_permission(action: str, resource: str, **kwargs: Any) -> Permission:
    """Create permission instance (backward compatibility)."""
    return Permission(action=action, resource=resource, conditions=kwargs)


def create_role(name: str, permissions: list[Permission] | None = None, **kwargs: Any) -> Role:
    """Create role instance (backward compatibility)."""
    return Role(
        name=name,
        permissions=permissions or [],
        parent_roles=kwargs.get("parent_roles", []),
        description=kwargs.get("description", ""),
        metadata=kwargs.get("metadata", {}),
    )


class PermissionCache:
    """Backward compatibility cache class."""

    def __init__(self, ttl: int = 300, max_size: int = 1000):
        """Initialize cache (unused in Casbin implementation)."""
        pass

    def get(self, key: str) -> None:
        """Get from cache (always returns None)."""
        return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set cache value (no-op)."""
        pass

    def clear(self) -> None:
        """Clear cache (no-op)."""
        pass


# Export main classes for compatibility
__all__ = [
    "CasbinRBACEngine",
    "RBACEngine",
    "Permission",
    "Role",
    "Action",
    "Resource",
    "PolicyEffect",
    "PermissionType",
    "ResourceType",
    "PermissionCache",
    "get_default_rbac_engine",
    "create_rbac_engine",
    "create_permission",
    "create_role",
]
