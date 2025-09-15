"""
Database models for feature flags storage
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import ARRAY

from dotmac.database.base import BaseModel

from .models import FeatureFlag, FeatureFlagStatus, RolloutStrategy


class FeatureFlagModel(BaseModel):
    """SQLAlchemy model for feature flags"""

    __tablename__ = "feature_flags"

    # Basic fields
    key = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="draft")

    # Rollout configuration
    strategy = Column(String(50), nullable=False, default="all_off")
    percentage = Column(Float, nullable=False, default=0.0)
    user_list = Column(ARRAY(String), nullable=True)
    tenant_list = Column(ARRAY(String), nullable=True)

    # Advanced configurations (stored as JSON)
    targeting_rules = Column(JSON, nullable=True)
    gradual_rollout = Column(JSON, nullable=True)
    ab_test = Column(JSON, nullable=True)
    payload = Column(JSON, nullable=True)

    # Metadata
    tags = Column(ARRAY(String), nullable=True)
    owner = Column(String(255), nullable=True)
    environments = Column(ARRAY(String), nullable=True)

    # Expiry
    expires_at = Column(DateTime, nullable=True)

    def to_pydantic(self) -> FeatureFlag:
        """Convert SQLAlchemy model to Pydantic model"""
        data = {
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "status": FeatureFlagStatus(self.status),
            "strategy": RolloutStrategy(self.strategy),
            "percentage": self.percentage,
            "user_list": self.user_list or [],
            "tenant_list": self.tenant_list or [],
            "targeting_rules": self._deserialize_targeting_rules(),
            "gradual_rollout": self._deserialize_gradual_rollout(),
            "ab_test": self._deserialize_ab_test(),
            "payload": self.payload,
            "tags": self.tags or [],
            "owner": self.owner,
            "environments": self.environments or [],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
        }

        return FeatureFlag(**data)

    @classmethod
    def from_pydantic(cls, flag: FeatureFlag) -> "FeatureFlagModel":
        """Create SQLAlchemy model from Pydantic model"""
        return cls(
            key=flag.key,
            name=flag.name,
            description=flag.description,
            status=flag.status.value,
            strategy=flag.strategy.value,
            percentage=flag.percentage,
            user_list=flag.user_list,
            tenant_list=flag.tenant_list,
            targeting_rules=cls._serialize_targeting_rules(flag.targeting_rules),
            gradual_rollout=cls._serialize_gradual_rollout(flag.gradual_rollout),
            ab_test=cls._serialize_ab_test(flag.ab_test),
            payload=flag.payload,
            tags=flag.tags,
            owner=flag.owner,
            environments=flag.environments,
            expires_at=flag.expires_at,
        )

    def update_from_pydantic(self, flag: FeatureFlag):
        """Update SQLAlchemy model from Pydantic model"""
        self.name = flag.name
        self.description = flag.description
        self.status = flag.status.value
        self.strategy = flag.strategy.value
        self.percentage = flag.percentage
        self.user_list = flag.user_list
        self.tenant_list = flag.tenant_list
        self.targeting_rules = self._serialize_targeting_rules(flag.targeting_rules)
        self.gradual_rollout = self._serialize_gradual_rollout(flag.gradual_rollout)
        self.ab_test = self._serialize_ab_test(flag.ab_test)
        self.payload = flag.payload
        self.tags = flag.tags
        self.owner = flag.owner
        self.environments = flag.environments
        self.expires_at = flag.expires_at
        self.updated_at = datetime.utcnow()

    def _deserialize_targeting_rules(self):
        """Convert JSON to TargetingRule objects"""
        if not self.targeting_rules:
            return []

        from .models import ComparisonOperator, TargetingAttribute, TargetingRule

        rules = []
        for rule_data in self.targeting_rules:
            rules.append(
                TargetingRule(
                    attribute=TargetingAttribute(rule_data["attribute"]),
                    operator=ComparisonOperator(rule_data["operator"]),
                    value=rule_data["value"],
                    description=rule_data.get("description"),
                )
            )

        return rules

    @staticmethod
    def _serialize_targeting_rules(rules):
        """Convert TargetingRule objects to JSON"""
        if not rules:
            return None

        return [
            {
                "attribute": rule.attribute.value,
                "operator": rule.operator.value,
                "value": rule.value,
                "description": rule.description,
            }
            for rule in rules
        ]

    def _deserialize_gradual_rollout(self):
        """Convert JSON to GradualRolloutConfig"""
        if not self.gradual_rollout:
            return None

        from .models import GradualRolloutConfig

        return GradualRolloutConfig(**self.gradual_rollout)

    @staticmethod
    def _serialize_gradual_rollout(config):
        """Convert GradualRolloutConfig to JSON"""
        if not config:
            return None

        data = config.model_dump()
        # Convert datetime objects to ISO strings
        data["start_date"] = config.start_date.isoformat()
        data["end_date"] = config.end_date.isoformat()

        return data

    def _deserialize_ab_test(self):
        """Convert JSON to ABTestConfig"""
        if not self.ab_test:
            return None

        from .models import ABTestConfig, ABTestVariant

        variants = []
        for variant_data in self.ab_test["variants"]:
            variants.append(ABTestVariant(**variant_data))

        return ABTestConfig(variants=variants, control_variant=self.ab_test["control_variant"])

    @staticmethod
    def _serialize_ab_test(config):
        """Convert ABTestConfig to JSON"""
        if not config:
            return None

        return {
            "variants": [variant.model_dump() for variant in config.variants],
            "control_variant": config.control_variant,
        }


class FeatureFlagAuditModel(BaseModel):
    """Audit trail for feature flag changes"""

    __tablename__ = "feature_flag_audit"

    flag_key = Column(String(255), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # created, updated, deleted, enabled, disabled
    previous_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    changed_by = Column(String(255), nullable=True)
    reason = Column(Text, nullable=True)

    @classmethod
    def log_change(
        cls,
        flag_key: str,
        action: str,
        previous_value: Optional[dict[str, Any]] = None,
        new_value: Optional[dict[str, Any]] = None,
        changed_by: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        """Create an audit log entry"""
        return cls(
            flag_key=flag_key,
            action=action,
            previous_value=previous_value,
            new_value=new_value,
            changed_by=changed_by,
            reason=reason,
        )


class FeatureFlagEvaluationModel(BaseModel):
    """Track feature flag evaluations for analytics"""

    __tablename__ = "feature_flag_evaluations"

    flag_key = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    tenant_id = Column(String(255), nullable=True, index=True)
    environment = Column(String(50), nullable=False, index=True)
    service_name = Column(String(100), nullable=True)

    # Evaluation result
    enabled = Column(Boolean, nullable=False)
    variant = Column(String(100), nullable=True)

    # Context (stored as JSON for flexibility)
    context = Column(JSON, nullable=True)

    # Metadata
    evaluation_time_ms = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)

    @classmethod
    def log_evaluation(
        cls,
        flag_key: str,
        environment: str,
        enabled: bool,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        service_name: Optional[str] = None,
        variant: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
        evaluation_time_ms: Optional[float] = None,
        error_message: Optional[str] = None,
    ):
        """Create an evaluation log entry"""
        return cls(
            flag_key=flag_key,
            user_id=user_id,
            tenant_id=tenant_id,
            environment=environment,
            service_name=service_name,
            enabled=enabled,
            variant=variant,
            context=context,
            evaluation_time_ms=evaluation_time_ms,
            error_message=error_message,
        )
