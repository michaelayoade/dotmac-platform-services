"""
Fixtures for billing catalog tests.

Provides authentication and test data fixtures.
"""

import pytest

from dotmac.platform.auth.core import UserInfo
from dotmac.platform.billing import models as billing_models  # noqa: F401

# Import catalog-related ORM models so SQLAlchemy registers the tables on Base.metadata
from dotmac.platform.billing.catalog import models as catalog_models  # noqa: F401


@pytest.fixture(autouse=True)
def billing_catalog_test_environment(monkeypatch):
    monkeypatch.setenv("TESTING", "1")
    monkeypatch.setenv("DOTMAC_DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture
def tenant_id():
    """Standard tenant ID for catalog tests."""
    return "test-tenant-123"


@pytest.fixture
def customer_id():
    """Standard customer ID for catalog tests."""
    return "customer-456"


@pytest.fixture
def user_id():
    """Standard user ID for catalog tests."""
    return "user-789"


@pytest.fixture
def mock_current_user(user_id, tenant_id):
    """Mock current user for authentication."""
    return UserInfo(
        user_id=user_id,
        tenant_id=tenant_id,
        email="test@example.com",
        username="testuser",
        roles=["admin"],
        permissions=["catalog:write", "catalog:read"],
    )


@pytest.fixture
def auth_headers():
    """Mock authentication headers."""
    return {"Authorization": "Bearer test-token", "X-Tenant-ID": "test-tenant-123"}
