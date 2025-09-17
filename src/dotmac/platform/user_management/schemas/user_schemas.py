"""
Production-ready user schemas using Pydantic 2 and DRY patterns.
Leverages existing base schemas for consistency.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from dotmac.platform.core.enhanced.base_schemas import (
    BaseCreateSchema,
    BaseResponseSchema,
    BaseUpdateSchema,
    EmailMixin,
    PhoneMixin,
    SearchSchema,
    StatusMixin,
    TenantMixin,
)


class UserType(str, Enum):
    """Unified user types across all platforms."""

    # ISP Framework user types
    CUSTOMER = "customer"
    TECHNICIAN = "technician"
    ISP_ADMIN = "isp_admin"
    ISP_SUPPORT = "isp_support"

    # Management Platform user types
    SUPER_ADMIN = "super_admin"
    PLATFORM_ADMIN = "platform_admin"
    TENANT_ADMIN = "tenant_admin"
    TENANT_USER = "tenant_user"
    PLATFORM_SUPPORT = "platform_support"

    # Common user types
    API_USER = "api_user"
    READONLY = "readonly"
    RESELLER = "reseller"
    PARTNER = "partner"


class UserStatus(str, Enum):
    """User account status."""

    PENDING = "pending"  # Registered but not verified
    ACTIVE = "active"  # Active and verified
    INACTIVE = "inactive"  # Temporarily disabled
    SUSPENDED = "suspended"  # Administratively suspended
    LOCKED = "locked"  # Account locked due to failed attempts
    EXPIRED = "expired"  # Account expired
    DELETED = "deleted"  # Marked for deletion
    ARCHIVED = "archived"  # Historical record


class MFAMethod(str, Enum):
    """Multi-factor authentication methods."""

    TOTP = "totp"  # Time-based OTP (Google Authenticator)
    SMS = "sms"  # SMS verification
    EMAIL = "email"  # Email verification
    BACKUP_CODES = "backup_codes"  # Backup recovery codes


class UserCreateSchema(BaseCreateSchema, EmailMixin, PhoneMixin, TenantMixin):
    """Schema for creating new users - leverages DRY mixins."""

    # Required fields
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_.-]+$",
        description="Unique username",
    )
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    user_type: UserType = Field(description="Type of user account")
    password: str = Field(
        ..., min_length=8, max_length=128, description="Password (will be hashed)"
    )

    # Optional fields
    middle_name: Optional[str] = Field(None, max_length=100)
    preferred_name: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=200)
    department: Optional[str] = Field(None, max_length=200)
    company: Optional[str] = Field(None, max_length=200)

    # Settings
    timezone: str = Field("UTC", description="User timezone")
    language: str = Field("en", description="Preferred language")

    # Initial role assignments
    roles: list[str] = Field(default_factory=list, description="Initial roles")
    permissions: list[str] = Field(default_factory=list, description="Initial permissions")

    # Platform-specific data
    platform_metadata: dict[str, Any] = Field(default_factory=dict)

    # Terms and privacy
    terms_accepted: bool = Field(False, description="Terms of service accepted")
    privacy_accepted: bool = Field(False, description="Privacy policy accepted")
    marketing_consent: bool = Field(False, description="Marketing communications consent")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if not v.replace("_", "").replace("-", "").replace(".", "").isalnum():
            raise ValueError(
                "Username can only contain letters, numbers, hyphens, underscores, and periods"
            )
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets security requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")

        # Check complexity requirements
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)

        if not all([has_upper, has_lower, has_digit, has_special]):
            raise ValueError(
                "Password must contain at least one uppercase letter, "
                "lowercase letter, digit, and special character"
            )

        # Check for common weak patterns
        weak_patterns = ["password", "123456", "qwerty", v.lower()]
        for pattern in weak_patterns:
            if pattern in v.lower():
                raise ValueError(f"Password cannot contain common pattern: {pattern}")

        return v

    @model_validator(mode="after")
    def validate_required_acceptances(self):
        """Validate required legal acceptances."""
        if not self.terms_accepted:
            raise ValueError("Terms of service must be accepted")
        if not self.privacy_accepted:
            raise ValueError("Privacy policy must be accepted")
        return self


class UserUpdateSchema(BaseUpdateSchema, PhoneMixin):
    """Schema for updating existing users - all fields optional."""

    # Basic info updates
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    preferred_name: Optional[str] = Field(None, max_length=100)

    # Contact info
    email: Optional[str] = Field(None, description="New email (requires verification)")

    # Professional info
    job_title: Optional[str] = Field(None, max_length=200)
    department: Optional[str] = Field(None, max_length=200)
    company: Optional[str] = Field(None, max_length=200)

    # Settings
    timezone: Optional[str] = Field(None)
    language: Optional[str] = Field(None)

    # Status updates (admin only)
    is_active: Optional[bool] = None
    status: Optional[UserStatus] = None

    # Platform-specific updates
    platform_metadata: Optional[dict[str, Any]] = None

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format."""
        if v:
            return v.lower().strip()
        return v


