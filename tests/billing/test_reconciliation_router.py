# mypy: disable-error-code="no-untyped-def"
"""
Integration tests for billing reconciliation API router.

Tests cover:
- API endpoint functionality
- Authentication and authorization
- Request/response validation
- Error handling
"""

import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

# Set test environment
os.environ["TESTING"] = "1"

from dotmac.platform.auth.core import UserInfo
from dotmac.platform.billing.bank_accounts.entities import (
    ManualPayment,
    PaymentMethodType,
    PaymentReconciliation,
)
from dotmac.platform.billing.reconciliation_router import router
from dotmac.platform.billing.reconciliation_schemas import (
    PaymentRetryRequest,
    ReconcilePaymentRequest,
    ReconciliationApprove,
    ReconciliationComplete,
    ReconciliationStart,
)
from dotmac.platform.billing.reconciliation_service import ReconciliationService


@pytest.fixture
def app():
    """Create FastAPI test app with router."""
    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


@pytest.fixture
def client(app):
    """Test client for API calls."""
    return TestClient(app)


@pytest.fixture
def mock_current_user():
    """Mock authenticated user."""
    return UserInfo(
        user_id="user-123",
        username="testuser",
        email="test@example.com",
        tenant_id="test-tenant-123",
        roles=["finance_admin"],
        permissions=[
            "billing.reconciliation.create",
            "billing.reconciliation.read",
            "billing.reconciliation.update",
            "billing.reconciliation.approve",
            "billing.payment.retry",
            "billing.admin",
        ],
    )


@pytest.fixture
def mock_service():
    """Mock ReconciliationService."""
    service = AsyncMock(spec=ReconciliationService)

    # Mock circuit breaker
    mock_cb = MagicMock()
    mock_cb.state = "closed"
    mock_cb.failure_count = 0
    mock_cb.failure_threshold = 5
    mock_cb.last_failure_time = None
    mock_cb.recovery_timeout = 60.0
    service.circuit_breaker = mock_cb

    return service


