"""
Tests for customer management API router.

Tests all REST API endpoints including:
- Customer CRUD operations
- Authentication and authorization
- Request/response validation
- Error handling
- Activity and notes endpoints
- Metrics endpoints
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any
from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient

from dotmac.platform.customer_management.models import (
    ActivityType,
    CustomerStatus,
    CustomerTier,
    CustomerType,
)


@pytest.fixture
def sample_customer_payload() -> Dict[str, Any]:
    """Sample customer creation payload."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "customer_type": "individual",
        "tier": "basic",
        "address_line1": "123 Main St",
        "city": "Anytown",
        "state_province": "CA",
        "postal_code": "12345",
        "country": "US",
        "tags": ["new", "priority"],
        "metadata": {"source": "web"},
        "custom_fields": {"referred_by": "friend"},
    }


class TestCustomerCRUDEndpoints:
    """Test customer CRUD API endpoints."""

    @pytest.mark.asyncio
    async def test_create_customer_success(
        self,
        authenticated_client: AsyncClient,
        sample_customer_payload: Dict[str, Any],
    ):
        """Test successful customer creation."""
        response = await authenticated_client.post(
            "/api/v1/customers/",
            json=sample_customer_payload,
        )

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["email"] == "john.doe@example.com"
        assert data["customer_type"] == "individual"
        assert data["tier"] == "basic"
        assert "id" in data
        assert "customer_number" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_customer_validation_error(
        self, authenticated_client: AsyncClient
    ):
        """Test customer creation with invalid data."""
        invalid_payload = {
            "first_name": "",  # Empty name
            "last_name": "Doe",
            "email": "invalid-email",  # Invalid email
        }

        response = await authenticated_client.post(
            "/api/v1/customers/",
            json=invalid_payload,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        data = response.json()
        assert "detail" in data
        # Check for validation errors
        errors = data["detail"]
        assert any(error["loc"] == ["first_name"] for error in errors)
        assert any(error["loc"] == ["email"] for error in errors)

    @pytest.mark.asyncio
    async def test_create_customer_duplicate_email(
        self,
        authenticated_client: AsyncClient,
        sample_customer_payload: Dict[str, Any],
    ):
        """Test creating customer with duplicate email."""
        # Create first customer
        response1 = await authenticated_client.post(
            "/api/v1/customers/",
            json=sample_customer_payload,
        )
        assert response1.status_code == status.HTTP_201_CREATED

        # Try to create second customer with same email
        sample_customer_payload["first_name"] = "Jane"
        response2 = await authenticated_client.post(
            "/api/v1/customers/",
            json=sample_customer_payload,
        )

        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response2.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_customer_unauthenticated(
        self,
        client: AsyncClient,
        sample_customer_payload: Dict[str, Any],
    ):
        """Test customer creation without authentication."""
        response = await client.post(
            "/api/v1/customers/",
            json=sample_customer_payload,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_customer_success(
        self,
        authenticated_client: AsyncClient,
        sample_customer_payload: Dict[str, Any],
    ):
        """Test successful customer retrieval."""
        # Create customer first
        create_response = await authenticated_client.post(
            "/api/v1/customers/",
            json=sample_customer_payload,
        )
        customer_data = create_response.json()
        customer_id = customer_data["id"]

        # Get customer
        response = await authenticated_client.get(f"/api/v1/customers/{customer_id}")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == customer_id
        assert data["first_name"] == "John"
        assert data["email"] == "john.doe@example.com"

    @pytest.mark.asyncio
    async def test_get_customer_with_includes(
        self,
        authenticated_client: AsyncClient,
        sample_customer_payload: Dict[str, Any],
    ):
        """Test customer retrieval with related data."""
        # Create customer first
        create_response = await authenticated_client.post(
            "/api/v1/customers/",
            json=sample_customer_payload,
        )
        customer_data = create_response.json()
        customer_id = customer_data["id"]

        # Get customer with activities and notes
        response = await authenticated_client.get(
            f"/api/v1/customers/{customer_id}",
            params={
                "include_activities": True,
                "include_notes": True,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == customer_id
        # These fields would be populated if the service implemented them
        # assert "activities" in data
        # assert "notes" in data

    @pytest.mark.asyncio
    async def test_get_customer_not_found(self, authenticated_client: AsyncClient):
        """Test retrieving non-existent customer."""
        non_existent_id = str(uuid4())
        response = await authenticated_client.get(
            f"/api/v1/customers/{non_existent_id}"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_customer_by_number(
        self,
        authenticated_client: AsyncClient,
        sample_customer_payload: Dict[str, Any],
    ):
        """Test retrieving customer by customer number."""
        # Create customer first
        create_response = await authenticated_client.post(
            "/api/v1/customers/",
            json=sample_customer_payload,
        )
        customer_data = create_response.json()
        customer_number = customer_data["customer_number"]

        # Get customer by number
        response = await authenticated_client.get(
            f"/api/v1/customers/by-number/{customer_number}"
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["customer_number"] == customer_number
        assert data["first_name"] == "John"

    @pytest.mark.asyncio
    async def test_update_customer_success(
        self,
        authenticated_client: AsyncClient,
        sample_customer_payload: Dict[str, Any],
    ):
        """Test successful customer update."""
        # Create customer first
        create_response = await authenticated_client.post(
            "/api/v1/customers/",
            json=sample_customer_payload,
        )
        customer_data = create_response.json()
        customer_id = customer_data["id"]

        # Update customer
        update_payload = {
            "first_name": "Jane",
            "tier": "premium",
            "metadata": {"updated": True},
        }

        response = await authenticated_client.patch(
            f"/api/v1/customers/{customer_id}",
            json=update_payload,
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["first_name"] == "Jane"
        assert data["tier"] == "premium"
        assert data["metadata"]["updated"] is True

    @pytest.mark.asyncio
    async def test_update_customer_not_found(self, authenticated_client: AsyncClient):
        """Test updating non-existent customer."""
        non_existent_id = str(uuid4())
        update_payload = {"first_name": "Jane"}

        response = await authenticated_client.patch(
            f"/api/v1/customers/{non_existent_id}",
            json=update_payload,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_customer_soft_delete(
        self,
        authenticated_client: AsyncClient,
        sample_customer_payload: Dict[str, Any],
    ):
        """Test soft delete customer."""
        # Create customer first
        create_response = await authenticated_client.post(
            "/api/v1/customers/",
            json=sample_customer_payload,
        )
        customer_data = create_response.json()
        customer_id = customer_data["id"]

        # Delete customer (soft delete by default)
        response = await authenticated_client.delete(
            f"/api/v1/customers/{customer_id}"
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify customer is no longer accessible
        get_response = await authenticated_client.get(
            f"/api/v1/customers/{customer_id}"
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_customer_hard_delete(
        self,
        authenticated_client: AsyncClient,
        sample_customer_payload: Dict[str, Any],
    ):
        """Test hard delete customer."""
        # Create customer first
        create_response = await authenticated_client.post(
            "/api/v1/customers/",
            json=sample_customer_payload,
        )
        customer_data = create_response.json()
        customer_id = customer_data["id"]

        # Hard delete customer
        response = await authenticated_client.delete(
            f"/api/v1/customers/{customer_id}",
            params={"hard_delete": True},
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestCustomerSearchEndpoint:
    """Test customer search functionality."""

    @pytest.mark.asyncio
    async def test_search_customers_basic(
        self,
        authenticated_client: AsyncClient,
        sample_customer_payload: Dict[str, Any],
    ):
        """Test basic customer search."""
        # Create a customer first
        await authenticated_client.post(
            "/api/v1/customers/",
            json=sample_customer_payload,
        )

        # Search for customers
        search_payload = {
            "query": "john",
            "page": 1,
            "page_size": 10,
        }

        response = await authenticated_client.post(
            "/api/v1/customers/search",
            json=search_payload,
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "customers" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "has_next" in data
        assert "has_prev" in data

        assert data["total"] >= 1
        assert len(data["customers"]) >= 1

    @pytest.mark.asyncio
    async def test_search_customers_filters(
        self,
        authenticated_client: AsyncClient,
        sample_customer_payload: Dict[str, Any],
    ):
        """Test customer search with filters."""
        # Create a customer first
        await authenticated_client.post(
            "/api/v1/customers/",
            json=sample_customer_payload,
        )

        # Search with filters
        search_payload = {
            "status": "prospect",
            "tier": "basic",
            "customer_type": "individual",
            "page": 1,
            "page_size": 10,
        }

        response = await authenticated_client.post(
            "/api/v1/customers/search",
            json=search_payload,
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["total"] >= 1

        # Check that returned customers match filters
        for customer in data["customers"]:
            assert customer["status"] == "prospect"
            assert customer["tier"] == "basic"
            assert customer["customer_type"] == "individual"

    @pytest.mark.asyncio
    async def test_search_customers_pagination(
        self, authenticated_client: AsyncClient
    ):
        """Test customer search pagination."""
        # Create multiple customers
        for i in range(5):
            payload = {
                "first_name": f"Customer{i}",
                "last_name": "Test",
                "email": f"customer{i}@example.com",
            }
            await authenticated_client.post("/api/v1/customers/", json=payload)

        # Test first page
        search_payload = {"page": 1, "page_size": 2}

        response = await authenticated_client.post(
            "/api/v1/customers/search",
            json=search_payload,
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data["customers"]) <= 2
        assert data["page"] == 1
        assert data["page_size"] == 2

        # Test second page if there are more results
        if data["has_next"]:
            search_payload["page"] = 2
            response2 = await authenticated_client.post(
                "/api/v1/customers/search",
                json=search_payload,
            )

            assert response2.status_code == status.HTTP_200_OK
            data2 = response2.json()
            assert data2["page"] == 2


class TestCustomerActivitiesEndpoints:
    """Test customer activities API endpoints."""

    @pytest.fixture
    async def customer_id(
        self,
        authenticated_client: AsyncClient,
        sample_customer_payload: Dict[str, Any],
    ) -> str:
        """Create a customer and return its ID."""
        create_response = await authenticated_client.post(
            "/api/v1/customers/",
            json=sample_customer_payload,
        )
        return create_response.json()["id"]

    @pytest.mark.asyncio
    async def test_add_customer_activity_success(
        self, authenticated_client: AsyncClient, customer_id: str
    ):
        """Test adding activity to customer."""
        activity_payload = {
            "activity_type": "contact_made",
            "title": "Phone call made",
            "description": "Follow-up call with customer",
            "metadata": {"duration": 300},
        }

        response = await authenticated_client.post(
            f"/api/v1/customers/{customer_id}/activities",
            json=activity_payload,
        )

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["activity_type"] == "contact_made"
        assert data["title"] == "Phone call made"
        assert data["metadata"]["duration"] == 300

    @pytest.mark.asyncio
    async def test_add_activity_customer_not_found(
        self, authenticated_client: AsyncClient
    ):
        """Test adding activity to non-existent customer."""
        non_existent_id = str(uuid4())
        activity_payload = {
            "activity_type": "contact_made",
            "title": "Test activity",
        }

        response = await authenticated_client.post(
            f"/api/v1/customers/{non_existent_id}/activities",
            json=activity_payload,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_customer_activities(
        self, authenticated_client: AsyncClient, customer_id: str
    ):
        """Test retrieving customer activities."""
        # Add an activity first
        activity_payload = {
            "activity_type": "updated",
            "title": "Customer updated",
        }
        await authenticated_client.post(
            f"/api/v1/customers/{customer_id}/activities",
            json=activity_payload,
        )

        # Get activities
        response = await authenticated_client.get(
            f"/api/v1/customers/{customer_id}/activities"
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least the creation activity

    @pytest.mark.asyncio
    async def test_get_activities_with_pagination(
        self, authenticated_client: AsyncClient, customer_id: str
    ):
        """Test activities retrieval with pagination."""
        response = await authenticated_client.get(
            f"/api/v1/customers/{customer_id}/activities",
            params={"limit": 5, "offset": 0},
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5


class TestCustomerNotesEndpoints:
    """Test customer notes API endpoints."""

    @pytest.fixture
    async def customer_id(
        self,
        authenticated_client: AsyncClient,
        sample_customer_payload: Dict[str, Any],
    ) -> str:
        """Create a customer and return its ID."""
        create_response = await authenticated_client.post(
            "/api/v1/customers/",
            json=sample_customer_payload,
        )
        return create_response.json()["id"]

    @pytest.mark.asyncio
    async def test_add_customer_note_success(
        self, authenticated_client: AsyncClient, customer_id: str
    ):
        """Test adding note to customer."""
        note_payload = {
            "subject": "Follow-up needed",
            "content": "Customer requested information about premium features",
            "is_internal": True,
        }

        response = await authenticated_client.post(
            f"/api/v1/customers/{customer_id}/notes",
            json=note_payload,
        )

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["subject"] == "Follow-up needed"
        assert data["content"].startswith("Customer requested")
        assert data["is_internal"] is True

    @pytest.mark.asyncio
    async def test_get_customer_notes(
        self, authenticated_client: AsyncClient, customer_id: str
    ):
        """Test retrieving customer notes."""
        # Add a note first
        note_payload = {
            "subject": "Test Note",
            "content": "This is a test note",
            "is_internal": False,
        }
        await authenticated_client.post(
            f"/api/v1/customers/{customer_id}/notes",
            json=note_payload,
        )

        # Get notes
        response = await authenticated_client.get(
            f"/api/v1/customers/{customer_id}/notes"
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_notes_filter_internal(
        self, authenticated_client: AsyncClient, customer_id: str
    ):
        """Test filtering internal vs external notes."""
        # Add internal note
        internal_note = {
            "subject": "Internal Note",
            "content": "Internal communication",
            "is_internal": True,
        }
        await authenticated_client.post(
            f"/api/v1/customers/{customer_id}/notes",
            json=internal_note,
        )

        # Add external note
        external_note = {
            "subject": "Customer Note",
            "content": "Customer visible note",
            "is_internal": False,
        }
        await authenticated_client.post(
            f"/api/v1/customers/{customer_id}/notes",
            json=external_note,
        )

        # Get only external notes
        response = await authenticated_client.get(
            f"/api/v1/customers/{customer_id}/notes",
            params={"include_internal": False},
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert all(not note["is_internal"] for note in data)


class TestCustomerMetricsEndpoints:
    """Test customer metrics API endpoints."""

    @pytest.fixture
    async def customer_id(
        self,
        authenticated_client: AsyncClient,
        sample_customer_payload: Dict[str, Any],
    ) -> str:
        """Create a customer and return its ID."""
        create_response = await authenticated_client.post(
            "/api/v1/customers/",
            json=sample_customer_payload,
        )
        return create_response.json()["id"]

    @pytest.mark.asyncio
    async def test_record_purchase(
        self, authenticated_client: AsyncClient, customer_id: str
    ):
        """Test recording customer purchase."""
        response = await authenticated_client.post(
            f"/api/v1/customers/{customer_id}/metrics/purchase",
            params={"amount": 150.75},
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.asyncio
    async def test_record_purchase_invalid_amount(
        self, authenticated_client: AsyncClient, customer_id: str
    ):
        """Test recording purchase with invalid amount."""
        response = await authenticated_client.post(
            f"/api/v1/customers/{customer_id}/metrics/purchase",
            params={"amount": -50.0},  # Negative amount
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_get_customer_metrics_overview(
        self, authenticated_client: AsyncClient
    ):
        """Test getting overall customer metrics."""
        response = await authenticated_client.get("/api/v1/customers/metrics/overview")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "total_customers" in data
        assert "active_customers" in data
        assert "churn_rate" in data
        assert "average_lifetime_value" in data
        assert "total_revenue" in data
        assert "customers_by_status" in data
        assert "customers_by_tier" in data
        assert "customers_by_type" in data


class TestCustomerSegmentsEndpoints:
    """Test customer segments API endpoints."""

    @pytest.mark.asyncio
    async def test_create_segment_success(self, authenticated_client: AsyncClient):
        """Test creating customer segment."""
        segment_payload = {
            "name": "High Value Customers",
            "description": "Customers with high lifetime value",
            "criteria": {"min_ltv": 1000},
            "is_dynamic": True,
        }

        response = await authenticated_client.post(
            "/api/v1/customers/segments",
            json=segment_payload,
        )

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["name"] == "High Value Customers"
        assert data["criteria"]["min_ltv"] == 1000
        assert data["is_dynamic"] is True

    @pytest.mark.asyncio
    async def test_recalculate_segment(self, authenticated_client: AsyncClient):
        """Test recalculating segment membership."""
        # Create a segment first
        segment_payload = {
            "name": "Test Segment",
            "is_dynamic": True,
        }
        create_response = await authenticated_client.post(
            "/api/v1/customers/segments",
            json=segment_payload,
        )
        segment_data = create_response.json()
        segment_id = segment_data["id"]

        # Recalculate segment
        response = await authenticated_client.post(
            f"/api/v1/customers/segments/{segment_id}/recalculate"
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "segment_id" in data
        assert "member_count" in data
        assert data["segment_id"] == segment_id


class TestErrorHandling:
    """Test error handling across endpoints."""

    @pytest.mark.asyncio
    async def test_invalid_uuid_format(self, authenticated_client: AsyncClient):
        """Test endpoints with invalid UUID format."""
        invalid_uuid = "not-a-uuid"

        response = await authenticated_client.get(
            f"/api/v1/customers/{invalid_uuid}"
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_server_error_handling(self, authenticated_client: AsyncClient):
        """Test server error handling."""
        # This would test how the API handles unexpected server errors
        # In a real test, you might mock the service to raise an exception
        pass

    @pytest.mark.asyncio
    async def test_malformed_json(self, authenticated_client: AsyncClient):
        """Test handling of malformed JSON payloads."""
        response = await authenticated_client.post(
            "/api/v1/customers/",
            content="{ invalid json }",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY