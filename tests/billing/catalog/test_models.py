"""
Tests for billing catalog models.

Covers Pydantic model validation, field constraints, and business logic.
"""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from pydantic import ValidationError

from dotmac.platform.billing.catalog.models import (
    Product,
    ProductCategory,
    ProductType,
    UsageType,
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductCategoryCreateRequest,
    ProductCategoryUpdateRequest,
    ProductResponse,
    ProductCategoryResponse,
)


class TestProductType:
    """Test ProductType enum."""

    def test_product_type_values(self):
        """Test ProductType enum values."""
        assert ProductType.ONE_TIME == "one_time"
        assert ProductType.SUBSCRIPTION == "subscription"
        assert ProductType.USAGE_BASED == "usage_based"
        assert ProductType.HYBRID == "hybrid"

    def test_product_type_enum_members(self):
        """Test ProductType enum has all expected members."""
        expected_types = {"ONE_TIME", "SUBSCRIPTION", "USAGE_BASED", "HYBRID"}
        actual_types = set(ProductType.__members__.keys())
        assert actual_types == expected_types


class TestUsageType:
    """Test UsageType enum."""

    def test_usage_type_values(self):
        """Test UsageType enum values."""
        assert UsageType.API_CALLS == "api_calls"
        assert UsageType.STORAGE_GB == "storage_gb"
        assert UsageType.BANDWIDTH_GB == "bandwidth_gb"
        assert UsageType.USERS == "users"
        assert UsageType.TRANSACTIONS == "transactions"

    def test_usage_type_enum_members(self):
        """Test UsageType enum has all expected members."""
        expected_types = {
            "API_CALLS", "STORAGE_GB", "BANDWIDTH_GB",
            "USERS", "TRANSACTIONS", "COMPUTE_HOURS"
        }
        actual_types = set(UsageType.__members__.keys())
        assert actual_types == expected_types


class TestProductCategory:
    """Test ProductCategory model."""

    def test_valid_category_creation(self, sample_product_category):
        """Test creating a valid product category."""
        category = sample_product_category
        assert category.category_id == "cat_123"
        assert category.tenant_id == "test-tenant-123"
        assert category.name == "Software Tools"
        assert category.is_active is True
        assert category.metadata == {"department": "engineering"}

    def test_category_validation_empty_name(self):
        """Test category validation fails with empty name."""
        with pytest.raises(ValidationError) as exc_info:
            ProductCategory(
                category_id="cat_123",
                tenant_id="test-tenant",
                name="",  # Empty name should fail
                description="Test",
                is_active=True,
                metadata={},
                created_at=datetime.now(timezone.utc),
            )

        errors = exc_info.value.errors()
        assert any("name" in str(error) for error in errors)

    def test_category_validation_long_name(self):
        """Test category validation fails with overly long name."""
        long_name = "x" * 256  # Exceeds max length

        with pytest.raises(ValidationError) as exc_info:
            ProductCategory(
                category_id="cat_123",
                tenant_id="test-tenant",
                name=long_name,
                description="Test",
                is_active=True,
                metadata={},
                created_at=datetime.now(timezone.utc),
            )

        errors = exc_info.value.errors()
        assert any("name" in str(error) for error in errors)

    def test_category_defaults(self):
        """Test category model defaults."""
        category = ProductCategory(
            category_id="cat_123",
            tenant_id="test-tenant",
            name="Test Category",
            created_at=datetime.now(timezone.utc),
        )

        assert category.description is None
        assert category.is_active is True
        assert category.metadata == {}
        assert category.updated_at is None


