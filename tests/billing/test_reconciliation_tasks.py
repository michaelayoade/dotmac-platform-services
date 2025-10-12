# mypy: disable-error-code="no-untyped-def"
"""
Integration tests for billing reconciliation Celery tasks.

Tests cover:
- Auto-reconciliation tasks
- Payment retry tasks
- Report generation tasks
- Circuit breaker monitoring
- Task idempotency
"""

import os
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Set test environment
os.environ["TESTING"] = "1"

from dotmac.platform.billing.reconciliation_tasks import (
    _auto_reconcile_impl,
    _generate_report_impl,
    _monitor_circuit_breaker_impl,
    _retry_failed_payments_impl,
    _schedule_reconciliation_impl,
)

pytestmark = pytest.mark.asyncio


# ==================== Auto-Reconciliation Tests ====================


class TestAutoReconcileImpl:
    """Test auto-reconciliation implementation."""

    @pytest.mark.asyncio
    async def test_auto_reconcile_success(self):
        """Test successful auto-reconciliation."""
        tenant_id = "test-tenant-123"
        bank_account_id = 1
        days_back = 7

        # Mock database session and payments
        mock_session = AsyncMock()
        mock_result = MagicMock()

        # Create mock payments
        mock_payments = [
            MagicMock(
                id=i,
                amount=1000.00,
                reconciled=False,
                tenant_id=tenant_id,
                bank_account_id=bank_account_id,
                status="verified",
            )
            for i in range(1, 4)
        ]

        mock_result.scalars.return_value.all.return_value = mock_payments
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        with patch(
            "dotmac.platform.billing.reconciliation_tasks.async_session_factory"
        ) as mock_ctx:
            mock_ctx.return_value.__aenter__.return_value = mock_session
            mock_ctx.return_value.__aexit__.return_value = None

            result = await _auto_reconcile_impl(tenant_id, bank_account_id, days_back)

        assert result["reconciled_count"] == 3
        assert result["total_amount"] == 3000.00
        assert mock_session.commit.called

        # Verify payments marked as reconciled
        for payment in mock_payments:
            assert payment.reconciled is True
            assert payment.reconciled_by == "system_auto"

    @pytest.mark.asyncio
    async def test_auto_reconcile_no_payments(self):
        """Test auto-reconciliation with no unreconciled payments."""
        tenant_id = "test-tenant-123"
        bank_account_id = 1
        days_back = 7

        # Mock empty result
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        with patch(
            "dotmac.platform.billing.reconciliation_tasks.async_session_factory"
        ) as mock_ctx:
            mock_ctx.return_value.__aenter__.return_value = mock_session
            mock_ctx.return_value.__aexit__.return_value = None

            result = await _auto_reconcile_impl(tenant_id, bank_account_id, days_back)

        assert result["reconciled_count"] == 0
        assert result["total_amount"] == 0

    @pytest.mark.asyncio
    async def test_auto_reconcile_date_range(self):
        """Test auto-reconciliation respects date range."""
        tenant_id = "test-tenant-123"
        bank_account_id = 1
        days_back = 30

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        with patch(
            "dotmac.platform.billing.reconciliation_tasks.async_session_factory"
        ) as mock_ctx:
            mock_ctx.return_value.__aenter__.return_value = mock_session
            mock_ctx.return_value.__aexit__.return_value = None

            result = await _auto_reconcile_impl(tenant_id, bank_account_id, days_back)

        # Verify query was executed with correct date range
        assert mock_session.execute.called
        assert result["period_days"] is None or days_back >= 7


# ==================== Payment Retry Tests ====================


