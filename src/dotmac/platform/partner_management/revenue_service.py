"""
Partner Revenue Service.

Provides revenue tracking, commission calculation, and payout management
for partner portal following project patterns.
"""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import structlog
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.partner_management.models import (
    CommissionStatus,
    Partner,
    PartnerCommissionEvent,
    PartnerPayout,
    PayoutStatus,
)
from dotmac.platform.partner_management.schemas import (
    PartnerCommissionEventResponse,
    PartnerPayoutResponse,
    PartnerRevenueMetrics,
)
from dotmac.platform.tenant import get_current_tenant_id

logger = structlog.get_logger(__name__)


class PartnerRevenueService:
    """Service for managing partner revenue, commissions, and payouts."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _resolve_tenant_id(self) -> str:
        """Resolve the current tenant ID from context or use default."""
        tenant_id_value = get_current_tenant_id()
        if not tenant_id_value:
            tenant_id = "default-tenant"
            logger.debug("No tenant context found, using default tenant")
        elif isinstance(tenant_id_value, str):
            tenant_id = tenant_id_value
        else:
            tenant_id = str(tenant_id_value)
        return tenant_id

    async def get_partner_revenue_metrics(
        self,
        partner_id: UUID,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> PartnerRevenueMetrics:
        """
        Get revenue metrics for a partner over a time period.

        Args:
            partner_id: Partner UUID
            period_start: Start of period (optional)
            period_end: End of period (optional)

        Returns:
            PartnerRevenueMetrics with total commissions, payouts, pending amount
        """
        # Set default period if not provided
        if period_end is None:
            period_end = datetime.now(UTC)
        if period_start is None:
            period_start = datetime.now(UTC).replace(day=1)  # Start of current month

        # Get total commission events (APPROVED or PAID)
        total_commissions_query = select(
            func.coalesce(func.sum(PartnerCommissionEvent.commission_amount), Decimal("0")),
            func.count(PartnerCommissionEvent.id),
        ).where(
            and_(
                PartnerCommissionEvent.partner_id == partner_id,
                PartnerCommissionEvent.status.in_(
                    [CommissionStatus.APPROVED, CommissionStatus.PAID]
                ),
                PartnerCommissionEvent.event_date >= period_start,
                PartnerCommissionEvent.event_date <= period_end,
            )
        )
        result = await self.session.execute(total_commissions_query)
        total_commissions, total_commission_count = result.one()

        # Get total payouts
        total_payouts_query = select(
            func.coalesce(func.sum(PartnerPayout.total_amount), Decimal("0"))
        ).where(
            and_(
                PartnerPayout.partner_id == partner_id,
                PartnerPayout.status == PayoutStatus.COMPLETED,
                PartnerPayout.payout_date >= period_start,
                PartnerPayout.payout_date <= period_end,
            )
        )
        result = await self.session.execute(total_payouts_query)
        total_payouts = result.scalar() or Decimal("0")

        # Get pending commission amount (approved but not paid)
        pending_query = select(
            func.coalesce(func.sum(PartnerCommissionEvent.commission_amount), Decimal("0"))
        ).where(
            and_(
                PartnerCommissionEvent.partner_id == partner_id,
                PartnerCommissionEvent.status == CommissionStatus.APPROVED,
                PartnerCommissionEvent.payout_id.is_(None),
            )
        )
        result = await self.session.execute(pending_query)
        pending_amount = result.scalar() or Decimal("0")

        return PartnerRevenueMetrics(
            partner_id=partner_id,
            period_start=period_start,
            period_end=period_end,
            total_commissions=total_commissions,
            total_commission_count=int(total_commission_count),
            total_payouts=total_payouts,
            pending_amount=pending_amount,
            currency="USD",  # TODO: Support multi-currency
        )

    async def list_commission_events(
        self,
        partner_id: UUID,
        status: CommissionStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PartnerCommissionEventResponse]:
        """
        List commission events for a partner.

        Args:
            partner_id: Partner UUID
            status: Optional filter by commission status
            limit: Max number of results (default: 100)
            offset: Pagination offset (default: 0)

        Returns:
            List of PartnerCommissionEventResponse
        """
        query = select(PartnerCommissionEvent).where(
            PartnerCommissionEvent.partner_id == partner_id
        )

        if status is not None:
            query = query.where(PartnerCommissionEvent.status == status)

        query = query.order_by(PartnerCommissionEvent.event_date.desc()).limit(limit).offset(offset)

        result = await self.session.execute(query)
        events = result.scalars().all()

        # Manually construct response to avoid metadata field conflict with SQLAlchemy
        return [
            PartnerCommissionEventResponse(
                id=event.id,
                partner_id=event.partner_id,
                invoice_id=event.invoice_id,
                customer_id=event.customer_id,
                commission_amount=event.commission_amount,
                currency=event.currency,
                base_amount=event.base_amount,
                commission_rate=event.commission_rate,
                status=event.status,
                event_type=event.event_type,
                event_date=event.event_date,
                payout_id=event.payout_id,
                paid_at=event.paid_at,
                notes=event.notes,
                metadata_=(
                    event.metadata_
                    if hasattr(event, "metadata_") and isinstance(event.metadata_, dict)
                    else {}
                ),
                created_at=event.created_at,
                updated_at=event.updated_at,
            )
            for event in events
        ]

    async def list_payouts(
        self,
        partner_id: UUID,
        status: PayoutStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PartnerPayoutResponse]:
        """
        List payouts for a partner.

        Args:
            partner_id: Partner UUID
            status: Optional filter by payout status
            limit: Max number of results (default: 100)
            offset: Pagination offset (default: 0)

        Returns:
            List of PartnerPayoutResponse
        """
        query = select(PartnerPayout).where(PartnerPayout.partner_id == partner_id)

        if status is not None:
            query = query.where(PartnerPayout.status == status)

        query = query.order_by(PartnerPayout.payout_date.desc()).limit(limit).offset(offset)

        result = await self.session.execute(query)
        payouts = result.scalars().all()

        return [PartnerPayoutResponse.model_validate(payout) for payout in payouts]

    async def create_payout_batch(
        self,
        partner_id: UUID,
        period_start: datetime,
        period_end: datetime,
        currency: str = "USD",
    ) -> PartnerPayoutResponse:
        """
        Create a payout batch aggregating approved unpaid commissions.

        Args:
            partner_id: Partner UUID
            period_start: Start of payout period
            period_end: End of payout period
            currency: Currency code (default: "USD")

        Returns:
            PartnerPayoutResponse for the created payout
        """
        # Get all approved commission events without payout
        events_query = select(PartnerCommissionEvent).where(
            and_(
                PartnerCommissionEvent.partner_id == partner_id,
                PartnerCommissionEvent.status == CommissionStatus.APPROVED,
                PartnerCommissionEvent.payout_id.is_(None),
                PartnerCommissionEvent.event_date >= period_start,
                PartnerCommissionEvent.event_date <= period_end,
            )
        )

        result = await self.session.execute(events_query)
        commission_events = list(result.scalars().all())

        if not commission_events:
            raise ValueError("No approved commissions found for the period")

        # Calculate total amount
        total_amount = sum(event.commission_amount for event in commission_events)

        # Create payout batch
        payout = PartnerPayout(
            id=uuid4(),
            partner_id=partner_id,
            tenant_id=commission_events[0].tenant_id,  # Use tenant from commission
            total_amount=total_amount,
            currency=currency,
            status=PayoutStatus.PENDING,
            payout_date=datetime.now(UTC),
            period_start=period_start,
            period_end=period_end,
            commission_count=len(commission_events),
        )

        self.session.add(payout)

        # Link commission events to payout (keep status as APPROVED for financial reporting)
        for event in commission_events:
            event.payout_id = payout.id

        await self.session.commit()
        await self.session.refresh(payout)

        return PartnerPayoutResponse.model_validate(payout)

    async def calculate_commission(
        self,
        partner_id: UUID,
        customer_id: UUID,
        invoice_amount: Decimal,
    ) -> Decimal:
        """
        Calculate commission for a partner based on their model and rates.

        Args:
            partner_id: Partner UUID
            customer_id: Customer UUID
            invoice_amount: Invoice amount

        Returns:
            Calculated commission amount
        """
        # Get partner
        partner_result = await self.session.execute(select(Partner).where(Partner.id == partner_id))
        partner = partner_result.scalar_one_or_none()
        if not partner:
            raise ValueError(f"Partner {partner_id} not found")

        # Check for custom commission rate in partner account
        from dotmac.platform.partner_management.models import CommissionModel, PartnerAccount

        account_result = await self.session.execute(
            select(PartnerAccount).where(
                and_(
                    PartnerAccount.partner_id == partner_id,
                    PartnerAccount.customer_id == customer_id,
                    PartnerAccount.is_active.is_(True),
                )
            )
        )
        account = account_result.scalar_one_or_none()

        # Determine commission rate
        rate: Decimal
        if account and account.custom_commission_rate is not None:
            rate = Decimal(account.custom_commission_rate)
        elif partner.default_commission_rate is not None:
            rate = Decimal(partner.default_commission_rate)
        else:
            rate = Decimal("0.00")

        # Calculate based on commission model
        if partner.commission_model == CommissionModel.FLAT_FEE:
            # Rate is the fixed fee amount
            return rate
        else:
            # Revenue share, tiered, or hybrid - use percentage
            return invoice_amount * rate
