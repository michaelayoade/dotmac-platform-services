"""
Pydantic schemas for Customer Management module.

Provides request/response validation models following project patterns.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
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
    middle_name: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    company_name: Optional[str] = Field(None, max_length=200)

    email: EmailStr
    phone: Optional[str] = Field(None, max_length=30)
    mobile: Optional[str] = Field(None, max_length=30)

    customer_type: CustomerType = Field(default=CustomerType.INDIVIDUAL)
    tier: CustomerTier = Field(default=CustomerTier.FREE)

    # Address
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state_province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, pattern="^[A-Z]{2}$", description="ISO 3166-1 alpha-2")

    # Preferences
    preferred_channel: CommunicationChannel = Field(default=CommunicationChannel.EMAIL)
    preferred_language: str = Field(default="en", max_length=10)
    timezone: str = Field(default="UTC", max_length=50)
    opt_in_marketing: bool = Field(default=False)
    opt_in_updates: bool = Field(default=True)

    # Business fields
    tax_id: Optional[str] = Field(None, max_length=50)
    vat_number: Optional[str] = Field(None, max_length=50)
    industry: Optional[str] = Field(None, max_length=100)

    @field_validator("phone", "mobile")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            raise ValueError("Phone number must contain only digits, +, -, and spaces")
        return v

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return v.lower()


class CustomerCreate(CustomerBase):
    """Schema for creating a new customer."""

    external_id: Optional[str] = Field(None, max_length=100)
    source_system: Optional[str] = Field(None, max_length=50)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    custom_fields: dict[str, Any] = Field(default_factory=dict)

    # Optional assignment
    assigned_to: Optional[UUID] = None
    segment_id: Optional[UUID] = None


class CustomerUpdate(BaseModel):
    """Schema for updating customer information."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    # All fields optional for partial updates
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    company_name: Optional[str] = Field(None, max_length=200)

    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=30)
    mobile: Optional[str] = Field(None, max_length=30)

    status: Optional[CustomerStatus] = None
    customer_type: Optional[CustomerType] = None
    tier: Optional[CustomerTier] = None

    # Address
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state_province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, pattern="^[A-Z]{2}$")

    # Preferences
    preferred_channel: Optional[CommunicationChannel] = None
    preferred_language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)
    opt_in_marketing: Optional[bool] = None
    opt_in_updates: Optional[bool] = None

    # Business fields
    tax_id: Optional[str] = Field(None, max_length=50)
    vat_number: Optional[str] = Field(None, max_length=50)
    industry: Optional[str] = Field(None, max_length=100)
    employee_count: Optional[int] = Field(None, ge=0)

    # Relationships
    assigned_to: Optional[UUID] = None
    segment_id: Optional[UUID] = None

    # Metadata
    metadata: Optional[dict[str, Any]] = None
    custom_fields: Optional[dict[str, Any]] = None
    tags: Optional[list[str]] = None


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
    last_purchase_date: Optional[datetime] = None
    first_purchase_date: Optional[datetime] = None

    # Scoring
    risk_score: int
    satisfaction_score: Optional[int] = None
    net_promoter_score: Optional[int] = None

    # Dates
    acquisition_date: datetime
    last_contact_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Relationships
    user_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    segment_id: Optional[UUID] = None

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

    query: Optional[str] = Field(None, description="Search query")
    status: Optional[CustomerStatus] = None
    customer_type: Optional[CustomerType] = None
    tier: Optional[CustomerTier] = None
    country: Optional[str] = Field(None, pattern="^[A-Z]{2}$")
    assigned_to: Optional[UUID] = None
    segment_id: Optional[UUID] = None
    tags: Optional[list[str]] = None

    # Date filters
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    last_purchase_after: Optional[datetime] = None
    last_purchase_before: Optional[datetime] = None

    # Value filters
    min_lifetime_value: Optional[Decimal] = Field(None, ge=0)
    max_lifetime_value: Optional[Decimal] = Field(None, ge=0)

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
    description: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, max_length=500)


class CustomerActivityResponse(BaseModel):
    """Response schema for customer activity."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    activity_type: ActivityType
    title: str
    description: Optional[str] = None
    metadata: dict[str, Any]
    performed_by: Optional[UUID] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
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
    created_by_id: Optional[UUID] = None
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
    description: Optional[str] = None
    criteria: dict[str, Any] = Field(default_factory=dict)
    is_dynamic: bool = Field(default=False)
    priority: int = Field(default=0, ge=0)


class CustomerSegmentResponse(BaseModel):
    """Response schema for customer segment."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: Optional[str] = None
    criteria: dict[str, Any]
    is_dynamic: bool
    priority: int
    member_count: int
    last_calculated: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


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
    top_segments: list[dict[str, Any]]