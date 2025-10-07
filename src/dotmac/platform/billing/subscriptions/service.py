"""
Subscription management service.

Handles complete subscription lifecycle with simple, clear operations.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

import structlog
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.billing.exceptions import (
    PlanNotFoundError,
    SubscriptionError,
    SubscriptionNotFoundError,
)
from dotmac.platform.billing.models import (
    BillingSubscriptionEventTable,
    BillingSubscriptionPlanTable,
    BillingSubscriptionTable,
)
from dotmac.platform.billing.subscriptions.models import (
    BillingCycle,
    ProrationBehavior,
    ProrationResult,
    Subscription,
    SubscriptionCreateRequest,
    SubscriptionEventType,
    SubscriptionPlan,
    SubscriptionPlanChangeRequest,
    SubscriptionPlanCreateRequest,
    SubscriptionStatus,
    SubscriptionUpdateRequest,
    UsageRecordRequest,
)

logger = structlog.get_logger(__name__)


def generate_plan_id() -> str:
    """Generate unique plan ID."""
    return f"plan_{uuid4().hex[:12]}"


def generate_subscription_id() -> str:
    """Generate unique subscription ID."""
    return f"sub_{uuid4().hex[:12]}"


def generate_event_id() -> str:
    """Generate unique event ID."""
    return f"evt_{uuid4().hex[:12]}"


class SubscriptionService:
    """Complete subscription lifecycle management."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session

    # ========================================
    # Subscription Plan Management
    # ========================================

    async def create_plan(
        self, plan_data: SubscriptionPlanCreateRequest, tenant_id: str
    ) -> SubscriptionPlan:
        """Create a new subscription plan."""

        # Create database record
        db_plan = BillingSubscriptionPlanTable(
            plan_id=generate_plan_id(),
            tenant_id=tenant_id,
            product_id=plan_data.product_id,
            name=plan_data.name,
            description=plan_data.description,
            billing_cycle=plan_data.billing_cycle.value,
            price=plan_data.price,
            currency=plan_data.currency,
            setup_fee=plan_data.setup_fee,
            trial_days=plan_data.trial_days,
            included_usage=plan_data.included_usage,
            overage_rates={k: str(v) for k, v in plan_data.overage_rates.items()},
            metadata_json=plan_data.metadata,
        )

        self.db.add(db_plan)
        await self.db.commit()
        await self.db.refresh(db_plan)

        plan = self._db_to_pydantic_plan(db_plan)

        logger.info(
            "Subscription plan created",
            plan_id=plan.plan_id,
            name=plan.name,
            billing_cycle=plan.billing_cycle,
            price=str(plan.price),
            tenant_id=tenant_id,
        )

        return plan

    async def get_plan(self, plan_id: str, tenant_id: str) -> SubscriptionPlan:
        """Get subscription plan by ID."""

        stmt = select(BillingSubscriptionPlanTable).where(
            and_(
                BillingSubscriptionPlanTable.plan_id == plan_id,
                BillingSubscriptionPlanTable.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        db_plan = result.scalar_one_or_none()

        if not db_plan:
            raise PlanNotFoundError(f"Plan {plan_id} not found")

        return self._db_to_pydantic_plan(db_plan)

    async def list_plans(
        self,
        tenant_id: str,
        product_id: str | None = None,
        billing_cycle: BillingCycle | None = None,
        active_only: bool = True,
    ) -> list[SubscriptionPlan]:
        """List subscription plans with filtering."""

        stmt = select(BillingSubscriptionPlanTable).where(
            BillingSubscriptionPlanTable.tenant_id == tenant_id
        )

        if product_id:
            stmt = stmt.where(BillingSubscriptionPlanTable.product_id == product_id)

        if billing_cycle:
            stmt = stmt.where(BillingSubscriptionPlanTable.billing_cycle == billing_cycle.value)

        if active_only:
            stmt = stmt.where(BillingSubscriptionPlanTable.is_active)

        stmt = stmt.order_by(BillingSubscriptionPlanTable.name)

        result = await self.db.execute(stmt)
        db_plans = result.scalars().all()

        return [self._db_to_pydantic_plan(db_plan) for db_plan in db_plans]

    # ========================================
    # Subscription Management
    # ========================================

    async def create_subscription(
        self, subscription_data: SubscriptionCreateRequest, tenant_id: str
    ) -> Subscription:
        """Create new subscription with proper lifecycle setup."""

        # Get the plan
        plan = await self.get_plan(subscription_data.plan_id, tenant_id)

        # Calculate subscription periods
        start_date = subscription_data.start_date or datetime.now(UTC)
        period_start = start_date
        period_end = self._calculate_period_end(period_start, plan.billing_cycle)

        # Handle trial period
        trial_end = None
        status = SubscriptionStatus.ACTIVE

        if subscription_data.trial_end_override:
            trial_end = subscription_data.trial_end_override
            status = SubscriptionStatus.TRIALING
        elif plan.has_trial():
            trial_days = plan.trial_days if plan.trial_days is not None else 0
            trial_end = start_date + timedelta(days=trial_days)
            status = SubscriptionStatus.TRIALING

        # Create subscription record
        db_subscription = BillingSubscriptionTable(
            subscription_id=generate_subscription_id(),
            tenant_id=tenant_id,
            customer_id=subscription_data.customer_id,
            plan_id=subscription_data.plan_id,
            current_period_start=period_start,
            current_period_end=period_end,
            status=status.value,
            trial_end=trial_end,
            custom_price=subscription_data.custom_price,
            metadata_json=subscription_data.metadata,
        )

        self.db.add(db_subscription)
        await self.db.commit()
        await self.db.refresh(db_subscription)

        subscription = self._db_to_pydantic_subscription(db_subscription)

        # Create subscription event
        await self._create_event(
            subscription.subscription_id,
            SubscriptionEventType.CREATED,
            {
                "plan_id": plan.plan_id,
                "trial_days": plan.trial_days,
                "custom_price": (
                    str(subscription_data.custom_price) if subscription_data.custom_price else None
                ),
            },
            tenant_id,
        )

        logger.info(
            "Subscription created",
            subscription_id=subscription.subscription_id,
            customer_id=subscription.customer_id,
            plan_id=subscription.plan_id,
            status=subscription.status,
            trial_end=subscription.trial_end,
            tenant_id=tenant_id,
        )

        return subscription

    async def get_subscription(self, subscription_id: str, tenant_id: str) -> Subscription:
        """Get subscription by ID."""

        stmt = select(BillingSubscriptionTable).where(
            and_(
                BillingSubscriptionTable.subscription_id == subscription_id,
                BillingSubscriptionTable.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        db_subscription = result.scalar_one_or_none()

        if not db_subscription:
            raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found")

        return self._db_to_pydantic_subscription(db_subscription)

    async def list_subscriptions(
        self,
        tenant_id: str,
        customer_id: str | None = None,
        plan_id: str | None = None,
        status: SubscriptionStatus | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> list[Subscription]:
        """List subscriptions with filtering and pagination."""

        stmt = select(BillingSubscriptionTable).where(
            BillingSubscriptionTable.tenant_id == tenant_id
        )

        if customer_id:
            stmt = stmt.where(BillingSubscriptionTable.customer_id == customer_id)

        if plan_id:
            stmt = stmt.where(BillingSubscriptionTable.plan_id == plan_id)

        if status:
            stmt = stmt.where(BillingSubscriptionTable.status == status.value)

        # Apply pagination
        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit)

        # Order by creation date, newest first
        stmt = stmt.order_by(BillingSubscriptionTable.created_at.desc())

        result = await self.db.execute(stmt)
        db_subscriptions = result.scalars().all()

        return [self._db_to_pydantic_subscription(db_sub) for db_sub in db_subscriptions]

    async def update_subscription(
        self, subscription_id: str, updates: SubscriptionUpdateRequest, tenant_id: str
    ) -> Subscription:
        """Update subscription details."""

        # Get existing subscription
        stmt = select(BillingSubscriptionTable).where(
            and_(
                BillingSubscriptionTable.subscription_id == subscription_id,
                BillingSubscriptionTable.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        db_subscription = result.scalar_one_or_none()

        if not db_subscription:
            raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found")

        # Apply updates
        update_data = updates.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "metadata":
                db_subscription.metadata_json = value
            else:
                setattr(db_subscription, field, value)

        await self.db.commit()
        await self.db.refresh(db_subscription)

        subscription = self._db_to_pydantic_subscription(db_subscription)

        logger.info(
            "Subscription updated",
            subscription_id=subscription_id,
            updates=list(update_data.keys()),
            tenant_id=tenant_id,
        )

        return subscription

    # ========================================
    # Subscription Lifecycle Operations
    # ========================================

    async def change_plan(
        self,
        subscription_id: str,
        change_request: SubscriptionPlanChangeRequest,
        tenant_id: str,
        user_id: str | None = None,
    ) -> tuple[Subscription, ProrationResult | None]:
        """Change subscription plan with proration handling."""

        subscription = await self.get_subscription(subscription_id, tenant_id)
        old_plan = await self.get_plan(subscription.plan_id, tenant_id)
        new_plan = await self.get_plan(change_request.new_plan_id, tenant_id)

        if subscription.plan_id == change_request.new_plan_id:
            raise SubscriptionError("Subscription is already on the requested plan")

        if not subscription.is_active():
            raise SubscriptionError("Cannot change plan for inactive subscription")

        # Calculate proration
        proration_result = None
        if change_request.proration_behavior == ProrationBehavior.CREATE_PRORATIONS:
            proration_result = self._calculate_proration(subscription, old_plan, new_plan)

        # Update subscription
        effective_date = change_request.effective_date or datetime.now(UTC)

        stmt = select(BillingSubscriptionTable).where(
            and_(
                BillingSubscriptionTable.subscription_id == subscription_id,
                BillingSubscriptionTable.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        db_subscription = result.scalar_one_or_none()

        if db_subscription is None:
            raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found")

        # Use setattr to avoid mypy Column assignment errors
        setattr(db_subscription, "plan_id", change_request.new_plan_id)

        await self.db.commit()
        await self.db.refresh(db_subscription)

        updated_subscription = self._db_to_pydantic_subscription(db_subscription)

        # Create plan change event
        await self._create_event(
            subscription_id,
            SubscriptionEventType.PLAN_CHANGED,
            {
                "old_plan_id": old_plan.plan_id,
                "new_plan_id": new_plan.plan_id,
                "proration_behavior": change_request.proration_behavior,
                "proration_amount": (
                    str(proration_result.proration_amount) if proration_result else "0"
                ),
                "effective_date": effective_date.isoformat(),
            },
            tenant_id,
            user_id,
        )

        logger.info(
            "Subscription plan changed",
            subscription_id=subscription_id,
            old_plan=old_plan.name,
            new_plan=new_plan.name,
            proration_amount=str(proration_result.proration_amount) if proration_result else "0",
            tenant_id=tenant_id,
        )

        return updated_subscription, proration_result

    async def cancel_subscription(
        self,
        subscription_id: str,
        tenant_id: str,
        at_period_end: bool = True,
        user_id: str | None = None,
    ) -> Subscription:
        """Cancel subscription (immediate or at period end)."""

        subscription = await self.get_subscription(subscription_id, tenant_id)

        if not subscription.is_active():
            raise SubscriptionError("Subscription is not active")

        now = datetime.now(UTC)
        immediate = not at_period_end

        stmt = select(BillingSubscriptionTable).where(
            and_(
                BillingSubscriptionTable.subscription_id == subscription_id,
                BillingSubscriptionTable.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        db_subscription = result.scalar_one_or_none()

        if db_subscription is None:
            raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found")

        if immediate:
            # End subscription immediately - use setattr to avoid mypy Column assignment errors
            setattr(db_subscription, "status", SubscriptionStatus.ENDED.value)
            setattr(db_subscription, "ended_at", now)
            setattr(db_subscription, "canceled_at", now)
        else:
            # Cancel at period end (default behavior) - use setattr to avoid mypy Column assignment errors
            setattr(db_subscription, "cancel_at_period_end", True)
            setattr(db_subscription, "canceled_at", now)
            setattr(db_subscription, "status", SubscriptionStatus.CANCELED.value)

        await self.db.commit()
        await self.db.refresh(db_subscription)

        updated_subscription = self._db_to_pydantic_subscription(db_subscription)

        # Create cancellation event
        await self._create_event(
            subscription_id,
            SubscriptionEventType.CANCELED,
            {
                "immediate": immediate,
                "canceled_at": now.isoformat(),
                "period_end": subscription.current_period_end.isoformat(),
            },
            tenant_id,
            user_id,
        )

        logger.info(
            "Subscription canceled",
            subscription_id=subscription_id,
            immediate=immediate,
            canceled_at=now.isoformat(),
            tenant_id=tenant_id,
        )

        return updated_subscription

    async def reactivate_subscription(
        self, subscription_id: str, tenant_id: str, user_id: str | None = None
    ) -> Subscription:
        """Reactivate a canceled subscription (if still in current period)."""

        subscription = await self.get_subscription(subscription_id, tenant_id)

        if subscription.status != SubscriptionStatus.CANCELED:
            raise SubscriptionError("Only canceled subscriptions can be reactivated")

        if datetime.now(UTC) > subscription.current_period_end:
            raise SubscriptionError("Cannot reactivate subscription after period end")

        stmt = select(BillingSubscriptionTable).where(
            and_(
                BillingSubscriptionTable.subscription_id == subscription_id,
                BillingSubscriptionTable.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        db_subscription = result.scalar_one_or_none()

        if db_subscription is None:
            raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found")

        # Use setattr to avoid mypy Column assignment errors
        setattr(db_subscription, "status", SubscriptionStatus.ACTIVE.value)
        setattr(db_subscription, "cancel_at_period_end", False)
        setattr(db_subscription, "canceled_at", None)

        await self.db.commit()
        await self.db.refresh(db_subscription)

        updated_subscription = self._db_to_pydantic_subscription(db_subscription)

        # Create reactivation event
        await self._create_event(
            subscription_id,
            SubscriptionEventType.RESUMED,
            {"reactivated_at": datetime.now(UTC).isoformat()},
            tenant_id,
            user_id,
        )

        logger.info(
            "Subscription reactivated",
            subscription_id=subscription_id,
            tenant_id=tenant_id,
        )

        return updated_subscription

    # ========================================
    # Usage Tracking
    # ========================================

    async def record_usage(
        self, usage_request: UsageRecordRequest, tenant_id: str
    ) -> dict[str, int]:
        """Record usage for a subscription."""

        subscription = await self.get_subscription(usage_request.subscription_id, tenant_id)

        if not subscription.is_active():
            raise SubscriptionError("Cannot record usage for inactive subscription")

        usage_timestamp = usage_request.timestamp or datetime.now(UTC)

        # Verify usage is within current period
        if not (
            subscription.current_period_start <= usage_timestamp <= subscription.current_period_end
        ):
            raise SubscriptionError("Usage timestamp is outside current billing period")

        stmt = select(BillingSubscriptionTable).where(
            and_(
                BillingSubscriptionTable.subscription_id == usage_request.subscription_id,
                BillingSubscriptionTable.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        db_subscription = result.scalar_one_or_none()

        if db_subscription is None:
            raise SubscriptionNotFoundError(
                f"Subscription {usage_request.subscription_id} not found"
            )

        # Update usage records
        usage_records_raw = getattr(db_subscription, "usage_records", None)
        current_usage: dict[str, int] = usage_records_raw if usage_records_raw else {}
        current_usage[usage_request.usage_type] = (
            current_usage.get(usage_request.usage_type, 0) + usage_request.quantity
        )

        # Use setattr to avoid mypy Column assignment errors
        setattr(db_subscription, "usage_records", current_usage)

        await self.db.commit()
        await self.db.refresh(db_subscription)

        logger.info(
            "Usage recorded",
            subscription_id=usage_request.subscription_id,
            usage_type=usage_request.usage_type,
            quantity=usage_request.quantity,
            total_usage=current_usage[usage_request.usage_type],
            tenant_id=tenant_id,
        )

        return current_usage

    async def get_usage_for_period(self, subscription_id: str, tenant_id: str) -> dict[str, int]:
        """Get current period usage for subscription."""

        subscription = await self.get_subscription(subscription_id, tenant_id)
        return subscription.usage_records

    # ========================================
    # Renewal Processing (for background jobs)
    # ========================================

    async def get_subscriptions_due_for_renewal(
        self, tenant_id: str, look_ahead_days: int = 1
    ) -> list[Subscription]:
        """Get subscriptions that need renewal within the specified timeframe."""

        cutoff_date = datetime.now(UTC) + timedelta(days=look_ahead_days)

        stmt = select(BillingSubscriptionTable).where(
            and_(
                BillingSubscriptionTable.tenant_id == tenant_id,
                BillingSubscriptionTable.status == SubscriptionStatus.ACTIVE.value,
                BillingSubscriptionTable.current_period_end <= cutoff_date,
            )
        )

        result = await self.db.execute(stmt)
        db_subscriptions = result.scalars().all()

        return [self._db_to_pydantic_subscription(db_sub) for db_sub in db_subscriptions]

    # ========================================
    # Private Helper Methods
    # ========================================

    def _calculate_period_end(self, start_date: datetime, billing_cycle: BillingCycle) -> datetime:
        """Calculate period end date based on billing cycle."""

        if billing_cycle == BillingCycle.MONTHLY:
            # Add one month
            if start_date.month == 12:
                return start_date.replace(year=start_date.year + 1, month=1)
            else:
                return start_date.replace(month=start_date.month + 1)

        elif billing_cycle == BillingCycle.QUARTERLY:
            # Add 3 months
            new_month = start_date.month + 3
            new_year = start_date.year
            while new_month > 12:
                new_month -= 12
                new_year += 1
            return start_date.replace(year=new_year, month=new_month)

        elif billing_cycle == BillingCycle.ANNUAL:
            # Add one year
            return start_date.replace(year=start_date.year + 1)

        else:
            raise SubscriptionError(f"Unsupported billing cycle: {billing_cycle}")

    def _calculate_proration(
        self, subscription: Subscription, old_plan: SubscriptionPlan, new_plan: SubscriptionPlan
    ) -> ProrationResult:
        """Calculate simple proration for plan changes."""

        now = datetime.now(UTC)
        total_period_seconds = (
            subscription.current_period_end - subscription.current_period_start
        ).total_seconds()
        remaining_seconds = (subscription.current_period_end - now).total_seconds()

        if remaining_seconds <= 0:
            # No time remaining, no proration
            return ProrationResult(
                proration_amount=Decimal("0"),
                proration_description="No proration needed - period has ended",
                old_plan_unused_amount=Decimal("0"),
                new_plan_prorated_amount=Decimal("0"),
                days_remaining=0,
            )

        # Calculate proration based on remaining time
        remaining_ratio = Decimal(str(remaining_seconds / total_period_seconds))
        days_remaining = int((subscription.current_period_end - now).days)

        # Get effective prices
        old_price = subscription.custom_price or old_plan.price
        new_price = new_plan.price

        # Calculate unused amount from old plan
        old_plan_unused = old_price * remaining_ratio

        # Calculate prorated amount for new plan
        new_plan_prorated = new_price * remaining_ratio

        # Net proration (positive = customer owes money, negative = customer gets credit)
        proration_amount = new_plan_prorated - old_plan_unused

        description = (
            f"Plan change from {old_plan.name} to {new_plan.name} "
            f"with {days_remaining} days remaining in period. "
            f"Unused credit: ${old_plan_unused:.2f}, "
            f"New plan prorated charge: ${new_plan_prorated:.2f}"
        )

        return ProrationResult(
            proration_amount=proration_amount,
            proration_description=description,
            old_plan_unused_amount=old_plan_unused,
            new_plan_prorated_amount=new_plan_prorated,
            days_remaining=days_remaining,
        )

    async def _create_event(
        self,
        subscription_id: str,
        event_type: SubscriptionEventType,
        event_data: dict[str, Any],
        tenant_id: str,
        user_id: str | None = None,
    ) -> None:
        """Create a subscription event for audit trail."""

        db_event = BillingSubscriptionEventTable(
            event_id=generate_event_id(),
            tenant_id=tenant_id,
            subscription_id=subscription_id,
            event_type=event_type.value,
            event_data=event_data,
            user_id=user_id,
        )

        self.db.add(db_event)
        await self.db.commit()

    def _db_to_pydantic_plan(self, db_plan: BillingSubscriptionPlanTable) -> SubscriptionPlan:
        """Convert database plan to Pydantic model."""
        # Extract values from SQLAlchemy columns
        plan_id: str = str(db_plan.plan_id)
        tenant_id: str = str(db_plan.tenant_id)
        product_id: str = str(db_plan.product_id)
        name: str = str(db_plan.name)
        description: str | None = str(db_plan.description) if db_plan.description else None
        billing_cycle_value: str = str(db_plan.billing_cycle)
        price: Decimal = Decimal(str(db_plan.price))
        currency: str = str(db_plan.currency)
        setup_fee: Decimal | None = Decimal(str(db_plan.setup_fee)) if db_plan.setup_fee else None
        trial_days: int | None = int(db_plan.trial_days) if db_plan.trial_days is not None else None
        is_active: bool = bool(db_plan.is_active)

        # Handle JSON fields
        included_usage_raw = getattr(db_plan, "included_usage", None)
        included_usage: dict[str, int] = included_usage_raw if included_usage_raw else {}

        overage_rates_raw = getattr(db_plan, "overage_rates", None)
        overage_rates: dict[str, Decimal] = {}
        if overage_rates_raw:
            overage_rates = {k: Decimal(v) for k, v in overage_rates_raw.items()}

        metadata_raw = getattr(db_plan, "metadata_json", None)
        metadata: dict[str, Any] = metadata_raw if metadata_raw else {}

        # Handle timestamps
        created_at: datetime = getattr(db_plan, "created_at", datetime.now(UTC))
        updated_at: datetime = getattr(db_plan, "updated_at", datetime.now(UTC))

        return SubscriptionPlan(
            plan_id=plan_id,
            tenant_id=tenant_id,
            product_id=product_id,
            name=name,
            description=description,
            billing_cycle=BillingCycle(billing_cycle_value),
            price=price,
            currency=currency,
            setup_fee=setup_fee,
            trial_days=trial_days,
            included_usage=included_usage,
            overage_rates=overage_rates,
            is_active=is_active,
            metadata=metadata,
            created_at=created_at,
            updated_at=updated_at,
        )

    def _db_to_pydantic_subscription(
        self, db_subscription: BillingSubscriptionTable
    ) -> Subscription:
        """Convert database subscription to Pydantic model."""

        # Helper to ensure timezone-aware datetimes for SQLite compatibility
        def ensure_tz_aware(dt: datetime | None) -> datetime | None:
            if dt and dt.tzinfo is None:
                return dt.replace(tzinfo=UTC)
            return dt

        # Extract values from SQLAlchemy columns
        subscription_id: str = str(db_subscription.subscription_id)
        tenant_id: str = str(db_subscription.tenant_id)
        customer_id: str = str(db_subscription.customer_id)
        plan_id: str = str(db_subscription.plan_id)
        status_value: str = str(db_subscription.status)
        cancel_at_period_end: bool = bool(db_subscription.cancel_at_period_end)

        # Handle datetime columns
        current_period_start_raw: datetime | None = getattr(
            db_subscription, "current_period_start", None
        )
        current_period_end_raw: datetime | None = getattr(
            db_subscription, "current_period_end", None
        )
        trial_end_raw: datetime | None = getattr(db_subscription, "trial_end", None)
        canceled_at_raw: datetime | None = getattr(db_subscription, "canceled_at", None)
        ended_at_raw: datetime | None = getattr(db_subscription, "ended_at", None)
        created_at_raw: datetime | None = getattr(db_subscription, "created_at", None)
        updated_at_raw: datetime | None = getattr(db_subscription, "updated_at", None)

        current_period_start = ensure_tz_aware(current_period_start_raw)
        current_period_end = ensure_tz_aware(current_period_end_raw)

        if current_period_start is None:
            raise ValueError("current_period_start cannot be None")
        if current_period_end is None:
            raise ValueError("current_period_end cannot be None")

        # Handle optional fields
        custom_price: Decimal | None = getattr(db_subscription, "custom_price", None)
        usage_records_raw: dict[str, Any] | None = getattr(db_subscription, "usage_records", None)
        usage_records: dict[str, int] = {}
        if usage_records_raw:
            usage_records = {k: int(v) for k, v in usage_records_raw.items()}

        metadata_raw: dict[str, Any] | None = getattr(db_subscription, "metadata_json", None)
        metadata: dict[str, Any] = metadata_raw if metadata_raw else {}

        created_at = ensure_tz_aware(created_at_raw)
        updated_at = ensure_tz_aware(updated_at_raw)

        if created_at is None:
            created_at = datetime.now(UTC)
        if updated_at is None:
            updated_at = datetime.now(UTC)

        return Subscription(
            subscription_id=subscription_id,
            tenant_id=tenant_id,
            customer_id=customer_id,
            plan_id=plan_id,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            status=SubscriptionStatus(status_value),
            trial_end=ensure_tz_aware(trial_end_raw),
            cancel_at_period_end=cancel_at_period_end,
            canceled_at=ensure_tz_aware(canceled_at_raw),
            ended_at=ensure_tz_aware(ended_at_raw),
            custom_price=custom_price,
            usage_records=usage_records,
            metadata=metadata,
            created_at=created_at,
            updated_at=updated_at,
        )

    async def _update_subscription_status(
        self, subscription_id: str, status: SubscriptionStatus, tenant_id: str
    ) -> bool:
        """Update subscription status."""
        stmt = select(BillingSubscriptionTable).where(
            and_(
                BillingSubscriptionTable.subscription_id == subscription_id,
                BillingSubscriptionTable.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        db_subscription = result.scalar_one_or_none()

        if not db_subscription:
            return False

        # Use setattr to avoid mypy Column assignment errors
        setattr(db_subscription, "status", status.value)
        await self.db.commit()
        return True

    async def _reset_usage_for_new_period(self, subscription_id: str, tenant_id: str) -> bool:
        """Reset usage records for new billing period."""
        stmt = select(BillingSubscriptionTable).where(
            and_(
                BillingSubscriptionTable.subscription_id == subscription_id,
                BillingSubscriptionTable.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        db_subscription = result.scalar_one_or_none()

        if not db_subscription:
            return False

        # Use setattr to avoid mypy Column assignment errors
        empty_usage: dict[str, Any] = {}
        setattr(db_subscription, "usage_records", empty_usage)
        await self.db.commit()
        return True

    async def record_event(
        self,
        subscription_id: str,
        event_type: SubscriptionEventType,
        event_data: dict[str, Any],
        tenant_id: str,
        user_id: str | None = None,
    ) -> None:
        """Public method to record subscription events."""
        await self._create_event(subscription_id, event_type, event_data, tenant_id, user_id)

    async def get_usage(self, subscription_id: str, tenant_id: str) -> dict[str, int] | None:
        """Get current usage for a subscription."""
        subscription = await self.get_subscription(subscription_id, tenant_id)
        if not subscription:
            return None
        return subscription.usage_records

    async def calculate_proration_preview(
        self, subscription_id: str, new_plan_id: str, tenant_id: str
    ) -> ProrationResult | None:
        """Preview proration calculation without making changes."""
        subscription = await self.get_subscription(subscription_id, tenant_id)
        if not subscription:
            return None

        old_plan = await self.get_plan(subscription.plan_id, tenant_id)
        new_plan = await self.get_plan(new_plan_id, tenant_id)

        if not old_plan or not new_plan:
            return None

        return self._calculate_proration(subscription, old_plan, new_plan)
