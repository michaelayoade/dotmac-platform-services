"""
Comprehensive tests for billing and customer metrics router.

Tests all three Phase 1 endpoints with mocked data, error handling, and edge cases.
"""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from dotmac.platform.auth.core import UserInfo
from dotmac.platform.billing.metrics_router import (
    router,
    customer_metrics_router,
    BillingMetricsResponse,
    PaymentListResponse,
    CustomerMetricsResponse,
)
from dotmac.platform.customer_management.models import CustomerStatus


@pytest.fixture
def mock_session():
    """Create mock database session."""
    session = AsyncMock()
    return session


@pytest.fixture
def mock_user():
    """Create mock user with tenant."""
    return UserInfo(
        user_id="test-user",
        username="testuser",
        email="test@example.com",
        tenant_id="test-tenant",
    )


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.include_router(customer_metrics_router, prefix="/api/v1")
    return app


# ============================================================================
# Billing Metrics Endpoint Tests
# ============================================================================


class TestBillingMetricsEndpoint:
    """Test GET /api/v1/billing/metrics endpoint."""

    @pytest.mark.asyncio
    async def test_get_billing_metrics_with_data(self, mock_session, mock_user):
        """Test billing metrics with full data."""
        from dotmac.platform.billing.metrics_router import get_billing_metrics

        # Mock subscription data
        subscription_result = Mock()
        subscription_result.one.return_value = Mock(count=50, total_amount=500000)

        # Mock invoice data
        invoice_result = Mock()
        invoice_result.one.return_value = Mock(total=100, paid=80, overdue=5)

        # Mock payment data
        payment_result = Mock()
        payment_result.one.return_value = Mock(
            total=120, successful=110, failed=10, total_amount=2500000
        )

        mock_session.execute = AsyncMock(
            side_effect=[subscription_result, invoice_result, payment_result]
        )

        response = await get_billing_metrics(
            period_days=30, session=mock_session, current_user=mock_user
        )

        assert isinstance(response, BillingMetricsResponse)
        assert response.mrr == 5000.0  # 500000 cents / 100
        assert response.arr == 60000.0  # MRR * 12
        assert response.active_subscriptions == 50
        assert response.total_invoices == 100
        assert response.paid_invoices == 80
        assert response.overdue_invoices == 5
        assert response.total_payments == 120
        assert response.successful_payments == 110
        assert response.failed_payments == 10
        assert response.total_payment_amount == 25000.0  # 2500000 cents / 100
        assert response.period == "30d"

    @pytest.mark.asyncio
    async def test_get_billing_metrics_with_zero_data(self, mock_session, mock_user):
        """Test billing metrics with no data."""
        from dotmac.platform.billing.metrics_router import get_billing_metrics

        # Mock empty results
        empty_result = Mock()
        empty_result.one.return_value = Mock(
            count=0, total_amount=0, total=0, paid=0, overdue=0, successful=0, failed=0
        )

        mock_session.execute = AsyncMock(return_value=empty_result)

        response = await get_billing_metrics(
            period_days=7, session=mock_session, current_user=mock_user
        )

        assert response.mrr == 0.0
        assert response.arr == 0.0
        assert response.active_subscriptions == 0
        assert response.total_payments == 0
        assert response.period == "7d"

    @pytest.mark.asyncio
    async def test_get_billing_metrics_exception_handling(self, mock_session, mock_user):
        """Test billing metrics handles exceptions gracefully."""
        from dotmac.platform.billing.metrics_router import get_billing_metrics

        # Make session.execute raise an exception
        mock_session.execute = AsyncMock(side_effect=Exception("Database error"))

        response = await get_billing_metrics(
            period_days=30, session=mock_session, current_user=mock_user
        )

        # Should return safe defaults
        assert response.mrr == 0.0
        assert response.arr == 0.0
        assert response.active_subscriptions == 0
        assert response.total_invoices == 0
        assert response.total_payments == 0
        assert response.period == "30d"

    @pytest.mark.asyncio
    async def test_get_billing_metrics_custom_period(self, mock_session, mock_user):
        """Test billing metrics with custom time period."""
        from dotmac.platform.billing.metrics_router import get_billing_metrics

        # Mock data
        subscription_result = Mock()
        subscription_result.one.return_value = Mock(count=100, total_amount=1000000)

        invoice_result = Mock()
        invoice_result.one.return_value = Mock(total=200, paid=180, overdue=10)

        payment_result = Mock()
        payment_result.one.return_value = Mock(
            total=250, successful=240, failed=10, total_amount=5000000
        )

        mock_session.execute = AsyncMock(
            side_effect=[subscription_result, invoice_result, payment_result]
        )

        response = await get_billing_metrics(
            period_days=90, session=mock_session, current_user=mock_user
        )

        assert response.period == "90d"
        assert response.mrr == 10000.0
        assert response.arr == 120000.0

    @pytest.mark.asyncio
    async def test_get_billing_metrics_without_tenant(self, mock_session):
        """Test billing metrics without tenant_id in user."""
        from dotmac.platform.billing.metrics_router import get_billing_metrics

        # User without tenant_id
        user_no_tenant = UserInfo(
            user_id="test-user",
            username="testuser",
            email="test@example.com",
        )

        # Mock data
        subscription_result = Mock()
        subscription_result.one.return_value = Mock(count=25, total_amount=250000)

        invoice_result = Mock()
        invoice_result.one.return_value = Mock(total=50, paid=45, overdue=2)

        payment_result = Mock()
        payment_result.one.return_value = Mock(
            total=60, successful=55, failed=5, total_amount=1250000
        )

        mock_session.execute = AsyncMock(
            side_effect=[subscription_result, invoice_result, payment_result]
        )

        response = await get_billing_metrics(
            period_days=30, session=mock_session, current_user=user_no_tenant
        )

        # Should still work without tenant filtering
        assert response.active_subscriptions == 25
        assert response.mrr == 2500.0


