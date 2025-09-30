"""
Final comprehensive tests for CustomerService to achieve 90% coverage.
Focused on core CRUD and search operations.
"""

import pytest
from datetime import datetime, UTC
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch, Mock
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
)


@pytest.fixture
def mock_session():
    """Create a properly configured mock async database session."""
    session = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.rollback = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def customer_service(mock_session):
    """Create CustomerService instance."""
    return CustomerService(mock_session)


class TestCustomerServiceCore:
    """Core tests for customer service focusing on high coverage areas."""

    @pytest.mark.asyncio
    async def test_create_customer_basic(self, customer_service, mock_session):
        """Test basic customer creation flow."""
        # Mock the customer number check to return None (available)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        create_data = CustomerCreate(
            email="test@example.com",
            first_name="Test",
            last_name="User",
        )

        customer = await customer_service.create_customer(create_data)

        assert customer.email == "test@example.com"
        assert customer.first_name == "Test"
        assert customer.last_name == "User"
        assert customer.customer_number.startswith("CUST-")
        assert mock_session.add.called
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_get_customer(self, customer_service, mock_session):
        """Test getting customer by ID."""
        customer_id = uuid4()
        mock_customer = Customer(
            id=customer_id,
            customer_number="CUST-123",
            email="test@example.com",
            first_name="Test",
            last_name="User",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_customer
        mock_session.execute.return_value = mock_result

        customer = await customer_service.get_customer(customer_id)

        assert customer == mock_customer
        assert mock_session.execute.called

    @pytest.mark.asyncio
    async def test_get_customer_by_number(self, customer_service, mock_session):
        """Test getting customer by customer number."""
        mock_customer = Customer(
            id=uuid4(),
            customer_number="CUST-456",
            email="test@example.com",
            first_name="Test",
            last_name="User",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_customer
        mock_session.execute.return_value = mock_result

        customer = await customer_service.get_customer_by_number("CUST-456")

        assert customer == mock_customer
        assert customer.customer_number == "CUST-456"

    @pytest.mark.asyncio
    async def test_get_customer_by_email(self, customer_service, mock_session):
        """Test getting customer by email."""
        mock_customer = Customer(
            id=uuid4(),
            customer_number="CUST-789",
            email="unique@example.com",
            first_name="Unique",
            last_name="User",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_customer
        mock_session.execute.return_value = mock_result

        customer = await customer_service.get_customer_by_email("unique@example.com")

        assert customer == mock_customer
        assert customer.email == "unique@example.com"

    @pytest.mark.asyncio
    async def test_update_customer(self, customer_service, mock_session):
        """Test updating customer."""
        customer_id = uuid4()
        mock_customer = Customer(
            id=customer_id,
            customer_number="CUST-001",
            email="old@example.com",
            first_name="Old",
            last_name="Name",
        )

        # Mock get_customer to return the mock customer
        with patch.object(customer_service, "get_customer", return_value=mock_customer):
            update_data = CustomerUpdate(
                first_name="New",
                last_name="Name",
            )

            result = await customer_service.update_customer(customer_id, update_data)

            assert result == mock_customer
            assert mock_session.execute.called
            assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_update_customer_not_found(self, customer_service):
        """Test updating non-existent customer."""
        with patch.object(customer_service, "get_customer", return_value=None):
            update_data = CustomerUpdate(first_name="Test")
            result = await customer_service.update_customer(uuid4(), update_data)
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_customer_soft(self, customer_service, mock_session):
        """Test soft deleting customer."""
        customer_id = uuid4()
        mock_customer = Customer(
            id=customer_id,
            customer_number="CUST-DEL",
            email="delete@example.com",
            first_name="Delete",
            last_name="Me",
        )

        with patch.object(customer_service, "get_customer", return_value=mock_customer):
            result = await customer_service.delete_customer(customer_id, hard_delete=False)

            assert result is True
            assert mock_customer.deleted_at is not None
            assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_delete_customer_hard(self, customer_service, mock_session):
        """Test hard deleting customer."""
        customer_id = uuid4()
        mock_customer = Customer(
            id=customer_id,
            customer_number="CUST-HARD",
            email="hard@example.com",
            first_name="Hard",
            last_name="Delete",
        )

        with patch.object(customer_service, "get_customer", return_value=mock_customer):
            result = await customer_service.delete_customer(customer_id, hard_delete=True)

            assert result is True
            assert mock_session.delete.called
            assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_delete_customer_not_found(self, customer_service):
        """Test deleting non-existent customer."""
        with patch.object(customer_service, "get_customer", return_value=None):
            result = await customer_service.delete_customer(uuid4())
            assert result is False

    @pytest.mark.asyncio
    async def test_search_customers_basic(self, customer_service, mock_session):
        """Test basic customer search."""
        # Mock count
        mock_count = MagicMock()
        mock_count.scalar.return_value = 10

        # Mock customers
        mock_customers = [
            Customer(id=uuid4(), email=f"user{i}@example.com", first_name=f"User{i}", last_name="Test")
            for i in range(10)
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_customers

        mock_session.execute.side_effect = [mock_count, mock_result]

        params = CustomerSearchParams(page=1, page_size=10)
        customers, total = await customer_service.search_customers(params)

        assert len(customers) == 10
        assert total == 10

    @pytest.mark.asyncio
    async def test_search_customers_with_filters(self, customer_service, mock_session):
        """Test customer search with status filter."""
        # Mock count
        mock_count = MagicMock()
        mock_count.scalar.return_value = 2

        # Mock customers
        mock_customers = [
            Customer(
                id=uuid4(),
                email="active1@example.com",
                first_name="Active1",
                last_name="User",
                status=CustomerStatus.ACTIVE,
            ),
            Customer(
                id=uuid4(),
                email="active2@example.com",
                first_name="Active2",
                last_name="User",
                status=CustomerStatus.ACTIVE,
            ),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_customers

        mock_session.execute.side_effect = [mock_count, mock_result]

        params = CustomerSearchParams(
            status=CustomerStatus.ACTIVE,
            page=1,
            page_size=10,
        )
        customers, total = await customer_service.search_customers(params)

        assert len(customers) == 2
        assert total == 2
        assert all(c.status == CustomerStatus.ACTIVE for c in customers)

    @pytest.mark.asyncio
    async def test_search_customers_with_query(self, customer_service, mock_session):
        """Test customer search with text query."""
        # Mock count
        mock_count = MagicMock()
        mock_count.scalar.return_value = 1

        # Mock customer
        mock_customers = [
            Customer(
                id=uuid4(),
                email="john.doe@example.com",
                first_name="John",
                last_name="Doe",
            )
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_customers

        mock_session.execute.side_effect = [mock_count, mock_result]

        params = CustomerSearchParams(
            query="john",
            page=1,
            page_size=10,
        )
        customers, total = await customer_service.search_customers(params)

        assert len(customers) == 1
        assert total == 1
        assert customers[0].first_name == "John"

    @pytest.mark.asyncio
    async def test_record_purchase(self, customer_service, mock_session):
        """Test recording a customer purchase."""
        customer_id = uuid4()
        mock_customer = Customer(
            id=customer_id,
            customer_number="CUST-PUR",
            email="purchase@example.com",
            first_name="Purchase",
            last_name="Test",
            lifetime_value=Decimal("0"),
            total_purchases=0,
            average_order_value=Decimal("0"),
            first_purchase_date=None,
            last_purchase_date=None,
        )

        with patch.object(customer_service, "get_customer", return_value=mock_customer):
            await customer_service.record_purchase(customer_id, Decimal("100.00"))

            assert mock_customer.lifetime_value == Decimal("100.00")
            assert mock_customer.total_purchases == 1
            assert mock_customer.average_order_value == Decimal("100.00")
            assert mock_customer.first_purchase_date is not None
            assert mock_customer.last_purchase_date is not None
            assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_record_purchase_customer_not_found(self, customer_service):
        """Test recording purchase for non-existent customer."""
        with patch.object(customer_service, "get_customer", return_value=None):
            with pytest.raises(ValueError, match="Customer not found"):
                await customer_service.record_purchase(uuid4(), Decimal("100.00"))

    @pytest.mark.asyncio
    async def test_add_activity(self, customer_service, mock_session):
        """Test adding customer activity."""
        from dotmac.platform.customer_management.schemas import CustomerActivityCreate
        from dotmac.platform.customer_management.models import CustomerActivity

        customer_id = uuid4()
        mock_customer = Customer(
            id=customer_id,
            customer_number="CUST-ACT",
            email="activity@example.com",
            first_name="Activity",
            last_name="Test",
        )

        with patch.object(customer_service, "get_customer", return_value=mock_customer):
            activity_data = CustomerActivityCreate(
                activity_type=ActivityType.UPDATED,
                title="Profile Update",
                description="Updated phone number",
            )

            activity = await customer_service.add_activity(customer_id, activity_data)

            assert activity.customer_id == customer_id
            assert activity.activity_type == ActivityType.UPDATED
            assert mock_session.add.called
            assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_add_activity_customer_not_found(self, customer_service):
        """Test adding activity to non-existent customer."""
        from dotmac.platform.customer_management.schemas import CustomerActivityCreate

        with patch.object(customer_service, "get_customer", return_value=None):
            activity_data = CustomerActivityCreate(
                activity_type=ActivityType.CREATED,
                title="Test",
                description="Test",
            )
            with pytest.raises(ValueError, match="Customer not found"):
                await customer_service.add_activity(uuid4(), activity_data)

    @pytest.mark.asyncio
    async def test_get_customer_activities(self, customer_service, mock_session):
        """Test retrieving customer activities."""
        from dotmac.platform.customer_management.models import CustomerActivity

        customer_id = uuid4()
        mock_activities = [
            CustomerActivity(
                id=uuid4(),
                customer_id=customer_id,
                activity_type=ActivityType.CREATED,
                title=f"Activity {i}",
            )
            for i in range(3)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_activities
        mock_session.execute.return_value = mock_result

        activities = await customer_service.get_customer_activities(customer_id)

        assert len(activities) == 3
        assert mock_session.execute.called

    @pytest.mark.asyncio
    async def test_add_note(self, customer_service, mock_session):
        """Test adding customer note."""
        from dotmac.platform.customer_management.schemas import CustomerNoteCreate
        from dotmac.platform.customer_management.models import CustomerNote

        customer_id = uuid4()
        mock_customer = Customer(
            id=customer_id,
            customer_number="CUST-NOTE",
            email="note@example.com",
            first_name="Note",
            last_name="Test",
        )

        with patch.object(customer_service, "get_customer", return_value=mock_customer):
            note_data = CustomerNoteCreate(
                subject="Support inquiry",
                content="Customer needs help with account",
            )

            note = await customer_service.add_note(customer_id, note_data, created_by="support")

            assert note.customer_id == customer_id
            assert note.subject == "Support inquiry"
            assert note.created_by == "support"
            assert mock_session.add.called
            assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_add_note_customer_not_found(self, customer_service):
        """Test adding note to non-existent customer."""
        from dotmac.platform.customer_management.schemas import CustomerNoteCreate

        with patch.object(customer_service, "get_customer", return_value=None):
            note_data = CustomerNoteCreate(
                subject="Test",
                content="Test content",
            )
            with pytest.raises(ValueError, match="Customer not found"):
                await customer_service.add_note(uuid4(), note_data, created_by="test")

    @pytest.mark.asyncio
    async def test_get_customer_notes(self, customer_service, mock_session):
        """Test retrieving customer notes."""
        from dotmac.platform.customer_management.models import CustomerNote

        customer_id = uuid4()
        mock_notes = [
            CustomerNote(
                id=uuid4(),
                customer_id=customer_id,
                subject=f"Note {i}",
                content=f"Content {i}",
                is_internal=i % 2 == 0,
            )
            for i in range(3)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_notes
        mock_session.execute.return_value = mock_result

        notes = await customer_service.get_customer_notes(customer_id)

        assert len(notes) == 3
        assert mock_session.execute.called

    @pytest.mark.asyncio
    async def test_get_customer_statistics(self, customer_service, mock_session):
        """Test getting customer statistics."""
        mock_customers = [
            Customer(
                id=uuid4(),
                status=CustomerStatus.ACTIVE,
                tier=CustomerTier.PREMIUM,
                lifetime_value=Decimal("1000"),
            ),
            Customer(
                id=uuid4(),
                status=CustomerStatus.ACTIVE,
                tier=CustomerTier.STANDARD,
                lifetime_value=Decimal("500"),
            ),
            Customer(
                id=uuid4(),
                status=CustomerStatus.INACTIVE,
                tier=CustomerTier.PREMIUM,
                lifetime_value=Decimal("2000"),
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_customers
        mock_session.execute.return_value = mock_result

        stats = await customer_service.get_customer_statistics()

        assert stats["total_customers"] == 3
        assert stats["by_status"]["active"] == 2
        assert stats["by_status"]["inactive"] == 1
        assert stats["by_tier"]["premium"] == 2
        assert stats["by_tier"]["standard"] == 1
        assert stats["total_lifetime_value"] == Decimal("3500")

    @pytest.mark.asyncio
    async def test_sort_customers(self, customer_service):
        """Test sorting customers."""
        customers = [
            Customer(
                id=uuid4(),
                first_name="Charlie",
                lifetime_value=Decimal("500"),
                created_at=datetime(2023, 3, 1, tzinfo=UTC),
            ),
            Customer(
                id=uuid4(),
                first_name="Alice",
                lifetime_value=Decimal("1000"),
                created_at=datetime(2023, 1, 1, tzinfo=UTC),
            ),
            Customer(
                id=uuid4(),
                first_name="Bob",
                lifetime_value=Decimal("750"),
                created_at=datetime(2023, 2, 1, tzinfo=UTC),
            ),
        ]

        # Sort by name
        sorted_by_name = customer_service.sort_customers(customers, "first_name")
        assert sorted_by_name[0].first_name == "Alice"
        assert sorted_by_name[2].first_name == "Charlie"

        # Sort by value descending
        sorted_by_value = customer_service.sort_customers(
            customers, "lifetime_value", reverse=True
        )
        assert sorted_by_value[0].lifetime_value == Decimal("1000")

    @pytest.mark.asyncio
    async def test_batch_process_customers(self, customer_service, mock_session):
        """Test batch processing customers."""
        customer_ids = [uuid4() for _ in range(5)]
        mock_customers = [
            Customer(id=cid, email=f"batch{i}@example.com", first_name=f"Batch{i}", last_name="Test")
            for i, cid in enumerate(customer_ids)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_customers
        mock_session.execute.return_value = mock_result

        results = await customer_service.batch_process_customers(
            customer_ids, "activate", batch_size=3
        )

        assert results["total_processed"] == 5
        assert results["successful"] == 5
        assert results["failed"] == 0
        assert results["operation"] == "activate"