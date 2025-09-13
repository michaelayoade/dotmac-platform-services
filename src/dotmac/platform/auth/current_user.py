"""
Current User Dependencies and Helpers

FastAPI dependencies for user authentication and authorization helpers.
"""

from typing import Any

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from .exceptions import (
    AuthError,
    InsufficientRole,
    InsufficientScope,
    TokenNotFound,
    get_http_status,
)


class UserClaims(BaseModel):
    """
    User claims model from JWT token.

    Provides structured access to user information and permissions.
    """

    user_id: str = Field(alias="sub", description="User ID")
    tenant_id: str | None = Field(None, description="Tenant ID")
    scopes: list[str] = Field(default_factory=list, description="User scopes/permissions")
    roles: list[str] = Field(default_factory=list, description="User roles")
    email: str | None = Field(None, description="User email")
    username: str | None = Field(None, description="Username")
    full_name: str | None = Field(None, description="Full name")

    # Token metadata
    issued_at: int | None = Field(None, alias="iat", description="Token issued at")
    expires_at: int | None = Field(None, alias="exp", description="Token expires at")
    token_id: str | None = Field(None, alias="jti", description="Token ID")
    issuer: str | None = Field(None, alias="iss", description="Token issuer")
    audience: str | None = Field(None, alias="aud", description="Token audience")

    # Authentication metadata
    authenticated: bool = Field(True, description="Whether user is authenticated")
    is_service: bool = Field(False, description="Whether this is a service token")

    # Custom claims
    extra_claims: dict[str, Any] = Field(default_factory=dict, description="Additional claims")

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.authenticated and bool(self.user_id)

    def has_scope(self, scope: str) -> bool:
        """Check if user has a specific scope"""
        return scope in self.scopes

    def has_any_scope(self, scopes: list[str]) -> bool:
        """Check if user has any of the specified scopes"""
        return any(scope in self.scopes for scope in scopes)

    def has_all_scopes(self, scopes: list[str]) -> bool:
        """Check if user has all specified scopes"""
        return all(scope in self.scopes for scope in scopes)

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role"""
        return role in self.roles

    def has_any_role(self, roles: list[str]) -> bool:
        """Check if user has any of the specified roles"""
        return any(role in self.roles for role in roles)

    def has_all_roles(self, roles: list[str]) -> bool:
        """Check if user has all specified roles"""
        return all(role in self.roles for role in roles)

    def is_admin(self) -> bool:
        """Check if user has admin privileges"""
        admin_roles = ["admin", "super_admin", "system_admin"]
        admin_scopes = ["admin:read", "admin:write", "admin:*"]
        return self.has_any_role(admin_roles) or self.has_any_scope(admin_scopes)

    def can_access_tenant(self, tenant_id: str) -> bool:
        """Check if user can access specified tenant"""
        # User can access their own tenant
        if self.tenant_id == tenant_id:
            return True

        # Admins can access any tenant
        if self.is_admin():
            return True

        # Check for cross-tenant access scopes
        cross_tenant_scopes = ["tenant:access:*", f"tenant:access:{tenant_id}"]
        return self.has_any_scope(cross_tenant_scopes)


class ServiceClaims(BaseModel):
    """
    Service claims model for service-to-service authentication.
    """

    service_name: str = Field(alias="sub", description="Service name")
    target_service: str = Field(description="Target service")
    allowed_operations: list[str] = Field(default_factory=list, description="Allowed operations")
    tenant_id: str | None = Field(None, description="Tenant context")

    # Token metadata
    issued_at: int | None = Field(None, alias="iat")
    expires_at: int | None = Field(None, alias="exp")
    token_id: str | None = Field(None, alias="jti")
    identity_id: str = Field(description="Service identity ID")

    # Authentication metadata
    authenticated: bool = Field(True)
    is_service: bool = Field(True)

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    def can_perform_operation(self, operation: str) -> bool:
        """Check if service can perform operation"""
        return operation in self.allowed_operations or "*" in self.allowed_operations


_CURRENT_USER_CTX: "CurrentUser | None" = None


def get_current_user(request: Request):
    """
    FastAPI dependency to get current authenticated user.

    Args:
        request: FastAPI request object

    Returns:
        UserClaims object with user information

    Raises:
        HTTPException: If user is not authenticated
    """
    try:
        # Check if user claims are available in request state
        if not hasattr(request.state, "user_claims"):
            raise TokenNotFound("User authentication required")

        claims_data = getattr(request.state, "user_claims", None)
        if not claims_data:
            raise TokenNotFound("User authentication required")

        # Check if user is authenticated
        if not claims_data.get("authenticated", False):
            raise TokenNotFound("User authentication required")

        # Don't allow service tokens for user endpoints
        if claims_data.get("is_service", False):
            raise AuthError("Service tokens not allowed for user endpoints")

        # Create UserClaims object
        return UserClaims(**claims_data)

    except AuthError as e:
        raise HTTPException(status_code=get_http_status(e), detail=e.to_dict()) from e
    except Exception as e:
        raise HTTPException(
            status_code=401, detail={"error": "AUTHENTICATION_ERROR", "message": str(e)}
        ) from e


# Compatibility model and helpers expected by some tests
class CurrentUser(BaseModel):
    id: str
    username: str | None = None
    email: str | None = None
    roles: list[str] = []
    scopes: list[str] = []
    tenant_id: str | None = None


class UserContext(BaseModel):
    user: CurrentUser | None = None
    authenticated: bool = False


def set_current_user(user: CurrentUser | None) -> None:
    global _CURRENT_USER_CTX
    _CURRENT_USER_CTX = user


def clear_current_user() -> None:
    set_current_user(None)


def get_current_user_context() -> CurrentUser | None:
    """Return the current user stored in module-level context (test helper)."""
    return _CURRENT_USER_CTX


def get_current_service(request: Request) -> ServiceClaims:
    """
    FastAPI dependency to get current authenticated service.

    Args:
        request: FastAPI request object

    Returns:
        ServiceClaims object with service information

    Raises:
        HTTPException: If service is not authenticated
    """
    try:
        # Check if service claims are available in request state
        if not hasattr(request.state, "service_claims"):
            raise TokenNotFound("Service authentication required")

        claims_data = getattr(request.state, "service_claims", None)
        if not claims_data:
            raise TokenNotFound("Service authentication required")

        # Check if service is authenticated
        if not claims_data.get("service_authenticated", False):
            raise TokenNotFound("Service authentication required")

        # Create ServiceClaims object
        return ServiceClaims(**claims_data)

    except AuthError as e:
        raise HTTPException(status_code=get_http_status(e), detail=e.to_dict()) from e
    except Exception as e:
        raise HTTPException(
            status_code=401, detail={"error": "SERVICE_AUTHENTICATION_ERROR", "message": str(e)}
        ) from e


def get_optional_user(request: Request) -> UserClaims | None:
    """
    FastAPI dependency to optionally get current user.

    Returns None if no user is authenticated instead of raising an exception.

    Args:
        request: FastAPI request object

    Returns:
        UserClaims object or None
    """
    try:
        return get_current_user(request)
    except HTTPException:
        return None


def require_scopes(required_scopes: list[str], require_all: bool = False):
    """
    FastAPI dependency factory to require specific scopes.

    Args:
        required_scopes: List of required scopes
        require_all: Whether all scopes are required (vs any)

    Returns:
        Dependency function
    """

    def _require_scopes(current_user: UserClaims = Depends(get_current_user)) -> UserClaims:
        if require_all:
            if not current_user.has_all_scopes(required_scopes):
                raise HTTPException(
                    status_code=403,
                    detail=InsufficientScope(
                        required_scopes=required_scopes, user_scopes=current_user.scopes
                    ).to_dict(),
                )
        elif not current_user.has_any_scope(required_scopes):
            raise HTTPException(
                status_code=403,
                detail=InsufficientScope(
                    required_scopes=required_scopes, user_scopes=current_user.scopes
                ).to_dict(),
            )

        return current_user

    return _require_scopes


def require_roles(required_roles: list[str], require_all: bool = False):
    """
    FastAPI dependency factory to require specific roles.

    Args:
        required_roles: List of required roles
        require_all: Whether all roles are required (vs any)

    Returns:
        Dependency function
    """

    def _require_roles(current_user: UserClaims = Depends(get_current_user)) -> UserClaims:
        if require_all:
            if not current_user.has_all_roles(required_roles):
                raise HTTPException(
                    status_code=403,
                    detail=InsufficientRole(
                        required_roles=required_roles, user_roles=current_user.roles
                    ).to_dict(),
                )
        elif not current_user.has_any_role(required_roles):
            raise HTTPException(
                status_code=403,
                detail=InsufficientRole(
                    required_roles=required_roles, user_roles=current_user.roles
                ).to_dict(),
            )

        return current_user

    return _require_roles


def require_authenticated(func):  # simple decorator for tests
    def wrapper(*args, **kwargs):
        user = get_current_user_context()
        if user is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return func(*args, **kwargs)

    return wrapper


def require_admin():
    """
    FastAPI dependency to require admin privileges.

    Returns:
        Dependency function
    """

    def _require_admin(current_user: UserClaims = Depends(get_current_user)) -> UserClaims:
        if not current_user.is_admin():
            raise HTTPException(
                status_code=403,
                detail=InsufficientRole(
                    "Administrator privileges required",
                    required_roles=["admin"],
                    user_roles=current_user.roles,
                ).to_dict(),
            )

        return current_user

    return _require_admin


def require_tenant_access(tenant_id: str):
    """
    FastAPI dependency factory to require access to specific tenant.

    Args:
        tenant_id: Tenant ID to check access for

    Returns:
        Dependency function
    """

    def _require_tenant_access(current_user: UserClaims = Depends(get_current_user)) -> UserClaims:
        if not current_user.can_access_tenant(tenant_id):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "TENANT_ACCESS_DENIED",
                    "message": f"Access denied to tenant {tenant_id}",
                    "user_tenant": current_user.tenant_id,
                    "requested_tenant": tenant_id,
                },
            )

        return current_user

    return _require_tenant_access


def require_service_operation(required_operations: list[str]):
    """
    FastAPI dependency factory to require service operations.

    Args:
        required_operations: List of required operations

    Returns:
        Dependency function
    """

    def _require_service_operation(
        current_service: ServiceClaims = Depends(get_current_service),
    ) -> ServiceClaims:
        for operation in required_operations:
            if not current_service.can_perform_operation(operation):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "INSUFFICIENT_SERVICE_PERMISSIONS",
                        "message": f"Service operation {operation} not allowed",
                        "service_name": current_service.service_name,
                        "allowed_operations": current_service.allowed_operations,
                        "required_operations": required_operations,
                    },
                )

        return current_service

    return _require_service_operation


"""Convenience dependency factories exposed as callables.

