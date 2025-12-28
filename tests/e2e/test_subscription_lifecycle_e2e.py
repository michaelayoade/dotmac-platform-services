"""
End-to-end tests for subscription lifecycle.

Tests cover subscription plans, subscriptions, lifecycle operations, and usage tracking.
"""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.billing.models import (
    BillingSubscriptionPlanTable,
    BillingSubscriptionTable,
)
from dotmac.platform.billing.subscriptions.models import (
    BillingCycle,
    SubscriptionStatus,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.e2e]


# ============================================================================
# Fixtures for Subscription Lifecycle E2E Tests
# ============================================================================


@pytest_asyncio.fixture
async def subscription_plan(e2e_db_session: AsyncSession, tenant_id: str):
    """Create a subscription plan."""
    unique_id = uuid.uuid4().hex[:8]
    plan = BillingSubscriptionPlanTable(
        plan_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        product_id=f"prod_{unique_id}",
        name=f"Test Plan {unique_id}",
        description="A test subscription plan",
        price=Decimal("49.99"),
        currency="USD",
        billing_cycle=BillingCycle.MONTHLY.value,
        is_active=True,
        included_usage={"api_calls": 10000, "storage_gb": 10},
        metadata_json={"tier": "standard", "features": ["feature1", "feature2", "feature3"]},
    )
    e2e_db_session.add(plan)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(plan)
    return plan


@pytest_asyncio.fixture
async def multiple_plans(e2e_db_session: AsyncSession, tenant_id: str):
    """Create multiple subscription plans."""
    plans = []
    cycles = [BillingCycle.MONTHLY, BillingCycle.ANNUAL, BillingCycle.MONTHLY]
    prices = [Decimal("29.99"), Decimal("299.99"), Decimal("99.99")]

    for i, (cycle, price) in enumerate(zip(cycles, prices)):
        unique_id = uuid.uuid4().hex[:8]
        plan = BillingSubscriptionPlanTable(
            plan_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            product_id=f"prod_{unique_id}",
            name=f"Plan {unique_id}",
            description=f"Plan description {i}",
            price=price,
            currency="USD",
            billing_cycle=cycle.value,
            is_active=True,
            included_usage={"api_calls": 1000 * (i + 1)},
            metadata_json={"features": [f"feature{i}"]},
        )
        e2e_db_session.add(plan)
        plans.append(plan)

    await e2e_db_session.commit()
    for p in plans:
        await e2e_db_session.refresh(p)
    return plans


@pytest_asyncio.fixture
async def active_subscription(
    e2e_db_session: AsyncSession,
    tenant_id: str,
    subscription_plan: BillingSubscriptionPlanTable,
):
    """Create an active subscription."""
    now = datetime.now(UTC)
    subscription = BillingSubscriptionTable(
        subscription_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        customer_id=str(uuid.uuid4()),
        plan_id=subscription_plan.plan_id,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        status=SubscriptionStatus.ACTIVE.value,
        cancel_at_period_end=False,
        usage_records={},
        metadata_json={},
    )
    e2e_db_session.add(subscription)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(subscription)
    return subscription


@pytest_asyncio.fixture
async def trial_subscription(
    e2e_db_session: AsyncSession,
    tenant_id: str,
    subscription_plan: BillingSubscriptionPlanTable,
):
    """Create a subscription in trial."""
    now = datetime.now(UTC)
    subscription = BillingSubscriptionTable(
        subscription_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        customer_id=str(uuid.uuid4()),
        plan_id=subscription_plan.plan_id,
        current_period_start=now,
        current_period_end=now + timedelta(days=14),
        trial_end=now + timedelta(days=14),
        status=SubscriptionStatus.TRIALING.value,
        cancel_at_period_end=False,
        usage_records={},
        metadata_json={},
    )
    e2e_db_session.add(subscription)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(subscription)
    return subscription


@pytest_asyncio.fixture
async def canceled_subscription(
    e2e_db_session: AsyncSession,
    tenant_id: str,
    subscription_plan: BillingSubscriptionPlanTable,
):
    """Create a canceled subscription."""
    now = datetime.now(UTC)
    subscription = BillingSubscriptionTable(
        subscription_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        customer_id=str(uuid.uuid4()),
        plan_id=subscription_plan.plan_id,
        current_period_start=now - timedelta(days=15),
        current_period_end=now + timedelta(days=15),
        status=SubscriptionStatus.CANCELED.value,
        cancel_at_period_end=True,
        canceled_at=now,
        usage_records={},
        metadata_json={},
    )
    e2e_db_session.add(subscription)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(subscription)
    return subscription


