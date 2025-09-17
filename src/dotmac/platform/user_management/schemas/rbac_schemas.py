"""
RBAC (Role-Based Access Control) schemas for user management v2 system.
Provides Pydantic 2 validation for roles, permissions, and access control operations.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from dotmac.platform.core.enhanced.base_schemas import (
    BaseCreateSchema,
    BaseResponseSchema,
    BaseUpdateSchema,
    PaginatedResponseSchema,
)

# Define enums here to avoid circular imports
class PermissionType(str, Enum):
    """Permission types for granular access control."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


class PermissionScope(str, Enum):
    """Permission scopes for different resources."""
    USER = "user"
    BILLING = "billing"
    NETWORK = "network"
    SUPPORT = "support"
    SYSTEM = "system"
    API = "api"


class RoleCategory(str, Enum):
    """Role categories for organization."""

    SYSTEM = "system"
    ADMIN = "admin"
    USER = "user"
    CUSTOM = "custom"


# Role Schemas
class RoleCreateSchema(BaseCreateSchema):
    """Schema for creating new roles."""

    name: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_.-]+$")
    display_name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = Field(None, max_length=1000)
    parent_role_id: Optional[UUID] = None
    role_category: RoleCategory = Field(default=RoleCategory.CUSTOM)
    is_active: bool = Field(default=True)
    is_default: bool = Field(default=False)
    custom_metadata: Optional[dict[str, Any]] = None
    permission_ids: Optional[list[UUID]] = Field(default_factory=list)

    # Multi-app support
    app_scope: Optional[str] = Field(
        None,
        description="Application scope for this role (e.g., 'isp', 'crm', 'ecommerce')",
    )
    cross_app_permissions: Optional[dict[str, list[str]]] = Field(
        default_factory=dict,
        description="Permissions across multiple apps: {'isp': ['customers:read'], 'crm': ['leads:write']}",
    )

    @field_validator("name")
    @classmethod
    def validate_name_format(cls, v: str) -> str:
        """Validate role name format."""
        if not v.replace("_", "").replace("-", "").replace(".", "").isalnum():
            raise ValueError(
                "Role name can only contain letters, numbers, underscores, hyphens, and dots"
            )
        return v.lower()

    @field_validator("custom_metadata")
    @classmethod
    def validate_metadata(cls, v: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
        """Validate metadata is not too large."""
        if v and len(str(v)) > 10000:
            raise ValueError("Metadata too large")
        return v

    @field_validator("cross_app_permissions")
    @classmethod
    def validate_cross_app_permissions(
        cls, v: Optional[dict[str, list[str]]]
    ) -> Optional[dict[str, list[str]]]:
        """Validate cross-app permissions format."""
        if not v:
            return v

        valid_apps = {"isp", "crm", "ecommerce", "projects", "analytics", "lms"}
        for app_name, permissions in v.items():
            if app_name not in valid_apps:
                raise ValueError(f"Invalid app name: {app_name}. Must be one of: {valid_apps}")

            if not isinstance(permissions, list):
                raise ValueError(f"Permissions for app '{app_name}' must be a list")

            for perm in permissions:
                if not isinstance(perm, str) or ":" not in perm:
                    raise ValueError(f"Permission '{perm}' must be in format 'resource:action'")

        return v


class RoleUpdateSchema(BaseUpdateSchema):
    """Schema for updating existing roles."""

    name: Optional[str] = Field(None, min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_.-]+$")
    display_name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = Field(None, max_length=1000)
    parent_role_id: Optional[UUID] = None
    role_category: Optional[RoleCategory] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    metadata: Optional[dict[str, Any]] = None

    @field_validator("name")
    @classmethod
    def validate_name_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate role name format."""
        if v and not v.replace("_", "").replace("-", "").replace(".", "").isalnum():
            raise ValueError(
                "Role name can only contain letters, numbers, underscores, hyphens, and dots"
            )
        return v.lower() if v else v


class RoleResponseSchema(BaseResponseSchema):
    """Schema for role responses."""

    name: str
    display_name: str
    description: Optional[str] = None
    parent_role_id: Optional[UUID] = None
    role_category: str
    is_active: bool
    is_system_role: bool
    is_default: bool
    tenant_id: Optional[UUID] = None
    metadata: Optional[dict[str, Any]] = None

    # Computed fields
    permission_count: Optional[int] = None
    user_count: Optional[int] = None
    parent_role_name: Optional[str] = None
    child_role_count: Optional[int] = None


class RoleDetailResponseSchema(RoleResponseSchema):
    """Detailed role response with related data."""

    permissions: list["PermissionResponseSchema"] = Field(default_factory=list)
    child_roles: list[RoleResponseSchema] = Field(default_factory=list)
    parent_role: Optional[RoleResponseSchema] = None


# Permission Schemas
class PermissionCreateSchema(BaseCreateSchema):
    """Schema for creating new permissions."""

    name: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_:.-]+$")
    display_name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = Field(None, max_length=1000)
    permission_type: PermissionType
    scope: PermissionScope
    resource: str = Field(..., min_length=1, max_length=100)
    parent_permission_id: Optional[UUID] = None
    is_active: bool = Field(default=True)
    conditions: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None

    @field_validator("name")
    @classmethod
    def validate_name_format(cls, v: str) -> str:
        """Validate permission name format."""
        if not all(c.isalnum() or c in "_:.-" for c in v):
            raise ValueError(
                "Permission name can only contain letters, numbers, underscores, colons, hyphens, and dots"
            )
        return v.lower()

    @field_validator("resource")
    @classmethod
    def validate_resource_format(cls, v: str) -> str:
        """Validate resource name format."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Resource name can only contain letters, numbers, underscores, and hyphens"
            )
        return v.lower()


