"""
Pydantic schemas for Partner Management module.

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

from dotmac.platform.partner_management.models import (
    CommissionModel,
    CommissionStatus,
    PartnerStatus,
    PartnerTier,
    PayoutStatus,
    ReferralStatus,
)


# ============================================================================
# Partner Schemas
# ============================================================================


class PartnerBase(BaseModel):
    """Base partner schema with common fields."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        from_attributes=True,
    )

    company_name: str = Field(min_length=1, max_length=255)
    legal_name: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None

    tier: PartnerTier = Field(default=PartnerTier.BRONZE)
    commission_model: CommissionModel = Field(default=CommissionModel.REVENUE_SHARE)
    default_commission_rate: Optional[Decimal] = Field(
        None,
        ge=Decimal("0"),
        le=Decimal("1"),
        description="Commission rate (0-1, e.g., 0.15 for 15%)",
    )

    # Contact information
    primary_email: EmailStr
    billing_email: Optional[EmailStr] = None
    support_email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=30)

    # Address
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state_province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, pattern="^[A-Z]{2}$", description="ISO 3166-1 alpha-2")

    # Business information
    tax_id: Optional[str] = Field(None, max_length=50)
    vat_number: Optional[str] = Field(None, max_length=50)
    business_registration: Optional[str] = Field(None, max_length=100)

    # SLA
    sla_response_hours: Optional[int] = Field(None, ge=0)
    sla_uptime_percentage: Optional[Decimal] = Field(None, ge=Decimal("0"), le=Decimal("100"))

    @field_validator("primary_email", "billing_email", "support_email")
    @classmethod
    def normalize_email(cls, v: Optional[EmailStr]) -> Optional[str]:
        if v:
            return v.lower()
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            raise ValueError("Phone number must contain only digits, +, -, and spaces")
        return v


class PartnerCreate(PartnerBase):
    """Schema for creating a new partner."""

    external_id: Optional[str] = Field(None, max_length=100)
    metadata: dict[str, Any] = Field(default_factory=dict)
    custom_fields: dict[str, Any] = Field(default_factory=dict)


class PartnerUpdate(BaseModel):
    """Schema for updating partner information."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    # All fields optional for partial updates
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    legal_name: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None

    status: Optional[PartnerStatus] = None
    tier: Optional[PartnerTier] = None
    commission_model: Optional[CommissionModel] = None
    default_commission_rate: Optional[Decimal] = Field(None, ge=Decimal("0"), le=Decimal("1"))

    # Contact information
    primary_email: Optional[EmailStr] = None
    billing_email: Optional[EmailStr] = None
    support_email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=30)

    # Address
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state_province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, pattern="^[A-Z]{2}$")

    # Business information
    tax_id: Optional[str] = Field(None, max_length=50)
    vat_number: Optional[str] = Field(None, max_length=50)
    business_registration: Optional[str] = Field(None, max_length=100)

    # SLA
    sla_response_hours: Optional[int] = Field(None, ge=0)
    sla_uptime_percentage: Optional[Decimal] = Field(None, ge=Decimal("0"), le=Decimal("100"))

    # Dates
    partnership_end_date: Optional[datetime] = None
    last_review_date: Optional[datetime] = None
    next_review_date: Optional[datetime] = None

    # Metadata
    metadata: Optional[dict[str, Any]] = None
    custom_fields: Optional[dict[str, Any]] = None


class PartnerResponse(PartnerBase):
    """Schema for partner response."""

    id: UUID
    partner_number: str
    status: PartnerStatus

    # Dates
    partnership_start_date: Optional[datetime] = None
    partnership_end_date: Optional[datetime] = None
    last_review_date: Optional[datetime] = None
    next_review_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Metrics
    total_customers: int
    total_revenue_generated: Decimal
    total_commissions_earned: Decimal
    total_commissions_paid: Decimal
    total_referrals: int
    converted_referrals: int

    # Metadata
    metadata: dict[str, Any]
    custom_fields: dict[str, Any]


class PartnerListResponse(BaseModel):
    """Response for partner list endpoint."""

    partners: list[PartnerResponse]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)


# ============================================================================
# Partner User Schemas
# ============================================================================


class PartnerUserBase(BaseModel):
    """Base partner user schema."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        from_attributes=True,
    )

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=30)
    role: str = Field(min_length=1, max_length=50, description="Role within partner organization")
    is_primary_contact: bool = Field(default=False)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return v.lower()


class PartnerUserCreate(PartnerUserBase):
    """Schema for creating a partner user."""

    partner_id: UUID
    user_id: Optional[UUID] = Field(None, description="Link to auth user account")


class PartnerUserUpdate(BaseModel):
    """Schema for updating partner user."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=30)
    role: Optional[str] = Field(None, min_length=1, max_length=50)
    is_primary_contact: Optional[bool] = None
    is_active: Optional[bool] = None


class PartnerUserResponse(PartnerUserBase):
    """Schema for partner user response."""

    id: UUID
    partner_id: UUID
    user_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Partner Account Schemas
# ============================================================================


class PartnerAccountBase(BaseModel):
    """Base partner account schema."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        from_attributes=True,
    )

    partner_id: UUID
    customer_id: UUID
    engagement_type: str = Field(min_length=1, max_length=50)
    custom_commission_rate: Optional[Decimal] = Field(None, ge=Decimal("0"), le=Decimal("1"))
    notes: Optional[str] = None


