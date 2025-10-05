"""Partner Portal Router - Self-service endpoints for partners."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.db import get_session_dependency
from dotmac.platform.partner_management.models import (
    Partner,
    PartnerAccount,
    PartnerCommissionEvent,
    ReferralLead,
    ReferralStatus,
)
from dotmac.platform.partner_management.schemas import (
    PartnerCommissionEventResponse,
    PartnerResponse,
    PartnerUpdate,
    ReferralLeadCreate,
    ReferralLeadResponse,
)

router = APIRouter(prefix="/portal", tags=["Partner Portal"])


# Portal-specific schemas
class PartnerDashboardStats(BaseModel):
    """Dashboard statistics for partner portal."""

    total_customers: int = Field(default=0, description="Total customers assigned")
    active_customers: int = Field(default=0, description="Currently active customers")
    total_revenue_generated: Decimal = Field(
        default=Decimal("0"), description="Total revenue from customers"
    )
    total_commissions_earned: Decimal = Field(
        default=Decimal("0"), description="Total commissions earned"
    )
    total_commissions_paid: Decimal = Field(
        default=Decimal("0"), description="Total commissions paid out"
    )
    pending_commissions: Decimal = Field(
        default=Decimal("0"), description="Pending commission amount"
    )
    total_referrals: int = Field(default=0, description="Total referrals submitted")
    converted_referrals: int = Field(default=0, description="Referrals that converted")
    pending_referrals: int = Field(default=0, description="Referrals pending conversion")
    conversion_rate: float = Field(default=0.0, description="Referral conversion rate")
    current_tier: str = Field(description="Current partner tier")
    commission_model: str = Field(description="Commission model")
    default_commission_rate: Decimal = Field(description="Default commission rate")


class PartnerCustomerResponse(BaseModel):
    """Partner customer information for portal."""

    id: UUID
    customer_id: UUID
    customer_name: str
    engagement_type: str
    custom_commission_rate: Decimal | None = None
    total_revenue: Decimal
    total_commissions: Decimal
    start_date: datetime
    end_date: datetime | None = None
    is_active: bool


# Dependency to get current partner from session/auth
# TODO: Implement actual partner authentication
async def get_current_partner(
    db: AsyncSession = Depends(get_session_dependency),
) -> Partner:
    """Get currently authenticated partner.

    This is a placeholder - should be replaced with actual partner auth.
    For now, returns first partner for testing.
    """
    result = await db.execute(select(Partner).limit(1))
    partner = result.scalar_one_or_none()

    if not partner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")

    return partner


@router.get("/dashboard", response_model=PartnerDashboardStats)
async def get_dashboard_stats(
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_session_dependency),
):
    """Get dashboard statistics for partner portal."""

    # Count active customers
    active_customers_result = await db.execute(
        select(func.count(PartnerAccount.id))
        .where(PartnerAccount.partner_id == partner.id)
        .where(PartnerAccount.is_active)
    )
    active_customers = active_customers_result.scalar() or 0

    # Count pending referrals
    pending_referrals_result = await db.execute(
        select(func.count(ReferralLead.id))
        .where(ReferralLead.partner_id == partner.id)
        .where(
            ReferralLead.status.in_(
                [ReferralStatus.NEW, ReferralStatus.CONTACTED, ReferralStatus.QUALIFIED]
            )
        )
    )
    pending_referrals = pending_referrals_result.scalar() or 0

    # Calculate pending commissions
    pending_commissions = partner.total_commissions_earned - partner.total_commissions_paid

    # Calculate conversion rate
    conversion_rate = 0.0
    if partner.total_referrals > 0:
        conversion_rate = (partner.converted_referrals / partner.total_referrals) * 100

    return PartnerDashboardStats(
        total_customers=partner.total_customers,
        active_customers=active_customers,
        total_revenue_generated=partner.total_revenue_generated,
        total_commissions_earned=partner.total_commissions_earned,
        total_commissions_paid=partner.total_commissions_paid,
        pending_commissions=pending_commissions,
        total_referrals=partner.total_referrals,
        converted_referrals=partner.converted_referrals,
        pending_referrals=pending_referrals,
        conversion_rate=conversion_rate,
        current_tier=partner.tier.value,
        commission_model=partner.commission_model.value,
        default_commission_rate=partner.default_commission_rate or Decimal("0"),
    )


@router.get("/profile", response_model=PartnerResponse)
async def get_partner_profile(
    partner: Partner = Depends(get_current_partner),
):
    """Get current partner profile."""
    return partner


@router.patch("/profile", response_model=PartnerResponse)
async def update_partner_profile(
    data: PartnerUpdate,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_session_dependency),
):
    """Update partner profile (limited fields)."""

    # Only allow updating certain fields from portal
    allowed_fields = {
        "company_name",
        "legal_name",
        "website",
        "billing_email",
        "phone",
    }

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in allowed_fields and value is not None:
            setattr(partner, field, value)

    await db.commit()
    await db.refresh(partner)

    return partner


@router.get("/referrals", response_model=list[ReferralLeadResponse])
async def list_partner_referrals(
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_session_dependency),
):
    """List all referrals submitted by partner."""

    result = await db.execute(
        select(ReferralLead)
        .where(ReferralLead.partner_id == partner.id)
        .order_by(ReferralLead.created_at.desc())
    )

    return result.scalars().all()


@router.post("/referrals", response_model=ReferralLeadResponse, status_code=status.HTTP_201_CREATED)
async def submit_referral(
    data: ReferralLeadCreate,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_session_dependency),
):
    """Submit a new referral."""

    referral = ReferralLead(
        partner_id=partner.id,
        tenant_id=partner.tenant_id,
        **data.model_dump(exclude={"partner_id"}),
    )

    db.add(referral)

    # Update partner referral count
    partner.total_referrals += 1

    await db.commit()
    await db.refresh(referral)

    return referral


@router.get("/commissions", response_model=list[PartnerCommissionEventResponse])
async def list_partner_commissions(
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_session_dependency),
):
    """List all commission events for partner."""

    result = await db.execute(
        select(PartnerCommissionEvent)
        .where(PartnerCommissionEvent.partner_id == partner.id)
        .order_by(PartnerCommissionEvent.event_date.desc())
    )

    return result.scalars().all()


@router.get("/customers", response_model=list[PartnerCustomerResponse])
async def list_partner_customers(
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_session_dependency),
):
    """List all customers assigned to partner."""

    result = await db.execute(
        select(PartnerAccount)
        .where(PartnerAccount.partner_id == partner.id)
        .order_by(PartnerAccount.created_at.desc())
    )

    accounts = result.scalars().all()

    # Transform to response format with aggregated financials
    customer_responses = []
    for account in accounts:
        # Aggregate revenue and commissions from commission events
        commission_result = await db.execute(
            select(
                func.sum(PartnerCommissionEvent.base_amount).label("total_revenue"),
                func.sum(PartnerCommissionEvent.commission_amount).label("total_commissions"),
            )
            .where(PartnerCommissionEvent.partner_id == partner.id)
            .where(PartnerCommissionEvent.customer_id == account.customer_id)
        )
        aggregates = commission_result.one()

        customer_responses.append(
            PartnerCustomerResponse(
                id=account.id,
                customer_id=account.customer_id,
                customer_name=f"Customer {str(account.customer_id)[:8]}",  # Placeholder - in production join with customer table
                engagement_type=account.engagement_type or "direct",
                custom_commission_rate=account.custom_commission_rate,
                total_revenue=aggregates.total_revenue or Decimal("0.00"),
                total_commissions=aggregates.total_commissions or Decimal("0.00"),
                start_date=account.start_date,
                end_date=account.end_date,
                is_active=account.is_active,
            )
        )

    return customer_responses