class TestProduct:
    """Test Product model."""

    def test_valid_product_creation(self, sample_product):
        """Test creating a valid product."""
        product = sample_product
        assert product.product_id == "prod_123"
        assert product.sku == "SKU-TOOL-001"
        assert product.product_type == ProductType.SUBSCRIPTION
        assert product.base_price == Decimal("99.99")
        assert product.currency == "USD"
        assert product.is_active is True

    def test_product_validation_negative_price(self):
        """Test product validation fails with negative price."""
        with pytest.raises(ValidationError) as exc_info:
            Product(
                product_id="prod_123",
                tenant_id="test-tenant",
                sku="SKU-TEST",
                name="Test Product",
                product_type=ProductType.ONE_TIME,
                base_price=Decimal("-10.00"),  # Negative price should fail
                currency="USD",
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )

        errors = exc_info.value.errors()
        assert any("base_price" in str(error) for error in errors)

    def test_product_validation_invalid_currency(self):
        """Test product validation fails with invalid currency."""
        with pytest.raises(ValidationError) as exc_info:
            Product(
                product_id="prod_123",
                tenant_id="test-tenant",
                sku="SKU-TEST",
                name="Test Product",
                product_type=ProductType.ONE_TIME,
                base_price=Decimal("10.00"),
                currency="INVALID",  # Invalid currency code
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )

        errors = exc_info.value.errors()
        assert any("currency" in str(error) for error in errors)

    def test_product_validation_empty_sku(self):
        """Test product validation fails with empty SKU."""
        with pytest.raises(ValidationError) as exc_info:
            Product(
                product_id="prod_123",
                tenant_id="test-tenant",
                sku="",  # Empty SKU should fail
                name="Test Product",
                product_type=ProductType.ONE_TIME,
                base_price=Decimal("10.00"),
                currency="USD",
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )

        errors = exc_info.value.errors()
        assert any("sku" in str(error) for error in errors)

    def test_product_defaults(self):
        """Test product model defaults."""
        product = Product(
            product_id="prod_123",
            tenant_id="test-tenant",
            sku="SKU-TEST",
            name="Test Product",
            product_type=ProductType.ONE_TIME,
            base_price=Decimal("10.00"),
            created_at=datetime.now(timezone.utc),
        )

        assert product.description is None
        assert product.category is None
        assert product.currency == "USD"
        assert product.is_active is True
        assert product.usage_rates == {}
        assert product.metadata == {}
        assert product.updated_at is None

    def test_product_business_methods(self, sample_product, usage_based_product):
        """Test product business logic methods."""
        # Test subscription product
        assert not sample_product.is_one_time()
        assert sample_product.is_subscription()
        assert not sample_product.is_usage_based()
        assert sample_product.supports_usage_billing()  # Has usage rates

        # Test usage-based product
        assert not usage_based_product.is_one_time()
        assert not usage_based_product.is_subscription()
        assert usage_based_product.is_usage_based()
        assert usage_based_product.supports_usage_billing()

    def test_product_usage_rate_validation(self):
        """Test usage rates are properly validated."""
        # Valid usage rates
        product = Product(
            product_id="prod_123",
            tenant_id="test-tenant",
            sku="SKU-TEST",
            name="Test Product",
            product_type=ProductType.USAGE_BASED,
            base_price=Decimal("0"),
            usage_rates={"api_calls": Decimal("0.01")},
            created_at=datetime.now(timezone.utc),
        )
        assert product.usage_rates["api_calls"] == Decimal("0.01")

    def test_product_json_encoders(self, sample_product):
        """Test product JSON serialization."""
        product_dict = sample_product.model_dump()

        # Decimal should be converted to string
        assert isinstance(product_dict["base_price"], str)

        # DateTime should be converted to ISO format
        assert isinstance(product_dict["created_at"], str)


class TestProductCreateRequest:
    """Test ProductCreateRequest model."""

    def test_valid_create_request(self, product_create_request):
        """Test valid product creation request."""
        request = product_create_request
        assert request.sku == "SKU-TEST-001"
        assert request.name == "Test Product"
        assert request.product_type == ProductType.ONE_TIME
        assert request.base_price == Decimal("49.99")

    def test_create_request_validation(self):
        """Test product creation request validation."""
        # Test invalid price
        with pytest.raises(ValidationError):
            ProductCreateRequest(
                sku="SKU-TEST",
                name="Test",
                product_type=ProductType.ONE_TIME,
                base_price=Decimal("-1"),  # Invalid negative price
            )

        # Test invalid currency
        with pytest.raises(ValidationError):
            ProductCreateRequest(
                sku="SKU-TEST",
                name="Test",
                product_type=ProductType.ONE_TIME,
                base_price=Decimal("10"),
                currency="INVALID",
            )

    def test_create_request_defaults(self):
        """Test product creation request defaults."""
        request = ProductCreateRequest(
            sku="SKU-TEST",
            name="Test Product",
            product_type=ProductType.ONE_TIME,
            base_price=Decimal("10.00"),
        )

        assert request.description is None
        assert request.category is None
        assert request.currency == "USD"
        assert request.usage_rates == {}
        assert request.metadata == {}

    def test_create_request_usage_rates_validation(self):
        """Test usage rates validation in create request."""
        # Valid usage rates
        request = ProductCreateRequest(
            sku="SKU-TEST",
            name="Test Product",
            product_type=ProductType.USAGE_BASED,
            base_price=Decimal("0"),
            usage_rates={"api_calls": Decimal("0.01")},
        )
        assert request.usage_rates["api_calls"] == Decimal("0.01")


