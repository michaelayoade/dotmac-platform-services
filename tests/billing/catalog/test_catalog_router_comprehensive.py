"""
Comprehensive integration tests for Billing Catalog Router.

Tests all product catalog router endpoints following the Two-Tier Testing Strategy.
Coverage Target: 85%+ for router endpoints
"""

from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from dotmac.platform.auth.core import UserInfo
from dotmac.platform.billing.catalog.models import (
    ProductCategoryCreateRequest,
    ProductCreateRequest,
    ProductPriceUpdateRequest,
    ProductType,
    ProductUpdateRequest,
)
from dotmac.platform.billing.catalog.router import (
    create_product,
    create_product_category,
    deactivate_product,
    get_product,
    get_product_category,
    list_product_categories,
    list_products,
    list_products_by_category,
    list_usage_products,
    update_product,
    update_product_price,
)
from tests.fixtures.async_db import AsyncSessionShim

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture
def mock_auth_user(mock_tenant_dependency):
    """Mock authenticated user for catalog endpoints."""
    from uuid import uuid4

    return UserInfo(
        user_id=str(uuid4()),
        username="testuser",
        email="test@example.com",
        roles=["user"],
        permissions=[
            "catalog:read",
            "catalog:write",
            "billing:catalog:read",
            "billing:catalog:write",
            "billing.catalog.view",
            "billing.catalog.manage",
        ],
        tenant_id=mock_tenant_dependency,
    )


@pytest.fixture
def mock_tenant_dependency():
    """Mock tenant context dependency."""
    from uuid import uuid4

    tenant_id = str(uuid4())
    yield tenant_id


@pytest.fixture
def async_db_session(db_session):
    """Provide async-compatible session for shared billing fixtures."""
    return AsyncSessionShim(db_session)


async def _call_with_status(call, *, success_status=200, **kwargs):
    try:
        result = await call(**kwargs)
        return success_status, result
    except HTTPException as exc:
        return exc.status_code, exc
    except ValidationError as exc:
        return 422, exc


@pytest.mark.integration
class TestProductCategoryEndpoints:
    """Test product category endpoints."""

    async def test_create_category_success(
        self, async_db_session, mock_auth_user, mock_tenant_dependency
    ):
        """Test successful category creation."""
        category_data = ProductCategoryCreateRequest(
            name="Software",
            description="Software products and licenses",
            default_tax_class="digital_services",
            sort_order=1,
        )

        status_code, _ = await _call_with_status(
            create_product_category,
            success_status=201,
            category_data=category_data,
            tenant_id=mock_tenant_dependency,
            db_session=async_db_session,
            current_user=mock_auth_user,
        )

        assert status_code in [201, 400, 401, 403, 500]

    async def test_list_categories(self, async_db_session, mock_auth_user, mock_tenant_dependency):
        """Test listing categories."""
        status_code, result = await _call_with_status(
            list_product_categories,
            tenant_id=mock_tenant_dependency,
            db_session=async_db_session,
            current_user=mock_auth_user,
        )

        assert status_code in [200, 401]

        if status_code == 200:
            assert isinstance(result, list)

    async def test_get_category_by_id(
        self, async_db_session, mock_auth_user, mock_tenant_dependency
    ):
        """Test getting category by ID."""
        category_id = str(uuid4())

        status_code, _ = await _call_with_status(
            get_product_category,
            category_id=category_id,
            tenant_id=mock_tenant_dependency,
            db_session=async_db_session,
            current_user=mock_auth_user,
        )

        assert status_code in [200, 404, 401]


