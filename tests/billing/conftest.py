"""
Billing system test fixtures and configuration.

Provides reusable fixtures for testing billing components.
"""

import pytest
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Any
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.orm import clear_mappers

# Set test environment
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Import models with error handling
try:
    from dotmac.platform.billing.catalog.models import (
        Product,
        ProductCategory,
        ProductType,
        UsageType,
        ProductCreateRequest,
        ProductCategoryCreateRequest,
    )
except ImportError:
    # Create mock classes if imports fail
    Product = MagicMock
    ProductCategory = MagicMock
    ProductType = MagicMock
    UsageType = MagicMock
    ProductCreateRequest = MagicMock
    ProductCategoryCreateRequest = MagicMock

try:
    from dotmac.platform.billing.subscriptions.models import (
        SubscriptionPlan,
        Subscription,
        BillingCycle,
        SubscriptionStatus,
        SubscriptionPlanCreateRequest,
        SubscriptionCreateRequest,
    )
except ImportError:
    SubscriptionPlan = MagicMock
    Subscription = MagicMock
    BillingCycle = MagicMock
    SubscriptionStatus = MagicMock
    SubscriptionPlanCreateRequest = MagicMock
    SubscriptionCreateRequest = MagicMock

try:
    from dotmac.platform.billing.pricing.models import (
        PricingRule,
        DiscountType,
        PricingRuleCreateRequest,
        PriceCalculationRequest,
    )
except ImportError:
    PricingRule = MagicMock
    DiscountType = MagicMock
    PricingRuleCreateRequest = MagicMock
    PriceCalculationRequest = MagicMock

# Import services with error handling
try:
    from dotmac.platform.billing.catalog.service import ProductService
except ImportError:
    ProductService = MagicMock

try:
    from dotmac.platform.billing.subscriptions.service import SubscriptionService
except ImportError:
    SubscriptionService = MagicMock

try:
    from dotmac.platform.billing.pricing.service import PricingEngine
except ImportError:
    PricingEngine = MagicMock

try:
    from dotmac.platform.billing.integration import BillingIntegrationService
except ImportError:
    BillingIntegrationService = MagicMock


@pytest.fixture
def tenant_id():
    """Standard tenant ID for billing tests."""
    return "test-tenant-123"


@pytest.fixture
def customer_id():
    """Standard customer ID for billing tests."""
    return "customer-456"


@pytest.fixture
def user_id():
    """Standard user ID for billing tests."""
    return "user-789"


# ========================================
# Product Catalog Fixtures
# ========================================


@pytest.fixture
def sample_product_category():
    """Sample product category for testing."""
    return ProductCategory(
        category_id="cat_123",
        tenant_id="test-tenant-123",
        name="Software Tools",
        description="Development and productivity software",
        is_active=True,
        metadata={"department": "engineering"},
        created_at=datetime.now(timezone.utc),
        updated_at=None,
    )


@pytest.fixture
def sample_product():
    """Sample product for testing."""
    return Product(
        product_id="prod_123",
        tenant_id="test-tenant-123",
        sku="SKU-TOOL-001",
        name="Development Tool Pro",
        description="Professional development environment",
        product_type=ProductType.SUBSCRIPTION,
        category="software-tools",
        base_price=Decimal("99.99"),
        currency="USD",
        is_active=True,
        usage_rates={"api_calls": Decimal("0.01"), "storage_gb": Decimal("0.50")},
        metadata={"tier": "professional"},
        created_at=datetime.now(timezone.utc),
        updated_at=None,
    )


@pytest.fixture
def usage_based_product():
    """Sample usage-based product for testing."""
    return Product(
        product_id="prod_usage_123",
        tenant_id="test-tenant-123",
        sku="SKU-API-001",
        name="API Service",
        description="Pay-per-use API service",
        product_type=ProductType.USAGE_BASED,
        category="api-services",
        base_price=Decimal("0"),
        currency="USD",
        is_active=True,
        usage_rates={"api_calls": Decimal("0.001"), "bandwidth_gb": Decimal("0.10")},
        metadata={"rate_limited": True},
        created_at=datetime.now(timezone.utc),
        updated_at=None,
    )


