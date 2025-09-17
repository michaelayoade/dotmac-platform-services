"""Tests for feature flags module."""

import pytest
from dotmac.platform.feature_flags import FeatureFlagManager, FeatureFlag


class TestFeatureFlags:
    def test_feature_flag_creation(self):
        """Test creating a feature flag."""
        flag = FeatureFlag(name="test_feature", enabled=True, description="Test feature flag")
        assert flag.name == "test_feature"
        assert flag.enabled is True

    def test_feature_flag_manager(self):
        """Test feature flag manager."""
        manager = FeatureFlagManager()
        manager.register_flag("test_flag", enabled=False)
        assert not manager.is_enabled("test_flag")