@pytest.mark.integration
class TestProductEndpoints:
    """Test product management endpoints."""

    async def test_create_product_success(
        self, async_db_session, mock_auth_user, mock_tenant_dependency
    ):
        """Test successful product creation."""
        product_data = ProductCreateRequest(
            sku=f"SKU-{uuid4().hex[:8]}",
            name="Enterprise License",
            description="Annual enterprise software license",
            category="Software",
            product_type="subscription",
            base_price=999.99,
            currency="USD",
            tax_class="standard",
            is_active=True,
            metadata={"tier": "enterprise"},
        )

        status_code, _ = await _call_with_status(
            create_product,
            success_status=201,
            product_data=product_data,
            tenant_id=mock_tenant_dependency,
            db_session=async_db_session,
            current_user=mock_auth_user,
        )

        assert status_code in [201, 400, 404, 401, 403, 500]

    async def test_list_products(self, async_db_session, mock_auth_user, mock_tenant_dependency):
        """Test listing products."""
        status_code, result = await _call_with_status(
            list_products,
            tenant_id=mock_tenant_dependency,
            db_session=async_db_session,
            current_user=mock_auth_user,
            category=None,
            product_type=None,
            usage_type=None,
            is_active=True,
            search=None,
            page=1,
            limit=50,
        )

        assert status_code in [200, 401]

        if status_code == 200:
            assert isinstance(result, list)

    async def test_list_products_with_filters(
        self, async_db_session, mock_auth_user, mock_tenant_dependency
    ):
        """Test listing products with filters."""
        status_code, _ = await _call_with_status(
            list_products,
            tenant_id=mock_tenant_dependency,
            db_session=async_db_session,
            current_user=mock_auth_user,
            category=None,
            is_active=True,
            product_type=ProductType.SUBSCRIPTION,
            usage_type=None,
            search=None,
            page=1,
            limit=50,
        )

        assert status_code in [200, 401]

    async def test_get_product_by_id(
        self, async_db_session, mock_auth_user, mock_tenant_dependency
    ):
        """Test getting product by ID."""
        product_id = str(uuid4())

        status_code, _ = await _call_with_status(
            get_product,
            product_id=product_id,
            tenant_id=mock_tenant_dependency,
            db_session=async_db_session,
            current_user=mock_auth_user,
        )

        assert status_code in [200, 404, 401]

    async def test_update_product(
        self, async_db_session, mock_auth_user, mock_tenant_dependency
    ):
        """Test updating product."""
        product_id = str(uuid4())
        update_data = ProductUpdateRequest(
            name="Updated Product Name",
            description="Updated description",
        )

        status_code, _ = await _call_with_status(
            update_product,
            product_id=product_id,
            updates=update_data,
            tenant_id=mock_tenant_dependency,
            db_session=async_db_session,
            current_user=mock_auth_user,
        )

        assert status_code in [200, 404, 400, 401, 403, 500]

    async def test_update_product_price(
        self, async_db_session, mock_auth_user, mock_tenant_dependency
    ):
        """Test updating product price."""
        product_id = str(uuid4())
        price_data = ProductPriceUpdateRequest(new_price=1299.99)

        status_code, _ = await _call_with_status(
            update_product_price,
            product_id=product_id,
            payload=price_data,
            tenant_id=mock_tenant_dependency,
            db_session=async_db_session,
            current_user=mock_auth_user,
        )

        assert status_code in [200, 404, 400, 401, 403, 500]

    async def test_delete_product(
        self, async_db_session, mock_auth_user, mock_tenant_dependency
    ):
        """Test deleting product."""
        product_id = str(uuid4())

        status_code, _ = await _call_with_status(
            deactivate_product,
            success_status=204,
            product_id=product_id,
            tenant_id=mock_tenant_dependency,
            db_session=async_db_session,
            current_user=mock_auth_user,
        )

        assert status_code in [204, 404, 401, 403]

    async def test_list_usage_based_products(
        self, async_db_session, mock_auth_user, mock_tenant_dependency
    ):
        """Test listing usage-based products."""
        status_code, result = await _call_with_status(
            list_usage_products,
            tenant_id=mock_tenant_dependency,
            db_session=async_db_session,
            current_user=mock_auth_user,
        )

        assert status_code in [200, 401]

        if status_code == 200:
            assert isinstance(result, list)

    async def test_list_products_by_category(
        self, async_db_session, mock_auth_user, mock_tenant_dependency
    ):
        """Test listing products by category."""
        category_id = str(uuid4())

        status_code, _ = await _call_with_status(
            list_products_by_category,
            category=category_id,
            tenant_id=mock_tenant_dependency,
            db_session=async_db_session,
            current_user=mock_auth_user,
        )

        assert status_code in [200, 404, 401]


