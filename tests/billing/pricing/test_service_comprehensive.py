"""
Comprehensive tests for pricing engine service.

Tests async operations, rule matching, discount calculations,
usage scenarios, and edge cases.
"""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from dotmac.platform.billing.pricing.service import (
    PricingEngine,
    generate_rule_id,
    generate_usage_id,
)
from dotmac.platform.billing.pricing.models import (
    PricingRuleCreateRequest,
    PricingRuleUpdateRequest,
    PriceCalculationRequest,
    DiscountType,
)
from dotmac.platform.billing.exceptions import PricingError, InvalidPricingRuleError

pytestmark = pytest.mark.asyncio


@pytest.fixture
def tenant_id():
    """Provide test tenant ID."""
    return "test-tenant-123"


@pytest.fixture
def product_id():
    """Provide test product ID."""
    return "prod-abc-123"


@pytest.fixture
def customer_id():
    """Provide test customer ID."""
    return "cust-xyz-789"


@pytest.fixture
def pricing_engine():
    """Create pricing engine instance."""
    return PricingEngine()


class TestRuleIDGeneration:
    """Test ID generation functions."""

    def test_generate_rule_id(self):
        """Test rule ID generation."""
        rule_id = generate_rule_id()
        assert rule_id.startswith("rule_")
        assert len(rule_id) == 17  # "rule_" + 12 hex chars

    def test_generate_usage_id(self):
        """Test usage ID generation."""
        usage_id = generate_usage_id()
        assert usage_id.startswith("usage_")
        assert len(usage_id) == 18  # "usage_" + 12 hex chars

    def test_unique_ids(self):
        """Test that generated IDs are unique."""
        ids = {generate_rule_id() for _ in range(100)}
        assert len(ids) == 100  # All unique


class TestCreatePricingRule:
    """Test pricing rule creation."""

    @pytest.mark.asyncio
    async def test_create_percentage_rule(self, pricing_engine, tenant_id):
        """Test creating percentage discount rule."""
        rule_data = PricingRuleCreateRequest(
            name="10% Off Electronics",
            applies_to_categories=["electronics"],
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10"),
        )

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_session:
            mock_session.return_value.__aenter__.return_value = MagicMock()

            rule = await pricing_engine.create_pricing_rule(rule_data, tenant_id)

            assert rule.name == "10% Off Electronics"
            assert rule.discount_type == DiscountType.PERCENTAGE
            assert rule.discount_value == Decimal("10")

    @pytest.mark.asyncio
    async def test_create_fixed_amount_rule(self, pricing_engine, tenant_id):
        """Test creating fixed amount discount rule."""
        rule_data = PricingRuleCreateRequest(
            name="$5 Off",
            applies_to_all=True,
            discount_type=DiscountType.FIXED_AMOUNT,
            discount_value=Decimal("5.00"),
        )

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_session:
            mock_session.return_value.__aenter__.return_value = MagicMock()

            rule = await pricing_engine.create_pricing_rule(rule_data, tenant_id)

            assert rule.discount_type == DiscountType.FIXED_AMOUNT
            assert rule.applies_to_all is True

    @pytest.mark.asyncio
    async def test_create_rule_with_min_quantity(self, pricing_engine, tenant_id):
        """Test creating rule with minimum quantity requirement."""
        rule_data = PricingRuleCreateRequest(
            name="Bulk Discount",
            applies_to_all=True,
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("15"),
            min_quantity=10,
        )

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_session:
            mock_session.return_value.__aenter__.return_value = MagicMock()

            rule = await pricing_engine.create_pricing_rule(rule_data, tenant_id)

            assert rule.min_quantity == 10

    @pytest.mark.asyncio
    async def test_create_rule_with_customer_segments(self, pricing_engine, tenant_id):
        """Test creating rule for specific customer segments."""
        rule_data = PricingRuleCreateRequest(
            name="VIP Discount",
            applies_to_all=True,
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("20"),
            customer_segments=["vip", "premium"],
        )

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_session:
            mock_session.return_value.__aenter__.return_value = MagicMock()

            rule = await pricing_engine.create_pricing_rule(rule_data, tenant_id)

            assert "vip" in rule.customer_segments
            assert "premium" in rule.customer_segments

    @pytest.mark.asyncio
    async def test_create_rule_with_time_constraints(self, pricing_engine, tenant_id):
        """Test creating rule with start and end dates."""
        now = datetime.now(timezone.utc)
        rule_data = PricingRuleCreateRequest(
            name="Holiday Sale",
            applies_to_all=True,
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("25"),
            starts_at=now,
            ends_at=now + timedelta(days=7),
        )

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_session:
            mock_session.return_value.__aenter__.return_value = MagicMock()

            rule = await pricing_engine.create_pricing_rule(rule_data, tenant_id)

            assert rule.starts_at is not None
            assert rule.ends_at is not None

    @pytest.mark.asyncio
    async def test_create_rule_validation_no_target(self, pricing_engine, tenant_id):
        """Test validation error when rule doesn't target anything."""
        rule_data = PricingRuleCreateRequest(
            name="Invalid Rule",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10"),
        )

        with pytest.raises(InvalidPricingRuleError) as exc:
            await pricing_engine.create_pricing_rule(rule_data, tenant_id)

        assert "must apply to at least something" in str(exc.value)

    @pytest.mark.asyncio
    async def test_create_rule_excessive_discount(self, pricing_engine, tenant_id):
        """Test validation for excessive percentage discount."""
        rule_data = PricingRuleCreateRequest(
            name="Too Much Discount",
            applies_to_all=True,
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("150"),  # Over 100%
        )

        with patch("dotmac.platform.settings.settings.billing.max_discount_percentage", 100):
            with pytest.raises(InvalidPricingRuleError) as exc:
                await pricing_engine.create_pricing_rule(rule_data, tenant_id)

            assert "cannot exceed" in str(exc.value)


