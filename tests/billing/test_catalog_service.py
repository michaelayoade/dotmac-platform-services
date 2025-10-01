"""
Comprehensive catalog service tests for high coverage.

Tests the product catalog service layer with proper mocking.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, or_, func

from dotmac.platform.billing.catalog.models import (
    Product,
    ProductCategory,
    ProductType,
    TaxClass,
    ProductCreateRequest,
    ProductUpdateRequest,
)
from dotmac.platform.billing.catalog.service import ProductService
from dotmac.platform.billing.exceptions import ProductNotFoundError


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    session.scalar = AsyncMock()
    session.scalars = AsyncMock()
    return session


@pytest.fixture
def product_service():
    """Product service instance."""
    return ProductService()


@pytest.fixture
def sample_product_data():
    """Sample product data."""
    return {
        "product_id": "prod_123",
        "tenant_id": "tenant_123",
        "sku": "SKU-001",
        "name": "Test Product",
        "description": "Test description",
        "product_type": ProductType.SUBSCRIPTION,
        "category": "software",
        "base_price": Decimal("99.99"),
        "currency": "USD",
        "tax_class": TaxClass.STANDARD,
        "is_active": True,
        "metadata": {"tier": "pro"},
        "created_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_category_data():
    """Sample category data."""
    return {
        "category_id": "cat_123",
        "tenant_id": "tenant_123",
        "name": "Software Tools",
        "description": "Development tools",
        "parent_category_id": None,
        "sort_order": 1,
        "created_at": datetime.now(timezone.utc),
    }


class TestProductServiceCRUD:
    """Test ProductService CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_product_success(self, product_service, mock_session, sample_product_data):
        """Test successful product creation."""
        # Setup
        create_request = ProductCreateRequest(
            sku=sample_product_data["sku"],
            name=sample_product_data["name"],
            description=sample_product_data["description"],
            product_type=sample_product_data["product_type"],
            category=sample_product_data["category"],
            base_price=sample_product_data["base_price"],
            currency=sample_product_data["currency"],
            tax_class=sample_product_data["tax_class"],
            metadata=sample_product_data["metadata"],
        )

        # Mock the database product
        mock_db_product = MagicMock()
        for key, value in sample_product_data.items():
            setattr(mock_db_product, key, value)

        # Configure mock session
        mock_session.scalar.return_value = None  # No existing product
        mock_session.refresh = AsyncMock(side_effect=lambda x: None)

        # Execute
        with patch('dotmac.platform.billing.catalog.service.get_async_session', return_value=mock_session):
            with patch('uuid.uuid4', return_value='prod_123'):
                result = await product_service.create_product(create_request, "tenant_123")

        # Verify
        assert result.sku == sample_product_data["sku"]
        assert result.name == sample_product_data["name"]
        assert result.base_price == sample_product_data["base_price"]
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_product_duplicate_sku(self, product_service, mock_session):
        """Test product creation with duplicate SKU."""
        # Setup
        create_request = ProductCreateRequest(
            sku="EXISTING-SKU",
            name="Test Product",
            description="Test",
            product_type=ProductType.ONE_TIME,
            category="test",
            base_price=Decimal("50.00"),
            currency="USD",
        )

        # Mock existing product
        mock_session.scalar.return_value = MagicMock()  # Product exists

        # Execute and verify
        with patch('dotmac.platform.billing.catalog.service.get_async_session', return_value=mock_session):
            with pytest.raises(ValueError, match="already exists"):
                await product_service.create_product(create_request, "tenant_123")

    @pytest.mark.asyncio
    async def test_get_product_success(self, product_service, mock_session, sample_product_data):
        """Test successful product retrieval."""
        # Setup
        mock_product = MagicMock()
        for key, value in sample_product_data.items():
            setattr(mock_product, key, value)

        mock_session.scalar.return_value = mock_product

        # Execute
        with patch('dotmac.platform.billing.catalog.service.get_async_session', return_value=mock_session):
            result = await product_service.get_product("prod_123", "tenant_123")

        # Verify
        assert result.product_id == "prod_123"
        assert result.sku == sample_product_data["sku"]

    @pytest.mark.asyncio
    async def test_get_product_not_found(self, product_service, mock_session):
        """Test product retrieval when not found."""
        # Setup
        mock_session.scalar.return_value = None

        # Execute and verify
        with patch('dotmac.platform.billing.catalog.service.get_async_session', return_value=mock_session):
            with pytest.raises(ProductNotFoundError):
                await product_service.get_product("nonexistent", "tenant_123")

    @pytest.mark.asyncio
    async def test_update_product_success(self, product_service, mock_session, sample_product_data):
        """Test successful product update."""
        # Setup
        update_request = ProductUpdateRequest(
            name="Updated Product",
            description="Updated description",
            base_price=Decimal("149.99"),
            is_active=False,
        )

        mock_product = MagicMock()
        for key, value in sample_product_data.items():
            setattr(mock_product, key, value)

        mock_session.scalar.return_value = mock_product

        # Execute
        with patch('dotmac.platform.billing.catalog.service.get_async_session', return_value=mock_session):
            result = await product_service.update_product("prod_123", update_request, "tenant_123")

        # Verify
        assert mock_product.name == "Updated Product"
        assert mock_product.description == "Updated description"
        assert mock_product.base_price == Decimal("149.99")
        assert mock_product.is_active is False
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_product_success(self, product_service, mock_session, sample_product_data):
        """Test successful product deletion."""
        # Setup
        mock_product = MagicMock()
        for key, value in sample_product_data.items():
            setattr(mock_product, key, value)

        mock_session.scalar.return_value = mock_product

        # Execute
        with patch('dotmac.platform.billing.catalog.service.get_async_session', return_value=mock_session):
            await product_service.delete_product("prod_123", "tenant_123")

        # Verify
        mock_session.delete.assert_called_once_with(mock_product)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_products_with_filters(self, product_service, mock_session):
        """Test listing products with filters."""
        # Setup mock products
        mock_products = [
            MagicMock(
                product_id=f"prod_{i}",
                sku=f"SKU-{i:03d}",
                name=f"Product {i}",
                base_price=Decimal(str(50 + i * 10)),
                is_active=i % 2 == 0,
            )
            for i in range(5)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_products
        mock_session.execute.return_value = mock_result

        # Execute
        with patch('dotmac.platform.billing.catalog.service.get_async_session', return_value=mock_session):
            result = await product_service.list_products(
                tenant_id="tenant_123",
                category="software",
                is_active=True,
                min_price=Decimal("50"),
                max_price=Decimal("100"),
                skip=0,
                limit=10,
            )

        # Verify
        assert isinstance(result, list)
        assert len(result) == 5
        mock_session.execute.assert_called_once()


class TestProductCategories:
    """Test product category operations."""

    @pytest.mark.asyncio
    async def test_create_category_success(self, product_service, mock_session, sample_category_data):
        """Test successful category creation."""
        # Setup
        from dotmac.platform.billing.catalog.models import ProductCategoryCreateRequest

        create_request = ProductCategoryCreateRequest(
            name=sample_category_data["name"],
            description=sample_category_data["description"],
            parent_category_id=None,
            sort_order=1,
        )

        # Mock the response
        mock_session.scalar.return_value = None  # No existing category

        # Execute
        with patch('dotmac.platform.billing.catalog.service.get_async_session', return_value=mock_session):
            with patch('uuid.uuid4', return_value='cat_123'):
                result = await product_service.create_category(create_request, "tenant_123")

        # Verify
        assert result.name == sample_category_data["name"]
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_category_hierarchy(self, product_service, mock_session):
        """Test retrieving category hierarchy."""
        # Setup mock categories
        mock_categories = [
            MagicMock(
                category_id="cat_1",
                name="Root Category",
                parent_category_id=None,
                sort_order=1,
            ),
            MagicMock(
                category_id="cat_2",
                name="Child Category",
                parent_category_id="cat_1",
                sort_order=2,
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_categories
        mock_session.execute.return_value = mock_result

        # Execute
        with patch('dotmac.platform.billing.catalog.service.get_async_session', return_value=mock_session):
            result = await product_service.get_category_hierarchy("tenant_123")

        # Verify
        assert len(result) == 2
        assert result[0].category_id == "cat_1"
        assert result[1].parent_category_id == "cat_1"


class TestProductSearch:
    """Test product search functionality."""

    @pytest.mark.asyncio
    async def test_search_products_by_name(self, product_service, mock_session):
        """Test searching products by name."""
        # Setup
        mock_products = [
            MagicMock(
                product_id="prod_1",
                name="Premium Software Suite",
                description="Enterprise software",
            ),
            MagicMock(
                product_id="prod_2",
                name="Basic Software Package",
                description="Entry-level software",
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_products
        mock_session.execute.return_value = mock_result

        # Execute
        with patch('dotmac.platform.billing.catalog.service.get_async_session', return_value=mock_session):
            result = await product_service.search_products(
                tenant_id="tenant_123",
                search_query="software",
            )

        # Verify
        assert len(result.items) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_products_by_type(self, product_service, mock_session):
        """Test getting products by type."""
        # Setup
        subscription_products = [
            MagicMock(
                product_id=f"sub_{i}",
                product_type=ProductType.SUBSCRIPTION,
                name=f"Subscription {i}",
            )
            for i in range(3)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = subscription_products
        mock_session.execute.return_value = mock_result

        # Execute
        with patch('dotmac.platform.billing.catalog.service.get_async_session', return_value=mock_session):
            result = await product_service.get_products_by_type(
                tenant_id="tenant_123",
                product_type=ProductType.SUBSCRIPTION,
            )

        # Verify
        assert len(result) == 3
        assert all(p.product_type == ProductType.SUBSCRIPTION for p in result)


class TestProductValidation:
    """Test product validation logic."""

    @pytest.mark.asyncio
    async def test_validate_price_changes(self, product_service):
        """Test price change validation."""
        # Test valid price
        assert product_service._validate_price(Decimal("99.99")) is True
        assert product_service._validate_price(Decimal("0")) is True

        # Test invalid price
        assert product_service._validate_price(Decimal("-10")) is False
        assert product_service._validate_price(None) is False

    @pytest.mark.asyncio
    async def test_validate_sku_format(self, product_service):
        """Test SKU format validation."""
        # Valid SKUs
        valid_skus = ["SKU-001", "PROD-ABC-123", "ITEM_2024"]
        for sku in valid_skus:
            assert product_service._validate_sku(sku) is True

        # Invalid SKUs
        invalid_skus = ["", " ", "sku with spaces", None]
        for sku in invalid_skus:
            assert product_service._validate_sku(sku) is False

    @pytest.mark.asyncio
    async def test_validate_currency_code(self, product_service):
        """Test currency code validation."""
        # Valid currency codes
        valid_currencies = ["USD", "EUR", "GBP", "JPY"]
        for currency in valid_currencies:
            assert product_service._validate_currency(currency) is True

        # Invalid currency codes
        invalid_currencies = ["US", "DOLLAR", "123", "", None]
        for currency in invalid_currencies:
            assert product_service._validate_currency(currency) is False


class TestProductBulkOperations:
    """Test bulk product operations."""

    @pytest.mark.asyncio
    async def test_bulk_update_prices(self, product_service, mock_session):
        """Test bulk price update."""
        # Setup
        product_ids = ["prod_1", "prod_2", "prod_3"]
        price_increase = Decimal("10.00")

        mock_products = [
            MagicMock(
                product_id=pid,
                base_price=Decimal("50.00"),
            )
            for pid in product_ids
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_products
        mock_session.execute.return_value = mock_result

        # Execute
        with patch('dotmac.platform.billing.catalog.service.get_async_session', return_value=mock_session):
            await product_service.bulk_update_prices(
                product_ids=product_ids,
                price_adjustment=price_increase,
                tenant_id="tenant_123",
            )

        # Verify
        for product in mock_products:
            assert product.base_price == Decimal("60.00")
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_activate_products(self, product_service, mock_session):
        """Test bulk product activation."""
        # Setup
        product_ids = ["prod_1", "prod_2"]

        mock_products = [
            MagicMock(product_id=pid, is_active=False)
            for pid in product_ids
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_products
        mock_session.execute.return_value = mock_result

        # Execute
        with patch('dotmac.platform.billing.catalog.service.get_async_session', return_value=mock_session):
            await product_service.bulk_activate_products(
                product_ids=product_ids,
                tenant_id="tenant_123",
            )

        # Verify
        for product in mock_products:
            assert product.is_active is True
        mock_session.commit.assert_called_once()


class TestProductMetrics:
    """Test product metrics and analytics."""

    @pytest.mark.asyncio
    async def test_get_product_sales_metrics(self, product_service, mock_session):
        """Test getting product sales metrics."""
        # Setup
        mock_metrics = MagicMock(
            product_id="prod_123",
            total_sales=100,
            revenue=Decimal("9999.00"),
            avg_order_value=Decimal("99.99"),
        )

        mock_session.scalar.return_value = mock_metrics

        # Execute
        with patch('dotmac.platform.billing.catalog.service.get_async_session', return_value=mock_session):
            result = await product_service.get_product_metrics(
                product_id="prod_123",
                tenant_id="tenant_123",
            )

        # Verify
        assert result["total_sales"] == 100
        assert result["revenue"] == Decimal("9999.00")

    @pytest.mark.asyncio
    async def test_get_category_performance(self, product_service, mock_session):
        """Test getting category performance metrics."""
        # Setup
        mock_performance = [
            {"category": "software", "revenue": Decimal("50000")},
            {"category": "hardware", "revenue": Decimal("30000")},
        ]

        mock_result = MagicMock()
        mock_result.all.return_value = mock_performance
        mock_session.execute.return_value = mock_result

        # Execute
        with patch('dotmac.platform.billing.catalog.service.get_async_session', return_value=mock_session):
            result = await product_service.get_category_performance(
                tenant_id="tenant_123",
            )

        # Verify
        assert len(result) == 2
        assert result[0]["revenue"] == Decimal("50000")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])