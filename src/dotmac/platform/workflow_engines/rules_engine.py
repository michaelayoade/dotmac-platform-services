"""
Business Rules Engine for validating and enforcing business rules.
"""


from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

class RuleOperator(str, Enum):
    """Rule comparison operators."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    REGEX = "regex"

class RuleSeverity(str, Enum):
    """Rule violation severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class RuleCondition:
    """A single rule condition."""

    field: str
    operator: RuleOperator
    value: Any
    description: Optional[str] = None

@dataclass
class BusinessRule:
    """A business rule definition."""

    name: str
    description: str
    conditions: list[RuleCondition]
    severity: RuleSeverity = RuleSeverity.ERROR
    active: bool = True
    tenant_specific: bool = False
    rule_group: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class RuleViolation:
    """A rule violation."""

    rule_name: str
    field: str
    condition: RuleCondition
    actual_value: Any
    message: str
    severity: RuleSeverity

@dataclass
class RuleResult:
    """Result of rule evaluation."""

    valid: bool
    violations: list[RuleViolation] = field(default_factory=list)
    warnings: list[RuleViolation] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    evaluated_rules: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "valid": self.valid,
            "violations": [
                {
                    "rule_name": v.rule_name,
                    "field": v.field,
                    "message": v.message,
                    "severity": v.severity.value,
                    "actual_value": v.actual_value,
                }
                for v in self.violations
            ],
            "warnings": [
                {
                    "rule_name": v.rule_name,
                    "field": v.field,
                    "message": v.message,
                    "severity": v.severity.value,
                    "actual_value": v.actual_value,
                }
                for v in self.warnings
            ],
            "errors": self.errors,
            "evaluated_rules": self.evaluated_rules,
        }

class BusinessRuleValidator(ABC):
    """Base class for custom business rule validators."""

    @abstractmethod
    async def validate(self, context: dict[str, Any], tenant_id: str) -> RuleResult:
        """Validate business rules."""
        pass

