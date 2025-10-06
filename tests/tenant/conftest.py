"""
Fixtures for tenant management tests.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.dotmac.platform.billing.subscriptions.models import Subscription
from src.dotmac.platform.billing.subscriptions.service import SubscriptionService
from src.dotmac.platform.tenant.models import Tenant, TenantPlanType, TenantStatus
from src.dotmac.platform.tenant.service import TenantService
from src.dotmac.platform.tenant.usage_billing_integration import (
    TenantUsageBillingIntegration,
)


@pytest.fixture
def mock_tenant_service() -> AsyncMock:
    """Create mock tenant service instance."""
    service = AsyncMock(spec=TenantService)

    # Store tenant state
    tenant_state = {
        "tenant-123": {
            "current_api_calls": 8000,
            "current_storage_gb": 7.5,
            "current_users": 5,
        }
    }

    # Mock record_usage method
    async def mock_record_usage(tenant_id, usage_data):
        from src.dotmac.platform.tenant.service import TenantNotFoundError

        # Validate tenant exists
        if tenant_id == "nonexistent" or tenant_id == "invalid":
            raise TenantNotFoundError(f"Tenant {tenant_id} not found")

        return Mock(
            id=1,
            tenant_id=tenant_id,
            period_start=usage_data.period_start,
            period_end=usage_data.period_end,
            api_calls=usage_data.api_calls,
            storage_gb=usage_data.storage_gb,
            bandwidth_gb=usage_data.bandwidth_gb,
            active_users=usage_data.active_users,
        )

    service.record_usage = AsyncMock(side_effect=mock_record_usage)

    # Mock update_tenant_usage_counters method
    async def mock_update_counters(tenant_id, api_calls=None, storage_gb=None, users=None):
        """Update tenant usage counters in mock state."""
        if tenant_id not in tenant_state:
            tenant_state[tenant_id] = {}
        if api_calls is not None:
            tenant_state[tenant_id]["current_api_calls"] = api_calls
        if storage_gb is not None:
            tenant_state[tenant_id]["current_storage_gb"] = storage_gb
        if users is not None:
            tenant_state[tenant_id]["current_users"] = users
        return True

    service.update_tenant_usage_counters = AsyncMock(side_effect=mock_update_counters)

    # Mock get_tenant method
    async def mock_get_tenant(tenant_id):
        from decimal import Decimal
        from src.dotmac.platform.tenant.service import TenantNotFoundError

        # Raise error for invalid tenant IDs
        if tenant_id == "nonexistent" or tenant_id == "invalid":
            raise TenantNotFoundError(f"Tenant {tenant_id} not found")

        state = tenant_state.get(
            tenant_id,
            {
                "current_api_calls": 8000,
                "current_storage_gb": 7.5,
                "current_users": 5,
            },
        )

        current_api_calls = state.get("current_api_calls", 8000)
        current_storage_gb = state.get("current_storage_gb", 7.5)
        current_users = state.get("current_users", 5)

        # Default limits (professional plan)
        max_api_calls = 10000
        max_storage_gb = 50  # Professional plan has 50GB storage
        max_users = 10

        # Special handling for minimal-limit tenant
        if "minimal-limit" in str(tenant_id).lower():
            max_api_calls = 0
            max_storage_gb = 1
            max_users = 1

        # Determine plan type based on tenant_id
        plan_type = "professional"
        if "free" in str(tenant_id).lower():
            plan_type = "free"
        elif "starter" in str(tenant_id).lower():
            plan_type = "starter"
        elif "enterprise" in str(tenant_id).lower():
            plan_type = "enterprise"

        return Mock(
            id=tenant_id,
            name="Test Organization",
            slug="test-org",
            plan_type=plan_type,
            billing_cycle="monthly",
            max_users=max_users,
            max_api_calls_per_month=max_api_calls,
            max_storage_gb=max_storage_gb,
            current_users=current_users,
            current_api_calls=current_api_calls,
            current_storage_gb=Decimal(str(current_storage_gb)),
            has_exceeded_api_limit=current_api_calls > max_api_calls,
            has_exceeded_storage_limit=current_storage_gb > max_storage_gb,
            has_exceeded_user_limit=current_users > max_users,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    service.get_tenant = AsyncMock(side_effect=mock_get_tenant)

    # Mock get_tenant_stats method
    async def mock_get_tenant_stats(tenant_id):
        state = tenant_state.get(
            tenant_id,
            {
                "current_api_calls": 8000,
                "current_storage_gb": 7.5,
                "current_users": 5,
            },
        )

        current_api_calls = state.get("current_api_calls", 8000)
        current_storage_gb = state.get("current_storage_gb", 7.5)
        current_users = state.get("current_users", 5)

        return Mock(
            api_usage_percent=(current_api_calls / 10000) * 100,
            storage_usage_percent=(current_storage_gb / 50) * 100,  # Professional plan: 50GB
            user_usage_percent=(current_users / 10) * 100,
        )

    service.get_tenant_stats = AsyncMock(side_effect=mock_get_tenant_stats)

    # Mock create_tenant method
    async def mock_create_tenant(tenant_data, created_by=None):
        from decimal import Decimal

        tenant_id = f"{tenant_data.slug}-id"

        # Initialize tenant state
        tenant_state[tenant_id] = {
            "current_api_calls": 0,
            "current_storage_gb": 0,
            "current_users": 0,
        }

        # Get max values from tenant_data if provided
        max_users = getattr(tenant_data, "max_users", 10)
        max_api_calls = getattr(tenant_data, "max_api_calls_per_month", 10000)
        max_storage = getattr(tenant_data, "max_storage_gb", 10)

        return Mock(
            id=tenant_id,
            name=tenant_data.name,
            slug=tenant_data.slug,
            plan_type=(
                tenant_data.plan_type.value
                if hasattr(tenant_data.plan_type, "value")
                else tenant_data.plan_type
            ),
            billing_cycle="monthly",
            max_users=max_users,
            max_api_calls_per_month=max_api_calls,
            max_storage_gb=max_storage,
            current_users=0,
            current_api_calls=0,
            current_storage_gb=Decimal("0"),
            has_exceeded_api_limit=False,
            has_exceeded_storage_limit=False,
            has_exceeded_user_limit=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    service.create_tenant = AsyncMock(side_effect=mock_create_tenant)

    return service


@pytest.fixture
def mock_subscription_service() -> AsyncMock:
    """Create mock subscription service."""
    service = AsyncMock(spec=SubscriptionService)

    # Mock record_usage method
    async def mock_record_usage(usage_request, tenant_id):
        return Mock(
            subscription_id=usage_request.subscription_id,
            usage_type=usage_request.usage_type,
            quantity=usage_request.quantity,
            timestamp=usage_request.timestamp,
        )

    service.record_usage = AsyncMock(side_effect=mock_record_usage)

    # Mock list_subscriptions method
    async def mock_list_subscriptions(tenant_id: str = None, status: str = None):
        if tenant_id:
            return [
                Mock(
                    subscription_id="sub-123",
                    tenant_id=tenant_id,
                    status=status or "active",
                )
            ]
        return []

    service.list_subscriptions = AsyncMock(side_effect=mock_list_subscriptions)

    return service


@pytest.fixture
def usage_billing_integration(
    mock_tenant_service: AsyncMock,
    mock_subscription_service: AsyncMock,
) -> TenantUsageBillingIntegration:
    """Create usage billing integration instance."""
    return TenantUsageBillingIntegration(
        tenant_service=mock_tenant_service,
        subscription_service=mock_subscription_service,
    )


@pytest.fixture
def sample_tenant() -> Mock:
    """Create a sample mock tenant for testing."""
    from decimal import Decimal

    return Mock(
        id="tenant-123",
        name="Test Organization",
        slug="test-org",
        plan_type="professional",
        billing_cycle="monthly",
        max_users=10,
        max_api_calls_per_month=10000,
        max_storage_gb=50,  # Storage limit is 50GB for these tests
        current_users=5,
        current_api_calls=8000,
        current_storage_gb=Decimal("7.5"),
        has_exceeded_api_limit=False,
        has_exceeded_storage_limit=False,
        has_exceeded_user_limit=False,
    )


# Alias for backwards compatibility with tests
@pytest.fixture
def tenant_service(mock_tenant_service: AsyncMock) -> AsyncMock:
    """Alias for mock_tenant_service."""
    return mock_tenant_service


@pytest.fixture
async def authenticated_client(
    mock_tenant_service: AsyncMock,
    mock_subscription_service: AsyncMock,
    usage_billing_integration: TenantUsageBillingIntegration,
):
    """Create authenticated async HTTP client with dependency overrides."""
    from fastapi import FastAPI
    from httpx import AsyncClient, ASGITransport

    # Create test app
    app = FastAPI()

    # Import and setup dependencies - use auth.core since that's what the router imports
    from src.dotmac.platform.auth.core import UserInfo, get_current_user
    from src.dotmac.platform.database import get_async_session
    from src.dotmac.platform.tenant.usage_billing_router import (
        get_subscription_service,
        get_tenant_service,
        get_usage_billing_integration,
        router,
    )

    # Override dependencies with mocks
    async def mock_get_current_user():
        """Return test user."""
        return UserInfo(
            user_id="test-user-123",
            email="test@example.com",
            username="testuser",
            roles=["admin"],
            permissions=["read", "write", "admin"],
            tenant_id="tenant-123",
        )

    async def mock_get_session():
        """Return mock session."""
        return AsyncMock()

    # Override the correct get_current_user from auth.core (not auth.dependencies)
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_async_session] = mock_get_session
    app.dependency_overrides[get_tenant_service] = lambda: mock_tenant_service
    app.dependency_overrides[get_subscription_service] = lambda: mock_subscription_service
    app.dependency_overrides[get_usage_billing_integration] = lambda: usage_billing_integration

    # Include the router
    app.include_router(router)

    # Create async client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
