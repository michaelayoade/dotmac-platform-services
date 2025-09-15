"""
Feature flag data models and enums
"""

import hashlib
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RolloutStrategy(str, Enum):
    """Feature flag rollout strategies"""

    ALL_ON = "all_on"  # 100% enabled
    ALL_OFF = "all_off"  # 0% enabled
    PERCENTAGE = "percentage"  # Percentage-based rollout
    USER_LIST = "user_list"  # Specific user IDs
    TENANT_LIST = "tenant_list"  # Specific tenant IDs
    GRADUAL = "gradual"  # Time-based gradual rollout
    AB_TEST = "ab_test"  # A/B testing with variants
    CANARY = "canary"  # Canary deployment
    RING = "ring"  # Ring-based deployment
    GEO = "geo"  # Geographic targeting
    CUSTOM = "custom"  # Custom rule-based


class TargetingAttribute(str, Enum):
    """Attributes that can be used for targeting"""

    USER_ID = "user_id"
    TENANT_ID = "tenant_id"
    EMAIL = "email"
    USER_TIER = "user_tier"
    PLAN_TYPE = "plan_type"
    REGION = "region"
    COUNTRY = "country"
    IP_ADDRESS = "ip_address"
    USER_AGENT = "user_agent"
    SIGNUP_DATE = "signup_date"
    LAST_LOGIN = "last_login"
    FEATURE_USAGE = "feature_usage"
    BETA_USER = "beta_user"
    INTERNAL_USER = "internal_user"


class ComparisonOperator(str, Enum):
    """Operators for targeting rule comparisons"""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    IN = "in"
    NOT_IN = "not_in"
    REGEX = "regex"


class TargetingRule(BaseModel):
    """Rule for targeting specific users/tenants"""

    attribute: TargetingAttribute
    operator: ComparisonOperator
    value: Union[str, int, float, list[str], bool]
    description: Optional[str] = None

    def evaluate(self, context: dict[str, Any]) -> bool:
        """Evaluate rule against context"""
        context_value = context.get(self.attribute.value)
        if context_value is None:
            return False

        if self.operator == ComparisonOperator.EQUALS:
            return context_value == self.value
        elif self.operator == ComparisonOperator.NOT_EQUALS:
            return context_value != self.value
        elif self.operator == ComparisonOperator.CONTAINS:
            return str(self.value) in str(context_value)
        elif self.operator == ComparisonOperator.NOT_CONTAINS:
            return str(self.value) not in str(context_value)
        elif self.operator == ComparisonOperator.STARTS_WITH:
            return str(context_value).startswith(str(self.value))
        elif self.operator == ComparisonOperator.ENDS_WITH:
            return str(context_value).endswith(str(self.value))
        elif self.operator == ComparisonOperator.GREATER_THAN:
            return float(context_value) > float(self.value)
        elif self.operator == ComparisonOperator.LESS_THAN:
            return float(context_value) < float(self.value)
        elif self.operator == ComparisonOperator.GREATER_EQUAL:
            return float(context_value) >= float(self.value)
        elif self.operator == ComparisonOperator.LESS_EQUAL:
            return float(context_value) <= float(self.value)
        elif self.operator == ComparisonOperator.IN:
            return context_value in self.value
        elif self.operator == ComparisonOperator.NOT_IN:
            return context_value not in self.value
        elif self.operator == ComparisonOperator.REGEX:
            import re

            return bool(re.match(str(self.value), str(context_value)))

        return False


class GradualRolloutConfig(BaseModel):
    """Configuration for gradual rollouts"""

    start_percentage: float = Field(0.0, ge=0.0, le=100.0)
    end_percentage: float = Field(100.0, ge=0.0, le=100.0)
    start_date: datetime
    end_date: datetime
    increment_percentage: float = Field(10.0, ge=0.1, le=100.0)
    increment_interval_hours: int = Field(24, ge=1)

    @model_validator(mode="after")
    def validate_ranges(self):
        if self.end_percentage is not None and self.start_percentage is not None:
            if self.end_percentage <= self.start_percentage:
                raise ValueError("end_percentage must be greater than start_percentage")
        if self.end_date is not None and self.start_date is not None:
            if self.end_date <= self.start_date:
                raise ValueError("end_date must be after start_date")
        return self

    def get_current_percentage(self) -> float:
        """Calculate current rollout percentage based on time"""
        now = datetime.utcnow()

        if now < self.start_date:
            return 0.0
        elif now > self.end_date:
            return self.end_percentage

        # Calculate time-based percentage
        total_duration = (self.end_date - self.start_date).total_seconds()
        elapsed_duration = (now - self.start_date).total_seconds()
        progress_ratio = elapsed_duration / total_duration

        percentage_range = self.end_percentage - self.start_percentage
        current_percentage = self.start_percentage + (percentage_range * progress_ratio)

        return min(max(current_percentage, self.start_percentage), self.end_percentage)


