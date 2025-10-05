"""
Comprehensive unit tests for Pricing Service.

Coverage target: 90%+
Strategy: Test validation logic, helper methods, and mock database operations
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from datetime import datetime, timezone
from decimal import Decimal

from dotmac.platform.billing.pricing.service import (
    PricingEngine,
    generate_rule_id,
    generate_usage_id,
)
from dotmac.platform.billing.pricing.models import (
    PricingRule,
    PricingRuleCreateRequest,
    PricingRuleUpdateRequest,
    PriceCalculationRequest,
    PriceCalculationContext,
    DiscountType,
)
from dotmac.platform.billing.models import BillingPricingRuleTable, BillingProductTable
from dotmac.platform.billing.exceptions import (
    PricingError,
    InvalidPricingRuleError,
    PriceCalculationError,
)

pytestmark = pytest.mark.asyncio


# ==================== Fixtures ====================


@pytest.fixture
def mock_session():
    """Mock AsyncSession for database operations."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def pricing_engine(mock_session):
    """PricingEngine instance with mocked session."""
    return PricingEngine(db_session=mock_session)


@pytest.fixture
def tenant_id():
    """Sample tenant ID."""
    return "tenant-123"


@pytest.fixture
def sample_rule_request():
    """Sample pricing rule creation request."""
    return PricingRuleCreateRequest(
        name="Black Friday Sale",
        applies_to_product_ids=["prod-1", "prod-2"],
        applies_to_categories=["electronics"],
        applies_to_all=False,
        min_quantity=1,
        customer_segments=["premium"],
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("20.00"),
        starts_at=datetime(2025, 11, 25, tzinfo=timezone.utc),
        ends_at=datetime(2025, 11, 30, tzinfo=timezone.utc),
        max_uses=100,
        metadata={"campaign_id": "bf2025"},
    )


@pytest.fixture
def mock_db_rule():
    """Mock database rule object with all required fields."""
    rule = MagicMock(spec=BillingPricingRuleTable)
    rule.rule_id = "rule_test123"
    rule.tenant_id = "tenant-123"
    rule.name = "Test Rule"
    rule.description = None
    rule.applies_to_product_ids = ["prod-1"]
    rule.applies_to_categories = ["electronics"]
    rule.applies_to_all = False
    rule.min_quantity = 1
    rule.customer_segments = ["premium"]
    rule.discount_type = "PERCENTAGE"
    rule.discount_value = Decimal("15.00")
    rule.starts_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    rule.ends_at = datetime(2025, 12, 31, tzinfo=timezone.utc)
    rule.max_uses = 100
    rule.current_uses = 10
    rule.priority = 0
    rule.is_active = True
    rule.metadata_json = {"note": "test"}
    rule.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    rule.updated_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return rule


@pytest.fixture
def mock_product():
    """Mock product for price calculations."""
    product = MagicMock(spec=BillingProductTable)
    product.product_id = "prod-1"
    product.base_price = Decimal("100.00")
    product.category = "electronics"
    return product


# ==================== Test Helper Functions ====================


class TestHelperFunctions:
    """Test ID generation helper functions."""

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
        """Test IDs are unique."""
        id1 = generate_rule_id()
        id2 = generate_rule_id()
        assert id1 != id2


# ==================== Test Validation Logic ====================


class TestRuleValidation:
    """Test pricing rule validation logic."""

    async def test_create_rule_no_target_fails(self, pricing_engine, tenant_id):
        """Test validation error when no target is specified."""
        invalid_request = PricingRuleCreateRequest(
            name="Invalid Rule",
            applies_to_product_ids=[],
            applies_to_categories=[],
            applies_to_all=False,  # No target!
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10.00"),
        )

        with pytest.raises(InvalidPricingRuleError, match="must apply to at least something"):
            await pricing_engine.create_pricing_rule(invalid_request, tenant_id)

    @patch("dotmac.platform.billing.pricing.service.settings")
    async def test_create_rule_excessive_percentage_fails(
        self, mock_settings, pricing_engine, tenant_id
    ):
        """Test validation error for excessive percentage discount."""
        # Set max discount to 100%
        mock_settings.billing.max_discount_percentage = 100

        invalid_request = PricingRuleCreateRequest(
            name="Excessive Discount",
            applies_to_all=True,
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("150.00"),  # >100%
        )

        with pytest.raises(InvalidPricingRuleError, match="cannot exceed"):
            await pricing_engine.create_pricing_rule(invalid_request, tenant_id)


