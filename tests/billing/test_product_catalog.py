"""
Tests for product catalog functionality.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone

from dotmac.platform.billing.catalog.models import (
    Product,
    ProductCategory,
    ProductType,
    UsageType,
    TaxClass,
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductCategoryCreateRequest,
    ProductFilters,
)
from dotmac.platform.billing.catalog.service import ProductService
from dotmac.platform.billing.exceptions import (
    ProductError,
    ProductNotFoundError,
    CategoryNotFoundError,
)


class TestProductCatalogModels:
    """Test product catalog models and validation."""

    def test_product_creation_valid(self):
        """Test creating a valid product."""
        product = Product(
            product_id="prod_123",
            tenant_id="tenant_1",
            sku="TEST-001",
            name="Test Product",
            category="Software",
            product_type=ProductType.ONE_TIME,
            base_price=Decimal("19.99"),
            currency="USD",
        )

        assert product.product_id == "prod_123"
        assert product.sku == "TEST-001"
        assert product.name == "Test Product"
        assert product.product_type == ProductType.ONE_TIME
        assert product.base_price == Decimal("19.99")
        assert product.currency == "USD"
        assert product.is_active is True

    def test_product_sku_validation(self):
        """Test SKU validation and normalization."""
        request = ProductCreateRequest(
            sku="  test-001  ",  # With spaces
            name="Test Product",
            category="Software",
            product_type=ProductType.ONE_TIME,
            base_price=Decimal("19.99"),
        )

        assert request.sku == "TEST-001"  # Should be normalized

    def test_product_negative_price_validation(self):
        """Test that negative prices are rejected."""
        with pytest.raises(ValueError, match="Base price cannot be negative"):
            ProductCreateRequest(
                sku="TEST-001",
                name="Test Product",
                category="Software",
                product_type=ProductType.ONE_TIME,
                base_price=Decimal("-10.00"),
            )

    def test_product_usage_based_configuration(self):
        """Test usage-based product configuration."""
        product = Product(
            product_id="prod_usage",
            tenant_id="tenant_1",
            sku="API-CALLS",
            name="API Call Service",
            category="API",
            product_type=ProductType.USAGE_BASED,
            base_price=Decimal("0.01"),  # Per-call price
            usage_type=UsageType.API_CALLS,
            usage_unit_name="API Calls",
        )

        assert product.is_usage_based() is True
        assert product.requires_usage_tracking() is True
        assert product.usage_type == UsageType.API_CALLS
        assert product.usage_unit_name == "API Calls"

    def test_hybrid_product_configuration(self):
        """Test hybrid product (subscription + usage) configuration."""
        product = Product(
            product_id="prod_hybrid",
            tenant_id="tenant_1",
            sku="SAAS-PRO",
            name="SaaS Pro Plan",
            category="SaaS",
            product_type=ProductType.HYBRID,
            base_price=Decimal("99.00"),  # Monthly base fee
            usage_type=UsageType.API_CALLS,
            usage_unit_name="API Calls",
        )

        assert product.is_usage_based() is True
        assert product.requires_usage_tracking() is True
        assert product.product_type == ProductType.HYBRID

    def test_product_category_creation(self):
        """Test product category creation."""
        category = ProductCategory(
            category_id="cat_123",
            tenant_id="tenant_1",
            name="Software",
            description="Software products and licenses",
            default_tax_class=TaxClass.STANDARD,
            sort_order=10,
        )

        assert category.name == "Software"
        assert category.default_tax_class == TaxClass.STANDARD
        assert category.sort_order == 10

    def test_product_filters(self):
        """Test product filtering configuration."""
        filters = ProductFilters(
            category="Software",
            product_type=ProductType.SUBSCRIPTION,
            usage_type=UsageType.API_CALLS,
            is_active=True,
            search="API",
        )

        assert filters.category == "Software"
        assert filters.product_type == ProductType.SUBSCRIPTION
        assert filters.usage_type == UsageType.API_CALLS
        assert filters.is_active is True
        assert filters.search == "API"


class TestProductService:
    """Test product service operations."""

    @pytest.fixture
    async def service(self, db_manager):
        """Create product service instance."""
        return ProductService(db_manager)

    @pytest.fixture
    def sample_category_request(self):
        """Sample category creation request."""
        return ProductCategoryCreateRequest(
            name="Software",
            description="Software products and services",
            default_tax_class=TaxClass.STANDARD,
            sort_order=10,
        )

    @pytest.fixture
    def sample_product_request(self):
        """Sample product creation request."""
        return ProductCreateRequest(
            sku="TEST-PROD-001",
            name="Test Software License",
            description="Professional software license",
            category="Software",
            product_type=ProductType.ONE_TIME,
            base_price=Decimal("199.99"),
            currency="USD",
            tax_class=TaxClass.STANDARD,
        )

    async def test_create_category(self, service, sample_category_request):
        """Test creating a product category."""
        tenant_id = "test_tenant"

        category = await service.create_category(sample_category_request, tenant_id)

        assert category.tenant_id == tenant_id
        assert category.name == "Software"
        assert category.description == "Software products and services"
        assert category.default_tax_class == TaxClass.STANDARD
        assert category.sort_order == 10
        assert category.category_id.startswith("cat_")

    async def test_create_duplicate_category(self, service, sample_category_request):
        """Test that duplicate category names are rejected."""
        tenant_id = "test_tenant"

        # Create first category
        await service.create_category(sample_category_request, tenant_id)

        # Attempt to create duplicate
        with pytest.raises(ProductError, match="Category 'Software' already exists"):
            await service.create_category(sample_category_request, tenant_id)

    async def test_create_product(self, service, sample_product_request):
        """Test creating a product."""
        tenant_id = "test_tenant"

        product = await service.create_product(sample_product_request, tenant_id)

        assert product.tenant_id == tenant_id
        assert product.sku == "TEST-PROD-001"
        assert product.name == "Test Software License"
        assert product.category == "Software"
        assert product.product_type == ProductType.ONE_TIME
        assert product.base_price == Decimal("199.99")
        assert product.currency == "USD"
        assert product.is_active is True
        assert product.product_id.startswith("prod_")

    async def test_create_duplicate_sku(self, service, sample_product_request):
        """Test that duplicate SKUs are rejected within tenant."""
        tenant_id = "test_tenant"

        # Create first product
        await service.create_product(sample_product_request, tenant_id)

        # Attempt to create duplicate SKU
        with pytest.raises(ProductError, match="Product with SKU 'TEST-PROD-001' already exists"):
            await service.create_product(sample_product_request, tenant_id)

    async def test_create_usage_based_product(self, service):
        """Test creating a usage-based product."""
        tenant_id = "test_tenant"

        request = ProductCreateRequest(
            sku="API-CALLS-001",
            name="API Call Service",
            description="Pay-per-API-call service",
            category="API Services",
            product_type=ProductType.USAGE_BASED,
            base_price=Decimal("0.01"),  # $0.01 per call
            usage_type=UsageType.API_CALLS,
            usage_unit_name="API Calls",
        )

        product = await service.create_product(request, tenant_id)

        assert product.product_type == ProductType.USAGE_BASED
        assert product.usage_type == UsageType.API_CALLS
        assert product.usage_unit_name == "API Calls"
        assert product.is_usage_based() is True

    async def test_create_usage_product_missing_type(self, service):
        """Test that usage-based products require usage_type."""
        tenant_id = "test_tenant"

        request = ProductCreateRequest(
            sku="API-CALLS-002",
            name="API Call Service",
            category="API Services",
            product_type=ProductType.USAGE_BASED,
            base_price=Decimal("0.01"),
            # Missing usage_type
        )

        with pytest.raises(ProductError, match="Usage type is required"):
            await service.create_product(request, tenant_id)

    async def test_get_product(self, service, sample_product_request):
        """Test retrieving a product by ID."""
        tenant_id = "test_tenant"

        # Create product
        created = await service.create_product(sample_product_request, tenant_id)

        # Retrieve product
        retrieved = await service.get_product(created.product_id, tenant_id)

        assert retrieved.product_id == created.product_id
        assert retrieved.sku == created.sku
        assert retrieved.name == created.name

    async def test_get_nonexistent_product(self, service):
        """Test retrieving a non-existent product."""
        tenant_id = "test_tenant"

        with pytest.raises(ProductNotFoundError):
            await service.get_product("nonexistent_id", tenant_id)

    async def test_get_product_by_sku(self, service, sample_product_request):
        """Test retrieving a product by SKU."""
        tenant_id = "test_tenant"

        # Create product
        created = await service.create_product(sample_product_request, tenant_id)

        # Retrieve by SKU
        retrieved = await service.get_product_by_sku("TEST-PROD-001", tenant_id)

        assert retrieved is not None
        assert retrieved.product_id == created.product_id
        assert retrieved.sku == "TEST-PROD-001"

    async def test_get_product_by_sku_not_found(self, service):
        """Test retrieving a non-existent SKU."""
        tenant_id = "test_tenant"

        retrieved = await service.get_product_by_sku("NONEXISTENT-SKU", tenant_id)
        assert retrieved is None

    async def test_list_products(self, service):
        """Test listing products with basic filtering."""
        tenant_id = "test_tenant"

        # Create test products
        requests = [
            ProductCreateRequest(
                sku="PROD-001",
                name="Product One",
                category="Software",
                product_type=ProductType.ONE_TIME,
                base_price=Decimal("99.99"),
            ),
            ProductCreateRequest(
                sku="PROD-002",
                name="Product Two",
                category="Hardware",
                product_type=ProductType.SUBSCRIPTION,
                base_price=Decimal("29.99"),
            ),
        ]

        for request in requests:
            await service.create_product(request, tenant_id)

        # List all products
        all_products = await service.list_products(tenant_id)
        assert len(all_products) == 2

        # Filter by category
        software_products = await service.list_products(
            tenant_id,
            filters=ProductFilters(category="Software")
        )
        assert len(software_products) == 1
        assert software_products[0].category == "Software"

        # Filter by product type
        subscription_products = await service.list_products(
            tenant_id,
            filters=ProductFilters(product_type=ProductType.SUBSCRIPTION)
        )
        assert len(subscription_products) == 1
        assert subscription_products[0].product_type == ProductType.SUBSCRIPTION

    async def test_list_products_with_search(self, service):
        """Test product search functionality."""
        tenant_id = "test_tenant"

        # Create products with different names
        requests = [
            ProductCreateRequest(
                sku="API-001",
                name="API Gateway Service",
                description="Advanced API management",
                category="API",
                product_type=ProductType.SUBSCRIPTION,
                base_price=Decimal("49.99"),
            ),
            ProductCreateRequest(
                sku="WEB-001",
                name="Web Hosting",
                description="Basic web hosting service",
                category="Hosting",
                product_type=ProductType.SUBSCRIPTION,
                base_price=Decimal("19.99"),
            ),
        ]

        for request in requests:
            await service.create_product(request, tenant_id)

        # Search by name
        api_products = await service.list_products(
            tenant_id,
            filters=ProductFilters(search="API")
        )
        assert len(api_products) == 1
        assert "API" in api_products[0].name

        # Search by description
        hosting_products = await service.list_products(
            tenant_id,
            filters=ProductFilters(search="hosting")
        )
        assert len(hosting_products) == 1
        assert "hosting" in hosting_products[0].description.lower()

    async def test_update_product(self, service, sample_product_request):
        """Test updating a product."""
        tenant_id = "test_tenant"

        # Create product
        product = await service.create_product(sample_product_request, tenant_id)

        # Update product
        updates = ProductUpdateRequest(
            name="Updated Product Name",
            base_price=Decimal("299.99"),
            description="Updated description",
        )

        updated = await service.update_product(product.product_id, updates, tenant_id)

        assert updated.name == "Updated Product Name"
        assert updated.base_price == Decimal("299.99")
        assert updated.description == "Updated description"
        # SKU should remain unchanged
        assert updated.sku == product.sku

    async def test_update_price(self, service, sample_product_request):
        """Test updating product price specifically."""
        tenant_id = "test_tenant"

        # Create product
        product = await service.create_product(sample_product_request, tenant_id)
        original_price = product.base_price

        # Update price
        new_price = Decimal("349.99")
        updated = await service.update_price(product.product_id, new_price, tenant_id)

        assert updated.base_price == new_price
        assert updated.base_price != original_price

    async def test_deactivate_product(self, service, sample_product_request):
        """Test deactivating a product (soft delete)."""
        tenant_id = "test_tenant"

        # Create product
        product = await service.create_product(sample_product_request, tenant_id)
        assert product.is_active is True

        # Deactivate product
        deactivated = await service.deactivate_product(product.product_id, tenant_id)
        assert deactivated.is_active is False

    async def test_get_usage_products(self, service):
        """Test retrieving products configured for usage-based billing."""
        tenant_id = "test_tenant"

        # Create mixed product types
        requests = [
            ProductCreateRequest(
                sku="ONE-TIME-001",
                name="One-time Product",
                category="Software",
                product_type=ProductType.ONE_TIME,
                base_price=Decimal("99.99"),
            ),
            ProductCreateRequest(
                sku="USAGE-001",
                name="Usage-based Product",
                category="API",
                product_type=ProductType.USAGE_BASED,
                base_price=Decimal("0.01"),
                usage_type=UsageType.API_CALLS,
            ),
            ProductCreateRequest(
                sku="HYBRID-001",
                name="Hybrid Product",
                category="SaaS",
                product_type=ProductType.HYBRID,
                base_price=Decimal("49.99"),
                usage_type=UsageType.STORAGE_GB,
            ),
        ]

        for request in requests:
            await service.create_product(request, tenant_id)

        # Get usage-based products
        usage_products = await service.get_usage_products(tenant_id)

        assert len(usage_products) == 2  # usage_based + hybrid
        product_types = [p.product_type for p in usage_products]
        assert ProductType.USAGE_BASED in product_types
        assert ProductType.HYBRID in product_types
        assert ProductType.ONE_TIME not in product_types

    async def test_get_products_by_category(self, service):
        """Test retrieving products by category."""
        tenant_id = "test_tenant"

        # Create products in different categories
        requests = [
            ProductCreateRequest(
                sku="SOFT-001",
                name="Software Product",
                category="Software",
                product_type=ProductType.ONE_TIME,
                base_price=Decimal("99.99"),
            ),
            ProductCreateRequest(
                sku="HARD-001",
                name="Hardware Product",
                category="Hardware",
                product_type=ProductType.ONE_TIME,
                base_price=Decimal("199.99"),
            ),
            ProductCreateRequest(
                sku="SOFT-002",
                name="Another Software Product",
                category="Software",
                product_type=ProductType.SUBSCRIPTION,
                base_price=Decimal("29.99"),
            ),
        ]

        for request in requests:
            await service.create_product(request, tenant_id)

        # Get products by category
        software_products = await service.get_products_by_category("Software", tenant_id)
        hardware_products = await service.get_products_by_category("Hardware", tenant_id)

        assert len(software_products) == 2
        assert len(hardware_products) == 1

        # All software products should have 'Software' category
        assert all(p.category == "Software" for p in software_products)
        assert all(p.category == "Hardware" for p in hardware_products)

    async def test_tenant_isolation(self, service, sample_product_request):
        """Test that products are properly isolated by tenant."""
        tenant_1 = "tenant_1"
        tenant_2 = "tenant_2"

        # Create product in tenant 1
        product_1 = await service.create_product(sample_product_request, tenant_1)

        # Should be able to retrieve from tenant 1
        retrieved_1 = await service.get_product(product_1.product_id, tenant_1)
        assert retrieved_1.product_id == product_1.product_id

        # Should NOT be able to retrieve from tenant 2
        with pytest.raises(ProductNotFoundError):
            await service.get_product(product_1.product_id, tenant_2)

        # Lists should be isolated
        tenant_1_products = await service.list_products(tenant_1)
        tenant_2_products = await service.list_products(tenant_2)

        assert len(tenant_1_products) == 1
        assert len(tenant_2_products) == 0