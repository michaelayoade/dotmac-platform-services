"""
Comprehensive tests for customer management service.

Tests all customer service functionality including:
- Customer CRUD operations
- Search and filtering
- Activity tracking
- Notes management
- Metrics and scoring
- Error handling and edge cases
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.customer_management.models import (
    ActivityType,
    Customer,
    CustomerActivity,
    CustomerNote,
    CustomerSegment,
    CustomerStatus,
    CustomerTier,
    CustomerType,
)
from dotmac.platform.customer_management.schemas import (
    CustomerActivityCreate,
    CustomerCreate,
    CustomerNoteCreate,
    CustomerSearchParams,
    CustomerSegmentCreate,
    CustomerUpdate,
)
from dotmac.platform.customer_management.service import CustomerService


@pytest.fixture
async def customer_service(async_db_session: AsyncSession) -> CustomerService:
    """Create customer service instance."""
    return CustomerService(async_db_session)


@pytest.fixture
def sample_customer_data() -> dict:
    """Sample customer data for testing."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "customer_type": CustomerType.INDIVIDUAL,
        "tier": CustomerTier.BASIC,
        "address_line1": "123 Main St",
        "city": "Anytown",
        "state_province": "CA",
        "postal_code": "12345",
        "country": "US",
        "tags": ["new", "priority"],
        "metadata": {"source": "web"},
        "custom_fields": {"referred_by": "friend"},
    }


@pytest.fixture
async def sample_customer(
    customer_service: CustomerService, sample_customer_data: dict
) -> Customer:
    """Create a sample customer for testing."""
    customer_data = CustomerCreate(**sample_customer_data)
    customer = await customer_service.create_customer(
        data=customer_data, created_by="test-user"
    )
    return customer


