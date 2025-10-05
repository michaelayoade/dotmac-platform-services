"""
Pydantic schemas for tenant management API.

Request and response models following Pydantic v2 patterns.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .models import BillingCycle, TenantInvitationStatus, TenantPlanType, TenantStatus


# Base schemas
class TenantBase(BaseModel):
    """Base tenant schema with common fields."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, from_attributes=True
    )

    name: str = Field(min_length=1, max_length=255, description="Tenant organization name")
    slug: str = Field(
        min_length=1,
        max_length=255,
        pattern=r"^[a-z0-9-]+$",
        description="Unique URL-friendly identifier",
    )
    domain: str | None = Field(None, max_length=255, description="Custom domain")
    email: EmailStr | None = Field(None, description="Primary contact email")
    phone: str | None = Field(None, max_length=50, description="Contact phone number")


class TenantCreate(TenantBase):
    """Schema for creating a new tenant."""

    plan_type: TenantPlanType = Field(
        default=TenantPlanType.FREE, description="Initial subscription plan"
    )
    billing_cycle: BillingCycle = Field(
        default=BillingCycle.MONTHLY, description="Billing frequency"
    )
    billing_email: EmailStr | None = Field(None, description="Billing contact email")

    # Company info (optional)
    company_size: str | None = Field(None, max_length=50, description="Company size range")
    industry: str | None = Field(None, max_length=100, description="Industry sector")
    country: str | None = Field(None, max_length=100, description="Country")
    timezone: str = Field(default="UTC", description="Tenant timezone")

    # Initial limits
    max_users: int = Field(default=5, ge=1, description="Maximum users allowed")
    max_api_calls_per_month: int = Field(default=10000, ge=0, description="Monthly API call limit")
    max_storage_gb: int = Field(default=10, ge=1, description="Storage limit in GB")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Ensure slug is lowercase and valid."""
        if not v:
            raise ValueError("Slug cannot be empty")
        v = v.lower().strip()
        if not v.replace("-", "").isalnum():
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
        return v


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    name: str | None = Field(None, min_length=1, max_length=255)
    domain: str | None = Field(None, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    billing_email: EmailStr | None = None
    billing_cycle: BillingCycle | None = None

    # Status updates
    status: TenantStatus | None = None

    # Limits
    max_users: int | None = Field(None, ge=1)
    max_api_calls_per_month: int | None = Field(None, ge=0)
    max_storage_gb: int | None = Field(None, ge=1)

    # Company info
    company_size: str | None = Field(None, max_length=50)
    industry: str | None = Field(None, max_length=100)
    country: str | None = Field(None, max_length=100)
    timezone: str | None = Field(None, max_length=50)

    # Branding
    logo_url: str | None = Field(None, max_length=500)
    primary_color: str | None = Field(None, max_length=20)


class TenantResponse(TenantBase):
    """Schema for tenant response."""

    id: str
    status: TenantStatus
    plan_type: TenantPlanType
    billing_cycle: BillingCycle
    billing_email: str | None

    # Subscription dates
    trial_ends_at: datetime | None
    subscription_starts_at: datetime | None
    subscription_ends_at: datetime | None

    # Limits and usage
    max_users: int
    max_api_calls_per_month: int
    max_storage_gb: int
    current_users: int
    current_api_calls: int
    current_storage_gb: float

    # Additional info
    company_size: str | None
    industry: str | None
    country: str | None
    timezone: str
    logo_url: str | None
    primary_color: str | None

    # Metadata
    features: dict[str, Any]
    settings: dict[str, Any]
    custom_metadata: dict[str, Any]

    # Timestamps
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    # Computed properties
    is_trial: bool = False
    is_active: bool = False
    trial_expired: bool = False
    has_exceeded_user_limit: bool = False
    has_exceeded_api_limit: bool = False
    has_exceeded_storage_limit: bool = False


class TenantListResponse(BaseModel):
    """Schema for paginated tenant list."""

    model_config = ConfigDict(from_attributes=True)

    items: list[TenantResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Tenant Settings Schemas
class TenantSettingCreate(BaseModel):
    """Schema for creating a tenant setting."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    key: str = Field(min_length=1, max_length=255, description="Setting key")
    value: str = Field(description="Setting value")
    value_type: str = Field(default="string", description="Value type (string, int, bool, json)")
    description: str | None = Field(None, description="Setting description")
    is_encrypted: bool = Field(default=False, description="Whether to encrypt the value")


