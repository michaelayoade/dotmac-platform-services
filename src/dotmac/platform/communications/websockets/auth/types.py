"""
Authentication types and data classes.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class UserInfo:
    """User information from authentication."""

    user_id: str
    username: Optional[str] = None
    email: Optional[str] = None
    tenant_id: Optional[str] = None

    # Permissions and roles
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)

    # Additional user data
    extra_data: dict[str, Any] = field(default_factory=dict)

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles

    def has_any_role(self, roles: list[str]) -> bool:
        """Check if user has any of the specified roles."""
        return any(role in self.roles for role in roles)


@dataclass
class AuthResult:
    """Result of authentication attempt."""

    success: bool
    user_info: Optional[UserInfo] = None
    error: Optional[str] = None

    # Token information
    token_type: Optional[str] = None
    expires_at: Optional[float] = None

    # Additional context
    auth_method: Optional[str] = None  # "jwt", "api_key", "session", etc.
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_authenticated(self) -> bool:
        """Check if authentication was successful (backward compatibility)."""
        return self.success

    @classmethod
    def success_result(
        cls,
        user_info: UserInfo,
        token_type: str = "jwt",  # nosec B107 - token type identifier, not password
        expires_at: Optional[float] = None,
        auth_method: str = "jwt",  # nosec B107 - auth method identifier, not password
    ) -> "AuthResult":
        """Create successful authentication result."""
        return cls(
            success=True,
            user_info=user_info,
            token_type=token_type,
            expires_at=expires_at,
            auth_method=auth_method,
        )

    @classmethod
    def failure_result(cls, error: str, auth_method: str = "jwt") -> "AuthResult":
        """Create failed authentication result."""
        return cls(success=False, error=error, auth_method=auth_method)
