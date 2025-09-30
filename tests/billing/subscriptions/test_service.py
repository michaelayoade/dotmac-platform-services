"""
Tests for billing subscription service.

Covers subscription and plan management operations.
"""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.exc import IntegrityError

from dotmac.platform.billing.subscriptions.service import SubscriptionService
from dotmac.platform.billing.subscriptions.models import (
    SubscriptionPlan,
    Subscription,
    BillingCycle,
    SubscriptionStatus,
    SubscriptionEventType,
    ProrationBehavior,
    SubscriptionPlanCreateRequest,
    SubscriptionCreateRequest,
    SubscriptionUpdateRequest,
    SubscriptionPlanChangeRequest,
    UsageRecordRequest,
    ProrationResult,
)
from dotmac.platform.billing.exceptions import (
    SubscriptionError,
    SubscriptionNotFoundError,
    PlanNotFoundError,
)


class TestSubscriptionServicePlans:
    """Test subscription plan management in service."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return SubscriptionService()

    @pytest.mark.asyncio
    async def test_create_plan_success(
        self,
        service,
        plan_create_request,
        tenant_id
    ):
        """Test successful plan creation."""
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            # Mock no existing plan
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session_instance.execute.return_value = mock_result
            mock_session_instance.commit = AsyncMock()
            mock_session_instance.refresh = AsyncMock()

            with patch('dotmac.platform.billing.subscriptions.service.generate_plan_id') as mock_gen_id:
                mock_gen_id.return_value = "plan_test123"

                result = await service.create_plan(plan_create_request, tenant_id)

                assert result.name == plan_create_request.name
                assert result.billing_cycle == plan_create_request.billing_cycle
                assert result.price == plan_create_request.price
                assert result.tenant_id == tenant_id

                mock_session_instance.add.assert_called_once()
                mock_session_instance.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_plan_duplicate_name(
        self,
        service,
        plan_create_request,
        tenant_id
    ):
        """Test plan creation fails with duplicate name."""
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            # Mock existing plan found
            existing_plan = MagicMock()
            existing_plan.name = plan_create_request.name
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = existing_plan
            mock_session_instance.execute.return_value = mock_result

            with pytest.raises(SubscriptionError) as exc_info:
                await service.create_plan(plan_create_request, tenant_id)

            assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_plan_success(self, service, tenant_id):
        """Test successful plan retrieval."""
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            mock_plan = MagicMock()
            mock_plan.plan_id = "plan_123"
            mock_plan.tenant_id = tenant_id
            mock_plan.product_id = "prod_123"
            mock_plan.name = "Test Plan"
            mock_plan.billing_cycle = "monthly"
            mock_plan.price = Decimal("29.99")
            mock_plan.currency = "USD"
            mock_plan.setup_fee = None
            mock_plan.trial_days = None
            mock_plan.included_usage = {}
            mock_plan.overage_rates = {}
            mock_plan.is_active = True
            mock_plan.metadata_json = {}
            mock_plan.created_at = datetime.now(timezone.utc)
            mock_plan.updated_at = None

            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_plan
            mock_session_instance.execute.return_value = mock_result

            result = await service.get_plan("plan_123", tenant_id)

            assert result is not None
            assert result.plan_id == "plan_123"
            assert result.name == "Test Plan"

    @pytest.mark.asyncio
    async def test_get_plan_not_found(self, service, tenant_id):
        """Test plan retrieval when plan doesn't exist."""
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session_instance.execute.return_value = mock_result

            result = await service.get_plan("nonexistent", tenant_id)
            assert result is None

    @pytest.mark.asyncio
    async def test_list_plans(self, service, tenant_id):
        """Test listing plans with filters."""
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            mock_plans = [
                MagicMock(
                    plan_id="plan_1",
                    tenant_id=tenant_id,
                    product_id="prod_1",
                    name="Plan 1",
                    billing_cycle="monthly",
                    price=Decimal("29.99"),
                    currency="USD",
                    setup_fee=None,
                    trial_days=None,
                    included_usage={},
                    overage_rates={},
                    is_active=True,
                    metadata_json={},
                    created_at=datetime.now(timezone.utc),
                    updated_at=None,
                ),
                MagicMock(
                    plan_id="plan_2",
                    tenant_id=tenant_id,
                    product_id="prod_2",
                    name="Plan 2",
                    billing_cycle="annual",
                    price=Decimal("299.99"),
                    currency="USD",
                    setup_fee=None,
                    trial_days=14,
                    included_usage={},
                    overage_rates={},
                    is_active=True,
                    metadata_json={},
                    created_at=datetime.now(timezone.utc),
                    updated_at=None,
                ),
            ]

            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = mock_plans
            mock_session_instance.execute.return_value = mock_result

            result = await service.list_plans(tenant_id)
            assert len(result) == 2
            assert result[0].plan_id == "plan_1"
            assert result[1].plan_id == "plan_2"

    @pytest.mark.asyncio
    async def test_update_plan_success(self, service, tenant_id):
        """Test successful plan update."""
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            mock_plan = MagicMock()
            mock_plan.plan_id = "plan_123"
            mock_plan.name = "Old Name"
            mock_plan.price = Decimal("29.99")

            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_plan
            mock_session_instance.execute.return_value = mock_result
            mock_session_instance.commit = AsyncMock()
            mock_session_instance.refresh = AsyncMock()

            update_data = {"name": "Updated Name", "price": Decimal("39.99")}

            result = await service.update_plan("plan_123", update_data, tenant_id)

            assert result is not None
            mock_session_instance.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_plan_success(self, service, tenant_id):
        """Test successful plan deactivation."""
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            mock_plan = MagicMock()
            mock_plan.is_active = True

            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_plan
            mock_session_instance.execute.return_value = mock_result
            mock_session_instance.commit = AsyncMock()

            result = await service.deactivate_plan("plan_123", tenant_id)

            assert result is True
            assert mock_plan.is_active is False
            mock_session_instance.commit.assert_called_once()


