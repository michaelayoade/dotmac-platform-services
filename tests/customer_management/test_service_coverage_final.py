"""
Final coverage tests for CustomerService to reach 90%.
Focus on simple tests for uncovered lines.
"""

import pytest
from datetime import datetime, UTC
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

from dotmac.platform.customer_management.models import (
    Customer,
    CustomerActivity,
    CustomerNote,
    CustomerStatus,
    CustomerTier,
    ActivityType,
)
from dotmac.platform.customer_management.service import CustomerService
from dotmac.platform.customer_management.schemas import CustomerSearchParams


@pytest.fixture
def mock_session():
    """Create a mock async database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def customer_service(mock_session):
    """Create CustomerService instance."""
    return CustomerService(mock_session)


class TestServiceCoverageFinal:
    """Final tests to reach 90% coverage."""

    @pytest.mark.asyncio
    async def test_search_customers_with_all_filters(self, customer_service, mock_session):
        """Test search with all filter combinations."""
        params = CustomerSearchParams(
            query="test",
            status=CustomerStatus.ACTIVE,
            tier=CustomerTier.PREMIUM,
            page=2,
            page_size=20,
            sort_by="lifetime_value",
            sort_order="desc",
        )

        # Mock count
        mock_count = MagicMock()
        mock_count.scalar.return_value = 50

        # Mock customers
        mock_customers = [
            Customer(
                id=uuid4(),
                email=f"test{i}@example.com",
                first_name=f"Test{i}",
                last_name="User",
                status=CustomerStatus.ACTIVE,
                tier=CustomerTier.PREMIUM,
                lifetime_value=Decimal(str(1000 - i * 100)),
            )
            for i in range(20)
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_customers

        mock_session.execute.side_effect = [mock_count, mock_result]

        customers, total = await customer_service.search_customers(params)

        assert len(customers) == 20
        assert total == 50

    @pytest.mark.asyncio
    async def test_search_customers_ascending_sort(self, customer_service, mock_session):
        """Test search with ascending sort order."""
        params = CustomerSearchParams(
            sort_by="created_at",
            sort_order="asc",  # Test ascending branch
            page=1,
            page_size=10,
        )

        mock_count = MagicMock()
        mock_count.scalar.return_value = 5

        mock_customers = []
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_customers

        mock_session.execute.side_effect = [mock_count, mock_result]

        customers, total = await customer_service.search_customers(params)

        assert customers == []
        assert total == 5

    @pytest.mark.asyncio
    async def test_get_customer_activities_with_limit_offset(self, customer_service, mock_session):
        """Test getting activities with pagination."""
        customer_id = uuid4()

        mock_activities = [
            CustomerActivity(
                id=uuid4(),
                customer_id=customer_id,
                activity_type=ActivityType.CREATED,
                title=f"Activity {i}",
                description=f"Description {i}",
            )
            for i in range(5)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_activities
        mock_session.execute.return_value = mock_result

        activities = await customer_service.get_customer_activities(
            customer_id=customer_id,
            limit=5,
            offset=10,
        )

        assert len(activities) == 5

    @pytest.mark.asyncio
    async def test_get_customer_notes_include_internal(self, customer_service, mock_session):
        """Test getting notes with internal flag."""
        customer_id = uuid4()

        # Test with include_internal=False
        external_notes = [
            CustomerNote(
                id=uuid4(),
                customer_id=customer_id,
                subject="External Note",
                content="Content",
                is_internal=False,
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = external_notes
        mock_session.execute.return_value = mock_result

        notes = await customer_service.get_customer_notes(
            customer_id=customer_id,
            include_internal=False,  # Test this branch
            limit=10,
            offset=0,
        )

        assert len(notes) == 1
        assert notes[0].is_internal is False

    @pytest.mark.asyncio
    async def test_batch_process_empty_list(self, customer_service, mock_session):
        """Test batch process with empty customer list."""
        results = await customer_service.batch_process_customers(
            customer_ids=[],
            operation="activate",
            batch_size=10,
        )

        assert results["total_processed"] == 0
        assert results["successful"] == 0
        assert results["failed"] == 0

    @pytest.mark.asyncio
    async def test_batch_process_single_batch(self, customer_service, mock_session):
        """Test batch process with single batch."""
        customer_ids = [uuid4() for _ in range(3)]

        mock_customers = [
            Customer(id=cid, email=f"cust{i}@example.com", first_name=f"Cust{i}", last_name="Test")
            for i, cid in enumerate(customer_ids)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_customers
        mock_session.execute.return_value = mock_result

        results = await customer_service.batch_process_customers(
            customer_ids=customer_ids,
            operation="update_status",
            batch_size=10,  # Larger than list size
        )

        assert results["total_processed"] == 3
        assert results["successful"] == 3

    @pytest.mark.asyncio
    async def test_sort_customers_empty_list(self, customer_service):
        """Test sorting empty customer list."""
        sorted_customers = customer_service.sort_customers([], "created_at")
        assert sorted_customers == []

    @pytest.mark.asyncio
    async def test_sort_customers_single_item(self, customer_service):
        """Test sorting single customer."""
        customer = Customer(
            id=uuid4(),
            email="single@example.com",
            first_name="Single",
            last_name="Customer",
        )

        sorted_customers = customer_service.sort_customers([customer], "email")
        assert len(sorted_customers) == 1
        assert sorted_customers[0] == customer