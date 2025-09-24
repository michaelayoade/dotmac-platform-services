"""
Integration tests for customer management module.

Tests end-to-end functionality including:
- Full customer lifecycle management
- Cross-module integrations
- Database transactions and consistency
- Performance under load
"""

import asyncio
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from typing import List
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.customer_management.models import (
    Customer,
    CustomerActivity,
    CustomerNote,
    ActivityType,
    CustomerStatus,
    CustomerTier,
)
from dotmac.platform.customer_management.service import CustomerService
from dotmac.platform.customer_management.schemas import CustomerCreate


class TestCustomerLifecycleIntegration:
    """Test complete customer lifecycle management."""

    @pytest.mark.asyncio
    async def test_complete_customer_journey(
        self, authenticated_client: AsyncClient, async_db_session: AsyncSession
    ):
        """Test complete customer journey from creation to deletion."""

        # 1. Create customer
        customer_payload = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "customer_type": "individual",
            "tier": "free",
        }

        create_response = await authenticated_client.post(
            "/api/v1/customers/",
            json=customer_payload,
        )
        assert create_response.status_code == 201
        customer_data = create_response.json()
        customer_id = customer_data["id"]

        # 2. Verify customer was created in database
        result = await async_db_session.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        db_customer = result.scalar_one_or_none()
        assert db_customer is not None
        assert db_customer.first_name == "John"
        assert db_customer.status == CustomerStatus.PROSPECT

        # 3. Add activity
        activity_payload = {
            "activity_type": "contact_made",
            "title": "Initial contact",
            "description": "Welcome call completed",
        }

        activity_response = await authenticated_client.post(
            f"/api/v1/customers/{customer_id}/activities",
            json=activity_payload,
        )
        assert activity_response.status_code == 201

        # 4. Add note
        note_payload = {
            "subject": "Customer feedback",
            "content": "Very interested in premium features",
            "is_internal": False,
        }

        note_response = await authenticated_client.post(
            f"/api/v1/customers/{customer_id}/notes",
            json=note_payload,
        )
        assert note_response.status_code == 201

        # 5. Update customer (upgrade tier)
        update_payload = {
            "tier": "premium",
            "status": "active",
        }

        update_response = await authenticated_client.patch(
            f"/api/v1/customers/{customer_id}",
            json=update_payload,
        )
        assert update_response.status_code == 200
        updated_data = update_response.json()
        assert updated_data["tier"] == "premium"
        assert updated_data["status"] == "active"

        # 6. Record purchase
        purchase_response = await authenticated_client.post(
            f"/api/v1/customers/{customer_id}/metrics/purchase",
            params={"amount": 299.99},
        )
        assert purchase_response.status_code == 204

        # 7. Verify metrics were updated
        get_response = await authenticated_client.get(
            f"/api/v1/customers/{customer_id}"
        )
        assert get_response.status_code == 200
        customer_with_metrics = get_response.json()
        assert customer_with_metrics["total_purchases"] == 1
        assert float(customer_with_metrics["lifetime_value"]) == 299.99

        # 8. Search for customer
        search_payload = {
            "query": "john doe",
            "status": "active",
        }

        search_response = await authenticated_client.post(
            "/api/v1/customers/search",
            json=search_payload,
        )
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert search_data["total"] >= 1
        assert any(c["id"] == customer_id for c in search_data["customers"])

        # 9. Get activities and notes
        activities_response = await authenticated_client.get(
            f"/api/v1/customers/{customer_id}/activities"
        )
        assert activities_response.status_code == 200
        activities = activities_response.json()
        assert len(activities) >= 2  # Creation + contact activity

        notes_response = await authenticated_client.get(
            f"/api/v1/customers/{customer_id}/notes"
        )
        assert notes_response.status_code == 200
        notes = notes_response.json()
        assert len(notes) == 1
        assert notes[0]["subject"] == "Customer feedback"

        # 10. Soft delete customer
        delete_response = await authenticated_client.delete(
            f"/api/v1/customers/{customer_id}"
        )
        assert delete_response.status_code == 204

        # 11. Verify customer is not accessible
        get_deleted_response = await authenticated_client.get(
            f"/api/v1/customers/{customer_id}"
        )
        assert get_deleted_response.status_code == 404

    @pytest.mark.asyncio
    async def test_customer_metrics_aggregation(
        self, authenticated_client: AsyncClient
    ):
        """Test that customer metrics aggregate correctly."""

        # Create multiple customers with different characteristics
        customers = []
        for i in range(5):
            customer_payload = {
                "first_name": f"Customer{i}",
                "last_name": "Test",
                "email": f"customer{i}@example.com",
                "customer_type": "individual" if i % 2 == 0 else "business",
                "tier": "free" if i < 2 else "premium",
            }

            response = await authenticated_client.post(
                "/api/v1/customers/",
                json=customer_payload,
            )
            customers.append(response.json())

        # Record purchases for some customers
        purchase_amounts = [100.0, 250.0, 500.0]
        for i, amount in enumerate(purchase_amounts):
            customer_id = customers[i]["id"]
            await authenticated_client.post(
                f"/api/v1/customers/{customer_id}/metrics/purchase",
                params={"amount": amount},
            )

        # Get overall metrics
        metrics_response = await authenticated_client.get(
            "/api/v1/customers/metrics/overview"
        )
        assert metrics_response.status_code == 200

        metrics = metrics_response.json()
        assert metrics["total_customers"] >= 5
        assert metrics["total_revenue"] >= 850.0  # Sum of purchases