class TenantSettingUpdate(BaseModel):
    """Schema for updating a tenant setting."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    value: str | None = None
    value_type: str | None = None
    description: str | None = None
    is_encrypted: bool | None = None


class TenantSettingResponse(BaseModel):
    """Schema for tenant setting response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str
    key: str
    value: str
    value_type: str
    description: str | None
    is_encrypted: bool
    created_at: datetime
    updated_at: datetime


# Tenant Usage Schemas
class TenantUsageCreate(BaseModel):
    """Schema for creating a usage record."""

    model_config = ConfigDict(validate_assignment=True)

    period_start: datetime
    period_end: datetime
    api_calls: int = Field(default=0, ge=0)
    storage_gb: float = Field(default=0, ge=0)
    active_users: int = Field(default=0, ge=0)
    bandwidth_gb: float = Field(default=0, ge=0)
    metrics: dict[str, Any] = Field(default_factory=dict)


class TenantUsageResponse(BaseModel):
    """Schema for usage response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str
    period_start: datetime
    period_end: datetime
    api_calls: int
    storage_gb: float
    active_users: int
    bandwidth_gb: float
    metrics: dict[str, Any]
    created_at: datetime
    updated_at: datetime


# Tenant Invitation Schemas
class TenantInvitationCreate(BaseModel):
    """Schema for creating a tenant invitation."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    email: EmailStr = Field(description="Email address to invite")
    role: str = Field(default="member", description="Role to assign")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Ensure email is lowercase."""
        return v.lower().strip()


class TenantInvitationResponse(BaseModel):
    """Schema for invitation response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    email: str
    role: str
    invited_by: str
    token: str
    status: TenantInvitationStatus
    expires_at: datetime
    accepted_at: datetime | None
    created_at: datetime
    is_expired: bool = False
    is_pending: bool = False


class TenantInvitationAccept(BaseModel):
    """Schema for accepting an invitation."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    token: str = Field(min_length=1, description="Invitation token")


# Tenant Statistics Schemas
class TenantStatsResponse(BaseModel):
    """Schema for tenant statistics."""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: str
    total_users: int
    active_users: int
    total_api_calls: int
    total_storage_gb: float
    total_bandwidth_gb: float

    # Limits
    user_limit: int
    api_limit: int
    storage_limit: int

    # Usage percentages
    user_usage_percent: float
    api_usage_percent: float
    storage_usage_percent: float

    # Subscription info
    plan_type: TenantPlanType
    status: TenantStatus
    days_until_expiry: int | None


# Feature management
class TenantFeatureUpdate(BaseModel):
    """Schema for updating tenant features."""

    model_config = ConfigDict(validate_assignment=True)

    features: dict[str, bool] = Field(description="Feature flags to enable/disable")


class TenantMetadataUpdate(BaseModel):
    """Schema for updating tenant metadata."""

    model_config = ConfigDict(validate_assignment=True)

    custom_metadata: dict[str, Any] = Field(description="Custom metadata")


# Bulk operations
class TenantBulkStatusUpdate(BaseModel):
    """Schema for bulk status updates."""

    model_config = ConfigDict(validate_assignment=True)

    tenant_ids: list[str] = Field(min_length=1, description="List of tenant IDs")
    status: TenantStatus = Field(description="New status to set")


class TenantBulkDeleteRequest(BaseModel):
    """Schema for bulk tenant deletion."""

    model_config = ConfigDict(validate_assignment=True)

    tenant_ids: list[str] = Field(min_length=1, description="List of tenant IDs to delete")
    permanent: bool = Field(default=False, description="Permanently delete (vs soft delete)")
