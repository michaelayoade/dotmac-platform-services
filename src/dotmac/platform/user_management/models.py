"""
User management database models.

Production-ready user models using SQLAlchemy 2.0.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from dotmac.platform.db import Base, TenantMixin, TimestampMixin


class User(Base, TimestampMixin, TenantMixin):
    """User model for authentication and authorization."""

    __tablename__ = "users"
    __table_args__ = (
        # Per-tenant uniqueness for username and email
        UniqueConstraint("tenant_id", "username", name="uq_users_tenant_username"),
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )

    # Core fields - removed unique=True, now using composite constraints above
    username: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)

    # Profile fields
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Extended profile fields
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)  # alias for phone_number
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Status fields
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_platform_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Security fields
    roles: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    permissions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # MFA fields
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Tracking fields
    last_login: Mapped[datetime | None] = mapped_column(nullable=True)
    last_login_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(nullable=True)

    # Additional metadata
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"

    def to_dict(self) -> dict:
        """Convert user to dictionary for API responses."""
        return {
            "user_id": str(self.id),
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "roles": self.roles or [],
            "permissions": self.permissions or [],
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_superuser": self.is_superuser,
            "is_platform_admin": self.is_platform_admin,
            "mfa_enabled": self.mfa_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "tenant_id": self.tenant_id,
        }


class BackupCode(Base, TimestampMixin, TenantMixin):
    """
    MFA Backup codes for account recovery.

    Backup codes are one-time use codes that can be used instead of TOTP
    when the user loses access to their authenticator device.
    """

    __tablename__ = "backup_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )

    # User relationship
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Hashed backup code (never store plaintext)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Track usage
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(nullable=True)
    used_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)

    def __repr__(self) -> str:
        return f"<BackupCode(id={self.id}, user_id={self.user_id}, used={self.used})>"


class EmailVerificationToken(Base, TimestampMixin, TenantMixin):
    """
    Email verification tokens for confirming email addresses.

    Tokens are single-use and expire after a set time period.
    """

    __tablename__ = "email_verification_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )

    # User relationship
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Token (hashed for security)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)

    # Email being verified
    email: Mapped[str] = mapped_column(String(255), nullable=False)

    # Token expiry
    expires_at: Mapped[datetime] = mapped_column(nullable=False)

    # Usage tracking
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(nullable=True)
    used_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)

    def is_expired(self) -> bool:
        """Check if token has expired."""
        from datetime import datetime

        return datetime.now(UTC) > self.expires_at

    def __repr__(self) -> str:
        return f"<EmailVerificationToken(id={self.id}, user_id={self.user_id}, email={self.email}, used={self.used})>"


class ProfileChangeHistory(Base, TimestampMixin, TenantMixin):
    """
    Track changes to user profile fields for audit purposes.

    Maintains a history of all profile updates including who made the change,
    what changed, and when.
    """

    __tablename__ = "profile_change_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )

    # User whose profile was changed
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Who made the change (could be admin)
    changed_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # What changed
    field_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Change context
    change_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ProfileChangeHistory(id={self.id}, user_id={self.user_id}, field={self.field_name})>"
        )
