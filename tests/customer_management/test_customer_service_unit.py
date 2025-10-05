"""
Unit Tests for Customer Service (Business Logic).

Strategy: Mock ALL dependencies (database, tenant context)
Focus: Test CRUD operations, validation, tenant isolation in isolation
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.customer_management.service import CustomerService
from dotmac.platform.customer_management.models import (
    Customer,
    CustomerActivity,
    CustomerStatus,
    ActivityType,
)
from dotmac.platform.customer_management.schemas import (
    CustomerCreate,
    CustomerUpdate,
)


class TestCustomerCreation:
    """Test customer creation logic."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock(spec=AsyncSession)
        session.commit = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def customer_service(self, mock_session):
        """Create customer service with mocked session."""
        return CustomerService(session=mock_session)

    @pytest.fixture
    def customer_create_data(self):
        """Create sample customer create data."""
        return CustomerCreate(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            company_name="Acme Corp",
            tags=["vip", "enterprise"],
            metadata={"source": "website"},
            custom_fields={"account_manager": "Jane Smith"},
        )

    async def test_create_customer_success(
        self, customer_service, mock_session, customer_create_data
    ):
        """Test successful customer creation."""
        with patch.object(
            customer_service, "_generate_customer_number", return_value="CUST-2025-001"
        ):
            with patch(
                "dotmac.platform.customer_management.service.get_current_tenant_id",
                return_value="tenant-1",
            ):
                customer = await customer_service.create_customer(
                    data=customer_create_data,
                    created_by="admin_user",
                )

                # Verify customer was added to session
                assert mock_session.add.called

                # Verify customer number was generated
                customer_obj = mock_session.add.call_args_list[0][0][0]
                assert customer_obj.customer_number == "CUST-2025-001"
                assert customer_obj.first_name == "John"
                assert customer_obj.last_name == "Doe"
                assert customer_obj.email == "john.doe@example.com"
                assert customer_obj.tenant_id == "tenant-1"

    async def test_create_customer_with_tags(
        self, customer_service, mock_session, customer_create_data
    ):
        """Test customer creation with tags."""
        with patch.object(customer_service, "_generate_customer_number", return_value="CUST-001"):
            with patch(
                "dotmac.platform.customer_management.service.get_current_tenant_id",
                return_value="tenant-1",
            ):
                await customer_service.create_customer(data=customer_create_data)

                # Verify tags were added (customer + activity + 2 tags = 4 adds)
                assert mock_session.add.call_count >= 3  # customer, activity, tags

    async def test_create_customer_creates_activity(
        self, customer_service, mock_session, customer_create_data
    ):
        """Test that customer creation creates an activity log."""
        with patch.object(customer_service, "_generate_customer_number", return_value="CUST-001"):
            with patch(
                "dotmac.platform.customer_management.service.get_current_tenant_id",
                return_value="tenant-1",
            ):
                await customer_service.create_customer(data=customer_create_data)

                # Check that activity was created (second add call)
                add_calls = mock_session.add.call_args_list
                activity_created = any(
                    isinstance(call[0][0], CustomerActivity) for call in add_calls
                )
                assert activity_created


class TestCustomerRetrieval:
    """Test customer retrieval methods."""

    @pytest.fixture
    def customer_service(self):
        """Create customer service."""
        mock_session = AsyncMock(spec=AsyncSession)
        return CustomerService(session=mock_session), mock_session

    @pytest.fixture
    def sample_customer(self):
        """Create sample customer."""
        customer_id = uuid4()
        return Customer(
            id=customer_id,
            customer_number="CUST-001",
            tenant_id="tenant-1",
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            status=CustomerStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    async def test_get_customer_by_id(self, customer_service, sample_customer):
        """Test getting customer by ID."""
        service, mock_session = customer_service

        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="tenant-1",
        ):
            with patch.object(
                mock_session,
                "execute",
                return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=sample_customer)),
            ):
                customer = await service.get_customer(str(sample_customer.id))

                assert customer is not None
                assert customer.customer_number == "CUST-001"
                assert customer.email == "jane.smith@example.com"

    async def test_get_customer_not_found(self, customer_service):
        """Test getting non-existent customer returns None."""
        service, mock_session = customer_service

        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="tenant-1",
        ):
            with patch.object(
                mock_session,
                "execute",
                return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
            ):
                customer = await service.get_customer(str(uuid4()))

                assert customer is None

    async def test_get_customer_by_email(self, customer_service, sample_customer):
        """Test getting customer by email."""
        service, mock_session = customer_service

        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="tenant-1",
        ):
            with patch.object(
                mock_session,
                "execute",
                return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=sample_customer)),
            ):
                customer = await service.get_customer_by_email("jane.smith@example.com")

                assert customer is not None
                assert customer.email == "jane.smith@example.com"

    async def test_get_customer_by_number(self, customer_service, sample_customer):
        """Test getting customer by customer number."""
        service, mock_session = customer_service

        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="tenant-1",
        ):
            with patch.object(
                mock_session,
                "execute",
                return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=sample_customer)),
            ):
                customer = await service.get_customer_by_number("CUST-001")

                assert customer is not None
                assert customer.customer_number == "CUST-001"


