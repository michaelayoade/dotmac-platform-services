"""
Simple router tests using direct function calls to improve coverage.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from dotmac.platform.customer_management.router import (
    get_customer_service,
)
from dotmac.platform.customer_management.service import CustomerService
from dotmac.platform.customer_management.models import Customer


class TestRouterSimple:
    """Simple router tests to improve coverage."""

    @pytest.mark.asyncio
    async def test_get_customer_service_dependency(self):
        """Test the service dependency function."""
        # This covers line 39-43
        mock_session = AsyncMock()

        service = await get_customer_service(mock_session)

        assert isinstance(service, CustomerService)
        assert service.session == mock_session

    @pytest.mark.asyncio
    async def test_router_imports(self):
        """Test that router imports are working."""
        # Import all router functions to ensure they're defined
        from dotmac.platform.customer_management.router import (
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
            router,
        )

        # Verify router is configured
        assert router.prefix == "/customers"
        assert "customers" in router.tags

    @pytest.mark.asyncio
    async def test_create_customer_validation_error_path(self):
        """Test create customer error handling."""
        from dotmac.platform.customer_management.router import create_customer
        from dotmac.platform.customer_management.schemas import CustomerCreate
        from dotmac.platform.auth.core import UserInfo
        from sqlalchemy.exc import IntegrityError

        # Create mock dependencies
        mock_service = AsyncMock()
        mock_service.create_customer.side_effect = IntegrityError(
            "Duplicate email",
            params=None,
            orig=None,
        )

        mock_user = UserInfo(
            user_id="test",
            username="test",
            email="test@test.com",
            roles=["user"],
            tenant_id="test",
        )

        customer_data = CustomerCreate(
            email="duplicate@example.com",
            first_name="Test",
            last_name="User",
        )

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await create_customer(
                data=customer_data,
                service=mock_service,
                current_user=mock_user,
            )

        assert exc_info.value.status_code == 400