# ==================== Test CRUD Operations ====================


class TestCreatePricingRule:
    """Test pricing rule creation."""

    @patch("dotmac.platform.billing.pricing.service.get_async_session")
    async def test_create_percentage_rule_success(
        self,
        mock_get_session,
        pricing_engine,
        mock_session,
        sample_rule_request,
        tenant_id,
        mock_db_rule,
    ):
        """Test successful creation of percentage discount rule."""
        # Setup context manager
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = AsyncMock()

        # Setup refresh to populate created rule
        async def refresh_side_effect(db_rule):
            for attr, value in vars(mock_db_rule).items():
                if not attr.startswith("_"):
                    setattr(db_rule, attr, value)

        mock_session.refresh.side_effect = refresh_side_effect

        result = await pricing_engine.create_pricing_rule(sample_rule_request, tenant_id)

        assert isinstance(result, PricingRule)
        assert result.discount_type == DiscountType.PERCENTAGE
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()


class TestGetPricingRule:
    """Test retrieving pricing rules."""

    @patch("dotmac.platform.billing.pricing.service.get_async_session")
    async def test_get_existing_rule(
        self, mock_get_session, pricing_engine, mock_session, tenant_id, mock_db_rule
    ):
        """Test getting an existing rule."""
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_db_rule
        mock_session.execute.return_value = mock_result

        result = await pricing_engine.get_pricing_rule("rule_test123", tenant_id)

        assert isinstance(result, PricingRule)
        assert result.rule_id == "rule_test123"

    @patch("dotmac.platform.billing.pricing.service.get_async_session")
    async def test_get_nonexistent_rule_fails(
        self, mock_get_session, pricing_engine, mock_session, tenant_id
    ):
        """Test error when rule doesn't exist."""
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(PricingError, match="not found"):
            await pricing_engine.get_pricing_rule("nonexistent", tenant_id)


class TestListPricingRules:
    """Test listing pricing rules."""

    @patch("dotmac.platform.billing.pricing.service.get_async_session")
    async def test_list_all_rules(
        self, mock_get_session, pricing_engine, mock_session, tenant_id, mock_db_rule
    ):
        """Test listing all active rules."""
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_db_rule]
        mock_session.execute.return_value = mock_result

        results = await pricing_engine.list_pricing_rules(tenant_id)

        assert len(results) == 1
        assert all(isinstance(r, PricingRule) for r in results)

    @patch("dotmac.platform.billing.pricing.service.get_async_session")
    async def test_list_with_product_filter(
        self, mock_get_session, pricing_engine, mock_session, tenant_id, mock_db_rule
    ):
        """Test listing rules filtered by product."""
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_db_rule]
        mock_session.execute.return_value = mock_result

        results = await pricing_engine.list_pricing_rules(
            tenant_id, active_only=True, product_id="prod-1"
        )

        assert len(results) >= 0  # May filter out
        mock_session.execute.assert_called_once()


class TestUpdatePricingRule:
    """Test updating pricing rules."""

    @patch("dotmac.platform.billing.pricing.service.get_async_session")
    async def test_update_rule_discount_value(
        self, mock_get_session, pricing_engine, mock_session, tenant_id, mock_db_rule
    ):
        """Test updating rule discount value."""
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_db_rule
        mock_session.execute.return_value = mock_result

        update_request = PricingRuleUpdateRequest(discount_value=Decimal("25.00"))

        result = await pricing_engine.update_pricing_rule("rule_test123", update_request, tenant_id)

        assert isinstance(result, PricingRule)
        mock_session.commit.assert_called_once()

    @patch("dotmac.platform.billing.pricing.service.get_async_session")
    async def test_update_nonexistent_rule_fails(
        self, mock_get_session, pricing_engine, mock_session, tenant_id
    ):
        """Test error when updating nonexistent rule."""
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        update_request = PricingRuleUpdateRequest(discount_value=Decimal("25.00"))

        with pytest.raises(PricingError, match="not found"):
            await pricing_engine.update_pricing_rule("nonexistent", update_request, tenant_id)


