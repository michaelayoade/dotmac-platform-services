"""
Convenience re-exports for FastAPI auth dependencies.

This module provides a stable import path for common dependency helpers.
"""

from __future__ import annotations

from .current_user import (
    RequireAdmin,
    RequireAdminAccess,
    RequireAdminRole,
    RequireAuthenticated,
    RequireModeratorRole,
    RequireReadAccess,
    RequireUserRole,
    RequireWriteAccess,
    ServiceClaims,
    UserClaims,
    get_current_service,
    get_current_tenant,
    get_current_user,
    get_optional_user,
    require_admin,
    require_roles,
    require_scopes,
    require_service_operation,
    require_tenant_access,
)

# Compatibility aliases for legacy import names
require_permissions = require_scopes  # type: ignore
get_current_active_user = get_current_user  # type: ignore

__all__ = [
    "RequireAdmin",
    "RequireAdminAccess",
    "RequireAdminRole",
    "RequireAuthenticated",
    "RequireModeratorRole",
    "RequireReadAccess",
    "RequireUserRole",
    "RequireWriteAccess",
    "ServiceClaims",
    "UserClaims",
    "get_current_active_user",
    "get_current_service",
    "get_current_tenant",
    "get_current_user",
    "get_optional_user",
    "require_admin",
    # Aliases
    "require_permissions",
    "require_roles",
    "require_scopes",
    "require_service_operation",
    "require_tenant_access",
]