class TestConcurrentOperations:
    """Test concurrent customer operations."""

    @pytest.mark.asyncio
    async def test_concurrent_customer_creation(
        self, authenticated_client: AsyncClient, async_db_session: AsyncSession
    ):
        """Test creating customers concurrently."""

        async def create_customer(index: int):
            customer_payload = {
                "first_name": f"Concurrent{index}",
                "last_name": "Customer",
                "email": f"concurrent{index}@example.com",
            }

            response = await authenticated_client.post(
                "/api/v1/customers/",
                json=customer_payload,
            )
            return response

        # Create 10 customers concurrently
        tasks = [create_customer(i) for i in range(10)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed
        successful_responses = [r for r in responses if not isinstance(r, Exception)]
        assert len(successful_responses) == 10

        for response in successful_responses:
            assert response.status_code == 201
            assert "customer_number" in response.json()

        # Verify all customers have unique customer numbers
        customer_numbers = [r.json()["customer_number"] for r in successful_responses]
        assert len(set(customer_numbers)) == 10  # All unique

    @pytest.mark.asyncio
    async def test_concurrent_customer_updates(
        self, authenticated_client: AsyncClient
    ):
        """Test updating same customer concurrently."""

        # Create a customer first
        customer_payload = {
            "first_name": "Concurrent",
            "last_name": "Update",
            "email": "concurrent.update@example.com",
        }

        create_response = await authenticated_client.post(
            "/api/v1/customers/",
            json=customer_payload,
        )
        customer_id = create_response.json()["id"]

        async def update_customer(field_value: str):
            update_payload = {"metadata": {"update_source": field_value}}

            response = await authenticated_client.patch(
                f"/api/v1/customers/{customer_id}",
                json=update_payload,
            )
            return response

        # Update same customer concurrently
        tasks = [update_customer(f"source_{i}") for i in range(5)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed
        successful_responses = [r for r in responses if not isinstance(r, Exception)]
        assert len(successful_responses) == 5

        for response in successful_responses:
            assert response.status_code == 200


class TestDataConsistency:
    """Test data consistency across operations."""

    @pytest.mark.asyncio
    async def test_activity_customer_relationship_consistency(
        self, async_db_session: AsyncSession
    ):
        """Test that activities are properly linked to customers."""

        service = CustomerService(async_db_session)

        # Create customer
        customer_data = CustomerCreate(
            first_name="Consistency",
            last_name="Test",
            email="consistency.test@example.com",
        )
        customer = await service.create_customer(customer_data, created_by="test")

        # Verify creation activity was added
        result = await async_db_session.execute(
            select(CustomerActivity).where(
                CustomerActivity.customer_id == customer.id
            )
        )
        activities = result.scalars().all()

        assert len(activities) == 1
        assert activities[0].activity_type == ActivityType.CREATED
        assert activities[0].customer_id == customer.id

        # Delete customer and verify activities are handled correctly
        await service.delete_customer(customer.id, hard_delete=True)

        # Activities should be deleted due to CASCADE
        result = await async_db_session.execute(
            select(CustomerActivity).where(
                CustomerActivity.customer_id == customer.id
            )
        )
        remaining_activities = result.scalars().all()
        assert len(remaining_activities) == 0

    @pytest.mark.asyncio
    async def test_soft_delete_consistency(
        self, async_db_session: AsyncSession
    ):
        """Test that soft delete works consistently."""

        service = CustomerService(async_db_session)

        # Create customer
        customer_data = CustomerCreate(
            first_name="SoftDelete",
            last_name="Test",
            email="softdelete.test@example.com",
        )
        customer = await service.create_customer(customer_data, created_by="test")

        # Add note
        from dotmac.platform.customer_management.schemas import CustomerNoteCreate
        note_data = CustomerNoteCreate(
            subject="Test Note",
            content="This is a test note",
        )
        await service.add_note(customer.id, note_data, uuid4())

        # Soft delete customer
        success = await service.delete_customer(customer.id, hard_delete=False)
        assert success

        # Customer should not be returned in regular queries
        retrieved = await service.get_customer(customer.id)
        assert retrieved is None

        # But should still exist in database (with deleted_at set)
        result = await async_db_session.execute(
            select(Customer).where(Customer.id == customer.id)
        )
        db_customer = result.scalar_one_or_none()
        assert db_customer is not None
        assert db_customer.deleted_at is not None

        # Notes should still exist
        result = await async_db_session.execute(
            select(CustomerNote).where(
                CustomerNote.customer_id == customer.id
            )
        )
        notes = result.scalars().all()
        assert len(notes) == 1


class TestSearchAndFiltering:
    """Test search and filtering functionality."""

    @pytest.mark.asyncio
    async def test_comprehensive_search_functionality(
        self, authenticated_client: AsyncClient
    ):
        """Test all search and filtering options."""

        # Create customers with different attributes
        test_customers = [
            {
                "first_name": "Alice",
                "last_name": "Smith",
                "email": "alice.smith@example.com",
                "customer_type": "individual",
                "tier": "premium",
                "status": "active",
                "city": "New York",
                "country": "US",
                "tags": ["vip", "early-adopter"],
            },
            {
                "first_name": "Bob",
                "last_name": "Johnson",
                "email": "bob.johnson@corp.com",
                "customer_type": "business",
                "tier": "enterprise",
                "status": "active",
                "city": "San Francisco",
                "country": "US",
                "company_name": "TechCorp",
                "tags": ["enterprise", "tech"],
            },
            {
                "first_name": "Charlie",
                "last_name": "Brown",
                "email": "charlie.brown@example.com",
                "customer_type": "individual",
                "tier": "basic",
                "status": "inactive",
                "city": "Chicago",
                "country": "US",
                "tags": ["basic-user"],
            },
        ]

        created_customers = []
        for customer_data in test_customers:
            response = await authenticated_client.post(
                "/api/v1/customers/",
                json=customer_data,
            )
            created_customers.append(response.json())

        # Test text search
        search_response = await authenticated_client.post(
            "/api/v1/customers/search",
            json={"query": "alice smith"},
        )
        assert search_response.status_code == 200
        search_results = search_response.json()
        assert search_results["total"] >= 1
        assert any(c["first_name"] == "Alice" for c in search_results["customers"])

        # Test status filter
        search_response = await authenticated_client.post(
            "/api/v1/customers/search",
            json={"status": "active"},
        )
        assert search_response.status_code == 200
        search_results = search_response.json()
        assert all(c["status"] == "active" for c in search_results["customers"])

        # Test tier filter
        search_response = await authenticated_client.post(
            "/api/v1/customers/search",
            json={"tier": "premium"},
        )
        assert search_response.status_code == 200
        search_results = search_response.json()
        assert all(c["tier"] == "premium" for c in search_results["customers"])

        # Test customer type filter
        search_response = await authenticated_client.post(
            "/api/v1/customers/search",
            json={"customer_type": "business"},
        )
        assert search_response.status_code == 200
        search_results = search_response.json()
        assert all(c["customer_type"] == "business" for c in search_results["customers"])

        # Test location filters
        search_response = await authenticated_client.post(
            "/api/v1/customers/search",
            json={"country": "US", "city": "New York"},
        )
        assert search_response.status_code == 200
        search_results = search_response.json()
        assert all(
            c["country"] == "US" and c["city"] == "New York"
            for c in search_results["customers"]
        )

        # Test tags filter
        search_response = await authenticated_client.post(
            "/api/v1/customers/search",
            json={"tags": ["vip"]},
        )
        assert search_response.status_code == 200
        search_results = search_response.json()
        assert all(
            "vip" in c.get("tags", [])
            for c in search_results["customers"]
        )

        # Test combined filters
        search_response = await authenticated_client.post(
            "/api/v1/customers/search",
            json={
                "customer_type": "individual",
                "tier": "premium",
                "status": "active",
            },
        )
        assert search_response.status_code == 200
        search_results = search_response.json()

        for customer in search_results["customers"]:
            assert customer["customer_type"] == "individual"
            assert customer["tier"] == "premium"
            assert customer["status"] == "active"


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases in integration scenarios."""

    @pytest.mark.asyncio
    async def test_duplicate_customer_handling(
        self, authenticated_client: AsyncClient
    ):
        """Test handling of duplicate customer creation attempts."""

        customer_payload = {
            "first_name": "Duplicate",
            "last_name": "Test",
            "email": "duplicate.test@example.com",
        }

        # Create first customer
        response1 = await authenticated_client.post(
            "/api/v1/customers/",
            json=customer_payload,
        )
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = await authenticated_client.post(
            "/api/v1/customers/",
            json=customer_payload,
        )
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_operations_on_nonexistent_customer(
        self, authenticated_client: AsyncClient
    ):
        """Test operations on non-existent customers."""

        non_existent_id = str(uuid4())

        # Try to get non-existent customer
        response = await authenticated_client.get(
            f"/api/v1/customers/{non_existent_id}"
        )
        assert response.status_code == 404

        # Try to update non-existent customer
        response = await authenticated_client.patch(
            f"/api/v1/customers/{non_existent_id}",
            json={"first_name": "Updated"},
        )
        assert response.status_code == 404

        # Try to add activity to non-existent customer
        response = await authenticated_client.post(
            f"/api/v1/customers/{non_existent_id}/activities",
            json={
                "activity_type": "updated",
                "title": "Test activity",
            },
        )
        assert response.status_code == 404

        # Try to add note to non-existent customer
        response = await authenticated_client.post(
            f"/api/v1/customers/{non_existent_id}/notes",
            json={
                "subject": "Test note",
                "content": "Test content",
            },
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_large_dataset_performance(
        self, authenticated_client: AsyncClient
    ):
        """Test performance with larger datasets."""

        # Create a reasonable number of customers for testing
        customer_count = 20
        customers = []

        for i in range(customer_count):
            customer_payload = {
                "first_name": f"Performance{i:03d}",
                "last_name": "Test",
                "email": f"performance{i:03d}@example.com",
                "customer_type": "individual" if i % 2 == 0 else "business",
                "tier": ["free", "basic", "premium"][i % 3],
                "tags": [f"tag{i % 5}", "performance-test"],
            }

            response = await authenticated_client.post(
                "/api/v1/customers/",
                json=customer_payload,
            )
            assert response.status_code == 201
            customers.append(response.json())

        # Test search performance
        search_response = await authenticated_client.post(
            "/api/v1/customers/search",
            json={"tags": ["performance-test"], "page_size": customer_count},
        )
        assert search_response.status_code == 200

        search_results = search_response.json()
        assert search_results["total"] == customer_count
        assert len(search_results["customers"]) == customer_count

        # Test pagination with larger dataset
        page_size = 5
        total_pages = (customer_count + page_size - 1) // page_size
        all_customers_paginated = []

        for page in range(1, total_pages + 1):
            search_response = await authenticated_client.post(
                "/api/v1/customers/search",
                json={
                    "tags": ["performance-test"],
                    "page": page,
                    "page_size": page_size,
                },
            )
            assert search_response.status_code == 200

            page_results = search_response.json()
            all_customers_paginated.extend(page_results["customers"])

        assert len(all_customers_paginated) == customer_count

        # Verify we got all customers and no duplicates
        customer_ids = [c["id"] for c in all_customers_paginated]
        assert len(set(customer_ids)) == customer_count  # No duplicates