@pytest.fixture
def product_create_request():
    """Sample product creation request."""
    return ProductCreateRequest(
        sku="SKU-TEST-001",
        name="Test Product",
        description="A test product",
        product_type=ProductType.ONE_TIME,
        category="test-category",
        base_price=Decimal("49.99"),
        currency="USD",
        usage_rates={"api_calls": Decimal("0.01")},
        metadata={"test": True},
    )


@pytest.fixture
def category_create_request():
    """Sample category creation request."""
    return ProductCategoryCreateRequest(
        name="Test Category",
        description="A test category",
        metadata={"test": True},
    )


# ========================================
# Subscription Fixtures
# ========================================


@pytest.fixture
def sample_subscription_plan():
    """Sample subscription plan for testing."""
    return SubscriptionPlan(
        plan_id="plan_123",
        tenant_id="test-tenant-123",
        product_id="prod_123",
        name="Pro Plan",
        description="Professional subscription plan",
        billing_cycle=BillingCycle.MONTHLY,
        price=Decimal("99.99"),
        currency="USD",
        setup_fee=Decimal("19.99"),
        trial_days=14,
        included_usage={"api_calls": 10000, "storage_gb": 100},
        overage_rates={"api_calls": Decimal("0.001"), "storage_gb": Decimal("0.50")},
        is_active=True,
        metadata={"tier": "professional"},
        created_at=datetime.now(timezone.utc),
        updated_at=None,
    )


@pytest.fixture
def sample_subscription(sample_subscription_plan):
    """Sample subscription for testing."""
    now = datetime.now(timezone.utc)
    return Subscription(
        subscription_id="sub_123",
        tenant_id="test-tenant-123",
        customer_id="customer-456",
        plan_id="plan_123",
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        status=SubscriptionStatus.ACTIVE,
        trial_end=now + timedelta(days=14),
        cancel_at_period_end=False,
        canceled_at=None,
        ended_at=None,
        custom_price=None,
        usage_records={"api_calls": 5000, "storage_gb": 50},
        metadata={"source": "web"},
        created_at=now,
        updated_at=None,
    )


@pytest.fixture
def plan_create_request():
    """Sample subscription plan creation request."""
    return SubscriptionPlanCreateRequest(
        product_id="prod_123",
        name="Test Plan",
        description="A test subscription plan",
        billing_cycle=BillingCycle.MONTHLY,
        price=Decimal("29.99"),
        currency="USD",
        setup_fee=Decimal("9.99"),
        trial_days=7,
        included_usage={"api_calls": 5000},
        overage_rates={"api_calls": Decimal("0.002")},
        metadata={"test": True},
    )


@pytest.fixture
def subscription_create_request():
    """Sample subscription creation request."""
    return SubscriptionCreateRequest(
        customer_id="customer-456",
        plan_id="plan_123",
        start_date=None,
        custom_price=None,
        trial_end_override=None,
        metadata={"source": "api"},
    )


# ========================================
# Pricing Fixtures
# ========================================


@pytest.fixture
def sample_pricing_rule():
    """Sample pricing rule for testing."""
    return PricingRule(
        rule_id="rule_123",
        tenant_id="test-tenant-123",
        name="Volume Discount",
        description="10% off for orders over $100",
        applies_to_product_ids=["prod_123"],
        applies_to_categories=[],
        applies_to_all=False,
        min_quantity=2,
        customer_segments=["premium"],
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("10"),
        starts_at=None,
        ends_at=None,
        max_uses=None,
        current_uses=0,
        priority=100,
        is_active=True,
        metadata={"campaign": "q4-2024"},
        created_at=datetime.now(timezone.utc),
        updated_at=None,
    )