class PermissionUpdateSchema(BaseUpdateSchema):
    """Schema for updating existing permissions."""

    display_name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None
    conditions: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None


class PermissionResponseSchema(BaseResponseSchema):
    """Schema for permission responses."""

    name: str
    display_name: str
    description: Optional[str] = None
    permission_type: str
    scope: str
    resource: str
    parent_permission_id: Optional[UUID] = None
    is_active: bool
    is_system_permission: bool
    conditions: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None

    # Computed fields
    child_permission_count: Optional[int] = None
    role_count: Optional[int] = None


# Role-Permission Association Schemas
class RolePermissionCreateSchema(BaseCreateSchema):
    """Schema for assigning permissions to roles."""

    role_id: UUID
    permission_id: UUID
    is_granted: bool = Field(default=True)
    conditions: Optional[dict[str, Any]] = None
    expires_at: Optional[datetime] = None


class RolePermissionUpdateSchema(BaseUpdateSchema):
    """Schema for updating role-permission assignments."""

    is_granted: Optional[bool] = None
    conditions: Optional[dict[str, Any]] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class RolePermissionResponseSchema(BaseResponseSchema):
    """Schema for role-permission assignment responses."""

    role_id: UUID
    permission_id: UUID
    is_granted: bool
    conditions: Optional[dict[str, Any]] = None
    granted_by: Optional[UUID] = None
    granted_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool

    # Related data
    role_name: Optional[str] = None
    permission_name: Optional[str] = None


# User-Role Association Schemas
class UserRoleCreateSchema(BaseCreateSchema):
    """Schema for assigning roles to users."""

    user_id: UUID
    role_id: UUID
    assignment_reason: Optional[str] = Field(None, max_length=255)
    scope_context: Optional[dict[str, Any]] = None
    conditions: Optional[dict[str, Any]] = None
    expires_at: Optional[datetime] = None


class UserRoleUpdateSchema(BaseUpdateSchema):
    """Schema for updating user-role assignments."""

    assignment_reason: Optional[str] = Field(None, max_length=255)
    scope_context: Optional[dict[str, Any]] = None
    conditions: Optional[dict[str, Any]] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class UserRoleResponseSchema(BaseResponseSchema):
    """Schema for user-role assignment responses."""

    user_id: UUID
    role_id: UUID
    assigned_by: Optional[UUID] = None
    assigned_at: datetime
    assignment_reason: Optional[str] = None
    scope_context: Optional[dict[str, Any]] = None
    conditions: Optional[dict[str, Any]] = None
    expires_at: Optional[datetime] = None
    is_active: bool

    # Related data
    user_username: Optional[str] = None
    role_name: Optional[str] = None


