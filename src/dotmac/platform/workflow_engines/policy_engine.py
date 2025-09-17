"""
Policy Engine for enforcing business policies and compliance rules.
"""


from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Dict, List

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

class PolicyAction(str, Enum):
    """Policy enforcement actions."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    LOG_WARNING = "log_warning"
    CONDITIONAL = "conditional"

class PolicyScope(str, Enum):
    """Policy scope levels."""

    GLOBAL = "global"
    TENANT = "tenant"
    USER = "user"
    ROLE = "role"
    WORKFLOW = "workflow"

@dataclass
class PolicyCondition:
    """A policy condition."""

    field: str
    operator: str
    value: Any
    description: Optional[str] = None

@dataclass
class Policy:
    """A business policy definition."""

    name: str
    description: str
    scope: PolicyScope
    action: PolicyAction
    conditions: List[PolicyCondition] = field(default_factory=list)
    priority: int = 0  # Higher number = higher priority
    active: bool = True
    requires_approval_from: Optional[List[str]] = None  # Roles that can approve
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PolicyResult:
    """Result of policy evaluation."""

    allowed: bool
    action: PolicyAction
    policy_name: str
    reason: Optional[str] = None
    requires_approval: bool = False
    approval_roles: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "allowed": self.allowed,
            "action": self.action.value,
            "policy_name": self.policy_name,
            "reason": self.reason,
            "requires_approval": self.requires_approval,
            "approval_roles": self.approval_roles,
            "metadata": self.metadata,
        }

class PolicyEvaluator(ABC):
    """Base class for custom policy evaluators."""

    @abstractmethod
    async def evaluate(
        self,
        policy: Policy,
        context: dict[str, Any],
        tenant_id: str,
    ) -> PolicyResult:
        """Evaluate a policy."""
        pass

class PolicyEngine:
    """Engine for enforcing business policies."""

    def __init__(self):
        self.policies: Dict[str, Policy] = {}
        self.custom_evaluators: Dict[str, PolicyEvaluator] = {}

        # Cache for frequently evaluated policies
        self._policy_cache: Dict[str, PolicyResult] = {}

    def register_policy(self, policy: Policy):
        """Register a business policy."""
        self.policies[policy.name] = policy

    def register_evaluator(self, name: str, evaluator: PolicyEvaluator):
        """Register a custom policy evaluator."""
        self.custom_evaluators[name] = evaluator

    async def check_workflow_policies(
        self,
        workflow_type: str,
        context: Dict[str, Any],
        tenant_id: str,
    ) -> PolicyResult:
        """Check policies for workflow execution."""
        applicable_policies = self._get_applicable_policies(
            PolicyScope.WORKFLOW, workflow_type, context, tenant_id
        )

        # Sort by priority (highest first)
        applicable_policies.sort(key=lambda p: p.priority, reverse=True)

        # Evaluate policies in priority order
        for policy in applicable_policies:
            result = await self._evaluate_policy(policy, context, tenant_id)

            # Return first policy that denies or requires approval
            if result.action in [PolicyAction.DENY, PolicyAction.REQUIRE_APPROVAL]:
                return result

        # If no policies deny, allow by default
        return PolicyResult(
            allowed=True,
            action=PolicyAction.ALLOW,
            policy_name="default",
            reason="No restrictive policies found",
        )

    async def evaluate_policy(
        self,
        policy_name: str,
        context: Dict[str, Any],
        tenant_id: str,
    ) -> PolicyResult:
        """Evaluate a specific policy."""
        if policy_name not in self.policies:
            return PolicyResult(
                allowed=False,
                action=PolicyAction.DENY,
                policy_name=policy_name,
                reason=f"Policy not found: {policy_name}",
            )

        policy = self.policies[policy_name]
        return await self._evaluate_policy(policy, context, tenant_id)

    async def check_user_permissions(
        self,
        user_id: str,
        action: str,
        resource: str,
        context: Dict[str, Any],
        tenant_id: str,
    ) -> PolicyResult:
        """Check user permissions for an action on a resource."""
        # Build permission context
        permission_context = {
            **context,
            "user_id": user_id,
            "action": action,
            "resource": resource,
        }

        # Get applicable user and role policies
        applicable_policies: List[Policy] = []

        # User-specific policies
        user_policies = self._get_applicable_policies(
            PolicyScope.USER, user_id, permission_context, tenant_id
        )
        applicable_policies.extend(user_policies)

        # Role-based policies (if user roles are in context)
        if "user_roles" in context:
            for role in context["user_roles"]:
                role_policies = self._get_applicable_policies(
                    PolicyScope.ROLE, role, permission_context, tenant_id
                )
                applicable_policies.extend(role_policies)

        # Evaluate policies
        return await self._evaluate_policies(applicable_policies, permission_context, tenant_id)

    async def check_resource_policies(
        self,
        resource_type: str,
        resource_id: str,
        action: str,
        context: Dict[str, Any],
        tenant_id: str,
    ) -> PolicyResult:
        """Check policies for resource access."""
        resource_context = {
            **context,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
        }

        # Get applicable policies
        applicable_policies = self._get_applicable_policies(
            PolicyScope.GLOBAL, resource_type, resource_context, tenant_id
        )

        return await self._evaluate_policies(applicable_policies, resource_context, tenant_id)

    def _get_applicable_policies(
        self,
        scope: PolicyScope,
        target: str,
        context: Dict[str, Any],
        tenant_id: str,
    ) -> List[Policy]:
        """Get policies applicable to the given scope and target."""
        applicable: List[Policy] = []

        for policy in self.policies.values():
            if not policy.active:
                continue

            # Check scope
            if policy.scope != scope and policy.scope != PolicyScope.GLOBAL:
                continue

            # Check tenant specificity
            if policy.scope == PolicyScope.TENANT:
                policy_tenant = policy.metadata.get("tenant_id")
                if policy_tenant and policy_tenant != tenant_id:
                    continue

            # Check if policy applies to this target
            if self._policy_applies_to_target(policy, target, context):
                applicable.append(policy)

        return applicable

    def _policy_applies_to_target(
        self,
        policy: Policy,
        target: str,
        context: Dict[str, Any],
    ) -> bool:
        """Check if policy applies to the target."""
        # Check metadata for target matching
        if "targets" in policy.metadata:
            targets = policy.metadata["targets"]
            if isinstance(targets, list):
                return target in targets or "*" in targets
            else:
                return target == targets or targets == "*"

        # If no specific targets, policy applies to all
        return True

    async def _evaluate_policies(
        self,
        policies: List[Policy],
        context: Dict[str, Any],
        tenant_id: str,
    ) -> PolicyResult:
        """Evaluate multiple policies."""
        # Sort by priority
        policies.sort(key=lambda p: p.priority, reverse=True)

        for policy in policies:
            result = await self._evaluate_policy(policy, context, tenant_id)

            # Return first restrictive result
            if result.action in [PolicyAction.DENY, PolicyAction.REQUIRE_APPROVAL]:
                return result

        # Allow if no restrictive policies
        return PolicyResult(
            allowed=True,
            action=PolicyAction.ALLOW,
            policy_name="default",
            reason="No restrictive policies found",
        )

    async def _evaluate_policy(
        self,
        policy: Policy,
        context: Dict[str, Any],
        tenant_id: str,
    ) -> PolicyResult:
        """Evaluate a single policy."""
        try:
            # Check for custom evaluator
            evaluator_name = policy.metadata.get("evaluator")
            if evaluator_name and evaluator_name in self.custom_evaluators:
                return await self.custom_evaluators[evaluator_name].evaluate(
                    policy, context, tenant_id
                )

            # Default condition-based evaluation
            return await self._evaluate_policy_conditions(policy, context)

        except Exception as e:
            logger.error(f"Error evaluating policy {policy.name}: {str(e)}")
            return PolicyResult(
                allowed=False,
                action=PolicyAction.DENY,
                policy_name=policy.name,
                reason=f"Policy evaluation error: {str(e)}",
            )

    async def _evaluate_policy_conditions(
        self,
        policy: Policy,
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate policy conditions."""
        # If no conditions, default behavior based on action
        if not policy.conditions:
            if policy.action == PolicyAction.ALLOW:
                return PolicyResult(
                    allowed=True,
                    action=PolicyAction.ALLOW,
                    policy_name=policy.name,
                    reason="Policy allows by default",
                )
            else:
                return PolicyResult(
                    allowed=False,
                    action=policy.action,
                    policy_name=policy.name,
                    reason="Policy denies by default",
                )

        # Evaluate all conditions (AND logic)
        all_conditions_met = True
        failed_conditions = []

        for condition in policy.conditions:
            if not self._evaluate_condition(condition, context):
                all_conditions_met = False
                failed_conditions.append(condition.field)

        # Determine result based on conditions
        if all_conditions_met:
            # Conditions met - apply policy action
            if policy.action == PolicyAction.ALLOW:
                return PolicyResult(
                    allowed=True,
                    action=PolicyAction.ALLOW,
                    policy_name=policy.name,
                    reason="All conditions met, policy allows",
                )
            elif policy.action == PolicyAction.REQUIRE_APPROVAL:
                return PolicyResult(
                    allowed=False,
                    action=PolicyAction.REQUIRE_APPROVAL,
                    policy_name=policy.name,
                    reason="Approval required by policy",
                    requires_approval=True,
                    approval_roles=policy.requires_approval_from or [],
                )
            else:
                return PolicyResult(
                    allowed=False,
                    action=policy.action,
                    policy_name=policy.name,
                    reason="Policy conditions met, action is restrictive",
                )
        else:
            # Conditions not met - opposite of policy action
            if policy.action == PolicyAction.DENY:
                return PolicyResult(
                    allowed=True,
                    action=PolicyAction.ALLOW,
                    policy_name=policy.name,
                    reason="Deny conditions not met, allowing",
                )
            else:
                return PolicyResult(
                    allowed=False,
                    action=PolicyAction.DENY,
                    policy_name=policy.name,
                    reason=f"Policy conditions not met for fields: {failed_conditions}",
                )

    def _evaluate_condition(
        self,
        condition: PolicyCondition,
        context: Dict[str, Any],
    ) -> bool:
        """Evaluate a single policy condition."""
        actual_value = self._get_field_value(condition.field, context)
        expected_value = condition.value

        if condition.operator == "equals":
            return actual_value == expected_value
        elif condition.operator == "not_equals":
            return actual_value != expected_value
        elif condition.operator == "greater_than":
            return actual_value > expected_value
        elif condition.operator == "less_than":
            return actual_value < expected_value
        elif condition.operator == "contains":
            return expected_value in str(actual_value)
        elif condition.operator == "in":
            return actual_value in expected_value
        elif condition.operator == "exists":
            return actual_value is not None
        else:
            logger.warning(f"Unknown operator: {condition.operator}")
            return False

    def _get_field_value(self, field_path: str, context: Dict[str, Any]) -> Any:
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

    def get_policies_summary(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of registered policies."""
        total_policies = len(self.policies)
        active_policies = sum(1 for policy in self.policies.values() if policy.active)

        policies_by_action = {}
        policies_by_scope = {}

        for policy in self.policies.values():
            # Count by action
            action = policy.action.value
            policies_by_action[action] = policies_by_action.get(action, 0) + 1

            # Count by scope
            scope = policy.scope.value
            policies_by_scope[scope] = policies_by_scope.get(scope, 0) + 1

        return {
            "total_policies": total_policies,
            "active_policies": active_policies,
            "inactive_policies": total_policies - active_policies,
            "policies_by_action": policies_by_action,
            "policies_by_scope": policies_by_scope,
        }