@pytest.fixture
def pricing_rule_create_request():
    """Sample pricing rule creation request."""
    return PricingRuleCreateRequest(
        name="Test Rule",
        description="A test pricing rule",
        applies_to_product_ids=["prod_123"],
        applies_to_categories=[],
        applies_to_all=False,
        min_quantity=1,
        customer_segments=["test"],
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("15"),
        starts_at=None,
        ends_at=None,
        max_uses=100,
        priority=50,
        metadata={"test": True},
    )


@pytest.fixture
def price_calculation_request():
    """Sample price calculation request."""
    return PriceCalculationRequest(
        product_id="prod_123",
        quantity=2,
        customer_id="customer-456",
        customer_segments=["premium"],
        calculation_date=None,
        metadata={"test": True},
    )


# ========================================
# Service Fixtures (Mocked)
# ========================================


@pytest.fixture
def mock_catalog_service():
    """Mock product catalog service."""
    service = AsyncMock(spec=ProductService)
    return service


@pytest.fixture
def mock_subscription_service():
    """Mock subscription service."""
    service = AsyncMock(spec=SubscriptionService)
    return service


@pytest.fixture
def mock_pricing_service():
    """Mock pricing service."""
    service = AsyncMock(spec=PricingEngine)
    return service


@pytest.fixture
def mock_integration_service():
    """Mock billing integration service."""
    service = AsyncMock(spec=BillingIntegrationService)
    return service


# ========================================
# Database Fixtures
# ========================================