class TestCustomerCRUDOperations:
    """Test basic CRUD operations for customers."""

    @pytest.mark.asyncio
    async def test_create_customer_success(
        self, customer_service: CustomerService, sample_customer_data: dict
    ):
        """Test successful customer creation."""
        customer_data = CustomerCreate(**sample_customer_data)
        customer = await customer_service.create_customer(
            data=customer_data, created_by="test-user"
        )

        assert customer.first_name == "John"
        assert customer.last_name == "Doe"
        assert customer.email == "john.doe@example.com"
        assert customer.customer_type == CustomerType.INDIVIDUAL
        assert customer.tier == CustomerTier.BASIC
        assert customer.tags == ["new", "priority"]
        assert customer.metadata_["source"] == "web"
        assert customer.custom_fields["referred_by"] == "friend"
        assert customer.customer_number is not None

    @pytest.mark.asyncio
    async def test_create_customer_generates_number(
        self, customer_service: CustomerService, sample_customer_data: dict
    ):
        """Test that customer number is automatically generated."""
        customer_data = CustomerCreate(**sample_customer_data)
        customer1 = await customer_service.create_customer(
            data=customer_data, created_by="test-user"
        )

        # Create another customer
        sample_customer_data["email"] = "jane.doe@example.com"
        customer_data2 = CustomerCreate(**sample_customer_data)
        customer2 = await customer_service.create_customer(
            data=customer_data2, created_by="test-user"
        )

        assert customer1.customer_number != customer2.customer_number
        assert len(customer1.customer_number) > 0
        assert len(customer2.customer_number) > 0

    @pytest.mark.asyncio
    async def test_create_customer_creates_activity(
        self, customer_service: CustomerService, async_db_session: AsyncSession
    ):
        """Test that creating a customer creates an initial activity."""
        customer_data = CustomerCreate(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
        )
        customer = await customer_service.create_customer(
            data=customer_data, created_by="test-user"
        )

        # Check that an activity was created
        result = await async_db_session.execute(
            select(CustomerActivity).where(
                CustomerActivity.customer_id == customer.id
            )
        )
        activities = result.scalars().all()

        assert len(activities) == 1
        assert activities[0].activity_type == ActivityType.CREATED
        assert activities[0].title == "Customer created"

    @pytest.mark.asyncio
    async def test_get_customer_by_id(
        self, customer_service: CustomerService, sample_customer: Customer
    ):
        """Test retrieving customer by ID."""
        retrieved = await customer_service.get_customer(
            customer_id=sample_customer.id
        )

        assert retrieved is not None
        assert retrieved.id == sample_customer.id
        assert retrieved.first_name == sample_customer.first_name
        assert retrieved.email == sample_customer.email

    @pytest.mark.asyncio
    async def test_get_customer_not_found(self, customer_service: CustomerService):
        """Test retrieving non-existent customer."""
        non_existent_id = uuid4()
        customer = await customer_service.get_customer(
            customer_id=non_existent_id
        )

        assert customer is None

    @pytest.mark.asyncio
    async def test_get_customer_by_number(
        self, customer_service: CustomerService, sample_customer: Customer
    ):
        """Test retrieving customer by customer number."""
        retrieved = await customer_service.get_customer_by_number(
            sample_customer.customer_number
        )

        assert retrieved is not None
        assert retrieved.id == sample_customer.id
        assert retrieved.customer_number == sample_customer.customer_number

    @pytest.mark.asyncio
    async def test_get_customer_by_email(
        self, customer_service: CustomerService, sample_customer: Customer
    ):
        """Test retrieving customer by email."""
        retrieved = await customer_service.get_customer_by_email(
            sample_customer.email
        )

        assert retrieved is not None
        assert retrieved.id == sample_customer.id
        assert retrieved.email == sample_customer.email

    @pytest.mark.asyncio
    async def test_update_customer_success(
        self, customer_service: CustomerService, sample_customer: Customer
    ):
        """Test successful customer update."""
        update_data = CustomerUpdate(
            first_name="Jane",
            phone="+9876543210",
            tier=CustomerTier.PREMIUM,
            metadata={"updated": True},
        )

        updated_customer = await customer_service.update_customer(
            customer_id=sample_customer.id,
            data=update_data,
            updated_by="test-user",
        )

        assert updated_customer is not None
        assert updated_customer.first_name == "Jane"
        assert updated_customer.phone == "+9876543210"
        assert updated_customer.tier == CustomerTier.PREMIUM
        assert updated_customer.metadata_["updated"] is True

    @pytest.mark.asyncio
    async def test_update_customer_not_found(self, customer_service: CustomerService):
        """Test updating non-existent customer."""
        non_existent_id = uuid4()
        update_data = CustomerUpdate(first_name="Jane")

        result = await customer_service.update_customer(
            customer_id=non_existent_id,
            data=update_data,
            updated_by="test-user",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_customer_soft_delete(
        self, customer_service: CustomerService, sample_customer: Customer
    ):
        """Test soft delete of customer."""
        success = await customer_service.delete_customer(
            customer_id=sample_customer.id,
            hard_delete=False,
        )

        assert success is True

        # Customer should not be returned in regular queries
        retrieved = await customer_service.get_customer(
            customer_id=sample_customer.id
        )
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_customer_hard_delete(
        self,
        customer_service: CustomerService,
        sample_customer: Customer,
        async_db_session: AsyncSession,
    ):
        """Test hard delete of customer."""
        customer_id = sample_customer.id

        success = await customer_service.delete_customer(
            customer_id=customer_id,
            hard_delete=True,
        )

        assert success is True

        # Customer should be completely removed from database
        result = await async_db_session.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        assert customer is None

    @pytest.mark.asyncio
    async def test_delete_customer_not_found(self, customer_service: CustomerService):
        """Test deleting non-existent customer."""
        non_existent_id = uuid4()

        success = await customer_service.delete_customer(
            customer_id=non_existent_id
        )

        assert success is False


class TestCustomerSearch:
    """Test customer search and filtering functionality."""

    @pytest.mark.asyncio
    async def test_search_customers_basic(
        self, customer_service: CustomerService, sample_customer: Customer
    ):
        """Test basic customer search."""
        search_params = CustomerSearchParams(query="john")

        customers, total = await customer_service.search_customers(search_params)

        assert total >= 1
        assert len(customers) >= 1
        assert any(c.id == sample_customer.id for c in customers)

    @pytest.mark.asyncio
    async def test_search_customers_by_email(
        self, customer_service: CustomerService, sample_customer: Customer
    ):
        """Test searching customers by email."""
        search_params = CustomerSearchParams(email=sample_customer.email)

        customers, total = await customer_service.search_customers(search_params)

        assert total == 1
        assert len(customers) == 1
        assert customers[0].id == sample_customer.id

    @pytest.mark.asyncio
    async def test_search_customers_by_status(
        self, customer_service: CustomerService, sample_customer: Customer
    ):
        """Test filtering customers by status."""
        search_params = CustomerSearchParams(status=CustomerStatus.PROSPECT)

        customers, total = await customer_service.search_customers(search_params)

        assert all(c.status == CustomerStatus.PROSPECT for c in customers)
        assert any(c.id == sample_customer.id for c in customers)

    @pytest.mark.asyncio
    async def test_search_customers_pagination(
        self, customer_service: CustomerService, sample_customer_data: dict
    ):
        """Test customer search pagination."""
        # Create multiple customers
        for i in range(5):
            customer_data = sample_customer_data.copy()
            customer_data["email"] = f"customer{i}@example.com"
            customer_data["first_name"] = f"Customer{i}"

            await customer_service.create_customer(
                data=CustomerCreate(**customer_data),
                created_by="test-user",
            )

        # Test first page
        search_params = CustomerSearchParams(page=1, page_size=2)
        customers, total = await customer_service.search_customers(search_params)

        assert len(customers) <= 2
        assert total >= 5

        # Test second page
        search_params = CustomerSearchParams(page=2, page_size=2)
        customers_page2, total2 = await customer_service.search_customers(search_params)

        assert len(customers_page2) <= 2
        assert total2 == total


class TestCustomerActivities:
    """Test customer activity management."""

    @pytest.mark.asyncio
    async def test_add_activity_success(
        self, customer_service: CustomerService, sample_customer: Customer
    ):
        """Test adding activity to customer."""
        activity_data = CustomerActivityCreate(
            activity_type=ActivityType.CONTACT_MADE,
            title="Phone call made",
            description="Called customer for follow-up",
            metadata={"duration": 300},
        )

        activity = await customer_service.add_activity(
            customer_id=sample_customer.id,
            data=activity_data,
            performed_by=uuid4(),
        )

        assert activity.customer_id == sample_customer.id
        assert activity.activity_type == ActivityType.CONTACT_MADE
        assert activity.title == "Phone call made"
        assert activity.metadata_["duration"] == 300

    @pytest.mark.asyncio
    async def test_add_activity_customer_not_found(
        self, customer_service: CustomerService
    ):
        """Test adding activity to non-existent customer."""
        non_existent_id = uuid4()
        activity_data = CustomerActivityCreate(
            activity_type=ActivityType.CONTACT_MADE,
            title="Test activity",
        )

        with pytest.raises(ValueError, match="Customer .* not found"):
            await customer_service.add_activity(
                customer_id=non_existent_id,
                data=activity_data,
                performed_by=uuid4(),
            )

    @pytest.mark.asyncio
    async def test_get_activities(
        self, customer_service: CustomerService, sample_customer: Customer
    ):
        """Test retrieving customer activities."""
        # Add some activities
        for i in range(3):
            activity_data = CustomerActivityCreate(
                activity_type=ActivityType.UPDATED,
                title=f"Update {i}",
                description=f"Customer update number {i}",
            )
            await customer_service.add_activity(
                customer_id=sample_customer.id,
                data=activity_data,
                performed_by=uuid4(),
            )

        # Retrieve activities
        activities = await customer_service.get_activities(
            customer_id=sample_customer.id,
            limit=10,
            offset=0,
        )

        # Should include the initial creation activity plus the 3 we added
        assert len(activities) >= 4


class TestCustomerNotes:
    """Test customer notes management."""

    @pytest.mark.asyncio
    async def test_add_note_success(
        self, customer_service: CustomerService, sample_customer: Customer
    ):
        """Test adding note to customer."""
        note_data = CustomerNoteCreate(
            subject="Follow-up needed",
            content="Customer requested information about premium features",
            is_internal=True,
        )

        note = await customer_service.add_note(
            customer_id=sample_customer.id,
            data=note_data,
            created_by_id=uuid4(),
        )

        assert note.customer_id == sample_customer.id
        assert note.subject == "Follow-up needed"
        assert note.content.startswith("Customer requested")
        assert note.is_internal is True

    @pytest.mark.asyncio
    async def test_add_note_customer_not_found(
        self, customer_service: CustomerService
    ):
        """Test adding note to non-existent customer."""
        non_existent_id = uuid4()
        note_data = CustomerNoteCreate(
            subject="Test note",
            content="Test content",
        )

        with pytest.raises(ValueError, match="Customer .* not found"):
            await customer_service.add_note(
                customer_id=non_existent_id,
                data=note_data,
                created_by_id=uuid4(),
            )

    @pytest.mark.asyncio
    async def test_get_notes(
        self, customer_service: CustomerService, sample_customer: Customer
    ):
        """Test retrieving customer notes."""
        created_by_id = uuid4()

        # Add internal and external notes
        internal_note = CustomerNoteCreate(
            subject="Internal Note",
            content="Internal communication",
            is_internal=True,
        )
        external_note = CustomerNoteCreate(
            subject="Customer Note",
            content="Customer visible note",
            is_internal=False,
        )

        await customer_service.add_note(
            customer_id=sample_customer.id,
            data=internal_note,
            created_by_id=created_by_id,
        )
        await customer_service.add_note(
            customer_id=sample_customer.id,
            data=external_note,
            created_by_id=created_by_id,
        )

        # Get all notes
        all_notes = await customer_service.get_notes(
            customer_id=sample_customer.id,
            include_internal=True,
        )
        assert len(all_notes) == 2

        # Get only external notes
        external_notes = await customer_service.get_notes(
            customer_id=sample_customer.id,
            include_internal=False,
        )
        assert len(external_notes) == 1
        assert external_notes[0].is_internal is False


class TestCustomerMetrics:
    """Test customer metrics and analytics."""

    @pytest.mark.asyncio
    async def test_update_metrics(
        self, customer_service: CustomerService, sample_customer: Customer
    ):
        """Test updating customer purchase metrics."""
        # Record a purchase
        await customer_service.update_metrics(
            customer_id=sample_customer.id,
            purchase_amount=100.50,
        )

        # Retrieve updated customer
        updated_customer = await customer_service.get_customer(
            customer_id=sample_customer.id
        )

        assert updated_customer.total_purchases == 1
        assert updated_customer.lifetime_value == Decimal("100.50")
        assert updated_customer.average_order_value == Decimal("100.50")
        assert updated_customer.first_purchase_date is not None
        assert updated_customer.last_purchase_date is not None

    @pytest.mark.asyncio
    async def test_get_customer_metrics(self, customer_service: CustomerService):
        """Test getting overall customer metrics."""
        metrics = await customer_service.get_customer_metrics()

        assert "total_customers" in metrics
        assert "active_customers" in metrics
        assert "churn_rate" in metrics
        assert "average_lifetime_value" in metrics
        assert "total_revenue" in metrics
        assert isinstance(metrics["total_customers"], int)


class TestCustomerSegments:
    """Test customer segmentation functionality."""

    @pytest.mark.asyncio
    async def test_create_segment(self, customer_service: CustomerService):
        """Test creating customer segment."""
        segment_data = CustomerSegmentCreate(
            name="High Value Customers",
            description="Customers with lifetime value > $1000",
            criteria={"min_ltv": 1000},
            is_dynamic=True,
        )

        segment = await customer_service.create_segment(segment_data)

        assert segment.name == "High Value Customers"
        assert segment.criteria["min_ltv"] == 1000
        assert segment.is_dynamic is True
        assert segment.member_count == 0

    @pytest.mark.asyncio
    async def test_recalculate_segment(
        self, customer_service: CustomerService, async_db_session: AsyncSession
    ):
        """Test recalculating dynamic segment membership."""
        # Create a segment
        segment_data = CustomerSegmentCreate(
            name="Test Segment",
            is_dynamic=True,
        )
        segment = await customer_service.create_segment(segment_data)

        # Recalculate (this is a simplified test)
        member_count = await customer_service.recalculate_segment(segment.id)

        assert isinstance(member_count, int)
        assert member_count >= 0