"""
Comprehensive router tests for customer management to achieve 90% coverage.
"""

import pytest
from datetime import datetime, UTC
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.customer_management.models import (
    Customer,
    CustomerActivity,
    CustomerNote,
    CustomerSegment,
    CustomerStatus,
    CustomerTier,
    ActivityType,
)
from dotmac.platform.customer_management.router import (
    get_customer_service,
    create_customer,
    get_customer,
    update_customer,
    delete_customer,
    search_customers,
    get_customer_by_number,
    add_customer_activity,
    get_customer_activities,
    add_customer_note,
    get_customer_notes,
    record_purchase,
    get_customer_metrics,
    create_segment,
    recalculate_segment,
)
from dotmac.platform.customer_management.schemas import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerSearchParams,
    CustomerActivityCreate,
    CustomerNoteCreate,
    CustomerSegmentCreate,
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
        user_id="user123",
        username="testuser",
        email="test@example.com",
        roles=["user"],
        tenant_id="test-tenant",
    )


@pytest.fixture
def sample_customer():
    """Create a sample customer."""
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
        lifetime_value=Decimal("1000.00"),
        total_purchases=5,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class TestRouterDependencies:
    """Test router dependencies."""

    @pytest.mark.asyncio
    async def test_get_customer_service(self, mock_session):
        """Test getting customer service dependency."""
        service = await get_customer_service(mock_session)
        assert isinstance(service, CustomerService)
        assert service.session == mock_session


class TestCustomerCRUD:
    """Test CRUD endpoints."""

    @pytest.mark.asyncio
    async def test_create_customer(self, mock_service, mock_user, sample_customer):
        """Test POST /customers endpoint."""
        create_data = CustomerCreate(
            email="new@example.com",
            first_name="New",
            last_name="User",
            phone="+9876543210",
        )

        mock_service.create_customer.return_value = sample_customer

        result = await create_customer(
            data=create_data,
            service=mock_service,
            current_user=mock_user,
        )

        assert isinstance(result, CustomerResponse)
        assert result.email == sample_customer.email
        mock_service.create_customer.assert_called_once_with(create_data)

    @pytest.mark.asyncio
    async def test_get_customer_success(self, mock_service, mock_user, sample_customer):
        """Test GET /customers/{customer_id} endpoint."""
        customer_id = sample_customer.id
        mock_service.get_customer.return_value = sample_customer

        result = await get_customer(
            customer_id=customer_id,
            service=mock_service,
            current_user=mock_user,
        )

        assert isinstance(result, CustomerResponse)
        assert result.id == customer_id
        mock_service.get_customer.assert_called_once_with(customer_id)

    @pytest.mark.asyncio
    async def test_get_customer_not_found(self, mock_service, mock_user):
        """Test GET /customers/{customer_id} when customer doesn't exist."""
        customer_id = uuid4()
        mock_service.get_customer.return_value = None

        with pytest.raises(HTTPException) as exc:
            await get_customer(
                customer_id=customer_id,
                service=mock_service,
                current_user=mock_user,
            )

        assert exc.value.status_code == 404
        assert "Customer not found" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_update_customer_success(self, mock_service, mock_user, sample_customer):
        """Test PUT /customers/{customer_id} endpoint."""
        customer_id = sample_customer.id
        update_data = CustomerUpdate(
            first_name="Updated",
            phone="+1111111111",
        )

        updated_customer = sample_customer
        updated_customer.first_name = "Updated"
        updated_customer.phone = "+1111111111"
        mock_service.update_customer.return_value = updated_customer

        result = await update_customer(
            customer_id=customer_id,
            data=update_data,
            service=mock_service,
            current_user=mock_user,
        )

        assert isinstance(result, CustomerResponse)
        assert result.first_name == "Updated"
        mock_service.update_customer.assert_called_once_with(customer_id, update_data)

    @pytest.mark.asyncio
    async def test_update_customer_not_found(self, mock_service, mock_user):
        """Test PUT /customers/{customer_id} when customer doesn't exist."""
        customer_id = uuid4()
        update_data = CustomerUpdate(first_name="Test")
        mock_service.update_customer.return_value = None

        with pytest.raises(HTTPException) as exc:
            await update_customer(
                customer_id=customer_id,
                data=update_data,
                service=mock_service,
                current_user=mock_user,
            )

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_customer_success(self, mock_service, mock_user):
        """Test DELETE /customers/{customer_id} endpoint."""
        customer_id = uuid4()
        mock_service.delete_customer.return_value = True

        result = await delete_customer(
            customer_id=customer_id,
            hard_delete=False,
            service=mock_service,
            current_user=mock_user,
        )

        assert result == {"success": True, "message": "Customer deleted successfully"}
        mock_service.delete_customer.assert_called_once_with(customer_id, hard_delete=False)

    @pytest.mark.asyncio
    async def test_delete_customer_not_found(self, mock_service, mock_user):
        """Test DELETE /customers/{customer_id} when customer doesn't exist."""
        customer_id = uuid4()
        mock_service.delete_customer.return_value = False

        with pytest.raises(HTTPException) as exc:
            await delete_customer(
                customer_id=customer_id,
                hard_delete=False,
                service=mock_service,
                current_user=mock_user,
            )

        assert exc.value.status_code == 404


