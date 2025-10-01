"""
Tests for tax calculation functionality
"""

from decimal import Decimal
from typing import List

import pytest

from dotmac.platform.billing.tax.calculator import (
    TaxCalculator,
    TaxRate,
    TaxCalculationResult,
)


@pytest.fixture
def basic_tax_rates() -> List[TaxRate]:
    """Basic tax rates for testing"""
    return [
        TaxRate(
            name="California Sales Tax",
            rate=Decimal("7.25"),
            jurisdiction="US-CA",
            tax_type="sales",
        ),
        TaxRate(
            name="New York Sales Tax",
            rate=Decimal("8.875"),
            jurisdiction="US-NY",
            tax_type="sales",
        ),
        TaxRate(
            name="UK VAT",
            rate=Decimal("20.0"),
            jurisdiction="EU-GB",
            tax_type="vat",
            is_inclusive=True,
        ),
    ]


@pytest.fixture
def compound_tax_rates() -> List[TaxRate]:
    """Tax rates with compound taxes (like Canadian GST + PST)"""
    return [
        TaxRate(
            name="BC GST",
            rate=Decimal("5.0"),
            jurisdiction="CA-BC",
            tax_type="gst",
        ),
        TaxRate(
            name="BC PST",
            rate=Decimal("7.0"),
            jurisdiction="CA-BC",
            tax_type="pst",
            is_compound=True,  # PST compounds on GST
        ),
    ]


@pytest.fixture
def tax_calculator(basic_tax_rates) -> TaxCalculator:
    """Tax calculator with basic rates"""
    return TaxCalculator(default_rates=basic_tax_rates)


class TestTaxRate:
    """Test TaxRate model"""

    def test_tax_rate_creation(self):
        """Test creating a tax rate"""
        rate = TaxRate(
            name="Test Tax",
            rate=Decimal("10.0"),
            jurisdiction="US-TEST",
            tax_type="sales",
        )
        
        assert rate.name == "Test Tax"
        assert rate.rate == Decimal("10.0")
        assert rate.jurisdiction == "US-TEST"
        assert rate.tax_type == "sales"
        assert rate.is_compound is False
        assert rate.is_inclusive is False
        assert rate.threshold_amount is None

    def test_tax_rate_validation(self):
        """Test tax rate validation"""
        # Rate cannot be negative
        with pytest.raises(ValueError):
            TaxRate(
                name="Invalid Tax",
                rate=Decimal("-5.0"),
                jurisdiction="US-TEST",
            )
        
        # Rate cannot exceed 100%
        with pytest.raises(ValueError):
            TaxRate(
                name="Invalid Tax",
                rate=Decimal("105.0"),
                jurisdiction="US-TEST",
            )


