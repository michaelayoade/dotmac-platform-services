"""
Fixtures for subscription tests (router and service).
"""

from decimal import Decimal
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.core import UserInfo
from dotmac.platform.billing.subscriptions.models import (
    BillingCycle,
    SubscriptionPlanCreateRequest,
)
from dotmac.platform.billing.subscriptions.service import SubscriptionService
from dotmac.platform.main import app


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_auth_dependency():
    """Mock authentication dependency."""
    mock_user = UserInfo(
        user_id="test-user-123",
        username="testuser",
        email="test@example.com",
        roles=["user"],
        permissions=["subscriptions:read", "subscriptions:write"],
        tenant_id="test-tenant-123",
    )

    with patch("dotmac.platform.auth.dependencies.get_current_user", return_value=mock_user):
        yield mock_user


@pytest.fixture
def mock_tenant_dependency():
    """Mock tenant context dependency."""
    with patch("dotmac.platform.tenant.get_current_tenant_id", return_value="test-tenant-123"):
        yield "test-tenant-123"


# Service test fixtures


@pytest.fixture
def tenant_id() -> str:
    """Test tenant ID for service tests."""
    return "test-tenant-sub"


@pytest.fixture
def customer_id() -> str:
    """Test customer ID."""
    return "cust_sub_123"


@pytest.fixture
def sample_plan_data() -> SubscriptionPlanCreateRequest:
    """Sample subscription plan data."""
    return SubscriptionPlanCreateRequest(
        product_id="prod_basic",
        name="Basic Plan",
        description="Basic subscription plan",
        billing_cycle=BillingCycle.MONTHLY,
        price=Decimal("29.99"),
        currency="USD",
        setup_fee=Decimal("10.00"),
        trial_days=14,
        included_usage={"api_calls": 1000},
        overage_rates={"api_calls": Decimal("0.01")},
        metadata={"tier": "basic"},
    )


@pytest.fixture
async def subscription_service(async_session: AsyncSession):
    """Subscription service instance."""
    return SubscriptionService(db_session=async_session)