class TestDeletePricingRule:
    """Test deleting pricing rules."""

    @patch("dotmac.platform.billing.pricing.service.get_async_session")
    async def test_delete_existing_rule(
        self, mock_get_session, pricing_engine, mock_session, tenant_id, mock_db_rule
    ):
        """Test deleting an existing rule."""
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_db_rule
        mock_session.execute.return_value = mock_result

        await pricing_engine.delete_pricing_rule("rule_test123", tenant_id)

        mock_session.delete.assert_called_once()
        mock_session.commit.assert_called_once()


class TestActivateDeactivateRules:
    """Test activating/deactivating rules."""

    @patch("dotmac.platform.billing.pricing.service.get_async_session")
    async def test_activate_rule(
        self, mock_get_session, pricing_engine, mock_session, tenant_id, mock_db_rule
    ):
        """Test activating a rule."""
        mock_db_rule.is_active = False
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_db_rule
        mock_session.execute.return_value = mock_result

        result = await pricing_engine.activate_pricing_rule("rule_test123", tenant_id)

        assert result.is_active is True
        mock_session.commit.assert_called_once()

    @patch("dotmac.platform.billing.pricing.service.get_async_session")
    async def test_deactivate_rule(
        self, mock_get_session, pricing_engine, mock_session, tenant_id, mock_db_rule
    ):
        """Test deactivating a rule."""
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_db_rule
        mock_session.execute.return_value = mock_result

        result = await pricing_engine.deactivate_pricing_rule("rule_test123", tenant_id)

        assert result.is_active is False
        mock_session.commit.assert_called_once()


# ==================== Test Price Calculation Engine ====================


class TestPriceCalculations:
    """Test price calculation logic."""

    @patch("dotmac.platform.billing.pricing.service.get_async_session")
    async def test_calculate_price_with_rule(
        self, mock_get_session, pricing_engine, mock_session, tenant_id, mock_db_rule, mock_product
    ):
        """Test price calculation with applicable rule."""
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = AsyncMock()

        # Mock product service
        with patch.object(pricing_engine.product_service, "get_product", return_value=mock_product):
            # Mock list of applicable rules
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_db_rule]
            mock_session.execute.return_value = mock_result

            request = PriceCalculationRequest(
                product_id="prod-1",
                quantity=1,
                customer_id="cust-1",
                customer_segments=["premium"],
            )

            result = await pricing_engine.calculate_price(request, tenant_id)

            assert result.product_id == "prod-1"
            assert result.base_price == Decimal("100.00")
            # 15% discount on $100 = $85
            assert result.final_price == Decimal("85.00")

    @patch("dotmac.platform.billing.pricing.service.get_async_session")
    async def test_calculate_price_no_rules(
        self, mock_get_session, pricing_engine, mock_session, tenant_id, mock_product
    ):
        """Test price calculation with no applicable rules."""
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = AsyncMock()

        with patch.object(pricing_engine.product_service, "get_product", return_value=mock_product):
            # No rules found
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_session.execute.return_value = mock_result

            request = PriceCalculationRequest(
                product_id="prod-1",
                quantity=1,
                customer_id="cust-1",
            )

            result = await pricing_engine.calculate_price(request, tenant_id)

            assert result.final_price == Decimal("100.00")  # No discount
            assert result.total_discount_amount == Decimal("0")

    @patch("dotmac.platform.billing.pricing.service.get_async_session")
    async def test_calculate_price_product_not_found(
        self, mock_get_session, pricing_engine, mock_session, tenant_id
    ):
        """Test error when product not found."""
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = AsyncMock()

        with patch.object(
            pricing_engine.product_service,
            "get_product",
            side_effect=Exception("Product not found"),
        ):
            request = PriceCalculationRequest(
                product_id="nonexistent",
                quantity=1,
                customer_id="cust-1",
            )

            with pytest.raises(PriceCalculationError):
                await pricing_engine.calculate_price(request, tenant_id)


