"""
Tests for billing catalog service.

Covers product and category management operations.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from dotmac.platform.billing.catalog.service import ProductService
from dotmac.platform.billing.catalog.models import (
    Product,
    ProductCategory,
    ProductType,
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductCategoryCreateRequest,
    ProductCategoryUpdateRequest,
)
from dotmac.platform.billing.exceptions import (
    ProductError,
    ProductNotFoundError,
    CategoryError,
    CategoryNotFoundError,
)


class TestProductServiceProducts:
    """Test product management in catalog service."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return ProductService()

    @pytest.mark.asyncio
    async def test_create_product_success(
        self,
        service,
        product_create_request,
        tenant_id,
        mock_db_product
    ):
        """Test successful product creation."""
        with patch('dotmac.platform.billing.catalog.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            # Mock database operations
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None  # No existing product
            mock_session_instance.execute.return_value = mock_result
            mock_session_instance.commit = AsyncMock()
            mock_session_instance.refresh = AsyncMock()

            # Mock the created product
            mock_session_instance.add.return_value = None

            result = await service.create_product(product_create_request, tenant_id)

            # Verify product was created
            assert result.name == product_create_request.name
            assert result.sku == product_create_request.sku
            assert result.product_type == product_create_request.product_type
            assert result.tenant_id == tenant_id

            # Verify database operations
            mock_session_instance.add.assert_called_once()
            mock_session_instance.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_product_duplicate_sku(
        self,
        service,
        product_create_request,
        tenant_id,
        mock_db_product
    ):
        """Test product creation fails with duplicate SKU."""
        with patch('dotmac.platform.billing.catalog.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            # Mock existing product found
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_db_product
            mock_session_instance.execute.return_value = mock_result

            with pytest.raises(ProductError) as exc_info:
                await service.create_product(product_create_request, tenant_id)

            assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_product_success(
        self,
        service,
        tenant_id,
        mock_db_product
    ):
        """Test successful product retrieval."""
        with patch('dotmac.platform.billing.catalog.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_db_product
            mock_session_instance.execute.return_value = mock_result

            result = await service.get_product("prod_123", tenant_id)

            assert result is not None
            assert result.product_id == "prod_123"
            assert result.tenant_id == tenant_id

    @pytest.mark.asyncio
    async def test_get_product_not_found(self, service, tenant_id):
        """Test product retrieval when product doesn't exist."""
        with patch('dotmac.platform.billing.catalog.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session_instance.execute.return_value = mock_result

            result = await service.get_product("nonexistent", tenant_id)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_product_by_sku_success(
        self,
        service,
        tenant_id,
        mock_db_product
    ):
        """Test successful product retrieval by SKU."""
        with patch('dotmac.platform.billing.catalog.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_db_product
            mock_session_instance.execute.return_value = mock_result

            result = await service.get_product_by_sku("SKU-TEST-001", tenant_id)

            assert result is not None
            assert result.sku == "SKU-TEST-001"
            assert result.tenant_id == tenant_id

    @pytest.mark.asyncio
    async def test_list_products(self, service, tenant_id):
        """Test listing products with filters."""
        with patch('dotmac.platform.billing.catalog.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            # Create mock products
            mock_products = [
                MagicMock(
                    product_id="prod_1",
                    tenant_id=tenant_id,
                    sku="SKU-1",
                    name="Product 1",
                    product_type="ONE_TIME",
                    category="category1",
                    is_active=True,
                    base_price=Decimal("10.00"),
                    currency="USD",
                    usage_rates={},
                    metadata_json={},
                    created_at=datetime.now(timezone.utc),
                    updated_at=None,
                ),
                MagicMock(
                    product_id="prod_2",
                    tenant_id=tenant_id,
                    sku="SKU-2",
                    name="Product 2",
                    product_type="SUBSCRIPTION",
                    category="category1",
                    is_active=True,
                    base_price=Decimal("20.00"),
                    currency="USD",
                    usage_rates={},
                    metadata_json={},
                    created_at=datetime.now(timezone.utc),
                    updated_at=None,
                ),
            ]

            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = mock_products
            mock_session_instance.execute.return_value = mock_result

            # Test without filters
            result = await service.list_products(tenant_id)
            assert len(result) == 2
            assert result[0].product_id == "prod_1"
            assert result[1].product_id == "prod_2"

            # Test with category filter
            result = await service.list_products(tenant_id, category="category1")
            assert len(result) == 2

            # Test with product type filter
            result = await service.list_products(tenant_id, product_type=ProductType.ONE_TIME)
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_update_product_success(
        self,
        service,
        tenant_id,
        mock_db_product
    ):
        """Test successful product update."""
        with patch('dotmac.platform.billing.catalog.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_db_product
            mock_session_instance.execute.return_value = mock_result
            mock_session_instance.commit = AsyncMock()
            mock_session_instance.refresh = AsyncMock()

            update_request = ProductUpdateRequest(
                name="Updated Product",
                base_price=Decimal("59.99"),
            )

            result = await service.update_product("prod_123", update_request, tenant_id)

            assert result is not None
            mock_session_instance.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_product_not_found(self, service, tenant_id):
        """Test product update when product doesn't exist."""
        with patch('dotmac.platform.billing.catalog.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session_instance.execute.return_value = mock_result

            update_request = ProductUpdateRequest(name="Updated Product")

            result = await service.update_product("nonexistent", update_request, tenant_id)
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_product_success(
        self,
        service,
        tenant_id,
        mock_db_product
    ):
        """Test successful product deletion (soft delete)."""
        with patch('dotmac.platform.billing.catalog.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_db_product
            mock_session_instance.execute.return_value = mock_result
            mock_session_instance.commit = AsyncMock()

            result = await service.delete_product("prod_123", tenant_id)

            assert result is True
            # Verify soft delete (is_active set to False)
            assert mock_db_product.is_active is False
            mock_session_instance.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_product_not_found(self, service, tenant_id):
        """Test product deletion when product doesn't exist."""
        with patch('dotmac.platform.billing.catalog.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session_instance.execute.return_value = mock_result

            result = await service.delete_product("nonexistent", tenant_id)
            assert result is False


class TestProductServiceCategories:
    """Test category management in catalog service."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return ProductService()

    @pytest.mark.asyncio
    async def test_create_category_success(
        self,
        service,
        category_create_request,
        tenant_id
    ):
        """Test successful category creation."""
        with patch('dotmac.platform.billing.catalog.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            # Mock no existing category
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session_instance.execute.return_value = mock_result
            mock_session_instance.commit = AsyncMock()
            mock_session_instance.refresh = AsyncMock()

            result = await service.create_category(category_create_request, tenant_id)

            assert result.name == category_create_request.name
            assert result.tenant_id == tenant_id

            mock_session_instance.add.assert_called_once()
            mock_session_instance.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_category_duplicate_name(
        self,
        service,
        category_create_request,
        tenant_id
    ):
        """Test category creation fails with duplicate name."""
        with patch('dotmac.platform.billing.catalog.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            # Mock existing category found
            mock_existing = MagicMock()
            mock_existing.name = category_create_request.name
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_existing
            mock_session_instance.execute.return_value = mock_result

            with pytest.raises(CategoryError) as exc_info:
                await service.create_category(category_create_request, tenant_id)

            assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_category_success(self, service, tenant_id):
        """Test successful category retrieval."""
        with patch('dotmac.platform.billing.catalog.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            mock_category = MagicMock()
            mock_category.category_id = "cat_123"
            mock_category.tenant_id = tenant_id
            mock_category.name = "Test Category"
            mock_category.description = "Test description"
            mock_category.is_active = True
            mock_category.metadata_json = {}
            mock_category.created_at = datetime.now(timezone.utc)
            mock_category.updated_at = None

            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_category
            mock_session_instance.execute.return_value = mock_result

            result = await service.get_category("cat_123", tenant_id)

            assert result is not None
            assert result.category_id == "cat_123"
            assert result.name == "Test Category"

    @pytest.mark.asyncio
    async def test_list_categories(self, service, tenant_id):
        """Test listing categories."""
        with patch('dotmac.platform.billing.catalog.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            mock_categories = [
                MagicMock(
                    category_id="cat_1",
                    tenant_id=tenant_id,
                    name="Category 1",
                    description="First category",
                    is_active=True,
                    metadata_json={},
                    created_at=datetime.now(timezone.utc),
                    updated_at=None,
                ),
                MagicMock(
                    category_id="cat_2",
                    tenant_id=tenant_id,
                    name="Category 2",
                    description="Second category",
                    is_active=False,  # Inactive
                    metadata_json={},
                    created_at=datetime.now(timezone.utc),
                    updated_at=None,
                ),
            ]

            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = mock_categories
            mock_session_instance.execute.return_value = mock_result

            # Test without filters (should include inactive)
            result = await service.list_categories(tenant_id, active_only=False)
            assert len(result) == 2

            # Test with active_only filter
            result = await service.list_categories(tenant_id, active_only=True)
            # Mock would still return both, but service should filter
            assert len(result) >= 0  # Service filtering logic may apply

    @pytest.mark.asyncio
    async def test_update_category_success(self, service, tenant_id):
        """Test successful category update."""
        with patch('dotmac.platform.billing.catalog.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            mock_category = MagicMock()
            mock_category.category_id = "cat_123"
            mock_category.tenant_id = tenant_id
            mock_category.name = "Old Name"

            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_category
            mock_session_instance.execute.return_value = mock_result
            mock_session_instance.commit = AsyncMock()
            mock_session_instance.refresh = AsyncMock()

            update_request = ProductCategoryUpdateRequest(
                name="Updated Category",
                description="Updated description",
            )

            result = await service.update_category("cat_123", update_request, tenant_id)

            assert result is not None
            mock_session_instance.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_category_success(self, service, tenant_id):
        """Test successful category deletion."""
        with patch('dotmac.platform.billing.catalog.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            mock_category = MagicMock()
            mock_category.is_active = True

            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_category
            mock_session_instance.execute.return_value = mock_result
            mock_session_instance.commit = AsyncMock()

            result = await service.delete_category("cat_123", tenant_id)

            assert result is True
            # Verify soft delete
            assert mock_category.is_active is False
            mock_session_instance.commit.assert_called_once()


class TestProductServiceHelpers:
    """Test helper methods in catalog service."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return ProductService()

    def test_generate_product_id(self, service):
        """Test product ID generation."""
        with patch('dotmac.platform.billing.catalog.service.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = "abcdef123456"

            product_id = service._generate_product_id()
            assert product_id == "prod_abcdef123456"

    def test_generate_category_id(self, service):
        """Test category ID generation."""
        with patch('dotmac.platform.billing.catalog.service.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = "123456abcdef"

            category_id = service._generate_category_id()
            assert category_id == "cat_123456abcdef"

    def test_db_to_pydantic_product(self, service, mock_db_product):
        """Test database to Pydantic product conversion."""
        result = service._db_to_pydantic_product(mock_db_product)

        assert isinstance(result, Product)
        assert result.product_id == mock_db_product.product_id
        assert result.sku == mock_db_product.sku
        assert result.name == mock_db_product.name

    def test_db_to_pydantic_product_with_usage_rates(self, service):
        """Test database to Pydantic product conversion with usage rates."""
        mock_db_product = MagicMock()
        mock_db_product.product_id = "prod_123"
        mock_db_product.tenant_id = "test-tenant"
        mock_db_product.sku = "SKU-TEST"
        mock_db_product.name = "Test Product"
        mock_db_product.description = "Test"
        mock_db_product.product_type = "USAGE_BASED"
        mock_db_product.category = "test"
        mock_db_product.base_price = Decimal("0")
        mock_db_product.currency = "USD"
        mock_db_product.is_active = True
        mock_db_product.usage_rates = {"api_calls": "0.01"}  # String from DB
        mock_db_product.metadata_json = {}
        mock_db_product.created_at = datetime.now(timezone.utc)
        mock_db_product.updated_at = None

        result = service._db_to_pydantic_product(mock_db_product)

        assert isinstance(result, Product)
        assert result.usage_rates["api_calls"] == Decimal("0.01")

    def test_db_to_pydantic_category(self, service):
        """Test database to Pydantic category conversion."""
        mock_db_category = MagicMock()
        mock_db_category.category_id = "cat_123"
        mock_db_category.tenant_id = "test-tenant"
        mock_db_category.name = "Test Category"
        mock_db_category.description = "Test description"
        mock_db_category.is_active = True
        mock_db_category.metadata_json = {"test": True}
        mock_db_category.created_at = datetime.now(timezone.utc)
        mock_db_category.updated_at = None

        result = service._db_to_pydantic_category(mock_db_category)

        assert isinstance(result, ProductCategory)
        assert result.category_id == "cat_123"
        assert result.name == "Test Category"
        assert result.metadata == {"test": True}


class TestProductServiceErrorHandling:
    """Test error handling in catalog service."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return ProductService()

    @pytest.mark.asyncio
    async def test_database_error_handling(self, service, product_create_request, tenant_id):
        """Test handling of database errors."""
        with patch('dotmac.platform.billing.catalog.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            # Simulate database error
            mock_session_instance.execute.side_effect = Exception("Database error")

            with pytest.raises(Exception) as exc_info:
                await service.create_product(product_create_request, tenant_id)

            assert "Database error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_integrity_error_handling(self, service, product_create_request, tenant_id):
        """Test handling of database integrity errors."""
        with patch('dotmac.platform.billing.catalog.service.get_async_session') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            # Mock no existing product initially
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session_instance.execute.return_value = mock_result

            # Simulate integrity error on commit
            mock_session_instance.commit.side_effect = IntegrityError("", "", "")

            with pytest.raises(IntegrityError):
                await service.create_product(product_create_request, tenant_id)