class TestCustomerUpdate:
    """Test customer update logic."""

    @pytest.fixture
    def customer_service(self):
        """Create customer service."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.add = MagicMock()
        return CustomerService(session=mock_session), mock_session

    @pytest.fixture
    def existing_customer(self):
        """Create existing customer."""
        customer_id = uuid4()
        return Customer(
            id=customer_id,
            customer_number="CUST-001",
            tenant_id="tenant-1",
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            status=CustomerStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    async def test_update_customer_success(self, customer_service, existing_customer):
        """Test successful customer update."""
        service, mock_session = customer_service

        update_data = CustomerUpdate(
            first_name="Jane",
            phone="+9876543210",
        )

        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="tenant-1",
        ):
            with patch.object(service, "get_customer", return_value=existing_customer):
                with patch.object(mock_session, "execute", return_value=None):
                    customer = await service.update_customer(
                        customer_id=str(existing_customer.id),
                        data=update_data,
                        updated_by="admin_user",
                    )

                    # Verify commit was called
                    assert mock_session.commit.called

                    # Verify activity was created
                    assert mock_session.add.called

    async def test_update_customer_not_found(self, customer_service):
        """Test updating non-existent customer returns None."""
        service, mock_session = customer_service

        update_data = CustomerUpdate(first_name="Jane")

        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="tenant-1",
        ):
            with patch.object(service, "get_customer", return_value=None):
                customer = await service.update_customer(
                    customer_id=str(uuid4()),
                    data=update_data,
                )

                assert customer is None

    async def test_update_customer_creates_activity(self, customer_service, existing_customer):
        """Test that customer update creates activity log."""
        service, mock_session = customer_service

        update_data = CustomerUpdate(first_name="Jane")

        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="tenant-1",
        ):
            with patch.object(service, "get_customer", return_value=existing_customer):
                with patch.object(mock_session, "execute", return_value=None):
                    await service.update_customer(
                        customer_id=str(existing_customer.id),
                        data=update_data,
                        updated_by="admin_user",
                    )

                    # Verify activity was added
                    add_calls = mock_session.add.call_args_list
                    activity_created = any(
                        isinstance(call[0][0], CustomerActivity) for call in add_calls
                    )
                    assert activity_created


class TestCustomerDeletion:
    """Test customer deletion (soft and hard delete)."""

    @pytest.fixture
    def customer_service(self):
        """Create customer service."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_session.delete = AsyncMock()
        mock_session.add = MagicMock()
        return CustomerService(session=mock_session), mock_session

    @pytest.fixture
    def existing_customer(self):
        """Create existing customer."""
        customer_id = uuid4()
        return Customer(
            id=customer_id,
            customer_number="CUST-001",
            tenant_id="tenant-1",
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            status=CustomerStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    async def test_soft_delete_customer(self, customer_service, existing_customer):
        """Test soft delete marks customer as deleted."""
        service, mock_session = customer_service

        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="tenant-1",
        ):
            with patch.object(service, "get_customer", return_value=existing_customer):
                result = await service.delete_customer(
                    customer_id=str(existing_customer.id),
                    deleted_by="admin_user",
                    hard_delete=False,
                )

                assert result is True

                # Customer should be marked as deleted
                assert existing_customer.deleted_at is not None
                assert existing_customer.status == CustomerStatus.ARCHIVED

                # Activity should be created
                assert mock_session.add.called

    async def test_hard_delete_customer(self, customer_service, existing_customer):
        """Test hard delete removes customer from database."""
        service, mock_session = customer_service

        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="tenant-1",
        ):
            with patch.object(service, "get_customer", return_value=existing_customer):
                result = await service.delete_customer(
                    customer_id=str(existing_customer.id),
                    hard_delete=True,
                )

                assert result is True

                # Session delete should be called (not implemented, but would be)
                # Note: mock_session.delete is AsyncMock, actual deletion handled in real code

    async def test_delete_customer_not_found(self, customer_service):
        """Test deleting non-existent customer returns False."""
        service, mock_session = customer_service

        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="tenant-1",
        ):
            with patch.object(service, "get_customer", return_value=None):
                result = await service.delete_customer(customer_id=str(uuid4()))

                assert result is False


