"""
Pydantic schemas for Customer Management module.

Provides request/response validation models following project patterns.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from dotmac.platform.customer_management.models import (
    ActivityType,
    CommunicationChannel,
    CustomerStatus,
    CustomerTier,
    CustomerType,
)


class CustomerBase(BaseModel):
    """Base customer schema with common fields."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        from_attributes=True,
    )

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    middle_name: str | None = Field(None, max_length=100)
    display_name: str | None = Field(None, max_length=200)
    company_name: str | None = Field(None, max_length=200)

    email: EmailStr
    phone: str | None = Field(None, max_length=30)
    mobile: str | None = Field(None, max_length=30)

    customer_type: CustomerType = Field(default=CustomerType.INDIVIDUAL)
    tier: CustomerTier = Field(default=CustomerTier.FREE)

    # Address
    address_line1: str | None = Field(None, max_length=200)
    address_line2: str | None = Field(None, max_length=200)
    city: str | None = Field(None, max_length=100)
    state_province: str | None = Field(None, max_length=100)
    postal_code: str | None = Field(None, max_length=20)
    country: str | None = Field(None, pattern="^[A-Z]{2}$", description="ISO 3166-1 alpha-2")

    # Preferences
    preferred_channel: CommunicationChannel = Field(default=CommunicationChannel.EMAIL)
    preferred_language: str = Field(default="en", max_length=10)
    timezone: str = Field(default="UTC", max_length=50)
    opt_in_marketing: bool = Field(default=False)
    opt_in_updates: bool = Field(default=True)

    # Business fields
    tax_id: str | None = Field(None, max_length=50)
    vat_number: str | None = Field(None, max_length=50)
    industry: str | None = Field(None, max_length=100)

    @field_validator("phone", "mobile")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v and not v.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            raise ValueError("Phone number must contain only digits, +, -, and spaces")
        return v

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return v.lower()


class CustomerCreate(CustomerBase):
    """Schema for creating a new customer."""

    external_id: str | None = Field(None, max_length=100)
    source_system: str | None = Field(None, max_length=50)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    custom_fields: dict[str, Any] = Field(default_factory=dict)

    # Optional assignment
    assigned_to: UUID | None = None
    segment_id: UUID | None = None


class CustomerUpdate(BaseModel):
    """Schema for updating customer information."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    # All fields optional for partial updates
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    middle_name: str | None = Field(None, max_length=100)
    display_name: str | None = Field(None, max_length=200)
    company_name: str | None = Field(None, max_length=200)

    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=30)
    mobile: str | None = Field(None, max_length=30)

    status: CustomerStatus | None = None
    customer_type: CustomerType | None = None
    tier: CustomerTier | None = None

    # Address
    address_line1: str | None = Field(None, max_length=200)
    address_line2: str | None = Field(None, max_length=200)
    city: str | None = Field(None, max_length=100)
    state_province: str | None = Field(None, max_length=100)
    postal_code: str | None = Field(None, max_length=20)
    country: str | None = Field(None, pattern="^[A-Z]{2}$")

    # Preferences
    preferred_channel: CommunicationChannel | None = None
    preferred_language: str | None = Field(None, max_length=10)
    timezone: str | None = Field(None, max_length=50)
    opt_in_marketing: bool | None = None
    opt_in_updates: bool | None = None

    # Business fields
    tax_id: str | None = Field(None, max_length=50)
    vat_number: str | None = Field(None, max_length=50)
    industry: str | None = Field(None, max_length=100)
    employee_count: int | None = Field(None, ge=0)

    # Relationships
    assigned_to: UUID | None = None
    segment_id: UUID | None = None

    # Metadata
    metadata: dict[str, Any] | None = None
    custom_fields: dict[str, Any] | None = None
    tags: list[str] | None = None


class CustomerResponse(CustomerBase):
    """Schema for customer response."""

    id: UUID
    customer_number: str
    status: CustomerStatus

    # Verification status
    email_verified: bool
    phone_verified: bool

    # Metrics
    lifetime_value: Decimal
    total_purchases: int
    average_order_value: Decimal
    last_purchase_date: datetime | None = None
    first_purchase_date: datetime | None = None

    # Scoring
    risk_score: int
    satisfaction_score: int | None = None
    net_promoter_score: int | None = None

    # Dates
    acquisition_date: datetime
    last_contact_date: datetime | None = None
    created_at: datetime
    updated_at: datetime

    # Relationships
    user_id: UUID | None = None
    assigned_to: UUID | None = None
    segment_id: UUID | None = None

    # Metadata
    tags: list[str]
    metadata: dict[str, Any]
    custom_fields: dict[str, Any]


class CustomerListResponse(BaseModel):
    """Response for customer list endpoint."""

    customers: list[CustomerResponse]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    has_next: bool
    has_prev: bool


class CustomerSearchParams(BaseModel):
    """Parameters for searching customers."""

    query: str | None = Field(None, description="Search query")
    status: CustomerStatus | None = None
    customer_type: CustomerType | None = None
    tier: CustomerTier | None = None
    country: str | None = Field(None, pattern="^[A-Z]{2}$")
    assigned_to: UUID | None = None
    segment_id: UUID | None = None
    tags: list[str] | None = None

    # Date filters
    created_after: datetime | None = None
    created_before: datetime | None = None
    last_purchase_after: datetime | None = None
    last_purchase_before: datetime | None = None

    # Value filters
    min_lifetime_value: Decimal | None = Field(None, ge=0)
    max_lifetime_value: Decimal | None = Field(None, ge=0)

    # Pagination
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class CustomerActivityCreate(BaseModel):
    """Schema for creating customer activity."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    activity_type: ActivityType
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    ip_address: str | None = Field(None, max_length=45)
    user_agent: str | None = Field(None, max_length=500)


class CustomerActivityResponse(BaseModel):
    """Response schema for customer activity."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    activity_type: ActivityType
    title: str
    description: str | None = None
    metadata: dict[str, Any]
    performed_by: UUID | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime


class CustomerNoteCreate(BaseModel):
    """Schema for creating customer note."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    subject: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    is_internal: bool = Field(default=True)


class CustomerNoteResponse(BaseModel):
    """Response schema for customer note."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    subject: str
    content: str
    is_internal: bool
    created_by_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class CustomerSegmentCreate(BaseModel):
    """Schema for creating customer segment."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    criteria: dict[str, Any] = Field(default_factory=dict)
    is_dynamic: bool = Field(default=False)
    priority: int = Field(default=0, ge=0)


class CustomerSegmentResponse(BaseModel):
    """Response schema for customer segment."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    criteria: dict[str, Any]
    is_dynamic: bool
    priority: int
    member_count: int
    last_calculated: datetime | None = None
    created_at: datetime
    updated_at: datetime


class CustomerSegmentSummary(BaseModel):
    """Summary of a customer segment for metrics."""

    name: str
    count: int


class CustomerMetrics(BaseModel):
    """Customer metrics and analytics."""

    total_customers: int
    active_customers: int
    new_customers_this_month: int
    churn_rate: float
    average_lifetime_value: Decimal
    total_revenue: Decimal

    # By status
    customers_by_status: dict[str, int]

    # By tier
    customers_by_tier: dict[str, int]

    # By type
    customers_by_type: dict[str, int]

    # Top segments
    top_segments: list[CustomerSegmentSummary]
