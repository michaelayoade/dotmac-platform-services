"""
Subscription management service.

Handles complete subscription lifecycle with simple, clear operations.
"""

import structlog
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import uuid4

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.billing.subscriptions.models import (
    SubscriptionPlan,
    Subscription,
    SubscriptionEvent,
    SubscriptionPlanCreateRequest,
    SubscriptionCreateRequest,
    SubscriptionUpdateRequest,
    SubscriptionPlanChangeRequest,
    UsageRecordRequest,
    BillingCycle,
    SubscriptionStatus,
    SubscriptionEventType,
    ProrationBehavior,
    ProrationResult,
)
from dotmac.platform.billing.models import (
    BillingSubscriptionPlanTable,
    BillingSubscriptionTable,
    BillingSubscriptionEventTable,
)
from dotmac.platform.billing.exceptions import (
    SubscriptionError,
    SubscriptionNotFoundError,
    PlanNotFoundError,
)
from dotmac.platform.settings import settings

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

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    # ========================================
    # Subscription Plan Management
    # ========================================

    async def create_plan(
        self,
        plan_data: SubscriptionPlanCreateRequest,
        tenant_id: str
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
                BillingSubscriptionPlanTable.tenant_id == tenant_id
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
        product_id: Optional[str] = None,
        billing_cycle: Optional[BillingCycle] = None,
        active_only: bool = True
    ) -> List[SubscriptionPlan]:
        """List subscription plans with filtering."""

        stmt = select(BillingSubscriptionPlanTable).where(
            BillingSubscriptionPlanTable.tenant_id == tenant_id
        )

        if product_id:
            stmt = stmt.where(BillingSubscriptionPlanTable.product_id == product_id)

        if billing_cycle:
            stmt = stmt.where(BillingSubscriptionPlanTable.billing_cycle == billing_cycle.value)

        if active_only:
            stmt = stmt.where(BillingSubscriptionPlanTable.is_active == True)

        stmt = stmt.order_by(BillingSubscriptionPlanTable.name)

        result = await self.db.execute(stmt)
        db_plans = result.scalars().all()

        return [self._db_to_pydantic_plan(db_plan) for db_plan in db_plans]

    # ========================================
    # Subscription Management
    # ========================================

    async def create_subscription(
        self,
        subscription_data: SubscriptionCreateRequest,
        tenant_id: str
    ) -> Subscription:
        """Create new subscription with proper lifecycle setup."""

        # Get the plan
        plan = await self.get_plan(subscription_data.plan_id, tenant_id)

        # Calculate subscription periods
        start_date = subscription_data.start_date or datetime.now(timezone.utc)
        period_start = start_date
        period_end = self._calculate_period_end(period_start, plan.billing_cycle)

        # Handle trial period
        trial_end = None
        status = SubscriptionStatus.ACTIVE

        if subscription_data.trial_end_override:
            trial_end = subscription_data.trial_end_override
            status = SubscriptionStatus.TRIALING
        elif plan.has_trial():
            trial_end = start_date + timedelta(days=plan.trial_days)
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
                "custom_price": str(subscription_data.custom_price) if subscription_data.custom_price else None,
            },
            tenant_id
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
                BillingSubscriptionTable.tenant_id == tenant_id
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
        customer_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        status: Optional[SubscriptionStatus] = None,
        page: int = 1,
        limit: int = 50
    ) -> List[Subscription]:
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
        self,
        subscription_id: str,
        updates: SubscriptionUpdateRequest,
        tenant_id: str
    ) -> Subscription:
        """Update subscription details."""

        # Get existing subscription
        stmt = select(BillingSubscriptionTable).where(
            and_(
                BillingSubscriptionTable.subscription_id == subscription_id,
                BillingSubscriptionTable.tenant_id == tenant_id
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
                setattr(db_subscription, "metadata_json", value)
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
        user_id: Optional[str] = None
    ) -> tuple[Subscription, Optional[ProrationResult]]:
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
        effective_date = change_request.effective_date or datetime.now(timezone.utc)

        stmt = select(BillingSubscriptionTable).where(
            and_(
                BillingSubscriptionTable.subscription_id == subscription_id,
                BillingSubscriptionTable.tenant_id == tenant_id
            )
        )
        result = await self.db.execute(stmt)
        db_subscription = result.scalar_one_or_none()

        db_subscription.plan_id = change_request.new_plan_id

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
                "proration_amount": str(proration_result.proration_amount) if proration_result else "0",
                "effective_date": effective_date.isoformat(),
            },
            tenant_id,
            user_id
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
        user_id: Optional[str] = None
    ) -> Subscription:
        """Cancel subscription (immediate or at period end)."""

        subscription = await self.get_subscription(subscription_id, tenant_id)

        if not subscription.is_active():
            raise SubscriptionError("Subscription is not active")

        now = datetime.now(timezone.utc)
        immediate = not at_period_end

        stmt = select(BillingSubscriptionTable).where(
            and_(
                BillingSubscriptionTable.subscription_id == subscription_id,
                BillingSubscriptionTable.tenant_id == tenant_id
            )
        )
        result = await self.db.execute(stmt)
        db_subscription = result.scalar_one_or_none()

        if immediate:
            # End subscription immediately
            db_subscription.status = SubscriptionStatus.ENDED.value
            db_subscription.ended_at = now
            db_subscription.canceled_at = now
        else:
            # Cancel at period end (default behavior)
            db_subscription.cancel_at_period_end = True
            db_subscription.canceled_at = now
            db_subscription.status = SubscriptionStatus.CANCELED.value

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
            user_id
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
        self,
        subscription_id: str,
        tenant_id: str,
        user_id: Optional[str] = None
    ) -> Subscription:
        """Reactivate a canceled subscription (if still in current period)."""

        subscription = await self.get_subscription(subscription_id, tenant_id)

        if subscription.status != SubscriptionStatus.CANCELED:
            raise SubscriptionError("Only canceled subscriptions can be reactivated")

        if datetime.now(timezone.utc) > subscription.current_period_end:
            raise SubscriptionError("Cannot reactivate subscription after period end")

        stmt = select(BillingSubscriptionTable).where(
            and_(
                BillingSubscriptionTable.subscription_id == subscription_id,
                BillingSubscriptionTable.tenant_id == tenant_id
            )
        )
        result = await self.db.execute(stmt)
        db_subscription = result.scalar_one_or_none()

        db_subscription.status = SubscriptionStatus.ACTIVE.value
        db_subscription.cancel_at_period_end = False
        db_subscription.canceled_at = None

        await self.db.commit()
        await self.db.refresh(db_subscription)

        updated_subscription = self._db_to_pydantic_subscription(db_subscription)

        # Create reactivation event
        await self._create_event(
            subscription_id,
            SubscriptionEventType.RESUMED,
            {"reactivated_at": datetime.now(timezone.utc).isoformat()},
            tenant_id,
            user_id
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
        self,
        usage_request: UsageRecordRequest,
        tenant_id: str
    ) -> Dict[str, int]:
        """Record usage for a subscription."""

        subscription = await self.get_subscription(usage_request.subscription_id, tenant_id)

        if not subscription.is_active():
            raise SubscriptionError("Cannot record usage for inactive subscription")

        usage_timestamp = usage_request.timestamp or datetime.now(timezone.utc)

        # Verify usage is within current period
        if not (subscription.current_period_start <= usage_timestamp <= subscription.current_period_end):
            raise SubscriptionError("Usage timestamp is outside current billing period")

            stmt = select(BillingSubscriptionTable).where(
                and_(
                    BillingSubscriptionTable.subscription_id == usage_request.subscription_id,
                    BillingSubscriptionTable.tenant_id == tenant_id
                )
            )
            result = await self.db.execute(stmt)
            db_subscription = result.scalar_one_or_none()

            # Update usage records
            current_usage = db_subscription.usage_records or {}
            current_usage[usage_request.usage_type] = current_usage.get(usage_request.usage_type, 0) + usage_request.quantity

            db_subscription.usage_records = current_usage

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

    async def get_usage_for_period(
        self,
        subscription_id: str,
        tenant_id: str
    ) -> Dict[str, int]:
        """Get current period usage for subscription."""

        subscription = await self.get_subscription(subscription_id, tenant_id)
        return subscription.usage_records

    # ========================================
    # Renewal Processing (for background jobs)
    # ========================================

    async def get_subscriptions_due_for_renewal(
        self,
        tenant_id: str,
        look_ahead_days: int = 1
    ) -> List[Subscription]:
        """Get subscriptions that need renewal within the specified timeframe."""

        cutoff_date = datetime.now(timezone.utc) + timedelta(days=look_ahead_days)

        stmt = select(BillingSubscriptionTable).where(
            and_(
                BillingSubscriptionTable.tenant_id == tenant_id,
                BillingSubscriptionTable.status == SubscriptionStatus.ACTIVE.value,
                BillingSubscriptionTable.current_period_end <= cutoff_date
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
        self,
        subscription: Subscription,
        old_plan: SubscriptionPlan,
        new_plan: SubscriptionPlan
    ) -> ProrationResult:
        """Calculate simple proration for plan changes."""

        now = datetime.now(timezone.utc)
        total_period_seconds = (subscription.current_period_end - subscription.current_period_start).total_seconds()
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
        event_data: Dict[str, Any],
        tenant_id: str,
        user_id: Optional[str] = None
    ):
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
        overage_rates = {}
        if db_plan.overage_rates:
            overage_rates = {k: Decimal(v) for k, v in db_plan.overage_rates.items()}

        return SubscriptionPlan(
            plan_id=db_plan.plan_id,
            tenant_id=db_plan.tenant_id,
            product_id=db_plan.product_id,
            name=db_plan.name,
            description=db_plan.description,
            billing_cycle=BillingCycle(db_plan.billing_cycle),
            price=db_plan.price,
            currency=db_plan.currency,
            setup_fee=db_plan.setup_fee,
            trial_days=db_plan.trial_days,
            included_usage=db_plan.included_usage or {},
            overage_rates=overage_rates,
            is_active=db_plan.is_active,
            metadata=db_plan.metadata_json or {},
            created_at=db_plan.created_at,
            updated_at=db_plan.updated_at,
        )

    def _db_to_pydantic_subscription(self, db_subscription: BillingSubscriptionTable) -> Subscription:
        """Convert database subscription to Pydantic model."""
        return Subscription(
            subscription_id=db_subscription.subscription_id,
            tenant_id=db_subscription.tenant_id,
            customer_id=db_subscription.customer_id,
            plan_id=db_subscription.plan_id,
            current_period_start=db_subscription.current_period_start,
            current_period_end=db_subscription.current_period_end,
            status=SubscriptionStatus(db_subscription.status),
            trial_end=db_subscription.trial_end,
            cancel_at_period_end=db_subscription.cancel_at_period_end,
            canceled_at=db_subscription.canceled_at,
            ended_at=db_subscription.ended_at,
            custom_price=db_subscription.custom_price,
            usage_records=db_subscription.usage_records or {},
            metadata=db_subscription.metadata_json or {},
            created_at=db_subscription.created_at,
            updated_at=db_subscription.updated_at,
        )

    async def _update_subscription_status(
        self,
        subscription_id: str,
        status: SubscriptionStatus,
        tenant_id: str
    ) -> bool:
        """Update subscription status."""
        stmt = select(BillingSubscriptionTable).where(
                and_(
                    BillingSubscriptionTable.subscription_id == subscription_id,
                    BillingSubscriptionTable.tenant_id == tenant_id
                )
            )
        result = await self.db.execute(stmt)
        db_subscription = result.scalar_one_or_none()

        if not db_subscription:
            return False

        db_subscription.status = status.value
        await self.db.commit()
        return True

    async def _reset_usage_for_new_period(
        self,
        subscription_id: str,
        tenant_id: str
    ) -> bool:
        """Reset usage records for new billing period."""
        stmt = select(BillingSubscriptionTable).where(
            and_(
                BillingSubscriptionTable.subscription_id == subscription_id,
                BillingSubscriptionTable.tenant_id == tenant_id
            )
        )
        result = await self.db.execute(stmt)
        db_subscription = result.scalar_one_or_none()

        if not db_subscription:
            return False

        db_subscription.usage_records = {}
        await self.db.commit()
        return True

    async def record_event(
        self,
        subscription_id: str,
        event_type: SubscriptionEventType,
        event_data: Dict[str, Any],
        tenant_id: str,
        user_id: Optional[str] = None
    ) -> None:
        """Public method to record subscription events."""
        await self._create_event(subscription_id, event_type, event_data, tenant_id, user_id)

    async def get_usage(
        self,
        subscription_id: str,
        tenant_id: str
    ) -> Optional[Dict[str, int]]:
        """Get current usage for a subscription."""
        subscription = await self.get_subscription(subscription_id, tenant_id)
        if not subscription:
            return None
        return subscription.usage_records

    async def calculate_proration_preview(
        self,
        subscription_id: str,
        new_plan_id: str,
        tenant_id: str
    ) -> Optional[ProrationResult]:
        """Preview proration calculation without making changes."""
        subscription = await self.get_subscription(subscription_id, tenant_id)
        if not subscription:
            return None

        old_plan = await self.get_plan(subscription.plan_id, tenant_id)
        new_plan = await self.get_plan(new_plan_id, tenant_id)

        if not old_plan or not new_plan:
            return None

        return self._calculate_proration(subscription, old_plan, new_plan)