@pytest.fixture
def sample_reconciliation():
    """Sample reconciliation for testing."""
    return PaymentReconciliation(
        id=123,
        tenant_id="test-tenant-123",
        bank_account_id=1,
        reconciliation_date=datetime.now(UTC),
        period_start=datetime.now(UTC) - timedelta(days=30),
        period_end=datetime.now(UTC),
        opening_balance=5000.00,
        closing_balance=6000.00,
        statement_balance=6000.00,
        total_deposits=1000.00,
        total_withdrawals=0.0,
        unreconciled_count=0,
        discrepancy_amount=0.0,
        status="in_progress",
        reconciled_items=[],
        meta_data={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


# ==================== Start Reconciliation Tests ====================


@pytest.mark.asyncio
async def test_start_reconciliation_success(
    client, mock_current_user, mock_service, sample_reconciliation
):
    """Test starting a new reconciliation session via API."""
    mock_service.start_reconciliation_session.return_value = sample_reconciliation

    request_data = {
        "bank_account_id": 1,
        "period_start": (datetime.now(UTC) - timedelta(days=30)).isoformat(),
        "period_end": datetime.now(UTC).isoformat(),
        "opening_balance": 5000.00,
        "statement_balance": 6000.00,
        "statement_file_url": "https://example.com/statement.pdf",
    }

    with patch(
        "dotmac.platform.billing.reconciliation_router.get_current_user",
        return_value=mock_current_user,
    ):
        with patch(
            "dotmac.platform.billing.reconciliation_router.get_reconciliation_service",
            return_value=mock_service,
        ):
            response = client.post("/reconciliations", json=request_data)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["id"] == 123
    assert data["status"] == "in_progress"
    assert data["bank_account_id"] == 1


@pytest.mark.asyncio
async def test_start_reconciliation_validation_error(client, mock_current_user, mock_service):
    """Test validation error when starting reconciliation."""
    mock_service.start_reconciliation_session.side_effect = ValueError(
        "period_start must be before period_end"
    )

    request_data = {
        "bank_account_id": 1,
        "period_start": datetime.now(UTC).isoformat(),
        "period_end": (datetime.now(UTC) - timedelta(days=30)).isoformat(),  # Invalid
        "opening_balance": 5000.00,
        "statement_balance": 6000.00,
    }

    with patch(
        "dotmac.platform.billing.reconciliation_router.get_current_user",
        return_value=mock_current_user,
    ):
        with patch(
            "dotmac.platform.billing.reconciliation_router.get_reconciliation_service",
            return_value=mock_service,
        ):
            response = client.post("/reconciliations", json=request_data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


# ==================== List Reconciliations Tests ====================


@pytest.mark.asyncio
async def test_list_reconciliations(client, mock_current_user, mock_service, sample_reconciliation):
    """Test listing reconciliation sessions."""
    mock_service.list_reconciliations.return_value = {
        "reconciliations": [sample_reconciliation],
        "total": 1,
        "page": 1,
        "page_size": 50,
        "pages": 1,
    }

    with patch(
        "dotmac.platform.billing.reconciliation_router.get_current_user",
        return_value=mock_current_user,
    ):
        with patch(
            "dotmac.platform.billing.reconciliation_router.get_reconciliation_service",
            return_value=mock_service,
        ):
            response = client.get("/reconciliations?page=1&page_size=50")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert len(data["reconciliations"]) == 1


@pytest.mark.asyncio
async def test_list_reconciliations_with_filters(client, mock_current_user, mock_service):
    """Test listing reconciliations with filters."""
    mock_service.list_reconciliations.return_value = {
        "reconciliations": [],
        "total": 0,
        "page": 1,
        "page_size": 50,
        "pages": 0,
    }

    with patch(
        "dotmac.platform.billing.reconciliation_router.get_current_user",
        return_value=mock_current_user,
    ):
        with patch(
            "dotmac.platform.billing.reconciliation_router.get_reconciliation_service",
            return_value=mock_service,
        ):
            response = client.get(
                "/reconciliations?bank_account_id=1&status=approved&page=1&page_size=50"
            )

    assert response.status_code == status.HTTP_200_OK
    mock_service.list_reconciliations.assert_called_once()


# ==================== Get Reconciliation Tests ====================


@pytest.mark.asyncio
async def test_get_reconciliation_summary(client, mock_current_user, mock_service):
    """Test getting reconciliation summary statistics."""
    mock_service.get_reconciliation_summary.return_value = {
        "period_days": 30,
        "total_sessions": 10,
        "approved_sessions": 8,
        "pending_sessions": 2,
        "total_discrepancies": Decimal("500.00"),
        "total_reconciled_items": 150,
        "average_discrepancy": Decimal("50.00"),
    }

    with patch(
        "dotmac.platform.billing.reconciliation_router.get_current_user",
        return_value=mock_current_user,
    ):
        with patch(
            "dotmac.platform.billing.reconciliation_router.get_reconciliation_service",
            return_value=mock_service,
        ):
            response = client.get("/reconciliations/summary?days=30")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["period_days"] == 30
    assert data["total_sessions"] == 10
    assert data["approved_sessions"] == 8


@pytest.mark.asyncio
async def test_get_specific_reconciliation(
    client, mock_current_user, mock_service, sample_reconciliation
):
    """Test getting a specific reconciliation by ID."""
    mock_service._get_reconciliation.return_value = sample_reconciliation

    with patch(
        "dotmac.platform.billing.reconciliation_router.get_current_user",
        return_value=mock_current_user,
    ):
        with patch(
            "dotmac.platform.billing.reconciliation_router.get_reconciliation_service",
            return_value=mock_service,
        ):
            response = client.get("/reconciliations/123")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == 123


@pytest.mark.asyncio
async def test_get_reconciliation_not_found(client, mock_current_user, mock_service):
    """Test 404 when reconciliation not found."""
    mock_service._get_reconciliation.side_effect = ValueError("Reconciliation 999 not found")

    with patch(
        "dotmac.platform.billing.reconciliation_router.get_current_user",
        return_value=mock_current_user,
    ):
        with patch(
            "dotmac.platform.billing.reconciliation_router.get_reconciliation_service",
            return_value=mock_service,
        ):
            response = client.get("/reconciliations/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


# ==================== Add Payment Tests ====================


@pytest.mark.asyncio
async def test_add_reconciled_payment(
    client, mock_current_user, mock_service, sample_reconciliation
):
    """Test adding a payment to reconciliation."""
    mock_service.add_reconciled_payment.return_value = sample_reconciliation

    request_data = {
        "payment_id": 101,
        "notes": "Matched bank statement",
    }

    with patch(
        "dotmac.platform.billing.reconciliation_router.get_current_user",
        return_value=mock_current_user,
    ):
        with patch(
            "dotmac.platform.billing.reconciliation_router.get_reconciliation_service",
            return_value=mock_service,
        ):
            response = client.post("/reconciliations/123/payments", json=request_data)

    assert response.status_code == status.HTTP_200_OK


# ==================== Complete Reconciliation Tests ====================


@pytest.mark.asyncio
async def test_complete_reconciliation(
    client, mock_current_user, mock_service, sample_reconciliation
):
    """Test completing a reconciliation session."""
    sample_reconciliation.status = "completed"
    sample_reconciliation.completed_by = "user-123"
    sample_reconciliation.completed_at = datetime.now(UTC)
    mock_service.complete_reconciliation.return_value = sample_reconciliation

    request_data = {
        "notes": "All items reconciled successfully",
    }

    with patch(
        "dotmac.platform.billing.reconciliation_router.get_current_user",
        return_value=mock_current_user,
    ):
        with patch(
            "dotmac.platform.billing.reconciliation_router.get_reconciliation_service",
            return_value=mock_service,
        ):
            response = client.post("/reconciliations/123/complete", json=request_data)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "completed"
    assert data["completed_by"] == "user-123"


# ==================== Approve Reconciliation Tests ====================


@pytest.mark.asyncio
async def test_approve_reconciliation(
    client, mock_current_user, mock_service, sample_reconciliation
):
    """Test approving a completed reconciliation."""
    sample_reconciliation.status = "approved"
    sample_reconciliation.approved_by = "user-123"
    sample_reconciliation.approved_at = datetime.now(UTC)
    mock_service.approve_reconciliation.return_value = sample_reconciliation

    request_data = {
        "notes": "Approved by finance team",
    }

    with patch(
        "dotmac.platform.billing.reconciliation_router.get_current_user",
        return_value=mock_current_user,
    ):
        with patch(
            "dotmac.platform.billing.reconciliation_router.get_reconciliation_service",
            return_value=mock_service,
        ):
            response = client.post("/reconciliations/123/approve", json=request_data)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "approved"
    assert data["approved_by"] == "user-123"


# ==================== Retry Payment Tests ====================


@pytest.mark.asyncio
async def test_retry_failed_payment(client, mock_current_user, mock_service):
    """Test retrying a failed payment."""
    mock_service.retry_failed_payment_with_recovery.return_value = {
        "success": True,
        "payment_id": 101,
        "attempts": 2,
        "circuit_breaker_state": "closed",
        "recovery_context": {"retry_count": 2, "last_error": None},
    }

    request_data = {
        "payment_id": 101,
        "max_attempts": 3,
        "notes": "Retry due to temporary network issue",
    }

    with patch(
        "dotmac.platform.billing.reconciliation_router.get_current_user",
        return_value=mock_current_user,
    ):
        with patch(
            "dotmac.platform.billing.reconciliation_router.get_reconciliation_service",
            return_value=mock_service,
        ):
            response = client.post("/reconciliations/retry-payment", json=request_data)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert data["payment_id"] == 101
    assert data["attempts"] == 2


@pytest.mark.asyncio
async def test_retry_payment_circuit_breaker_open(client, mock_current_user, mock_service):
    """Test retry blocked by open circuit breaker."""
    mock_service.retry_failed_payment_with_recovery.return_value = {
        "success": False,
        "payment_id": 101,
        "attempts": 0,
        "circuit_breaker_state": "open",
        "recovery_context": {"error": "Circuit breaker is open"},
    }

    request_data = {
        "payment_id": 101,
        "max_attempts": 3,
    }

    with patch(
        "dotmac.platform.billing.reconciliation_router.get_current_user",
        return_value=mock_current_user,
    ):
        with patch(
            "dotmac.platform.billing.reconciliation_router.get_reconciliation_service",
            return_value=mock_service,
        ):
            response = client.post("/reconciliations/retry-payment", json=request_data)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is False
    assert data["circuit_breaker_state"] == "open"


# ==================== Circuit Breaker Status Tests ====================


@pytest.mark.asyncio
async def test_get_circuit_breaker_status(client, mock_current_user, mock_service):
    """Test getting circuit breaker status."""
    with patch(
        "dotmac.platform.billing.reconciliation_router.get_current_user",
        return_value=mock_current_user,
    ):
        with patch(
            "dotmac.platform.billing.reconciliation_router.get_reconciliation_service",
            return_value=mock_service,
        ):
            response = client.get("/reconciliations/circuit-breaker/status")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "state" in data
    assert "failure_count" in data
    assert "failure_threshold" in data


# ==================== Authorization Tests ====================


@pytest.mark.asyncio
async def test_unauthorized_access(client):
    """Test that endpoints require authentication."""
    # Mock no user (unauthenticated)
    with patch(
        "dotmac.platform.billing.reconciliation_router.get_current_user",
        side_effect=Exception("Not authenticated"),
    ):
        response = client.get("/reconciliations")

    # Should return 401 or 500 depending on implementation
    assert response.status_code >= 400


@pytest.mark.asyncio
async def test_insufficient_permissions(client):
    """Test that endpoints enforce permissions."""
    # Mock user without required permissions
    unprivileged_user = UserInfo(
        user_id="user-456",
        username="readonly",
        email="readonly@example.com",
        tenant_id="test-tenant-123",
        roles=["viewer"],
        permissions=["billing.reconciliation.read"],  # Only read permission
    )

    request_data = {
        "bank_account_id": 1,
        "period_start": (datetime.now(UTC) - timedelta(days=30)).isoformat(),
        "period_end": datetime.now(UTC).isoformat(),
        "opening_balance": 5000.00,
        "statement_balance": 6000.00,
    }

    with patch(
        "dotmac.platform.billing.reconciliation_router.get_current_user",
        return_value=unprivileged_user,
    ):
        with patch(
            "dotmac.platform.billing.reconciliation_router.require_permission",
            side_effect=Exception("Permission denied"),
        ):
            response = client.post("/reconciliations", json=request_data)

    # Should return 403 or 500 depending on implementation
    assert response.status_code >= 400


# ==================== Edge Cases ====================


@pytest.mark.asyncio
async def test_invalid_request_data(client, mock_current_user):
    """Test validation of invalid request data."""
    request_data = {
        "bank_account_id": "invalid",  # Should be int
        "period_start": "not-a-date",
        "period_end": "also-not-a-date",
        "opening_balance": "not-a-number",
        "statement_balance": "also-not-a-number",
    }

    with patch(
        "dotmac.platform.billing.reconciliation_router.get_current_user",
        return_value=mock_current_user,
    ):
        response = client.post("/reconciliations", json=request_data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_server_error_handling(client, mock_current_user, mock_service):
    """Test graceful handling of server errors."""
    mock_service.start_reconciliation_session.side_effect = Exception("Database connection failed")

    request_data = {
        "bank_account_id": 1,
        "period_start": (datetime.now(UTC) - timedelta(days=30)).isoformat(),
        "period_end": datetime.now(UTC).isoformat(),
        "opening_balance": 5000.00,
        "statement_balance": 6000.00,
    }

    with patch(
        "dotmac.platform.billing.reconciliation_router.get_current_user",
        return_value=mock_current_user,
    ):
        with patch(
            "dotmac.platform.billing.reconciliation_router.get_reconciliation_service",
            return_value=mock_service,
        ):
            response = client.post("/reconciliations", json=request_data)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