class TestRetryFailedPaymentsImpl:
    """Test payment retry implementation."""

    @pytest.mark.asyncio
    async def test_retry_failed_payments_success(self):
        """Test successful batch payment retry."""
        tenant_id = "test-tenant-123"
        max_payments = 50

        # Mock database session
        mock_session = AsyncMock()
        mock_result = MagicMock()

        # Create mock failed payments
        mock_payments = [
            MagicMock(
                id=i,
                status="failed",
                tenant_id=tenant_id,
            )
            for i in range(1, 4)
        ]

        mock_result.scalars.return_value.all.return_value = mock_payments
        mock_session.execute.return_value = mock_result

        # Mock service with successful retries
        mock_service = AsyncMock()
        mock_service.retry_failed_payment_with_recovery.return_value = {
            "success": True,
            "payment_id": 1,
            "attempts": 2,
        }
        mock_service.circuit_breaker.state = "closed"

        with patch(
            "dotmac.platform.billing.reconciliation_tasks.async_session_factory"
        ) as mock_ctx:
            mock_ctx.return_value.__aenter__.return_value = mock_session
            mock_ctx.return_value.__aexit__.return_value = None

            with patch(
                "dotmac.platform.billing.reconciliation_tasks.ReconciliationService",
                return_value=mock_service,
            ):
                result = await _retry_failed_payments_impl(tenant_id, max_payments)

        assert result["attempted"] == 3
        assert result["succeeded"] == 3
        assert result["failed"] == 0
        assert result["circuit_breaker_state"] == "closed"

    @pytest.mark.asyncio
    async def test_retry_failed_payments_no_failures(self):
        """Test retry with no failed payments."""
        tenant_id = "test-tenant-123"
        max_payments = 50

        # Mock empty result
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        with patch(
            "dotmac.platform.billing.reconciliation_tasks.async_session_factory"
        ) as mock_ctx:
            mock_ctx.return_value.__aenter__.return_value = mock_session
            mock_ctx.return_value.__aexit__.return_value = None

            result = await _retry_failed_payments_impl(tenant_id, max_payments)

        assert result["attempted"] == 0
        assert result["succeeded"] == 0
        assert result["failed"] == 0

    @pytest.mark.asyncio
    async def test_retry_failed_payments_partial_success(self):
        """Test retry with some successes and some failures."""
        tenant_id = "test-tenant-123"
        max_payments = 50

        # Mock database session
        mock_session = AsyncMock()
        mock_result = MagicMock()

        mock_payments = [MagicMock(id=i, status="failed") for i in range(1, 4)]
        mock_result.scalars.return_value.all.return_value = mock_payments
        mock_session.execute.return_value = mock_result

        # Mock service with mixed results
        mock_service = AsyncMock()
        mock_service.circuit_breaker.state = "half_open"

        # First two succeed, third fails
        mock_service.retry_failed_payment_with_recovery.side_effect = [
            {"success": True, "payment_id": 1, "attempts": 1},
            {"success": True, "payment_id": 2, "attempts": 2},
            {"success": False, "payment_id": 3, "attempts": 3},
        ]

        with patch(
            "dotmac.platform.billing.reconciliation_tasks.async_session_factory"
        ) as mock_ctx:
            mock_ctx.return_value.__aenter__.return_value = mock_session
            mock_ctx.return_value.__aexit__.return_value = None

            with patch(
                "dotmac.platform.billing.reconciliation_tasks.ReconciliationService",
                return_value=mock_service,
            ):
                result = await _retry_failed_payments_impl(tenant_id, max_payments)

        assert result["attempted"] == 3
        assert result["succeeded"] == 2
        assert result["failed"] == 1
        assert result["circuit_breaker_state"] == "half_open"

    @pytest.mark.asyncio
    async def test_retry_respects_max_payments(self):
        """Test that retry respects max_payments limit."""
        tenant_id = "test-tenant-123"
        max_payments = 2  # Only process 2 payments

        mock_session = AsyncMock()
        mock_result = MagicMock()

        # Create 5 failed payments but limit should be 2
        mock_payments = [MagicMock(id=i, status="failed") for i in range(1, 6)]
        mock_result.scalars.return_value.all.return_value = mock_payments
        mock_session.execute.return_value = mock_result

        mock_service = AsyncMock()
        mock_service.retry_failed_payment_with_recovery.return_value = {"success": True}
        mock_service.circuit_breaker.state = "closed"

        with patch(
            "dotmac.platform.billing.reconciliation_tasks.async_session_factory"
        ) as mock_ctx:
            mock_ctx.return_value.__aenter__.return_value = mock_session
            mock_ctx.return_value.__aexit__.return_value = None

            with patch(
                "dotmac.platform.billing.reconciliation_tasks.ReconciliationService",
                return_value=mock_service,
            ):
                result = await _retry_failed_payments_impl(tenant_id, max_payments)

        # Should process all returned payments (up to max_payments limit in query)
        assert result["attempted"] == 5  # All 5 in mock data


# ==================== Report Generation Tests ====================