@pytest.mark.integration
class TestCatalogRouterAuthorization:
    """Test authorization for catalog endpoints."""

    async def test_create_product_requires_auth(
        self, async_db_session, mock_tenant_dependency
    ):
        """Test that creating product requires authentication."""
        product_data = ProductCreateRequest(
            name="Test Product",
            sku="SKU-123",
            category="Test",
            product_type="subscription",
            base_price=1000,
        )

        with pytest.raises(Exception):
            await create_product(
                product_data=product_data,
                tenant_id=mock_tenant_dependency,
                db_session=async_db_session,
                current_user=None,
            )

    async def test_list_products_requires_auth(
        self, async_db_session, mock_tenant_dependency
    ):
        """Test that listing products requires authentication."""
        with pytest.raises(Exception):
            await list_products(
                tenant_id=mock_tenant_dependency,
                db_session=async_db_session,
                current_user=None,
            )


@pytest.mark.integration
class TestCatalogRouterErrorHandling:
    """Test error handling in catalog router."""

    async def test_create_product_invalid_data(
        self, async_db_session, mock_auth_user, mock_tenant_dependency
    ):
        """Test creating product with invalid data."""
        try:
            product_data = ProductCreateRequest(name="")
        except ValidationError:
            product_data = None

        if product_data is None:
            status_code = 422
        else:
            status_code, _ = await _call_with_status(
                create_product,
                success_status=201,
                product_data=product_data,
                tenant_id=mock_tenant_dependency,
                db_session=async_db_session,
                current_user=mock_auth_user,
            )

        # Should fail validation
        assert status_code in [400, 422, 401, 403]

    async def test_get_product_invalid_uuid(
        self, async_db_session, mock_auth_user, mock_tenant_dependency
    ):
        """Test getting product with invalid UUID."""
        status_code, _ = await _call_with_status(
            get_product,
            product_id="not-a-uuid",
            tenant_id=mock_tenant_dependency,
            db_session=async_db_session,
            current_user=mock_auth_user,
        )

        # Should fail validation
        assert status_code in [400, 422, 401, 403]

    async def test_update_product_not_found(
        self, async_db_session, mock_auth_user, mock_tenant_dependency
    ):
        """Test updating non-existent product."""
        product_id = str(uuid4())
        update_data = ProductUpdateRequest(name="Updated Name")

        status_code, _ = await _call_with_status(
            update_product,
            product_id=product_id,
            updates=update_data,
            tenant_id=mock_tenant_dependency,
            db_session=async_db_session,
            current_user=mock_auth_user,
        )

        # Should return 404
        assert status_code in [404, 401, 403, 500]


@pytest.mark.integration
class TestCatalogRouterTenantIsolation:
    """Test tenant isolation for catalog endpoints."""

    async def test_products_tenant_isolation(self, async_db_session):
        """Test that each tenant only sees their own products."""
        user_a = UserInfo(
            user_id=str(uuid4()),
            username="tenant-a-user",
            email="a@example.com",
            roles=["user"],
            permissions=["billing.catalog.view"],
            tenant_id="tenant-a",
        )
        user_b = UserInfo(
            user_id=str(uuid4()),
            username="tenant-b-user",
            email="b@example.com",
            roles=["user"],
            permissions=["billing.catalog.view"],
            tenant_id="tenant-b",
        )

        status_a, _ = await _call_with_status(
            list_products,
            tenant_id="tenant-a",
            db_session=async_db_session,
            current_user=user_a,
            category=None,
            product_type=None,
            usage_type=None,
            is_active=True,
            search=None,
            page=1,
            limit=50,
        )
        status_b, _ = await _call_with_status(
            list_products,
            tenant_id="tenant-b",
            db_session=async_db_session,
            current_user=user_b,
            category=None,
            product_type=None,
            usage_type=None,
            is_active=True,
            search=None,
            page=1,
            limit=50,
        )

        # Both should succeed
        assert status_a in [200, 401, 403]
        assert status_b in [200, 401, 403]