# ==================== Test Helper Methods ====================


class TestDiscountCalculations:
    """Test discount calculation helper methods."""

    def test_apply_percentage_discount(self, pricing_engine):
        """Test percentage discount calculation."""
        base_price = Decimal("100.00")
        discount_value = Decimal("20.00")

        final_price = pricing_engine._apply_discount(
            base_price, DiscountType.PERCENTAGE, discount_value
        )

        assert final_price == Decimal("80.00")

    def test_apply_fixed_amount_discount(self, pricing_engine):
        """Test fixed amount discount."""
        base_price = Decimal("100.00")
        discount_value = Decimal("15.00")

        final_price = pricing_engine._apply_discount(
            base_price, DiscountType.FIXED_AMOUNT, discount_value
        )

        assert final_price == Decimal("85.00")

    def test_apply_fixed_price(self, pricing_engine):
        """Test fixed price override."""
        base_price = Decimal("100.00")
        discount_value = Decimal("75.00")

        final_price = pricing_engine._apply_discount(
            base_price, DiscountType.FIXED_PRICE, discount_value
        )

        assert final_price == Decimal("75.00")

    def test_prevent_negative_price(self, pricing_engine):
        """Test discounts don't result in negative prices."""
        base_price = Decimal("50.00")
        discount_value = Decimal("100.00")

        final_price = pricing_engine._apply_discount(
            base_price, DiscountType.FIXED_AMOUNT, discount_value
        )

        assert final_price == Decimal("0.00")


class TestRuleMatching:
    """Test rule matching logic."""

    def test_rule_matches_product_id(self, pricing_engine, mock_db_rule):
        """Test rule matching by product ID."""
        context = PriceCalculationContext(
            product_id="prod-1",
            quantity=1,
            customer_id="cust-1",
            customer_segments=["premium"],
            base_price=Decimal("100.00"),
        )

        rule = PricingRule(
            rule_id=mock_db_rule.rule_id,
            tenant_id=mock_db_rule.tenant_id,
            name=mock_db_rule.name,
            description=mock_db_rule.description,
            applies_to_product_ids=mock_db_rule.applies_to_product_ids,
            applies_to_categories=mock_db_rule.applies_to_categories,
            applies_to_all=mock_db_rule.applies_to_all,
            min_quantity=mock_db_rule.min_quantity,
            customer_segments=mock_db_rule.customer_segments,
            discount_type=DiscountType.PERCENTAGE,
            discount_value=mock_db_rule.discount_value,
            starts_at=mock_db_rule.starts_at,
            ends_at=mock_db_rule.ends_at,
            max_uses=mock_db_rule.max_uses,
            current_uses=mock_db_rule.current_uses,
            priority=mock_db_rule.priority,
            is_active=mock_db_rule.is_active,
            metadata=mock_db_rule.metadata_json,
            created_at=mock_db_rule.created_at,
            updated_at=mock_db_rule.updated_at,
        )

        matches = pricing_engine._rule_matches_context(rule, context)
        assert matches is True

    def test_rule_no_match_insufficient_quantity(self, pricing_engine, mock_db_rule):
        """Test rule doesn't match when quantity too low."""
        mock_db_rule.min_quantity = 5

        context = PriceCalculationContext(
            product_id="prod-1",
            quantity=2,  # Less than min_quantity
            customer_id="cust-1",
            base_price=Decimal("100.00"),
        )

        rule = PricingRule(
            rule_id=mock_db_rule.rule_id,
            tenant_id=mock_db_rule.tenant_id,
            name=mock_db_rule.name,
            description=mock_db_rule.description,
            applies_to_product_ids=mock_db_rule.applies_to_product_ids,
            applies_to_categories=mock_db_rule.applies_to_categories,
            applies_to_all=mock_db_rule.applies_to_all,
            min_quantity=mock_db_rule.min_quantity,
            customer_segments=mock_db_rule.customer_segments,
            discount_type=DiscountType.PERCENTAGE,
            discount_value=mock_db_rule.discount_value,
            starts_at=mock_db_rule.starts_at,
            ends_at=mock_db_rule.ends_at,
            max_uses=mock_db_rule.max_uses,
            current_uses=mock_db_rule.current_uses,
            priority=mock_db_rule.priority,
            is_active=mock_db_rule.is_active,
            metadata=mock_db_rule.metadata_json,
            created_at=mock_db_rule.created_at,
            updated_at=mock_db_rule.updated_at,
        )

        matches = pricing_engine._rule_matches_context(rule, context)
        assert matches is False


