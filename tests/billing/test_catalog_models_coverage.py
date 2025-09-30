"""Tests for catalog models to reach 90%+ coverage - Phase 2."""

import pytest
from decimal import Decimal
from pydantic import ValidationError

from dotmac.platform.billing.catalog.models import (
    Product,
    ProductCategory,
    ProductCategoryCreateRequest,
    ProductCreateRequest,
    ProductType,
    ProductUpdateRequest,
    TaxClass,
    UsageType,
)


class TestProductValidations:
    """Test Product model validators to cover missing lines."""

    def test_validate_base_price_negative(self):
        """Test base_price validator rejects negative values."""
        with pytest.raises(ValidationError) as exc_info:
            Product(
                tenant_id="tenant_1",
                product_id="prod_1",
                sku="TEST-001",
                name="Test Product",
                category="Electronics",
                product_type=ProductType.ONE_TIME,
                base_price=Decimal("-10.00"),  # Negative price
                currency="USD",
            )

        assert "Base price cannot be negative" in str(exc_info.value)

    def test_validate_base_price_zero(self):
        """Test base_price validator allows zero."""
        product = Product(
            tenant_id="tenant_1",
            product_id="prod_1",
            sku="TEST-001",
            name="Test Product",
            category="Electronics",
            product_type=ProductType.ONE_TIME,
            base_price=Decimal("0.00"),
            currency="USD",
        )

        assert product.base_price == Decimal("0.00")

    def test_validate_sku_empty_string(self):
        """Test SKU validator rejects empty string."""
        with pytest.raises(ValidationError) as exc_info:
            Product(
                tenant_id="tenant_1",
                product_id="prod_1",
                sku="",  # Empty SKU
                name="Test Product",
                category="Electronics",
                product_type=ProductType.ONE_TIME,
                base_price=Decimal("10.00"),
                currency="USD",
            )

        assert "SKU cannot be empty" in str(exc_info.value)

    def test_validate_sku_whitespace_only(self):
        """Test SKU validator rejects whitespace-only string."""
        with pytest.raises(ValidationError) as exc_info:
            Product(
                tenant_id="tenant_1",
                product_id="prod_1",
                sku="   ",  # Whitespace only
                name="Test Product",
                category="Electronics",
                product_type=ProductType.ONE_TIME,
                base_price=Decimal("10.00"),
                currency="USD",
            )

        assert "SKU cannot be empty" in str(exc_info.value)

    def test_validate_sku_converts_to_uppercase(self):
        """Test SKU validator converts to uppercase."""
        product = Product(
            tenant_id="tenant_1",
            product_id="prod_1",
            sku="test-sku-001",
            name="Test Product",
            category="Electronics",
            product_type=ProductType.ONE_TIME,
            base_price=Decimal("10.00"),
            currency="USD",
        )

        assert product.sku == "TEST-SKU-001"

    def test_validate_sku_strips_whitespace(self):
        """Test SKU validator strips leading/trailing whitespace."""
        product = Product(
            tenant_id="tenant_1",
            product_id="prod_1",
            sku="  TEST-001  ",
            name="Test Product",
            category="Electronics",
            product_type=ProductType.ONE_TIME,
            base_price=Decimal("10.00"),
            currency="USD",
        )

        assert product.sku == "TEST-001"

    def test_validate_currency_invalid_length(self):
        """Test currency validator rejects non-3-letter codes."""
        with pytest.raises(ValidationError) as exc_info:
            Product(
                tenant_id="tenant_1",
                product_id="prod_1",
                sku="TEST-001",
                name="Test Product",
                category="Electronics",
                product_type=ProductType.ONE_TIME,
                base_price=Decimal("10.00"),
                currency="US",  # Only 2 letters
            )

        assert "Currency must be a 3-letter code" in str(exc_info.value)

    def test_validate_currency_too_long(self):
        """Test currency validator rejects codes longer than 3 letters."""
        with pytest.raises(ValidationError) as exc_info:
            Product(
                tenant_id="tenant_1",
                product_id="prod_1",
                sku="TEST-001",
                name="Test Product",
                category="Electronics",
                product_type=ProductType.ONE_TIME,
                base_price=Decimal("10.00"),
                currency="USDD",  # 4 letters
            )

        assert "String should have at most 3 characters" in str(exc_info.value)

    def test_validate_currency_converts_to_uppercase(self):
        """Test currency validator converts to uppercase."""
        product = Product(
            tenant_id="tenant_1",
            product_id="prod_1",
            sku="TEST-001",
            name="Test Product",
            category="Electronics",
            product_type=ProductType.ONE_TIME,
            base_price=Decimal("10.00"),
            currency="eur",
        )

        assert product.currency == "EUR"

    def test_is_usage_based_true_for_usage_based(self):
        """Test is_usage_based returns True for USAGE_BASED type."""
        product = Product(
            tenant_id="tenant_1",
            product_id="prod_1",
            sku="TEST-001",
            name="Test Product",
            category="API",
            product_type=ProductType.USAGE_BASED,
            base_price=Decimal("0.01"),
            currency="USD",
            usage_type=UsageType.API_CALLS,
        )

        assert product.is_usage_based() is True

    def test_is_usage_based_true_for_hybrid(self):
        """Test is_usage_based returns True for HYBRID type."""
        product = Product(
            tenant_id="tenant_1",
            product_id="prod_1",
            sku="TEST-001",
            name="Test Product",
            category="API",
            product_type=ProductType.HYBRID,
            base_price=Decimal("10.00"),
            currency="USD",
            usage_type=UsageType.API_CALLS,
        )

        assert product.is_usage_based() is True

    def test_is_usage_based_false_for_one_time(self):
        """Test is_usage_based returns False for ONE_TIME type."""
        product = Product(
            tenant_id="tenant_1",
            product_id="prod_1",
            sku="TEST-001",
            name="Test Product",
            category="Electronics",
            product_type=ProductType.ONE_TIME,
            base_price=Decimal("10.00"),
            currency="USD",
        )

        assert product.is_usage_based() is False

    def test_requires_usage_tracking_true(self):
        """Test requires_usage_tracking returns True when usage type is set."""
        product = Product(
            tenant_id="tenant_1",
            product_id="prod_1",
            sku="TEST-001",
            name="Test Product",
            category="API",
            product_type=ProductType.USAGE_BASED,
            base_price=Decimal("0.01"),
            currency="USD",
            usage_type=UsageType.API_CALLS,
        )

        assert product.requires_usage_tracking() is True

    def test_requires_usage_tracking_false_no_usage_type(self):
        """Test requires_usage_tracking returns False when no usage type."""
        product = Product(
            tenant_id="tenant_1",
            product_id="prod_1",
            sku="TEST-001",
            name="Test Product",
            category="Electronics",
            product_type=ProductType.USAGE_BASED,
            base_price=Decimal("0.01"),
            currency="USD",
            usage_type=None,
        )

        assert product.requires_usage_tracking() is False


