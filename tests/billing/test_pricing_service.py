"""Comprehensive tests for pricing engine service.

Tests rule management, price calculation, discount application, and usage tracking."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.billing.exceptions import InvalidPricingRuleError, PricingError
from dotmac.platform.billing.models import BillingPricingRuleTable
from dotmac.platform.billing.pricing.models import (
    DiscountType,
    PriceCalculationRequest,
    PricingRule,
    PricingRuleCreateRequest,
    PricingRuleUpdateRequest,
)
from dotmac.platform.billing.pricing.service import (
    PricingEngine,
    generate_rule_id,
    generate_usage_id,
)
from dotmac.platform.billing.money_utils import money_handler
from dotmac.platform.settings import settings


@pytest.fixture
def mock_db_session() -> AsyncSession:
    """Provide a mock database session for pricing engine tests."""
    session = MagicMock(spec=AsyncSession)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    # Configure execute to return empty results by default
    mock_result = MagicMock()
    mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    session.execute = AsyncMock(return_value=mock_result)

    return session


class TestIDGenerators:
    """Test ID generator functions."""

    def test_generate_rule_id(self) -> None:
        """Test rule ID generation."""
        rule_id = generate_rule_id()
        assert rule_id.startswith("rule_")
        assert len(rule_id) == 17  # "rule_" + 12 hex chars

    def test_generate_rule_id_unique(self) -> None:
        """Test rule IDs are unique."""
        ids = {generate_rule_id() for _ in range(100)}
        assert len(ids) == 100

    def test_generate_usage_id(self) -> None:
        """Test usage ID generation."""
        usage_id = generate_usage_id()
        assert usage_id.startswith("usage_")
        assert len(usage_id) == 18  # "usage_" + 12 hex chars

    def test_generate_usage_id_unique(self) -> None:
        """Test usage IDs are unique."""
        ids = {generate_usage_id() for _ in range(100)}
        assert len(ids) == 100


class TestPricingEngineInitialization:
    """Test pricing engine initialization."""

    def test_pricing_engine_initialization(self, mock_db_session: AsyncSession) -> None:
        """Test pricing engine is initialized correctly."""
        engine = PricingEngine(mock_db_session)
        assert engine.product_service is not None


@pytest.mark.asyncio
class TestCreatePricingRule:
    """Test creating pricing rules."""

    async def test_create_percentage_rule_success(self, mock_db_session: AsyncSession) -> None:
        """Test creating a percentage discount rule."""
        engine = PricingEngine(mock_db_session)

        rule_data = PricingRuleCreateRequest(
            name="Summer Sale",
            applies_to_categories=["electronics"],
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("20"),
        )

        mock_db_rule = MagicMock(spec=BillingPricingRuleTable)
        mock_db_rule.rule_id = "rule_123"
        mock_db_rule.tenant_id = "tenant_123"
        mock_db_rule.name = "Summer Sale"
        mock_db_rule.applies_to_product_ids = []
        mock_db_rule.applies_to_categories = ["electronics"]
        mock_db_rule.applies_to_all = False
        mock_db_rule.min_quantity = None
        mock_db_rule.customer_segments = []
        mock_db_rule.discount_type = "percentage"
        mock_db_rule.discount_value = Decimal("20")
        mock_db_rule.starts_at = None
        mock_db_rule.ends_at = None
        mock_db_rule.max_uses = None
        mock_db_rule.current_uses = 0
        mock_db_rule.is_active = True
        mock_db_rule.metadata_json = {}
        mock_db_rule.priority = 0
        mock_db_rule.created_at = datetime.now(UTC)
        mock_db_rule.updated_at = datetime.now(UTC)

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # Mock refresh to set attributes
            async def mock_refresh_side_effect(obj: PricingRule) -> None:
                for key, value in vars(mock_db_rule).items():
                    if not key.startswith("_"):
                        setattr(obj, key, value)

            mock_session.refresh.side_effect = mock_refresh_side_effect

            result = await engine.create_pricing_rule(rule_data, "tenant_123")

        assert result.name == "Summer Sale"
        assert result.discount_type == DiscountType.PERCENTAGE
        assert result.discount_value == Decimal("20")
        assert result.applies_to_categories == ["electronics"]

    async def test_create_rule_with_no_applicability_fails(
        self, mock_db_session: AsyncSession
    ) -> None:
        """Test that rules without applicability fail."""
        engine = PricingEngine(mock_db_session)

        rule_data = PricingRuleCreateRequest(
            name="Invalid Rule",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10"),
            # No applies_to_* fields set
        )

        with pytest.raises(InvalidPricingRuleError) as exc_info:
            await engine.create_pricing_rule(rule_data, "tenant_123")

        assert "must apply to at least something" in str(exc_info.value)

    async def test_create_rule_excessive_percentage_discount_fails(
        self, mock_db_session: AsyncSession
    ) -> None:
        """Test that percentage discounts over max fail."""
        engine = PricingEngine(mock_db_session)

        rule_data = PricingRuleCreateRequest(
            name="Too Much Discount",
            applies_to_all=True,
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("150"),  # Over 100%
        )

        with patch("dotmac.platform.billing.pricing.service.settings") as mock_settings:
            mock_settings.billing.max_discount_percentage = 100

            with pytest.raises(InvalidPricingRuleError) as exc_info:
                await engine.create_pricing_rule(rule_data, "tenant_123")

            assert "cannot exceed" in str(exc_info.value)

    async def test_create_fixed_amount_rule(self, mock_db_session: AsyncSession) -> None:
        """Test creating a fixed amount discount rule."""
        engine = PricingEngine(mock_db_session)

        rule_data = PricingRuleCreateRequest(
            name="$10 Off",
            applies_to_product_ids=["prod_123"],
            discount_type=DiscountType.FIXED_AMOUNT,
            discount_value=Decimal("10.00"),
        )

        mock_db_rule = MagicMock(spec=BillingPricingRuleTable)
        mock_db_rule.rule_id = "rule_456"
        mock_db_rule.tenant_id = "tenant_123"
        mock_db_rule.name = "$10 Off"
        mock_db_rule.applies_to_product_ids = ["prod_123"]
        mock_db_rule.applies_to_categories = []
        mock_db_rule.applies_to_all = False
        mock_db_rule.min_quantity = None
        mock_db_rule.customer_segments = []
        mock_db_rule.discount_type = "fixed_amount"
        mock_db_rule.discount_value = Decimal("10.00")
        mock_db_rule.starts_at = None
        mock_db_rule.ends_at = None
        mock_db_rule.max_uses = None
        mock_db_rule.current_uses = 0
        mock_db_rule.is_active = True
        mock_db_rule.metadata_json = {}
        mock_db_rule.priority = 0
        mock_db_rule.created_at = datetime.now(UTC)
        mock_db_rule.updated_at = datetime.now(UTC)

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            async def mock_refresh_side_effect(obj: PricingRule) -> None:
                for key, value in vars(mock_db_rule).items():
                    if not key.startswith("_"):
                        setattr(obj, key, value)

            mock_session.refresh.side_effect = mock_refresh_side_effect

            result = await engine.create_pricing_rule(rule_data, "tenant_123")

        assert result.discount_type == DiscountType.FIXED_AMOUNT
        assert result.discount_value == Decimal("10.00")


@pytest.mark.asyncio
class TestGetPricingRule:
    """Test retrieving pricing rules."""

    async def test_get_pricing_rule_success(self, mock_db_session: AsyncSession) -> None:
        """Test getting a pricing rule by ID."""
        engine = PricingEngine(mock_db_session)

        mock_db_rule = MagicMock(spec=BillingPricingRuleTable)
        mock_db_rule.rule_id = "rule_123"
        mock_db_rule.tenant_id = "tenant_123"
        mock_db_rule.name = "Test Rule"
        mock_db_rule.applies_to_product_ids = []
        mock_db_rule.applies_to_categories = []
        mock_db_rule.applies_to_all = True
        mock_db_rule.min_quantity = None
        mock_db_rule.customer_segments = []
        mock_db_rule.discount_type = "percentage"
        mock_db_rule.discount_value = Decimal("10")
        mock_db_rule.starts_at = None
        mock_db_rule.ends_at = None
        mock_db_rule.max_uses = None
        mock_db_rule.current_uses = 0
        mock_db_rule.is_active = True
        mock_db_rule.metadata_json = {}
        mock_db_rule.priority = 0
        mock_db_rule.created_at = datetime.now(UTC)
        mock_db_rule.updated_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_db_rule

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            result = await engine.get_pricing_rule("rule_123", "tenant_123")

        assert result.rule_id == "rule_123"
        assert result.name == "Test Rule"

    async def test_get_pricing_rule_not_found(self, mock_db_session: AsyncSession) -> None:
        """Test getting non-existent rule raises error."""
        engine = PricingEngine(mock_db_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with pytest.raises(PricingError) as exc_info:
                await engine.get_pricing_rule("nonexistent", "tenant_123")

        assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
class TestListPricingRules:
    """Test listing pricing rules with filters."""

    async def test_list_all_active_rules(self, mock_db_session: AsyncSession) -> None:
        """Test listing all active rules."""
        engine = PricingEngine(mock_db_session)

        mock_db_rule1 = self._create_mock_rule("rule_1", "Rule 1", True)
        mock_db_rule2 = self._create_mock_rule("rule_2", "Rule 2", True)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_db_rule1, mock_db_rule2]

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            rules = await engine.list_pricing_rules("tenant_123", active_only=True)

        assert len(rules) == 2
        assert rules[0].rule_id == "rule_1"
        assert rules[1].rule_id == "rule_2"

    async def test_list_rules_filtered_by_product(self, mock_db_session: AsyncSession) -> None:
        """Test listing rules filtered by product ID."""
        engine = PricingEngine(mock_db_session)

        mock_db_rule = self._create_mock_rule("rule_123", "Product Rule", True)
        mock_db_rule.applies_to_product_ids = ["prod_123"]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_db_rule]

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            rules = await engine.list_pricing_rules(
                "tenant_123", active_only=True, product_id="prod_123"
            )

        assert len(rules) == 1
        assert rules[0].applies_to_product_ids == ["prod_123"]

    async def test_list_rules_filtered_by_category(self, mock_db_session: AsyncSession) -> None:
        """Test listing rules filtered by category."""
        engine = PricingEngine(mock_db_session)

        mock_db_rule = self._create_mock_rule("rule_123", "Category Rule", True)
        mock_db_rule.applies_to_categories = ["electronics"]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_db_rule]

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            rules = await engine.list_pricing_rules(
                "tenant_123", active_only=True, category="electronics"
            )

        assert len(rules) == 1
        assert rules[0].applies_to_categories == ["electronics"]

    def _create_mock_rule(self, rule_id: str, name: str, is_active: bool) -> MagicMock:
        """Helper to create mock rule."""
        mock_rule = MagicMock(spec=BillingPricingRuleTable)
        mock_rule.rule_id = rule_id
        mock_rule.tenant_id = "tenant_123"
        mock_rule.name = name
        mock_rule.applies_to_product_ids = []
        mock_rule.applies_to_categories = []
        mock_rule.applies_to_all = False
        mock_rule.min_quantity = None
        mock_rule.customer_segments = []
        mock_rule.discount_type = "percentage"
        mock_rule.discount_value = Decimal("10")
        mock_rule.starts_at = None
        mock_rule.ends_at = None
        mock_rule.max_uses = None
        mock_rule.current_uses = 0
        mock_rule.is_active = is_active
        mock_rule.metadata_json = {}
        mock_rule.priority = 0
        mock_rule.created_at = datetime.now(UTC)
        mock_rule.updated_at = datetime.now(UTC)
        return mock_rule


@pytest.mark.asyncio
class TestUpdatePricingRule:
    """Test updating pricing rules."""

    async def test_update_rule_name(self, mock_db_session: AsyncSession) -> None:
        """Test updating rule name."""
        engine = PricingEngine(mock_db_session)

        mock_db_rule = MagicMock(spec=BillingPricingRuleTable)
        mock_db_rule.rule_id = "rule_123"
        mock_db_rule.tenant_id = "tenant_123"
        mock_db_rule.name = "Old Name"
        mock_db_rule.applies_to_product_ids = []
        mock_db_rule.applies_to_categories = []
        mock_db_rule.applies_to_all = True
        mock_db_rule.min_quantity = None
        mock_db_rule.customer_segments = []
        mock_db_rule.discount_type = "percentage"
        mock_db_rule.discount_value = Decimal("10")
        mock_db_rule.starts_at = None
        mock_db_rule.ends_at = None
        mock_db_rule.max_uses = None
        mock_db_rule.current_uses = 0
        mock_db_rule.is_active = True
        mock_db_rule.metadata_json = {}
        mock_db_rule.priority = 0
        mock_db_rule.created_at = datetime.now(UTC)
        mock_db_rule.updated_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_db_rule

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        updates = PricingRuleUpdateRequest(name="New Name")

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # Update the name after commit
            async def mock_commit_side_effect() -> None:
                mock_db_rule.name = "New Name"

            mock_session.commit.side_effect = mock_commit_side_effect

            result = await engine.update_pricing_rule("rule_123", updates, "tenant_123")

        assert result.name == "New Name"

    async def test_update_rule_not_found(self, mock_db_session: AsyncSession) -> None:
        """Test updating non-existent rule fails."""
        engine = PricingEngine(mock_db_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        updates = PricingRuleUpdateRequest(name="New Name")

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with pytest.raises(PricingError) as exc_info:
                await engine.update_pricing_rule("nonexistent", updates, "tenant_123")

        assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
class TestDeactivatePricingRule:
    """Test deactivating pricing rules."""

    async def test_deactivate_rule_success(self, mock_db_session: AsyncSession) -> None:
        """Test deactivating a pricing rule."""
        engine = PricingEngine(mock_db_session)

        mock_db_rule = MagicMock(spec=BillingPricingRuleTable)
        mock_db_rule.rule_id = "rule_123"
        mock_db_rule.tenant_id = "tenant_123"
        mock_db_rule.name = "Test Rule"
        mock_db_rule.applies_to_product_ids = []
        mock_db_rule.applies_to_categories = []
        mock_db_rule.applies_to_all = True
        mock_db_rule.min_quantity = None
        mock_db_rule.customer_segments = []
        mock_db_rule.discount_type = "percentage"
        mock_db_rule.discount_value = Decimal("10")
        mock_db_rule.starts_at = None
        mock_db_rule.ends_at = None
        mock_db_rule.max_uses = None
        mock_db_rule.current_uses = 0
        mock_db_rule.is_active = True
        mock_db_rule.metadata_json = {}
        mock_db_rule.priority = 0
        mock_db_rule.created_at = datetime.now(UTC)
        mock_db_rule.updated_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_db_rule

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            result = await engine.deactivate_pricing_rule("rule_123", "tenant_123")

        assert result.is_active is False

    async def test_deactivate_rule_not_found(self, mock_db_session: AsyncSession) -> None:
        """Test deactivating non-existent rule fails."""
        engine = PricingEngine(mock_db_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with pytest.raises(PricingError) as exc_info:
                await engine.deactivate_pricing_rule("nonexistent", "tenant_123")

        assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
class TestPriceCalculation:
    """Test price calculation engine."""

    async def test_calculate_price_with_percentage_discount(
        self, mock_db_session: AsyncSession
    ) -> None:
        """Test price calculation with percentage discount."""
        engine = PricingEngine(mock_db_session)

        # Mock product
        mock_product = MagicMock()
        mock_product.product_id = "prod_123"
        mock_product.base_price = Decimal("100.00")
        mock_product.category = "electronics"

        # Mock pricing rule
        mock_db_rule = MagicMock(spec=BillingPricingRuleTable)
        mock_db_rule.rule_id = "rule_123"
        mock_db_rule.tenant_id = "tenant_123"
        mock_db_rule.name = "10% Off"
        mock_db_rule.applies_to_product_ids = ["prod_123"]
        mock_db_rule.applies_to_categories = []
        mock_db_rule.applies_to_all = False
        mock_db_rule.min_quantity = None
        mock_db_rule.customer_segments = []
        mock_db_rule.discount_type = "percentage"
        mock_db_rule.discount_value = Decimal("10")
        mock_db_rule.starts_at = None
        mock_db_rule.ends_at = None
        mock_db_rule.max_uses = None
        mock_db_rule.current_uses = 0
        mock_db_rule.is_active = True
        mock_db_rule.metadata_json = {}
        mock_db_rule.priority = 10
        mock_db_rule.created_at = datetime.now(UTC)
        mock_db_rule.updated_at = datetime.now(UTC)

        request = PriceCalculationRequest(
            product_id="prod_123",
            quantity=2,
            customer_id="cust_123",
        )

        # Mock product service
        with patch.object(engine.product_service, "get_product", return_value=mock_product):
            # Mock rule queries
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_db_rule]

            mock_session = AsyncMock(spec=AsyncSession)
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()

            with patch(
                "dotmac.platform.billing.pricing.service.get_async_session"
            ) as mock_get_session:
                mock_get_session.return_value.__aenter__.return_value = mock_session

                result = await engine.calculate_price(request, "tenant_123")

        assert result.base_price == Decimal("100.00")
        assert result.quantity == 2
        assert result.subtotal == Decimal("200.00")
        assert result.total_discount_amount == Decimal("20.00")  # 10% of 200
        assert result.final_price == Decimal("180.00")
        assert len(result.applied_adjustments) == 1
        assert result.applied_adjustments[0].discount_type == DiscountType.PERCENTAGE
        assert result.currency == "USD"

    async def test_calculate_price_normalizes_multi_currency(
        self, mock_db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Ensure multi-currency calculations populate normalized totals."""

        monkeypatch.setattr(settings.billing, "enable_multi_currency", True)
        monkeypatch.setattr(settings.billing, "default_currency", "USD")

        engine = PricingEngine(mock_db_session)

        mock_product = MagicMock()
        mock_product.product_id = "prod_eur"
        mock_product.base_price = Decimal("120.00")
        mock_product.category = "saas"
        mock_product.currency = "EUR"

        request = PriceCalculationRequest(
            product_id="prod_eur",
            quantity=1,
            customer_id="cust_123",
            currency="EUR",
        )

        class DummyRateService:
            def __init__(self, session: AsyncSession) -> None:
                self.session = session

            async def convert_money(self, money, target_currency: str, *, force_refresh: bool = False):
                return money_handler.create_money(money.amount * Decimal("1.10"), target_currency)

            async def get_rate(self, base_currency: str, target_currency: str, *, force_refresh: bool = False):
                return Decimal("1.10")

        with patch.object(engine.product_service, "get_product", return_value=mock_product):
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []

            mock_session = AsyncMock(spec=AsyncSession)
            mock_session.execute = AsyncMock(return_value=mock_result)

            with patch(
                "dotmac.platform.billing.pricing.service.CurrencyRateService",
                DummyRateService,
            ):
                result = await engine.calculate_price(request, "tenant_123")

        assert result.currency == "EUR"
        assert result.normalized_currency == "USD"
        assert result.normalized_amount == Decimal("132.00")

    async def test_calculate_price_with_fixed_amount_discount(
        self, mock_db_session: AsyncSession
    ) -> None:
        """Test price calculation with fixed amount discount."""
        engine = PricingEngine(mock_db_session)

        # Mock product
        mock_product = MagicMock()
        mock_product.product_id = "prod_123"
        mock_product.base_price = Decimal("50.00")
        mock_product.category = "books"

        # Mock pricing rule - $10 off
        mock_db_rule = MagicMock(spec=BillingPricingRuleTable)
        mock_db_rule.rule_id = "rule_456"
        mock_db_rule.tenant_id = "tenant_123"
        mock_db_rule.name = "$10 Off"
        mock_db_rule.applies_to_product_ids = []
        mock_db_rule.applies_to_categories = ["books"]
        mock_db_rule.applies_to_all = False
        mock_db_rule.min_quantity = None
        mock_db_rule.customer_segments = []
        mock_db_rule.discount_type = "fixed_amount"
        mock_db_rule.discount_value = Decimal("10.00")
        mock_db_rule.starts_at = None
        mock_db_rule.ends_at = None
        mock_db_rule.max_uses = None
        mock_db_rule.current_uses = 0
        mock_db_rule.is_active = True
        mock_db_rule.metadata_json = {}
        mock_db_rule.priority = 5
        mock_db_rule.created_at = datetime.now(UTC)
        mock_db_rule.updated_at = datetime.now(UTC)

        request = PriceCalculationRequest(
            product_id="prod_123",
            quantity=1,
            customer_id="cust_123",
        )

        with patch.object(engine.product_service, "get_product", return_value=mock_product):
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_db_rule]

            mock_session = AsyncMock(spec=AsyncSession)
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()

            with patch(
                "dotmac.platform.billing.pricing.service.get_async_session"
            ) as mock_get_session:
                mock_get_session.return_value.__aenter__.return_value = mock_session

                result = await engine.calculate_price(request, "tenant_123")

        assert result.subtotal == Decimal("50.00")
        assert result.total_discount_amount == Decimal("10.00")
        assert result.final_price == Decimal("40.00")
        assert result.applied_adjustments[0].discount_type == DiscountType.FIXED_AMOUNT

    async def test_calculate_price_no_applicable_rules(self, mock_db_session: AsyncSession) -> None:
        """Test price calculation with no applicable rules."""
        engine = PricingEngine(mock_db_session)

        mock_product = MagicMock()
        mock_product.product_id = "prod_123"
        mock_product.base_price = Decimal("100.00")
        mock_product.category = "electronics"

        request = PriceCalculationRequest(
            product_id="prod_123",
            quantity=1,
            customer_id="cust_123",
        )

        with patch.object(engine.product_service, "get_product", return_value=mock_product):
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []  # No rules

            mock_session = AsyncMock(spec=AsyncSession)
            mock_session.execute = AsyncMock(return_value=mock_result)

            with patch(
                "dotmac.platform.billing.pricing.service.get_async_session"
            ) as mock_get_session:
                mock_get_session.return_value.__aenter__.return_value = mock_session

                result = await engine.calculate_price(request, "tenant_123")

        assert result.subtotal == Decimal("100.00")
        assert result.total_discount_amount == Decimal("0")
        assert result.final_price == Decimal("100.00")
        assert len(result.applied_adjustments) == 0