# Bulk Operations Schemas
class BulkRoleAssignmentSchema(BaseModel):
    """Schema for bulk role assignments."""

    model_config = ConfigDict(str_strip_whitespace=True)

    user_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    role_ids: list[UUID] = Field(..., min_length=1, max_length=10)
    assignment_reason: Optional[str] = Field(None, max_length=255)
    expires_at: Optional[datetime] = None

    @field_validator("user_ids")
    @classmethod
    def validate_user_ids(cls, v: list[UUID]) -> list[UUID]:
        """Validate user ID list."""
        if len(set(v)) != len(v):
            raise ValueError("Duplicate user IDs not allowed")
        return v

    @field_validator("role_ids")
    @classmethod
    def validate_role_ids(cls, v: list[UUID]) -> list[UUID]:
        """Validate role ID list."""
        if len(set(v)) != len(v):
            raise ValueError("Duplicate role IDs not allowed")
        return v


class BulkPermissionAssignmentSchema(BaseModel):
    """Schema for bulk permission assignments to roles."""

    model_config = ConfigDict(str_strip_whitespace=True)

    role_ids: list[UUID] = Field(..., min_length=1, max_length=10)
    permission_ids: list[UUID] = Field(..., min_length=1, max_length=50)
    is_granted: bool = Field(default=True)
    expires_at: Optional[datetime] = None


# Search and Filter Schemas
class RoleSearchSchema(BaseModel):
    """Schema for role search and filtering."""

    model_config = ConfigDict(str_strip_whitespace=True)

    query: Optional[str] = Field(None, min_length=1, max_length=100)
    role_category: Optional[RoleCategory] = None
    is_active: Optional[bool] = None
    is_system_role: Optional[bool] = None
    is_default: Optional[bool] = None
    parent_role_id: Optional[UUID] = None
    has_permissions: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="name")
    sort_order: str = Field(default="asc", pattern=r"^(asc|desc)$")


class PermissionSearchSchema(BaseModel):
    """Schema for permission search and filtering."""

    model_config = ConfigDict(str_strip_whitespace=True)

    query: Optional[str] = Field(None, min_length=1, max_length=100)
    permission_type: Optional[PermissionType] = None
    scope: Optional[PermissionScope] = None
    resource: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None
    is_system_permission: Optional[bool] = None
    parent_permission_id: Optional[UUID] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="name")
    sort_order: str = Field(default="asc", pattern=r"^(asc|desc)$")


# Permission Group Schemas
class PermissionGroupCreateSchema(BaseCreateSchema):
    """Schema for creating permission groups."""

    name: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_.-]+$")
    display_name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = Field(None, max_length=1000)
    category: str = Field(..., min_length=1, max_length=50)
    priority: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)
    permission_ids: list[UUID] = Field(default_factory=list, max_length=50)
    metadata: Optional[dict[str, Any]] = None


class PermissionGroupResponseSchema(BaseResponseSchema):
    """Schema for permission group responses."""

    name: str
    display_name: str
    description: Optional[str] = None
    category: str
    priority: int
    is_active: bool
    metadata: Optional[dict[str, Any]] = None

    # Computed fields
    permission_count: Optional[int] = None
    permissions: Optional[list[PermissionResponseSchema]] = None


# Access Control Check Schemas
class PermissionCheckRequestSchema(BaseModel):
    """Schema for checking user permissions."""

    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: UUID
    permission_name: str = Field(..., min_length=1, max_length=100)
    resource_id: Optional[str] = None
    context: Optional[dict[str, Any]] = None


class PermissionCheckResponseSchema(BaseModel):
    """Schema for permission check responses."""

    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: UUID
    permission_name: str
    has_permission: bool
    granted_by_roles: list[str] = Field(default_factory=list)
    denied_reason: Optional[str] = None
    context_matched: bool = True


class UserPermissionSummarySchema(BaseModel):
    """Schema for user permission summary."""

    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: UUID
    effective_permissions: list[str] = Field(default_factory=list)
    roles: list[RoleResponseSchema] = Field(default_factory=list)
    permission_details: list[PermissionResponseSchema] = Field(default_factory=list)
    computed_at: datetime = Field(default_factory=datetime.utcnow)


# Response Collections
RolePaginatedResponseSchema = PaginatedResponseSchema[RoleResponseSchema]
PermissionPaginatedResponseSchema = PaginatedResponseSchema[PermissionResponseSchema]
RolePermissionPaginatedResponseSchema = PaginatedResponseSchema[RolePermissionResponseSchema]
UserRolePaginatedResponseSchema = PaginatedResponseSchema[UserRoleResponseSchema]