class TestProductCategoryCreateRequestValidations:
    """Test ProductCategoryCreateRequest validators."""

    def test_validate_name_empty_string(self):
        """Test name validator rejects empty string."""
        with pytest.raises(ValidationError) as exc_info:
            ProductCategoryCreateRequest(name="")

        assert "Category name cannot be empty" in str(exc_info.value)

    def test_validate_name_whitespace_only(self):
        """Test name validator rejects whitespace-only string."""
        with pytest.raises(ValidationError) as exc_info:
            ProductCategoryCreateRequest(name="   ")

        assert "Category name cannot be empty" in str(exc_info.value)

    def test_validate_name_strips_whitespace(self):
        """Test name validator strips whitespace."""
        request = ProductCategoryCreateRequest(name="  Electronics  ")

        assert request.name == "Electronics"


class TestProductCreateRequestValidations:
    """Test ProductCreateRequest validators."""

    def test_validate_base_price_negative(self):
        """Test base_price validator rejects negative values."""
        with pytest.raises(ValidationError) as exc_info:
            ProductCreateRequest(
                sku="TEST-001",
                name="Test Product",
                category="Electronics",
                product_type=ProductType.ONE_TIME,
                base_price=Decimal("-10.00"),
                currency="USD",
            )

        assert "Base price cannot be negative" in str(exc_info.value)

    def test_validate_base_price_zero_allowed(self):
        """Test base_price validator allows zero."""
        request = ProductCreateRequest(
            sku="TEST-001",
            name="Test Product",
            category="Electronics",
            product_type=ProductType.ONE_TIME,
            base_price=Decimal("0.00"),
            currency="USD",
        )

        assert request.base_price == Decimal("0.00")


class TestProductUpdateRequestValidations:
    """Test ProductUpdateRequest validators."""

    def test_validate_base_price_negative(self):
        """Test base_price validator rejects negative values."""
        with pytest.raises(ValidationError) as exc_info:
            ProductUpdateRequest(base_price=Decimal("-10.00"))

        assert "Base price cannot be negative" in str(exc_info.value)

    def test_validate_base_price_none_allowed(self):
        """Test base_price validator allows None."""
        request = ProductUpdateRequest(base_price=None)

        assert request.base_price is None

    def test_validate_base_price_zero_allowed(self):
        """Test base_price validator allows zero."""
        request = ProductUpdateRequest(base_price=Decimal("0.00"))

        assert request.base_price == Decimal("0.00")


class TestTaxClassEnum:
    """Test TaxClass enum values."""

    def test_tax_class_values(self):
        """Test all TaxClass enum values are accessible."""
        assert TaxClass.STANDARD.value == "standard"
        assert TaxClass.REDUCED.value == "reduced"
        assert TaxClass.EXEMPT.value == "exempt"
        assert TaxClass.ZERO_RATED.value == "zero_rated"
        assert TaxClass.DIGITAL_SERVICES.value == "digital_services"


class TestUsageTypeEnum:
    """Test UsageType enum values."""

    def test_usage_type_values(self):
        """Test all UsageType enum values are accessible."""
        assert UsageType.API_CALLS.value == "api_calls"
        assert UsageType.STORAGE_GB.value == "storage_gb"
        assert UsageType.BANDWIDTH_GB.value == "bandwidth_gb"
        assert UsageType.USERS.value == "users"
        assert UsageType.TRANSACTIONS.value == "transactions"
        assert UsageType.COMPUTE_HOURS.value == "compute_hours"
        assert UsageType.CUSTOM.value == "custom"


class TestProductTypeEnum:
    """Test ProductType enum values."""

    def test_product_type_values(self):
        """Test all ProductType enum values are accessible."""
        assert ProductType.ONE_TIME.value == "one_time"
        assert ProductType.SUBSCRIPTION.value == "subscription"
        assert ProductType.USAGE_BASED.value == "usage_based"
        assert ProductType.HYBRID.value == "hybrid"


class TestProductCategory:
    """Test ProductCategory model."""

    def test_product_category_creation(self):
        """Test ProductCategory creation with all fields."""
        category = ProductCategory(
            tenant_id="tenant_1",
            category_id="cat_1",
            name="Electronics",
            description="Electronic products",
            default_tax_class=TaxClass.STANDARD,
            sort_order=10,
        )

        assert category.category_id == "cat_1"
        assert category.name == "Electronics"
        assert category.description == "Electronic products"
        assert category.default_tax_class == TaxClass.STANDARD
        assert category.sort_order == 10

    def test_product_category_defaults(self):
        """Test ProductCategory default values."""
        category = ProductCategory(
            tenant_id="tenant_1",
            category_id="cat_1",
            name="Electronics",
        )

        assert category.description is None
        assert category.default_tax_class == TaxClass.STANDARD
        assert category.sort_order == 0