class TestCustomerList:
    """Test customer listing endpoints."""


    @pytest.mark.asyncio
    async def test_search_customers(self, mock_service, mock_user):
        """Test POST /customers/search endpoint."""
        search_params = CustomerSearchParams(
            query="john",
            status=CustomerStatus.ACTIVE,
            page=1,
            page_size=10,
        )

        mock_customers = [MagicMock(spec=Customer) for _ in range(2)]
        mock_service.search_customers.return_value = (mock_customers, 2)

        result = await search_customers(
            params=search_params,
            service=mock_service,
            current_user=mock_user,
        )

        assert result.total == 2
        assert len(result.customers) == 2
        mock_service.search_customers.assert_called_once_with(search_params)

    @pytest.mark.asyncio
    async def test_get_customer_by_number(self, mock_service, mock_user, sample_customer):
        """Test GET /customers/by-number/{customer_number} endpoint."""
        customer_number = "CUST-001"
        mock_service.get_customer_by_number.return_value = sample_customer

        result = await get_customer_by_number(
            customer_number=customer_number,
            service=mock_service,
            current_user=mock_user,
        )

        assert isinstance(result, CustomerResponse)
        assert result.customer_number == customer_number
        mock_service.get_customer_by_number.assert_called_once_with(customer_number)


class TestCustomerActivities:
    """Test customer activity endpoints."""

    @pytest.mark.asyncio
    async def test_add_activity(self, mock_service, mock_user, sample_customer):
        """Test POST /customers/{customer_id}/activities endpoint."""
        customer_id = sample_customer.id
        activity_data = CustomerActivityCreate(
            activity_type=ActivityType.UPDATED,
            title="Profile Updated",
            description="Customer updated their profile",
        )

        mock_activity = CustomerActivity(
            id=uuid4(),
            customer_id=customer_id,
            activity_type=ActivityType.UPDATED,
            title="Profile Updated",
            description="Customer updated their profile",
        )

        mock_service.add_activity.return_value = mock_activity

        result = await add_customer_activity(
            customer_id=customer_id,
            data=activity_data,
            service=mock_service,
            current_user=mock_user,
        )

        assert isinstance(result, CustomerActivityResponse)
        assert result.activity_type == ActivityType.UPDATED
        mock_service.add_activity.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_activities(self, mock_service, mock_user):
        """Test GET /customers/{customer_id}/activities endpoint."""
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

        mock_service.get_customer_activities.return_value = mock_activities

        result = await get_customer_activities(
            customer_id=customer_id,
            limit=50,
            offset=0,
            service=mock_service,
            current_user=mock_user,
        )

        assert len(result) == 3
        mock_service.get_customer_activities.assert_called_once_with(
            customer_id, limit=50, offset=0
        )