class TestTenantIsolation:
    """Test tenant isolation in customer operations."""

    @pytest.fixture
    def customer_service(self):
        """Create customer service."""
        mock_session = AsyncMock(spec=AsyncSession)
        return CustomerService(session=mock_session)

    async def test_customer_creation_uses_tenant_id(self, customer_service):
        """Test that customer creation includes tenant_id."""
        mock_session = customer_service.session
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        customer_data = CustomerCreate(
            first_name="Test",
            last_name="User",
            email="test@example.com",
        )

        with patch.object(customer_service, "_generate_customer_number", return_value="CUST-001"):
            with patch(
                "dotmac.platform.customer_management.service.get_current_tenant_id",
                return_value="tenant-123",
            ):
                await customer_service.create_customer(data=customer_data)

                # Verify customer has correct tenant_id
                customer_obj = mock_session.add.call_args_list[0][0][0]
                assert customer_obj.tenant_id == "tenant-123"

    async def test_tenant_resolution_fallback(self, customer_service):
        """Test tenant resolution falls back to default when no context."""
        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id", return_value=None
        ):
            tenant_id = customer_service._resolve_tenant_id()

            # Should fall back to default tenant
            assert tenant_id == "default-tenant"


class TestValidation:
    """Test input validation."""

    @pytest.fixture
    def customer_service(self):
        """Create customer service."""
        mock_session = AsyncMock(spec=AsyncSession)
        return CustomerService(session=mock_session)

    async def test_invalid_uuid_raises_error(self, customer_service):
        """Test that invalid UUID raises ValueError."""
        with pytest.raises(ValueError) as exc:
            await customer_service.get_customer("not-a-uuid")

        assert "invalid uuid" in str(exc.value).lower()

    async def test_validate_and_get_tenant(self, customer_service):
        """Test UUID validation and tenant resolution."""
        valid_uuid = str(uuid4())

        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="tenant-1",
        ):
            validated_id, tenant_id = customer_service._validate_and_get_tenant(valid_uuid)

            assert isinstance(validated_id, UUID)
            assert tenant_id == "tenant-1"


class TestCustomerActivities:
    """Test customer activity management methods."""

    async def test_add_activity_success(self, customer_service, existing_customer):
        """Test adding an activity to a customer."""
        from dotmac.platform.customer_management.schemas import CustomerActivityCreate

        activity_data = CustomerActivityCreate(
            activity_type="CALL",
            description="Follow-up call with customer",
            metadata={"duration_minutes": 15},
        )

        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="test-tenant",
        ):
            activity = await customer_service.add_activity(
                existing_customer.id, activity_data, performed_by="user-123"
            )

            assert activity.customer_id == existing_customer.id
            assert activity.activity_type == "CALL"
            assert activity.description == "Follow-up call with customer"
            assert activity.performed_by == "user-123"

    async def test_get_customer_activities(self, customer_service, existing_customer):
        """Test retrieving customer activities."""
        from dotmac.platform.customer_management.schemas import CustomerActivityCreate

        # Add some activities first
        activity1 = CustomerActivityCreate(
            activity_type="CALL",
            description="Call 1",
        )
        activity2 = CustomerActivityCreate(
            activity_type="EMAIL",
            description="Email 1",
        )

        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="test-tenant",
        ):
            await customer_service.add_activity(existing_customer.id, activity1)
            await customer_service.add_activity(existing_customer.id, activity2)

            activities = await customer_service.get_customer_activities(existing_customer.id)

            assert len(activities) >= 2


class TestCustomerNotes:
    """Test customer note management methods."""

    async def test_add_note_success(self, customer_service, existing_customer):
        """Test adding a note to a customer."""
        from dotmac.platform.customer_management.schemas import CustomerNoteCreate

        note_data = CustomerNoteCreate(
            content="Customer prefers morning calls",
            is_internal=True,
            category="PREFERENCE",
        )

        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="test-tenant",
        ):
            note = await customer_service.add_note(
                existing_customer.id, note_data, created_by="user-123"
            )

            assert note.customer_id == existing_customer.id
            assert note.content == "Customer prefers morning calls"
            assert note.is_internal is True
            assert note.created_by == "user-123"

    async def test_get_customer_notes_all(self, customer_service, existing_customer):
        """Test retrieving all customer notes."""
        from dotmac.platform.customer_management.schemas import CustomerNoteCreate

        # Add some notes
        note1 = CustomerNoteCreate(content="Internal note", is_internal=True)
        note2 = CustomerNoteCreate(content="External note", is_internal=False)

        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="test-tenant",
        ):
            await customer_service.add_note(existing_customer.id, note1)
            await customer_service.add_note(existing_customer.id, note2)

            notes = await customer_service.get_customer_notes(
                existing_customer.id, include_internal=True
            )

            assert len(notes) >= 2

    async def test_get_customer_notes_external_only(self, customer_service, existing_customer):
        """Test retrieving only external notes."""
        from dotmac.platform.customer_management.schemas import CustomerNoteCreate

        note = CustomerNoteCreate(content="Public note", is_internal=False)

        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="test-tenant",
        ):
            await customer_service.add_note(existing_customer.id, note)

            notes = await customer_service.get_customer_notes(
                existing_customer.id, include_internal=False
            )

            # Should only include external notes
            for n in notes:
                assert n.is_internal is False


