"""
Access Control Manager - Comprehensive RBAC and ABAC implementation.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Optional

import structlog
from pydantic import ValidationError

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

logger = structlog.get_logger(__name__)


class AccessControlManager:
    """
    Comprehensive access control system with RBAC and ABAC capabilities.
    """

    def __init__(self, audit_logger: Optional[structlog.BoundLogger] = None):
        self.audit_logger = audit_logger or logger

        # Core storage
        self._permissions: dict[str, Permission] = {}
        self._roles: dict[str, Role] = {}
        self._access_control_entries: dict[str, AccessControlEntry] = {}

        # Caches for performance
        self._permission_cache: dict[str, AccessDecision] = {}
        self._role_hierarchy_cache: dict[str, set[str]] = {}

        # Configuration
        self.cache_ttl_seconds = 300  # 5 minutes
        self.enable_caching = True
        self.max_cache_entries = 10000

        # Initialize system permissions and roles
        self._initialize_system_permissions()
        self._initialize_system_roles()

    def _initialize_system_permissions(self) -> None:
        """Initialize built-in system permissions."""

        system_permissions = [
            # Plugin permissions
            Permission(
                permission_id="plugin_read",
                name="Read Plugin",
                description="Read plugin information and metadata",
                resource_type=ResourceType.PLUGIN,
                action=ActionType.READ,
                permission_type=PermissionType.ALLOW,
            ),
            Permission(
                permission_id="plugin_execute",
                name="Execute Plugin",
                description="Execute plugin methods and functionality",
                resource_type=ResourceType.PLUGIN,
                action=ActionType.EXECUTE,
                permission_type=PermissionType.ALLOW,
            ),
            Permission(
                permission_id="plugin_install",
                name="Install Plugin",
                description="Install new plugins",
                resource_type=ResourceType.PLUGIN,
                action=ActionType.INSTALL,
                permission_type=PermissionType.ALLOW,
            ),
            Permission(
                permission_id="plugin_manage",
                name="Manage Plugin",
                description="Full plugin management capabilities",
                resource_type=ResourceType.PLUGIN,
                action=ActionType.MANAGE,
                permission_type=PermissionType.ALLOW,
            ),
            # API permissions
            Permission(
                permission_id="api_read",
                name="Read API",
                description="Read access to API endpoints",
                resource_type=ResourceType.API,
                action=ActionType.READ,
                permission_type=PermissionType.ALLOW,
            ),
            Permission(
                permission_id="api_write",
                name="Write API",
                description="Write access to API endpoints",
                resource_type=ResourceType.API,
                action=ActionType.WRITE,
                permission_type=PermissionType.ALLOW,
            ),
            # Data permissions
            Permission(
                permission_id="data_read",
                name="Read Data",
                description="Read access to data resources",
                resource_type=ResourceType.DATA,
                action=ActionType.READ,
                permission_type=PermissionType.ALLOW,
            ),
            Permission(
                permission_id="data_write",
                name="Write Data",
                description="Write access to data resources",
                resource_type=ResourceType.DATA,
                action=ActionType.WRITE,
                permission_type=PermissionType.ALLOW,
            ),
            # System permissions
            Permission(
                permission_id="system_monitor",
                name="Monitor System",
                description="Monitor system resources and health",
                resource_type=ResourceType.SYSTEM,
                action=ActionType.MONITOR,
                permission_type=PermissionType.ALLOW,
            ),
            Permission(
                permission_id="system_manage",
                name="Manage System",
                description="Full system management capabilities",
                resource_type=ResourceType.SYSTEM,
                action=ActionType.MANAGE,
                permission_type=PermissionType.ALLOW,
            ),
        ]

        for permission in system_permissions:
            self._permissions[permission.permission_id] = permission

        logger.info("Initialized system permissions", count=len(system_permissions))

    def _initialize_system_roles(self) -> None:
        """Initialize built-in system roles."""

        system_roles = [
            Role(
                role_id="plugin_user",
                name="Plugin User",
                description="Basic plugin user with read and execute permissions",
                permissions=["plugin_read", "plugin_execute", "api_read"],
                tenant_scoped=True,
            ),
            Role(
                role_id="plugin_developer",
                name="Plugin Developer",
                description="Plugin developer with enhanced permissions",
                permissions=["plugin_read", "plugin_execute", "plugin_install", "api_read", "api_write", "data_read"],
                tenant_scoped=True,
            ),
            Role(
                role_id="plugin_admin",
                name="Plugin Administrator",
                description="Full plugin administration capabilities",
                permissions=["plugin_manage", "api_read", "api_write", "data_read", "data_write", "system_monitor"],
                tenant_scoped=True,
            ),
            Role(
                role_id="system_admin",
                name="System Administrator",
                description="Full system administration capabilities",
                permissions=[
                    "system_manage",
                    "plugin_manage",
                    "api_read",
                    "api_write",
                    "data_read",
                    "data_write",
                    "system_monitor",
                ],
                system_role=True,
                tenant_scoped=False,
            ),
        ]

        for role in system_roles:
            self._roles[role.role_id] = role

        logger.info("Initialized system roles", count=len(system_roles))

    async def create_permission(self, permission: Permission) -> str:
        """Create new permission."""

        if permission.permission_id in self._permissions:
            raise ValidationError(f"Permission already exists: {permission.permission_id}")

        self._permissions[permission.permission_id] = permission

        self.audit_logger.info(
            "Permission created",
            permission_id=permission.permission_id,
            name=permission.name,
            resource_type=permission.resource_type.value,
            action=permission.action.value,
            created_by=permission.created_by,
        )

        return permission.permission_id

    async def create_role(self, role: Role) -> str:
        """Create new role."""

        if role.role_id in self._roles:
            raise ValidationError(f"Role already exists: {role.role_id}")

        # Validate permissions exist
        for perm_id in role.permissions:
            if perm_id not in self._permissions:
                raise ValidationError(f"Permission not found: {perm_id}")

        self._roles[role.role_id] = role

        # Clear role hierarchy cache
        self._role_hierarchy_cache.clear()

        self.audit_logger.info(
            "Role created",
            role_id=role.role_id,
            name=role.name,
            permission_count=len(role.permissions),
            tenant_scoped=role.tenant_scoped,
            created_by=role.created_by,
        )

        return role.role_id

    async def grant_permission(
        self,
        subject_type: str,
        subject_id: str,
        resource_type: ResourceType,
        resource_id: str,
        permissions: list[str],
        roles: Optional[list[str]] = None,
        granted_by: str = "",
        expires_at: Optional[datetime] = None,
        conditions: Optional[dict[str, Any]] = None,
    ) -> str:
        """Grant permissions to subject."""

        # Validate permissions and roles exist
        for perm_id in permissions:
            if perm_id not in self._permissions:
                raise ValidationError(f"Permission not found: {perm_id}")

        for role_id in roles or []:
            if role_id not in self._roles:
                raise ValidationError(f"Role not found: {role_id}")

        # Create ACE
        ace = AccessControlEntry(
            subject_type=subject_type,
            subject_id=subject_id,
            resource_type=resource_type,
            resource_id=resource_id,
            permissions=permissions,
            roles=roles or [],
            granted_by=granted_by,
            expires_at=expires_at,
            conditions=conditions or {},
        )

        self._access_control_entries[ace.ace_id] = ace

        # Clear permission cache
        self._clear_permission_cache(subject_id)

        self.audit_logger.info(
            "Permissions granted",
            ace_id=ace.ace_id,
            subject_type=subject_type,
            subject_id=subject_id,
            resource_type=resource_type.value,
            resource_id=resource_id,
            permission_count=len(permissions),
            role_count=len(roles or []),
            granted_by=granted_by,
        )

        return ace.ace_id

    async def check_permission(self, request: AccessRequest) -> AccessDecision:
        """Check if access request should be allowed."""

        start_time = asyncio.get_event_loop().time()

        # Check cache first
        cache_key = self._get_cache_key(request)
        if self.enable_caching and cache_key in self._permission_cache:
            cached_decision = self._permission_cache[cache_key]

            # Check cache expiry
            cache_age = (datetime.now(timezone.utc) - cached_decision.evaluated_at).total_seconds()
            if cache_age < self.cache_ttl_seconds:
                cached_decision.request_id = request.request_id
                return cached_decision

        # Evaluate permission
        decision = await self._evaluate_permission(request)

        # Calculate evaluation time
        evaluation_time = (asyncio.get_event_loop().time() - start_time) * 1000
        decision.evaluation_time_ms = evaluation_time

        # Cache decision
        if self.enable_caching:
            self._cache_decision(cache_key, decision)

        # Audit log
        self.audit_logger.info(
            "Permission evaluated",
            request_id=request.request_id,
            subject_id=request.subject_id,
            resource_type=request.resource_type.value,
            resource_id=request.resource_id,
            action=request.action.value,
            decision=decision.decision,
            reason=decision.reason,
            evaluation_time_ms=evaluation_time,
        )

        return decision

    async def _evaluate_permission(self, request: AccessRequest) -> AccessDecision:
        """Evaluate access permission request."""

        decision = AccessDecision(
            request_id=request.request_id, decision="deny", reason="No matching permissions found"
        )

        try:
            # Find applicable ACEs
            applicable_aces = self._find_applicable_aces(request)

            # Evaluate permissions from ACEs
            allow_permissions = []
            deny_permissions = []

            for ace in applicable_aces:
                # Check ACE validity
                if not ace.active or ace.is_expired():
                    continue

                # Evaluate ACE conditions
                if not self._evaluate_ace_conditions(ace, request):
                    continue

                decision.matched_aces.append(ace.ace_id)

                # Check direct permissions
                for perm_id in ace.permissions:
                    permission = self._permissions.get(perm_id)
                    if not permission:
                        continue

                    if not permission.active or permission.is_expired():
                        continue

                    if not permission.matches_resource(request.resource_type, request.resource_id):
                        continue

                    if permission.action != request.action:
                        continue

                    if not permission.evaluate_conditions(request.context):
                        continue

                    decision.matched_permissions.append(perm_id)

                    if permission.permission_type == PermissionType.ALLOW:
                        allow_permissions.append(permission)
                    elif permission.permission_type == PermissionType.DENY:
                        deny_permissions.append(permission)

                # Check role permissions
                for role_id in ace.roles:
                    role_permissions = await self._get_role_permissions(role_id)

                    decision.matched_roles.append(role_id)

                    for permission in role_permissions:
                        if not permission.active or permission.is_expired():
                            continue

                        if not permission.matches_resource(request.resource_type, request.resource_id):
                            continue

                        if permission.action != request.action:
                            continue

                        if not permission.evaluate_conditions(request.context):
                            continue

                        decision.matched_permissions.append(permission.permission_id)

                        if permission.permission_type == PermissionType.ALLOW:
                            allow_permissions.append(permission)
                        elif permission.permission_type == PermissionType.DENY:
                            deny_permissions.append(permission)

            # Apply decision logic: explicit deny overrides allow
            if deny_permissions:
                decision.decision = "deny"
                decision.reason = f"Explicit deny permission found: {deny_permissions[0].name}"
            elif allow_permissions:
                decision.decision = "allow"
                decision.reason = f"Allow permission granted: {allow_permissions[0].name}"
            else:
                decision.decision = "deny"
                decision.reason = "No applicable permissions found"

        except Exception as e:
            decision.decision = "error"
            decision.reason = f"Permission evaluation error: {e}"
            logger.error("Permission evaluation error", request_id=request.request_id, error=str(e))

        return decision

    def _find_applicable_aces(self, request: AccessRequest) -> list[AccessControlEntry]:
        """Find ACEs applicable to the request."""
        applicable_aces = []

        for ace in self._access_control_entries.values():
            if not ace.active:
                continue

            # Match subject
            if ace.subject_id != request.subject_id and ace.subject_id != "*":
                continue

            if ace.subject_type != request.subject_type:
                continue

            # Match resource
            if ace.resource_type != request.resource_type:
                continue

            if ace.resource_id != request.resource_id and ace.resource_id != "*":
                continue

            applicable_aces.append(ace)

        return applicable_aces

    def _evaluate_ace_conditions(self, ace: AccessControlEntry, request: AccessRequest) -> bool:
        """Evaluate ACE conditions."""

        # Basic expiry check
        if ace.is_expired():
            return False

        # Evaluate custom conditions
        for condition_key, condition_value in ace.conditions.items():
            context_value = request.context.get(condition_key)

            if isinstance(condition_value, dict):
                # Complex condition evaluation
                if "equals" in condition_value:
                    if context_value != condition_value["equals"]:
                        return False
            else:
                # Simple equality check
                if context_value != condition_value:
                    return False

        return True

    async def _get_role_permissions(self, role_id: str) -> list[Permission]:
        """Get all permissions for a role (including inherited)."""

        all_role_ids = await self._get_role_hierarchy(role_id)
        permissions = []

        for rid in all_role_ids:
            role = self._roles.get(rid)
            if not role or not role.active:
                continue

            for perm_id in role.permissions:
                permission = self._permissions.get(perm_id)
                if permission and permission.active:
                    permissions.append(permission)

        return permissions

    async def _get_role_hierarchy(self, role_id: str) -> set[str]:
        """Get role hierarchy including parent roles."""

        if role_id in self._role_hierarchy_cache:
            return self._role_hierarchy_cache[role_id]

        visited = set()

        def collect_roles(rid: str):
            if rid in visited:
                return

            visited.add(rid)
            role = self._roles.get(rid)
            if role:
                for parent_id in role.parent_roles:
                    collect_roles(parent_id)

        collect_roles(role_id)

        self._role_hierarchy_cache[role_id] = visited
        return visited

    def _get_cache_key(self, request: AccessRequest) -> str:
        """Generate cache key for permission request."""
        return f"{request.subject_id}:{request.resource_type.value}:{request.resource_id}:{request.action.value}"

    def _cache_decision(self, cache_key: str, decision: AccessDecision) -> None:
        """Cache permission decision."""

        # Implement LRU eviction if cache is full
        if len(self._permission_cache) >= self.max_cache_entries:
            # Remove oldest entry
            oldest_key = min(self._permission_cache.keys(), key=lambda k: self._permission_cache[k].evaluated_at)
            del self._permission_cache[oldest_key]

        self._permission_cache[cache_key] = decision

    def _clear_permission_cache(self, subject_id: str) -> None:
        """Clear permission cache for subject."""
        keys_to_remove = [key for key in self._permission_cache.keys() if key.startswith(f"{subject_id}:")]

        for key in keys_to_remove:
            del self._permission_cache[key]

    async def revoke_permission(self, ace_id: str, revoked_by: str) -> bool:
        """Revoke access control entry."""

        if ace_id not in self._access_control_entries:
            raise ValidationError(f"ACE not found: {ace_id}")

        ace = self._access_control_entries[ace_id]
        ace.active = False

        # Clear relevant caches
        self._clear_permission_cache(ace.subject_id)

        self.audit_logger.info(
            "Permission revoked",
            ace_id=ace_id,
            subject_id=ace.subject_id,
            revoked_by=revoked_by,
        )

        return True

    # Query methods

    def get_permission(self, permission_id: str) -> Optional[Permission]:
        """Get permission by ID."""
        return self._permissions.get(permission_id)

    def get_role(self, role_id: str) -> Optional[Role]:
        """Get role by ID."""
        return self._roles.get(role_id)

    def get_subject_permissions(self, subject_id: str) -> list[AccessControlEntry]:
        """Get all permissions for subject."""
        return [ace for ace in self._access_control_entries.values() if ace.subject_id == subject_id and ace.active]

    def list_permissions(self) -> list[Permission]:
        """List all permissions."""
        return [p for p in self._permissions.values() if p.active]

    def list_roles(self) -> list[Role]:
        """List all roles."""
        return [r for r in self._roles.values() if r.active]