class TestSubscriptionServiceSubscriptions:
    """Test subscription management in service."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return SubscriptionService()

    @pytest.mark.asyncio
    async def test_create_subscription_success(
        self,
        service,
        subscription_create_request,
        tenant_id,
        sample_subscription_plan
    ):
        """Test successful subscription creation."""
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            # Mock plan retrieval
            with patch.object(service, 'get_plan') as mock_get_plan:
                mock_get_plan.return_value = sample_subscription_plan

                mock_session_instance.commit = AsyncMock()
                mock_session_instance.refresh = AsyncMock()

                with patch('dotmac.platform.billing.subscriptions.service.generate_subscription_id') as mock_gen_id:
                    mock_gen_id.return_value = "sub_test123"

                    result = await service.create_subscription(subscription_create_request, tenant_id)

                    assert result.customer_id == subscription_create_request.customer_id
                    assert result.plan_id == subscription_create_request.plan_id
                    assert result.tenant_id == tenant_id

                    mock_session_instance.add.assert_called_once()
                    mock_session_instance.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_subscription_plan_not_found(
        self,
        service,
        subscription_create_request,
        tenant_id
    ):
        """Test subscription creation fails when plan not found."""
        with patch.object(service, 'get_plan') as mock_get_plan:
            mock_get_plan.return_value = None

            with pytest.raises(PlanNotFoundError):
                await service.create_subscription(subscription_create_request, tenant_id)

    @pytest.mark.asyncio
    async def test_get_subscription_success(self, service, tenant_id):
        """Test successful subscription retrieval."""
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            now = datetime.now(timezone.utc)
            mock_subscription = MagicMock()
            mock_subscription.subscription_id = "sub_123"
            mock_subscription.tenant_id = tenant_id
            mock_subscription.customer_id = "customer-456"
            mock_subscription.plan_id = "plan_123"
            mock_subscription.current_period_start = now
            mock_subscription.current_period_end = now + timedelta(days=30)
            mock_subscription.status = "active"
            mock_subscription.trial_end = None
            mock_subscription.cancel_at_period_end = False
            mock_subscription.canceled_at = None
            mock_subscription.ended_at = None
            mock_subscription.custom_price = None
            mock_subscription.usage_records = {}
            mock_subscription.metadata_json = {}
            mock_subscription.created_at = now
            mock_subscription.updated_at = None

            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_subscription
            mock_session_instance.execute.return_value = mock_result

            result = await service.get_subscription("sub_123", tenant_id)

            assert result is not None
            assert result.subscription_id == "sub_123"
            assert result.customer_id == "customer-456"

    @pytest.mark.asyncio
    async def test_list_subscriptions(self, service, tenant_id):
        """Test listing subscriptions with filters."""
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            now = datetime.now(timezone.utc)
            mock_subscriptions = [
                MagicMock(
                    subscription_id="sub_1",
                    tenant_id=tenant_id,
                    customer_id="customer-1",
                    plan_id="plan_1",
                    current_period_start=now,
                    current_period_end=now + timedelta(days=30),
                    status="active",
                    trial_end=None,
                    cancel_at_period_end=False,
                    canceled_at=None,
                    ended_at=None,
                    custom_price=None,
                    usage_records={},
                    metadata_json={},
                    created_at=now,
                    updated_at=None,
                ),
            ]

            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = mock_subscriptions
            mock_session_instance.execute.return_value = mock_result

            result = await service.list_subscriptions(tenant_id)
            assert len(result) == 1
            assert result[0].subscription_id == "sub_1"

    @pytest.mark.asyncio
    async def test_update_subscription_success(self, service, tenant_id):
        """Test successful subscription update."""
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            now = datetime.now(timezone.utc)
            mock_subscription = MagicMock()
            mock_subscription.subscription_id = "sub_123"
            mock_subscription.custom_price = None

            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_subscription
            mock_session_instance.execute.return_value = mock_result
            mock_session_instance.commit = AsyncMock()
            mock_session_instance.refresh = AsyncMock()

            update_request = SubscriptionUpdateRequest(
                custom_price=Decimal("49.99"),
                metadata={"updated": True},
            )

            result = await service.update_subscription("sub_123", update_request, tenant_id)

            assert result is not None
            mock_session_instance.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_subscription_not_found(self, service, tenant_id):
        """Test subscription update when subscription doesn't exist."""
        with patch('dotmac.platform.billing.subscriptions.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session_instance.execute.return_value = mock_result

            update_request = SubscriptionUpdateRequest(custom_price=Decimal("49.99"))

            with pytest.raises(SubscriptionNotFoundError):
                await service.update_subscription("nonexistent", update_request, tenant_id)


class TestSubscriptionServiceLifecycle:
    """Test subscription lifecycle operations."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return SubscriptionService()

    @pytest.mark.asyncio
    async def test_cancel_subscription_immediate(self, service, tenant_id, sample_subscription):
        """Test immediate subscription cancellation."""
        with patch.object(service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = sample_subscription

            with patch('dotmac.platform.billing.subscriptions.service.get_async_session') as mock_session:
                mock_session_instance = AsyncMock()
                mock_session.return_value.__aenter__.return_value = mock_session_instance

                mock_subscription = MagicMock()
                mock_result = AsyncMock()
                mock_result.scalar_one_or_none.return_value = mock_subscription
                mock_session_instance.execute.return_value = mock_result
                mock_session_instance.commit = AsyncMock()
                mock_session_instance.refresh = AsyncMock()

                with patch.object(service, '_create_event') as mock_create_event:
                    result = await service.cancel_subscription("sub_123", immediate=True, tenant_id=tenant_id)

                    assert result is not None
                    assert mock_subscription.status == SubscriptionStatus.ENDED.value
                    mock_create_event.assert_called_once()
                    mock_session_instance.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_subscription_at_period_end(self, service, tenant_id, sample_subscription):
        """Test subscription cancellation at period end."""
        with patch.object(service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = sample_subscription

            with patch('dotmac.platform.billing.subscriptions.service.get_async_session') as mock_session:
                mock_session_instance = AsyncMock()
                mock_session.return_value.__aenter__.return_value = mock_session_instance

                mock_subscription = MagicMock()
                mock_result = AsyncMock()
                mock_result.scalar_one_or_none.return_value = mock_subscription
                mock_session_instance.execute.return_value = mock_result
                mock_session_instance.commit = AsyncMock()
                mock_session_instance.refresh = AsyncMock()

                with patch.object(service, '_create_event') as mock_create_event:
                    result = await service.cancel_subscription("sub_123", immediate=False, tenant_id=tenant_id)

                    assert result is not None
                    assert mock_subscription.cancel_at_period_end is True
                    assert mock_subscription.status == SubscriptionStatus.CANCELED.value
                    mock_create_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_reactivate_subscription_success(self, service, tenant_id):
        """Test successful subscription reactivation."""
        # Create canceled subscription
        now = datetime.now(timezone.utc)
        canceled_subscription = Subscription(
            subscription_id="sub_123",
            tenant_id=tenant_id,
            customer_id="customer-456",
            plan_id="plan_123",
            current_period_start=now,
            current_period_end=now + timedelta(days=10),  # Still in period
            status=SubscriptionStatus.CANCELED,
            created_at=now,
        )

        with patch.object(service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = canceled_subscription

            with patch('dotmac.platform.billing.subscriptions.service.get_async_session') as mock_session:
                mock_session_instance = AsyncMock()
                mock_session.return_value.__aenter__.return_value = mock_session_instance

                mock_subscription = MagicMock()
                mock_result = AsyncMock()
                mock_result.scalar_one_or_none.return_value = mock_subscription
                mock_session_instance.execute.return_value = mock_result
                mock_session_instance.commit = AsyncMock()
                mock_session_instance.refresh = AsyncMock()

                with patch.object(service, '_create_event') as mock_create_event:
                    result = await service.reactivate_subscription("sub_123", tenant_id)

                    assert result is not None
                    assert mock_subscription.status == SubscriptionStatus.ACTIVE.value
                    assert mock_subscription.cancel_at_period_end is False
                    mock_create_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_reactivate_subscription_after_period_end(self, service, tenant_id):
        """Test subscription reactivation fails after period end."""
        # Create canceled subscription with ended period
        now = datetime.now(timezone.utc)
        ended_subscription = Subscription(
            subscription_id="sub_123",
            tenant_id=tenant_id,
            customer_id="customer-456",
            plan_id="plan_123",
            current_period_start=now - timedelta(days=30),
            current_period_end=now - timedelta(days=1),  # Period already ended
            status=SubscriptionStatus.CANCELED,
            created_at=now - timedelta(days=30),
        )

        with patch.object(service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = ended_subscription

            with pytest.raises(SubscriptionError) as exc_info:
                await service.reactivate_subscription("sub_123", tenant_id)

            assert "Cannot reactivate subscription after period end" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_change_plan_success(self, service, tenant_id, sample_subscription_plan):
        """Test successful plan change."""
        now = datetime.now(timezone.utc)
        subscription = Subscription(
            subscription_id="sub_123",
            tenant_id=tenant_id,
            customer_id="customer-456",
            plan_id="plan_old",
            current_period_start=now,
            current_period_end=now + timedelta(days=15),  # 15 days remaining
            status=SubscriptionStatus.ACTIVE,
            created_at=now,
        )

        old_plan = SubscriptionPlan(
            plan_id="plan_old",
            tenant_id=tenant_id,
            product_id="prod_123",
            name="Old Plan",
            billing_cycle=BillingCycle.MONTHLY,
            price=Decimal("29.99"),
            is_active=True,
            created_at=now,
        )

        new_plan = SubscriptionPlan(
            plan_id="plan_new",
            tenant_id=tenant_id,
            product_id="prod_123",
            name="New Plan",
            billing_cycle=BillingCycle.MONTHLY,
            price=Decimal("49.99"),
            is_active=True,
            created_at=now,
        )

        change_request = SubscriptionPlanChangeRequest(
            new_plan_id="plan_new",
            proration_behavior=ProrationBehavior.CREATE_PRORATIONS,
        )

        with patch.object(service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = subscription

            with patch.object(service, 'get_plan') as mock_get_plan:
                mock_get_plan.side_effect = [old_plan, new_plan]

                with patch('dotmac.platform.billing.subscriptions.service.get_async_session') as mock_session:
                    mock_session_instance = AsyncMock()
                    mock_session.return_value.__aenter__.return_value = mock_session_instance

                    mock_subscription = MagicMock()
                    mock_result = AsyncMock()
                    mock_result.scalar_one_or_none.return_value = mock_subscription
                    mock_session_instance.execute.return_value = mock_result
                    mock_session_instance.commit = AsyncMock()
                    mock_session_instance.refresh = AsyncMock()

                    with patch.object(service, '_create_event') as mock_create_event:
                        updated_sub, proration = await service.change_plan("sub_123", change_request, tenant_id)

                        assert updated_sub is not None
                        assert proration is not None
                        assert isinstance(proration, ProrationResult)
                        mock_create_event.assert_called_once()


class TestSubscriptionServiceUsageTracking:
    """Test usage tracking functionality."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return SubscriptionService()

    @pytest.mark.asyncio
    async def test_record_usage_success(self, service, tenant_id, sample_subscription):
        """Test successful usage recording."""
        usage_request = UsageRecordRequest(
            subscription_id="sub_123",
            usage_type="api_calls",
            quantity=1000,
            timestamp=datetime.now(timezone.utc),
        )

        with patch.object(service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = sample_subscription

            with patch('dotmac.platform.billing.subscriptions.service.get_async_session') as mock_session:
                mock_session_instance = AsyncMock()
                mock_session.return_value.__aenter__.return_value = mock_session_instance

                mock_subscription = MagicMock()
                mock_subscription.usage_records = {"api_calls": 5000}
                mock_result = AsyncMock()
                mock_result.scalar_one_or_none.return_value = mock_subscription
                mock_session_instance.execute.return_value = mock_result
                mock_session_instance.commit = AsyncMock()
                mock_session_instance.refresh = AsyncMock()

                result = await service.record_usage(usage_request, tenant_id)

                assert result is not None
                assert "api_calls" in result
                assert result["api_calls"] == 6000  # 5000 + 1000
                mock_session_instance.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_usage_outside_period(self, service, tenant_id, sample_subscription):
        """Test usage recording fails when outside billing period."""
        # Usage timestamp outside current period
        usage_request = UsageRecordRequest(
            subscription_id="sub_123",
            usage_type="api_calls",
            quantity=1000,
            timestamp=datetime.now(timezone.utc) + timedelta(days=60),  # Future timestamp
        )

        with patch.object(service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = sample_subscription

            with pytest.raises(SubscriptionError) as exc_info:
                await service.record_usage(usage_request, tenant_id)

            assert "outside current billing period" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_usage_for_period(self, service, tenant_id, sample_subscription):
        """Test getting usage for current period."""
        with patch.object(service, 'get_subscription') as mock_get_sub:
            mock_get_sub.return_value = sample_subscription

            result = await service.get_usage_for_period("sub_123", tenant_id)

            assert result == {"api_calls": 5000, "storage_gb": 50}


class TestSubscriptionServiceHelpers:
    """Test helper methods in subscription service."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return SubscriptionService()

    def test_calculate_period_end_monthly(self, service):
        """Test monthly period end calculation."""
        start_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
        end_date = service._calculate_period_end(start_date, BillingCycle.MONTHLY)

        assert end_date.year == 2024
        assert end_date.month == 2
        assert end_date.day == 15

        # Test December to January transition
        december_start = datetime(2024, 12, 15, tzinfo=timezone.utc)
        january_end = service._calculate_period_end(december_start, BillingCycle.MONTHLY)

        assert january_end.year == 2025
        assert january_end.month == 1
        assert january_end.day == 15

    def test_calculate_period_end_quarterly(self, service):
        """Test quarterly period end calculation."""
        start_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
        end_date = service._calculate_period_end(start_date, BillingCycle.QUARTERLY)

        assert end_date.year == 2024
        assert end_date.month == 4
        assert end_date.day == 15

        # Test year transition
        november_start = datetime(2024, 11, 15, tzinfo=timezone.utc)
        february_end = service._calculate_period_end(november_start, BillingCycle.QUARTERLY)

        assert february_end.year == 2025
        assert february_end.month == 2
        assert february_end.day == 15

    def test_calculate_period_end_annual(self, service):
        """Test annual period end calculation."""
        start_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
        end_date = service._calculate_period_end(start_date, BillingCycle.ANNUAL)

        assert end_date.year == 2025
        assert end_date.month == 1
        assert end_date.day == 15

    def test_calculate_proration(self, service):
        """Test proration calculation."""
        now = datetime.now(timezone.utc)
        subscription = Subscription(
            subscription_id="sub_123",
            tenant_id="test-tenant",
            customer_id="customer-456",
            plan_id="plan_old",
            current_period_start=now - timedelta(days=15),  # 15 days into 30-day period
            current_period_end=now + timedelta(days=15),    # 15 days remaining
            status=SubscriptionStatus.ACTIVE,
            created_at=now,
        )

        old_plan = SubscriptionPlan(
            plan_id="plan_old",
            tenant_id="test-tenant",
            product_id="prod_123",
            name="Old Plan",
            billing_cycle=BillingCycle.MONTHLY,
            price=Decimal("30.00"),  # $30/month
            is_active=True,
            created_at=now,
        )

        new_plan = SubscriptionPlan(
            plan_id="plan_new",
            tenant_id="test-tenant",
            product_id="prod_123",
            name="New Plan",
            billing_cycle=BillingCycle.MONTHLY,
            price=Decimal("60.00"),  # $60/month
            is_active=True,
            created_at=now,
        )

        result = service._calculate_proration(subscription, old_plan, new_plan)

        assert isinstance(result, ProrationResult)
        assert result.days_remaining == 15
        # With half the period remaining:
        # Old plan unused: $30 * 0.5 = $15
        # New plan prorated: $60 * 0.5 = $30
        # Proration: $30 - $15 = $15 (customer owes $15)
        assert result.proration_amount > Decimal("0")
        assert result.old_plan_unused_amount > Decimal("0")
        assert result.new_plan_prorated_amount > Decimal("0")

    def test_db_to_pydantic_plan(self, service):
        """Test database to Pydantic plan conversion."""
        mock_db_plan = MagicMock()
        mock_db_plan.plan_id = "plan_123"
        mock_db_plan.tenant_id = "test-tenant"
        mock_db_plan.product_id = "prod_123"
        mock_db_plan.name = "Test Plan"
        mock_db_plan.description = "Test description"
        mock_db_plan.billing_cycle = "monthly"
        mock_db_plan.price = Decimal("29.99")
        mock_db_plan.currency = "USD"
        mock_db_plan.setup_fee = None
        mock_db_plan.trial_days = None
        mock_db_plan.included_usage = {"api_calls": 1000}
        mock_db_plan.overage_rates = {"api_calls": "0.001"}  # String from DB
        mock_db_plan.is_active = True
        mock_db_plan.metadata_json = {"tier": "basic"}
        mock_db_plan.created_at = datetime.now(timezone.utc)
        mock_db_plan.updated_at = None

        result = service._db_to_pydantic_plan(mock_db_plan)

        assert isinstance(result, SubscriptionPlan)
        assert result.plan_id == "plan_123"
        assert result.billing_cycle == BillingCycle.MONTHLY
        assert result.overage_rates["api_calls"] == Decimal("0.001")
        assert result.metadata == {"tier": "basic"}

    def test_db_to_pydantic_subscription(self, service):
        """Test database to Pydantic subscription conversion."""
        now = datetime.now(timezone.utc)
        mock_db_subscription = MagicMock()
        mock_db_subscription.subscription_id = "sub_123"
        mock_db_subscription.tenant_id = "test-tenant"
        mock_db_subscription.customer_id = "customer-456"
        mock_db_subscription.plan_id = "plan_123"
        mock_db_subscription.current_period_start = now
        mock_db_subscription.current_period_end = now + timedelta(days=30)
        mock_db_subscription.status = "active"
        mock_db_subscription.trial_end = None
        mock_db_subscription.cancel_at_period_end = False
        mock_db_subscription.canceled_at = None
        mock_db_subscription.ended_at = None
        mock_db_subscription.custom_price = None
        mock_db_subscription.usage_records = {"api_calls": 5000}
        mock_db_subscription.metadata_json = {"source": "web"}
        mock_db_subscription.created_at = now
        mock_db_subscription.updated_at = None

        result = service._db_to_pydantic_subscription(mock_db_subscription)

        assert isinstance(result, Subscription)
        assert result.subscription_id == "sub_123"
        assert result.status == SubscriptionStatus.ACTIVE
        assert result.usage_records == {"api_calls": 5000}
        assert result.metadata == {"source": "web"}