class UserResponseSchema(BaseResponseSchema, EmailMixin, PhoneMixin, StatusMixin, TenantMixin):
    """Schema for user API responses - leverages DRY mixins."""

    # Core identification
    username: str = Field(description="Unique username")
    first_name: str = Field(description="First name")
    last_name: str = Field(description="Last name")
    middle_name: Optional[str] = Field(None, description="Middle name")
    preferred_name: Optional[str] = Field(None, description="Preferred display name")
    user_type: UserType = Field(description="User account type")
    status: UserStatus = Field(description="Current account status")

    # Professional information
    job_title: Optional[str] = Field(None, description="Job title")
    department: Optional[str] = Field(None, description="Department")
    company: Optional[str] = Field(None, description="Company name")

    # Verification status
    email_verified: bool = Field(False, description="Email verification status")
    phone_verified: bool = Field(False, description="Phone verification status")
    email_verified_at: Optional[datetime] = None
    phone_verified_at: Optional[datetime] = None

    # Security information
    mfa_enabled: bool = Field(False, description="MFA enabled status")
    mfa_methods: list[MFAMethod] = Field(default_factory=list, description="Enabled MFA methods")
    password_changed_at: Optional[datetime] = Field(None, description="Last password change")

    # Activity information
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    login_count: int = Field(0, description="Total login count")
    failed_login_count: int = Field(0, description="Failed login attempts")
    locked_until: Optional[datetime] = Field(None, description="Account locked until")

    # Profile information
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    timezone: str = Field("UTC", description="User timezone")
    language: str = Field("en", description="Preferred language")

    # Role and permission information
    roles: list[str] = Field(default_factory=list, description="Assigned roles")
    permissions: list[str] = Field(default_factory=list, description="Effective permissions")

    # Platform-specific data
    platform_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Platform-specific data"
    )

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return " ".join(parts)

    @property
    def display_name(self) -> str:
        """Get preferred display name."""
        return self.preferred_name or self.full_name

    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if not self.locked_until:
            return False
        return datetime.now(timezone.utc) < self.locked_until

    @property
    def can_login(self) -> bool:
        """Check if user can currently login."""
        return (
            self.is_active
            and self.status == UserStatus.ACTIVE
            and not self.is_locked
            and self.email_verified
        )


class UserSummarySchema(BaseResponseSchema):
    """Lightweight user schema for lists and summaries."""

    username: str
    first_name: str
    last_name: str
    email: str
    user_type: UserType
    status: UserStatus
    is_active: bool
    last_login: Optional[datetime] = None
    avatar_url: Optional[str] = None

    @property
    def display_name(self) -> str:
        """Get display name."""
        return f"{self.first_name} {self.last_name}"


class UserSearchSchema(SearchSchema):
    """Schema for user search operations."""

    # Search filters
    user_type: Optional[UserType] = Field(None, description="Filter by user type")
    status: Optional[UserStatus] = Field(None, description="Filter by status")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    email_verified: Optional[bool] = Field(None, description="Filter by email verification")
    tenant_id: Optional[UUID] = Field(None, description="Filter by tenant")

    # Date range filters
    created_after: Optional[datetime] = Field(None, description="Created after date")
    created_before: Optional[datetime] = Field(None, description="Created before date")
    last_login_after: Optional[datetime] = Field(None, description="Last login after date")
    last_login_before: Optional[datetime] = Field(None, description="Last login before date")

    # Role and permission filters
    has_role: Optional[str] = Field(None, description="Filter by role")
    has_permission: Optional[str] = Field(None, description="Filter by permission")

    # Advanced filters
    company: Optional[str] = Field(None, description="Filter by company")
    department: Optional[str] = Field(None, description="Filter by department")
    mfa_enabled: Optional[bool] = Field(None, description="Filter by MFA status")


class UserBulkOperationSchema(BaseCreateSchema):
    """Schema for bulk user operations."""

    user_ids: list[UUID] = Field(
        ..., min_items=1, max_items=100, description="User IDs to operate on"
    )
    operation: str = Field(..., description="Bulk operation to perform")
    parameters: Optional[dict[str, Any]] = Field(None, description="Operation parameters")

    @field_validator("operation")
    @classmethod
    def validate_operation(cls, v: str) -> str:
        """Validate bulk operation type."""
        allowed_operations = [
            "activate",
            "deactivate",
            "suspend",
            "delete",
            "assign_role",
            "remove_role",
            "update_status",
            "send_invitation",
            "reset_password",
        ]
        if v not in allowed_operations:
            raise ValueError(f"Invalid operation. Must be one of: {allowed_operations}")
        return v


class UserInvitationSchema(BaseCreateSchema, EmailMixin, TenantMixin):
    """Schema for user invitation operations."""

    # Invitation details
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    user_type: UserType = Field(description="Type of user account to create")

    # Role assignments
    roles: list[str] = Field(default_factory=list, description="Initial roles")
    permissions: list[str] = Field(default_factory=list, description="Initial permissions")

    # Invitation settings
    expires_in_days: int = Field(7, ge=1, le=30, description="Invitation expiry in days")
    send_email: bool = Field(True, description="Send invitation email")
    custom_message: Optional[str] = Field(
        None, max_length=500, description="Custom invitation message"
    )

    # Inviter information
    invited_by: Optional[UUID] = Field(None, description="User who sent the invitation")


class UserActivationSchema(BaseCreateSchema):
    """Schema for user account activation."""

    user_id: UUID = Field(description="User ID to activate")
    activation_token: str = Field(description="Activation token from invitation/registration")
    password: Optional[str] = Field(None, min_length=8, description="Password for new accounts")

    @field_validator("password")
    @classmethod
    def validate_password_if_provided(cls, v: Optional[str]) -> Optional[str]:
        """Validate password if provided."""
        if v:
            # Reuse validation from UserCreateSchema
            return UserCreateSchema.validate_password_strength(v)
        return v


__all__ = [
    "UserType",
    "UserStatus",
    "MFAMethod",
    "UserCreateSchema",
    "UserUpdateSchema",
    "UserResponseSchema",
    "UserSummarySchema",
    "UserSearchSchema",
    "UserBulkOperationSchema",
    "UserInvitationSchema",
    "UserActivationSchema",
]
