"""
Comprehensive tests for pricing router endpoints.

Tests all REST endpoints, authentication, error handling,
query parameters, and response validation.
"""
import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from dotmac.platform.billing.pricing.router import router
from dotmac.platform.billing.pricing.models import (

pytestmark = pytest.mark.asyncio

    PricingRuleCreateRequest,
    PricingRuleUpdateRequest,
    PricingRuleResponse,
    PriceCalculationRequest,
    PriceCalculationResult,
    DiscountType,
    PricingRule,
)
from dotmac.platform.billing.exceptions import PricingError

# Use authenticated_client from conftest.py instead of local fixtures
# The test_app fixture already registers the pricing router


@pytest.fixture
def mock_user():
    """Create mock authenticated user."""
    user = MagicMock()
    user.user_id = "user-123"
    user.tenant_id = "tenant-456"
    return user


@pytest.fixture
def mock_service():
    """Create mock pricing service."""
    return AsyncMock()


@pytest.fixture
def sample_rule():
    """Create sample pricing rule."""
    return PricingRule(
        rule_id="rule-123",
        tenant_id="tenant-456",
        name="10% Off Electronics",
        applies_to_categories=["electronics"],
        applies_to_all=False,
        applies_to_product_ids=[],
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("10"),
        min_quantity=None,
        customer_segments=[],
        starts_at=None,
        ends_at=None,
        max_uses=None,
        current_uses=0,
        is_active=True,
        metadata={},
        priority=10,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
    )


class TestCreatePricingRule:
    """Test POST /rules endpoint."""

    @pytest.mark.asyncio
    async def test_create_rule_success(self, client, mock_user, mock_service, sample_rule):
        """Test successful rule creation."""
        rule_data = {
            "name": "10% Off Electronics",
            "applies_to_categories": ["electronics"],
            "discount_type": "percentage",
            "discount_value": "10",
        }

        with patch(
            "dotmac.platform.billing.pricing.router.get_current_user", return_value=mock_user
        ):
            with patch(
                "dotmac.platform.billing.pricing.router.get_current_tenant_id",
                return_value="tenant-456",
            ):
                with patch("dotmac.platform.billing.pricing.router.PricingService") as MockService:
                    mock_instance = MockService.return_value
                    mock_instance.create_rule = AsyncMock(return_value=sample_rule)

                    response = client.post(
                        "/api/v1/billing/pricing/rules",
                        json=rule_data,
                    )

                    assert response.status_code == status.HTTP_201_CREATED
                    data = response.json()
                    assert data["name"] == "10% Off Electronics"

    @pytest.mark.asyncio
    async def test_create_rule_validation_error(self, client, mock_user):
        """Test rule creation with validation error."""
        rule_data = {
            "name": "Invalid Rule",
            # Missing required discount_type and discount_value
        }

        with patch(
            "dotmac.platform.billing.pricing.router.get_current_user", return_value=mock_user
        ):
            with patch(
                "dotmac.platform.billing.pricing.router.get_current_tenant_id",
                return_value="tenant-456",
            ):
                response = client.post(
                    "/api/v1/billing/pricing/rules",
                    json=rule_data,
                )

                assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestListPricingRules:
    """Test GET /rules endpoint."""

    @pytest.mark.asyncio
    async def test_list_all_rules(self, client, mock_user, sample_rule):
        """Test listing all pricing rules."""
        with patch(
            "dotmac.platform.billing.pricing.router.get_current_user", return_value=mock_user
        ):
            with patch(
                "dotmac.platform.billing.pricing.router.get_current_tenant_id",
                return_value="tenant-456",
            ):
                with patch("dotmac.platform.billing.pricing.router.PricingService") as MockService:
                    mock_instance = MockService.return_value
                    mock_instance.list_rules = AsyncMock(return_value=[sample_rule])

                    response = client.get("/api/v1/billing/pricing/rules")

                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert len(data) == 1
                    assert data[0]["rule_id"] == "rule-123"

    @pytest.mark.asyncio
    async def test_list_rules_with_filters(self, client, mock_user, sample_rule):
        """Test listing rules with query filters."""
        with patch(
            "dotmac.platform.billing.pricing.router.get_current_user", return_value=mock_user
        ):
            with patch(
                "dotmac.platform.billing.pricing.router.get_current_tenant_id",
                return_value="tenant-456",
            ):
                with patch("dotmac.platform.billing.pricing.router.PricingService") as MockService:
                    mock_instance = MockService.return_value
                    mock_instance.list_rules = AsyncMock(return_value=[sample_rule])

                    response = client.get(
                        "/api/v1/billing/pricing/rules",
                        params={
                            "product_id": "prod-123",
                            "active_only": True,
                            "category": "electronics",
                        },
                    )

                    assert response.status_code == status.HTTP_200_OK
                    mock_instance.list_rules.assert_called_once()


