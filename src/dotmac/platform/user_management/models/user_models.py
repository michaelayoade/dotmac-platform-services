"""
Production-ready SQLAlchemy models for user management.
Leverages existing base model patterns for DRY approach.
"""

from datetime import datetime, timezone
from typing import Any, Optional

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
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from dotmac.platform.database.base import BaseModel

from ..schemas.user_schemas import UserStatus, UserType


class UserModel(BaseModel):
    """
    Core user model with comprehensive user management features.
    Inherits from BaseModel for DRY approach with timestamps, UUID, etc.
    """

    __tablename__ = "users_v2"

    # === Core Identity ===
    username = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique username for login",
    )
    email = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Primary email address",
    )

    # === Personal Information ===
    first_name = Column(String(100), nullable=False, comment="User's first name")
    last_name = Column(String(100), nullable=False, comment="User's last name")
    middle_name = Column(String(100), nullable=True, comment="User's middle name")
    preferred_name = Column(String(100), nullable=True, comment="Preferred display name")

    # === Classification ===
    user_type = Column(
        SQLEnum(UserType, name="user_type_enum"),
        nullable=False,
        index=True,
        comment="Type of user account",
    )
    status = Column(
        SQLEnum(UserStatus, name="user_status_enum"),
        nullable=False,
        default=UserStatus.PENDING,
        index=True,
        comment="Current account status",
    )

    # === Status Flags ===
    is_active = Column(
        Boolean, nullable=False, default=True, index=True, comment="Account active flag"
    )
    is_verified = Column(
        Boolean, nullable=False, default=False, comment="Email verification status"
    )
    is_superuser = Column(
        Boolean, nullable=False, default=False, comment="Superuser privileges flag"
    )

    # === Verification Status ===
    email_verified = Column(
        Boolean, nullable=False, default=False, comment="Email verification flag"
    )
    phone_verified = Column(
        Boolean, nullable=False, default=False, comment="Phone verification flag"
    )
    email_verified_at = Column(DateTime, nullable=True, comment="Email verification timestamp")
    phone_verified_at = Column(DateTime, nullable=True, comment="Phone verification timestamp")

    # === Professional Information ===
    job_title = Column(String(200), nullable=True, comment="Job title")
    department = Column(String(200), nullable=True, comment="Department")
    company = Column(String(200), nullable=True, comment="Company name")

    # === Contact Information ===
    phone = Column(String(20), nullable=True, comment="Primary phone number")
    mobile = Column(String(20), nullable=True, comment="Mobile phone number")

    # === Settings ===
    timezone = Column(String(50), nullable=False, default="UTC", comment="User timezone")
    language = Column(String(10), nullable=False, default="en", comment="Preferred language")

    # === Security Information ===
    password_changed_at = Column(DateTime, nullable=True, comment="Last password change timestamp")
    mfa_enabled = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Multi-factor authentication enabled",
    )
    mfa_methods = Column(JSON, nullable=True, default=list, comment="Enabled MFA methods")

    # === Activity Tracking ===
    last_login = Column(DateTime, nullable=True, comment="Last successful login")
    login_count = Column(Integer, nullable=False, default=0, comment="Total login count")
    failed_login_count = Column(Integer, nullable=False, default=0, comment="Failed login attempts")
    locked_until = Column(DateTime, nullable=True, comment="Account locked until timestamp")

    # === Profile Information ===
    avatar_url = Column(String(500), nullable=True, comment="Avatar image URL")

    # === Multi-tenant Support ===
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customer_tenants.id"),
        nullable=True,
        index=True,
        comment="Tenant association",
    )

    # === Platform-specific Data ===
    platform_metadata = Column(
        JSON, nullable=True, default=dict, comment="Platform-specific metadata"
    )

    # === Legal Compliance ===
    terms_accepted = Column(
        Boolean, nullable=False, default=False, comment="Terms of service accepted"
    )
    privacy_accepted = Column(
        Boolean, nullable=False, default=False, comment="Privacy policy accepted"
    )
    marketing_consent = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Marketing communications consent",
    )
    terms_accepted_at = Column(DateTime, nullable=True, comment="Terms acceptance timestamp")
    privacy_accepted_at = Column(DateTime, nullable=True, comment="Privacy acceptance timestamp")

    # === Relationships ===
    tenant = relationship("Tenant", back_populates="users")

    profile = relationship(
        "UserProfileModel",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    passwords = relationship(
        "UserPasswordModel", back_populates="user", cascade="all, delete-orphan"
    )

    sessions = relationship("UserSessionModel", back_populates="user", cascade="all, delete-orphan")

    mfa_settings = relationship("UserMFAModel", back_populates="user", cascade="all, delete-orphan")

    api_keys = relationship("UserApiKeyModel", back_populates="user", cascade="all, delete-orphan")

    roles = relationship("UserRoleModel", back_populates="user", cascade="all, delete-orphan")

    audit_events = relationship(
        "AuthAuditModel", back_populates="user", cascade="all, delete-orphan"
    )

    # === Indexes for Performance ===
    __table_args__ = (
        Index("idx_users_v2_email_status", "email", "status"),
        Index("idx_users_v2_username_status", "username", "status"),
        Index("idx_users_v2_type_tenant", "user_type", "tenant_id"),
        Index("idx_users_v2_status_active", "status", "is_active"),
        Index("idx_users_v2_created_tenant", "created_at", "tenant_id"),
        Index("idx_users_v2_last_login", "last_login"),
        UniqueConstraint("email", name="uq_users_v2_email"),
        UniqueConstraint("username", name="uq_users_v2_username"),
        {"comment": "Core user management table with comprehensive features"},
    )

    # === Computed Properties ===

    @hybrid_property
    def full_name(self) -> str:
        """Get user's full name."""
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return " ".join(parts)

    @hybrid_property
    def display_name(self) -> str:
        """Get preferred display name."""
        return self.preferred_name or self.full_name

    @hybrid_property
    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if not self.locked_until:
            return False
        return datetime.now(timezone.utc) < self.locked_until

    @hybrid_property
    def can_login(self) -> bool:
        """Check if user can currently login."""
        return (
            self.is_active
            and self.status == UserStatus.ACTIVE
            and not self.is_locked
            and self.email_verified
        )

    @hybrid_property
    def needs_password_change(self) -> bool:
        """Check if password change is required."""
        if not self.password_changed_at:
            return True

        # Check if password is older than 90 days
        days_since_change = (datetime.now(timezone.utc) - self.password_changed_at).days
        return days_since_change > 90

    # === Instance Methods ===

    def lock_account(self, duration_minutes: int = 30) -> None:
        """Lock user account for specified duration."""
        from datetime import timedelta

        self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
        self.failed_login_count += 1

    def unlock_account(self) -> None:
        """Unlock user account."""
        self.locked_until = None
        self.failed_login_count = 0

    def record_login(self) -> None:
        """Record successful login."""
        self.last_login = datetime.now(timezone.utc)
        self.login_count += 1
        self.failed_login_count = 0
        self.locked_until = None

    def record_failed_login(self) -> None:
        """Record failed login attempt."""
        self.failed_login_count += 1

        # Auto-lock after 5 failed attempts
        if self.failed_login_count >= 5:
            self.lock_account()

    def activate_account(self) -> None:
        """Activate user account."""
        self.status = UserStatus.ACTIVE
        self.is_active = True
        self.email_verified = True
        self.email_verified_at = datetime.now(timezone.utc)

    def deactivate_account(self, reason: Optional[str] = None) -> None:
        """Deactivate user account."""
        self.status = UserStatus.INACTIVE
        self.is_active = False

        # Store deactivation reason in metadata
        if reason:
            if not self.platform_metadata:
                self.platform_metadata = {}
            self.platform_metadata["deactivation_reason"] = reason
            self.platform_metadata["deactivated_at"] = datetime.now(timezone.utc).isoformat()

    def get_effective_permissions(self) -> list[str]:
        """Get all effective permissions for this user."""
        permissions = set()

        # Add permissions from roles
        for user_role in self.roles:
            if user_role.role and user_role.is_active:
                for role_perm in user_role.role.permissions:
                    if role_perm.permission:
                        permissions.add(role_perm.permission.name)

        return list(permissions)

    def has_permission(self, permission_name: str) -> bool:
        """Check if user has specific permission."""
        return permission_name in self.get_effective_permissions()

    def has_role(self, role_name: str) -> bool:
        """Check if user has specific role."""
        for user_role in self.roles:
            if user_role.role and user_role.role.name == role_name and user_role.is_active:
                return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "middle_name": self.middle_name,
            "preferred_name": self.preferred_name,
            "full_name": self.full_name,
            "display_name": self.display_name,
            "user_type": self.user_type.value,
            "status": self.status.value,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "email_verified": self.email_verified,
            "phone_verified": self.phone_verified,
            "email_verified_at": self.email_verified_at,
            "phone_verified_at": self.phone_verified_at,
            "job_title": self.job_title,
            "department": self.department,
            "company": self.company,
            "phone": self.phone,
            "mobile": self.mobile,
            "timezone": self.timezone,
            "language": self.language,
            "mfa_enabled": self.mfa_enabled,
            "mfa_methods": self.mfa_methods or [],
            "last_login": self.last_login,
            "login_count": self.login_count,
            "avatar_url": self.avatar_url,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "can_login": self.can_login,
            "is_locked": self.is_locked,
            "needs_password_change": self.needs_password_change,
        }

    def __repr__(self) -> str:
        return f"<UserModel(id={self.id}, username='{self.username}', email='{self.email}')>"