# ============================================================================
# Payment List Endpoint Tests
# ============================================================================


class TestPaymentListEndpoint:
    """Test GET /api/v1/billing/payments endpoint."""

    @pytest.mark.asyncio
    async def test_get_recent_payments_with_data(self, mock_session, mock_user):
        """Test payment list with data."""
        from dotmac.platform.billing.metrics_router import get_recent_payments
        from dotmac.platform.billing.core.models import PaymentStatus, PaymentMethodType

        # Mock payment entities
        mock_payments = [
            Mock(
                payment_id=f"pay_{i}",
                amount=10000 + i * 100,
                currency="USD",
                status=PaymentStatus.SUCCEEDED,
                customer_id=f"cust_{i}",
                payment_method_type=PaymentMethodType.CARD,
                provider="stripe",
                created_at=datetime.now(timezone.utc) - timedelta(days=i),
                processed_at=datetime.now(timezone.utc) - timedelta(days=i, hours=1),
                failure_reason=None,
            )
            for i in range(10)
        ]

        # Mock query results
        result = Mock()
        result.scalars.return_value.all.return_value = mock_payments

        count_result = Mock()
        count_result.scalar.return_value = 100

        mock_session.execute = AsyncMock(side_effect=[count_result, result])

        response = await get_recent_payments(
            limit=50, offset=0, status=None, session=mock_session, current_user=mock_user
        )

        assert isinstance(response, PaymentListResponse)
        assert len(response.payments) == 10
        assert response.total_count == 100
        assert response.limit == 50
        assert response.payments[0].payment_id == "pay_0"
        assert response.payments[0].amount == 100.0  # 10000 cents / 100
        assert response.payments[0].currency == "USD"
        assert response.payments[0].status == "succeeded"

    @pytest.mark.asyncio
    async def test_get_recent_payments_with_status_filter(self, mock_session, mock_user):
        """Test payment list with status filtering."""
        from dotmac.platform.billing.metrics_router import get_recent_payments
        from dotmac.platform.billing.core.models import PaymentStatus, PaymentMethodType

        # Mock only failed payments
        mock_payments = [
            Mock(
                payment_id=f"pay_failed_{i}",
                amount=5000,
                currency="USD",
                status=PaymentStatus.FAILED,
                customer_id=f"cust_{i}",
                payment_method_type=PaymentMethodType.CARD,
                provider="stripe",
                created_at=datetime.now(timezone.utc),
                processed_at=None,
                failure_reason="Insufficient funds",
            )
            for i in range(5)
        ]

        result = Mock()
        result.scalars.return_value.all.return_value = mock_payments

        count_result = Mock()
        count_result.scalar.return_value = 5

        mock_session.execute = AsyncMock(side_effect=[count_result, result])

        response = await get_recent_payments(
            limit=10,
            offset=0,
            status="failed",
            session=mock_session,
            current_user=mock_user,
        )

        assert len(response.payments) == 5
        assert response.total_count == 5
        assert all(p.status == "failed" for p in response.payments)
        assert all(p.failure_reason == "Insufficient funds" for p in response.payments)

    @pytest.mark.asyncio
    async def test_get_recent_payments_pagination(self, mock_session, mock_user):
        """Test payment list with pagination."""
        from dotmac.platform.billing.metrics_router import get_recent_payments
        from dotmac.platform.billing.core.models import PaymentStatus, PaymentMethodType

        # Mock second page of results
        mock_payments = [
            Mock(
                payment_id=f"pay_{i}",
                amount=10000,
                currency="USD",
                status=PaymentStatus.SUCCEEDED,
                customer_id=f"cust_{i}",
                payment_method_type=PaymentMethodType.CARD,
                provider="stripe",
                created_at=datetime.now(timezone.utc),
                processed_at=datetime.now(timezone.utc),
                failure_reason=None,
            )
            for i in range(50, 60)
        ]

        result = Mock()
        result.scalars.return_value.all.return_value = mock_payments

        count_result = Mock()
        count_result.scalar.return_value = 200

        mock_session.execute = AsyncMock(side_effect=[count_result, result])

        response = await get_recent_payments(
            limit=10, offset=50, status=None, session=mock_session, current_user=mock_user
        )

        assert len(response.payments) == 10
        assert response.total_count == 200
        assert response.payments[0].payment_id == "pay_50"

    @pytest.mark.asyncio
    async def test_get_recent_payments_empty_list(self, mock_session, mock_user):
        """Test payment list with no data."""
        from dotmac.platform.billing.metrics_router import get_recent_payments

        result = Mock()
        result.scalars.return_value.all.return_value = []

        count_result = Mock()
        count_result.scalar.return_value = 0

        mock_session.execute = AsyncMock(side_effect=[count_result, result])

        response = await get_recent_payments(
            limit=50, offset=0, status=None, session=mock_session, current_user=mock_user
        )

        assert len(response.payments) == 0
        assert response.total_count == 0

    @pytest.mark.asyncio
    async def test_get_recent_payments_exception_handling(self, mock_session, mock_user):
        """Test payment list handles exceptions gracefully."""
        from dotmac.platform.billing.metrics_router import get_recent_payments

        mock_session.execute = AsyncMock(side_effect=Exception("Database error"))

        response = await get_recent_payments(
            limit=50, offset=0, status=None, session=mock_session, current_user=mock_user
        )

        # Should return empty list on error
        assert len(response.payments) == 0
        assert response.total_count == 0
        assert response.limit == 50