These are designed to be used as `Depends(RequireX)` in route signatures.
"""


def RequireAuthenticated(current_user: UserClaims = Depends(get_current_user)) -> None:  # noqa: N802
    _ = current_user
    return None


def RequireReadAccess(current_user: UserClaims = Depends(require_scopes(["read"]))) -> None:  # noqa: N802
    _ = current_user
    return None


def RequireWriteAccess(current_user: UserClaims = Depends(require_scopes(["write"]))) -> None:  # noqa: N802
    _ = current_user
    return None


def RequireAdminAccess(  # noqa: N802
    current_user: UserClaims = Depends(require_scopes(["admin:read", "admin:write"], require_all=False))
) -> None:
    _ = current_user
    return None


def RequireUserRole(current_user: UserClaims = Depends(require_roles(["user"]))) -> None:  # noqa: N802
    _ = current_user
    return None


def RequireModeratorRole(  # noqa: N802
    current_user: UserClaims = Depends(require_roles(["moderator", "admin"], require_all=False))
) -> None:
    _ = current_user
    return None


def RequireAdminRole(  # noqa: N802
    current_user: UserClaims = Depends(require_roles(["admin", "super_admin"], require_all=False))
) -> None:
    _ = current_user
    return None


def RequireAdmin(current_user: UserClaims = Depends(get_current_user)) -> None:  # noqa: N802
    if not current_user.is_admin():
        raise HTTPException(
            status_code=403,
            detail=InsufficientRole(
                "Administrator privileges required",
                required_roles=["admin"],
                user_roles=current_user.roles,
            ).to_dict(),
        )
    return None


def get_current_tenant(request: Request) -> str:
    """
    FastAPI dependency to get current user's tenant ID.

    Args:
        request: FastAPI request object

    Returns:
        Tenant ID string

    Raises:
        HTTPException: If user is not authenticated or no tenant ID
    """
    user = get_current_user(request)
    if not user.tenant_id:
        raise HTTPException(
            status_code=get_http_status(InsufficientScope()),
            detail="User does not have tenant access",
        )
    return user.tenant_id