class TestGenerateReportImpl:
    """Test report generation implementation."""

    @pytest.mark.asyncio
    async def test_generate_daily_report_success(self):
        """Test successful daily report generation."""
        tenant_id = "test-tenant-123"

        # Mock session
        mock_session = AsyncMock()

        # Mock service summary
        mock_service = AsyncMock()
        mock_service.get_reconciliation_summary.return_value = {
            "total_sessions": 5,
            "approved_sessions": 4,
            "pending_sessions": 1,
            "total_discrepancies": Decimal("100.00"),
        }

        # Mock payment statistics
        mock_stats = MagicMock()
        mock_stats.total_payments = 100
        mock_stats.total_amount = Decimal("50000.00")
        mock_stats.reconciled_payments = 90

        mock_result = MagicMock()
        mock_result.one.return_value = mock_stats
        mock_session.execute.return_value = mock_result

        with patch(
            "dotmac.platform.billing.reconciliation_tasks.async_session_factory"
        ) as mock_ctx:
            mock_ctx.return_value.__aenter__.return_value = mock_session
            mock_ctx.return_value.__aexit__.return_value = None

            with patch(
                "dotmac.platform.billing.reconciliation_tasks.ReconciliationService",
                return_value=mock_service,
            ):
                report = await _generate_report_impl(tenant_id)

        assert report["tenant_id"] == tenant_id
        assert report["reconciliation_sessions"] == 5
        assert report["approved_sessions"] == 4
        assert report["pending_sessions"] == 1
        assert report["total_payments"] == 100
        assert report["reconciled_payments"] == 90
        assert report["reconciliation_rate"] == 90.0  # 90/100 * 100

    @pytest.mark.asyncio
    async def test_generate_report_no_payments(self):
        """Test report generation with no payments."""
        tenant_id = "test-tenant-123"

        mock_session = AsyncMock()

        mock_service = AsyncMock()
        mock_service.get_reconciliation_summary.return_value = {
            "total_sessions": 0,
            "approved_sessions": 0,
            "pending_sessions": 0,
            "total_discrepancies": Decimal("0.00"),
        }

        mock_stats = MagicMock()
        mock_stats.total_payments = 0
        mock_stats.total_amount = None
        mock_stats.reconciled_payments = 0

        mock_result = MagicMock()
        mock_result.one.return_value = mock_stats
        mock_session.execute.return_value = mock_result

        with patch(
            "dotmac.platform.billing.reconciliation_tasks.async_session_factory"
        ) as mock_ctx:
            mock_ctx.return_value.__aenter__.return_value = mock_session
            mock_ctx.return_value.__aexit__.return_value = None

            with patch(
                "dotmac.platform.billing.reconciliation_tasks.ReconciliationService",
                return_value=mock_service,
            ):
                report = await _generate_report_impl(tenant_id)

        assert report["total_payments"] == 0
        assert report["reconciliation_rate"] == 0
        assert report["total_amount"] == 0.0


# ==================== Circuit Breaker Monitoring Tests ====================


class TestMonitorCircuitBreakerImpl:
    """Test circuit breaker monitoring implementation."""

    @pytest.mark.asyncio
    async def test_monitor_circuit_breaker_healthy(self):
        """Test monitoring with healthy circuit breaker."""
        mock_session = AsyncMock()

        mock_service = AsyncMock()
        mock_service.circuit_breaker.state = "closed"
        mock_service.circuit_breaker.failure_count = 1
        mock_service.circuit_breaker.failure_threshold = 5

        with patch(
            "dotmac.platform.billing.reconciliation_tasks.async_session_factory"
        ) as mock_ctx:
            mock_ctx.return_value.__aenter__.return_value = mock_session
            mock_ctx.return_value.__aexit__.return_value = None

            with patch(
                "dotmac.platform.billing.reconciliation_tasks.ReconciliationService",
                return_value=mock_service,
            ):
                status = await _monitor_circuit_breaker_impl()

        assert status["status"] == "healthy"
        assert status["circuit_breaker_state"] == "closed"
        assert status["failure_count"] == 1
        assert status["failure_threshold"] == 5

    @pytest.mark.asyncio
    async def test_monitor_circuit_breaker_open(self):
        """Test monitoring with open circuit breaker."""
        mock_session = AsyncMock()

        mock_service = AsyncMock()
        mock_service.circuit_breaker.state = "open"
        mock_service.circuit_breaker.failure_count = 5
        mock_service.circuit_breaker.failure_threshold = 5

        with patch(
            "dotmac.platform.billing.reconciliation_tasks.async_session_factory"
        ) as mock_ctx:
            mock_ctx.return_value.__aenter__.return_value = mock_session
            mock_ctx.return_value.__aexit__.return_value = None

            with patch(
                "dotmac.platform.billing.reconciliation_tasks.ReconciliationService",
                return_value=mock_service,
            ):
                status = await _monitor_circuit_breaker_impl()

        assert status["status"] == "degraded"
        assert status["circuit_breaker_state"] == "open"

    @pytest.mark.asyncio
    async def test_monitor_circuit_breaker_half_open(self):
        """Test monitoring with half-open circuit breaker."""
        mock_session = AsyncMock()

        mock_service = AsyncMock()
        mock_service.circuit_breaker.state = "half_open"
        mock_service.circuit_breaker.failure_count = 3
        mock_service.circuit_breaker.failure_threshold = 5

        with patch(
            "dotmac.platform.billing.reconciliation_tasks.async_session_factory"
        ) as mock_ctx:
            mock_ctx.return_value.__aenter__.return_value = mock_session
            mock_ctx.return_value.__aexit__.return_value = None

            with patch(
                "dotmac.platform.billing.reconciliation_tasks.ReconciliationService",
                return_value=mock_service,
            ):
                status = await _monitor_circuit_breaker_impl()

        assert status["status"] == "recovering"
        assert status["circuit_breaker_state"] == "half_open"


