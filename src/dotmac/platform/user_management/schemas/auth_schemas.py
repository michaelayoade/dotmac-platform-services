"""
Production-ready authentication schemas using Pydantic 2.
Leverages DRY patterns for consistent validation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from dotmac.platform.core.enhanced.base_schemas import BaseCreateSchema, BaseResponseSchema


class AuthProvider(str, Enum):
    """Supported authentication providers."""

    LOCAL = "local"  # Local username/password
    OAUTH_GOOGLE = "oauth_google"  # Google OAuth
    OAUTH_MICROSOFT = "oauth_microsoft"  # Microsoft OAuth
    SAML = "saml"  # SAML SSO
    LDAP = "ldap"  # LDAP/Active Directory
    API_KEY = "api_key"  # API key authentication


class SessionType(str, Enum):
    """Types of authentication sessions."""

    WEB = "web"  # Web browser session
    MOBILE = "mobile"  # Mobile app session
    API = "api"  # API access session
    CLI = "cli"  # Command line interface
    SYSTEM = "system"  # System/service account


class TokenType(str, Enum):
    """JWT token types."""

    ACCESS = "access"  # Short-lived access token
    REFRESH = "refresh"  # Long-lived refresh token
    ACTIVATION = "activation"  # Account activation token
    RESET = "reset"  # Password reset token
    INVITATION = "invitation"  # User invitation token
    MFA = "mfa"  # MFA verification token


class AuthAuditEventType(str, Enum):
    """Authentication audit event types."""

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_CHANGE_FAILED = "password_change_failed"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    MFA_FAILED = "mfa_failed"
    API_KEY_CREATED = "api_key_created"
    API_KEY_DELETED = "api_key_deleted"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    SESSION_EXPIRED = "session_expired"


class LoginRequestSchema(BaseCreateSchema):
    """Schema for user login requests."""

    # Authentication credentials
    username: str = Field(..., min_length=1, description="Username or email")
    password: str = Field(..., min_length=1, description="Password")

    # Session configuration
    session_type: SessionType = Field(SessionType.WEB, description="Type of session")
    remember_me: bool = Field(False, description="Extended session duration")

    # Client information
    client_ip: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    device_fingerprint: Optional[str] = Field(None, description="Device fingerprint")

    # Multi-factor authentication
    mfa_code: Optional[str] = Field(None, description="MFA verification code")
    mfa_method: Optional[str] = Field(None, description="MFA method used")

    # Platform context
    platform: Optional[str] = Field(None, description="Platform identifier")
    tenant_id: Optional[UUID] = Field(None, description="Tenant ID for multi-tenant login")

    @field_validator("username")
    @classmethod
    def normalize_username(cls, v: str) -> str:
        """Normalize username for consistent lookup."""
        return v.lower().strip()


class LoginAttemptResult(BaseResponseSchema):
    """Result of a login attempt with detailed status information."""

    success: bool = Field(..., description="Whether login was successful")
    access_token: Optional[str] = Field(None, description="JWT access token if successful")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token if successful")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: Optional[int] = Field(None, description="Token expiry in seconds")
    user: Optional[dict[str, Any]] = Field(None, description="User information if successful")
    requires_mfa: bool = Field(default=False, description="Whether MFA is required")
    mfa_token: Optional[str] = Field(None, description="MFA verification token")
    tenant_id: Optional[UUID] = Field(None, description="Tenant ID")
    permissions: list[str] = Field(default_factory=list, description="User permissions")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    locked_until: Optional[datetime] = Field(None, description="Account locked until timestamp")


class LoginResponseSchema(BaseResponseSchema):
    """Schema for successful login responses."""

    # Authentication tokens
    access_token: str = Field(description="JWT access token")
    refresh_token: str = Field(description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(description="Access token expiry in seconds")

    # Session information
    session_id: str = Field(description="Session identifier")
    session_expires_at: datetime = Field(description="Session expiry timestamp")

    # User information
    user: dict[str, Any] = Field(description="User profile information")

    # Security information
    requires_mfa: bool = Field(False, description="MFA required for complete authentication")
    mfa_methods: list[str] = Field(default_factory=list, description="Available MFA methods")

    # Warnings and notifications
    password_expires_in_days: Optional[int] = Field(None, description="Days until password expires")
    account_warnings: list[str] = Field(default_factory=list, description="Account warnings")


class TokenResponseSchema(BaseResponseSchema):
    """Schema for token-only responses."""

    access_token: str = Field(description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(description="Token expiry in seconds")
    scope: Optional[str] = Field(None, description="Token scope")


class RefreshTokenSchema(BaseCreateSchema):
    """Schema for token refresh requests."""

    refresh_token: str = Field(..., description="Valid refresh token")
    scope: Optional[str] = Field(None, description="Requested token scope")


class PasswordResetRequestSchema(BaseCreateSchema):
    """Schema for password reset requests."""

    email: str = Field(..., description="User email address")
    client_ip: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")


class PasswordResetConfirmSchema(BaseCreateSchema):
    """Schema for password reset confirmation."""

    reset_token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets security requirements."""
        # Reuse validation from user schemas
        from .user_schemas import UserCreateSchema

        return UserCreateSchema.validate_password_strength(v)

    @model_validator(mode="after")
    def passwords_match(self):
        """Validate password confirmation matches."""
        if self.new_password != self.confirm_password:
            raise ValueError("Password confirmation does not match")
        return self