@pytest.mark.asyncio
class TestRuleUsageTracking:
    """Test rule usage tracking."""

    async def test_get_rule_usage_stats(self, mock_db_session: AsyncSession) -> None:
        """Test getting usage statistics for a rule."""
        engine = PricingEngine(mock_db_session)

        mock_db_rule = MagicMock(spec=BillingPricingRuleTable)
        mock_db_rule.rule_id = "rule_123"
        mock_db_rule.name = "Test Rule"
        mock_db_rule.current_uses = 5
        mock_db_rule.max_uses = 10
        mock_db_rule.is_active = True
        mock_db_rule.created_at = datetime.now(UTC)

        mock_rule_result = MagicMock()
        mock_rule_result.scalar_one_or_none.return_value = mock_db_rule

        mock_usage_result = MagicMock()
        mock_usage_result.scalar.return_value = 5

        mock_session = AsyncMock(spec=AsyncSession)

        # Setup execute to return different results based on call
        call_count = 0

        async def mock_execute(stmt: Any) -> Any:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_rule_result
            else:
                return mock_usage_result

        mock_session.execute = mock_execute

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            stats = await engine.get_rule_usage_stats("rule_123", "tenant_123")

        assert stats is not None
        assert stats["rule_id"] == "rule_123"
        assert stats["current_uses"] == 5
        assert stats["actual_usage_count"] == 5
        assert stats["max_uses"] == 10
        assert stats["usage_remaining"] == 5

    async def test_reset_rule_usage(self, mock_db_session: AsyncSession) -> None:
        """Test resetting rule usage counter."""
        engine = PricingEngine(mock_db_session)

        mock_db_rule = MagicMock(spec=BillingPricingRuleTable)
        mock_db_rule.rule_id = "rule_123"
        mock_db_rule.current_uses = 10

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_db_rule

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            success = await engine.reset_rule_usage("rule_123", "tenant_123")

        assert success is True
        assert mock_db_rule.current_uses == 0