class UserProfileModel(BaseModel):
    """
    Extended user profile information.
    Separate from core user model to optimize queries.
    """

    __tablename__ = "user_profiles_v2"

    # === Foreign Key ===
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users_v2.id"),
        nullable=False,
        unique=True,
        comment="Reference to user",
    )

    # === Personal Details ===
    title = Column(String(20), nullable=True, comment="Title (Mr., Ms., Dr., etc.)")
    date_of_birth = Column(DateTime, nullable=True, comment="Date of birth")
    gender = Column(String(20), nullable=True, comment="Gender")

    # === Additional Contact ===
    website = Column(String(500), nullable=True, comment="Personal or professional website")
    linkedin_url = Column(String(500), nullable=True, comment="LinkedIn profile URL")

    # === Bio Information ===
    bio = Column(Text, nullable=True, comment="User biography or description")
    skills = Column(JSON, nullable=True, default=list, comment="User skills list")
    interests = Column(JSON, nullable=True, default=list, comment="User interests list")

    # === Emergency Contact ===
    emergency_contact_name = Column(String(200), nullable=True, comment="Emergency contact name")
    emergency_contact_phone = Column(String(20), nullable=True, comment="Emergency contact phone")
    emergency_contact_relationship = Column(
        String(100), nullable=True, comment="Emergency contact relationship"
    )

    # === Custom Fields ===
    custom_fields = Column(JSON, nullable=True, default=dict, comment="Custom profile fields")

    # === Relationships ===
    user = relationship("UserModel", back_populates="profile")

    contact_info = relationship(
        "UserContactInfoModel",
        back_populates="profile",
        uselist=False,
        cascade="all, delete-orphan",
    )

    preferences = relationship(
        "UserPreferencesModel",
        back_populates="profile",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # === Indexes ===
    __table_args__ = (
        Index("idx_user_profiles_v2_user_id", "user_id"),
        {"comment": "Extended user profile information"},
    )

    def __repr__(self) -> str:
        return f"<UserProfileModel(user_id={self.user_id})>"


class UserContactInfoModel(BaseModel):
    """
    User contact information including addresses.
    Separate model for complex contact data.
    """

    __tablename__ = "user_contact_info_v2"

    # === Foreign Key ===
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles_v2.id"),
        nullable=False,
        unique=True,
        comment="Reference to user profile",
    )

    # === Primary Address ===
    address_line1 = Column(String(200), nullable=True, comment="Address line 1")
    address_line2 = Column(String(200), nullable=True, comment="Address line 2")
    city = Column(String(100), nullable=True, comment="City")
    state = Column(String(100), nullable=True, comment="State or province")
    postal_code = Column(String(20), nullable=True, comment="Postal/ZIP code")
    country = Column(String(100), nullable=True, comment="Country")

    # === Secondary Address ===
    billing_address_line1 = Column(String(200), nullable=True, comment="Billing address line 1")
    billing_address_line2 = Column(String(200), nullable=True, comment="Billing address line 2")
    billing_city = Column(String(100), nullable=True, comment="Billing city")
    billing_state = Column(String(100), nullable=True, comment="Billing state or province")
    billing_postal_code = Column(String(20), nullable=True, comment="Billing postal/ZIP code")
    billing_country = Column(String(100), nullable=True, comment="Billing country")

    # === Geographic Information ===
    latitude = Column(String(50), nullable=True, comment="Geographic latitude")
    longitude = Column(String(50), nullable=True, comment="Geographic longitude")

    # === Relationships ===
    profile = relationship("UserProfileModel", back_populates="contact_info")

    # === Indexes ===
    __table_args__ = (
        Index("idx_user_contact_info_v2_profile_id", "profile_id"),
        {"comment": "User contact and address information"},
    )

    def get_primary_address(self) -> Optional[dict[str, str]]:
        """Get primary address as dictionary."""
        if not self.address_line1:
            return None

        return {
            "line1": self.address_line1,
            "line2": self.address_line2,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
        }

    def get_billing_address(self) -> Optional[dict[str, str]]:
        """Get billing address as dictionary."""
        if not self.billing_address_line1:
            return None

        return {
            "line1": self.billing_address_line1,
            "line2": self.billing_address_line2,
            "city": self.billing_city,
            "state": self.billing_state,
            "postal_code": self.billing_postal_code,
            "country": self.billing_country,
        }

    def __repr__(self) -> str:
        return f"<UserContactInfoModel(profile_id={self.profile_id})>"


