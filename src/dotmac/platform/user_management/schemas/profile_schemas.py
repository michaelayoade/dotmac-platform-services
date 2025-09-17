"""
User profile schemas for user management v2 system.
Provides Pydantic 2 validation for user profiles and extended information.
"""

from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import Field, field_validator

from dotmac.platform.core.enhanced.base_schemas import (
    BaseCreateSchema,
    BaseResponseSchema,
    BaseUpdateSchema,
)


class ContactType(str, Enum):
    """Contact information types."""

    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    EMERGENCY = "emergency"


class AddressType(str, Enum):
    """Address types."""

    BILLING = "billing"
    SHIPPING = "shipping"
    SERVICE = "service"
    MAILING = "mailing"


class UserProfileCreateSchema(BaseCreateSchema):
    """Schema for creating user profiles."""

    user_id: UUID
    avatar_url: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = Field(None, max_length=1000)
    website: Optional[str] = Field(None, max_length=255)
    company: Optional[str] = Field(None, max_length=200)
    job_title: Optional[str] = Field(None, max_length=150)
    department: Optional[str] = Field(None, max_length=100)
    profile_metadata: Optional[dict[str, Any]] = None

    @field_validator("website")
    @classmethod
    def validate_website_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate website URL format."""
        if v and not (v.startswith("http://") or v.startswith("https://")):
            v = f"https://{v}"
        return v


class UserProfileUpdateSchema(BaseUpdateSchema):
    """Schema for updating user profiles."""

    avatar_url: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = Field(None, max_length=1000)
    website: Optional[str] = Field(None, max_length=255)
    company: Optional[str] = Field(None, max_length=200)
    job_title: Optional[str] = Field(None, max_length=150)
    department: Optional[str] = Field(None, max_length=100)
    profile_metadata: Optional[dict[str, Any]] = None


class UserProfileResponseSchema(BaseResponseSchema):
    """Schema for user profile responses."""

    user_id: UUID
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    website: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    profile_metadata: Optional[dict[str, Any]] = None


class UserContactCreateSchema(BaseCreateSchema):
    """Schema for creating user contact information."""

    user_id: UUID
    contact_type: ContactType
    contact_value: str = Field(..., max_length=255)
    label: Optional[str] = Field(None, max_length=100)
    is_primary: bool = Field(default=False)
    is_verified: bool = Field(default=False)
    contact_metadata: Optional[dict[str, Any]] = None


class UserContactUpdateSchema(BaseUpdateSchema):
    """Schema for updating user contact information."""

    contact_value: Optional[str] = Field(None, max_length=255)
    label: Optional[str] = Field(None, max_length=100)
    is_primary: Optional[bool] = None
    is_verified: Optional[bool] = None
    contact_metadata: Optional[dict[str, Any]] = None


class UserContactResponseSchema(BaseResponseSchema):
    """Schema for user contact information responses."""

    user_id: UUID
    contact_type: str
    contact_value: str
    label: Optional[str] = None
    is_primary: bool
    is_verified: bool
    contact_metadata: Optional[dict[str, Any]] = None


class UserPreferencesCreateSchema(BaseCreateSchema):
    """Schema for creating user preferences."""

    user_id: UUID
    language: str = Field(default="en", max_length=10)
    timezone: str = Field(default="UTC", max_length=50)
    theme: str = Field(default="light", max_length=20)
    email_notifications: bool = Field(default=True)
    sms_notifications: bool = Field(default=False)
    push_notifications: bool = Field(default=True)
    marketing_emails: bool = Field(default=False)
    preferences_metadata: Optional[dict[str, Any]] = None


class UserPreferencesUpdateSchema(BaseUpdateSchema):
    """Schema for updating user preferences."""

    language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)
    theme: Optional[str] = Field(None, max_length=20)
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    marketing_emails: Optional[bool] = None
    preferences_metadata: Optional[dict[str, Any]] = None


class UserPreferencesResponseSchema(BaseResponseSchema):
    """Schema for user preferences responses."""

    user_id: UUID
    language: str
    timezone: str
    theme: str
    email_notifications: bool
    sms_notifications: bool
    push_notifications: bool
    marketing_emails: bool
    preferences_metadata: Optional[dict[str, Any]] = None
