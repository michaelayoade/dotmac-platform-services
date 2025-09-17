"""
RBAC (Role-Based Access Control) repositories for user management v2 system.
Provides data access layer for roles, permissions, and access control operations.
"""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dotmac.platform.core.decorators import standard_exception_handler
from dotmac.platform.observability.logging import get_logger
from dotmac.platform.observability.unified_logging import get_logger

from ..models.rbac_models import (
    PermissionModel,
    PermissionScope,
    PermissionType,
    RoleModel,
    RolePermissionModel,
    UserRoleModel,
)
from ..schemas.rbac_schemas import (
    PermissionCreateSchema,
    PermissionSearchSchema,
    RoleCreateSchema,
    RoleSearchSchema,
)
from .base_repository import BaseRepository

logger = get_logger(__name__)

class RoleRepository(BaseRepository[RoleModel]):
    """Repository for role management operations."""

    def __init__(self, db_session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(db_session, RoleModel, tenant_id)

    @standard_exception_handler
    async def create_role(
        self, role_data: RoleCreateSchema, created_by: Optional[UUID] = None
    ) -> RoleModel:
        """
        Create new role with permissions.

        Args:
            role_data: Role creation data
            created_by: User who created the role

        Returns:
            Created role model
        """
        role_dict = role_data.model_dump(exclude={"permission_ids"})
        role_dict["tenant_id"] = self.tenant_id
        role_dict["created_by"] = created_by

        role = await self.create(**role_dict)

        # Assign permissions if provided
        if role_data.permission_ids:
            for permission_id in role_data.permission_ids:
                await self._assign_permission_to_role(role.id, permission_id, created_by)

        logger.info(
            f"Created role {role.name} with {len(role_data.permission_ids or [])} permissions"
        )
        return role

    @standard_exception_handler
    async def get_role_by_name(self, name: str) -> Optional[RoleModel]:
        """Get role by name within tenant."""
        query = select(RoleModel).where(
            and_(RoleModel.name == name, RoleModel.tenant_id == self.tenant_id)
        )

        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    @standard_exception_handler
    async def get_role_with_permissions(self, role_id: UUID) -> Optional[RoleModel]:
        """Get role with all associated permissions."""
        query = (
            select(RoleModel)
            .options(
                selectinload(RoleModel.permissions).selectinload(RolePermissionModel.permission),
                selectinload(RoleModel.child_roles),
                selectinload(RoleModel.parent_role),
            )
            .where(RoleModel.id == role_id)
        )

        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    @standard_exception_handler
    async def search_roles(self, search_params: RoleSearchSchema) -> tuple[list[RoleModel], int]:
        """
        Search roles with filters and pagination.

        Args:
            search_params: Search parameters

        Returns:
            Tuple of (roles, total_count)
        """
        query = select(RoleModel)
        count_query = select(func.count(RoleModel.id))

        # Base filters
        filters = [RoleModel.tenant_id == self.tenant_id]

        if search_params.query:
            search_filter = or_(
                RoleModel.name.ilike(f"%{search_params.query}%"),
                RoleModel.display_name.ilike(f"%{search_params.query}%"),
                RoleModel.description.ilike(f"%{search_params.query}%"),
            )
            filters.append(search_filter)

        if search_params.role_category is not None:
            filters.append(RoleModel.role_category == search_params.role_category.value)

        if search_params.is_active is not None:
            filters.append(RoleModel.is_active == search_params.is_active)

        if search_params.is_system_role is not None:
            filters.append(RoleModel.is_system_role == search_params.is_system_role)

        if search_params.is_default is not None:
            filters.append(RoleModel.is_default == search_params.is_default)

        if search_params.parent_role_id is not None:
            filters.append(RoleModel.parent_role_id == search_params.parent_role_id)

        if search_params.created_after:
            filters.append(RoleModel.created_at >= search_params.created_after)

        if search_params.created_before:
            filters.append(RoleModel.created_at <= search_params.created_before)

        # Apply filters
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

        # Get total count
        count_result = await self.db_session.execute(count_query)
        total_count = count_result.scalar()

        # Apply sorting
        sort_column = getattr(RoleModel, search_params.sort_by, RoleModel.name)
        if search_params.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (search_params.page - 1) * search_params.page_size
        query = query.offset(offset).limit(search_params.page_size)

        # Load permissions count
        query = query.options(
            selectinload(RoleModel.permissions), selectinload(RoleModel.user_roles)
        )

        result = await self.db_session.execute(query)
        roles = result.scalars().all()

        return list(roles), total_count

    @standard_exception_handler
    async def get_user_roles(self, user_id: UUID, include_expired: bool = False) -> list[RoleModel]:
        """Get all active roles for a user."""
        query = (
            select(RoleModel)
            .join(UserRoleModel, UserRoleModel.role_id == RoleModel.id)
            .where(
                and_(
                    UserRoleModel.user_id == user_id,
                    UserRoleModel.is_active is True,
                    RoleModel.is_active is True,
                )
            )
        )

        if not include_expired:
            query = query.where(
                or_(
                    UserRoleModel.expires_at.is_(None),
                    UserRoleModel.expires_at > datetime.now(timezone.utc),
                )
            )

        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    @standard_exception_handler
    async def get_default_role(self) -> Optional[RoleModel]:
        """Get the default role for new users in this tenant."""
        query = select(RoleModel).where(
            and_(
                RoleModel.tenant_id == self.tenant_id,
                RoleModel.is_default is True,
                RoleModel.is_active is True,
            )
        )

        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    @standard_exception_handler
    async def delete_role(self, role_id: UUID) -> bool:
        """
        Delete role if it's not a system role and has no users.

        Args:
            role_id: Role ID to delete

        Returns:
            True if deleted successfully
        """
        role = await self.get_by_id(role_id)
        if not role:
            return False

        if role.is_system_role:
            raise ValueError("Cannot delete system role")

        # Check if role has active users
        user_count_query = select(func.count(UserRoleModel.id)).where(
            and_(UserRoleModel.role_id == role_id, UserRoleModel.is_active is True)
        )
        result = await self.db_session.execute(user_count_query)
        user_count = result.scalar()

        if user_count > 0:
            raise ValueError(f"Cannot delete role with {user_count} active users")

        await self.delete(role_id)
        return True

    async def _assign_permission_to_role(
        self, role_id: UUID, permission_id: UUID, granted_by: Optional[UUID] = None
    ) -> RolePermissionModel:
        """Assign permission to role."""
        role_permission = RolePermissionModel(
            role_id=role_id,
            permission_id=permission_id,
            granted_by=granted_by,
            is_granted=True,
            is_active=True,
        )

        self.db_session.add(role_permission)
        await self.db_session.flush()
        return role_permission

class PermissionRepository(BaseRepository[PermissionModel]):
    """Repository for permission management operations."""

    def __init__(self, db_session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(db_session, PermissionModel, tenant_id)

    @standard_exception_handler
    async def create_permission(
        self, permission_data: PermissionCreateSchema, created_by: Optional[UUID] = None
    ) -> PermissionModel:
        """Create new permission."""
        permission_dict = permission_data.model_dump()
        permission_dict["created_by"] = created_by

        permission = await self.create(**permission_dict)
        logger.info(f"Created permission {permission.name}")
        return permission

    @standard_exception_handler
    async def get_permission_by_name(self, name: str) -> Optional[PermissionModel]:
        """Get permission by name."""
        query = select(PermissionModel).where(PermissionModel.name == name)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    @standard_exception_handler
    async def search_permissions(
        self, search_params: PermissionSearchSchema
    ) -> tuple[list[PermissionModel], int]:
        """Search permissions with filters and pagination."""
        query = select(PermissionModel)
        count_query = select(func.count(PermissionModel.id))

        filters = []

        if search_params.query:
            search_filter = or_(
                PermissionModel.name.ilike(f"%{search_params.query}%"),
                PermissionModel.display_name.ilike(f"%{search_params.query}%"),
                PermissionModel.description.ilike(f"%{search_params.query}%"),
            )
            filters.append(search_filter)

        if search_params.permission_type is not None:
            filters.append(PermissionModel.permission_type == search_params.permission_type)

        if search_params.scope is not None:
            filters.append(PermissionModel.scope == search_params.scope)

        if search_params.resource is not None:
            filters.append(PermissionModel.resource.ilike(f"%{search_params.resource}%"))

        if search_params.is_active is not None:
            filters.append(PermissionModel.is_active == search_params.is_active)

        if search_params.is_system_permission is not None:
            filters.append(
                PermissionModel.is_system_permission == search_params.is_system_permission
            )

        if search_params.parent_permission_id is not None:
            filters.append(
                PermissionModel.parent_permission_id == search_params.parent_permission_id
            )

        # Apply filters
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Get total count
        count_result = await self.db_session.execute(count_query)
        total_count = count_result.scalar()

        # Apply sorting
        sort_column = getattr(PermissionModel, search_params.sort_by, PermissionModel.name)
        if search_params.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (search_params.page - 1) * search_params.page_size
        query = query.offset(offset).limit(search_params.page_size)

        result = await self.db_session.execute(query)
        permissions = result.scalars().all()

        return list(permissions), total_count

    @standard_exception_handler
    async def get_permissions_by_type_and_scope(
        self, permission_type: PermissionType, scope: PermissionScope
    ) -> list[PermissionModel]:
        """Get permissions by type and scope."""
        query = select(PermissionModel).where(
            and_(
                PermissionModel.permission_type == permission_type,
                PermissionModel.scope == scope,
                PermissionModel.is_active is True,
            )
        )

        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    @standard_exception_handler
    async def delete_permission(self, permission_id: UUID) -> bool:
        """Delete permission if it's not a system permission."""
        permission = await self.get_by_id(permission_id)
        if not permission:
            return False

        if permission.is_system_permission:
            raise ValueError("Cannot delete system permission")

        await self.delete(permission_id)
        return True

class RolePermissionRepository(BaseRepository[RolePermissionModel]):
    """Repository for role-permission associations."""

    def __init__(self, db_session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(db_session, RolePermissionModel, tenant_id)

    @standard_exception_handler
    async def assign_permission_to_role(
        self,
        role_id: UUID,
        permission_id: UUID,
        granted_by: Optional[UUID] = None,
        is_granted: bool = True,
        conditions: Optional[dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
    ) -> RolePermissionModel:
        """Assign permission to role."""
        role_permission = RolePermissionModel(
            role_id=role_id,
            permission_id=permission_id,
            granted_by=granted_by,
            is_granted=is_granted,
            conditions=conditions,
            expires_at=expires_at,
            is_active=True,
        )

        self.db_session.add(role_permission)
        await self.db_session.flush()
        return role_permission

    @standard_exception_handler
    async def revoke_permission_from_role(self, role_id: UUID, permission_id: UUID) -> bool:
        """Revoke permission from role."""
        query = delete(RolePermissionModel).where(
            and_(
                RolePermissionModel.role_id == role_id,
                RolePermissionModel.permission_id == permission_id,
            )
        )

        result = await self.db_session.execute(query)
        return result.rowcount > 0

    @standard_exception_handler
    async def get_role_permissions(self, role_id: UUID) -> list[PermissionModel]:
        """Get all permissions for a role."""
        query = (
            select(PermissionModel)
            .join(
                RolePermissionModel,
                RolePermissionModel.permission_id == PermissionModel.id,
            )
            .where(
                and_(
                    RolePermissionModel.role_id == role_id,
                    RolePermissionModel.is_granted is True,
                    RolePermissionModel.is_active is True,
                    or_(
                        RolePermissionModel.expires_at.is_(None),
                        RolePermissionModel.expires_at > datetime.now(timezone.utc),
                    ),
                )
            )
        )

        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    @standard_exception_handler
    async def bulk_assign_permissions(
        self,
        role_ids: list[UUID],
        permission_ids: list[UUID],
        granted_by: Optional[UUID] = None,
        is_granted: bool = True,
        expires_at: Optional[datetime] = None,
    ) -> list[RolePermissionModel]:
        """Bulk assign permissions to multiple roles."""
        role_permissions = []

        for role_id in role_ids:
            for permission_id in permission_ids:
                # Check if assignment already exists
                existing_query = select(RolePermissionModel).where(
                    and_(
                        RolePermissionModel.role_id == role_id,
                        RolePermissionModel.permission_id == permission_id,
                    )
                )
                result = await self.db_session.execute(existing_query)
                existing = result.scalar_one_or_none()

                if not existing:
                    role_permission = RolePermissionModel(
                        role_id=role_id,
                        permission_id=permission_id,
                        granted_by=granted_by,
                        is_granted=is_granted,
                        expires_at=expires_at,
                        is_active=True,
                    )
                    role_permissions.append(role_permission)
                    self.db_session.add(role_permission)

        await self.db_session.flush()
        return role_permissions

class UserRoleRepository(BaseRepository[UserRoleModel]):
    """Repository for user-role associations."""

    def __init__(self, db_session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(db_session, UserRoleModel, tenant_id)

    @standard_exception_handler
    async def assign_role_to_user(
        self,
        user_id: UUID,
        role_id: UUID,
        assigned_by: Optional[UUID] = None,
        assignment_reason: Optional[str] = None,
        scope_context: Optional[dict[str, Any]] = None,
        conditions: Optional[dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
    ) -> UserRoleModel:
        """Assign role to user."""
        # Check if assignment already exists
        existing = await self.get_user_role(user_id, role_id)
        if existing and existing.is_active:
            return existing

        user_role = UserRoleModel(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
            assignment_reason=assignment_reason,
            scope_context=scope_context,
            conditions=conditions,
            expires_at=expires_at,
            is_active=True,
        )

        self.db_session.add(user_role)
        await self.db_session.flush()
        return user_role

    @standard_exception_handler
    async def revoke_role_from_user(self, user_id: UUID, role_id: UUID) -> bool:
        """Revoke role from user."""
        query = (
            update(UserRoleModel)
            .where(and_(UserRoleModel.user_id == user_id, UserRoleModel.role_id == role_id))
            .values(is_active=False, updated_at=datetime.now(timezone.utc))
        )

        result = await self.db_session.execute(query)
        return result.rowcount > 0

    @standard_exception_handler
    async def get_user_role(self, user_id: UUID, role_id: UUID) -> Optional[UserRoleModel]:
        """Get specific user-role assignment."""
        query = select(UserRoleModel).where(
            and_(UserRoleModel.user_id == user_id, UserRoleModel.role_id == role_id)
        )

        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    @standard_exception_handler
    async def get_user_effective_permissions(self, user_id: UUID) -> set[str]:
        """Get all effective permissions for a user through their roles."""
        query = (
            select(PermissionModel.name)
            .join(
                RolePermissionModel,
                RolePermissionModel.permission_id == PermissionModel.id,
            )
            .join(RoleModel, RoleModel.id == RolePermissionModel.role_id)
            .join(UserRoleModel, UserRoleModel.role_id == RoleModel.id)
            .where(
                and_(
                    UserRoleModel.user_id == user_id,
                    UserRoleModel.is_active is True,
                    RoleModel.is_active is True,
                    RolePermissionModel.is_granted is True,
                    RolePermissionModel.is_active is True,
                    PermissionModel.is_active is True,
                    or_(
                        UserRoleModel.expires_at.is_(None),
                        UserRoleModel.expires_at > datetime.now(timezone.utc),
                    ),
                    or_(
                        RolePermissionModel.expires_at.is_(None),
                        RolePermissionModel.expires_at > datetime.now(timezone.utc),
                    ),
                )
            )
        )

        result = await self.db_session.execute(query)
        return set(result.scalars().all())

    @standard_exception_handler
    async def bulk_assign_roles(
        self,
        user_ids: list[UUID],
        role_ids: list[UUID],
        assigned_by: Optional[UUID] = None,
        assignment_reason: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> list[UserRoleModel]:
        """Bulk assign roles to multiple users."""
        user_roles = []

        for user_id in user_ids:
            for role_id in role_ids:
                # Check if assignment already exists and is active
                existing = await self.get_user_role(user_id, role_id)
                if not existing or not existing.is_active:
                    user_role = await self.assign_role_to_user(
                        user_id=user_id,
                        role_id=role_id,
                        assigned_by=assigned_by,
                        assignment_reason=assignment_reason,
                        expires_at=expires_at,
                    )
                    user_roles.append(user_role)

        return user_roles
