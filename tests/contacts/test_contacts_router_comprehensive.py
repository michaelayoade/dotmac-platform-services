"""
Comprehensive tests for contacts router endpoints.

Tests cover all API endpoints with proper mocking and isolation.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4
from fastapi import HTTPException
from fastapi.testclient import TestClient

from dotmac.platform.contacts.router import router
from dotmac.platform.contacts.schemas import (
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ContactMethodCreate,
    ContactMethodUpdate,
    ContactLabelDefinitionCreate,
    ContactFieldDefinitionCreate,
    ContactActivityCreate,
    ContactSearchRequest,
    ContactBulkUpdate,
    ContactBulkDelete,
)

pytestmark = pytest.mark.asyncio


# Test data fixtures
@pytest.fixture
def sample_contact_id():
    return uuid4()


@pytest.fixture
def sample_tenant_id():
    return uuid4()


@pytest.fixture
def sample_user_id():
    return uuid4()


@pytest.fixture
def mock_user_info(sample_user_id):
    """Mock UserInfo object."""
    user_info = Mock()
    user_info.user_id = sample_user_id
    user_info.tenant_id = str(uuid4())
    user_info.email = "test@example.com"
    return user_info


@pytest.fixture
def mock_contact_response(sample_contact_id, sample_tenant_id):
    """Mock contact response."""
    mock = Mock()
    mock.contact_id = sample_contact_id
    mock.tenant_id = sample_tenant_id
    mock.first_name = "John"
    mock.last_name = "Doe"
    mock.email = "john@example.com"
    mock.status = "active"
    mock.stage = "lead"
    mock.contact_methods = []
    mock.labels = []
    mock.custom_fields = {}
    return mock


class TestContactCRUDEndpoints:
    """Test basic CRUD endpoints for contacts."""

    @pytest.mark.asyncio
    async def test_create_contact(self, mock_user_info, sample_tenant_id, mock_contact_response):
        """Test creating a new contact."""
        with patch("dotmac.platform.contacts.router.get_async_session"):
            with patch(
                "dotmac.platform.contacts.router.require_permission",
                return_value=lambda: mock_user_info,
            ):
                with patch(
                    "dotmac.platform.contacts.router.get_current_tenant_id",
                    return_value=lambda: sample_tenant_id,
                ):
                    with patch("dotmac.platform.contacts.router.ContactService") as MockService:
                        mock_service = MockService.return_value
                        mock_service.create_contact = AsyncMock(return_value=mock_contact_response)

                        from dotmac.platform.contacts.router import create_contact

                        contact_data = ContactCreate(
                            first_name="John", last_name="Doe", email="john@example.com"
                        )

                        result = await create_contact(
                            contact_data=contact_data,
                            db=Mock(),
                            current_user=mock_user_info,
                            tenant_id=sample_tenant_id,
                        )

                        assert result == mock_contact_response
                        mock_service.create_contact.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_contact_success(
        self, sample_contact_id, sample_tenant_id, mock_user_info, mock_contact_response
    ):
        """Test getting an existing contact."""
        with patch("dotmac.platform.contacts.router.ContactService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_contact = AsyncMock(return_value=mock_contact_response)

            from dotmac.platform.contacts.router import get_contact

            result = await get_contact(
                contact_id=sample_contact_id,
                include_methods=True,
                include_labels=True,
                db=Mock(),
                current_user=mock_user_info,
                tenant_id=sample_tenant_id,
            )

            assert result == mock_contact_response
            mock_service.get_contact.assert_called_once_with(
                contact_id=sample_contact_id,
                tenant_id=sample_tenant_id,
                include_methods=True,
                include_labels=True,
            )

    @pytest.mark.asyncio
    async def test_get_contact_not_found(self, sample_contact_id, sample_tenant_id, mock_user_info):
        """Test getting a non-existent contact."""
        with patch("dotmac.platform.contacts.router.ContactService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_contact = AsyncMock(return_value=None)

            from dotmac.platform.contacts.router import get_contact

            with pytest.raises(HTTPException) as exc_info:
                await get_contact(
                    contact_id=sample_contact_id,
                    include_methods=True,
                    include_labels=True,
                    db=Mock(),
                    current_user=mock_user_info,
                    tenant_id=sample_tenant_id,
                )

            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_update_contact_success(
        self, sample_contact_id, sample_tenant_id, mock_user_info, mock_contact_response
    ):
        """Test updating a contact."""
        with patch("dotmac.platform.contacts.router.ContactService") as MockService:
            mock_service = MockService.return_value
            mock_service.update_contact = AsyncMock(return_value=mock_contact_response)

            from dotmac.platform.contacts.router import update_contact

            contact_data = ContactUpdate(first_name="Jane")

            result = await update_contact(
                contact_id=sample_contact_id,
                contact_data=contact_data,
                db=Mock(),
                current_user=mock_user_info,
                tenant_id=sample_tenant_id,
            )

            assert result == mock_contact_response
            mock_service.update_contact.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_contact_not_found(
        self, sample_contact_id, sample_tenant_id, mock_user_info
    ):
        """Test updating a non-existent contact."""
        with patch("dotmac.platform.contacts.router.ContactService") as MockService:
            mock_service = MockService.return_value
            mock_service.update_contact = AsyncMock(return_value=None)

            from dotmac.platform.contacts.router import update_contact

            contact_data = ContactUpdate(first_name="Jane")

            with pytest.raises(HTTPException) as exc_info:
                await update_contact(
                    contact_id=sample_contact_id,
                    contact_data=contact_data,
                    db=Mock(),
                    current_user=mock_user_info,
                    tenant_id=sample_tenant_id,
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_contact_success(
        self, sample_contact_id, sample_tenant_id, mock_user_info
    ):
        """Test deleting a contact (soft delete)."""
        with patch("dotmac.platform.contacts.router.ContactService") as MockService:
            mock_service = MockService.return_value
            mock_service.delete_contact = AsyncMock(return_value=True)

            from dotmac.platform.contacts.router import delete_contact

            result = await delete_contact(
                contact_id=sample_contact_id,
                hard_delete=False,
                db=Mock(),
                current_user=mock_user_info,
                tenant_id=sample_tenant_id,
            )

            # Should return None (204 No Content)
            assert result is None
            mock_service.delete_contact.assert_called_once_with(
                contact_id=sample_contact_id,
                tenant_id=sample_tenant_id,
                hard_delete=False,
                deleted_by=mock_user_info.user_id,
            )

    @pytest.mark.asyncio
    async def test_delete_contact_hard_delete(
        self, sample_contact_id, sample_tenant_id, mock_user_info
    ):
        """Test hard deleting a contact."""
        with patch("dotmac.platform.contacts.router.ContactService") as MockService:
            mock_service = MockService.return_value
            mock_service.delete_contact = AsyncMock(return_value=True)

            from dotmac.platform.contacts.router import delete_contact

            await delete_contact(
                contact_id=sample_contact_id,
                hard_delete=True,
                db=Mock(),
                current_user=mock_user_info,
                tenant_id=sample_tenant_id,
            )

            mock_service.delete_contact.assert_called_once_with(
                contact_id=sample_contact_id,
                tenant_id=sample_tenant_id,
                hard_delete=True,
                deleted_by=mock_user_info.user_id,
            )

    @pytest.mark.asyncio
    async def test_delete_contact_not_found(
        self, sample_contact_id, sample_tenant_id, mock_user_info
    ):
        """Test deleting a non-existent contact."""
        with patch("dotmac.platform.contacts.router.ContactService") as MockService:
            mock_service = MockService.return_value
            mock_service.delete_contact = AsyncMock(return_value=False)

            from dotmac.platform.contacts.router import delete_contact

            with pytest.raises(HTTPException) as exc_info:
                await delete_contact(
                    contact_id=sample_contact_id,
                    hard_delete=False,
                    db=Mock(),
                    current_user=mock_user_info,
                    tenant_id=sample_tenant_id,
                )

            assert exc_info.value.status_code == 404


class TestContactSearchEndpoint:
    """Test contact search functionality."""

    @pytest.mark.asyncio
    async def test_search_contacts_basic(self, sample_tenant_id, mock_user_info):
        """Test basic contact search."""
        with patch("dotmac.platform.contacts.router.ContactService") as MockService:
            mock_service = MockService.return_value
            # Return empty list to avoid validation issues
            mock_service.search_contacts = AsyncMock(return_value=([], 1))

            from dotmac.platform.contacts.router import search_contacts

            search_request = ContactSearchRequest(query="John", page=1, page_size=10)

            result = await search_contacts(
                search_request=search_request,
                db=Mock(),
                current_user=mock_user_info,
                tenant_id=sample_tenant_id,
            )

            assert result.total == 1
            assert len(result.contacts) == 0
            assert result.page == 1
            assert result.has_next is False
            assert result.has_prev is False

    @pytest.mark.asyncio
    async def test_search_contacts_with_pagination(self, sample_tenant_id, mock_user_info):
        """Test contact search with pagination."""
        with patch("dotmac.platform.contacts.router.ContactService") as MockService:
            mock_service = MockService.return_value
            mock_service.search_contacts = AsyncMock(return_value=([], 25))

            from dotmac.platform.contacts.router import search_contacts

            search_request = ContactSearchRequest(query="test", page=2, page_size=10)

            result = await search_contacts(
                search_request=search_request,
                db=Mock(),
                current_user=mock_user_info,
                tenant_id=sample_tenant_id,
            )

            assert result.total == 25
            assert result.page == 2
            assert result.has_next is True  # Page 2 * 10 = 20 < 25
            assert result.has_prev is True  # Page > 1

    @pytest.mark.asyncio
    async def test_search_contacts_with_filters(self, sample_tenant_id, mock_user_info):
        """Test contact search with filters."""
        with patch("dotmac.platform.contacts.router.ContactService") as MockService:
            mock_service = MockService.return_value
            mock_service.search_contacts = AsyncMock(return_value=([], 1))

            from dotmac.platform.contacts.router import search_contacts

            search_request = ContactSearchRequest(
                query="John",
                status="active",
                stage="lead",
                owner_id=uuid4(),
                tags=["vip"],
                label_ids=[uuid4()],
                page=1,
                page_size=10,
            )

            result = await search_contacts(
                search_request=search_request,
                db=Mock(),
                current_user=mock_user_info,
                tenant_id=sample_tenant_id,
            )

            assert result.total == 1
            mock_service.search_contacts.assert_called_once()


class TestContactMethodEndpoints:
    """Test contact method management endpoints."""

    @pytest.mark.asyncio
    async def test_add_contact_method(self, sample_contact_id, sample_tenant_id, mock_user_info):
        """Test adding a contact method."""
        with patch("dotmac.platform.contacts.router.ContactService") as MockService:
            mock_service = MockService.return_value
            mock_method = Mock(method_id=uuid4(), method_type="email", value="test@example.com")
            mock_service.add_contact_method = AsyncMock(return_value=mock_method)

            from dotmac.platform.contacts.router import add_contact_method

            method_data = ContactMethodCreate(type="email", value="test@example.com")

            result = await add_contact_method(
                contact_id=sample_contact_id,
                method_data=method_data,
                db=Mock(),
                current_user=mock_user_info,
                tenant_id=sample_tenant_id,
            )

            assert result == mock_method
            mock_service.add_contact_method.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_contact_method_contact_not_found(
        self, sample_contact_id, sample_tenant_id, mock_user_info
    ):
        """Test adding method to non-existent contact."""
        with patch("dotmac.platform.contacts.router.ContactService") as MockService:
            mock_service = MockService.return_value
            mock_service.add_contact_method = AsyncMock(return_value=None)

            from dotmac.platform.contacts.router import add_contact_method

            method_data = ContactMethodCreate(type="email", value="test@example.com")

            with pytest.raises(HTTPException) as exc_info:
                await add_contact_method(
                    contact_id=sample_contact_id,
                    method_data=method_data,
                    db=Mock(),
                    current_user=mock_user_info,
                    tenant_id=sample_tenant_id,
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_contact_method(self, sample_tenant_id, mock_user_info):
        """Test updating a contact method."""
        method_id = uuid4()
        with patch("dotmac.platform.contacts.router.ContactService") as MockService:
            mock_service = MockService.return_value
            mock_method = Mock(method_id=method_id, value="updated@example.com")
            mock_service.update_contact_method = AsyncMock(return_value=mock_method)

            from dotmac.platform.contacts.router import update_contact_method

            method_data = ContactMethodUpdate(value="updated@example.com")

            result = await update_contact_method(
                method_id=method_id,
                method_data=method_data,
                db=Mock(),
                current_user=mock_user_info,
                tenant_id=sample_tenant_id,
            )

            assert result == mock_method

    @pytest.mark.asyncio
    async def test_update_contact_method_not_found(self, sample_tenant_id, mock_user_info):
        """Test updating non-existent contact method."""
        method_id = uuid4()
        with patch("dotmac.platform.contacts.router.ContactService") as MockService:
            mock_service = MockService.return_value
            mock_service.update_contact_method = AsyncMock(return_value=None)

            from dotmac.platform.contacts.router import update_contact_method

            method_data = ContactMethodUpdate(value="updated@example.com")

            with pytest.raises(HTTPException) as exc_info:
                await update_contact_method(
                    method_id=method_id,
                    method_data=method_data,
                    db=Mock(),
                    current_user=mock_user_info,
                    tenant_id=sample_tenant_id,
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_contact_method(self, sample_tenant_id, mock_user_info):
        """Test deleting a contact method."""
        method_id = uuid4()
        with patch("dotmac.platform.contacts.router.ContactService") as MockService:
            mock_service = MockService.return_value
            mock_service.delete_contact_method = AsyncMock(return_value=True)

            from dotmac.platform.contacts.router import delete_contact_method

            result = await delete_contact_method(
                method_id=method_id,
                db=Mock(),
                current_user=mock_user_info,
                tenant_id=sample_tenant_id,
            )

            assert result is None
            mock_service.delete_contact_method.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_contact_method_not_found(self, sample_tenant_id, mock_user_info):
        """Test deleting non-existent contact method."""
        method_id = uuid4()
        with patch("dotmac.platform.contacts.router.ContactService") as MockService:
            mock_service = MockService.return_value
            mock_service.delete_contact_method = AsyncMock(return_value=False)

            from dotmac.platform.contacts.router import delete_contact_method

            with pytest.raises(HTTPException) as exc_info:
                await delete_contact_method(
                    method_id=method_id,
                    db=Mock(),
                    current_user=mock_user_info,
                    tenant_id=sample_tenant_id,
                )

            assert exc_info.value.status_code == 404


class TestContactActivityEndpoints:
    """Test contact activity endpoints."""

    @pytest.mark.asyncio
    async def test_add_contact_activity(self, sample_contact_id, sample_tenant_id, mock_user_info):
        """Test adding an activity to a contact."""
        with patch("dotmac.platform.contacts.router.ContactService") as MockService:
            mock_service = MockService.return_value
            mock_activity = Mock(activity_id=uuid4(), activity_type="note", description="Test note")
            mock_service.add_contact_activity = AsyncMock(return_value=mock_activity)

            from dotmac.platform.contacts.router import add_contact_activity

            activity_data = ContactActivityCreate(
                activity_type="note", subject="Test note", status="completed"
            )

            result = await add_contact_activity(
                contact_id=sample_contact_id,
                activity_data=activity_data,
                db=Mock(),
                current_user=mock_user_info,
                tenant_id=sample_tenant_id,
            )

            assert result == mock_activity
            mock_service.add_contact_activity.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_contact_activity_contact_not_found(
        self, sample_contact_id, sample_tenant_id, mock_user_info
    ):
        """Test adding activity to non-existent contact."""
        with patch("dotmac.platform.contacts.router.ContactService") as MockService:
            mock_service = MockService.return_value
            mock_service.add_contact_activity = AsyncMock(return_value=None)

            from dotmac.platform.contacts.router import add_contact_activity

            activity_data = ContactActivityCreate(
                activity_type="note", subject="Test", status="completed"
            )

            with pytest.raises(HTTPException) as exc_info:
                await add_contact_activity(
                    contact_id=sample_contact_id,
                    activity_data=activity_data,
                    db=Mock(),
                    current_user=mock_user_info,
                    tenant_id=sample_tenant_id,
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_contact_activities(
        self, sample_contact_id, sample_tenant_id, mock_user_info
    ):
        """Test getting activities for a contact."""
        with patch("dotmac.platform.contacts.router.ContactService") as MockService:
            mock_service = MockService.return_value
            mock_activities = [
                Mock(activity_id=uuid4(), activity_type="note"),
                Mock(activity_id=uuid4(), activity_type="call"),
            ]
            mock_service.get_contact_activities = AsyncMock(return_value=mock_activities)

            from dotmac.platform.contacts.router import get_contact_activities

            result = await get_contact_activities(
                contact_id=sample_contact_id,
                limit=50,
                offset=0,
                db=Mock(),
                current_user=mock_user_info,
                tenant_id=sample_tenant_id,
            )

            assert len(result) == 2
            mock_service.get_contact_activities.assert_called_once_with(
                contact_id=sample_contact_id, tenant_id=sample_tenant_id, limit=50, offset=0
            )


class TestLabelDefinitionEndpoints:
    """Test label definition endpoints."""

    @pytest.mark.asyncio
    async def test_create_label_definition(self, sample_tenant_id, mock_user_info):
        """Test creating a label definition."""
        with patch("dotmac.platform.contacts.router.ContactLabelService") as MockService:
            mock_service = MockService.return_value
            mock_label = Mock(label_id=uuid4(), name="VIP", category="customer_type")
            mock_service.create_label_definition = AsyncMock(return_value=mock_label)

            from dotmac.platform.contacts.router import create_label_definition

            label_data = ContactLabelDefinitionCreate(name="VIP", category="customer_type")

            result = await create_label_definition(
                label_data=label_data,
                db=Mock(),
                current_user=mock_user_info,
                tenant_id=sample_tenant_id,
            )

            assert result == mock_label

    @pytest.mark.asyncio
    async def test_get_label_definitions(self, sample_tenant_id, mock_user_info):
        """Test getting label definitions."""
        with patch("dotmac.platform.contacts.router.ContactLabelService") as MockService:
            mock_service = MockService.return_value
            mock_labels = [
                Mock(label_id=uuid4(), name="VIP"),
                Mock(label_id=uuid4(), name="Partner"),
            ]
            mock_service.get_label_definitions = AsyncMock(return_value=mock_labels)

            from dotmac.platform.contacts.router import get_label_definitions

            result = await get_label_definitions(
                category=None,
                include_hidden=False,
                db=Mock(),
                current_user=mock_user_info,
                tenant_id=sample_tenant_id,
            )

            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_label_definitions_filtered(self, sample_tenant_id, mock_user_info):
        """Test getting filtered label definitions."""
        with patch("dotmac.platform.contacts.router.ContactLabelService") as MockService:
            mock_service = MockService.return_value
            mock_labels = [Mock(label_id=uuid4(), name="VIP", category="customer_type")]
            mock_service.get_label_definitions = AsyncMock(return_value=mock_labels)

            from dotmac.platform.contacts.router import get_label_definitions

            result = await get_label_definitions(
                category="customer_type",
                include_hidden=True,
                db=Mock(),
                current_user=mock_user_info,
                tenant_id=sample_tenant_id,
            )

            mock_service.get_label_definitions.assert_called_once_with(
                tenant_id=sample_tenant_id, category="customer_type", include_hidden=True
            )


class TestFieldDefinitionEndpoints:
    """Test custom field definition endpoints."""

    @pytest.mark.asyncio
    async def test_create_field_definition(self, sample_tenant_id, mock_user_info):
        """Test creating a custom field definition."""
        with patch("dotmac.platform.contacts.router.ContactFieldService") as MockService:
            mock_service = MockService.return_value
            mock_field = Mock(field_id=uuid4(), field_name="custom_field", field_type="text")
            mock_service.create_field_definition = AsyncMock(return_value=mock_field)

            from dotmac.platform.contacts.router import create_field_definition

            field_data = ContactFieldDefinitionCreate(name="custom_field", field_type="text")

            result = await create_field_definition(
                field_data=field_data,
                db=Mock(),
                current_user=mock_user_info,
                tenant_id=sample_tenant_id,
            )

            assert result == mock_field

    @pytest.mark.asyncio
    async def test_get_field_definitions(self, sample_tenant_id, mock_user_info):
        """Test getting field definitions."""
        with patch("dotmac.platform.contacts.router.ContactFieldService") as MockService:
            mock_service = MockService.return_value
            mock_fields = [
                Mock(field_id=uuid4(), field_name="custom_1"),
                Mock(field_id=uuid4(), field_name="custom_2"),
            ]
            mock_service.get_field_definitions = AsyncMock(return_value=mock_fields)

            from dotmac.platform.contacts.router import get_field_definitions

            result = await get_field_definitions(
                field_group=None,
                include_hidden=False,
                db=Mock(),
                current_user=mock_user_info,
                tenant_id=sample_tenant_id,
            )

            assert len(result) == 2


class TestBulkOperations:
    """Test bulk operations on contacts."""

    @pytest.mark.asyncio
    async def test_bulk_update_contacts_success(
        self, sample_tenant_id, mock_user_info, mock_contact_response
    ):
        """Test bulk updating contacts successfully."""
        contact_ids = [uuid4(), uuid4(), uuid4()]

        with patch("dotmac.platform.contacts.router.ContactService") as MockService:
            mock_service = MockService.return_value
            mock_service.update_contact = AsyncMock(return_value=mock_contact_response)

            from dotmac.platform.contacts.router import bulk_update_contacts

            bulk_update = ContactBulkUpdate(
                contact_ids=contact_ids, update_data=ContactUpdate(status="active")
            )

            result = await bulk_update_contacts(
                bulk_update=bulk_update,
                db=Mock(),
                current_user=mock_user_info,
                tenant_id=sample_tenant_id,
            )

            assert result["updated"] == 3
            assert len(result["errors"]) == 0
            assert mock_service.update_contact.call_count == 3

    @pytest.mark.asyncio
    async def test_bulk_update_contacts_partial_failure(
        self, sample_tenant_id, mock_user_info, mock_contact_response
    ):
        """Test bulk update with some failures."""
        contact_ids = [uuid4(), uuid4(), uuid4()]

        with patch("dotmac.platform.contacts.router.ContactService") as MockService:
            mock_service = MockService.return_value
            # First succeeds, second fails (None), third raises exception
            mock_service.update_contact = AsyncMock(
                side_effect=[mock_contact_response, None, Exception("Database error")]
            )

            from dotmac.platform.contacts.router import bulk_update_contacts

            bulk_update = ContactBulkUpdate(
                contact_ids=contact_ids, update_data=ContactUpdate(status="active")
            )

            result = await bulk_update_contacts(
                bulk_update=bulk_update,
                db=Mock(),
                current_user=mock_user_info,
                tenant_id=sample_tenant_id,
            )

            assert result["updated"] == 1
            assert len(result["errors"]) == 2

    @pytest.mark.asyncio
    async def test_bulk_delete_contacts_success(self, sample_tenant_id, mock_user_info):
        """Test bulk deleting contacts successfully."""
        contact_ids = [uuid4(), uuid4()]

        with patch("dotmac.platform.contacts.router.ContactService") as MockService:
            mock_service = MockService.return_value
            mock_service.delete_contact = AsyncMock(return_value=True)

            from dotmac.platform.contacts.router import bulk_delete_contacts

            bulk_delete = ContactBulkDelete(contact_ids=contact_ids, hard_delete=False)

            result = await bulk_delete_contacts(
                bulk_delete=bulk_delete,
                db=Mock(),
                current_user=mock_user_info,
                tenant_id=sample_tenant_id,
            )

            assert result["deleted"] == 2
            assert len(result["errors"]) == 0
            assert mock_service.delete_contact.call_count == 2

    @pytest.mark.asyncio
    async def test_bulk_delete_contacts_with_failures(self, sample_tenant_id, mock_user_info):
        """Test bulk delete with some failures."""
        contact_ids = [uuid4(), uuid4(), uuid4()]

        with patch("dotmac.platform.contacts.router.ContactService") as MockService:
            mock_service = MockService.return_value
            # First succeeds, second fails (False), third raises exception
            mock_service.delete_contact = AsyncMock(
                side_effect=[True, False, Exception("Permission denied")]
            )

            from dotmac.platform.contacts.router import bulk_delete_contacts

            bulk_delete = ContactBulkDelete(contact_ids=contact_ids, hard_delete=True)

            result = await bulk_delete_contacts(
                bulk_delete=bulk_delete,
                db=Mock(),
                current_user=mock_user_info,
                tenant_id=sample_tenant_id,
            )

            assert result["deleted"] == 1
            assert len(result["errors"]) == 2