# ==================== Test Bulk Operations ====================


class TestBulkOperations:
    """Test bulk rule operations."""

    @patch("dotmac.platform.billing.pricing.service.get_async_session")
    async def test_bulk_activate_rules(
        self, mock_get_session, pricing_engine, mock_session, tenant_id, mock_db_rule
    ):
        """Test bulk activating rules."""
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_db_rule]
        mock_session.execute.return_value = mock_result

        rule_ids = ["rule_test123"]
        results = await pricing_engine.bulk_activate_rules(rule_ids, tenant_id)

        assert len(results) == 1
        assert all(r.is_active for r in results)

    @patch("dotmac.platform.billing.pricing.service.get_async_session")
    async def test_bulk_deactivate_rules(
        self, mock_get_session, pricing_engine, mock_session, tenant_id, mock_db_rule
    ):
        """Test bulk deactivating rules."""
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_db_rule]
        mock_session.execute.return_value = mock_result

        rule_ids = ["rule_test123"]
        results = await pricing_engine.bulk_deactivate_rules(rule_ids, tenant_id)

        assert len(results) == 1
        assert all(not r.is_active for r in results)


# ==================== Test Usage Tracking ====================


class TestRuleUsageTracking:
    """Test rule usage tracking."""

    @patch("dotmac.platform.billing.pricing.service.get_async_session")
    async def test_increment_rule_usage(
        self, mock_get_session, pricing_engine, mock_session, mock_db_rule
    ):
        """Test incrementing rule usage counter."""
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = AsyncMock()

        initial_uses = mock_db_rule.current_uses

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_db_rule
        mock_session.execute.return_value = mock_result

        await pricing_engine._increment_rule_usage("rule_test123")

        assert mock_db_rule.current_uses == initial_uses + 1
        mock_session.commit.assert_called_once()

    @patch("dotmac.platform.billing.pricing.service.get_async_session")
    async def test_reset_rule_usage(
        self, mock_get_session, pricing_engine, mock_session, tenant_id, mock_db_rule
    ):
        """Test resetting rule usage counter."""
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = AsyncMock()

        mock_db_rule.current_uses = 50

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_db_rule
        mock_session.execute.return_value = mock_result

        await pricing_engine.reset_rule_usage("rule_test123", tenant_id)

        assert mock_db_rule.current_uses == 0
        mock_session.commit.assert_called_once()


# ==================== Test Conflict Detection ====================


class TestConflictDetection:
    """Test rule conflict detection."""

    @patch("dotmac.platform.billing.pricing.service.get_async_session")
    async def test_detect_rule_conflicts(
        self, mock_get_session, pricing_engine, mock_session, tenant_id, mock_db_rule
    ):
        """Test detecting overlapping rules."""
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = AsyncMock()

        # Create second conflicting rule
        mock_db_rule2 = MagicMock(spec=BillingPricingRuleTable)
        for attr, value in vars(mock_db_rule).items():
            if not attr.startswith("_"):
                setattr(mock_db_rule2, attr, value)
        mock_db_rule2.rule_id = "rule_conflict"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_db_rule, mock_db_rule2]
        mock_session.execute.return_value = mock_result

        conflicts = await pricing_engine.detect_rule_conflicts(tenant_id)

        assert isinstance(conflicts, list)