class TestGetPricingRule:
    """Test pricing rule retrieval."""

    @pytest.mark.asyncio
    async def test_get_existing_rule(self, pricing_engine, tenant_id):
        """Test getting an existing pricing rule."""
        rule_id = "rule-123"

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock database response
            mock_result = MagicMock()
            mock_db_rule = MagicMock()
            mock_db_rule.rule_id = rule_id
            mock_db_rule.name = "Test Rule"
            mock_result.scalar_one_or_none.return_value = mock_db_rule
            mock_db.execute.return_value = mock_result

            rule = await pricing_engine.get_pricing_rule(rule_id, tenant_id)

            assert rule.rule_id == rule_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_rule(self, pricing_engine, tenant_id):
        """Test getting a non-existent pricing rule."""
        rule_id = "nonexistent"

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            with pytest.raises(PricingError) as exc:
                await pricing_engine.get_pricing_rule(rule_id, tenant_id)

            assert "not found" in str(exc.value)


class TestListPricingRules:
    """Test pricing rule listing."""

    @pytest.mark.asyncio
    async def test_list_all_rules(self, pricing_engine, tenant_id):
        """Test listing all active rules."""
        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result

            rules = await pricing_engine.list_pricing_rules(tenant_id)

            assert isinstance(rules, list)

    @pytest.mark.asyncio
    async def test_list_rules_for_product(self, pricing_engine, tenant_id, product_id):
        """Test listing rules for specific product."""
        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result

            rules = await pricing_engine.list_pricing_rules(tenant_id, product_id=product_id)

            assert isinstance(rules, list)

    @pytest.mark.asyncio
    async def test_list_rules_for_category(self, pricing_engine, tenant_id):
        """Test listing rules for specific category."""
        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result

            rules = await pricing_engine.list_pricing_rules(tenant_id, category="electronics")

            assert isinstance(rules, list)

    @pytest.mark.asyncio
    async def test_list_inactive_rules(self, pricing_engine, tenant_id):
        """Test listing inactive rules."""
        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result

            rules = await pricing_engine.list_pricing_rules(tenant_id, active_only=False)

            assert isinstance(rules, list)


class TestUpdatePricingRule:
    """Test pricing rule updates."""

    @pytest.mark.asyncio
    async def test_update_rule_discount_value(self, pricing_engine, tenant_id):
        """Test updating discount value."""
        rule_id = "rule-123"
        updates = PricingRuleUpdateRequest(discount_value=Decimal("15"))

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            mock_db_rule = MagicMock()
            mock_db_rule.rule_id = rule_id
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_db_rule
            mock_db.execute.return_value = mock_result

            rule = await pricing_engine.update_pricing_rule(rule_id, updates, tenant_id)

            assert rule is not None

    @pytest.mark.asyncio
    async def test_update_nonexistent_rule(self, pricing_engine, tenant_id):
        """Test updating non-existent rule."""
        rule_id = "nonexistent"
        updates = PricingRuleUpdateRequest(name="New Name")

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            with pytest.raises(PricingError):
                await pricing_engine.update_pricing_rule(rule_id, updates, tenant_id)


