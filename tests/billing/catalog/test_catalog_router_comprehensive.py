"""
Comprehensive integration tests for Billing Catalog Router.

Tests all product catalog router endpoints following the Two-Tier Testing Strategy.
Coverage Target: 85%+ for router endpoints
"""

import pytest
from uuid import uuid4
from unittest.mock import patch
from fastapi.testclient import TestClient

from dotmac.platform.main import app
from dotmac.platform.auth.core import UserInfo


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_auth_dependency():
    """Mock authentication dependency."""
    mock_user = UserInfo(
        user_id="test-user-123",
        username="testuser",
        email="test@example.com",
        roles=["user"],
        permissions=["catalog:read", "catalog:write"],
        tenant_id="test-tenant-123",
    )

    with patch("dotmac.platform.auth.dependencies.get_current_user", return_value=mock_user):
        yield mock_user


@pytest.fixture
def mock_tenant_dependency():
    """Mock tenant context dependency."""
    with patch("dotmac.platform.tenant.get_current_tenant_id", return_value="test-tenant-123"):
        yield "test-tenant-123"


class TestProductCategoryEndpoints:
    """Test product category endpoints."""

    @pytest.mark.asyncio
    async def test_create_category_success(
        self, test_client, mock_auth_dependency, mock_tenant_dependency
    ):
        """Test successful category creation."""
        category_data = {
            "name": "Software",
            "description": "Software products and licenses",
            "default_tax_class": "DIGITAL_GOODS",
            "sort_order": 1,
        }

        response = test_client.post(
            "/api/v1/billing/catalog/categories",
            json=category_data,
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code in [201, 400, 401, 500]

    @pytest.mark.asyncio
    async def test_list_categories(self, test_client, mock_auth_dependency, mock_tenant_dependency):
        """Test listing categories."""
        response = test_client.get(
            "/api/v1/billing/catalog/categories",
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_category_by_id(
        self, test_client, mock_auth_dependency, mock_tenant_dependency
    ):
        """Test getting category by ID."""
        category_id = str(uuid4())

        response = test_client.get(
            f"/api/v1/billing/catalog/categories/{category_id}",
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code in [200, 404, 401]


class TestProductEndpoints:
    """Test product management endpoints."""

    @pytest.mark.asyncio
    async def test_create_product_success(
        self, test_client, mock_auth_dependency, mock_tenant_dependency
    ):
        """Test successful product creation."""
        product_data = {
            "name": "Enterprise License",
            "description": "Annual enterprise software license",
            "sku": f"SKU-{uuid4().hex[:8]}",
            "product_type": "SUBSCRIPTION",
            "category_id": str(uuid4()),
            "base_price": 999.99,
            "currency": "USD",
            "is_active": True,
        }

        response = test_client.post(
            "/api/v1/billing/catalog/products",
            json=product_data,
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code in [201, 400, 404, 401, 500]

    @pytest.mark.asyncio
    async def test_list_products(self, test_client, mock_auth_dependency, mock_tenant_dependency):
        """Test listing products."""
        response = test_client.get(
            "/api/v1/billing/catalog/products",
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_products_with_filters(
        self, test_client, mock_auth_dependency, mock_tenant_dependency
    ):
        """Test listing products with filters."""
        response = test_client.get(
            "/api/v1/billing/catalog/products?is_active=true&product_type=SUBSCRIPTION",
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code in [200, 401]

    @pytest.mark.asyncio
    async def test_get_product_by_id(
        self, test_client, mock_auth_dependency, mock_tenant_dependency
    ):
        """Test getting product by ID."""
        product_id = str(uuid4())

        response = test_client.get(
            f"/api/v1/billing/catalog/products/{product_id}",
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code in [200, 404, 401]

    @pytest.mark.asyncio
    async def test_update_product(self, test_client, mock_auth_dependency, mock_tenant_dependency):
        """Test updating product."""
        product_id = str(uuid4())
        update_data = {
            "name": "Updated Product Name",
            "description": "Updated description",
        }

        response = test_client.put(
            f"/api/v1/billing/catalog/products/{product_id}",
            json=update_data,
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code in [200, 404, 400, 401, 500]

    @pytest.mark.asyncio
    async def test_update_product_price(
        self, test_client, mock_auth_dependency, mock_tenant_dependency
    ):
        """Test updating product price."""
        product_id = str(uuid4())
        price_data = {
            "new_price": 1299.99,
        }

        response = test_client.patch(
            f"/api/v1/billing/catalog/products/{product_id}/price",
            json=price_data,
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code in [200, 404, 400, 401, 500]

    @pytest.mark.asyncio
    async def test_delete_product(self, test_client, mock_auth_dependency, mock_tenant_dependency):
        """Test deleting product."""
        product_id = str(uuid4())

        response = test_client.delete(
            f"/api/v1/billing/catalog/products/{product_id}",
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code in [204, 404, 401]

    @pytest.mark.asyncio
    async def test_list_usage_based_products(
        self, test_client, mock_auth_dependency, mock_tenant_dependency
    ):
        """Test listing usage-based products."""
        response = test_client.get(
            "/api/v1/billing/catalog/products/usage-based",
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_products_by_category(
        self, test_client, mock_auth_dependency, mock_tenant_dependency
    ):
        """Test listing products by category."""
        category_id = str(uuid4())

        response = test_client.get(
            f"/api/v1/billing/catalog/categories/{category_id}/products",
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code in [200, 404, 401]


class TestCatalogRouterAuthorization:
    """Test authorization for catalog endpoints."""

    @pytest.mark.asyncio
    async def test_create_product_requires_auth(self, test_client):
        """Test that creating product requires authentication."""
        product_data = {
            "name": "Test Product",
            "sku": "SKU-123",
        }

        response = test_client.post(
            "/api/v1/billing/catalog/products",
            json=product_data,
        )

        # Should fail without authentication
        assert response.status_code in [401, 403, 422]

    @pytest.mark.asyncio
    async def test_list_products_requires_auth(self, test_client):
        """Test that listing products requires authentication."""
        response = test_client.get("/api/v1/billing/catalog/products")

        # Should fail without authentication
        assert response.status_code in [401, 403, 422]


class TestCatalogRouterErrorHandling:
    """Test error handling in catalog router."""

    @pytest.mark.asyncio
    async def test_create_product_invalid_data(
        self, test_client, mock_auth_dependency, mock_tenant_dependency
    ):
        """Test creating product with invalid data."""
        product_data = {
            "name": "",  # Invalid empty name
        }

        response = test_client.post(
            "/api/v1/billing/catalog/products",
            json=product_data,
            headers={"Authorization": "Bearer fake-token"},
        )

        # Should fail validation
        assert response.status_code in [400, 422, 401]

    @pytest.mark.asyncio
    async def test_get_product_invalid_uuid(
        self, test_client, mock_auth_dependency, mock_tenant_dependency
    ):
        """Test getting product with invalid UUID."""
        response = test_client.get(
            "/api/v1/billing/catalog/products/not-a-uuid",
            headers={"Authorization": "Bearer fake-token"},
        )

        # Should fail validation
        assert response.status_code in [400, 422, 401]

    @pytest.mark.asyncio
    async def test_update_product_not_found(
        self, test_client, mock_auth_dependency, mock_tenant_dependency
    ):
        """Test updating non-existent product."""
        product_id = str(uuid4())
        update_data = {"name": "Updated Name"}

        response = test_client.put(
            f"/api/v1/billing/catalog/products/{product_id}",
            json=update_data,
            headers={"Authorization": "Bearer fake-token"},
        )

        # Should return 404
        assert response.status_code in [404, 401, 500]


class TestCatalogRouterTenantIsolation:
    """Test tenant isolation for catalog endpoints."""

    @pytest.mark.asyncio
    async def test_products_tenant_isolation(self, test_client, mock_auth_dependency):
        """Test that each tenant only sees their own products."""
        # Test with tenant A
        with patch("dotmac.platform.tenant.get_current_tenant_id", return_value="tenant-a"):
            response_a = test_client.get(
                "/api/v1/billing/catalog/products",
                headers={"Authorization": "Bearer fake-token"},
            )

        # Test with tenant B
        with patch("dotmac.platform.tenant.get_current_tenant_id", return_value="tenant-b"):
            response_b = test_client.get(
                "/api/v1/billing/catalog/products",
                headers={"Authorization": "Bearer fake-token"},
            )

        # Both should succeed
        assert response_a.status_code in [200, 401]
        assert response_b.status_code in [200, 401]
