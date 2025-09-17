"""
RBAC (Role-Based Access Control) service for user management v2 system.
Provides comprehensive role and permission management with multi-tenant support.
"""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.observability.logging import get_logger
from dotmac.platform.observability.unified_logging import get_logger

from dotmac.platform.core.decorators import standard_exception_handler

from ..models.rbac_models import RoleModel, RolePermissionModel, UserRoleModel
from ..repositories.rbac_repository import (
    PermissionRepository,
    RolePermissionRepository,
    RoleRepository,
    UserRoleRepository,
)
from ..repositories.user_repository import UserRepository
from ..schemas.rbac_schemas import (
    BulkPermissionAssignmentSchema,
    PermissionCheckResponseSchema,
    PermissionCreateSchema,
    PermissionResponseSchema,
    PermissionSearchSchema,
    RoleCreateSchema,
    RoleDetailResponseSchema,
    RoleResponseSchema,
    RoleSearchSchema,
    RoleUpdateSchema,
    UserPermissionSummarySchema,
)
from .base_service import BaseService

logger = get_logger(__name__)

class RBACService(BaseService):
    """Service for Role-Based Access Control operations."""

    def __init__(self, db_session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(db_session, tenant_id)
        self.role_repo = RoleRepository(db_session, tenant_id)
        self.permission_repo = PermissionRepository(db_session, tenant_id)
        self.role_permission_repo = RolePermissionRepository(db_session, tenant_id)
        self.user_role_repo = UserRoleRepository(db_session, tenant_id)
        self.user_repo = UserRepository(db_session, tenant_id)

    # Role Management
    @standard_exception_handler
    async def create_role(
        self, role_data: RoleCreateSchema, created_by: Optional[UUID] = None
    ) -> RoleResponseSchema:
        """
        Create new role with permissions.

        Args:
            role_data: Role creation data
            created_by: User who created the role

        Returns:
            Created role information
        """
        # Check if role name already exists
        existing_role = await self.role_repo.get_role_by_name(role_data.name)
        if existing_role:
            raise ValueError(f"Role '{role_data.name}' already exists")

        # Validate parent role if specified
        if role_data.parent_role_id:
            parent_role = await self.role_repo.get_by_id(role_data.parent_role_id)
            if not parent_role:
                raise ValueError("Parent role not found")
            if parent_role.tenant_id != self.tenant_id:
                raise ValueError("Parent role belongs to different tenant")

        # Validate permissions if specified
        if role_data.permission_ids:
            for permission_id in role_data.permission_ids:
                permission = await self.permission_repo.get_by_id(permission_id)
                if not permission:
                    raise ValueError(f"Permission {permission_id} not found")
                if not permission.is_active:
                    raise ValueError(f"Permission {permission_id} is not active")

        role = await self.role_repo.create_role(role_data, created_by)

        logger.info(
            f"Created role {role.name} with {len(role_data.permission_ids or [])} permissions"
        )
        return RoleResponseSchema.model_validate(role)

    @standard_exception_handler
    async def update_role(
        self,
        role_id: UUID,
        role_data: RoleUpdateSchema,
        updated_by: Optional[UUID] = None,
    ) -> RoleResponseSchema:
        """Update existing role."""
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise ValueError("Role not found")

        if role.is_system_role and role_data.name:
            raise ValueError("Cannot rename system role")

        # Check name uniqueness if changing name
        if role_data.name and role_data.name != role.name:
            existing_role = await self.role_repo.get_role_by_name(role_data.name)
            if existing_role:
                raise ValueError(f"Role '{role_data.name}' already exists")

        # Validate parent role if changing
        if role_data.parent_role_id:
            if role_data.parent_role_id == role_id:
                raise ValueError("Role cannot be its own parent")

            parent_role = await self.role_repo.get_by_id(role_data.parent_role_id)
            if not parent_role:
                raise ValueError("Parent role not found")

        updated_role = await self.role_repo.update(
            role_id, **role_data.model_dump(exclude_unset=True)
        )

        logger.info(f"Updated role {updated_role.name}")
        return RoleResponseSchema.model_validate(updated_role)

    @standard_exception_handler
    async def get_role_details(self, role_id: UUID) -> RoleDetailResponseSchema:
        """Get role with detailed information including permissions and relationships."""
        role = await self.role_repo.get_role_with_permissions(role_id)
        if not role:
            raise ValueError("Role not found")

        # Get permissions
        permissions = await self.role_permission_repo.get_role_permissions(role_id)
        permission_schemas = [PermissionResponseSchema.model_validate(p) for p in permissions]

        # Get child roles
        child_roles = [RoleResponseSchema.model_validate(child) for child in role.child_roles]

        # Get parent role
        parent_role = None
        if role.parent_role:
            parent_role = RoleResponseSchema.model_validate(role.parent_role)

        role_schema = RoleResponseSchema.model_validate(role)

        return RoleDetailResponseSchema(
            **role_schema.model_dump(),
            permissions=permission_schemas,
            child_roles=child_roles,
            parent_role=parent_role,
        )

    @standard_exception_handler
    async def search_roles(
        self, search_params: RoleSearchSchema
    ) -> tuple[list[RoleResponseSchema], int]:
        """Search roles with filters and pagination."""
        roles, total_count = await self.role_repo.search_roles(search_params)

        role_schemas = []
        for role in roles:
            role_schema = RoleResponseSchema.model_validate(role)
            # Add computed fields
            role_schema.permission_count = len(role.permissions)
            role_schema.user_count = len(role.user_roles)
            role_schema.child_role_count = len(role.child_roles)
            if role.parent_role:
                role_schema.parent_role_name = role.parent_role.name
            role_schemas.append(role_schema)

        return role_schemas, total_count

    @standard_exception_handler
    async def delete_role(self, role_id: UUID) -> bool:
        """Delete role if it's not a system role and has no users."""
        success = await self.role_repo.delete_role(role_id)
        if success:
            logger.info(f"Deleted role {role_id}")
        return success

    # Permission Management
    @standard_exception_handler
    async def create_permission(
        self, permission_data: PermissionCreateSchema, created_by: Optional[UUID] = None
    ) -> PermissionResponseSchema:
        """Create new permission."""
        # Check if permission name already exists
        existing_permission = await self.permission_repo.get_permission_by_name(
            permission_data.name
        )
        if existing_permission:
            raise ValueError(f"Permission '{permission_data.name}' already exists")

        # Validate parent permission if specified
        if permission_data.parent_permission_id:
            parent_permission = await self.permission_repo.get_by_id(
                permission_data.parent_permission_id
            )
            if not parent_permission:
                raise ValueError("Parent permission not found")

        permission = await self.permission_repo.create_permission(permission_data, created_by)

        logger.info(f"Created permission {permission.name}")
        return PermissionResponseSchema.model_validate(permission)

    @standard_exception_handler
    async def search_permissions(
        self, search_params: PermissionSearchSchema
    ) -> tuple[list[PermissionResponseSchema], int]:
        """Search permissions with filters and pagination."""
        permissions, total_count = await self.permission_repo.search_permissions(search_params)

        permission_schemas = []
        for permission in permissions:
            permission_schema = PermissionResponseSchema.model_validate(permission)
            # Add computed fields
            permission_schema.child_permission_count = len(permission.child_permissions)
            permission_schema.role_count = len(permission.role_permissions)
            permission_schemas.append(permission_schema)

        return permission_schemas, total_count

    # Role-Permission Management
    @standard_exception_handler
    async def assign_permission_to_role(
        self,
        role_id: UUID,
        permission_id: UUID,
        granted_by: Optional[UUID] = None,
        conditions: Optional[dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
    ) -> bool:
        """Assign permission to role."""
        # Validate role and permission exist
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise ValueError("Role not found")

        permission = await self.permission_repo.get_by_id(permission_id)
        if not permission:
            raise ValueError("Permission not found")

        # Check if assignment already exists
        existing_permissions = await self.role_permission_repo.get_role_permissions(role_id)
        if permission in existing_permissions:
            return True  # Already assigned

        await self.role_permission_repo.assign_permission_to_role(
            role_id=role_id,
            permission_id=permission_id,
            granted_by=granted_by,
            conditions=conditions,
            expires_at=expires_at,
        )

        logger.info(f"Assigned permission {permission.name} to role {role.name}")
        return True

    @standard_exception_handler
    async def revoke_permission_from_role(self, role_id: UUID, permission_id: UUID) -> bool:
        """Revoke permission from role."""
        success = await self.role_permission_repo.revoke_permission_from_role(
            role_id, permission_id
        )
        if success:
            logger.info(f"Revoked permission {permission_id} from role {role_id}")
        return success

    @standard_exception_handler
    async def bulk_assign_permissions(
        self, request: BulkPermissionAssignmentSchema, granted_by: Optional[UUID] = None
    ) -> list[RolePermissionModel]:
        """Bulk assign permissions to multiple roles."""
        # Validate all roles exist
        for role_id in request.role_ids:
            role = await self.role_repo.get_by_id(role_id)
            if not role:
                raise ValueError(f"Role {role_id} not found")

        # Validate all permissions exist
        for permission_id in request.permission_ids:
            permission = await self.permission_repo.get_by_id(permission_id)
            if not permission:
                raise ValueError(f"Permission {permission_id} not found")

        assignments = await self.role_permission_repo.bulk_assign_permissions(
            role_ids=request.role_ids,
            permission_ids=request.permission_ids,
            granted_by=granted_by,
            is_granted=request.is_granted,
            expires_at=request.expires_at,
        )

        logger.info(f"Bulk assigned {len(assignments)} permission assignments")
        return assignments

    # User-Role Management
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
    ) -> bool:
        """Assign role to user."""
        # Validate user exists
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        # Validate role exists
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise ValueError("Role not found")

        if not role.is_active:
            raise ValueError("Cannot assign inactive role")

        await self.user_role_repo.assign_role_to_user(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
            assignment_reason=assignment_reason,
            scope_context=scope_context,
            conditions=conditions,
            expires_at=expires_at,
        )

        logger.info(f"Assigned role {role.name} to user {user_id}")
        return True

    @standard_exception_handler
    async def revoke_role_from_user(self, user_id: UUID, role_id: UUID) -> bool:
        """Revoke role from user."""
        success = await self.user_role_repo.revoke_role_from_user(user_id, role_id)
        if success:
            logger.info(f"Revoked role {role_id} from user {user_id}")
        return success

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
        # Validate all users exist
        for user_id in user_ids:
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")

        # Validate all roles exist and are active
        for role_id in role_ids:
            role = await self.role_repo.get_by_id(role_id)
            if not role:
                raise ValueError(f"Role {role_id} not found")
            if not role.is_active:
                raise ValueError(f"Role {role_id} is not active")

        assignments = await self.user_role_repo.bulk_assign_roles(
            user_ids=user_ids,
            role_ids=role_ids,
            assigned_by=assigned_by,
            assignment_reason=assignment_reason,
            expires_at=expires_at,
        )

        logger.info(f"Bulk assigned {len(assignments)} role assignments")
        return assignments

    # Permission Checking and Authorization
    @standard_exception_handler
    async def check_user_permission(
        self,
        user_id: UUID,
        permission_name: str,
        resource_id: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> PermissionCheckResponseSchema:
        """
        Check if user has specific permission.

        Args:
            user_id: User ID to check
            permission_name: Name of permission to check
            resource_id: Optional resource ID for context-specific checks
            context: Optional context data for conditional permissions

        Returns:
            Permission check result with details
        """
        # Get user's effective permissions
        effective_permissions = await self.user_role_repo.get_user_effective_permissions(user_id)

        has_permission = permission_name in effective_permissions

        granted_by_roles = []
        denied_reason = None
        context_matched = True

        if has_permission:
            # Find which roles granted this permission
            user_roles = await self.role_repo.get_user_roles(user_id)
            for role in user_roles:
                role_permissions = await self.role_permission_repo.get_role_permissions(role.id)
                for permission in role_permissions:
                    if permission.name == permission_name:
                        granted_by_roles.append(role.name)
                        break
        else:
            denied_reason = "User does not have the required permission"

        # Context-specific permission checking would be implemented here
        # This would involve evaluating conditions and context data against permission rules

        return PermissionCheckResponseSchema(
            user_id=user_id,
            permission_name=permission_name,
            has_permission=has_permission,
            granted_by_roles=granted_by_roles,
            denied_reason=denied_reason,
            context_matched=context_matched,
        )

    @standard_exception_handler
    async def get_user_permission_summary(self, user_id: UUID) -> UserPermissionSummarySchema:
        """Get comprehensive permission summary for user."""
        # Get user's roles
        user_roles = await self.role_repo.get_user_roles(user_id)
        role_schemas = [RoleResponseSchema.model_validate(role) for role in user_roles]

        # Get effective permissions
        effective_permissions = await self.user_role_repo.get_user_effective_permissions(user_id)
        effective_permissions_list = list(effective_permissions)

        # Get detailed permission information
        permission_details = []
        for permission_name in effective_permissions_list:
            permission = await self.permission_repo.get_permission_by_name(permission_name)
            if permission:
                permission_details.append(PermissionResponseSchema.model_validate(permission))

        return UserPermissionSummarySchema(
            user_id=user_id,
            effective_permissions=effective_permissions_list,
            roles=role_schemas,
            permission_details=permission_details,
            computed_at=datetime.now(timezone.utc),
        )

    @standard_exception_handler
    async def assign_default_role_to_user(self, user_id: UUID) -> bool:
        """Assign default role to new user."""
        default_role = await self.role_repo.get_default_role()
        if not default_role:
            logger.warning("No default role configured for tenant")
            return False

        success = await self.assign_role_to_user(
            user_id=user_id,
            role_id=default_role.id,
            assignment_reason="Default role for new user",
        )

        if success:
            logger.info(f"Assigned default role {default_role.name} to user {user_id}")

        return success

    # Utility Methods
    @standard_exception_handler
    async def get_role_hierarchy(self, role_id: UUID) -> dict[str, Any]:
        """Get complete role hierarchy for a role."""
        role = await self.role_repo.get_role_with_permissions(role_id)
        if not role:
            return {}

        def build_hierarchy(role_model: RoleModel) -> dict[str, Any]:
            return {
                "id": str(role_model.id),
                "name": role_model.name,
                "display_name": role_model.display_name,
                "permission_count": len(role_model.permissions),
                "child_roles": [build_hierarchy(child) for child in role_model.child_roles],
            }

        return build_hierarchy(role)

    @standard_exception_handler
    async def validate_role_assignment(
        self, user_id: UUID, role_id: UUID, context: Optional[dict[str, Any]] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Validate if role can be assigned to user.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if user exists
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False, "User not found"

        # Check if role exists and is active
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            return False, "Role not found"

        if not role.is_active:
            return False, "Role is not active"

        # Check tenant isolation
        if role.tenant_id and role.tenant_id != self.tenant_id:
            return False, "Role belongs to different tenant"

        # Check if user already has role
        existing_assignment = await self.user_role_repo.get_user_role(user_id, role_id)
        if existing_assignment and existing_assignment.is_active:
            return False, "User already has this role"

        # Business rule validations would be implemented here based on specific requirements:
        # - Check role conflicts (e.g., user cannot have both admin and customer roles)
        # - Check maximum roles per user (e.g., limit to 5 roles per user)
        # - Check role prerequisites (e.g., manager role requires employee role first)

        return True, None
