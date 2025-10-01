"""
RBAC Service Layer - Handles role and permission management
"""
from typing import List, Optional, Set, Dict, Any
from datetime import datetime, timezone
from uuid import UUID
import logging
from functools import lru_cache

from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError

from dotmac.platform.auth.models import (
    Role, Permission, PermissionCategory,
    user_roles, role_permissions, user_permissions,
    PermissionGrant
)
from dotmac.platform.caching import cache_get, cache_set, cache_delete
from dotmac.platform.auth.exceptions import AuthError, AuthorizationError
from dotmac.platform.auth.rbac_audit import rbac_audit_logger
from dotmac.platform.tenant import get_current_tenant_id

logger = logging.getLogger(__name__)


class RBACService:
    """Service for managing roles and permissions"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self._permission_cache: Dict[str, Permission] = {}
        self._role_cache: Dict[str, Role] = {}

    # ==================== User Permissions ====================

    async def get_user_permissions(
        self,
        user_id: UUID,
        include_expired: bool = False
    ) -> Set[str]:
        """Get all permissions for a user (from roles and direct grants)"""
        cache_key = f"user_perms:{user_id}"

        # Check cache first
        cached = cache_get(cache_key)
        if cached and not include_expired:
            return set(cached)

        permissions = set()
        now = datetime.now(timezone.utc)

        # Get permissions from roles
        query = (
            select(Permission.name)
            .join(role_permissions)
            .join(Role)
            .join(user_roles)
            .where(user_roles.c.user_id == user_id)
            .where(Role.is_active == True)
            .where(Permission.is_active == True)
        )

        if not include_expired:
            query = query.where(
                or_(
                    user_roles.c.expires_at.is_(None),
                    user_roles.c.expires_at > now
                )
            )

        role_perms = await self.db.execute(query)
        permissions.update(p[0] for p in role_perms)

        # Get direct user permissions (overrides)
        direct_query = (
            select(Permission.name, user_permissions.c.granted)
            .join(user_permissions)
            .where(user_permissions.c.user_id == user_id)
            .where(Permission.is_active == True)
        )

        if not include_expired:
            direct_query = direct_query.where(
                or_(
                    user_permissions.c.expires_at.is_(None),
                    user_permissions.c.expires_at > now
                )
            )

        direct_perms = await self.db.execute(direct_query)

        for perm_name, granted in direct_perms:
            if granted:
                permissions.add(perm_name)
            else:
                permissions.discard(perm_name)  # Revoke permission

        # Include inherited permissions
        permissions = await self._expand_permissions(permissions)

        # Cache for 5 minutes
        cache_set(cache_key, list(permissions), ttl=300)

        logger.info(f"Loaded {len(permissions)} permissions for user {user_id}")
        return permissions

    async def user_has_permission(
        self,
        user_id: UUID,
        permission: str
    ) -> bool:
        """Check if user has a specific permission"""
        user_perms = await self.get_user_permissions(user_id)

        # Check exact match
        if permission in user_perms:
            return True

        # Check wildcard permissions (e.g., "ticket.*" matches "ticket.read")
        for user_perm in user_perms:
            if user_perm.endswith(".*"):
                prefix = user_perm[:-2]
                if permission.startswith(prefix + "."):
                    return True
            elif user_perm == "*":  # Superadmin
                return True

        return False

    async def user_has_any_permission(
        self,
        user_id: UUID,
        permissions: List[str]
    ) -> bool:
        """Check if user has any of the specified permissions"""
        for perm in permissions:
            if await self.user_has_permission(user_id, perm):
                return True
        return False

    async def user_has_all_permissions(
        self,
        user_id: UUID,
        permissions: List[str]
    ) -> bool:
        """Check if user has all specified permissions"""
        for perm in permissions:
            if not await self.user_has_permission(user_id, perm):
                return False
        return True

    # ==================== Role Management ====================

    async def get_user_roles(
        self,
        user_id: UUID,
        include_expired: bool = False
    ) -> List[Role]:
        """Get all roles assigned to a user"""
        query = (
            select(Role)
            .join(user_roles)
            .where(user_roles.c.user_id == user_id)
            .where(Role.is_active == True)
        )

        if not include_expired:
            now = datetime.now(timezone.utc)
            query = query.where(
                or_(
                    user_roles.c.expires_at.is_(None),
                    user_roles.c.expires_at > now
                )
            )

        result = await self.db.execute(query.options(selectinload(Role.permissions)))
        return result.scalars().all()

    async def assign_role_to_user(
        self,
        user_id: UUID,
        role_name: str,
        granted_by: UUID,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Assign a role to a user"""
        # Get role
        role = await self._get_role_by_name(role_name)
        if not role:
            raise AuthorizationError(f"Role '{role_name}' not found")

        # Check if already assigned
        existing = await self.db.execute(
            select(user_roles).where(
                and_(
                    user_roles.c.user_id == user_id,
                    user_roles.c.role_id == role.id
                )
            )
        )

        if existing.first():
            logger.info(f"Role {role_name} already assigned to user {user_id}")
            return

        # Assign role
        await self.db.execute(
            user_roles.insert().values(
                user_id=user_id,
                role_id=role.id,
                granted_by=granted_by,
                expires_at=expires_at,
                metadata=metadata
            )
        )

        # Log the grant
        await self._log_permission_grant(
            user_id=user_id,
            role_id=role.id,
            granted_by=granted_by,
            action="grant",
            expires_at=expires_at
        )

        # Clear cache
        cache_delete(f"user_perms:{user_id}")

        await self.db.commit()
        logger.info(f"Assigned role {role_name} to user {user_id}")

        # Audit log the role assignment
        tenant_id = get_current_tenant_id() or "default"
        await rbac_audit_logger.log_role_assigned(
            user_id=str(user_id),
            role_name=role_name,
            role_id=str(role.id),
            assigned_by=str(granted_by),
            tenant_id=tenant_id,
            expires_at=expires_at.isoformat() if expires_at else None,
            metadata=metadata
        )

    async def revoke_role_from_user(
        self,
        user_id: UUID,
        role_name: str,
        revoked_by: UUID,
        reason: Optional[str] = None
    ) -> None:
        """Revoke a role from a user"""
        role = await self._get_role_by_name(role_name)
        if not role:
            raise AuthorizationError(f"Role '{role_name}' not found")

        # Remove role assignment
        result = await self.db.execute(
            user_roles.delete().where(
                and_(
                    user_roles.c.user_id == user_id,
                    user_roles.c.role_id == role.id
                )
            )
        )

        if result.rowcount == 0:
            logger.warning(f"Role {role_name} was not assigned to user {user_id}")
            return

        # Log the revocation
        await self._log_permission_grant(
            user_id=user_id,
            role_id=role.id,
            granted_by=revoked_by,
            action="revoke",
            reason=reason
        )

        # Clear cache
        cache_delete(f"user_perms:{user_id}")

        await self.db.commit()
        logger.info(f"Revoked role {role_name} from user {user_id}")

        # Audit log the role revocation
        tenant_id = get_current_tenant_id() or "default"
        await rbac_audit_logger.log_role_revoked(
            user_id=str(user_id),
            role_name=role_name,
            role_id=str(role.id),
            revoked_by=str(revoked_by),
            tenant_id=tenant_id,
            reason=reason
        )

    # ==================== Permission Management ====================

    async def grant_permission_to_user(
        self,
        user_id: UUID,
        permission_name: str,
        granted_by: UUID,
        expires_at: Optional[datetime] = None,
        reason: Optional[str] = None
    ) -> None:
        """Grant a specific permission directly to a user"""
        permission = await self._get_permission_by_name(permission_name)
        if not permission:
            raise AuthorizationError(f"Permission '{permission_name}' not found")

        # Check if already granted
        existing = await self.db.execute(
            select(user_permissions).where(
                and_(
                    user_permissions.c.user_id == user_id,
                    user_permissions.c.permission_id == permission.id
                )
            )
        )

        if existing.first():
            # Update existing grant
            await self.db.execute(
                user_permissions.update()
                .where(
                    and_(
                        user_permissions.c.user_id == user_id,
                        user_permissions.c.permission_id == permission.id
                    )
                )
                .values(
                    granted=True,
                    granted_by=granted_by,
                    expires_at=expires_at,
                    reason=reason,
                    granted_at=datetime.now(timezone.utc)
                )
            )
        else:
            # Create new grant
            await self.db.execute(
                user_permissions.insert().values(
                    user_id=user_id,
                    permission_id=permission.id,
                    granted=True,
                    granted_by=granted_by,
                    expires_at=expires_at,
                    reason=reason
                )
            )

        # Log the grant
        await self._log_permission_grant(
            user_id=user_id,
            permission_id=permission.id,
            granted_by=granted_by,
            action="grant",
            expires_at=expires_at,
            reason=reason
        )

        # Clear cache
        cache_delete(f"user_perms:{user_id}")

        await self.db.commit()
        logger.info(f"Granted permission {permission_name} to user {user_id}")

        # Audit log the permission grant
        tenant_id = get_current_tenant_id() or "default"
        await rbac_audit_logger.log_permission_granted(
            user_id=str(user_id),
            permission_name=permission_name,
            permission_id=str(permission.id),
            granted_by=str(granted_by),
            tenant_id=tenant_id,
            expires_at=expires_at.isoformat() if expires_at else None,
            reason=reason
        )

    # ==================== Role/Permission CRUD ====================

    async def create_role(
        self,
        name: str,
        display_name: str,
        description: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        parent_role: Optional[str] = None,
        is_default: bool = False
    ) -> Role:
        """Create a new role"""
        # Check if role exists
        existing = await self._get_role_by_name(name)
        if existing:
            raise IntegrityError(f"Role '{name}' already exists", None, None)

        # Get parent role if specified
        parent = None
        if parent_role:
            parent = await self._get_role_by_name(parent_role)
            if not parent:
                raise AuthorizationError(f"Parent role '{parent_role}' not found")

        # Create role
        role = Role(
            name=name,
            display_name=display_name,
            description=description,
            parent_id=parent.id if parent else None,
            is_default=is_default
        )
        self.db.add(role)

        # Add permissions
        if permissions:
            for perm_name in permissions:
                perm = await self._get_permission_by_name(perm_name)
                if perm:
                    role.permissions.append(perm)

        await self.db.commit()
        logger.info(f"Created role: {name}")
        return role

    async def create_permission(
        self,
        name: str,
        display_name: str,
        category: PermissionCategory,
        description: Optional[str] = None,
        parent_permission: Optional[str] = None
    ) -> Permission:
        """Create a new permission"""
        # Check if permission exists
        existing = await self._get_permission_by_name(name)
        if existing:
            raise IntegrityError(f"Permission '{name}' already exists", None, None)

        # Get parent permission if specified
        parent = None
        if parent_permission:
            parent = await self._get_permission_by_name(parent_permission)
            if not parent:
                raise AuthorizationError(f"Parent permission '{parent_permission}' not found")

        # Create permission
        permission = Permission(
            name=name,
            display_name=display_name,
            category=category,
            description=description,
            parent_id=parent.id if parent else None
        )
        self.db.add(permission)
        await self.db.commit()

        logger.info(f"Created permission: {name}")
        return permission

    # ==================== Helper Methods ====================

    async def _get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role by name (cached)"""
        if name in self._role_cache:
            return self._role_cache[name]

        result = await self.db.execute(
            select(Role).where(Role.name == name)
        )
        role = result.scalar_one_or_none()

        if role:
            self._role_cache[name] = role

        return role

    async def _get_permission_by_name(self, name: str) -> Optional[Permission]:
        """Get permission by name (cached)"""
        if name in self._permission_cache:
            return self._permission_cache[name]

        result = await self.db.execute(
            select(Permission).where(Permission.name == name)
        )
        permission = result.scalar_one_or_none()

        if permission:
            self._permission_cache[name] = permission

        return permission

    async def _expand_permissions(self, permissions: Set[str]) -> Set[str]:
        """Expand permissions to include inherited ones"""
        expanded = set(permissions)

        # Add parent permissions
        for perm_name in list(permissions):
            perm = await self._get_permission_by_name(perm_name)
            if perm and perm.parent_id:
                parent = await self.db.get(Permission, perm.parent_id)
                if parent:
                    expanded.add(parent.name)

        # Add wildcard expansions
        # e.g., "ticket.read.all" implies "ticket.read.assigned" and "ticket.read.own"
        for perm in list(expanded):
            parts = perm.split(".")
            if len(parts) > 1:
                # Add broader permissions
                for i in range(1, len(parts)):
                    expanded.add(".".join(parts[:i]) + ".*")

        return expanded

    async def _log_permission_grant(
        self,
        user_id: UUID,
        role_id: Optional[UUID] = None,
        permission_id: Optional[UUID] = None,
        granted_by: UUID = None,
        action: str = "grant",
        expires_at: Optional[datetime] = None,
        reason: Optional[str] = None
    ) -> None:
        """Log permission grant/revoke for audit trail"""
        grant_log = PermissionGrant(
            user_id=user_id,
            role_id=role_id,
            permission_id=permission_id,
            granted_by=granted_by,
            action=action,
            expires_at=expires_at,
            reason=reason,
            metadata={
                "ip_address": "system",  # Would get from request context
                "user_agent": "system"
            }
        )
        self.db.add(grant_log)


# ==================== Dependency Functions ====================

def get_rbac_service(db: Session) -> RBACService:
    """Dependency to get RBAC service"""
    return RBACService(db)