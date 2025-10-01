"""
Final push to 90% coverage - focused tests for uncovered lines.
"""

import pytest
from datetime import datetime, UTC
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

from dotmac.platform.customer_management.models import (
    Customer,
    CustomerStatus,
    CustomerTier,
    ActivityType,
)
from dotmac.platform.customer_management.service import CustomerService
from dotmac.platform.customer_management.schemas import (
    CustomerCreate,
    CustomerUpdate,
    CustomerSearchParams,
    CustomerActivityCreate,
    CustomerNoteCreate,
)


@pytest.fixture
def mock_session():
    """Create mock async session."""
    session = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.execute = AsyncMock()
    session.refresh = AsyncMock()
    session.rollback = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def service(mock_session):
    """Create service instance."""
    return CustomerService(mock_session)


class TestUncoveredServiceLines:
    """Test uncovered service lines to reach 90%."""

    @pytest.mark.asyncio
    async def test_create_customer_minimum_fields(self, service, mock_session):
        """Test creating customer with minimum required fields only."""
        # Cover lines 48, 51-52 (minimal customer creation)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        data = CustomerCreate(
            email="minimal@example.com",
            first_name="Min",
            last_name="User",
        )

        customer = await service.create_customer(data)

        assert customer.email == "minimal@example.com"
        assert customer.first_name == "Min"
        assert customer.customer_number.startswith("CUST-")
        assert mock_session.add.called

    @pytest.mark.asyncio
    async def test_update_customer_empty_update(self, service, mock_session):
        """Test updating customer with empty update data."""
        # Cover lines 247-248, 251-252, 255-256
        customer_id = uuid4()
        mock_customer = Customer(
            id=customer_id,
            customer_number="CUST-EMPTY",
            email="empty@example.com",
            first_name="Empty",
            last_name="Update",
        )

        with patch.object(service, "get_customer", return_value=mock_customer):
            # Update with no actual changes
            update_data = CustomerUpdate()
            result = await service.update_customer(customer_id, update_data)

            assert result == mock_customer
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_customers_no_filters(self, service, mock_session):
        """Test search with no filters at all."""
        # Cover lines 353, 355, 357, 361
        params = CustomerSearchParams(
            page=1,
            page_size=10,
        )

        mock_count = MagicMock()
        mock_count.scalar.return_value = 0

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_count, mock_result]

        customers, total = await service.search_customers(params)

        assert customers == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_add_activity_minimal(self, service, mock_session):
        """Test adding activity with minimal data."""
        # Cover lines 385-404
        customer_id = uuid4()
        mock_customer = Customer(
            id=customer_id,
            customer_number="CUST-ACT",
            email="activity@example.com",
            first_name="Act",
            last_name="Test",
        )

        with patch.object(service, "get_customer", return_value=mock_customer):
            data = CustomerActivityCreate(
                activity_type=ActivityType.VIEWED,
                title="Page View",
                description="Viewed product",
            )

            activity = await service.add_activity(customer_id, data)

            assert activity.activity_type == ActivityType.VIEWED
            assert activity.title == "Page View"
            mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_note_minimal(self, service, mock_session):
        """Test adding note with minimal data."""
        # Cover lines 414-430
        customer_id = uuid4()
        mock_customer = Customer(
            id=customer_id,
            customer_number="CUST-NOTE",
            email="note@example.com",
            first_name="Note",
            last_name="Test",
        )

        with patch.object(service, "get_customer", return_value=mock_customer):
            data = CustomerNoteCreate(
                subject="Quick Note",
                content="Test content",
            )

            note = await service.add_note(customer_id, data)

            assert note.subject == "Quick Note"
            assert note.content == "Test content"
            mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_activities_basic(self, service, mock_session):
        """Test get activities with basic parameters."""
        # Cover lines 441-473
        customer_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        activities = await service.get_customer_activities(customer_id)

        assert activities == []
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_notes_basic(self, service, mock_session):
        """Test get notes with basic parameters."""
        # Cover lines 482-499
        customer_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        notes = await service.get_customer_notes(customer_id)

        assert notes == []
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_process_activate(self, service, mock_session):
        """Test batch processing with activate operation."""
        # Cover lines 634-664
        customer_ids = [uuid4(), uuid4()]

        mock_customers = [
            Customer(id=customer_ids[0], status=CustomerStatus.INACTIVE),
            Customer(id=customer_ids[1], status=CustomerStatus.INACTIVE),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_customers
        mock_session.execute.return_value = mock_result

        results = await service.batch_process_customers(
            customer_ids,
            "activate",
            batch_size=10
        )

        assert results["total_processed"] == 2
        assert results["successful"] == 2
        assert results["operation"] == "activate"

        # Verify customers were activated
        for customer in mock_customers:
            assert customer.status == CustomerStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_batch_process_deactivate(self, service, mock_session):
        """Test batch processing with deactivate operation."""
        # Cover more of lines 634-664
        customer_ids = [uuid4()]

        mock_customer = Customer(
            id=customer_ids[0],
            status=CustomerStatus.ACTIVE,
            email="test@example.com",
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_customer]
        mock_session.execute.return_value = mock_result

        results = await service.batch_process_customers(
            customer_ids,
            "deactivate",
            batch_size=10
        )

        assert results["total_processed"] == 1
        assert results["successful"] == 1
        assert mock_customer.status == CustomerStatus.INACTIVE

    @pytest.mark.asyncio
    async def test_get_statistics_with_customers(self, service, mock_session):
        """Test get statistics with actual customers."""
        # Cover lines 668-683
        customers = [
            Customer(
                status=CustomerStatus.ACTIVE,
                tier=CustomerTier.PREMIUM,
                lifetime_value=Decimal("1500"),
            ),
            Customer(
                status=CustomerStatus.ACTIVE,
                tier=CustomerTier.STANDARD,
                lifetime_value=Decimal("500"),
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = customers
        mock_session.execute.return_value = mock_result

        stats = await service.get_customer_statistics()

        assert stats["total_customers"] == 2
        assert stats["by_status"]["active"] == 2
        assert stats["by_tier"]["premium"] == 1
        assert stats["by_tier"]["standard"] == 1
        assert stats["total_lifetime_value"] == Decimal("2000")

    @pytest.mark.asyncio
    async def test_sort_customers_by_different_fields(self, service):
        """Test sorting customers by various fields."""
        # Cover lines 687-702
        customers = [
            Customer(
                id=uuid4(),
                email="b@test.com",
                customer_number="CUST-002",
                total_purchases=5,
            ),
            Customer(
                id=uuid4(),
                email="a@test.com",
                customer_number="CUST-001",
                total_purchases=10,
            ),
        ]

        # Sort by email
        sorted_email = service.sort_customers(customers, "email")
        assert sorted_email[0].email == "a@test.com"

        # Sort by customer_number
        sorted_number = service.sort_customers(customers, "customer_number")
        assert sorted_number[0].customer_number == "CUST-001"

        # Sort by total_purchases reverse
        sorted_purchases = service.sort_customers(customers, "total_purchases", reverse=True)
        assert sorted_purchases[0].total_purchases == 10

    @pytest.mark.asyncio
    async def test_search_with_tier_filter(self, service, mock_session):
        """Test search with tier filter."""
        # Cover line 357 specifically
        params = CustomerSearchParams(
            tier=CustomerTier.PREMIUM,
            page=1,
            page_size=10,
        )

        mock_count = MagicMock()
        mock_count.scalar.return_value = 1

        mock_customer = Customer(
            id=uuid4(),
            email="premium@example.com",
            first_name="Premium",
            last_name="Customer",
            tier=CustomerTier.PREMIUM,
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_customer]

        mock_session.execute.side_effect = [mock_count, mock_result]

        customers, total = await service.search_customers(params)

        assert len(customers) == 1
        assert customers[0].tier == CustomerTier.PREMIUM
        assert total == 1