# ============================================================================
# Customer Metrics Endpoint Tests
# ============================================================================


class TestCustomerMetricsEndpoint:
    """Test GET /api/v1/customers/metrics/overview endpoint."""

    @pytest.mark.asyncio
    async def test_get_customer_metrics_with_data(self, mock_session, mock_user):
        """Test customer metrics with full data."""
        from dotmac.platform.billing.metrics_router import get_customer_metrics_overview

        # Mock customer counts
        total_result = Mock()
        total_result.scalar.return_value = 500

        active_result = Mock()
        active_result.scalar.return_value = 450

        new_customers_result = Mock()
        new_customers_result.scalar.return_value = 50

        churned_result = Mock()
        churned_result.scalar.return_value = 10

        customers_last_month_result = Mock()
        customers_last_month_result.scalar.return_value = 40

        # Mock status breakdown
        status_result = Mock()
        status_result.all.return_value = [
            Mock(status=CustomerStatus.ACTIVE, count=450),
            Mock(status=CustomerStatus.INACTIVE, count=30),
            Mock(status=CustomerStatus.SUSPENDED, count=10),
            Mock(status=CustomerStatus.CHURNED, count=10),
        ]

        mock_session.execute = AsyncMock(
            side_effect=[
                total_result,
                active_result,
                new_customers_result,
                churned_result,
                customers_last_month_result,
                status_result,
            ]
        )

        response = await get_customer_metrics_overview(
            period_days=30, session=mock_session, current_user=mock_user
        )

        assert isinstance(response, CustomerMetricsResponse)
        assert response.total_customers == 500
        assert response.active_customers == 450
        assert response.new_customers_this_month == 50
        assert response.churned_customers_this_month == 10
        assert response.customer_growth_rate == 25.0  # (50-40)/40 * 100
        assert response.churn_rate == 2.22  # (10/450) * 100
        assert response.customers_by_status["active"] == 450
        assert response.at_risk_customers == 40  # inactive + suspended
        assert response.period == "30d"

    @pytest.mark.asyncio
    async def test_get_customer_metrics_with_zero_data(self, mock_session, mock_user):
        """Test customer metrics with no data."""
        from dotmac.platform.billing.metrics_router import get_customer_metrics_overview

        # Mock empty results
        zero_result = Mock()
        zero_result.scalar.return_value = 0

        empty_status_result = Mock()
        empty_status_result.all.return_value = []

        mock_session.execute = AsyncMock(
            side_effect=[
                zero_result,
                zero_result,
                zero_result,
                zero_result,
                zero_result,
                empty_status_result,
            ]
        )

        response = await get_customer_metrics_overview(
            period_days=30, session=mock_session, current_user=mock_user
        )

        assert response.total_customers == 0
        assert response.active_customers == 0
        assert response.customer_growth_rate == 0.0
        assert response.churn_rate == 0.0
        assert response.customers_by_status == {}
        assert response.at_risk_customers == 0

    @pytest.mark.asyncio
    async def test_get_customer_metrics_growth_calculation(self, mock_session, mock_user):
        """Test customer metrics growth rate calculation."""
        from dotmac.platform.billing.metrics_router import get_customer_metrics_overview

        # Mock data for growth calculation
        total_result = Mock()
        total_result.scalar.return_value = 1000

        active_result = Mock()
        active_result.scalar.return_value = 900

        new_customers_result = Mock()
        new_customers_result.scalar.return_value = 120

        churned_result = Mock()
        churned_result.scalar.return_value = 20

        # Last month had 100 new customers
        customers_last_month_result = Mock()
        customers_last_month_result.scalar.return_value = 100

        status_result = Mock()
        status_result.all.return_value = [
            Mock(status=CustomerStatus.ACTIVE, count=900),
            Mock(status=CustomerStatus.CHURNED, count=100),
        ]

        mock_session.execute = AsyncMock(
            side_effect=[
                total_result,
                active_result,
                new_customers_result,
                churned_result,
                customers_last_month_result,
                status_result,
            ]
        )

        response = await get_customer_metrics_overview(
            period_days=30, session=mock_session, current_user=mock_user
        )

        # Growth rate: (120 - 100) / 100 * 100 = 20%
        assert response.customer_growth_rate == 20.0
        # Churn rate: (20 / 900) * 100 = 2.22%
        assert response.churn_rate == 2.22

    @pytest.mark.asyncio
    async def test_get_customer_metrics_exception_handling(self, mock_session, mock_user):
        """Test customer metrics handles exceptions gracefully."""
        from dotmac.platform.billing.metrics_router import get_customer_metrics_overview

        mock_session.execute = AsyncMock(side_effect=Exception("Database error"))

        response = await get_customer_metrics_overview(
            period_days=30, session=mock_session, current_user=mock_user
        )

        # Should return safe defaults
        assert response.total_customers == 0
        assert response.active_customers == 0
        assert response.customer_growth_rate == 0.0
        assert response.churn_rate == 0.0
        assert response.customers_by_status == {}

    @pytest.mark.asyncio
    async def test_get_customer_metrics_custom_period(self, mock_session, mock_user):
        """Test customer metrics with custom time period."""
        from dotmac.platform.billing.metrics_router import get_customer_metrics_overview

        # Mock data
        total_result = Mock()
        total_result.scalar.return_value = 2000

        active_result = Mock()
        active_result.scalar.return_value = 1800

        new_customers_result = Mock()
        new_customers_result.scalar.return_value = 200

        churned_result = Mock()
        churned_result.scalar.return_value = 50

        customers_last_month_result = Mock()
        customers_last_month_result.scalar.return_value = 180

        status_result = Mock()
        status_result.all.return_value = [
            Mock(status=CustomerStatus.ACTIVE, count=1800),
        ]

        mock_session.execute = AsyncMock(
            side_effect=[
                total_result,
                active_result,
                new_customers_result,
                churned_result,
                customers_last_month_result,
                status_result,
            ]
        )

        response = await get_customer_metrics_overview(
            period_days=90, session=mock_session, current_user=mock_user
        )

        assert response.period == "90d"
        assert response.total_customers == 2000


