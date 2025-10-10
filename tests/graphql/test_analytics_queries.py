"""
Tests for GraphQL analytics queries.

Tests dashboard and metrics queries using Strawberry test client.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from dotmac.platform.graphql.schema import schema


@pytest.fixture
async def graphql_client():
    """Create GraphQL test client using schema.execute."""
    # We'll use schema.execute directly instead of test client
    return schema


@pytest.fixture
def mock_user():
    """Create mock user for context."""
    from dotmac.platform.auth.core import UserInfo

    return UserInfo(
        user_id="test-user-123",
        tenant_id="tenant-123",
        permissions=["view:dashboard"],
    )


@pytest.fixture
def mock_context(mock_user):
    """Create mock GraphQL context."""
    from unittest.mock import MagicMock

    from dotmac.platform.graphql.context import Context

    context = MagicMock(spec=Context)
    context.current_user = mock_user
    context.db = AsyncMock()
    return context


class TestAnalyticsQueries:
    """Test analytics and metrics GraphQL queries."""

    @pytest.mark.asyncio
    async def test_version_query(self, graphql_client):
        """Test simple version query without authentication."""
        query = """
            query {
                version
            }
        """

        result = await graphql_client.execute(query)

        assert result.errors is None
        assert result.data["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_billing_metrics_query_requires_auth(self, graphql_client):
        """Test that billing metrics requires authentication."""
        query = """
            query {
                billingMetrics(period: "30d") {
                    mrr
                    arr
                    activeSubscriptions
                }
            }
        """

        # Create context without user (guest)
        from unittest.mock import MagicMock

        from dotmac.platform.graphql.context import Context

        guest_context = MagicMock(spec=Context)
        guest_context.current_user = None
        guest_context.db = AsyncMock()

        result = await graphql_client.execute(query, context_value=guest_context)

        assert result.errors is not None
        assert "Authentication required" in str(result.errors[0])

    @pytest.mark.asyncio
    async def test_billing_metrics_query_success(self, graphql_client, mock_context):
        """Test successful billing metrics query."""
        query = """
            query {
                billingMetrics(period: "30d") {
                    mrr
                    arr
                    activeSubscriptions
                    totalInvoices
                    paidInvoices
                    overdueInvoices
                    totalPayments
                    successfulPayments
                    failedPayments
                    period
                }
            }
        """

        # Mock the cached service function
        mock_billing_data = {
            "mrr": 5000.0,
            "arr": 60000.0,
            "active_subscriptions": 25,
            "total_invoices": 100,
            "paid_invoices": 85,
            "overdue_invoices": 5,
            "total_payments": 90,
            "successful_payments": 85,
            "failed_payments": 5,
            "total_payment_amount": 42500.0,
            "period": "30d",
            "timestamp": datetime.now(UTC),
        }

        with patch(
            "dotmac.platform.billing.metrics_router._get_billing_metrics_cached",
            return_value=mock_billing_data,
        ):
            result = await graphql_client.execute(query, context_value=mock_context)

        assert result.errors is None
        data = result.data["billingMetrics"]
        assert data["mrr"] == 5000.0
        assert data["arr"] == 60000.0
        assert data["activeSubscriptions"] == 25
        assert data["totalInvoices"] == 100
        assert data["paidInvoices"] == 85

    @pytest.mark.asyncio
    async def test_customer_metrics_query_success(self, graphql_client, mock_context):
        """Test successful customer metrics query."""
        query = """
            query {
                customerMetrics(period: "30d") {
                    totalCustomers
                    activeCustomers
                    newCustomers
                    churnedCustomers
                    customerGrowthRate
                    churnRate
                    retentionRate
                    period
                }
            }
        """

        mock_customer_data = {
            "total_customers": 150,
            "active_customers": 140,
            "new_customers_this_month": 20,
            "churned_customers_this_month": 5,
            "customer_growth_rate": 15.5,
            "churn_rate": 3.3,
            "period": "30d",
            "timestamp": datetime.now(UTC),
        }

        with patch(
            "dotmac.platform.billing.metrics_router._get_customer_metrics_cached",
            return_value=mock_customer_data,
        ):
            result = await graphql_client.execute(query, context_value=mock_context)

        assert result.errors is None
        data = result.data["customerMetrics"]
        assert data["totalCustomers"] == 150
        assert data["activeCustomers"] == 140
        assert data["newCustomers"] == 20
        assert data["churnRate"] == 3.3
        assert data["retentionRate"] == pytest.approx(96.7, 0.1)

    @pytest.mark.asyncio
    async def test_dashboard_overview_query(self, graphql_client, mock_context):
        """Test dashboard overview query - all metrics in one request."""
        query = """
            query {
                dashboardOverview(period: "30d") {
                    billing {
                        mrr
                        arr
                        activeSubscriptions
                    }
                    customers {
                        totalCustomers
                        activeCustomers
                        churnRate
                    }
                    monitoring {
                        errorRate
                        totalRequests
                        successfulRequests
                    }
                }
            }
        """

        mock_billing_data = {
            "mrr": 5000.0,
            "arr": 60000.0,
            "active_subscriptions": 25,
            "total_invoices": 100,
            "paid_invoices": 85,
            "overdue_invoices": 5,
            "total_payments": 90,
            "successful_payments": 85,
            "failed_payments": 5,
            "total_payment_amount": 42500.0,
            "period": "30d",
            "timestamp": datetime.now(UTC),
        }

        mock_customer_data = {
            "total_customers": 150,
            "active_customers": 140,
            "new_customers_this_month": 20,
            "churned_customers_this_month": 5,
            "customer_growth_rate": 15.5,
            "churn_rate": 3.3,
            "period": "30d",
            "timestamp": datetime.now(UTC),
        }

        # Mock database query for monitoring
        from unittest.mock import MagicMock

        mock_row = MagicMock()
        mock_row.total = 1000
        mock_row.critical = 5
        mock_row.warnings = 20
        mock_row.api_requests = 800
        mock_row.user_activities = 150
        mock_row.system_activities = 50

        mock_result = MagicMock()
        mock_result.one.return_value = mock_row
        mock_context.db.execute = AsyncMock(return_value=mock_result)

        with (
            patch(
                "dotmac.platform.billing.metrics_router._get_billing_metrics_cached",
                return_value=mock_billing_data,
            ),
            patch(
                "dotmac.platform.billing.metrics_router._get_customer_metrics_cached",
                return_value=mock_customer_data,
            ),
        ):
            result = await graphql_client.execute(query, context_value=mock_context)

        assert result.errors is None
        data = result.data["dashboardOverview"]

        # Verify billing data
        assert data["billing"]["mrr"] == 5000.0
        assert data["billing"]["arr"] == 60000.0

        # Verify customer data
        assert data["customers"]["totalCustomers"] == 150
        assert data["customers"]["churnRate"] == 3.3

        # Verify monitoring data
        assert data["monitoring"]["totalRequests"] == 1000
        assert data["monitoring"]["successfulRequests"] == 995

    @pytest.mark.asyncio
    async def test_monitoring_metrics_query(self, graphql_client, mock_context):
        """Test monitoring metrics query."""
        query = """
            query {
                monitoringMetrics(period: "24h") {
                    errorRate
                    criticalErrors
                    warningCount
                    totalRequests
                    successfulRequests
                    failedRequests
                    apiRequests
                    period
                }
            }
        """

        # Mock database query
        from unittest.mock import MagicMock

        mock_row = MagicMock()
        mock_row.total = 5000
        mock_row.critical = 10
        mock_row.warnings = 50
        mock_row.api_requests = 4000
        mock_row.user_activities = 800
        mock_row.system_activities = 200

        mock_result = MagicMock()
        mock_result.one.return_value = mock_row
        mock_context.db.execute = AsyncMock(return_value=mock_result)

        result = await graphql_client.execute(query, context_value=mock_context)

        assert result.errors is None
        data = result.data["monitoringMetrics"]
        assert data["totalRequests"] == 5000
        assert data["criticalErrors"] == 10
        assert data["warningCount"] == 50
        assert data["apiRequests"] == 4000
        assert data["period"] == "24h"

    @pytest.mark.asyncio
    async def test_query_with_different_periods(self, graphql_client, mock_context):
        """Test queries with different time periods."""
        query = """
            query GetMetrics($period: String!) {
                billingMetrics(period: $period) {
                    period
                    mrr
                }
            }
        """

        mock_billing_data = {
            "mrr": 5000.0,
            "arr": 60000.0,
            "active_subscriptions": 25,
            "total_invoices": 100,
            "paid_invoices": 85,
            "overdue_invoices": 5,
            "total_payments": 90,
            "successful_payments": 85,
            "failed_payments": 5,
            "total_payment_amount": 42500.0,
            "period": "7d",
            "timestamp": datetime.now(UTC),
        }

        with patch(
            "dotmac.platform.billing.metrics_router._get_billing_metrics_cached",
            return_value=mock_billing_data,
        ):
            # Test with 7 days
            result = await graphql_client.execute(
                query, variable_values={"period": "7d"}, context_value=mock_context
            )
            assert result.errors is None
            assert result.data["billingMetrics"]["period"] == "7d"
