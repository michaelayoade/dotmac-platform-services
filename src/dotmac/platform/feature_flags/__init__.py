"""
Feature Flag System for DotMac Framework
Supports gradual rollouts, A/B testing, and safe deployments
"""

from .api import create_feature_flag_router
from .client import FeatureFlagClient
from .decorators import ab_test, feature_flag, requires_feature
from .manager import FeatureFlagManager
from .middleware import FeatureFlagMiddleware
from .models import FeatureFlag, RolloutStrategy, TargetingRule

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
