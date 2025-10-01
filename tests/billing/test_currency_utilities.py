"""
Tests for currency utilities
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from dotmac.platform.billing.config import BillingConfig, CurrencyConfig
from dotmac.platform.billing.utils.currency import (
    CurrencyFormatter,
    get_currency_formatter,
    format_money,
    parse_money,
)


@pytest.fixture
def usd_currency_config():
    """USD currency configuration"""
    return CurrencyConfig(
        default_currency="USD",
        currency_symbol="$",
        currency_decimal_places=2,
        currency_format="{symbol}{amount}",
        use_minor_units=True,
    )


@pytest.fixture
def yen_currency_config():
    """Japanese Yen configuration (no decimal places)"""
    return CurrencyConfig(
        default_currency="JPY",
        currency_symbol="¥",
        currency_decimal_places=0,
        currency_format="{symbol}{amount}",
        use_minor_units=False,
    )


@pytest.fixture
def euro_currency_config():
    """Euro currency configuration with different format"""
    return CurrencyConfig(
        default_currency="EUR",
        currency_symbol="€",
        currency_decimal_places=2,
        currency_format="{amount} {symbol}",
        use_minor_units=True,
    )


@pytest.fixture
def mock_billing_config(usd_currency_config):
    """Mock billing configuration with USD"""
    config = MagicMock(spec=BillingConfig)
    config.currency = usd_currency_config
    return config


class TestCurrencyFormatter:
    """Test currency formatter functionality"""

    def test_format_amount_usd_with_symbol(self, mock_billing_config):
        """Test formatting USD amount with symbol"""
        
        with patch('dotmac.platform.billing.utils.currency.get_billing_config', return_value=mock_billing_config):
            formatter = CurrencyFormatter()
            
            # $100.00 in cents
            result = formatter.format_amount(10000, include_symbol=True)
            assert result == "$100.00"
            
            # $1.99 in cents
            result = formatter.format_amount(199, include_symbol=True)
            assert result == "$1.99"
            
            # $0.01 in cents
            result = formatter.format_amount(1, include_symbol=True)
            assert result == "$0.01"

    def test_format_amount_usd_without_symbol(self, mock_billing_config):
        """Test formatting USD amount without symbol"""
        
        with patch('dotmac.platform.billing.utils.currency.get_billing_config', return_value=mock_billing_config):
            formatter = CurrencyFormatter()
            
            result = formatter.format_amount(10000, include_symbol=False)
            assert result == "100.00"
            
            result = formatter.format_amount(199, include_symbol=False)
            assert result == "1.99"

    def test_format_amount_yen(self, yen_currency_config):
        """Test formatting Japanese Yen (no decimal places)"""
        
        mock_config = MagicMock()
        mock_config.currency = yen_currency_config
        
        with patch('dotmac.platform.billing.utils.currency.get_billing_config', return_value=mock_config):
            formatter = CurrencyFormatter()
            
            # ¥100 (no minor units)
            result = formatter.format_amount(100, include_symbol=True)
            assert result == "¥100"
            
            result = formatter.format_amount(100, include_symbol=False)
            assert result == "100"

    def test_format_amount_euro(self, euro_currency_config):
        """Test formatting Euro with different format pattern"""
        
        mock_config = MagicMock()
        mock_config.currency = euro_currency_config
        
        with patch('dotmac.platform.billing.utils.currency.get_billing_config', return_value=mock_config):
            formatter = CurrencyFormatter()
            
            # €100.00 with format "{amount} {symbol}"
            result = formatter.format_amount(10000, include_symbol=True)
            assert result == "100.00 €"

    def test_parse_amount_usd(self, mock_billing_config):
        """Test parsing USD amounts"""
        
        with patch('dotmac.platform.billing.utils.currency.get_billing_config', return_value=mock_billing_config):
            formatter = CurrencyFormatter()
            
            # With symbol
            result = formatter.parse_amount("$100.00")
            assert result == 10000
            
            # Without symbol
            result = formatter.parse_amount("100.00")
            assert result == 10000
            
            # With thousands separator
            result = formatter.parse_amount("$1,234.56")
            assert result == 123456
            
            # Just cents
            result = formatter.parse_amount("$0.99")
            assert result == 99

    def test_parse_amount_yen(self, yen_currency_config):
        """Test parsing Japanese Yen amounts"""
        
        mock_config = MagicMock()
        mock_config.currency = yen_currency_config
        
        with patch('dotmac.platform.billing.utils.currency.get_billing_config', return_value=mock_config):
            formatter = CurrencyFormatter()
            
            result = formatter.parse_amount("¥100")
            assert result == 100
            
            result = formatter.parse_amount("100")
            assert result == 100

    def test_convert_to_minor_units(self, mock_billing_config):
        """Test converting to minor units"""
        
        with patch('dotmac.platform.billing.utils.currency.get_billing_config', return_value=mock_billing_config):
            formatter = CurrencyFormatter()
            
            # $100.00 -> 10000 cents
            result = formatter.convert_to_minor_units(Decimal("100.00"))
            assert result == 10000
            
            # $1.99 -> 199 cents
            result = formatter.convert_to_minor_units(Decimal("1.99"))
            assert result == 199
            
            # $0.01 -> 1 cent
            result = formatter.convert_to_minor_units(Decimal("0.01"))
            assert result == 1

    def test_convert_to_minor_units_yen(self, yen_currency_config):
        """Test converting to minor units for currency without decimals"""
        
        mock_config = MagicMock()
        mock_config.currency = yen_currency_config
        
        with patch('dotmac.platform.billing.utils.currency.get_billing_config', return_value=mock_config):
            formatter = CurrencyFormatter()
            
            # No conversion needed for JPY
            result = formatter.convert_to_minor_units(Decimal("100"))
            assert result == 100

    def test_convert_to_major_units(self, mock_billing_config):
        """Test converting to major units"""

        with patch('dotmac.platform.billing.utils.currency.get_billing_config', return_value=mock_billing_config):
            formatter = CurrencyFormatter()

            # 10000 cents -> $100.00
            result = formatter.convert_to_major_units(10000)
            assert result == Decimal("100.00")

            # 199 cents -> $1.99
            result = formatter.convert_to_major_units(199)
            assert result == Decimal("1.99")

            # 1 cent -> $0.01
            result = formatter.convert_to_major_units(1)
            assert result == Decimal("0.01")

    def test_convert_to_major_units_yen(self, yen_currency_config):
        """Test converting to major units for currency without decimals"""
        
        mock_config = MagicMock()
        mock_config.currency = yen_currency_config
        
        with patch('dotmac.platform.billing.utils.currency.get_billing_config', return_value=mock_config):
            formatter = CurrencyFormatter()
            
            # No conversion needed for JPY
            result = formatter.convert_to_major_units(100)
            assert result == Decimal("100")

    def test_get_currency_info(self, mock_billing_config):
        """Test getting currency information"""
        
        with patch('dotmac.platform.billing.utils.currency.get_billing_config', return_value=mock_billing_config):
            formatter = CurrencyFormatter()
            
            info = formatter.get_currency_info()
            
            assert info["currency_code"] == "USD"
            assert info["currency_symbol"] == "$"
            assert info["decimal_places"] == 2
            assert info["uses_minor_units"] is True
            assert info["format_pattern"] == "{symbol}{amount}"

    def test_validate_amount(self, mock_billing_config):
        """Test amount validation"""
        
        with patch('dotmac.platform.billing.utils.currency.get_billing_config', return_value=mock_billing_config):
            formatter = CurrencyFormatter()
            
            # Valid amounts
            assert formatter.validate_amount(0) is True
            assert formatter.validate_amount(1) is True
            assert formatter.validate_amount(10000) is True
            assert formatter.validate_amount(99_999_999_999) is True
            
            # Invalid amounts
            assert formatter.validate_amount(-1) is False
            assert formatter.validate_amount(100_000_000_000) is False  # Too large

    def test_rounding_behavior(self, mock_billing_config):
        """Test proper rounding behavior"""
        
        with patch('dotmac.platform.billing.utils.currency.get_billing_config', return_value=mock_billing_config):
            formatter = CurrencyFormatter()
            
            # Test rounding half up
            result = formatter.convert_to_minor_units(Decimal("1.235"))
            assert result == 124  # Rounds up to 124 cents
            
            result = formatter.convert_to_minor_units(Decimal("1.234"))
            assert result == 123  # Rounds down to 123 cents

    def test_zero_amounts(self, mock_billing_config):
        """Test handling of zero amounts"""
        
        with patch('dotmac.platform.billing.utils.currency.get_billing_config', return_value=mock_billing_config):
            formatter = CurrencyFormatter()
            
            # Format zero
            result = formatter.format_amount(0)
            assert result == "$0.00"
            
            # Parse zero
            result = formatter.parse_amount("$0.00")
            assert result == 0
            
            # Convert zero
            result = formatter.convert_to_minor_units(Decimal("0"))
            assert result == 0
            
            result = formatter.convert_to_major_units(0)
            assert result == Decimal("0.00")


class TestCurrencyUtilityFunctions:
    """Test utility functions"""

    @patch('dotmac.platform.billing.utils.currency._currency_formatter', None)
    def test_get_currency_formatter_singleton(self, mock_billing_config):
        """Test that currency formatter is a singleton"""
        
        with patch('dotmac.platform.billing.utils.currency.get_billing_config', return_value=mock_billing_config):
            formatter1 = get_currency_formatter()
            formatter2 = get_currency_formatter()
            
            # Should return the same instance
            assert formatter1 is formatter2

    def test_format_money_convenience_function(self, mock_billing_config):
        """Test format_money convenience function"""
        
        with patch('dotmac.platform.billing.utils.currency.get_billing_config', return_value=mock_billing_config):
            result = format_money(10000)  # $100.00
            assert result == "$100.00"
            
            result = format_money(10000, include_symbol=False)
            assert result == "100.00"

    def test_parse_money_convenience_function(self, mock_billing_config):
        """Test parse_money convenience function"""
        
        with patch('dotmac.platform.billing.utils.currency.get_billing_config', return_value=mock_billing_config):
            result = parse_money("$100.00")
            assert result == 10000
            
            result = parse_money("100.00")
            assert result == 10000

    def test_edge_cases(self, mock_billing_config):
        """Test edge cases and error handling"""
        
        with patch('dotmac.platform.billing.utils.currency.get_billing_config', return_value=mock_billing_config):
            formatter = CurrencyFormatter()
            
            # Empty string parsing should raise error
            with pytest.raises(Exception):
                formatter.parse_amount("")
            
            # Invalid format should raise error
            with pytest.raises(Exception):
                formatter.parse_amount("not_a_number")

    def test_large_amounts(self, mock_billing_config):
        """Test handling of large amounts"""
        
        with patch('dotmac.platform.billing.utils.currency.get_billing_config', return_value=mock_billing_config):
            formatter = CurrencyFormatter()
            
            # Large valid amount
            large_amount = 999_999_99  # $9,999.99 in cents
            result = formatter.format_amount(large_amount)
            assert result == "$9999.99"
            
            # Parse it back
            parsed = formatter.parse_amount(result)
            assert parsed == large_amount

    def test_precision_preservation(self, mock_billing_config):
        """Test that precision is preserved in conversions"""
        
        with patch('dotmac.platform.billing.utils.currency.get_billing_config', return_value=mock_billing_config):
            formatter = CurrencyFormatter()
            
            # Test round-trip conversion
            original_minor = 12345  # $123.45
            major = formatter.convert_to_major_units(original_minor)
            back_to_minor = formatter.convert_to_minor_units(major)
            
            assert back_to_minor == original_minor

    def test_currency_format_customization(self, euro_currency_config):
        """Test custom currency format patterns"""
        
        mock_config = MagicMock()
        mock_config.currency = euro_currency_config
        
        with patch('dotmac.platform.billing.utils.currency.get_billing_config', return_value=mock_config):
            formatter = CurrencyFormatter()
            
            # Euro format: "{amount} {symbol}"
            result = formatter.format_amount(12345)  # €123.45
            assert result == "123.45 €"

    def test_whitespace_handling(self, mock_billing_config):
        """Test handling of whitespace in parsing"""
        
        with patch('dotmac.platform.billing.utils.currency.get_billing_config', return_value=mock_billing_config):
            formatter = CurrencyFormatter()
            
            # Various whitespace scenarios
            test_cases = [
                "  $100.00  ",
                "$ 100.00",
                "100.00 ",
                " 100.00",
            ]
            
            for case in test_cases:
                result = formatter.parse_amount(case)
                assert result == 10000, f"Failed for: '{case}'"