class TestTaxCalculator:
    """Test TaxCalculator functionality"""

    def test_calculate_exclusive_tax_single_rate(self, tax_calculator):
        """Test tax calculation with single rate (exclusive)"""
        
        # $100.00 in cents with 7.25% CA sales tax
        result = tax_calculator.calculate_tax(
            amount=10000,  # $100.00
            jurisdiction="US-CA",
            is_tax_inclusive=False,
        )
        
        assert isinstance(result, TaxCalculationResult)
        assert result.subtotal == 10000
        assert result.tax_amount == 725  # $7.25 in cents
        assert result.total_amount == 10725  # $107.25 in cents
        assert len(result.tax_breakdown) == 1
        assert result.tax_breakdown[0]["name"] == "California Sales Tax"
        assert result.tax_breakdown[0]["rate"] == 7.25
        assert result.tax_breakdown[0]["amount"] == 725

    def test_calculate_inclusive_tax_single_rate(self, tax_calculator):
        """Test tax calculation with single rate (inclusive)"""
        
        # $120.00 total with 20% UK VAT included
        result = tax_calculator.calculate_tax(
            amount=12000,  # $120.00 total
            jurisdiction="EU-GB",
            is_tax_inclusive=True,
        )
        
        assert isinstance(result, TaxCalculationResult)
        assert result.total_amount == 12000
        assert result.subtotal == 10000  # $100.00 before tax
        assert result.tax_amount == 2000   # $20.00 tax
        assert len(result.tax_breakdown) == 1
        assert result.tax_breakdown[0]["name"] == "UK VAT"

    def test_calculate_compound_taxes(self):
        """Test calculation with compound taxes"""
        
        calculator = TaxCalculator()
        
        # Add BC GST and PST rates
        calculator.add_tax_rate(
            jurisdiction="CA-BC",
            name="BC GST",
            rate=5.0,
            tax_type="gst",
        )
        calculator.add_tax_rate(
            jurisdiction="CA-BC",
            name="BC PST",
            rate=7.0,
            tax_type="pst",
            is_compound=True,
        )
        
        # $100.00 with GST (5%) + PST (7% on subtotal + GST)
        result = calculator.calculate_tax(
            amount=10000,  # $100.00
            jurisdiction="CA-BC",
            is_tax_inclusive=False,
        )
        
        # GST: $100 * 5% = $5.00 = 500 cents
        # PST: ($100 + $5) * 7% = $7.35 = 735 cents
        # Total tax: 500 + 735 = 1235 cents = $12.35
        assert result.subtotal == 10000
        assert result.tax_amount == 1235
        assert result.total_amount == 11235
        assert len(result.tax_breakdown) == 2

    def test_calculate_line_item_tax(self, tax_calculator):
        """Test tax calculation for multiple line items"""
        
        line_items = [
            {
                "description": "Product A",
                "amount": 5000,  # $50.00
                "is_tax_exempt": False,
            },
            {
                "description": "Product B (Tax Exempt)",
                "amount": 3000,  # $30.00
                "is_tax_exempt": True,
            },
            {
                "description": "Product C",
                "amount": 2000,  # $20.00
                "is_tax_exempt": False,
            },
        ]
        
        total_tax, items_with_tax = tax_calculator.calculate_line_item_tax(
            line_items=line_items,
            jurisdiction="US-CA",
        )
        
        # Only Product A and C should be taxed
        # Tax = (5000 + 2000) * 7.25% = 7000 * 0.0725 = 507.5 = 508 cents (rounded)
        assert total_tax == 508
        assert len(items_with_tax) == 3
        
        # Check tax amounts per item
        assert items_with_tax[0]["tax_amount"] == 363  # $50 * 7.25% = 362.5 rounded to 363
        assert items_with_tax[1]["tax_amount"] == 0    # Tax exempt
        assert items_with_tax[2]["tax_amount"] == 145  # $20 * 7.25% = 145

    def test_reverse_calculate_tax(self, tax_calculator):
        """Test reverse tax calculation (extracting tax from total)"""
        
        # Total of $107.25 includes 7.25% CA sales tax
        result = tax_calculator.reverse_calculate_tax(
            total_amount=10725,
            jurisdiction="US-CA",
        )
        
        # Should extract $7.25 tax from $107.25 total
        # Subtotal = $107.25 / 1.0725 = $100.00
        assert result.total_amount == 10725
        assert abs(result.subtotal - 10000) <= 1  # Allow for rounding
        assert abs(result.tax_amount - 725) <= 1   # Allow for rounding

    def test_get_effective_rate(self, tax_calculator):
        """Test getting effective tax rate for jurisdiction"""
        
        ca_rate = tax_calculator.get_effective_rate("US-CA")
        ny_rate = tax_calculator.get_effective_rate("US-NY")
        unknown_rate = tax_calculator.get_effective_rate("US-UNKNOWN")
        
        assert ca_rate == Decimal("7.25")
        assert ny_rate == Decimal("8.875")
        assert unknown_rate == Decimal("0")

    def test_tax_with_threshold(self, tax_calculator):
        """Test tax calculation with minimum threshold"""
        
        # Add a tax with $50 minimum threshold
        tax_calculator.add_tax_rate(
            jurisdiction="US-THRESHOLD",
            name="Threshold Tax",
            rate=10.0,
            threshold_amount=5000,  # $50.00 minimum
        )
        
        # Amount below threshold - no tax
        result_below = tax_calculator.calculate_tax(
            amount=4000,  # $40.00 - below threshold
            jurisdiction="US-THRESHOLD",
        )
        assert result_below.tax_amount == 0
        
        # Amount above threshold - tax applies
        result_above = tax_calculator.calculate_tax(
            amount=6000,  # $60.00 - above threshold
            jurisdiction="US-THRESHOLD",
        )
        assert result_above.tax_amount == 600  # $6.00

    def test_add_tax_rate_dynamically(self):
        """Test adding tax rates dynamically"""
        
        calculator = TaxCalculator()
        
        # Initially no rates
        assert len(calculator.default_rates) == 0
        
        # Add a rate
        calculator.add_tax_rate(
            jurisdiction="US-TEST",
            name="Test Tax",
            rate=5.5,
        )
        
        assert len(calculator.default_rates) == 1
        assert calculator.default_rates[0].name == "Test Tax"
        assert calculator.default_rates[0].rate == Decimal("5.5")

    def test_tax_calculation_with_reduced_rate_items(self, tax_calculator):
        """Test tax calculation with reduced rate items"""
        
        # Add reduced rate for UK VAT
        tax_calculator.add_tax_rate(
            jurisdiction="EU-GB",
            name="UK VAT Reduced",
            rate=5.0,
        )
        
        line_items = [
            {
                "description": "Standard Rate Item",
                "amount": 10000,
                "tax_class": "standard",
            },
            {
                "description": "Reduced Rate Item",
                "amount": 5000,
                "tax_class": "reduced",
            },
            {
                "description": "Zero Rate Item",
                "amount": 3000,
                "tax_class": "zero",
            },
        ]
        
        total_tax, items_with_tax = tax_calculator.calculate_line_item_tax(
            line_items=line_items,
            jurisdiction="EU-GB",
        )
        
        # Standard: 10000 * 20% = 2000
        # Reduced: 5000 * 5% = 250  
        # Zero: 3000 * 0% = 0
        # Total: 2000 + 250 + 0 = 2250
        assert total_tax == 2250

    def test_rounding_behavior(self, tax_calculator):
        """Test proper rounding of tax amounts"""
        
        # Test amount that produces fractional cents
        result = tax_calculator.calculate_tax(
            amount=1001,  # $10.01
            jurisdiction="US-CA",  # 7.25%
        )
        
        # $10.01 * 7.25% = $0.725725 = 72.5725 cents
        # Should round to 73 cents (ROUND_HALF_UP)
        assert result.tax_amount == 73

    def test_zero_amount_calculation(self, tax_calculator):
        """Test tax calculation with zero amount"""
        
        result = tax_calculator.calculate_tax(
            amount=0,
            jurisdiction="US-CA",
        )
        
        assert result.subtotal == 0
        assert result.tax_amount == 0
        assert result.total_amount == 0

    def test_jurisdiction_fallback(self, tax_calculator):
        """Test fallback for unknown jurisdiction"""
        
        result = tax_calculator.calculate_tax(
            amount=10000,
            jurisdiction="UNKNOWN-JURISDICTION",
        )
        
        # No tax should be applied for unknown jurisdiction
        assert result.tax_amount == 0
        assert result.total_amount == 10000
        assert len(result.tax_breakdown) == 0