class ABTestVariant(BaseModel):
    """A/B test variant configuration"""

    name: str
    percentage: float = Field(ge=0.0, le=100.0)
    payload: Optional[dict[str, Any]] = None
    description: Optional[str] = None


class ABTestConfig(BaseModel):
    """A/B test configuration"""

    variants: list[ABTestVariant]
    control_variant: str = "control"

    @field_validator("variants")
    def validate_variants_sum_to_100(self, v):
        total = sum(variant.percentage for variant in v)
        if abs(total - 100.0) > 0.01:  # Allow small floating point errors
            raise ValueError(f"Variant percentages must sum to 100%, got {total}%")
        return v

    def get_variant_for_user(self, user_id: str) -> ABTestVariant:
        """Determine variant for user using consistent hashing"""
        # Create consistent hash based on user ID
        hash_value = int(hashlib.sha256(user_id.encode()).hexdigest()[:8], 16)
        percentage_bucket = (hash_value % 10000) / 100.0  # 0-99.99%

        cumulative_percentage = 0.0
        for variant in self.variants:
            cumulative_percentage += variant.percentage
            if percentage_bucket < cumulative_percentage:
                return variant

        # Fallback to control
        return next(
            (v for v in self.variants if v.name == self.control_variant),
            self.variants[0],
        )


class FeatureFlagStatus(str, Enum):
    """Feature flag status"""

    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class FeatureFlag(BaseModel):
    """Feature flag configuration model"""

    key: str = Field(..., description="Unique feature flag identifier")
    name: str = Field(..., description="Human-readable name")
    description: Optional[str] = None
    status: FeatureFlagStatus = FeatureFlagStatus.DRAFT

    # Rollout configuration
    strategy: RolloutStrategy = RolloutStrategy.ALL_OFF
    percentage: float = Field(0.0, ge=0.0, le=100.0)
    user_list: list[str] = Field(default_factory=list)
    tenant_list: list[str] = Field(default_factory=list)

    # Advanced configurations
    targeting_rules: list[TargetingRule] = Field(default_factory=list)
    gradual_rollout: Optional[GradualRolloutConfig] = None
    ab_test: Optional[ABTestConfig] = None

    # Metadata
    tags: list[str] = Field(default_factory=list)
    owner: Optional[str] = None
    environments: list[str] = Field(default_factory=lambda: ["development", "staging", "production"])

    # Dates
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    # Payload for complex features
    payload: Optional[dict[str, Any]] = None

    def is_enabled_for_context(self, context: dict[str, Any]) -> bool:
        """Determine if flag is enabled for given context"""
        if self.status != FeatureFlagStatus.ACTIVE:
            return False

        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False

        # Check targeting rules first
        if self.targeting_rules:
            for rule in self.targeting_rules:
                if not rule.evaluate(context):
                    return False

        # Apply strategy
        if self.strategy == RolloutStrategy.ALL_OFF:
            return False
        elif self.strategy == RolloutStrategy.ALL_ON:
            return True
        elif self.strategy == RolloutStrategy.USER_LIST:
            return context.get("user_id") in self.user_list
        elif self.strategy == RolloutStrategy.TENANT_LIST:
            return context.get("tenant_id") in self.tenant_list
        elif self.strategy == RolloutStrategy.PERCENTAGE:
            return self._is_user_in_percentage(context.get("user_id", ""), self.percentage)
        elif self.strategy == RolloutStrategy.GRADUAL:
            if self.gradual_rollout:
                current_percentage = self.gradual_rollout.get_current_percentage()
                return self._is_user_in_percentage(context.get("user_id", ""), current_percentage)
        elif self.strategy == RolloutStrategy.AB_TEST:
            if self.ab_test:
                return True  # A/B test participants are "enabled", variant determines behavior

        return False

    def get_variant_for_context(self, context: dict[str, Any]) -> Optional[str]:
        """Get A/B test variant for context"""
        if self.strategy == RolloutStrategy.AB_TEST and self.ab_test:
            user_id = context.get("user_id", "")
            if user_id:
                variant = self.ab_test.get_variant_for_user(user_id)
                return variant.name
        return None

    def get_payload_for_context(self, context: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Get feature payload for context"""
        if self.strategy == RolloutStrategy.AB_TEST and self.ab_test:
            user_id = context.get("user_id", "")
            if user_id:
                variant = self.ab_test.get_variant_for_user(user_id)
                return variant.payload
        return self.payload

    def _is_user_in_percentage(self, user_id: str, percentage: float) -> bool:
        """Determine if user falls within percentage using consistent hashing"""
        if not user_id:
            return False

        # Create consistent hash combining flag key and user ID
        hash_input = f"{self.key}:{user_id}".encode()
        hash_value = int(hashlib.sha256(hash_input).hexdigest()[:8], 16)
        user_percentage = (hash_value % 10000) / 100.0  # 0-99.99%

        return user_percentage < percentage

    model_config = ConfigDict(use_enum_values=True)
