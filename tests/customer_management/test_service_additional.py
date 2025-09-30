"""
Additional tests for CustomerService to reach 90% coverage.
Focus on covering the missing lines in service.py.
"""

import pytest
from datetime import datetime, UTC
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4
from sqlalchemy.exc import IntegrityError

from dotmac.platform.customer_management.models import Customer, CustomerStatus, CustomerTier
from dotmac.platform.customer_management.service import CustomerService
from dotmac.platform.customer_management.schemas import (
    CustomerCreate,
    CustomerUpdate,
    CustomerActivityCreate,
    CustomerNoteCreate,
)


@pytest.fixture
def mock_session():
    """Create a mock async database session."""
    session = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def customer_service(mock_session):
    """Create CustomerService instance."""
    return CustomerService(mock_session)


class TestServiceEdgeCases:
    """Test edge cases to cover missing lines."""

    @pytest.mark.asyncio
    async def test_create_customer_with_all_fields(self, customer_service, mock_session):
        """Test creating customer with all optional fields."""
        # Mock customer number check
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        create_data = CustomerCreate(
            email="full@example.com",
            first_name="Full",
            last_name="User",
            phone="+1234567890",
            company_name="Company Inc",
            address_line1="123 Main St",
            address_line2="Apt 4",
            city="New York",
            state="NY",
            postal_code="10001",
            country="US",
            tags=["vip", "premium"],
            metadata={"source": "web"},
            custom_fields={"preference": "email"},
        )

        customer = await customer_service.create_customer(create_data)

        assert customer.email == "full@example.com"
        assert customer.tags == ["vip", "premium"]
        assert customer.metadata == {"source": "web"}
        assert customer.custom_fields == {"preference": "email"}

    @pytest.mark.asyncio
    async def test_create_customer_duplicate_retry(self, customer_service, mock_session):
        """Test customer number generation with multiple retries."""
        # First 5 calls return existing, then None
        mock_results = []
        for _ in range(5):
            mr = MagicMock()
            mr.scalar_one_or_none.return_value = MagicMock()  # Exists
            mock_results.append(mr)

        final_result = MagicMock()
        final_result.scalar_one_or_none.return_value = None  # Available
        mock_results.append(final_result)

        mock_session.execute.side_effect = mock_results

        create_data = CustomerCreate(
            email="retry@example.com",
            first_name="Retry",
            last_name="Test",
        )

        customer = await customer_service.create_customer(create_data)
        assert customer.customer_number.startswith("CUST-")
        assert mock_session.execute.call_count == 6

    @pytest.mark.asyncio
    async def test_update_customer_with_json_fields(self, customer_service, mock_session):
        """Test updating customer with JSON fields."""
        customer = Customer(
            id=uuid4(),
            customer_number="CUST-JSON",
            email="json@example.com",
            first_name="Json",
            last_name="Test",
            tags=["old"],
            metadata={"old": "data"},
        )

        update_data = CustomerUpdate(
            tags=["new", "updated"],
            metadata={"new": "metadata"},
            custom_fields={"preference": "sms"},
        )

        with patch.object(customer_service, "get_customer", return_value=customer):
            result = await customer_service.update_customer(customer.id, update_data)

            assert result == customer
            assert customer.tags == ["new", "updated"]
            assert customer.metadata == {"new": "metadata"}
            assert customer.custom_fields == {"preference": "sms"}

    @pytest.mark.asyncio
    async def test_record_purchase_with_existing_purchases(self, customer_service, mock_session):
        """Test recording purchase with existing purchase history."""
        customer = Customer(
            id=uuid4(),
            customer_number="CUST-PURCHASE",
            email="purchase@example.com",
            first_name="Purchase",
            last_name="Test",
            lifetime_value=Decimal("500.00"),
            total_purchases=3,
            average_order_value=Decimal("166.67"),
            first_purchase_date=datetime(2023, 1, 1, tzinfo=UTC),
            last_purchase_date=datetime(2023, 6, 1, tzinfo=UTC),
        )

        with patch.object(customer_service, "get_customer", return_value=customer):
            await customer_service.record_purchase(customer.id, Decimal("200.00"))

            assert customer.lifetime_value == Decimal("700.00")
            assert customer.total_purchases == 4
            assert customer.average_order_value == Decimal("175.00")
            assert customer.last_purchase_date > datetime(2023, 6, 1, tzinfo=UTC)

    @pytest.mark.asyncio
    async def test_batch_process_with_errors(self, customer_service, mock_session):
        """Test batch processing with some failures."""
        customer_ids = [uuid4() for _ in range(6)]

        # First batch succeeds
        batch1_customers = [
            Customer(id=cid, email=f"batch{i}@example.com", first_name=f"Batch{i}", last_name="Test")
            for i, cid in enumerate(customer_ids[:3])
        ]
        result1 = MagicMock()
        result1.scalars.return_value.all.return_value = batch1_customers

        # Second batch fails
        batch2_customers = [
            Customer(id=cid, email=f"batch{i}@example.com", first_name=f"Batch{i}", last_name="Test")
            for i, cid in enumerate(customer_ids[3:], start=3)
        ]
        result2 = MagicMock()
        result2.scalars.return_value.all.return_value = batch2_customers

        mock_session.execute.side_effect = [result1, result2]
        mock_session.commit.side_effect = [None, IntegrityError("Error", None, None)]

        results = await customer_service.batch_process_customers(
            customer_ids, "deactivate", batch_size=3
        )

        assert results["total_processed"] == 6
        assert results["successful"] == 3
        assert results["failed"] == 3
        assert results["operation"] == "deactivate"

    @pytest.mark.asyncio
    async def test_get_customer_statistics_empty(self, customer_service, mock_session):
        """Test statistics with no customers."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        stats = await customer_service.get_customer_statistics()

        assert stats["total_customers"] == 0
        assert stats["by_status"] == {}
        assert stats["by_tier"] == {}
        assert stats["total_lifetime_value"] == Decimal("0")

    @pytest.mark.asyncio
    async def test_sort_customers_various_fields(self, customer_service):
        """Test sorting by different fields."""
        customers = [
            Customer(
                id=uuid4(),
                email="z@example.com",
                last_name="Zulu",
                total_purchases=5,
                created_at=datetime(2023, 12, 1, tzinfo=UTC),
            ),
            Customer(
                id=uuid4(),
                email="a@example.com",
                last_name="Alpha",
                total_purchases=10,
                created_at=datetime(2023, 1, 1, tzinfo=UTC),
            ),
            Customer(
                id=uuid4(),
                email="m@example.com",
                last_name="Mike",
                total_purchases=2,
                created_at=datetime(2023, 6, 1, tzinfo=UTC),
            ),
        ]

        # Sort by email
        sorted_email = customer_service.sort_customers(customers, "email")
        assert sorted_email[0].email == "a@example.com"
        assert sorted_email[2].email == "z@example.com"

        # Sort by total_purchases descending
        sorted_purchases = customer_service.sort_customers(customers, "total_purchases", reverse=True)
        assert sorted_purchases[0].total_purchases == 10
        assert sorted_purchases[2].total_purchases == 2

        # Sort by last_name
        sorted_name = customer_service.sort_customers(customers, "last_name")
        assert sorted_name[0].last_name == "Alpha"
        assert sorted_name[2].last_name == "Zulu"