class PartnerAccountCreate(PartnerAccountBase):
    """Schema for creating partner account assignment."""

    metadata: dict[str, Any] = Field(default_factory=dict)


class PartnerAccountUpdate(BaseModel):
    """Schema for updating partner account."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    engagement_type: Optional[str] = Field(None, min_length=1, max_length=50)
    custom_commission_rate: Optional[Decimal] = Field(None, ge=Decimal("0"), le=Decimal("1"))
    is_active: Optional[bool] = None
    end_date: Optional[datetime] = None
    notes: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class PartnerAccountResponse(PartnerAccountBase):
    """Schema for partner account response."""

    id: UUID
    start_date: datetime
    end_date: Optional[datetime] = None
    is_active: bool
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Commission Event Schemas
# ============================================================================


class PartnerCommissionEventBase(BaseModel):
    """Base commission event schema."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        from_attributes=True,
    )

    partner_id: UUID
    commission_amount: Decimal = Field(ge=Decimal("0"))
    currency: str = Field(default="USD", min_length=3, max_length=3, description="ISO 4217 code")
    event_type: str = Field(min_length=1, max_length=50)


class PartnerCommissionEventCreate(PartnerCommissionEventBase):
    """Schema for creating commission event."""

    invoice_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    base_amount: Optional[Decimal] = Field(None, ge=Decimal("0"))
    commission_rate: Optional[Decimal] = Field(None, ge=Decimal("0"), le=Decimal("1"))
    notes: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PartnerCommissionEventUpdate(BaseModel):
    """Schema for updating commission event."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    status: Optional[CommissionStatus] = None
    payout_id: Optional[UUID] = None
    notes: Optional[str] = None


class PartnerCommissionEventResponse(PartnerCommissionEventBase):
    """Schema for commission event response."""

    id: UUID
    invoice_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    base_amount: Optional[Decimal] = None
    commission_rate: Optional[Decimal] = None
    status: CommissionStatus
    event_date: datetime
    payout_id: Optional[UUID] = None
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class PartnerCommissionEventListResponse(BaseModel):
    """Response for commission event list."""

    events: list[PartnerCommissionEventResponse]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)


# ============================================================================
# Referral Lead Schemas
# ============================================================================


class ReferralLeadBase(BaseModel):
    """Base referral lead schema."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        from_attributes=True,
    )

    partner_id: UUID
    company_name: Optional[str] = Field(None, max_length=255)
    contact_name: str = Field(min_length=1, max_length=255)
    contact_email: EmailStr
    contact_phone: Optional[str] = Field(None, max_length=30)
    estimated_value: Optional[Decimal] = Field(None, ge=Decimal("0"))
    notes: Optional[str] = None

    @field_validator("contact_email")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return v.lower()


class ReferralLeadCreate(ReferralLeadBase):
    """Schema for creating referral lead."""

    source: Optional[str] = Field(None, max_length=100, description="Referral source/campaign")
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReferralLeadUpdate(BaseModel):
    """Schema for updating referral lead."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    company_name: Optional[str] = Field(None, max_length=255)
    contact_name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=30)
    estimated_value: Optional[Decimal] = Field(None, ge=Decimal("0"))
    status: Optional[ReferralStatus] = None
    notes: Optional[str] = None
    converted_customer_id: Optional[UUID] = None
    conversion_date: Optional[datetime] = None
    actual_value: Optional[Decimal] = Field(None, ge=Decimal("0"))
    first_contact_date: Optional[datetime] = None
    qualified_date: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None


class ReferralLeadResponse(ReferralLeadBase):
    """Schema for referral lead response."""

    id: UUID
    status: ReferralStatus
    submitted_date: datetime
    converted_customer_id: Optional[UUID] = None
    conversion_date: Optional[datetime] = None
    actual_value: Optional[Decimal] = None
    first_contact_date: Optional[datetime] = None
    qualified_date: Optional[datetime] = None
    source: Optional[str] = None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ReferralLeadListResponse(BaseModel):
    """Response for referral lead list."""

    referrals: list[ReferralLeadResponse]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)


# ============================================================================
# Summary/Analytics Schemas
# ============================================================================


class PartnerSummary(BaseModel):
    """Partner performance summary."""

    partner_id: UUID
    partner_name: str
    status: PartnerStatus
    tier: PartnerTier

    # Counts
    active_customers: int
    total_referrals: int
    converted_referrals: int

    # Financial
    total_revenue: Decimal
    pending_commissions: Decimal
    paid_commissions: Decimal
    outstanding_balance: Decimal

    # Rates
    conversion_rate: float = Field(ge=0, le=100, description="Referral conversion percentage")
    average_deal_value: Decimal


class PartnerPayoutSummary(BaseModel):
    """Payout summary for a partner."""

    partner_id: UUID
    period_start: datetime
    period_end: datetime
    currency: str

    # Amounts
    total_commission_events: int
    total_commission_amount: Decimal
    adjustments: Decimal = Field(default=Decimal("0"))
    net_payout_amount: Decimal

    # Status
    status: PayoutStatus
    payout_date: Optional[datetime] = None

    # Event breakdown
    events: list[PartnerCommissionEventResponse] = Field(default_factory=list)
