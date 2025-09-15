"""
Feature Flag System for DotMac Framework
Supports gradual rollouts, A/B testing, and safe deployments
"""

from .api import create_feature_flag_router
from .client import FeatureFlagClient
from .decorators import ab_test, feature_flag, requires_feature
from .middleware import FeatureFlagMiddleware
from .models import RolloutStrategy, TargetingRule

# Lightweight compatibility classes for simplified tests
class FeatureFlag:  # type: ignore[override]
    def __init__(self, name: str, enabled: bool = False, description: str | None = None):
        self.name = name
        self.enabled = enabled
        self.description = description


class FeatureFlagManager:  # type: ignore[override]
    def __init__(self):
        import logging

        logging.getLogger(__name__).info("FeatureFlagManager initialized for development environment")
        self._flags: dict[str, bool] = {}

    def register_flag(self, name: str, enabled: bool = False) -> None:
        self._flags[name] = enabled

    def is_enabled(self, name: str) -> bool:
        return bool(self._flags.get(name, False))

__all__ = [
    "FeatureFlagManager",
    "FeatureFlag",
    "RolloutStrategy",
    "TargetingRule",
    "feature_flag",
    "requires_feature",
    "ab_test",
    "FeatureFlagMiddleware",
    "FeatureFlagClient",
    "create_feature_flag_router",
]
