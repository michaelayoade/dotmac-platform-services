"""
Shared fixtures for customer management tests.
"""

import pytest
from datetime import datetime, UTC
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.customer_management.models import (
    Customer,
    CustomerStatus,
    CustomerTier,
    CustomerType,
    CommunicationChannel,
)
from dotmac.platform.customer_management.service import CustomerService
from dotmac.platform.auth.core import UserInfo


@pytest.fixture
def mock_session():
    """Create a mock async database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def mock_service():
    """Create a mock customer service."""
    service = AsyncMock(spec=CustomerService)
    return service


@pytest.fixture
def mock_user():
    """Create a mock current user."""
    return UserInfo(
        user_id=str(uuid4()),  # Use valid UUID format
        username="testuser",
        email="test@example.com",
        roles=["user"],
        tenant_id="test-tenant",
    )


@pytest.fixture
def sample_customer():
    """Create a sample customer with all required fields."""
    return Customer(
        id=uuid4(),
        tenant_id="test-tenant",
        customer_number="CUST-001",
        email="customer@example.com",
        first_name="John",
        last_name="Doe",
        phone="+1234567890",
        company_name="Test Corp",
        status=CustomerStatus.ACTIVE,
        tier=CustomerTier.STANDARD,
        customer_type=CustomerType.INDIVIDUAL,
        preferred_channel=CommunicationChannel.EMAIL,
        preferred_language="en",
        timezone="UTC",
        opt_in_marketing=False,
        opt_in_updates=True,
        email_verified=True,
        phone_verified=False,
        lifetime_value=Decimal("1000.00"),
        average_order_value=Decimal("200.00"),
        total_purchases=5,
        risk_score=50,
        acquisition_date=datetime.now(UTC),
        tags=[],
        metadata_={},
        custom_fields={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_customers():
    """Create multiple sample customers for list tests."""
    customers = []
    for i in range(3):
        customer = Customer(
            id=uuid4(),
            tenant_id="test-tenant",
            customer_number=f"CUST-{i+1:03d}",
            email=f"customer{i+1}@example.com",
            first_name=f"Customer{i+1}",
            last_name="Test",
            phone=f"+123456789{i}",
            status=CustomerStatus.ACTIVE,
            tier=CustomerTier.STANDARD,
            customer_type=CustomerType.INDIVIDUAL,
            preferred_channel=CommunicationChannel.EMAIL,
            preferred_language="en",
            timezone="UTC",
            opt_in_marketing=False,
            opt_in_updates=True,
            email_verified=True,
            phone_verified=False,
            lifetime_value=Decimal("1000.00"),
            average_order_value=Decimal("200.00"),
            total_purchases=5,
            risk_score=50,
            acquisition_date=datetime.now(UTC),
            tags=[],
            metadata_={},
            custom_fields={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        customers.append(customer)
    return customers