@pytest.mark.asyncio
class TestRuleActivation:
    """Test rule activation/deactivation."""

    async def test_activate_rule(self, mock_db_session: AsyncSession) -> None:
        """Test activating a rule."""
        engine = PricingEngine(mock_db_session)

        mock_db_rule = MagicMock(spec=BillingPricingRuleTable)
        mock_db_rule.rule_id = "rule_123"
        mock_db_rule.is_active = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_db_rule

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            success = await engine.activate_rule("rule_123", "tenant_123")

        assert success is True
        assert mock_db_rule.is_active is True

    async def test_deactivate_rule(self, mock_db_session: AsyncSession) -> None:
        """Test deactivating a rule."""
        engine = PricingEngine(mock_db_session)

        mock_db_rule = MagicMock(spec=BillingPricingRuleTable)
        mock_db_rule.rule_id = "rule_123"
        mock_db_rule.is_active = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_db_rule

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            success = await engine.deactivate_rule("rule_123", "tenant_123")

        assert success is True
        assert mock_db_rule.is_active is False

    async def test_bulk_activate_rules(self, mock_db_session: AsyncSession) -> None:
        """Test bulk activating rules."""
        engine = PricingEngine(mock_db_session)

        with patch.object(engine, "activate_rule") as mock_activate:
            mock_activate.side_effect = [True, True, False]  # 2 success, 1 not found

            results = await engine.bulk_activate_rules(["rule_1", "rule_2", "rule_3"], "tenant_123")

        assert results["activated"] == 2
        assert results["failed"] == 1
        assert len(results["errors"]) == 1

    async def test_bulk_deactivate_rules(self, mock_db_session: AsyncSession) -> None:
        """Test bulk deactivating rules."""
        engine = PricingEngine(mock_db_session)

        with patch.object(engine, "deactivate_rule") as mock_deactivate:
            mock_deactivate.side_effect = [True, True]

            results = await engine.bulk_deactivate_rules(["rule_1", "rule_2"], "tenant_123")

        assert results["deactivated"] == 2
        assert results["failed"] == 0


