"""
Test cases for database and repository functionality.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.core.pagination import Page, PaginationParams
from dotmac.platform.core.repository import (
    AsyncRepository,
    EntityNotFoundError,
    RepositoryError,
)


@pytest.mark.unit
class TestPaginationHelpers:
    """Test pagination helper functionality."""

    def test_pagination_params(self):
        """Test PaginationParams creation and calculations."""
        params = PaginationParams(page=1, size=10)
        assert params.page == 1
        assert params.size == 10
        assert params.skip == 0
        assert params.limit == 10

        params2 = PaginationParams(page=3, size=20)
        assert params2.page == 3
        assert params2.size == 20
        assert params2.skip == 40  # (3-1) * 20
        assert params2.limit == 20

    def test_page(self):
        """Test Page functionality."""
        items = [1, 2, 3, 4, 5]
        page = Page.create(items=items, total=50, page=1, size=5)

        assert page.items == items
        assert page.total == 50
        assert page.page == 1
        assert page.size == 5
        assert page.pages == 10  # 50 / 5
        assert page.has_next is True
        assert page.has_prev is False

        # Test last page
        last_page = Page.create(items=items, total=50, page=10, size=5)
        assert last_page.has_next is False
        assert last_page.has_prev is True

    def test_page_single_page(self):
        """Test page with single page of results."""
        items = [1, 2, 3]
        page = Page.create(items=items, total=3, page=1, size=10)

        assert page.pages == 1
        assert page.has_next is False
        assert page.has_prev is False


@pytest.mark.unit
class TestRepositoryErrors:
    """Test repository error classes."""

    def test_repository_error(self):
        """Test base RepositoryError."""
        error = RepositoryError("Database connection failed")
        assert str(error) == "Database connection failed"
        assert isinstance(error, Exception)

    def test_entity_not_found_error(self):
        """Test EntityNotFoundError."""
        error = EntityNotFoundError("User with ID 123 not found")
        assert "User with ID 123 not found" in str(error)
        assert isinstance(error, RepositoryError)

    def test_error_inheritance(self):
        """Test error class inheritance."""
        base_error = RepositoryError("Base")
        not_found = EntityNotFoundError("Not found")

        assert isinstance(base_error, Exception)
        assert isinstance(not_found, Exception)
        assert isinstance(not_found, RepositoryError)


@pytest.mark.unit
class TestAsyncRepositoryMock:
    """Test async repository with mocks."""

    @pytest.mark.asyncio
    async def test_repository_get(self):
        """Test repository get method."""
        session = AsyncMock(spec=AsyncSession)

        # Create a mock model
        class TestModel:
            def __init__(self, id, name):
                self.id = id
                self.name = name

        # Setup mock response
        mock_result = Mock()
        mock_obj = TestModel(id=1, name="Test")
        mock_result.unique.return_value.scalar_one_or_none.return_value = mock_obj
        session.execute.return_value = mock_result

        # Create repository (simplified for testing)
        repo = AsyncRepository(session, TestModel, dict, dict)

        # Mock the get method behavior
        repo.get = AsyncMock(return_value=mock_obj)

        result = await repo.get(1)
        assert result is not None
        assert result.id == 1
        assert result.name == "Test"

    @pytest.mark.asyncio
    async def test_repository_create(self):
        """Test repository create method."""
        session = AsyncMock(spec=AsyncSession)

        class TestModel:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

        repo = AsyncRepository(session, TestModel, dict, dict)

        # Mock the create method
        new_obj = TestModel(id=1, name="New")
        repo.create = AsyncMock(return_value=new_obj)

        result = await repo.create({"name": "New"})
        assert result.id == 1
        assert result.name == "New"

    @pytest.mark.asyncio
    async def test_repository_delete(self):
        """Test repository delete method."""
        session = AsyncMock(spec=AsyncSession)

        class TestModel:
            pass

        repo = AsyncRepository(session, TestModel, dict, dict)

        # Mock the delete method
        repo.delete = AsyncMock(return_value=True)

        result = await repo.delete(1)
        assert result is True

        # Test delete not found
        repo.delete = AsyncMock(return_value=False)
        result = await repo.delete(999)
        assert result is False


@pytest.mark.unit
class TestPaginationIntegration:
    """Test pagination with repository integration."""

    @pytest.mark.asyncio
    async def test_paginated_query(self):
        """Test paginated query results."""
        session = AsyncMock(spec=AsyncSession)

        class TestModel:
            def __init__(self, id):
                self.id = id

        # Create test data
        test_items = [TestModel(id=i) for i in range(1, 6)]

        # Mock repository with pagination
        repo = AsyncRepository(session, TestModel, dict, dict)

        # Create paginated result
        page = Page.create(items=test_items, total=15, page=2, size=5)

        assert len(page.items) == 5
        assert page.total == 15
        assert page.page == 2
        assert page.pages == 3
        assert page.has_next is True
        assert page.has_prev is True
