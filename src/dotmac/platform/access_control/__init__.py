"""Access control and RBAC system for DotMac Framework."""

from .decorators import check_access, require_permission
from .manager import AccessControlManager
from .models import (
    AccessControlEntry,
    AccessDecision,
    AccessRequest,
    ActionType,
    Permission,
    PermissionType,
    ResourceType,
    Role,
)

__all__ = [
    "PermissionType",
    "ResourceType",
    "ActionType",
    "Permission",
    "Role",
    "AccessControlEntry",
    "AccessRequest",
    "AccessDecision",
    "AccessControlManager",
    "require_permission",
    "check_access",
]