class TestCustomerNotes:
    """Test customer note endpoints."""

    @pytest.mark.asyncio
    async def test_add_note(self, mock_service, mock_user):
        """Test POST /customers/{customer_id}/notes endpoint."""
        customer_id = uuid4()
        note_data = CustomerNoteCreate(
            subject="Support Request",
            content="Customer needs help with billing",
        )

        mock_note = CustomerNote(
            id=uuid4(),
            customer_id=customer_id,
            subject="Support Request",
            content="Customer needs help with billing",
            created_by=mock_user.user_id,
        )

        mock_service.add_note.return_value = mock_note

        result = await add_customer_note(
            customer_id=customer_id,
            data=note_data,
            service=mock_service,
            current_user=mock_user,
        )

        assert isinstance(result, CustomerNoteResponse)
        assert result.subject == "Support Request"
        mock_service.add_note.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_notes(self, mock_service, mock_user):
        """Test GET /customers/{customer_id}/notes endpoint."""
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

        mock_service.get_customer_notes.return_value = mock_notes

        result = await get_customer_notes(
            customer_id=customer_id,
            include_internal=True,
            limit=50,
            offset=0,
            service=mock_service,
            current_user=mock_user,
        )

        assert len(result) == 3
        mock_service.get_customer_notes.assert_called_once_with(
            customer_id, include_internal=True, limit=50, offset=0
        )


class TestCustomerMetrics:
    """Test customer metrics endpoints."""

    @pytest.mark.asyncio
    async def test_record_purchase(self, mock_service, mock_user):
        """Test POST /customers/{customer_id}/purchase endpoint."""
        customer_id = uuid4()
        amount = Decimal("150.00")

        mock_service.record_purchase.return_value = None

        result = await record_purchase(
            customer_id=customer_id,
            amount=amount,
            service=mock_service,
            current_user=mock_user,
        )

        assert result == {"success": True, "message": "Purchase recorded successfully"}
        mock_service.record_purchase.assert_called_once_with(customer_id, amount)

    @pytest.mark.asyncio
    async def test_get_metrics(self, mock_service, mock_user, sample_customer):
        """Test GET /customers/{customer_id}/metrics endpoint."""
        customer_id = sample_customer.id
        mock_service.get_customer.return_value = sample_customer

        result = await get_customer_metrics(
            customer_id=customer_id,
            service=mock_service,
            current_user=mock_user,
        )

        assert isinstance(result, CustomerMetrics)
        assert result.lifetime_value == sample_customer.lifetime_value
        assert result.total_purchases == sample_customer.total_purchases
        mock_service.get_customer.assert_called_once_with(customer_id)

    @pytest.mark.asyncio
    async def test_get_metrics_not_found(self, mock_service, mock_user):
        """Test GET /customers/{customer_id}/metrics when customer doesn't exist."""
        customer_id = uuid4()
        mock_service.get_customer.return_value = None

        with pytest.raises(HTTPException) as exc:
            await get_customer_metrics(
                customer_id=customer_id,
                service=mock_service,
                current_user=mock_user,
            )

        assert exc.value.status_code == 404


class TestCustomerSegments:
    """Test customer segment endpoints."""

    @pytest.mark.asyncio
    async def test_create_segment(self, mock_service, mock_user):
        """Test POST /segments endpoint."""
        segment_data = CustomerSegmentCreate(
            name="VIP Customers",
            description="High value customers",
            criteria={"min_lifetime_value": 5000},
        )

        mock_segment = CustomerSegment(
            id=uuid4(),
            tenant_id="test-tenant",
            name="VIP Customers",
            description="High value customers",
            criteria={"min_lifetime_value": 5000},
        )

        mock_service.create_segment.return_value = mock_segment

        result = await create_segment(
            data=segment_data,
            service=mock_service,
            current_user=mock_user,
        )

        assert isinstance(result, CustomerSegmentResponse)
        assert result.name == "VIP Customers"
        mock_service.create_segment.assert_called_once_with(segment_data)


    @pytest.mark.asyncio
    async def test_recalculate_segment(self, mock_service, mock_user):
        """Test POST /segments/{segment_id}/recalculate endpoint."""
        segment_id = uuid4()

        mock_service.recalculate_segment.return_value = 10

        result = await recalculate_segment(
            segment_id=segment_id,
            service=mock_service,
            current_user=mock_user,
        )

        assert result == {
            "success": True,
            "message": "Segment recalculated successfully",
            "customers_count": 10,
        }
        mock_service.recalculate_segment.assert_called_once_with(segment_id)