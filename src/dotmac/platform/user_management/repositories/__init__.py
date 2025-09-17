"""
Production-ready repository layer for user management.
Implements comprehensive data access patterns.
"""

from .auth_repository import (
    ApiKeyRepository,
    AuthAuditRepository,
    AuthRepository,
    MFARepository,
    SessionRepository,
)
from .rbac_repository import (
    PermissionRepository,
    RolePermissionRepository,
    RoleRepository,
    UserRoleRepository,
    count_query,
    count_result,
    existing,
    existing_query,
    filters,
    logger,
    offset,
    permission,
    permission_dict,
    permissions,
    query,
    result,
    role,
    role_dict,
    role_permission,
    role_permissions,
    roles,
    search_filter,
    sort_column,
    total_count,
    user_count,
    user_count_query,
    user_role,
    user_roles,
)
from .user_repository import UserProfileRepository, UserRepository, UserSearchRepository

__all__ = [
    # User repositories
    "UserRepository",
    "UserProfileRepository",
    "UserSearchRepository",
    # Authentication repositories
    "AuthRepository",
    "SessionRepository",
    "MFARepository",
    "ApiKeyRepository",
    "AuthAuditRepository",
    # Role and permission repositories
    "RoleRepository",
    "PermissionRepository",
    # Base repository
    "BaseRepository",
]