@pytest.mark.asyncio
class TestRuleConflictDetection:
    """Test rule conflict detection."""

    async def test_detect_no_conflicts(self, mock_db_session: AsyncSession) -> None:
        """Test detecting no conflicts when rules don't overlap."""
        engine = PricingEngine(mock_db_session)

        mock_db_rule1 = self._create_mock_rule("rule_1", "Rule 1", ["prod_1"], [], 10)
        mock_db_rule2 = self._create_mock_rule("rule_2", "Rule 2", ["prod_2"], [], 10)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_db_rule1, mock_db_rule2]

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            conflicts = await engine.detect_rule_conflicts("tenant_123")

        assert len(conflicts) == 0

    async def test_detect_priority_overlap_conflict(self, mock_db_session: AsyncSession) -> None:
        """Test detecting priority overlap conflicts."""
        engine = PricingEngine(mock_db_session)

        # Two rules with same priority and overlapping products
        mock_db_rule1 = self._create_mock_rule("rule_1", "Rule 1", ["prod_1"], [], 10)
        mock_db_rule2 = self._create_mock_rule("rule_2", "Rule 2", ["prod_1"], [], 10)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_db_rule1, mock_db_rule2]

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch("dotmac.platform.billing.pricing.service.get_async_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            conflicts = await engine.detect_rule_conflicts("tenant_123")

        assert len(conflicts) > 0
        assert conflicts[0]["type"] == "priority_overlap"
        assert conflicts[0]["priority"] == 10

    def _create_mock_rule(
        self,
        rule_id: str,
        name: str,
        product_ids: list[str],
        categories: list[str],
        priority: int,
    ) -> MagicMock:
        """Helper to create mock rule for conflict detection."""
        mock_rule = MagicMock(spec=BillingPricingRuleTable)
        mock_rule.rule_id = rule_id
        mock_rule.tenant_id = "tenant_123"
        mock_rule.name = name
        mock_rule.applies_to_product_ids = product_ids
        mock_rule.applies_to_categories = categories
        mock_rule.applies_to_all = False
        mock_rule.min_quantity = None
        mock_rule.customer_segments = []
        mock_rule.discount_type = "percentage"
        mock_rule.discount_value = Decimal("10")
        mock_rule.starts_at = None
        mock_rule.ends_at = None
        mock_rule.max_uses = None
        mock_rule.current_uses = 0
        mock_rule.is_active = True
        mock_rule.metadata_json = {}
        mock_rule.priority = priority
        mock_rule.created_at = datetime.now(UTC)
        mock_rule.updated_at = datetime.now(UTC)
        return mock_rule
