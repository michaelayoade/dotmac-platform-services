"""
Comprehensive subscription service tests for high coverage.

Tests the subscription service layer with proper mocking.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from dotmac.platform.billing.subscriptions.models import (
    SubscriptionPlan,
    Subscription,
    BillingCycle,
    SubscriptionStatus,
    SubscriptionPlanCreateRequest,
    SubscriptionCreateRequest,
    SubscriptionUpdateRequest,
)
from dotmac.platform.billing.subscriptions.service import SubscriptionService
from dotmac.platform.billing.exceptions import SubscriptionNotFoundError, PlanNotFoundError


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    session.scalar = AsyncMock()
    session.scalars = AsyncMock()
    return session


@pytest.fixture
def subscription_service():
    """Subscription service instance."""
    return SubscriptionService()


@pytest.fixture
def sample_plan_data():
    """Sample subscription plan data."""
    return {
        "plan_id": "plan_123",
        "tenant_id": "tenant_123",
        "product_id": "prod_123",
        "name": "Pro Plan",
        "description": "Professional plan",
        "billing_cycle": BillingCycle.MONTHLY,
        "price": Decimal("99.99"),
        "currency": "USD",
        "setup_fee": Decimal("19.99"),
        "trial_days": 14,
        "included_usage": {"api_calls": 10000, "storage_gb": 100},
        "overage_rates": {"api_calls": Decimal("0.001"), "storage_gb": Decimal("0.50")},
        "created_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_subscription_data():
    """Sample subscription data."""
    now = datetime.now(timezone.utc)
    return {
        "subscription_id": "sub_123",
        "tenant_id": "tenant_123",
        "customer_id": "cust_123",
        "plan_id": "plan_123",
        "current_period_start": now,
        "current_period_end": now + timedelta(days=30),
        "status": SubscriptionStatus.ACTIVE,
        "trial_end": now + timedelta(days=14),
        "cancel_at_period_end": False,
        "canceled_at": None,
        "ended_at": None,
        "usage_records": {"api_calls": 5000, "storage_gb": 50},
        "metadata": {"source": "web"},
        "created_at": now,
    }


class TestSubscriptionPlanCRUD:
    """Test subscription plan CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_plan_success(self, subscription_service, mock_session, sample_plan_data):
        """Test successful plan creation."""
        # Setup
        create_request = SubscriptionPlanCreateRequest(
            product_id=sample_plan_data["product_id"],
            name=sample_plan_data["name"],
            description=sample_plan_data["description"],
            billing_cycle=sample_plan_data["billing_cycle"],
            price=sample_plan_data["price"],
            currency=sample_plan_data["currency"],
            setup_fee=sample_plan_data["setup_fee"],
            trial_days=sample_plan_data["trial_days"],
            included_usage=sample_plan_data["included_usage"],
            overage_rates=sample_plan_data["overage_rates"],
        )

        # Mock the database plan
        mock_db_plan = MagicMock()
        for key, value in sample_plan_data.items():
            setattr(mock_db_plan, key, value)

        mock_session.scalar.return_value = None  # No existing plan

        # Execute
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session', return_value=mock_session):
            with patch('uuid.uuid4', return_value='plan_123'):
                result = await subscription_service.create_plan(create_request, "tenant_123")

        # Verify
        assert result.name == sample_plan_data["name"]
        assert result.price == sample_plan_data["price"]
        assert result.billing_cycle == sample_plan_data["billing_cycle"]
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_plan_success(self, subscription_service, mock_session, sample_plan_data):
        """Test successful plan retrieval."""
        # Setup
        mock_plan = MagicMock()
        for key, value in sample_plan_data.items():
            setattr(mock_plan, key, value)

        mock_session.scalar.return_value = mock_plan

        # Execute
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session', return_value=mock_session):
            result = await subscription_service.get_plan("plan_123", "tenant_123")

        # Verify
        assert result.plan_id == "plan_123"
        assert result.name == sample_plan_data["name"]

    @pytest.mark.asyncio
    async def test_get_plan_not_found(self, subscription_service, mock_session):
        """Test plan retrieval when not found."""
        # Setup
        mock_session.scalar.return_value = None

        # Execute and verify
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session', return_value=mock_session):
            with pytest.raises(PlanNotFoundError):
                await subscription_service.get_plan("nonexistent", "tenant_123")

    @pytest.mark.asyncio
    async def test_list_plans(self, subscription_service, mock_session):
        """Test listing subscription plans."""
        # Setup mock plans
        mock_plans = [
            MagicMock(
                plan_id=f"plan_{i}",
                name=f"Plan {i}",
                billing_cycle=BillingCycle.MONTHLY if i % 2 == 0 else BillingCycle.ANNUAL,
                price=Decimal(str(50 + i * 30)),
            )
            for i in range(3)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_plans
        mock_session.execute.return_value = mock_result

        # Execute
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session', return_value=mock_session):
            result = await subscription_service.list_plans(
                tenant_id="tenant_123",
                product_id="prod_123",
            )

        # Verify
        assert len(result) == 3
        mock_session.execute.assert_called_once()


class TestSubscriptionLifecycle:
    """Test subscription lifecycle operations."""

    @pytest.mark.asyncio
    async def test_create_subscription_success(self, subscription_service, mock_session, sample_subscription_data):
        """Test successful subscription creation."""
        # Setup
        create_request = SubscriptionCreateRequest(
            customer_id=sample_subscription_data["customer_id"],
            plan_id=sample_subscription_data["plan_id"],
            start_date=sample_subscription_data["current_period_start"],
            trial_end_override=sample_subscription_data["trial_end"],
            metadata=sample_subscription_data["metadata"],
        )

        # Mock plan
        mock_plan = MagicMock(
            plan_id="plan_123",
            billing_cycle=BillingCycle.MONTHLY,
            price=Decimal("99.99"),
            trial_days=14,
        )
        mock_session.scalar.return_value = mock_plan

        # Execute
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session', return_value=mock_session):
            with patch('uuid.uuid4', return_value='sub_123'):
                result = await subscription_service.create_subscription(create_request, "tenant_123")

        # Verify
        assert result.customer_id == sample_subscription_data["customer_id"]
        assert result.plan_id == sample_subscription_data["plan_id"]
        assert result.status in [SubscriptionStatus.TRIALING, SubscriptionStatus.ACTIVE]
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_subscription(self, subscription_service, mock_session, sample_subscription_data):
        """Test subscription cancellation."""
        # Setup
        mock_subscription = MagicMock()
        for key, value in sample_subscription_data.items():
            setattr(mock_subscription, key, value)

        mock_session.scalar.return_value = mock_subscription

        # Execute
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session', return_value=mock_session):
            result = await subscription_service.cancel_subscription(
                subscription_id="sub_123",
                tenant_id="tenant_123",
                at_period_end=True,
            )

        # Verify
        if result.cancel_at_period_end:
            assert mock_subscription.cancel_at_period_end is True
            assert mock_subscription.status == SubscriptionStatus.ACTIVE
        else:
            assert mock_subscription.status == SubscriptionStatus.CANCELED
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_reactivate_subscription(self, subscription_service, mock_session):
        """Test subscription reactivation."""
        # Setup
        mock_subscription = MagicMock(
            subscription_id="sub_123",
            status=SubscriptionStatus.CANCELED,
            cancel_at_period_end=True,
            ended_at=None,
        )
        mock_session.scalar.return_value = mock_subscription

        # Execute
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session', return_value=mock_session):
            result = await subscription_service.reactivate_subscription(
                subscription_id="sub_123",
                tenant_id="tenant_123",
            )

        # Verify
        assert mock_subscription.cancel_at_period_end is False
        assert mock_subscription.status == SubscriptionStatus.ACTIVE
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_pause_subscription(self, subscription_service, mock_session):
        """Test subscription pausing."""
        # Setup
        mock_subscription = MagicMock(
            subscription_id="sub_123",
            status=SubscriptionStatus.ACTIVE,
        )
        mock_session.scalar.return_value = mock_subscription

        # Execute
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session', return_value=mock_session):
            result = await subscription_service.pause_subscription(
                subscription_id="sub_123",
                tenant_id="tenant_123",
            )

        # Verify
        assert mock_subscription.status == SubscriptionStatus.PAUSED
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_subscription(self, subscription_service, mock_session):
        """Test subscription resuming."""
        # Setup
        mock_subscription = MagicMock(
            subscription_id="sub_123",
            status=SubscriptionStatus.PAUSED,
        )
        mock_session.scalar.return_value = mock_subscription

        # Execute
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session', return_value=mock_session):
            result = await subscription_service.resume_subscription(
                subscription_id="sub_123",
                tenant_id="tenant_123",
            )

        # Verify
        assert mock_subscription.status == SubscriptionStatus.ACTIVE
        mock_session.commit.assert_called_once()


class TestSubscriptionPlanChanges:
    """Test subscription plan change operations."""

    @pytest.mark.asyncio
    async def test_change_plan_upgrade(self, subscription_service, mock_session):
        """Test upgrading subscription plan."""
        # Setup
        old_plan = MagicMock(
            plan_id="plan_basic",
            price=Decimal("29.99"),
            billing_cycle=BillingCycle.MONTHLY,
        )

        new_plan = MagicMock(
            plan_id="plan_pro",
            price=Decimal("99.99"),
            billing_cycle=BillingCycle.MONTHLY,
        )

        mock_subscription = MagicMock(
            subscription_id="sub_123",
            plan_id="plan_basic",
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
        )

        # Mock the database calls
        mock_session.scalar.side_effect = [mock_subscription, new_plan]

        # Execute
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session', return_value=mock_session):
            result = await subscription_service.change_plan(
                subscription_id="sub_123",
                new_plan_id="plan_pro",
                tenant_id="tenant_123",
                immediate=True,
            )

        # Verify
        assert mock_subscription.plan_id == "plan_pro"
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_proration(self, subscription_service):
        """Test proration calculation for plan changes."""
        # Setup
        old_price = Decimal("30.00")
        new_price = Decimal("60.00")
        days_remaining = 15
        days_in_period = 30

        # Execute
        proration = subscription_service._calculate_proration(
            old_price=old_price,
            new_price=new_price,
            days_remaining=days_remaining,
            days_in_period=days_in_period,
        )

        # Verify
        expected_proration = Decimal("15.00")  # (60-30) * 15/30
        assert proration == expected_proration


class TestSubscriptionUsageTracking:
    """Test subscription usage tracking."""

    @pytest.mark.asyncio
    async def test_record_usage(self, subscription_service, mock_session):
        """Test recording subscription usage."""
        # Setup
        mock_subscription = MagicMock(
            subscription_id="sub_123",
            usage_records={"api_calls": 1000, "storage_gb": 10},
        )
        mock_session.scalar.return_value = mock_subscription

        # Execute
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session', return_value=mock_session):
            await subscription_service.record_usage(
                subscription_id="sub_123",
                tenant_id="tenant_123",
                usage_type="api_calls",
                quantity=500,
            )

        # Verify
        assert mock_subscription.usage_records["api_calls"] == 1500
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_overage(self, subscription_service, mock_session):
        """Test overage calculation."""
        # Setup
        mock_subscription = MagicMock(
            subscription_id="sub_123",
            usage_records={"api_calls": 15000, "storage_gb": 150},
        )

        mock_plan = MagicMock(
            included_usage={"api_calls": 10000, "storage_gb": 100},
            overage_rates={"api_calls": Decimal("0.001"), "storage_gb": Decimal("0.50")},
        )

        mock_session.scalar.side_effect = [mock_subscription, mock_plan]

        # Execute
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session', return_value=mock_session):
            overage = await subscription_service.calculate_overage(
                subscription_id="sub_123",
                tenant_id="tenant_123",
            )

        # Verify
        assert overage["api_calls"]["overage_units"] == 5000
        assert overage["api_calls"]["overage_charge"] == Decimal("5.00")
        assert overage["storage_gb"]["overage_units"] == 50
        assert overage["storage_gb"]["overage_charge"] == Decimal("25.00")


class TestSubscriptionQueries:
    """Test subscription query operations."""

    @pytest.mark.asyncio
    async def test_get_active_subscriptions(self, subscription_service, mock_session):
        """Test getting active subscriptions."""
        # Setup
        mock_subscriptions = [
            MagicMock(
                subscription_id=f"sub_{i}",
                status=SubscriptionStatus.ACTIVE,
                customer_id=f"cust_{i}",
            )
            for i in range(5)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_subscriptions
        mock_session.execute.return_value = mock_result

        # Execute
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session', return_value=mock_session):
            result = await subscription_service.get_active_subscriptions(
                tenant_id="tenant_123",
            )

        # Verify
        assert len(result) == 5
        assert all(s.status == SubscriptionStatus.ACTIVE for s in result)

    @pytest.mark.asyncio
    async def test_get_subscriptions_by_customer(self, subscription_service, mock_session):
        """Test getting subscriptions by customer."""
        # Setup
        customer_subscriptions = [
            MagicMock(
                subscription_id=f"sub_{i}",
                customer_id="cust_123",
                status=SubscriptionStatus.ACTIVE if i % 2 == 0 else SubscriptionStatus.CANCELED,
            )
            for i in range(3)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = customer_subscriptions
        mock_session.execute.return_value = mock_result

        # Execute
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session', return_value=mock_session):
            result = await subscription_service.get_customer_subscriptions(
                customer_id="cust_123",
                tenant_id="tenant_123",
            )

        # Verify
        assert len(result) == 3
        assert all(s.customer_id == "cust_123" for s in result)

    @pytest.mark.asyncio
    async def test_get_expiring_trials(self, subscription_service, mock_session):
        """Test getting expiring trial subscriptions."""
        # Setup
        now = datetime.now(timezone.utc)
        expiring_trials = [
            MagicMock(
                subscription_id=f"sub_{i}",
                status=SubscriptionStatus.TRIALING,
                trial_end=now + timedelta(days=i),
            )
            for i in range(1, 4)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = expiring_trials
        mock_session.execute.return_value = mock_result

        # Execute
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session', return_value=mock_session):
            result = await subscription_service.get_expiring_trials(
                tenant_id="tenant_123",
                days_ahead=7,
            )

        # Verify
        assert len(result) == 3
        assert all(s.status == SubscriptionStatus.TRIALING for s in result)


class TestSubscriptionMetrics:
    """Test subscription metrics and analytics."""

    @pytest.mark.asyncio
    async def test_get_subscription_metrics(self, subscription_service, mock_session):
        """Test getting subscription metrics."""
        # Setup
        mock_metrics = {
            "total_subscriptions": 100,
            "active_subscriptions": 80,
            "trial_subscriptions": 10,
            "canceled_subscriptions": 10,
            "mrr": Decimal("7999.20"),  # Monthly Recurring Revenue
            "arr": Decimal("95990.40"),  # Annual Recurring Revenue
        }

        mock_result = MagicMock()
        mock_result.one.return_value = mock_metrics
        mock_session.execute.return_value = mock_result

        # Execute
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session', return_value=mock_session):
            result = await subscription_service.get_subscription_metrics(
                tenant_id="tenant_123",
            )

        # Verify
        assert result["total_subscriptions"] == 100
        assert result["active_subscriptions"] == 80
        assert result["mrr"] == Decimal("7999.20")

    @pytest.mark.asyncio
    async def test_get_churn_rate(self, subscription_service, mock_session):
        """Test calculating churn rate."""
        # Setup
        mock_churn_data = {
            "start_active": 100,
            "end_active": 95,
            "canceled": 8,
            "new": 3,
        }

        mock_result = MagicMock()
        mock_result.one.return_value = mock_churn_data
        mock_session.execute.return_value = mock_result

        # Execute
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session', return_value=mock_session):
            churn_rate = await subscription_service.calculate_churn_rate(
                tenant_id="tenant_123",
                start_date=datetime.now(timezone.utc) - timedelta(days=30),
                end_date=datetime.now(timezone.utc),
            )

        # Verify
        # Churn rate = (canceled / start_active) * 100
        expected_churn = Decimal("8.0")  # 8%
        assert churn_rate == expected_churn


if __name__ == "__main__":
    pytest.main([__file__, "-v"])