class UserPreferencesModel(BaseModel):
    """
    User preferences and settings.
    Separate model for preference management.
    """

    __tablename__ = "user_preferences_v2"

    # === Foreign Key ===
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles_v2.id"),
        nullable=False,
        unique=True,
        comment="Reference to user profile",
    )

    # === UI Preferences ===
    theme = Column(String(20), nullable=False, default="light", comment="UI theme preference")
    date_format = Column(
        String(20),
        nullable=False,
        default="YYYY-MM-DD",
        comment="Preferred date format",
    )
    time_format = Column(String(10), nullable=False, default="24h", comment="Preferred time format")
    number_format = Column(
        String(20),
        nullable=False,
        default="1,234.56",
        comment="Preferred number format",
    )

    # === Notification Preferences ===
    email_notifications = Column(
        Boolean, nullable=False, default=True, comment="Email notifications enabled"
    )
    sms_notifications = Column(
        Boolean, nullable=False, default=False, comment="SMS notifications enabled"
    )
    push_notifications = Column(
        Boolean, nullable=False, default=True, comment="Push notifications enabled"
    )
    in_app_notifications = Column(
        Boolean, nullable=False, default=True, comment="In-app notifications enabled"
    )

    # === Notification Types ===
    security_alerts = Column(
        Boolean, nullable=False, default=True, comment="Security alert notifications"
    )
    account_updates = Column(
        Boolean, nullable=False, default=True, comment="Account update notifications"
    )
    system_maintenance = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="System maintenance notifications",
    )
    marketing_emails = Column(
        Boolean, nullable=False, default=False, comment="Marketing email notifications"
    )

    # === Privacy Settings ===
    profile_visibility = Column(
        String(20),
        nullable=False,
        default="private",
        comment="Profile visibility setting",
    )
    activity_visibility = Column(
        String(20),
        nullable=False,
        default="private",
        comment="Activity visibility setting",
    )

    # === Custom Preferences ===
    dashboard_layout = Column(
        JSON, nullable=True, default=dict, comment="Dashboard layout preferences"
    )
    custom_preferences = Column(
        JSON, nullable=True, default=dict, comment="Custom user preferences"
    )

    # === Relationships ===
    profile = relationship("UserProfileModel", back_populates="preferences")

    # === Indexes ===
    __table_args__ = (
        Index("idx_user_preferences_v2_profile_id", "profile_id"),
        {"comment": "User preferences and settings"},
    )

    def get_notification_settings(self) -> dict[str, bool]:
        """Get all notification settings."""
        return {
            "email": self.email_notifications,
            "sms": self.sms_notifications,
            "push": self.push_notifications,
            "in_app": self.in_app_notifications,
            "security_alerts": self.security_alerts,
            "account_updates": self.account_updates,
            "system_maintenance": self.system_maintenance,
            "marketing": self.marketing_emails,
        }

    def update_notification_settings(self, settings: dict[str, bool]) -> None:
        """Update notification settings from dictionary."""
        for key, value in settings.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self) -> str:
        return f"<UserPreferencesModel(profile_id={self.profile_id})>"


__all__ = [
    "UserModel",
    "UserProfileModel",
    "UserContactInfoModel",
    "UserPreferencesModel",
]