class TestProductUpdateRequest:
    """Test ProductUpdateRequest model."""

    def test_valid_update_request(self):
        """Test valid product update request."""
        request = ProductUpdateRequest(
            name="Updated Product",
            description="Updated description",
            base_price=Decimal("59.99"),
        )

        assert request.name == "Updated Product"
        assert request.description == "Updated description"
        assert request.base_price == Decimal("59.99")

    def test_update_request_partial_updates(self):
        """Test partial updates in update request."""
        # Only update name
        request = ProductUpdateRequest(name="New Name")
        assert request.name == "New Name"
        assert request.description is None
        assert request.base_price is None

        # Only update price
        request = ProductUpdateRequest(base_price=Decimal("19.99"))
        assert request.name is None
        assert request.base_price == Decimal("19.99")

    def test_update_request_validation(self):
        """Test product update request validation."""
        # Test invalid price
        with pytest.raises(ValidationError):
            ProductUpdateRequest(base_price=Decimal("-1"))

        # Test invalid currency
        with pytest.raises(ValidationError):
            ProductUpdateRequest(currency="TOOLONG")


class TestProductCategoryCreateRequest:
    """Test ProductCategoryCreateRequest model."""

    def test_valid_category_create_request(self, category_create_request):
        """Test valid category creation request."""
        request = category_create_request
        assert request.name == "Test Category"
        assert request.description == "A test category"
        assert request.metadata == {"test": True}

    def test_category_create_request_validation(self):
        """Test category creation request validation."""
        # Test empty name
        with pytest.raises(ValidationError):
            ProductCategoryCreateRequest(name="")

        # Test long name
        with pytest.raises(ValidationError):
            ProductCategoryCreateRequest(name="x" * 256)

    def test_category_create_request_defaults(self):
        """Test category creation request defaults."""
        request = ProductCategoryCreateRequest(name="Test Category")

        assert request.description is None
        assert request.metadata == {}


class TestProductCategoryUpdateRequest:
    """Test ProductCategoryUpdateRequest model."""

    def test_valid_category_update_request(self):
        """Test valid category update request."""
        request = ProductCategoryUpdateRequest(
            name="Updated Category",
            description="Updated description",
        )

        assert request.name == "Updated Category"
        assert request.description == "Updated description"

    def test_category_update_request_partial(self):
        """Test partial category updates."""
        request = ProductCategoryUpdateRequest(name="New Name")
        assert request.name == "New Name"
        assert request.description is None

    def test_category_update_request_validation(self):
        """Test category update request validation."""
        with pytest.raises(ValidationError):
            ProductCategoryUpdateRequest(name="x" * 256)


class TestProductResponse:
    """Test ProductResponse model."""

    def test_product_response_creation(self):
        """Test product response model creation."""
        now = datetime.now(timezone.utc)
        response = ProductResponse(
            product_id="prod_123",
            tenant_id="test-tenant",
            sku="SKU-TEST",
            name="Test Product",
            product_type=ProductType.ONE_TIME,
            base_price=Decimal("10.00"),
            currency="USD",
            is_active=True,
            usage_rates={},
            metadata={},
            created_at=now,
            updated_at=None,
        )

        assert response.product_id == "prod_123"
        assert response.sku == "SKU-TEST"
        assert response.product_type == ProductType.ONE_TIME

    def test_product_response_json_encoders(self):
        """Test product response JSON serialization."""
        now = datetime.now(timezone.utc)
        response = ProductResponse(
            product_id="prod_123",
            tenant_id="test-tenant",
            sku="SKU-TEST",
            name="Test Product",
            product_type=ProductType.ONE_TIME,
            base_price=Decimal("10.00"),
            currency="USD",
            is_active=True,
            usage_rates={"api_calls": Decimal("0.01")},
            metadata={},
            created_at=now,
            updated_at=None,
        )

        response_dict = response.model_dump()

        # Check JSON encoding
        assert isinstance(response_dict["base_price"], str)
        assert isinstance(response_dict["created_at"], str)
        assert isinstance(response_dict["usage_rates"]["api_calls"], str)


class TestProductCategoryResponse:
    """Test ProductCategoryResponse model."""

    def test_category_response_creation(self):
        """Test category response model creation."""
        now = datetime.now(timezone.utc)
        response = ProductCategoryResponse(
            category_id="cat_123",
            tenant_id="test-tenant",
            name="Test Category",
            description="Test description",
            is_active=True,
            metadata={},
            created_at=now,
            updated_at=None,
        )

        assert response.category_id == "cat_123"
        assert response.name == "Test Category"
        assert response.is_active is True

    def test_category_response_json_encoders(self):
        """Test category response JSON serialization."""
        now = datetime.now(timezone.utc)
        response = ProductCategoryResponse(
            category_id="cat_123",
            tenant_id="test-tenant",
            name="Test Category",
            description="Test description",
            is_active=True,
            metadata={},
            created_at=now,
            updated_at=None,
        )

        response_dict = response.model_dump()
        assert isinstance(response_dict["created_at"], str)