class TestDeactivatePricingRule:
    """Test pricing rule deactivation."""

    @pytest.mark.asyncio
    async def test_deactivate_active_rule(self, pricing_engine, tenant_id):
        """Test deactivating an active rule."""
        rule_id = "rule-123"

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            mock_db_rule = MagicMock()
            mock_db_rule.rule_id = rule_id
            mock_db_rule.is_active = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_db_rule
            mock_db.execute.return_value = mock_result

            rule = await pricing_engine.deactivate_pricing_rule(rule_id, tenant_id)

            assert mock_db_rule.is_active is False


class TestPriceCalculation:
    """Test price calculation logic."""

    @pytest.mark.asyncio
    async def test_calculate_price_basic(self, pricing_engine, tenant_id, product_id, customer_id):
        """Test basic price calculation."""
        request = PriceCalculationRequest(
            product_id=product_id,
            customer_id=customer_id,
            quantity=1,
        )

        with patch.object(pricing_engine.product_service, "get_product") as mock_get:
            mock_product = MagicMock()
            mock_product.product_id = product_id
            mock_product.base_price = Decimal("100.00")
            mock_product.category = "electronics"
            mock_get.return_value = mock_product

            with patch.object(pricing_engine, "_get_applicable_rules", return_value=[]):
                result = await pricing_engine.calculate_price(request, tenant_id)

                assert result.base_price == Decimal("100.00")
                assert result.final_price == Decimal("100.00")
                assert result.total_discount_amount == Decimal("0")

    @pytest.mark.asyncio
    async def test_activate_rule(self, pricing_engine, tenant_id):
        """Test activating a pricing rule."""
        rule_id = "rule-123"

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            mock_db_rule = MagicMock()
            mock_db_rule.is_active = False
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_db_rule
            mock_db.execute.return_value = mock_result

            success = await pricing_engine.activate_rule(rule_id, tenant_id)

            assert success is True
            assert mock_db_rule.is_active is True

    @pytest.mark.asyncio
    async def test_deactivate_rule(self, pricing_engine, tenant_id):
        """Test deactivating a pricing rule."""
        rule_id = "rule-123"

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            mock_db_rule = MagicMock()
            mock_db_rule.is_active = True
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_db_rule
            mock_db.execute.return_value = mock_result

            success = await pricing_engine.deactivate_rule(rule_id, tenant_id)

            assert success is True
            assert mock_db_rule.is_active is False

    @pytest.mark.asyncio
    async def test_get_rule_usage_stats(self, pricing_engine, tenant_id):
        """Test getting rule usage statistics."""
        rule_id = "rule-123"

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            mock_db_rule = MagicMock()
            mock_db_rule.rule_id = rule_id
            mock_db_rule.name = "Test Rule"
            mock_db_rule.current_uses = 10
            mock_db_rule.max_uses = 100
            mock_db_rule.is_active = True

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_db_rule
            mock_result.scalar.return_value = 10
            mock_db.execute.return_value = mock_result

            stats = await pricing_engine.get_rule_usage_stats(rule_id, tenant_id)

            assert stats["rule_id"] == rule_id
            assert stats["current_uses"] == 10
            assert stats["max_uses"] == 100

    @pytest.mark.asyncio
    async def test_reset_rule_usage(self, pricing_engine, tenant_id):
        """Test resetting rule usage counter."""
        rule_id = "rule-123"

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            mock_db_rule = MagicMock()
            mock_db_rule.current_uses = 50
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_db_rule
            mock_db.execute.return_value = mock_result

            success = await pricing_engine.reset_rule_usage(rule_id, tenant_id)

            assert success is True
            assert mock_db_rule.current_uses == 0

    @pytest.mark.asyncio
    async def test_detect_rule_conflicts(self, pricing_engine, tenant_id):
        """Test detecting conflicts between pricing rules."""
        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result

            conflicts = await pricing_engine.detect_rule_conflicts(tenant_id)

            assert isinstance(conflicts, list)

    @pytest.mark.asyncio
    async def test_bulk_activate_rules(self, pricing_engine, tenant_id):
        """Test bulk activating rules."""
        rule_ids = ["rule-1", "rule-2", "rule-3"]

        with patch.object(pricing_engine, "activate_rule", return_value=True):
            results = await pricing_engine.bulk_activate_rules(rule_ids, tenant_id)

            assert results["activated"] == 3
            assert results["failed"] == 0

    @pytest.mark.asyncio
    async def test_bulk_deactivate_rules(self, pricing_engine, tenant_id):
        """Test bulk deactivating rules."""
        rule_ids = ["rule-1", "rule-2", "rule-3"]

        with patch.object(pricing_engine, "deactivate_rule", return_value=True):
            results = await pricing_engine.bulk_deactivate_rules(rule_ids, tenant_id)

            assert results["deactivated"] == 3
            assert results["failed"] == 0