@pytest.fixture
async def mock_db_session():
    """Mock database session for testing."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    session.scalar = AsyncMock()
    session.scalars = AsyncMock()

    # Mock query results
    mock_result = MagicMock()
    mock_result.scalar.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    mock_result.all.return_value = []
    session.execute.return_value = mock_result

    return session


@pytest.fixture
def mock_db_product():
    """Mock database product record."""
    # Use mock instead of importing to avoid conflicts
    BillingProductTable = MagicMock

    db_product = MagicMock(spec=BillingProductTable)
    db_product.product_id = "prod_123"
    db_product.tenant_id = "test-tenant-123"
    db_product.sku = "SKU-TEST-001"
    db_product.name = "Test Product"
    db_product.description = "A test product"
    db_product.product_type = "ONE_TIME"
    db_product.category = "test-category"
    db_product.base_price = Decimal("49.99")
    db_product.currency = "USD"
    db_product.is_active = True
    db_product.usage_rates = {"api_calls": "0.01"}
    db_product.metadata_json = {"test": True}
    db_product.created_at = datetime.now(timezone.utc)
    db_product.updated_at = None
    return db_product


@pytest.fixture
def mock_db_subscription():
    """Mock database subscription record."""
    # Use mock instead of importing to avoid conflicts
    BillingSubscriptionTable = MagicMock

    now = datetime.now(timezone.utc)
    db_subscription = MagicMock(spec=BillingSubscriptionTable)
    db_subscription.subscription_id = "sub_123"
    db_subscription.tenant_id = "test-tenant-123"
    db_subscription.customer_id = "customer-456"
    db_subscription.plan_id = "plan_123"
    db_subscription.current_period_start = now
    db_subscription.current_period_end = now + timedelta(days=30)
    db_subscription.status = "active"
    db_subscription.trial_end = now + timedelta(days=14)
    db_subscription.cancel_at_period_end = False
    db_subscription.canceled_at = None
    db_subscription.ended_at = None
    db_subscription.custom_price = None
    db_subscription.usage_records = {"api_calls": 5000}
    db_subscription.metadata_json = {"source": "web"}
    db_subscription.created_at = now
    db_subscription.updated_at = None
    return db_subscription


@pytest.fixture
def mock_db_pricing_rule():
    """Mock database pricing rule record."""
    # Use mock instead of importing to avoid conflicts
    BillingPricingRuleTable = MagicMock

    db_rule = MagicMock(spec=BillingPricingRuleTable)
    db_rule.rule_id = "rule_123"
    db_rule.tenant_id = "test-tenant-123"
    db_rule.name = "Test Rule"
    db_rule.description = "A test rule"
    db_rule.applies_to_product_ids = ["prod_123"]
    db_rule.applies_to_categories = []
    db_rule.applies_to_all = False
    db_rule.min_quantity = 1
    db_rule.customer_segments = ["test"]
    db_rule.discount_type = "percentage"
    db_rule.discount_value = Decimal("10")
    db_rule.starts_at = None
    db_rule.ends_at = None
    db_rule.max_uses = None
    db_rule.current_uses = 0
    db_rule.priority = 100
    db_rule.is_active = True
    db_rule.metadata_json = {"test": True}
    db_rule.created_at = datetime.now(timezone.utc)
    db_rule.updated_at = None
    return db_rule


# ========================================
# Test Data Builders
# ========================================


class TestDataBuilder:
    """Helper class for building test data with variations."""

    @staticmethod
    def build_product(**overrides) -> Product:
        """Build a product with optional field overrides."""
        defaults = {
            "product_id": "prod_test",
            "tenant_id": "test-tenant",
            "sku": "SKU-TEST",
            "name": "Test Product",
            "description": "Test description",
            "product_type": ProductType.ONE_TIME,
            "category": "test",
            "base_price": Decimal("10.00"),
            "currency": "USD",
            "is_active": True,
            "usage_rates": {},
            "metadata": {},
            "created_at": datetime.now(timezone.utc),
            "updated_at": None,
        }
        defaults.update(overrides)
        return Product(**defaults)

    @staticmethod
    def build_subscription_plan(**overrides) -> SubscriptionPlan:
        """Build a subscription plan with optional field overrides."""
        defaults = {
            "plan_id": "plan_test",
            "tenant_id": "test-tenant",
            "product_id": "prod_test",
            "name": "Test Plan",
            "description": "Test plan description",
            "billing_cycle": BillingCycle.MONTHLY,
            "price": Decimal("29.99"),
            "currency": "USD",
            "setup_fee": None,
            "trial_days": None,
            "included_usage": {},
            "overage_rates": {},
            "is_active": True,
            "metadata": {},
            "created_at": datetime.now(timezone.utc),
            "updated_at": None,
        }
        defaults.update(overrides)
        return SubscriptionPlan(**defaults)

    @staticmethod
    def build_subscription(**overrides) -> Subscription:
        """Build a subscription with optional field overrides."""
        now = datetime.now(timezone.utc)
        defaults = {
            "subscription_id": "sub_test",
            "tenant_id": "test-tenant",
            "customer_id": "customer_test",
            "plan_id": "plan_test",
            "current_period_start": now,
            "current_period_end": now + timedelta(days=30),
            "status": SubscriptionStatus.ACTIVE,
            "trial_end": None,
            "cancel_at_period_end": False,
            "canceled_at": None,
            "ended_at": None,
            "custom_price": None,
            "usage_records": {},
            "metadata": {},
            "created_at": now,
            "updated_at": None,
        }
        defaults.update(overrides)
        return Subscription(**defaults)

    @staticmethod
    def build_pricing_rule(**overrides) -> PricingRule:
        """Build a pricing rule with optional field overrides."""
        defaults = {
            "rule_id": "rule_test",
            "tenant_id": "test-tenant",
            "name": "Test Rule",
            "description": "Test rule description",
            "applies_to_product_ids": [],
            "applies_to_categories": [],
            "applies_to_all": True,
            "min_quantity": None,
            "customer_segments": [],
            "discount_type": DiscountType.PERCENTAGE,
            "discount_value": Decimal("10"),
            "starts_at": None,
            "ends_at": None,
            "max_uses": None,
            "current_uses": 0,
            "priority": 100,
            "is_active": True,
            "metadata": {},
            "created_at": datetime.now(timezone.utc),
            "updated_at": None,
        }
        defaults.update(overrides)
        return PricingRule(**defaults)


@pytest.fixture
def test_data_builder():
    """Test data builder fixture."""
    return TestDataBuilder


# ========================================
# Authentication and Context Fixtures
# ========================================


@pytest.fixture
def mock_current_user():
    """Mock authenticated user for testing."""
    # Create mock user claims
    user_claims = MagicMock()
    user_claims.configure_mock(
        user_id="user_123",
        tenant_id="test-tenant-123",
        scopes=["billing:read", "billing:write", "billing:admin"],
        metadata={"test": True},
    )
    return user_claims


@pytest.fixture
def mock_tenant_context():
    """Mock tenant context for testing."""
    from unittest.mock import MagicMock

    context = MagicMock()
    context.tenant_id = "test-tenant-123"
    context.user_id = "user_123"
    return context


# ========================================
# Error Fixtures
# ========================================


@pytest.fixture
def billing_error_scenarios():
    """Common error scenarios for billing tests."""
    return {
        "product_not_found": {
            "exception": "ProductNotFoundError",
            "message": "Product not found",
        },
        "subscription_not_found": {
            "exception": "SubscriptionNotFoundError",
            "message": "Subscription not found",
        },
        "plan_not_found": {
            "exception": "PlanNotFoundError",
            "message": "Plan not found",
        },
        "pricing_error": {
            "exception": "PricingError",
            "message": "Pricing calculation error",
        },
        "subscription_error": {
            "exception": "SubscriptionError",
            "message": "Subscription operation error",
        },
    }


# ========================================
# Router Testing Fixtures
# ========================================


@pytest.fixture
async def router_client(async_session, test_app):
    """
    HTTP client for router integration tests with proper session override.

    This fixture ensures the router endpoints use the same database session
    as the test, allowing tests to create data and verify it through API calls.

    Overrides BOTH get_session_dependency AND get_async_session since different
    routers use different session dependencies.
    """
    from httpx import AsyncClient, ASGITransport
    from dotmac.platform.db import get_session_dependency, get_async_session

    # Override BOTH session dependencies to use test session
    async def override_get_session():
        yield async_session

    test_app.dependency_overrides[get_session_dependency] = override_get_session
    test_app.dependency_overrides[get_async_session] = override_get_session

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    # Clear overrides after test
    test_app.dependency_overrides.clear()


@pytest.fixture
async def unauth_client(async_session):
    """
    HTTP client for testing unauthorized access (401/403 scenarios).

    This fixture creates a fresh FastAPI app WITHOUT auth override,
    allowing tests to verify authentication failures properly.

    Still includes session override for database consistency.
    """
    from httpx import AsyncClient, ASGITransport
    from fastapi import FastAPI
    from dotmac.platform.db import get_session_dependency, get_async_session
    from dotmac.platform.tenant import get_current_tenant_id

    # Create minimal app without auth override
    app = FastAPI(title="Unauth Test App")

    # Override session dependencies (needed for DB access)
    async def override_get_session():
        yield async_session

    app.dependency_overrides[get_session_dependency] = override_get_session
    app.dependency_overrides[get_async_session] = override_get_session

    # Override tenant (needed for tenant filtering)
    def override_get_current_tenant_id():
        return "test-tenant"

    app.dependency_overrides[get_current_tenant_id] = override_get_current_tenant_id

    # Register billing routers
    try:
        from dotmac.platform.billing.payments.router import router as payments_router

        app.include_router(payments_router, prefix="/api/v1/billing", tags=["Payments"])
    except ImportError:
        pass

    try:
        from dotmac.platform.billing.subscriptions.router import router as subscriptions_router

        app.include_router(
            subscriptions_router, prefix="/api/v1/billing/subscriptions", tags=["Subscriptions"]
        )
    except ImportError:
        pass

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def error_mock_client(test_app):
    """
    HTTP client for testing error handling with mocked dependencies.

    This fixture does NOT override session dependencies, allowing tests
    to mock database errors and other failure scenarios.

    Note: Cannot be used with tests that need real DB data.
    """
    from httpx import AsyncClient, ASGITransport

    # Use test_app but don't override sessions - allows mocking
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