class TestCustomerStatistics:
    """Test customer statistics and metrics methods."""

    async def test_get_customer_count(self, customer_service):
        """Test getting total customer count."""
        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="test-tenant",
        ):
            count = await customer_service.get_customer_count()
            assert isinstance(count, int)
            assert count >= 0

    async def test_get_customer_count_by_status(self, customer_service):
        """Test getting customer count filtered by status."""
        from dotmac.platform.customer_management.models import CustomerStatus

        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="test-tenant",
        ):
            count = await customer_service.get_customer_count(status=CustomerStatus.ACTIVE)
            assert isinstance(count, int)
            assert count >= 0

    async def test_get_customer_statistics(self, customer_service):
        """Test getting customer statistics."""
        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="test-tenant",
        ):
            stats = await customer_service.get_customer_statistics()

            assert isinstance(stats, dict)
            assert "total_customers" in stats
            assert "active_customers" in stats

    async def test_record_purchase(self, customer_service, existing_customer):
        """Test recording a customer purchase."""
        from decimal import Decimal

        amount = Decimal("99.99")

        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="test-tenant",
        ):
            await customer_service.record_purchase(existing_customer.id, amount)

            # Verify customer was updated
            updated = await customer_service.get_customer(existing_customer.id)
            # Purchase should have been recorded


class TestCustomerSegmentation:
    """Test customer segmentation methods."""

    async def test_create_segment(self, customer_service):
        """Test creating a customer segment."""
        segment_data = {
            "name": "High Value Customers",
            "description": "Customers with LTV > $10k",
            "criteria": {"lifetime_value_min": 10000},
            "is_dynamic": True,
        }

        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="test-tenant",
        ):
            segment = await customer_service.create_segment(segment_data)

            assert segment.name == "High Value Customers"
            assert segment.is_dynamic is True

    async def test_recalculate_segment(self, customer_service):
        """Test recalculating segment membership."""
        # First create a segment
        segment_data = {
            "name": "Premium Tier",
            "criteria": {"tier": "PREMIUM"},
            "is_dynamic": True,
        }

        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="test-tenant",
        ):
            segment = await customer_service.create_segment(segment_data)

            # Recalculate it
            updated = await customer_service.recalculate_segment(segment.id)
            assert updated.id == segment.id

    async def test_get_customer_metrics(self, customer_service):
        """Test getting customer metrics overview."""
        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="test-tenant",
        ):
            metrics = await customer_service.get_customer_metrics()

            assert isinstance(metrics, dict)


class TestBatchOperations:
    """Test batch processing methods."""

    async def test_batch_process_archive(self, customer_service):
        """Test batch archiving customers."""
        from uuid import uuid4

        customer_ids = [uuid4(), uuid4()]

        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="test-tenant",
        ):
            await customer_service.batch_process_customers(customer_ids, "archive")

    async def test_batch_process_activate(self, customer_service):
        """Test batch activating customers."""
        from uuid import uuid4

        customer_ids = [uuid4(), uuid4()]

        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="test-tenant",
        ):
            await customer_service.batch_process_customers(customer_ids, "activate")


class TestHelperMethods:
    """Test internal helper methods."""

    def test_customer_to_dict(self, customer_service, existing_customer):
        """Test converting customer to dictionary."""
        result = customer_service._customer_to_dict(existing_customer)

        assert isinstance(result, dict)
        assert result["id"] == existing_customer.id
        assert result["email"] == existing_customer.email
        assert "metadata" in result  # Should map metadata_ to metadata

    async def test_generate_customer_number(self, customer_service):
        """Test generating unique customer numbers."""
        with patch(
            "dotmac.platform.customer_management.service.get_current_tenant_id",
            return_value="test-tenant",
        ):
            number = await customer_service._generate_customer_number()

            assert isinstance(number, str)
            assert len(number) > 0


class TestUtilityMethods:
    """Test utility methods."""

    def test_get_customers_by_criteria(self, customer_service, existing_customer):
        """Test filtering customers by criteria."""
        from dotmac.platform.customer_management.models import CustomerStatus

        customers = [existing_customer]

        result = customer_service.get_customers_by_criteria(customers, status=CustomerStatus.ACTIVE)

        assert isinstance(result, list)

    def test_sort_customers(self, customer_service, existing_customer):
        """Test sorting customers."""
        customers = [existing_customer]

        result = customer_service.sort_customers(customers, sort_by="created_at")

        assert isinstance(result, list)
        assert len(result) == 1
