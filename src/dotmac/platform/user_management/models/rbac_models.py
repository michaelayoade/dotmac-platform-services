"""
Role-Based Access Control (RBAC) models for user management v2 system.
Implements comprehensive role and permission management with multi-tenant support.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from dotmac.platform.database.base import BaseModel


# Import enums from schemas to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..schemas.rbac_schemas import PermissionType, PermissionScope


class RoleModel(BaseModel):
    """
    Role model for RBAC system.
    Defines roles that can be assigned to users with specific permissions.
    """

    __tablename__ = "roles_v2"

    # Basic role information
    name = Column(String(100), nullable=False, index=True)
    display_name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)

    # Role hierarchy and categorization
    parent_role_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("roles_v2.id"), nullable=True)
    role_category = Column(
        String(50), nullable=False, default="custom"
    )  # system, admin, user, custom

    # Status and configuration
    is_active = Column(Boolean, default=True, nullable=False)
    is_system_role = Column(Boolean, default=False, nullable=False)  # Cannot be deleted
    is_default = Column(Boolean, default=False, nullable=False)  # Default role for new users

    # Tenant isolation
    tenant_id = Column(PostgreSQLUUID(as_uuid=True), nullable=True, index=True)

    # Multi-app support
    app_scope = Column(
        String(50), nullable=True, index=True
    )  # Application scope (e.g., 'isp', 'crm', 'ecommerce')
    cross_app_permissions = Column(
        JSON, nullable=True
    )  # Cross-app permissions: {'isp': ['customers:read'], 'crm': ['leads:write']}

    # Metadata and configuration
    custom_metadata = Column(JSON, nullable=True)  # Additional role configuration

    # Relationships
    parent_role = relationship(
        "RoleModel", remote_side="RoleModel.id", back_populates="child_roles"
    )
    child_roles = relationship(
        "RoleModel", back_populates="parent_role", cascade="all, delete-orphan"
    )
    permissions = relationship(
        "RolePermissionModel", back_populates="role", cascade="all, delete-orphan"
    )
    user_roles = relationship("UserRoleModel", back_populates="role", cascade="all, delete-orphan")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("name", "tenant_id", name="uq_roles_name_tenant"),
        Index("idx_roles_active_category", "is_active", "role_category"),
        Index("idx_roles_tenant_active", "tenant_id", "is_active"),
        Index("idx_roles_app_scope", "app_scope", "tenant_id"),
    )

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}', tenant_id={self.tenant_id})>"


class PermissionModel(BaseModel):
    """
    Permission model defining specific access rights.
    Permissions are assigned to roles and define what actions can be performed.
    """

    __tablename__ = "permissions_v2"

    # Permission identification
    name = Column(String(100), nullable=False, unique=True, index=True)
    display_name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)

    # Permission categorization
    permission_type = Column(String(20), nullable=False, index=True)  # read, write, delete, admin
    scope = Column(String(20), nullable=False, index=True)  # user, billing, network, support, system, api
    resource = Column(
        String(100), nullable=False, index=True
    )  # Specific resource (users, invoices, etc.)

    # Permission hierarchy and dependencies
    parent_permission_id = Column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("permissions_v2.id"), nullable=True
    )

    # Status and system flags
    is_active = Column(Boolean, default=True, nullable=False)
    is_system_permission = Column(Boolean, default=False, nullable=False)  # Cannot be deleted

    # Multi-app support
    app_scope = Column(
        String(50), nullable=True, index=True
    )  # Application scope for this permission

    # Metadata for complex permissions
    conditions = Column(JSON, nullable=True)  # Conditional permission logic
    custom_metadata = Column(JSON, nullable=True)  # Additional permission data

    # Relationships
    parent_permission = relationship(
        "PermissionModel",
        remote_side="PermissionModel.id",
        back_populates="child_permissions",
    )
    child_permissions = relationship(
        "PermissionModel",
        back_populates="parent_permission",
        cascade="all, delete-orphan",
    )
    role_permissions = relationship(
        "RolePermissionModel", back_populates="permission", cascade="all, delete-orphan"
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_permissions_v2_type_scope", "permission_type", "scope"),
        Index("idx_permissions_v2_resource_active", "resource", "is_active"),
    )

    def __repr__(self):
        return f"<Permission(id={self.id}, name='{self.name}', type={self.permission_type.value})>"


class RolePermissionModel(BaseModel):
    """
    Association model linking roles to permissions.
    Enables many-to-many relationship with additional metadata.
    """

    __tablename__ = "role_permissions_v2"

    # Foreign keys
    role_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("roles_v2.id", ondelete="CASCADE"),
        nullable=False,
    )
    permission_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("permissions_v2.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Permission customization
    is_granted = Column(
        Boolean, default=True, nullable=False
    )  # Permission can be explicitly denied
    conditions = Column(JSON, nullable=True)  # Role-specific permission conditions

    # Grant information
    granted_by = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("users_v2.id"), nullable=True)
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Expiry and status
    expires_at = Column(DateTime, nullable=True)  # Temporary permissions
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    role = relationship("RoleModel", back_populates="permissions")
    permission = relationship("PermissionModel", back_populates="role_permissions")
    granted_by_user = relationship("UserModel", foreign_keys=[granted_by])

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_v2_role_permission"),
        Index("idx_role_permissions_v2_role_active", "role_id", "is_active"),
        Index("idx_role_permissions_v2_permission_granted", "permission_id", "is_granted"),
        Index("idx_role_permissions_v2_expires", "expires_at"),
    )

    def __repr__(self):
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id}, granted={self.is_granted})>"


class UserRoleModel(BaseModel):
    """
    Association model linking users to roles.
    Supports role assignment with context and expiry.
    """

    __tablename__ = "user_roles_v2"

    # Foreign keys
    user_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users_v2.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("roles_v2.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Assignment context
    assigned_by = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("users_v2.id"), nullable=True)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    assignment_reason = Column(String(255), nullable=True)  # Why role was assigned

    # Role scope and limitations
    scope_context = Column(JSON, nullable=True)  # Context-specific role assignment
    conditions = Column(JSON, nullable=True)  # Conditional role activation

    # Expiry and status
    expires_at = Column(DateTime, nullable=True)  # Temporary role assignment
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    user = relationship("UserModel", foreign_keys=[user_id], back_populates="user_roles")
    role = relationship("RoleModel", back_populates="user_roles")
    assigned_by_user = relationship("UserModel", foreign_keys=[assigned_by])

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_v2_user_role"),
        Index("idx_user_roles_v2_user_active", "user_id", "is_active"),
        Index("idx_user_roles_v2_role_active", "role_id", "is_active"),
        Index("idx_user_roles_v2_expires", "expires_at"),
        Index("idx_user_roles_v2_assigned_by", "assigned_by"),
    )

    def __repr__(self):
        return (
            f"<UserRole(user_id={self.user_id}, role_id={self.role_id}, active={self.is_active})>"
        )


class PermissionGroupModel(BaseModel):
    """
    Permission groups for organizing related permissions.
    Simplifies role management by grouping common permissions.
    """

    __tablename__ = "permission_groups_v2"

    # Group information
    name = Column(String(100), nullable=False, unique=True, index=True)
    display_name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)

    # Categorization
    category = Column(String(50), nullable=False, index=True)
    priority = Column(Integer, default=0, nullable=False)  # Display order

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Metadata
    custom_metadata = Column(JSON, nullable=True)

    # Relationships
    permissions = relationship(
        "PermissionGroupItemModel", back_populates="group", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_permission_groups_v2_category_active", "category", "is_active"),)

    def __repr__(self):
        return f"<PermissionGroup(id={self.id}, name='{self.name}')>"


class PermissionGroupItemModel(BaseModel):
    """
    Association model for permission groups and permissions.
    """

    __tablename__ = "permission_group_items_v2"

    # Foreign keys
    group_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("permission_groups_v2.id", ondelete="CASCADE"),
        nullable=False,
    )
    permission_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("permissions_v2.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Item configuration
    is_required = Column(Boolean, default=False, nullable=False)  # Required for group
    order_index = Column(Integer, default=0, nullable=False)  # Display order

    # Relationships
    group = relationship("PermissionGroupModel", back_populates="permissions")
    permission = relationship("PermissionModel")

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "group_id",
            "permission_id",
            name="uq_permission_group_items_v2_group_permission",
        ),
        Index("idx_permission_group_items_v2_group", "group_id"),
    )

    def __repr__(self):
        return (
            f"<PermissionGroupItem(group_id={self.group_id}, permission_id={self.permission_id})>"
        )
