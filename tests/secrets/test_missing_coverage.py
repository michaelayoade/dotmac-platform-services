"""Simple tests to cover missing lines in secrets module."""

import pytest
from unittest.mock import patch, MagicMock, Mock
from dotmac.platform.secrets.secrets_loader import get_nested_attr


class TestGetNestedAttrMissingCoverage:
    """Test missing coverage for get_nested_attr function."""

    def test_get_nested_attr_attribute_error(self):
        """Test get_nested_attr when AttributeError is raised."""
        class TestObj:
            pass

        obj = TestObj()

        # This should trigger AttributeError and return default
        result = get_nested_attr(obj, "nonexistent.attribute", "default_value")
        assert result == "default_value"

    def test_get_nested_attr_no_default_value(self):
        """Test get_nested_attr without providing default."""
        class TestObj:
            pass

        obj = TestObj()

        # Should return None when no default is provided
        result = get_nested_attr(obj, "nonexistent")
        assert result is None

    def test_get_nested_attr_nested_path_error(self):
        """Test get_nested_attr with nested path that fails."""
        class TestObj:
            def __init__(self):
                self.level1 = "not an object"

        obj = TestObj()

        # This should fail when trying to access 'level2' on a string
        result = get_nested_attr(obj, "level1.level2", "fallback")
        assert result == "fallback"

    def test_get_nested_attr_single_level_missing(self):
        """Test get_nested_attr with single level missing attribute."""
        obj = Mock()
        # Mock to not have the attribute 'missing'
        del obj.missing  # This will cause AttributeError on access

        result = get_nested_attr(obj, "missing", "default")
        assert result == "default"