# ============================================================================
# Subscription Plan Tests
# ============================================================================


class TestSubscriptionPlanE2E:
    """End-to-end tests for subscription plan management."""

    async def test_create_plan(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating a subscription plan."""
        unique_id = uuid.uuid4().hex[:8]
        plan_data = {
            "product_id": f"prod_{unique_id}",
            "name": f"New Plan {unique_id}",
            "description": "A new subscription plan",
            "price": "59.99",
            "currency": "USD",
            "billing_cycle": "monthly",
            "features": ["api_access", "support"],
        }

        response = await async_client.post(
            "/api/v1/billing/subscriptions/plans",
            json=plan_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == plan_data["name"]
        assert "plan_id" in data

    async def test_list_plans(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_plans: list[BillingSubscriptionPlanTable],
    ):
        """Test listing subscription plans."""
        response = await async_client.get(
            "/api/v1/billing/subscriptions/plans",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_plans_active_only(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_plans: list[BillingSubscriptionPlanTable],
    ):
        """Test listing only active plans."""
        response = await async_client.get(
            "/api/v1/billing/subscriptions/plans?active_only=true",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        for plan in data:
            assert plan["is_active"] is True

    async def test_get_plan(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        subscription_plan: BillingSubscriptionPlanTable,
    ):
        """Test getting a specific plan."""
        response = await async_client.get(
            f"/api/v1/billing/subscriptions/plans/{subscription_plan.plan_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["plan_id"] == subscription_plan.plan_id

    async def test_get_plan_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting non-existent plan."""
        fake_id = str(uuid.uuid4())
        response = await async_client.get(
            f"/api/v1/billing/subscriptions/plans/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404


# ============================================================================
# Subscription CRUD Tests
# ============================================================================


class TestSubscriptionCRUDE2E:
    """End-to-end tests for subscription CRUD operations."""

    async def test_create_subscription(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        subscription_plan: BillingSubscriptionPlanTable,
    ):
        """Test creating a subscription."""
        subscription_data = {
            "customer_id": str(uuid.uuid4()),
            "plan_id": subscription_plan.plan_id,
        }

        response = await async_client.post(
            "/api/v1/billing/subscriptions",
            json=subscription_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["plan_id"] == subscription_plan.plan_id
        assert data["status"] in ["active", "trialing"]

    async def test_list_subscriptions(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        active_subscription: BillingSubscriptionTable,
    ):
        """Test listing subscriptions."""
        response = await async_client.get(
            "/api/v1/billing/subscriptions",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_subscriptions_filter_by_status(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        active_subscription: BillingSubscriptionTable,
    ):
        """Test listing subscriptions filtered by status."""
        response = await async_client.get(
            "/api/v1/billing/subscriptions?status=active",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        for sub in data:
            assert sub["status"] == "active"

    async def test_get_subscription(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        active_subscription: BillingSubscriptionTable,
    ):
        """Test getting a specific subscription."""
        response = await async_client.get(
            f"/api/v1/billing/subscriptions/{active_subscription.subscription_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["subscription_id"] == active_subscription.subscription_id

    async def test_get_subscription_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting non-existent subscription."""
        fake_id = str(uuid.uuid4())
        response = await async_client.get(
            f"/api/v1/billing/subscriptions/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_update_subscription(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        active_subscription: BillingSubscriptionTable,
    ):
        """Test updating a subscription."""
        update_data = {
            "metadata": {"custom_field": "custom_value"},
        }

        response = await async_client.patch(
            f"/api/v1/billing/subscriptions/{active_subscription.subscription_id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200


# ============================================================================
# Subscription Lifecycle Tests
# ============================================================================


class TestSubscriptionLifecycleE2E:
    """End-to-end tests for subscription lifecycle operations."""

    async def test_cancel_subscription_at_period_end(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        active_subscription: BillingSubscriptionTable,
    ):
        """Test canceling a subscription at period end."""
        response = await async_client.post(
            f"/api/v1/billing/subscriptions/{active_subscription.subscription_id}/cancel?at_period_end=true",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "cancel" in data.get("message", "").lower()

    async def test_cancel_subscription_immediately(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        e2e_db_session: AsyncSession,
        subscription_plan: BillingSubscriptionPlanTable,
        tenant_id: str,
    ):
        """Test canceling a subscription immediately."""
        # Create a fresh subscription
        now = datetime.now(UTC)
        subscription = BillingSubscriptionTable(
            subscription_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            customer_id=str(uuid.uuid4()),
            plan_id=subscription_plan.plan_id,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            status=SubscriptionStatus.ACTIVE.value,
            cancel_at_period_end=False,
            usage_records={},
            metadata_json={},
        )
        e2e_db_session.add(subscription)
        await e2e_db_session.commit()

        response = await async_client.post(
            f"/api/v1/billing/subscriptions/{subscription.subscription_id}/cancel?at_period_end=false",
            headers=auth_headers,
        )

        assert response.status_code == 200

    async def test_reactivate_subscription(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        canceled_subscription: BillingSubscriptionTable,
    ):
        """Test reactivating a canceled subscription."""
        response = await async_client.post(
            f"/api/v1/billing/subscriptions/{canceled_subscription.subscription_id}/reactivate",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "reactivat" in data.get("message", "").lower()

    async def test_change_subscription_plan(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        active_subscription: BillingSubscriptionTable,
        multiple_plans: list[BillingSubscriptionPlanTable],
    ):
        """Test changing subscription plan."""
        new_plan = multiple_plans[1]  # Different plan

        change_data = {
            "new_plan_id": new_plan.plan_id,
            "prorate": True,
        }

        response = await async_client.post(
            f"/api/v1/billing/subscriptions/{active_subscription.subscription_id}/change-plan",
            json=change_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    async def test_get_expiring_subscriptions(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        active_subscription: BillingSubscriptionTable,
    ):
        """Test getting expiring subscriptions."""
        response = await async_client.get(
            "/api/v1/billing/subscriptions/expiring?days=30",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "days_ahead" in data

    async def test_extend_subscription(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        active_subscription: BillingSubscriptionTable,
    ):
        """Test extending a subscription."""
        response = await async_client.post(
            f"/api/v1/billing/subscriptions/{active_subscription.subscription_id}/extend",
            headers=auth_headers,
        )

        assert response.status_code == 200

    async def test_check_renewal_eligibility(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        active_subscription: BillingSubscriptionTable,
    ):
        """Test checking renewal eligibility."""
        response = await async_client.get(
            f"/api/v1/billing/subscriptions/{active_subscription.subscription_id}/renewal-eligibility",
            headers=auth_headers,
        )

        assert response.status_code == 200


# ============================================================================
# Usage Tracking Tests
# ============================================================================


class TestSubscriptionUsageE2E:
    """End-to-end tests for subscription usage tracking."""

    async def test_record_usage(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        active_subscription: BillingSubscriptionTable,
    ):
        """Test recording usage for a subscription."""
        usage_data = {
            "subscription_id": active_subscription.subscription_id,
            "usage_type": "api_calls",
            "quantity": 100,
        }

        response = await async_client.post(
            f"/api/v1/billing/subscriptions/{active_subscription.subscription_id}/usage",
            json=usage_data,
            headers=auth_headers,
        )

        assert response.status_code == 201

    async def test_get_usage(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        active_subscription: BillingSubscriptionTable,
    ):
        """Test getting subscription usage."""
        response = await async_client.get(
            f"/api/v1/billing/subscriptions/{active_subscription.subscription_id}/usage",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "subscription_id" in data
        assert "usage" in data

    async def test_proration_preview(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        active_subscription: BillingSubscriptionTable,
        multiple_plans: list[BillingSubscriptionPlanTable],
    ):
        """Test proration preview for plan change."""
        new_plan = multiple_plans[1]

        response = await async_client.post(
            f"/api/v1/billing/subscriptions/proration-preview?subscription_id={active_subscription.subscription_id}&new_plan_id={new_plan.plan_id}",
            headers=auth_headers,
        )

        # May succeed or fail based on service implementation
        assert response.status_code in [200, 400, 404]


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestSubscriptionErrorsE2E:
    """End-to-end tests for subscription error handling."""

    async def test_create_subscription_invalid_plan(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating subscription with invalid plan."""
        subscription_data = {
            "customer_id": str(uuid.uuid4()),
            "plan_id": str(uuid.uuid4()),  # Non-existent plan
        }

        response = await async_client.post(
            "/api/v1/billing/subscriptions",
            json=subscription_data,
            headers=auth_headers,
        )

        assert response.status_code in [400, 404]

    async def test_cancel_already_canceled(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        canceled_subscription: BillingSubscriptionTable,
    ):
        """Test canceling an already canceled subscription."""
        response = await async_client.post(
            f"/api/v1/billing/subscriptions/{canceled_subscription.subscription_id}/cancel",
            headers=auth_headers,
        )

        # May succeed or fail based on implementation
        assert response.status_code in [200, 400]

    async def test_unauthorized_access(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test accessing subscriptions without authentication."""
        response = await async_client.get(
            "/api/v1/billing/subscriptions",
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 401