class TestGetPricingRule:
    """Test GET /rules/{rule_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_existing_rule(self, client, mock_user, sample_rule):
        """Test getting an existing rule."""
        with patch(
            "dotmac.platform.billing.pricing.router.get_current_user", return_value=mock_user
        ):
            with patch(
                "dotmac.platform.billing.pricing.router.get_current_tenant_id",
                return_value="tenant-456",
            ):
                with patch("dotmac.platform.billing.pricing.router.PricingService") as MockService:
                    mock_instance = MockService.return_value
                    mock_instance.get_rule = AsyncMock(return_value=sample_rule)

                    response = client.get("/api/v1/billing/pricing/rules/rule-123")

                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["rule_id"] == "rule-123"

    @pytest.mark.asyncio
    async def test_get_nonexistent_rule(self, client, mock_user):
        """Test getting a non-existent rule."""
        with patch(
            "dotmac.platform.billing.pricing.router.get_current_user", return_value=mock_user
        ):
            with patch(
                "dotmac.platform.billing.pricing.router.get_current_tenant_id",
                return_value="tenant-456",
            ):
                with patch("dotmac.platform.billing.pricing.router.PricingService") as MockService:
                    mock_instance = MockService.return_value
                    mock_instance.get_rule = AsyncMock(return_value=None)

                    response = client.get("/api/v1/billing/pricing/rules/nonexistent")

                    assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdatePricingRule:
    """Test PATCH /rules/{rule_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_rule_success(self, client, mock_user, sample_rule):
        """Test successful rule update."""
        update_data = {"discount_value": "15"}

        with patch(
            "dotmac.platform.billing.pricing.router.get_current_user", return_value=mock_user
        ):
            with patch(
                "dotmac.platform.billing.pricing.router.get_current_tenant_id",
                return_value="tenant-456",
            ):
                with patch("dotmac.platform.billing.pricing.router.PricingService") as MockService:
                    mock_instance = MockService.return_value
                    updated_rule = sample_rule.model_copy(update={"discount_value": Decimal("15")})
                    mock_instance.update_rule = AsyncMock(return_value=updated_rule)

                    response = client.patch(
                        "/api/v1/billing/pricing/rules/rule-123",
                        json=update_data,
                    )

                    assert response.status_code == status.HTTP_200_OK


class TestDeletePricingRule:
    """Test DELETE /rules/{rule_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_rule_success(self, client, mock_user):
        """Test successful rule deletion."""
        with patch(
            "dotmac.platform.billing.pricing.router.get_current_user", return_value=mock_user
        ):
            with patch(
                "dotmac.platform.billing.pricing.router.get_current_tenant_id",
                return_value="tenant-456",
            ):
                with patch("dotmac.platform.billing.pricing.router.PricingService") as MockService:
                    mock_instance = MockService.return_value
                    mock_instance.delete_rule = AsyncMock(return_value=True)

                    response = client.delete("/api/v1/billing/pricing/rules/rule-123")

                    assert response.status_code == status.HTTP_200_OK
                    assert "deleted successfully" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_delete_nonexistent_rule(self, client, mock_user):
        """Test deleting non-existent rule."""
        with patch(
            "dotmac.platform.billing.pricing.router.get_current_user", return_value=mock_user
        ):
            with patch(
                "dotmac.platform.billing.pricing.router.get_current_tenant_id",
                return_value="tenant-456",
            ):
                with patch("dotmac.platform.billing.pricing.router.PricingService") as MockService:
                    mock_instance = MockService.return_value
                    mock_instance.delete_rule = AsyncMock(return_value=False)

                    response = client.delete("/api/v1/billing/pricing/rules/nonexistent")

                    assert response.status_code == status.HTTP_404_NOT_FOUND


class TestActivateDeactivateRule:
    """Test rule activation/deactivation endpoints."""

    @pytest.mark.asyncio
    async def test_activate_rule(self, client, mock_user):
        """Test activating a pricing rule."""
        with patch(
            "dotmac.platform.billing.pricing.router.get_current_user", return_value=mock_user
        ):
            with patch(
                "dotmac.platform.billing.pricing.router.get_current_tenant_id",
                return_value="tenant-456",
            ):
                with patch("dotmac.platform.billing.pricing.router.PricingService") as MockService:
                    mock_instance = MockService.return_value
                    mock_instance.activate_rule = AsyncMock(return_value=True)

                    response = client.post("/api/v1/billing/pricing/rules/rule-123/activate")

                    assert response.status_code == status.HTTP_200_OK
                    assert "activated successfully" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_deactivate_rule(self, client, mock_user):
        """Test deactivating a pricing rule."""
        with patch(
            "dotmac.platform.billing.pricing.router.get_current_user", return_value=mock_user
        ):
            with patch(
                "dotmac.platform.billing.pricing.router.get_current_tenant_id",
                return_value="tenant-456",
            ):
                with patch("dotmac.platform.billing.pricing.router.PricingService") as MockService:
                    mock_instance = MockService.return_value
                    mock_instance.deactivate_rule = AsyncMock(return_value=True)

                    response = client.post("/api/v1/billing/pricing/rules/rule-123/deactivate")

                    assert response.status_code == status.HTTP_200_OK
                    assert "deactivated successfully" in response.json()["message"]


class TestCalculatePrice:
    """Test price calculation endpoints."""

    @pytest.mark.asyncio
    async def test_calculate_price_post(self, client, mock_user):
        """Test POST price calculation."""
        calc_request = {
            "product_id": "prod-123",
            "customer_id": "cust-456",
            "quantity": 2,
            "customer_segments": ["vip"],
        }

        calc_result = PriceCalculationResult(
            product_id="prod-123",
            customer_id="cust-456",
            quantity=2,
            base_price=Decimal("100.00"),
            subtotal=Decimal("200.00"),
            total_discount_amount=Decimal("20.00"),
            final_price=Decimal("180.00"),
            applied_adjustments=[],
        )

        with patch(
            "dotmac.platform.billing.pricing.router.get_current_user", return_value=mock_user
        ):
            with patch(
                "dotmac.platform.billing.pricing.router.get_current_tenant_id",
                return_value="tenant-456",
            ):
                with patch("dotmac.platform.billing.pricing.router.PricingService") as MockService:
                    mock_instance = MockService.return_value
                    mock_instance.calculate_price = AsyncMock(return_value=calc_result)

                    response = client.post(
                        "/api/v1/billing/pricing/calculate",
                        json=calc_request,
                    )

                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["final_price"] == "180.00"

    @pytest.mark.asyncio
    async def test_calculate_price_get(self, client, mock_user):
        """Test GET price calculation with query params."""
        calc_result = PriceCalculationResult(
            product_id="prod-123",
            customer_id="cust-789",
            quantity=1,
            base_price=Decimal("50.00"),
            subtotal=Decimal("50.00"),
            total_discount_amount=Decimal("0.00"),
            final_price=Decimal("50.00"),
            applied_adjustments=[],
        )

        with patch(
            "dotmac.platform.billing.pricing.router.get_current_user", return_value=mock_user
        ):
            with patch(
                "dotmac.platform.billing.pricing.router.get_current_tenant_id",
                return_value="tenant-456",
            ):
                with patch("dotmac.platform.billing.pricing.router.PricingService") as MockService:
                    mock_instance = MockService.return_value
                    mock_instance.calculate_price = AsyncMock(return_value=calc_result)

                    response = client.get(
                        "/api/v1/billing/pricing/calculate/prod-123",
                        params={
                            "customer_id": "cust-789",
                            "quantity": 1,
                        },
                    )

                    assert response.status_code == status.HTTP_200_OK


class TestRuleUsageEndpoints:
    """Test rule usage tracking endpoints."""

    @pytest.mark.asyncio
    async def test_get_rule_usage(self, client, mock_user):
        """Test getting rule usage statistics."""
        usage_stats = {
            "rule_id": "rule-123",
            "rule_name": "Test Rule",
            "current_uses": 50,
            "max_uses": 100,
            "usage_remaining": 50,
            "is_active": True,
            "created_at": "2025-01-01T00:00:00Z",
        }

        with patch(
            "dotmac.platform.billing.pricing.router.get_current_user", return_value=mock_user
        ):
            with patch(
                "dotmac.platform.billing.pricing.router.get_current_tenant_id",
                return_value="tenant-456",
            ):
                with patch("dotmac.platform.billing.pricing.router.PricingService") as MockService:
                    mock_instance = MockService.return_value
                    mock_instance.get_rule_usage_stats = AsyncMock(return_value=usage_stats)

                    response = client.get("/api/v1/billing/pricing/rules/rule-123/usage")

                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["current_uses"] == 50

    @pytest.mark.asyncio
    async def test_reset_rule_usage(self, client, mock_user):
        """Test resetting rule usage counter."""
        with patch(
            "dotmac.platform.billing.pricing.router.get_current_user", return_value=mock_user
        ):
            with patch(
                "dotmac.platform.billing.pricing.router.get_current_tenant_id",
                return_value="tenant-456",
            ):
                with patch("dotmac.platform.billing.pricing.router.PricingService") as MockService:
                    mock_instance = MockService.return_value
                    mock_instance.reset_rule_usage = AsyncMock(return_value=True)

                    response = client.post("/api/v1/billing/pricing/rules/rule-123/reset-usage")

                    assert response.status_code == status.HTTP_200_OK
                    assert "reset successfully" in response.json()["message"]


class TestRuleTestingEndpoints:
    """Test rule testing and validation endpoints."""

    @pytest.mark.asyncio
    async def test_test_pricing_rules(self, client, mock_user, sample_rule):
        """Test rule testing endpoint."""
        test_request = {
            "product_id": "prod-123",
            "customer_id": "cust-456",
            "quantity": 1,
            "customer_segments": [],
        }

        with patch(
            "dotmac.platform.billing.pricing.router.get_current_user", return_value=mock_user
        ):
            with patch(
                "dotmac.platform.billing.pricing.router.get_current_tenant_id",
                return_value="tenant-456",
            ):
                with patch("dotmac.platform.billing.pricing.router.PricingService") as MockService:
                    mock_instance = MockService.return_value
                    mock_instance.get_applicable_rules = AsyncMock(return_value=[sample_rule])

                    response = client.post(
                        "/api/v1/billing/pricing/rules/test",
                        json=test_request,
                    )

                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert "applicable_rules" in data
                    assert len(data["applicable_rules"]) == 1

    @pytest.mark.asyncio
    async def test_detect_conflicts(self, client, mock_user):
        """Test conflict detection endpoint."""
        conflicts = [
            {
                "type": "priority_overlap",
                "rule1": {"id": "rule-1", "name": "Rule 1"},
                "rule2": {"id": "rule-2", "name": "Rule 2"},
                "priority": 10,
                "description": "Rules have overlapping conditions",
            }
        ]

        with patch(
            "dotmac.platform.billing.pricing.router.get_current_user", return_value=mock_user
        ):
            with patch(
                "dotmac.platform.billing.pricing.router.get_current_tenant_id",
                return_value="tenant-456",
            ):
                with patch("dotmac.platform.billing.pricing.router.PricingService") as MockService:
                    mock_instance = MockService.return_value
                    mock_instance.detect_rule_conflicts = AsyncMock(return_value=conflicts)

                    response = client.get("/api/v1/billing/pricing/rules/conflicts")

                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["conflicts_found"] is True
                    assert data["total_conflicts"] == 1


class TestBulkOperations:
    """Test bulk operation endpoints."""

    @pytest.mark.asyncio
    async def test_bulk_activate_rules(self, client, mock_user):
        """Test bulk rule activation."""
        rule_ids = ["rule-1", "rule-2", "rule-3"]

        results = {
            "activated": 3,
            "failed": 0,
            "errors": [],
        }

        with patch(
            "dotmac.platform.billing.pricing.router.get_current_user", return_value=mock_user
        ):
            with patch(
                "dotmac.platform.billing.pricing.router.get_current_tenant_id",
                return_value="tenant-456",
            ):
                with patch("dotmac.platform.billing.pricing.router.PricingService") as MockService:
                    mock_instance = MockService.return_value
                    mock_instance.bulk_activate_rules = AsyncMock(return_value=results)

                    response = client.post(
                        "/api/v1/billing/pricing/rules/bulk-activate",
                        json=rule_ids,
                    )

                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["activated"] == 3

    @pytest.mark.asyncio
    async def test_bulk_deactivate_rules(self, client, mock_user):
        """Test bulk rule deactivation."""
        rule_ids = ["rule-1", "rule-2"]

        results = {
            "deactivated": 2,
            "failed": 0,
            "errors": [],
        }

        with patch(
            "dotmac.platform.billing.pricing.router.get_current_user", return_value=mock_user
        ):
            with patch(
                "dotmac.platform.billing.pricing.router.get_current_tenant_id",
                return_value="tenant-456",
            ):
                with patch("dotmac.platform.billing.pricing.router.PricingService") as MockService:
                    mock_instance = MockService.return_value
                    mock_instance.bulk_deactivate_rules = AsyncMock(return_value=results)

                    response = client.post(
                        "/api/v1/billing/pricing/rules/bulk-deactivate",
                        json=rule_ids,
                    )

                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["deactivated"] == 2
