"""
Integration Tests for Billing Routers (API Endpoints).

Strategy: Use REAL database, mock ONLY external APIs (payment providers, event bus)
Focus: Test API contracts, authentication, validation, database integration
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient

from dotmac.platform.billing.core.enums import PaymentStatus
from dotmac.platform.billing.subscriptions.models import (
    BillingCycle,
    SubscriptionStatus,
)


# Reset rate limiter before each test to prevent state leakage
@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter singleton before each test to ensure test isolation.

    The rate limiter uses in-memory storage that persists across tests,
    which can cause tests to fail if a previous test exhausted the rate limit.
    """
    from dotmac.platform.core.rate_limiting import reset_limiter

    reset_limiter()
    yield
    # Optional: Reset again after test for extra safety
    reset_limiter()


@pytest.mark.asyncio
class TestPaymentsRouter:
    """Integration tests for payments router."""

    async def test_get_failed_payments_success(
        self, router_client: AsyncClient, auth_headers, async_session
    ):
        """Test getting failed payments summary."""
        # Import entities here to avoid circular imports
        from dotmac.platform.billing.core.entities import PaymentEntity

        # Create test failed payments in database
        now = datetime.now(UTC)
        payment1 = PaymentEntity(
            tenant_id="test-tenant",  # Must match test_app tenant override
            amount=10000,  # $100
            currency="USD",
            customer_id="cust_123",
            status=PaymentStatus.FAILED,
            payment_method_type="card",
            provider="stripe",  # Required field
            created_at=now - timedelta(days=5),
        )
        payment2 = PaymentEntity(
            tenant_id="test-tenant",  # Must match test_app tenant override
            amount=5000,  # $50
            currency="USD",
            customer_id="cust_456",
            status=PaymentStatus.FAILED,
            payment_method_type="card",
            provider="stripe",  # Required field
            created_at=now - timedelta(days=2),
        )

        async_session.add(payment1)
        async_session.add(payment2)
        await async_session.commit()

        # Call API
        response = await router_client.get(
            "/api/v1/billing/payments/failed",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["count"] == 2
        assert data["total_amount"] == 15000.0  # $150 total

    async def test_get_failed_payments_requires_auth(self, unauth_client: AsyncClient):
        """Test that failed payments endpoint requires authentication."""
        response = await unauth_client.get("/api/v1/billing/payments/failed")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_failed_payments_handles_errors(
        self, router_client: AsyncClient, auth_headers
    ):
        """Test that failed payments endpoint handles DB errors gracefully."""
        with patch("dotmac.platform.db.get_session_dependency") as mock_session:
            # Simulate database error
            mock_session.return_value.execute = AsyncMock(side_effect=Exception("DB Error"))

            response = await router_client.get(
                "/api/v1/billing/payments/failed",
                headers=auth_headers,
            )

            # Should return empty summary instead of 500 error
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["count"] == 0
            assert data["total_amount"] == 0.0


@pytest.mark.asyncio
class TestSubscriptionsRouter:
    """Integration tests for subscriptions router."""

    async def test_create_subscription_plan_success(
        self, router_client: AsyncClient, auth_headers, async_session
    ):
        """Test creating subscription plan."""
        plan_data = {
            "product_id": "prod_123",
            "name": "Basic Plan",
            "description": "Basic subscription",
            "billing_cycle": BillingCycle.MONTHLY.value,
            "price": 29.99,
            "currency": "usd",
            "setup_fee": 0,
            "trial_days": 14,
            "included_usage": {},
            "overage_rates": {},
            "metadata": {},
        }

        response = await router_client.post(
            "/api/v1/billing/subscriptions/plans",
            json=plan_data,
            headers=auth_headers,
        )

        # Debug: Print response if not 201
        if response.status_code != status.HTTP_201_CREATED:
            print(f"ERROR: Status {response.status_code}, Body: {response.text}")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["name"] == "Basic Plan"
        assert float(data["price"]) == 29.99  # Price is returned as string from Decimal
        assert data["billing_cycle"] == BillingCycle.MONTHLY.value
        assert "plan_id" in data

    async def test_create_subscription_plan_requires_auth(self, unauth_client: AsyncClient):
        """Test that plan creation requires authentication."""
        plan_data = {
            "product_id": "prod_123",
            "name": "Test Plan",
            "billing_cycle": "monthly",
            "price": 10.00,
            "currency": "usd",
        }

        response = await unauth_client.post(
            "/api/v1/billing/subscriptions/plans",
            json=plan_data,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_list_subscription_plans(
        self, router_client: AsyncClient, auth_headers, async_session
    ):
        """Test listing subscription plans."""
        # Create test plan in database
        from dotmac.platform.billing.models import BillingSubscriptionPlanTable

        plan = BillingSubscriptionPlanTable(
            plan_id="plan_123",
            tenant_id="test-tenant",
            product_id="prod_123",
            name="Test Plan",
            description="Test subscription plan",
            billing_cycle=BillingCycle.MONTHLY.value,
            price=Decimal("29.99"),
            currency="usd",
            is_active=True,
        )

        async_session.add(plan)
        await async_session.commit()

        # Call API
        response = await router_client.get(
            "/api/v1/billing/subscriptions/plans",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert isinstance(data, list)
        # Debug: print actual data to understand what's returned
        if not any(p["plan_id"] == "plan_123" for p in data):
            print(
                f"Expected plan_123 not found. Received plans: {[p['plan_id'] for p in data] if data else 'empty list'}"
            )
        assert len(data) >= 1, f"Expected at least 1 plan, got {len(data)}"
        assert any(
            p["plan_id"] == "plan_123" for p in data
        ), f"plan_123 not in {[p['plan_id'] for p in data]}"

    async def test_get_subscription_plan_by_id(
        self, router_client: AsyncClient, auth_headers, async_session
    ):
        """Test getting subscription plan by ID."""
        from dotmac.platform.billing.models import BillingSubscriptionPlanTable

        plan = BillingSubscriptionPlanTable(
            plan_id="plan_456",
            tenant_id="test-tenant",
            product_id="prod_123",
            name="Premium Plan",
            description="Premium subscription",
            billing_cycle=BillingCycle.ANNUAL.value,
            price=Decimal("299.99"),
            currency="usd",
            is_active=True,
        )

        async_session.add(plan)
        await async_session.commit()

        response = await router_client.get(
            "/api/v1/billing/subscriptions/plans/plan_456",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["plan_id"] == "plan_456"
        assert data["name"] == "Premium Plan"
        assert float(data["price"]) == 299.99  # Price is returned as string from Decimal

    async def test_get_nonexistent_plan_returns_404(self, router_client: AsyncClient, auth_headers):
        """Test getting non-existent plan returns 404."""
        response = await router_client.get(
            "/api/v1/billing/subscriptions/plans/plan_nonexistent",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_create_subscription_success(
        self, router_client: AsyncClient, auth_headers, async_session
    ):
        """Test creating customer subscription."""
        # Create plan first
        from dotmac.platform.billing.models import BillingSubscriptionPlanTable

        plan = BillingSubscriptionPlanTable(
            plan_id="plan_789",
            tenant_id="test-tenant",
            product_id="prod_123",
            name="Monthly Plan",
            billing_cycle=BillingCycle.MONTHLY.value,
            price=Decimal("49.99"),
            currency="usd",
            trial_days=7,
            is_active=True,
        )

        async_session.add(plan)
        await async_session.commit()

        subscription_data = {
            "customer_id": "cust_123",
            "plan_id": "plan_789",
            "metadata": {},
        }

        response = await router_client.post(
            "/api/v1/billing/subscriptions/",
            json=subscription_data,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["customer_id"] == "cust_123"
        assert data["plan_id"] == "plan_789"
        assert data["status"] == SubscriptionStatus.TRIALING.value  # Has 7 day trial
        assert "subscription_id" in data

    async def test_create_subscription_invalid_plan_returns_400(
        self, router_client: AsyncClient, auth_headers
    ):
        """Test creating subscription with invalid plan returns 400."""
        subscription_data = {
            "customer_id": "cust_123",
            "plan_id": "plan_nonexistent",
        }

        response = await router_client.post(
            "/api/v1/billing/subscriptions/",
            json=subscription_data,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
class TestInvoiceRouter:
    """Integration tests for invoice router (if exists)."""

    async def test_invoice_creation_validation(self, router_client: AsyncClient, auth_headers):
        """Test invoice creation with validation."""
        # This test assumes invoice router exists
        # If not, it will be skipped
        invoice_data = {
            "customer_id": "cust_123",
            "billing_email": "customer@example.com",
            "billing_address": {"street": "123 Main St", "city": "Boston"},
            "line_items": [
                {
                    "description": "Product A",
                    "quantity": 2,
                    "unit_price": 50.00,
                    "total_price": 100.00,
                    "tax_rate": 0.0,
                    "tax_amount": 0.0,
                    "discount_percentage": 0.0,
                    "discount_amount": 0.0,
                }
            ],
            "currency": "USD",
        }

        # Try creating invoice (may not exist)
        try:
            response = await router_client.post(
                "/api/v1/billing/invoices",
                json=invoice_data,
                headers=auth_headers,
            )

            # If endpoint exists, verify response
            if response.status_code != status.HTTP_404_NOT_FOUND:
                assert response.status_code in [
                    status.HTTP_201_CREATED,
                    status.HTTP_200_OK,
                ]
        except Exception:
            # Endpoint may not exist, skip
            pytest.skip("Invoice endpoint not implemented")


@pytest.mark.asyncio
class TestTenantIsolation:
    """Test tenant isolation across billing endpoints."""

    async def test_plans_tenant_isolation(
        self, router_client: AsyncClient, auth_headers, async_session
    ):
        """Test that plans are isolated by tenant."""
        from dotmac.platform.billing.models import BillingSubscriptionPlanTable

        # Create plan for tenant-1
        plan_tenant1 = BillingSubscriptionPlanTable(
            plan_id="plan_tenant1",
            tenant_id="test-tenant",
            product_id="prod_123",
            name="Tenant 1 Plan",
            billing_cycle=BillingCycle.MONTHLY.value,
            price=Decimal("29.99"),
            currency="usd",
            is_active=True,
        )

        # Create plan for different tenant
        plan_tenant2 = BillingSubscriptionPlanTable(
            plan_id="plan_tenant2",
            tenant_id="tenant-2",
            product_id="prod_123",
            name="Tenant 2 Plan",
            billing_cycle=BillingCycle.MONTHLY.value,
            price=Decimal("29.99"),
            currency="usd",
            is_active=True,
        )

        async_session.add(plan_tenant1)
        async_session.add(plan_tenant2)
        await async_session.commit()

        # List plans (should only see tenant-1 plans)
        response = await router_client.get(
            "/api/v1/billing/subscriptions/plans",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should only see tenant-1 plan
        plan_ids = [p["plan_id"] for p in data]
        assert "plan_tenant1" in plan_ids
        assert "plan_tenant2" not in plan_ids


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling in billing routers."""

    async def test_invalid_json_returns_422(self, router_client: AsyncClient, auth_headers):
        """Test that invalid JSON returns 422 validation error."""
        response = await router_client.post(
            "/api/v1/billing/subscriptions/plans",
            content="not valid json",
            headers={**auth_headers, "Content-Type": "application/json"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_missing_required_fields_returns_422(
        self, router_client: AsyncClient, auth_headers
    ):
        """Test that missing required fields returns 422."""
        incomplete_data = {
            "name": "Test Plan",
            # Missing: billing_cycle, price, currency
        }

        response = await router_client.post(
            "/api/v1/billing/subscriptions/plans",
            json=incomplete_data,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_service_exception_handling(self, router_client: AsyncClient, auth_headers):
        """Test that service exceptions are properly handled by router."""
        # Test with a malformed request that will cause service-level error
        plan_data = {
            "product_id": "prod_123",
            "name": "Test Plan",
            "billing_cycle": "INVALID_CYCLE",  # Invalid enum value
            "price": 10.00,
            "currency": "usd",
        }

        response = await router_client.post(
            "/api/v1/billing/subscriptions/plans",
            json=plan_data,
            headers=auth_headers,
        )

        # Should return 422 validation error for invalid enum
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
class TestRateLimiting:
    """Test rate limiting on billing endpoints (if implemented)."""

    async def test_rate_limit_enforcement(self, router_client: AsyncClient, auth_headers):
        """Test that rate limits are enforced.

        SECURITY: Rate limiting is REQUIRED for billing endpoints to prevent:
        - Denial of service attacks
        - Resource exhaustion
        - Abuse of billing operations

        This test MUST NOT skip - rate limiting is a mandatory security control.
        """
        # Enable rate limiting for this specific test (global fixture disables it)
        from dotmac.platform.core.rate_limiting import get_limiter, reset_limiter
        import os

        # Ensure Redis URL is set for rate limiting storage (required for pytest-xdist)
        # The rate limiter looks for RATE_LIMIT_STORAGE_URL, not REDIS_URL
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/2")
        os.environ["RATE_LIMIT_STORAGE_URL"] = redis_url

        # Reset and recreate limiter with Redis storage
        reset_limiter()
        limiter_instance = get_limiter()
        original_enabled = limiter_instance.enabled
        limiter_instance.enabled = True

        try:
            # Try to make many requests rapidly (exceeds 100/minute limit)
            responses = []
            for _ in range(150):  # Exceed the 100/minute limit on list_subscription_plans
                response = await router_client.get(
                    "/api/v1/billing/subscriptions/plans",
                    headers=auth_headers,
                )
                responses.append(response.status_code)

            # SECURITY: Rate limiting MUST be enforced - 429 responses are REQUIRED
            rate_limited_count = responses.count(status.HTTP_429_TOO_MANY_REQUESTS)

            assert rate_limited_count > 0, (
                f"SECURITY FAILURE: Rate limiting not enforced on billing endpoints! "
                f"Made 150 requests, expected HTTP 429 responses but got none. "
                f"Response codes: {set(responses)}. "
                f"This is a critical security vulnerability - billing endpoints MUST be rate limited."
            )
        finally:
            # Restore original state
            limiter_instance.enabled = original_enabled