class ChangePasswordSchema(BaseCreateSchema):
    """Schema for password change by authenticated users."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")

    # Force logout other sessions after password change
    logout_other_sessions: bool = Field(True, description="Logout other sessions")

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets security requirements."""
        from .user_schemas import UserCreateSchema

        return UserCreateSchema.validate_password_strength(v)

    @model_validator(mode="after")
    def validate_password_change(self):
        """Validate password change requirements."""
        if self.current_password == self.new_password:
            raise ValueError("New password must be different from current password")
        if self.new_password != self.confirm_password:
            raise ValueError("Password confirmation does not match")
        return self


class MFASetupSchema(BaseCreateSchema):
    """Schema for MFA setup initiation."""

    method: str = Field(..., description="MFA method to set up")
    phone_number: Optional[str] = Field(None, description="Phone number for SMS MFA")

    @field_validator("method")
    @classmethod
    def validate_mfa_method(cls, v: str) -> str:
        """Validate MFA method is supported."""
        supported_methods = ["totp", "sms", "email"]
        if v not in supported_methods:
            raise ValueError(f"Unsupported MFA method. Use one of: {supported_methods}")
        return v


class MFASetupResponseSchema(BaseResponseSchema):
    """Schema for MFA setup response."""

    method: str = Field(description="MFA method being set up")
    qr_code: Optional[str] = Field(None, description="QR code for TOTP setup")
    secret: Optional[str] = Field(None, description="TOTP secret key")
    backup_codes: Optional[list[str]] = Field(None, description="Backup recovery codes")
    setup_token: str = Field(description="Token to confirm MFA setup")


class MFAVerifySchema(BaseCreateSchema):
    """Schema for MFA verification."""

    code: str = Field(..., min_length=6, max_length=8, description="MFA verification code")
    method: str = Field(..., description="MFA method used")
    setup_token: Optional[str] = Field(None, description="Setup token for initial verification")
    remember_device: bool = Field(False, description="Remember this device for MFA")


class LogoutSchema(BaseCreateSchema):
    """Schema for logout requests."""

    all_sessions: bool = Field(False, description="Logout from all sessions")
    session_id: Optional[str] = Field(None, description="Specific session to logout")


class SessionInfoSchema(BaseResponseSchema):
    """Schema for session information."""

    session_id: str = Field(description="Session identifier")
    user_id: UUID = Field(description="User ID")
    session_type: SessionType = Field(description="Type of session")
    created_at: datetime = Field(description="Session creation time")
    last_activity: datetime = Field(description="Last activity time")
    expires_at: datetime = Field(description="Session expiry time")

    # Client information
    client_ip: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    device_fingerprint: Optional[str] = Field(None, description="Device fingerprint")

    # Session status
    is_active: bool = Field(True, description="Session active status")
    is_current: bool = Field(False, description="Is this the current session")


# Backwards-compatible alias for request naming used in services/tests
# Some modules import MFASetupRequestSchema; keep alias to avoid churn
MFASetupRequestSchema = MFASetupSchema


class AuthAuditSchema(BaseResponseSchema):
    """Schema for authentication audit events."""

    user_id: UUID = Field(description="User ID")
    event_type: str = Field(description="Authentication event type")
    success: bool = Field(description="Whether the event was successful")

    # Context information
    client_ip: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    session_id: Optional[str] = Field(None, description="Session ID")

    # Additional details
    failure_reason: Optional[str] = Field(None, description="Reason for failure")
    mfa_method: Optional[str] = Field(None, description="MFA method used")
    auth_provider: AuthProvider = Field(AuthProvider.LOCAL, description="Authentication provider")

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional event metadata")


class ApiKeySchema(BaseResponseSchema):
    """Schema for API key information."""

    key_id: str = Field(description="API key identifier")
    name: str = Field(description="API key name/description")
    prefix: str = Field(description="API key prefix for identification")

    # Permissions and scope
    permissions: list[str] = Field(default_factory=list, description="API key permissions")
    scope: Optional[str] = Field(None, description="API key scope")

    # Lifecycle information
    created_at: datetime = Field(description="Key creation time")
    expires_at: Optional[datetime] = Field(None, description="Key expiry time")
    last_used: Optional[datetime] = Field(None, description="Last usage time")
    usage_count: int = Field(0, description="Number of times used")

    # Status
    is_active: bool = Field(True, description="Key active status")


class ApiKeyCreateSchema(BaseCreateSchema):
    """Schema for creating API keys."""

    name: str = Field(..., min_length=1, max_length=100, description="API key name")
    description: Optional[str] = Field(None, max_length=500, description="API key description")

    # Permissions and scope
    permissions: list[str] = Field(default_factory=list, description="API key permissions")
    scope: Optional[str] = Field(None, description="API key scope")

    # Expiry configuration
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="Days until expiry")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate API key name."""
        if not v.replace(" ", "").replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                "Name can only contain letters, numbers, spaces, hyphens, and underscores"
            )
        return v.strip()


__all__ = [
    "AuthProvider",
    "SessionType",
    "TokenType",
    "AuthAuditEventType",
    "LoginRequestSchema",
    "LoginAttemptResult",
    "LoginResponseSchema",
    "TokenResponseSchema",
    "RefreshTokenSchema",
    "PasswordResetRequestSchema",
    "PasswordResetConfirmSchema",
    "ChangePasswordSchema",
    "MFASetupSchema",
    "MFASetupRequestSchema",
    "MFASetupResponseSchema",
    "MFAVerifySchema",
    "LogoutSchema",
    "SessionInfoSchema",
    "AuthAuditSchema",
    "ApiKeySchema",
    "ApiKeyCreateSchema",
]