# ============================================================================
# Router Integration Tests
# ============================================================================


class TestRouterIntegration:
    """Test router integration and configuration."""

    def test_billing_router_exists(self):
        """Test billing metrics router is properly configured."""
        assert router is not None
        assert len(router.routes) >= 2  # /metrics and /payments
        assert "Billing Metrics" in router.tags

    def test_customer_metrics_router_exists(self):
        """Test customer metrics router is properly configured."""
        assert customer_metrics_router is not None
        assert len(customer_metrics_router.routes) >= 1  # /overview
        assert "Customer Metrics" in customer_metrics_router.tags

    def test_billing_metrics_route_config(self):
        """Test billing metrics endpoint configuration."""
        # Find the /metrics route
        metrics_route = next((r for r in router.routes if "/metrics" in r.path), None)
        assert metrics_route is not None
        assert "GET" in metrics_route.methods

    def test_payments_route_config(self):
        """Test payments endpoint configuration."""
        # Find the /payments route
        payments_route = next((r for r in router.routes if "/payments" in r.path), None)
        assert payments_route is not None
        assert "GET" in payments_route.methods

    def test_customer_overview_route_config(self):
        """Test customer overview endpoint configuration."""
        # Find the /overview route
        overview_route = next(
            (r for r in customer_metrics_router.routes if "/overview" in r.path), None
        )
        assert overview_route is not None
        assert "GET" in overview_route.methods