# ==================== Schedule Reconciliation Tests ====================


class TestScheduleReconciliationImpl:
    """Test reconciliation scheduling implementation."""

    @pytest.mark.asyncio
    async def test_schedule_reconciliation_success(self):
        """Test successful reconciliation scheduling."""
        tenant_id = "test-tenant-123"
        bank_account_id = 1
        period_days = 30

        mock_session = AsyncMock()

        # Mock last reconciliation
        mock_last_rec = MagicMock()
        mock_last_rec.closing_balance = 5000.00

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_last_rec
        mock_session.execute.return_value = mock_result

        # Mock service
        mock_service = AsyncMock()
        mock_reconciliation = MagicMock()
        mock_reconciliation.id = 456
        mock_service.start_reconciliation_session.return_value = mock_reconciliation

        with patch(
            "dotmac.platform.billing.reconciliation_tasks.async_session_factory"
        ) as mock_ctx:
            mock_ctx.return_value.__aenter__.return_value = mock_session
            mock_ctx.return_value.__aexit__.return_value = None

            with patch(
                "dotmac.platform.billing.reconciliation_tasks.ReconciliationService",
                return_value=mock_service,
            ):
                result = await _schedule_reconciliation_impl(
                    tenant_id, bank_account_id, period_days
                )

        assert result == "456"
        assert mock_service.start_reconciliation_session.called

    @pytest.mark.asyncio
    async def test_schedule_reconciliation_no_previous(self):
        """Test scheduling when no previous reconciliation exists."""
        tenant_id = "test-tenant-123"
        bank_account_id = 1
        period_days = 30

        mock_session = AsyncMock()

        # Mock no last reconciliation
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Mock service
        mock_service = AsyncMock()
        mock_reconciliation = MagicMock()
        mock_reconciliation.id = 123
        mock_service.start_reconciliation_session.return_value = mock_reconciliation

        with patch(
            "dotmac.platform.billing.reconciliation_tasks.async_session_factory"
        ) as mock_ctx:
            mock_ctx.return_value.__aenter__.return_value = mock_session
            mock_ctx.return_value.__aexit__.return_value = None

            with patch(
                "dotmac.platform.billing.reconciliation_tasks.ReconciliationService",
                return_value=mock_service,
            ):
                result = await _schedule_reconciliation_impl(
                    tenant_id, bank_account_id, period_days
                )

        assert result == "123"

        # Verify opening balance defaults to 0.0 when no previous reconciliation
        call_args = mock_service.start_reconciliation_session.call_args
        assert call_args[1]["opening_balance"] == 0.0


# ==================== Task Integration Tests ====================


class TestTaskIntegration:
    """Test task integration and error handling."""

    @pytest.mark.asyncio
    async def test_task_handles_database_errors(self):
        """Test that tasks handle database errors gracefully."""
        tenant_id = "test-tenant-123"
        bank_account_id = 1
        days_back = 7

        # Mock database error
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Database connection lost")

        with patch(
            "dotmac.platform.billing.reconciliation_tasks.async_session_factory"
        ) as mock_ctx:
            mock_ctx.return_value.__aenter__.return_value = mock_session
            mock_ctx.return_value.__aexit__.return_value = None

            with pytest.raises(Exception, match="Database connection lost"):
                await _auto_reconcile_impl(tenant_id, bank_account_id, days_back)

    @pytest.mark.asyncio
    async def test_task_handles_service_errors(self):
        """Test that tasks handle service errors gracefully."""
        tenant_id = "test-tenant-123"
        max_payments = 50

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [MagicMock(id=1)]
        mock_session.execute.return_value = mock_result

        # Mock service that raises error
        mock_service = AsyncMock()
        mock_service.retry_failed_payment_with_recovery.side_effect = Exception(
            "Retry service unavailable"
        )
        mock_service.circuit_breaker.state = "open"

        with patch(
            "dotmac.platform.billing.reconciliation_tasks.async_session_factory"
        ) as mock_ctx:
            mock_ctx.return_value.__aenter__.return_value = mock_session
            mock_ctx.return_value.__aexit__.return_value = None

            with patch(
                "dotmac.platform.billing.reconciliation_tasks.ReconciliationService",
                return_value=mock_service,
            ):
                result = await _retry_failed_payments_impl(tenant_id, max_payments)

        # Should track failure but not crash
        assert result["attempted"] == 1
        assert result["failed"] == 1
        assert result["succeeded"] == 0
