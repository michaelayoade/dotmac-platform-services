"""
Example of strategic test management using the new test utilities.

This demonstrates how to use the test_utils module to create maintainable,
reliable tests that address common failure patterns.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone, timedelta

from tests.test_utils import (
    AsyncTestCase,
    create_async_session_mock,
    TestDataFactory,
    TenantContext,
    utcnow,
    with_tenant_context
)
from dotmac.platform.billing.invoicing.service import InvoiceService
from dotmac.platform.billing.core.enums import InvoiceStatus


class TestInvoiceServiceStrategic(AsyncTestCase):
    """
    Strategic test implementation using standardized utilities.

    This test class demonstrates:
    1. Using base classes for common setup
    2. Proper async session mocking
    3. Tenant context management
    4. Consistent test data creation
    5. Fixed datetime usage
    """

    @pytest.fixture(autouse=True)
    def setup_invoice_service(self):
        """Setup invoice service with proper mocks."""
        # Initialize test utilities
        self.session = create_async_session_mock()
        self.factory = TestDataFactory()

        # Create invoice service with mocked session
        self.invoice_service = InvoiceService(self.session)

        # Setup common test data
        self.tenant_id = "test-tenant-123"
        self.customer_id = str(self.factory.create_user()["id"])

    @pytest.mark.asyncio
    @with_tenant_context("test-tenant-123")
    async def test_create_invoice_with_tenant_isolation_fixed(self):
        """
        Test creating an invoice with proper tenant isolation.

        This test demonstrates the strategic approach:
        - Uses proper async session mocking (no coroutine warnings)
        - Uses timezone-aware datetime (no deprecation warnings)
        - Uses tenant context manager
        - Uses test data factory for consistency
        """

        # Arrange: Create test data using factory
        invoice_data = self.factory.create_invoice(overrides={
            "customer_id": self.customer_id,
            "tenant_id": self.tenant_id,
            "line_items": [
                {
                    "description": "Test Service",
                    "quantity": 1,
                    "unit_price": 5000,  # $50.00 in cents
                    "total_price": 5000
                }
            ]
        })

        # Mock the database operations properly
        mock_invoice = Mock()
        mock_invoice.id = invoice_data["id"]
        mock_invoice.invoice_number = invoice_data["invoice_number"]
        mock_invoice.tenant_id = self.tenant_id
        mock_invoice.customer_id = self.customer_id
        mock_invoice.status = InvoiceStatus.DRAFT
        mock_invoice.total_amount = 5000
        mock_invoice.created_at = utcnow()  # Uses timezone-aware datetime

        # Configure session to return our mock invoice
        self.session.execute.return_value.scalar_one_or_none.return_value = None  # For uniqueness check

        with patch('dotmac.platform.billing.invoicing.service.InvoiceEntity') as MockInvoice:
            MockInvoice.return_value = mock_invoice

            # Act: Create the invoice
            result = await self.invoice_service.create_invoice(
                customer_id=self.customer_id,
                line_items=invoice_data["line_items"],
                tenant_id=self.tenant_id
            )

        # Assert: Verify the result
        assert result.id == invoice_data["id"]
        assert result.tenant_id == self.tenant_id
        assert result.status == InvoiceStatus.DRAFT

        # Verify database operations were called
        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(mock_invoice)

    @pytest.mark.asyncio
    async def test_get_invoice_with_tenant_context(self):
        """
        Test retrieving invoice with tenant isolation.

        Demonstrates how tenant context ensures proper data isolation.
        """

        invoice_id = "test-invoice-123"

        # Create mock invoice with tenant context
        with TenantContext(self.tenant_id) as tenant:
            mock_invoice = Mock()
            mock_invoice.id = invoice_id
            mock_invoice.tenant_id = tenant.current
            mock_invoice.status = InvoiceStatus.DRAFT

            # Configure session to return invoice
            self.session.execute.return_value.scalar_one_or_none.return_value = mock_invoice

            # Act
            result = await self.invoice_service.get_invoice(invoice_id)

            # Assert
            assert result.id == invoice_id
            assert result.tenant_id == tenant.current

    @pytest.mark.asyncio
    async def test_invoice_date_handling_fixed(self):
        """
        Test that invoice dates are handled with timezone awareness.

        This fixes the datetime.utcnow() deprecation warnings.
        """

        # Use the fixed utcnow() function
        issue_date = utcnow()
        due_date = issue_date + timedelta(days=30)

        invoice_data = self.factory.create_invoice(overrides={
            "issue_date": issue_date,
            "due_date": due_date,
            "customer_id": self.customer_id,
            "tenant_id": self.tenant_id
        })

        # Verify dates are timezone-aware
        assert issue_date.tzinfo is not None
        assert due_date.tzinfo is not None
        assert isinstance(issue_date, datetime)

        # Mock and test invoice creation with proper dates
        mock_invoice = Mock()
        mock_invoice.issue_date = issue_date
        mock_invoice.due_date = due_date

        self.session.execute.return_value.scalar_one_or_none.return_value = None

        with patch('dotmac.platform.billing.invoicing.service.InvoiceEntity') as MockInvoice:
            MockInvoice.return_value = mock_invoice

            result = await self.invoice_service.create_invoice(
                customer_id=self.customer_id,
                line_items=invoice_data["line_items"],
                issue_date=issue_date,
                due_date=due_date,
                tenant_id=self.tenant_id
            )

        assert result.issue_date == issue_date
        assert result.due_date == due_date


# ============================================================================
# Integration Test Example
# ============================================================================

@pytest.mark.integration  # Can be run separately
class TestInvoiceServiceIntegration:
    """
    Integration test example using strategic utilities.

    Shows how to test actual service integration with minimal mocking.
    """

    @pytest.fixture(autouse=True)
    async def setup_integration(self, async_db_session):
        """Setup for integration tests with real database."""
        self.session = async_db_session
        self.service = InvoiceService(self.session)
        self.factory = TestDataFactory()

    @pytest.mark.asyncio
    async def test_invoice_lifecycle_integration(self):
        """
        Test complete invoice lifecycle with real database operations.

        This test uses the actual database but with controlled test data.
        """

        # This would use actual database operations
        # but with the test utilities for data creation
        invoice_data = self.factory.create_invoice()

        # Test would proceed with real database calls
        # but isolated within a transaction that rolls back

        assert True  # Placeholder for actual implementation


# ============================================================================
# Performance Test Example
# ============================================================================

class TestInvoiceServicePerformance:
    """
    Performance test example using strategic utilities.
    """

    def setup_method(self):
        """Setup for performance tests."""
        self.factory = TestDataFactory()
        self.session_mock = create_async_session_mock()

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_bulk_invoice_creation_performance(self):
        """
        Test performance of bulk invoice creation.

        Uses consistent test data and proper mocking.
        """

        # Generate bulk test data
        invoice_batch = [
            self.factory.create_invoice(overrides={"customer_id": f"customer-{i}"})
            for i in range(100)
        ]

        # Test with proper async mocking
        service = InvoiceService(self.session_mock)

        # Performance test would measure timing here
        # This demonstrates the setup approach
        assert len(invoice_batch) == 100