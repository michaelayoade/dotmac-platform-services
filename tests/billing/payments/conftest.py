"""
Fixtures for payment service and router tests.
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from tests.fixtures.async_db import create_mock_async_result, create_mock_async_session

from dotmac.platform.main import app
from dotmac.platform.auth.core import UserInfo
from dotmac.platform.billing.core.entities import (
    PaymentEntity,
    PaymentMethodEntity,
)
from dotmac.platform.billing.core.enums import (
    PaymentMethodStatus,
    PaymentMethodType,
    PaymentStatus,
)
from dotmac.platform.billing.payments.providers import (
    PaymentProvider,
    PaymentResult,
    RefundResult,
)
from dotmac.platform.billing.payments.service import PaymentService


# Helper functions
def setup_mock_db_result(mock_db_session, scalar_value=None, scalars_values=None):
    """Helper to setup mock database result using proper async patterns"""
    if scalars_values is not None:
        mock_result = create_mock_async_result(scalars_values)
    elif scalar_value is not None:
        mock_result = create_mock_async_result([scalar_value])
        # For scalar queries, configure scalar methods
        mock_result.scalar_one_or_none = MagicMock(return_value=scalar_value)
    else:
        mock_result = create_mock_async_result([])

    mock_db_session.execute = AsyncMock(return_value=mock_result)
    return mock_result


def setup_mock_refresh(mock_db_session):
    """Helper to setup mock refresh that populates required entity fields"""

    async def mock_refresh(entity):
        now = datetime.now(timezone.utc)
        # Set required fields for PaymentEntity
        if hasattr(entity, "payment_id"):
            if not getattr(entity, "payment_id", None):
                entity.payment_id = "payment_123"
            if not getattr(entity, "created_at", None):
                entity.created_at = now
            if not getattr(entity, "updated_at", None):
                entity.updated_at = now
            if not hasattr(entity, "retry_count") or entity.retry_count is None:
                entity.retry_count = 0
            if not hasattr(entity, "extra_data") or entity.extra_data is None:
                entity.extra_data = {}
        # Set required fields for PaymentMethodEntity
        if hasattr(entity, "payment_method_id"):
            if not getattr(entity, "payment_method_id", None):
                entity.payment_method_id = "pm_123"
            if not getattr(entity, "created_at", None):
                entity.created_at = now
            if not getattr(entity, "updated_at", None):
                entity.updated_at = now
            if not hasattr(entity, "extra_data") or entity.extra_data is None:
                entity.extra_data = {}

    mock_db_session.refresh = AsyncMock(side_effect=mock_refresh)
    return mock_db_session


# Service fixtures
@pytest.fixture
def mock_payment_db_session():
    """Create a mock async database session using proper async patterns"""
    return create_mock_async_session()


@pytest.fixture
def mock_payment_provider():
    """Create a mock payment provider"""
    provider = AsyncMock(spec=PaymentProvider)

    # Default successful charge response
    provider.charge_payment_method = AsyncMock(
        return_value=PaymentResult(
            success=True,
            provider_payment_id="provider_payment_123",
            provider_fee=29,  # $1.00 payment = 2.9% fee
        )
    )

    # Default successful refund response
    provider.refund_payment = AsyncMock(
        return_value=RefundResult(
            success=True,
            provider_refund_id="provider_refund_456",
        )
    )

    return provider


@pytest.fixture
def payment_service(mock_payment_db_session, mock_payment_provider):
    """Create PaymentService instance with mock dependencies"""
    return PaymentService(
        db_session=mock_payment_db_session, payment_providers={"stripe": mock_payment_provider}
    )


@pytest.fixture
def sample_payment_entity():
    """Create a sample payment entity"""
    now = datetime.now(timezone.utc)
    payment = MagicMock(spec=PaymentEntity)
    payment.tenant_id = "test-tenant"
    payment.payment_id = "payment_123"
    payment.amount = 1000
    payment.currency = "USD"
    payment.customer_id = "customer_456"
    payment.status = PaymentStatus.SUCCEEDED
    payment.provider = "stripe"
    payment.provider_payment_id = "provider_payment_123"
    payment.payment_method_type = PaymentMethodType.CARD
    payment.payment_method_details = {
        "payment_method_id": "pm_789",
        "last_four": "4242",
        "brand": "visa",
    }
    payment.retry_count = 0
    payment.extra_data = {}
    payment.created_at = now
    payment.updated_at = now
    payment.processed_at = now
    payment.idempotency_key = None
    payment.provider_fee = None
    payment.failure_reason = None
    payment.next_retry_at = None
    return payment


@pytest.fixture
def sample_payment_method_entity():
    """Create a sample payment method entity"""
    now = datetime.now(timezone.utc)
    payment_method = MagicMock(spec=PaymentMethodEntity)
    payment_method.tenant_id = "test-tenant"
    payment_method.payment_method_id = "pm_789"
    payment_method.customer_id = "customer_456"
    payment_method.type = PaymentMethodType.CARD
    payment_method.status = PaymentMethodStatus.ACTIVE
    payment_method.provider = "stripe"
    payment_method.provider_payment_method_id = "stripe_pm_123"
    payment_method.display_name = "Visa ending in 4242"
    payment_method.last_four = "4242"
    payment_method.brand = "visa"
    payment_method.expiry_month = 12
    payment_method.expiry_year = 2025
    payment_method.is_default = True
    payment_method.is_active = True
    payment_method.created_at = now
    payment_method.updated_at = now
    payment_method.deleted_at = None
    payment_method.bank_name = None
    payment_method.account_type = None
    payment_method.routing_number_last_four = None
    payment_method.auto_pay_enabled = False
    payment_method.verified_at = now
    payment_method.extra_data = {}
    payment_method.events = []  # Fix for event publishing
    return payment_method


# Router fixtures
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
        permissions=["payments:read", "payments:write"],
        tenant_id="test-tenant-123",
    )

    with patch("dotmac.platform.auth.dependencies.get_current_user", return_value=mock_user):
        yield mock_user


@pytest.fixture
def mock_tenant_dependency():
    """Mock tenant context dependency."""
    with patch("dotmac.platform.tenant.get_current_tenant_id", return_value="test-tenant-123"):
        yield "test-tenant-123"
