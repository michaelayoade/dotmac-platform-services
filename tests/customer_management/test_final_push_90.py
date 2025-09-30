"""
Final push to reach 90% coverage - simple tests for remaining lines.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

from dotmac.platform.customer_management.service import CustomerService
from dotmac.platform.customer_management.models import Customer


@pytest.fixture
def mock_session():
    """Mock session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def service(mock_session):
    """Service instance."""
    return CustomerService(mock_session)


class TestFinalCoverage:
    """Simple tests to reach 90%."""

    @pytest.mark.asyncio
    async def test_get_customer_none(self, service, mock_session):
        """Test get_customer returns None when not found."""
        # Cover lines 127-132
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.get_customer(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_customer_by_number_none(self, service, mock_session):
        """Test get_customer_by_number returns None."""
        # Cover lines 161, 163
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.get_customer_by_number("CUST-999")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_customer_by_email_none(self, service, mock_session):
        """Test get_customer_by_email returns None."""
        # Cover lines 183
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.get_customer_by_email("notfound@example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_customer_not_found(self, service, mock_session):
        """Test delete returns False when customer not found."""
        # Cover line 203
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.delete_customer(uuid4())
        assert result is False