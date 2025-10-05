"""
Analytics and metrics GraphQL queries.

Provides GraphQL queries for dashboard data, metrics, and analytics.
Reuses existing REST endpoint logic with caching.
"""

import asyncio
from datetime import UTC, datetime, timedelta

import strawberry
import structlog
from sqlalchemy import select

from dotmac.platform.graphql.context import Context
from dotmac.platform.graphql.types.metrics import (
    BillingMetrics,
    CustomerMetrics,
    DashboardOverview,
    MonitoringMetrics,
)

logger = structlog.get_logger(__name__)


@strawberry.type
class AnalyticsQueries:
    """Analytics and metrics queries optimized for dashboards and charts."""

    @strawberry.field(description="Get billing overview metrics")
    async def billing_metrics(
        self,
        info: strawberry.Info[Context],
        period: str = "30d",
    ) -> BillingMetrics:
        """
        Get billing metrics including MRR, ARR, invoices, and payments.

        Args:
            period: Time period for metrics (e.g., "7d", "30d", "90d")

        Returns:
            BillingMetrics with revenue and payment data
        """
        if not info.context.current_user:
            raise Exception("Authentication required")

        # Parse period to days
        period_days = int(period.replace("d", ""))

        # Reuse existing cached service
        from dotmac.platform.billing.metrics_router import _get_billing_metrics_cached

        result = await _get_billing_metrics_cached(
            period_days=period_days,
            tenant_id=info.context.current_user.tenant_id,
            session=info.context.db,
        )

        return BillingMetrics(**result)

    @strawberry.field(description="Get customer analytics metrics")
    async def customer_metrics(
        self,
        info: strawberry.Info[Context],
        period: str = "30d",
    ) -> CustomerMetrics:
        """
        Get customer metrics including growth, churn, and retention rates.

        Args:
            period: Time period for metrics (e.g., "7d", "30d", "90d")

        Returns:
            CustomerMetrics with customer analytics
        """
        if not info.context.current_user:
            raise Exception("Authentication required")

        period_days = int(period.replace("d", ""))

        # Reuse existing cached service
        from dotmac.platform.billing.metrics_router import _get_customer_metrics_cached

        result = await _get_customer_metrics_cached(
            period_days=period_days,
            tenant_id=info.context.current_user.tenant_id,
            session=info.context.db,
        )

        # Calculate additional fields needed for GraphQL type
        total_value = result.get("active_customers", 0) * 1000  # Placeholder calculation
        avg_value = total_value / max(result.get("total_customers", 1), 1)

        return CustomerMetrics(
            total_customers=result["total_customers"],
            active_customers=result["active_customers"],
            new_customers=result["new_customers_this_month"],
            churned_customers=result["churned_customers_this_month"],
            customer_growth_rate=result["customer_growth_rate"],
            churn_rate=result["churn_rate"],
            retention_rate=100 - result["churn_rate"],
            average_customer_value=avg_value,
            total_customer_value=total_value,
            period=result["period"],
            timestamp=result["timestamp"],
        )

    @strawberry.field(description="Get system monitoring metrics")
    async def monitoring_metrics(
        self,
        info: strawberry.Info[Context],
        period: str = "1h",
    ) -> MonitoringMetrics:
        """
        Get system health and monitoring metrics.

        Args:
            period: Time period for metrics (e.g., "1h", "24h", "7d")

        Returns:
            MonitoringMetrics with system health data
        """
        if not info.context.current_user:
            raise Exception("Authentication required")

        # Calculate period boundaries
        now = datetime.now(UTC)
        if period.endswith("h"):
            hours = int(period.replace("h", ""))
            period_start = now - timedelta(hours=hours)
        else:
            days = int(period.replace("d", ""))
            period_start = now - timedelta(days=days)

        # Query audit logs for monitoring data
        from sqlalchemy import case, func, select

        from dotmac.platform.audit.models import ActivitySeverity, ActivityType, AuditActivity

        # Query activity counts and error rates
        activity_query = select(
            func.count(AuditActivity.id).label("total"),
            func.sum(
                case(
                    (AuditActivity.severity == ActivitySeverity.CRITICAL, 1),
                    else_=0,
                )
            ).label("critical"),
            func.sum(
                case(
                    (AuditActivity.severity == ActivitySeverity.HIGH, 1),
                    else_=0,
                )
            ).label("warnings"),
            func.sum(
                case(
                    (AuditActivity.activity_type == ActivityType.API_REQUEST, 1),
                    else_=0,
                )
            ).label("api_requests"),
            func.sum(
                case(
                    (AuditActivity.activity_type.like("user.%"), 1),
                    else_=0,
                )
            ).label("user_activities"),
            func.sum(
                case(
                    (AuditActivity.activity_type.like("system.%"), 1),
                    else_=0,
                )
            ).label("system_activities"),
        ).where(AuditActivity.created_at >= period_start)

        if info.context.current_user.tenant_id:
            activity_query = activity_query.where(
                AuditActivity.tenant_id == info.context.current_user.tenant_id
            )

        result = await info.context.db.execute(activity_query)
        row = result.one()

        total_requests = row.total or 0
        critical_errors = row.critical or 0
        warnings = row.warnings or 0

        # Calculate error rate
        error_rate = (critical_errors / max(total_requests, 1)) * 100

        # Placeholder performance metrics (would come from OpenTelemetry in production)
        return MonitoringMetrics(
            error_rate=round(error_rate, 2),
            critical_errors=critical_errors,
            warning_count=warnings,
            avg_response_time_ms=125.5,  # Placeholder
            p95_response_time_ms=250.0,  # Placeholder
            p99_response_time_ms=500.0,  # Placeholder
            total_requests=total_requests,
            successful_requests=total_requests - critical_errors,
            failed_requests=critical_errors,
            api_requests=row.api_requests or 0,
            user_activities=row.user_activities or 0,
            system_activities=row.system_activities or 0,
            high_latency_requests=0,  # Placeholder
            timeout_count=0,  # Placeholder
            period=period,
            timestamp=now,
        )

    @strawberry.field(description="Get complete dashboard overview in one query")
    async def dashboard_overview(
        self,
        info: strawberry.Info[Context],
        period: str = "30d",
    ) -> DashboardOverview:
        """
        Get all dashboard metrics in a single optimized query.

        This is the power of GraphQL - fetch all related data in one request
        with parallel execution.

        Args:
            period: Time period for metrics

        Returns:
            DashboardOverview with all metrics
        """
        if not info.context.current_user:
            raise Exception("Authentication required")

        # Parse period to days
        period_days = int(period.replace("d", ""))

        # Reuse existing cached services - fetch in parallel
        from sqlalchemy import case, func

        from dotmac.platform.audit.models import ActivitySeverity, ActivityType, AuditActivity
        from dotmac.platform.billing.metrics_router import (
            _get_billing_metrics_cached,
            _get_customer_metrics_cached,
        )

        # Fetch billing and customer metrics in parallel
        billing_data, customer_data = await asyncio.gather(
            _get_billing_metrics_cached(
                period_days=period_days,
                tenant_id=info.context.current_user.tenant_id,
                session=info.context.db,
            ),
            _get_customer_metrics_cached(
                period_days=period_days,
                tenant_id=info.context.current_user.tenant_id,
                session=info.context.db,
            ),
        )

        # Convert to GraphQL types
        billing = BillingMetrics(**billing_data)

        customer_total_value = customer_data.get("active_customers", 0) * 1000
        customers = CustomerMetrics(
            total_customers=customer_data["total_customers"],
            active_customers=customer_data["active_customers"],
            new_customers=customer_data["new_customers_this_month"],
            churned_customers=customer_data["churned_customers_this_month"],
            customer_growth_rate=customer_data["customer_growth_rate"],
            churn_rate=customer_data["churn_rate"],
            retention_rate=100 - customer_data["churn_rate"],
            average_customer_value=customer_total_value / max(customer_data["total_customers"], 1),
            total_customer_value=customer_total_value,
            period=customer_data["period"],
            timestamp=customer_data["timestamp"],
        )

        # Get monitoring metrics (last 24h)
        from datetime import datetime, timedelta

        now = datetime.now(UTC)
        period_start = now - timedelta(hours=24)

        activity_query = select(
            func.count(AuditActivity.id).label("total"),
            func.sum(case((AuditActivity.severity == ActivitySeverity.CRITICAL, 1), else_=0)).label(
                "critical"
            ),
            func.sum(case((AuditActivity.severity == ActivitySeverity.HIGH, 1), else_=0)).label(
                "warnings"
            ),
            func.sum(
                case((AuditActivity.activity_type == ActivityType.API_REQUEST, 1), else_=0)
            ).label("api_requests"),
            func.sum(case((AuditActivity.activity_type.like("user.%"), 1), else_=0)).label(
                "user_activities"
            ),
            func.sum(case((AuditActivity.activity_type.like("system.%"), 1), else_=0)).label(
                "system_activities"
            ),
        ).where(AuditActivity.created_at >= period_start)

        if info.context.current_user.tenant_id:
            activity_query = activity_query.where(
                AuditActivity.tenant_id == info.context.current_user.tenant_id
            )

        result = await info.context.db.execute(activity_query)
        row = result.one()

        total_requests = row.total or 0
        critical_errors = row.critical or 0
        error_rate = (critical_errors / max(total_requests, 1)) * 100

        monitoring = MonitoringMetrics(
            error_rate=round(error_rate, 2),
            critical_errors=critical_errors,
            warning_count=row.warnings or 0,
            avg_response_time_ms=125.5,
            p95_response_time_ms=250.0,
            p99_response_time_ms=500.0,
            total_requests=total_requests,
            successful_requests=total_requests - critical_errors,
            failed_requests=critical_errors,
            api_requests=row.api_requests or 0,
            user_activities=row.user_activities or 0,
            system_activities=row.system_activities or 0,
            high_latency_requests=0,
            timeout_count=0,
            period="24h",
            timestamp=now,
        )

        return DashboardOverview(
            billing=billing,
            customers=customers,
            monitoring=monitoring,
            analytics=None,
            auth=None,
            communications=None,
            file_storage=None,
        )