class BusinessRulesEngine:
    """Engine for evaluating business rules."""

    def __init__(self):
        self.rules: dict[str, BusinessRule] = {}
        self.rule_groups: dict[str, list[str]] = {}
        self.custom_validators: dict[str, BusinessRuleValidator] = {}

    def register_rule(self, rule: BusinessRule):
        """Register a business rule."""
        self.rules[rule.name] = rule

        # Add to rule group if specified
        if rule.rule_group:
            if rule.rule_group not in self.rule_groups:
                self.rule_groups[rule.rule_group] = []
            self.rule_groups[rule.rule_group].append(rule.name)

    def register_validator(self, name: str, validator: BusinessRuleValidator):
        """Register a custom rule validator."""
        self.custom_validators[name] = validator

    async def validate_workflow_rules(
        self,
        workflow_type: str,
        context: dict[str, Any],
        tenant_id: str,
    ) -> RuleResult:
        """Validate rules specific to a workflow type."""
        # Get rules for this workflow type
        applicable_rules = []

        for _rule_name, rule in self.rules.items():
            # Check if rule applies to this workflow
            if (
                rule.rule_group == workflow_type
                or rule.metadata.get("workflow_types", []) == ["*"]
                or workflow_type in rule.metadata.get("workflow_types", [])
            ):
                if rule.active:
                    applicable_rules.append(rule)

        return await self._evaluate_rules(applicable_rules, context, tenant_id)

    async def evaluate_rule(
        self,
        rule_name: str,
        context: dict[str, Any],
        tenant_id: str,
    ) -> RuleResult:
        """Evaluate a specific rule."""
        if rule_name not in self.rules:
            return RuleResult(
                valid=False,
                errors=[f"Rule not found: {rule_name}"],
            )

        rule = self.rules[rule_name]
        if not rule.active:
            return RuleResult(valid=True, evaluated_rules=0)

        return await self._evaluate_rules([rule], context, tenant_id)

    async def evaluate_rule_group(
        self,
        group_name: str,
        context: dict[str, Any],
        tenant_id: str,
    ) -> RuleResult:
        """Evaluate all rules in a group."""
        if group_name not in self.rule_groups:
            return RuleResult(
                valid=False,
                errors=[f"Rule group not found: {group_name}"],
            )

        rule_names = self.rule_groups[group_name]
        rules = [self.rules[name] for name in rule_names if self.rules[name].active]

        return await self._evaluate_rules(rules, context, tenant_id)

    async def _evaluate_rules(
        self,
        rules: list[BusinessRule],
        context: dict[str, Any],
        tenant_id: str,
    ) -> RuleResult:
        """Evaluate a list of rules."""
        result = RuleResult(valid=True, evaluated_rules=len(rules))

        for rule in rules:
            try:
                # Check if rule is tenant-specific
                if rule.tenant_specific:
                    tenant_context = context.get("tenant_context", {})
                    evaluation_context = {**context, **tenant_context}
                else:
                    evaluation_context = context

                # Evaluate rule conditions
                rule_violations = await self._evaluate_rule_conditions(rule, evaluation_context)

                # Process violations
                for violation in rule_violations:
                    if violation.severity in [
                        RuleSeverity.ERROR,
                        RuleSeverity.CRITICAL,
                    ]:
                        result.violations.append(violation)
                        result.valid = False
                    else:
                        result.warnings.append(violation)

            except Exception as e:
                logger.error(f"Error evaluating rule {rule.name}: {str(e)}")
                result.errors.append(f"Rule evaluation error for {rule.name}: {str(e)}")
                result.valid = False

        return result

    async def _evaluate_rule_conditions(
        self,
        rule: BusinessRule,
        context: dict[str, Any],
    ) -> list[RuleViolation]:
        """Evaluate all conditions for a rule."""
        violations = []

        for condition in rule.conditions:
            try:
                violation = await self._evaluate_condition(rule, condition, context)
                if violation:
                    violations.append(violation)
            except Exception as e:
                logger.error(
                    f"Error evaluating condition for rule {rule.name}, "
                    f"field {condition.field}: {str(e)}"
                )

        return violations

    async def _evaluate_condition(
        self,
        rule: BusinessRule,
        condition: RuleCondition,
        context: dict[str, Any],
    ) -> Optional[RuleViolation]:
        """Evaluate a single condition."""
        # Get field value from context
        actual_value = self._get_field_value(condition.field, context)
        expected_value = condition.value

        # Evaluate based on operator
        condition_met = False

        if condition.operator == RuleOperator.EQUALS:
            condition_met = actual_value == expected_value
        elif condition.operator == RuleOperator.NOT_EQUALS:
            condition_met = actual_value != expected_value
        elif condition.operator == RuleOperator.GREATER_THAN:
            condition_met = actual_value > expected_value
        elif condition.operator == RuleOperator.LESS_THAN:
            condition_met = actual_value < expected_value
        elif condition.operator == RuleOperator.GREATER_EQUAL:
            condition_met = actual_value >= expected_value
        elif condition.operator == RuleOperator.LESS_EQUAL:
            condition_met = actual_value <= expected_value
        elif condition.operator == RuleOperator.CONTAINS:
            condition_met = expected_value in str(actual_value)
        elif condition.operator == RuleOperator.NOT_CONTAINS:
            condition_met = expected_value not in str(actual_value)
        elif condition.operator == RuleOperator.IN:
            condition_met = actual_value in expected_value
        elif condition.operator == RuleOperator.NOT_IN:
            condition_met = actual_value not in expected_value
        elif condition.operator == RuleOperator.REGEX:
            import re

            condition_met = bool(re.match(expected_value, str(actual_value)))

        # Return violation if condition not met
        if not condition_met:
            message = (
                condition.description
                or f"Field {condition.field} violates rule {rule.name}: "
                f"expected {condition.operator.value} {expected_value}, "
                f"got {actual_value}"
            )

            return RuleViolation(
                rule_name=rule.name,
                field=condition.field,
                condition=condition,
                actual_value=actual_value,
                message=message,
                severity=rule.severity,
            )

        return None

    def _get_field_value(self, field_path: str, context: dict[str, Any]) -> Any:
        """Get field value from context using dot notation."""
        parts = field_path.split(".")
        value = context

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

            if value is None:
                break

        return value

    def get_rules_summary(self, tenant_id: Optional[str] = None) -> dict[str, Any]:
        """Get summary of registered rules."""
        total_rules = len(self.rules)
        active_rules = sum(1 for rule in self.rules.values() if rule.active)

        rules_by_severity = {}
        rules_by_group = {}

        for rule in self.rules.values():
            # Count by severity
            severity = rule.severity.value
            rules_by_severity[severity] = rules_by_severity.get(severity, 0) + 1

            # Count by group
            group = rule.rule_group or "default"
            rules_by_group[group] = rules_by_group.get(group, 0) + 1

        return {
            "total_rules": total_rules,
            "active_rules": active_rules,
            "inactive_rules": total_rules - active_rules,
            "rules_by_severity": rules_by_severity,
            "rules_by_group": rules_by_group,
            "rule_groups": list(self.rule_groups.keys()),
        }
