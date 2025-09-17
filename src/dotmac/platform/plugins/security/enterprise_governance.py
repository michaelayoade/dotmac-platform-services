"""
Enterprise plugin governance tools with comprehensive policy management,
compliance monitoring, and automated enforcement.
"""

import asyncio

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from dotmac.platform.core.decorators import standard_exception_handler
from dotmac.platform.core.enhanced.exceptions import ValidationError
from dotmac.security.audit import get_audit_logger
from dotmac.platform.plugins.security.audit_monitor import UnifiedAuditMonitor

from .access_control_system import AccessControlManager
from .certification_system import PluginCertificationSystem
from .marketplace_validation_pipeline import MarketplaceValidationPipeline

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger("plugins.governance")
audit_logger = get_audit_logger()

class PolicyType(Enum):
    """Policy type enumeration."""

    SECURITY = "security"
    COMPLIANCE = "compliance"
    OPERATIONAL = "operational"
    BUSINESS = "business"

class EnforcementAction(Enum):
    """Policy enforcement actions."""

    LOG = "log"
    WARN = "warn"
    BLOCK = "block"
    QUARANTINE = "quarantine"
    REVOKE = "revoke"
    SUSPEND = "suspend"

class GovernanceLevel(Enum):
    """Governance levels for different environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    ENTERPRISE = "enterprise"

@dataclass
class GovernancePolicy:
    """Governance policy definition."""

    policy_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""

    # Policy details
    policy_type: PolicyType = PolicyType.SECURITY
    governance_level: GovernanceLevel = GovernanceLevel.PRODUCTION

    # Rules and conditions
    rules: list[dict[str, Any]] = field(default_factory=list)
    conditions: dict[str, Any] = field(default_factory=dict)

    # Enforcement
    enforcement_action: EnforcementAction = EnforcementAction.LOG
    auto_enforce: bool = True

    # Scope
    applies_to_tenants: list[str] = field(default_factory=list)  # Empty = all tenants
    applies_to_plugin_types: list[str] = field(default_factory=list)  # Empty = all types

    # Metadata
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "1.0"

    # Status
    active: bool = True
    mandatory: bool = False

    def applies_to_tenant(self, tenant_id: UUID) -> bool:
        """Check if policy applies to tenant."""
        if not self.applies_to_tenants:
            return True
        return str(tenant_id) in self.applies_to_tenants

    def applies_to_plugin(self, plugin_metadata: dict[str, Any]) -> bool:
        """Check if policy applies to plugin."""
        if not self.applies_to_plugin_types:
            return True

        plugin_type = plugin_metadata.get("type", "")
        return plugin_type in self.applies_to_plugin_types

@dataclass
class PolicyViolation:
    """Policy violation record."""

    violation_id: str = field(default_factory=lambda: str(uuid4()))
    policy_id: str = ""

    # Violation details
    tenant_id: Optional[UUID] = None
    plugin_id: str = ""
    violation_type: str = ""
    severity: str = "medium"  # "low", "medium", "high", "critical"
    description: str = ""

    # Context
    context: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)

    # Status
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: str = ""

    # Enforcement
    enforcement_taken: Optional[EnforcementAction] = None
    enforcement_details: dict[str, Any] = field(default_factory=dict)

@dataclass
class ComplianceReport:
    """Compliance assessment report."""

    report_id: str = field(default_factory=lambda: str(uuid4()))
    tenant_id: Optional[UUID] = None

    # Report scope
    assessment_period_start: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) - timedelta(days=30)
    )
    assessment_period_end: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Compliance metrics
    total_plugins: int = 0
    compliant_plugins: int = 0
    non_compliant_plugins: int = 0
    compliance_score: float = 0.0  # 0-100

    # Violations summary
    total_violations: int = 0
    critical_violations: int = 0
    high_violations: int = 0
    medium_violations: int = 0
    low_violations: int = 0

    # Policy compliance
    policy_compliance: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Recommendations
    recommendations: list[str] = field(default_factory=list)
    action_items: list[dict[str, Any]] = field(default_factory=list)

    # Generation metadata
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    generated_by: str = ""

class EnterprisePluginGovernanceSystem:
    """
    Comprehensive enterprise plugin governance with policy management,
    compliance monitoring, and automated enforcement.
    """

    def __init__(
        self,
        access_control_system: Optional[AccessControlManager] = None,
        certification_system: Optional[PluginCertificationSystem] = None,
        validation_pipeline: Optional[MarketplaceValidationPipeline] = None,
        audit_monitor: Optional[UnifiedAuditMonitor] = None,
    ):
        # Core systems integration
        self.access_control = access_control_system
        self.certification = certification_system
        self.validation_pipeline = validation_pipeline
        self.audit_monitor = audit_monitor  # Optional audit monitor

        # Governance storage
        self._policies: dict[str, GovernancePolicy] = {}
        self._violations: dict[str, PolicyViolation] = {}
        self._compliance_reports: dict[str, ComplianceReport] = {}

        # Monitoring and enforcement
        self._monitoring_tasks: dict[UUID, asyncio.Task] = {}
        self._enforcement_handlers: dict[EnforcementAction, callable] = {}

        # Configuration
        self.monitoring_interval_seconds = 300  # 5 minutes
        self.compliance_assessment_interval_hours = 24
        self.auto_remediation_enabled = True

        # Initialize built-in policies
        self._initialize_default_policies()

        # Setup enforcement handlers
        self._setup_enforcement_handlers()

    def _initialize_default_policies(self) -> None:
        """Initialize default governance policies."""

        default_policies = [
            # Security policies
            GovernancePolicy(
                policy_id="security_scan_required",
                name="Security Scan Required",
                description="All plugins must pass security scanning before deployment",
                policy_type=PolicyType.SECURITY,
                governance_level=GovernanceLevel.PRODUCTION,
                rules=[
                    {"condition": "security_scan_status", "operator": "equals", "value": "passed"}
                ],
                enforcement_action=EnforcementAction.BLOCK,
                mandatory=True,
            ),
            GovernancePolicy(
                policy_id="certification_required",
                name="Plugin Certification Required",
                description="Plugins must be certified before production use",
                policy_type=PolicyType.SECURITY,
                governance_level=GovernanceLevel.PRODUCTION,
                rules=[
                    {
                        "condition": "certification_status",
                        "operator": "in",
                        "value": ["certified", "trusted"],
                    }
                ],
                enforcement_action=EnforcementAction.BLOCK,
                mandatory=True,
            ),
            GovernancePolicy(
                policy_id="resource_limits",
                name="Resource Usage Limits",
                description="Plugins must stay within resource usage limits",
                policy_type=PolicyType.OPERATIONAL,
                rules=[
                    {"condition": "memory_usage_mb", "operator": "less_than", "value": 512},
                    {"condition": "cpu_usage_percent", "operator": "less_than", "value": 50},
                ],
                enforcement_action=EnforcementAction.WARN,
            ),
            # Compliance policies
            GovernancePolicy(
                policy_id="data_privacy_compliance",
                name="Data Privacy Compliance",
                description="Plugins handling personal data must comply with privacy regulations",
                policy_type=PolicyType.COMPLIANCE,
                governance_level=GovernanceLevel.ENTERPRISE,
                rules=[
                    {
                        "condition": "handles_personal_data",
                        "operator": "equals",
                        "value": True,
                        "requires": [
                            {
                                "condition": "privacy_audit_passed",
                                "operator": "equals",
                                "value": True,
                            },
                            {
                                "condition": "data_encryption_enabled",
                                "operator": "equals",
                                "value": True,
                            },
                        ],
                    }
                ],
                enforcement_action=EnforcementAction.QUARANTINE,
                mandatory=True,
            ),
            GovernancePolicy(
                policy_id="audit_logging_required",
                name="Audit Logging Required",
                description="Enterprise plugins must implement comprehensive audit logging",
                policy_type=PolicyType.COMPLIANCE,
                governance_level=GovernanceLevel.ENTERPRISE,
                rules=[
                    {"condition": "audit_logging_implemented", "operator": "equals", "value": True}
                ],
                enforcement_action=EnforcementAction.BLOCK,
            ),
            # Business policies
            GovernancePolicy(
                policy_id="license_compliance",
                name="License Compliance",
                description="Plugins must use approved licenses",
                policy_type=PolicyType.BUSINESS,
                rules=[
                    {
                        "condition": "license_type",
                        "operator": "in",
                        "value": ["MIT", "Apache-2.0", "BSD-3-Clause", "Proprietary"],
                    }
                ],
                enforcement_action=EnforcementAction.WARN,
            ),
        ]

        for policy in default_policies:
            self._policies[policy.policy_id] = policy

        logger.info(f"Initialized {len(default_policies)} default governance policies")

    def _setup_enforcement_handlers(self) -> None:
        """Setup enforcement action handlers."""

        self._enforcement_handlers = {
            EnforcementAction.LOG: self._handle_log_enforcement,
            EnforcementAction.WARN: self._handle_warn_enforcement,
            EnforcementAction.BLOCK: self._handle_block_enforcement,
            EnforcementAction.QUARANTINE: self._handle_quarantine_enforcement,
            EnforcementAction.REVOKE: self._handle_revoke_enforcement,
            EnforcementAction.SUSPEND: self._handle_suspend_enforcement,
        }

    @standard_exception_handler
    async def create_policy(self, policy: GovernancePolicy) -> str:
        """Create new governance policy."""

        if policy.policy_id in self._policies:
            raise ValidationError(f"Policy already exists: {policy.policy_id}")

        # Validate policy rules
        await self._validate_policy_rules(policy)

        self._policies[policy.policy_id] = policy

        audit_logger.info(
            "Governance policy created",
            extra={
                "policy_id": policy.policy_id,
                "name": policy.name,
                "policy_type": policy.policy_type.value,
                "governance_level": policy.governance_level.value,
                "enforcement_action": policy.enforcement_action.value,
                "created_by": policy.created_by,
            },
        )

        return policy.policy_id

    async def _validate_policy_rules(self, policy: GovernancePolicy) -> None:
        """Validate policy rules syntax and logic."""

        for rule in policy.rules:
            if "condition" not in rule:
                raise ValidationError("Policy rule missing 'condition' field")

            if "operator" not in rule:
                raise ValidationError("Policy rule missing 'operator' field")

            # Validate operators
            valid_operators = [
                "equals",
                "not_equals",
                "in",
                "not_in",
                "greater_than",
                "less_than",
                "contains",
            ]
            if rule["operator"] not in valid_operators:
                raise ValidationError(f"Invalid operator: {rule['operator']}")

    @standard_exception_handler
    async def evaluate_plugin_compliance(
        self,
        plugin_id: str,
        plugin_metadata: dict[str, Any],
        tenant_id: Optional[UUID] = None,
        governance_level: Optional[GovernanceLevel] = None,
    ) -> list[PolicyViolation]:
        """Evaluate plugin compliance against governance policies."""

        violations = []
        applicable_policies = self._get_applicable_policies(
            tenant_id=tenant_id, plugin_metadata=plugin_metadata, governance_level=governance_level
        )

        for policy in applicable_policies:
            try:
                policy_violations = await self._evaluate_policy_compliance(
                    policy, plugin_id, plugin_metadata, tenant_id
                )
                violations.extend(policy_violations)

            except Exception as e:
                logger.error(f"Error evaluating policy {policy.policy_id}: {e}")

                # Create error violation
                error_violation = PolicyViolation(
                    policy_id=policy.policy_id,
                    tenant_id=tenant_id,
                    plugin_id=plugin_id,
                    violation_type="policy_evaluation_error",
                    severity="high",
                    description=f"Policy evaluation failed: {e}",
                    context={"error": str(e)},
                )
                violations.append(error_violation)

        # Store violations
        for violation in violations:
            self._violations[violation.violation_id] = violation

        audit_logger.info(
            "Plugin compliance evaluated",
            extra={
                "plugin_id": plugin_id,
                "tenant_id": str(tenant_id) if tenant_id else None,
                "policies_evaluated": len(applicable_policies),
                "violations_found": len(violations),
            },
        )

        return violations

    def _get_applicable_policies(
        self,
        tenant_id: Optional[UUID] = None,
        plugin_metadata: Optional[dict[str, Any]] = None,
        governance_level: Optional[GovernanceLevel] = None,
    ) -> list[GovernancePolicy]:
        """Get policies applicable to the given context."""

        applicable_policies = []

        for policy in self._policies.values():
            if not policy.active:
                continue

            # Check governance level
            if governance_level and policy.governance_level != governance_level:
                # Allow lower levels to apply higher policies
                level_hierarchy = {
                    GovernanceLevel.DEVELOPMENT: 0,
                    GovernanceLevel.TESTING: 1,
                    GovernanceLevel.STAGING: 2,
                    GovernanceLevel.PRODUCTION: 3,
                    GovernanceLevel.ENTERPRISE: 4,
                }

                if level_hierarchy.get(governance_level, 0) < level_hierarchy.get(
                    policy.governance_level, 0
                ):
                    continue

            # Check tenant applicability
            if tenant_id and not policy.applies_to_tenant(tenant_id):
                continue

            # Check plugin applicability
            if plugin_metadata and not policy.applies_to_plugin(plugin_metadata):
                continue

            applicable_policies.append(policy)

        return applicable_policies

    async def _evaluate_policy_compliance(
        self,
        policy: GovernancePolicy,
        plugin_id: str,
        plugin_metadata: dict[str, Any],
        tenant_id: Optional[UUID],
    ) -> list[PolicyViolation]:
        """Evaluate plugin against specific policy."""

        violations = []

        for rule in policy.rules:
            violation = await self._evaluate_rule(
                rule, policy, plugin_id, plugin_metadata, tenant_id
            )
            if violation:
                violations.append(violation)

        return violations

    async def _evaluate_rule(
        self,
        rule: dict[str, Any],
        policy: GovernancePolicy,
        plugin_id: str,
        plugin_metadata: dict[str, Any],
        tenant_id: Optional[UUID],
    ) -> Optional[PolicyViolation]:
        """Evaluate individual policy rule."""

        condition = rule["condition"]
        operator = rule["operator"]
        expected_value = rule["value"]

        # Get actual value from plugin context
        actual_value = await self._get_plugin_condition_value(
            condition, plugin_id, plugin_metadata, tenant_id
        )

        # Evaluate condition
        if not self._evaluate_condition(actual_value, operator, expected_value):
            # Check nested requirements
            if "requires" in rule:
                for sub_rule in rule["requires"]:
                    sub_violation = await self._evaluate_rule(
                        sub_rule, policy, plugin_id, plugin_metadata, tenant_id
                    )
                    if sub_violation:
                        return sub_violation

            # Create violation
            return PolicyViolation(
                policy_id=policy.policy_id,
                tenant_id=tenant_id,
                plugin_id=plugin_id,
                violation_type=f"rule_{condition}",
                severity=self._get_violation_severity(policy),
                description=f"Policy rule violated: {condition} {operator} {expected_value}, got {actual_value}",
                context={
                    "rule": rule,
                    "actual_value": actual_value,
                    "expected_value": expected_value,
                },
                evidence={
                    "plugin_metadata": plugin_metadata,
                    "condition": condition,
                    "operator": operator,
                },
            )

        return None

    async def _get_plugin_condition_value(
        self,
        condition: str,
        plugin_id: str,
        plugin_metadata: dict[str, Any],
        tenant_id: Optional[UUID],
    ) -> Any:
        """Get actual value for condition from plugin context."""

        # Check plugin metadata first
        if condition in plugin_metadata:
            return plugin_metadata[condition]

        # Dynamic value resolution based on condition type
        if condition == "security_scan_status":
            # Would integrate with security scanner
            return "passed"  # Placeholder

        elif condition == "certification_status":
            # Would check certification system
            if self.certification:
                cert = self.certification.get_active_certificate(plugin_id)
                return "certified" if cert and not cert.revoked else "uncertified"
            return "uncertified"

        elif condition == "memory_usage_mb":
            # Would get from monitoring system
            return 256  # Placeholder

        elif condition == "cpu_usage_percent":
            # Would get from monitoring system
            return 25  # Placeholder

        elif condition == "handles_personal_data":
            # Check if plugin handles personal data
            return plugin_metadata.get("data_types", {}).get("personal", False)

        elif condition == "privacy_audit_passed":
            # Check privacy audit status
            return plugin_metadata.get("audits", {}).get("privacy_audit", False)

        elif condition == "data_encryption_enabled":
            # Check encryption configuration
            return plugin_metadata.get("security", {}).get("encryption_enabled", False)

        elif condition == "audit_logging_implemented":
            # Check audit logging implementation
            return plugin_metadata.get("features", {}).get("audit_logging", False)

        elif condition == "license_type":
            return plugin_metadata.get("license", "Unknown")

        # Default: look in plugin metadata with dot notation
        keys = condition.split(".")
        value = plugin_metadata
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None

        return value

    def _evaluate_condition(self, actual_value: Any, operator: str, expected_value: Any) -> bool:
        """Evaluate condition with operator."""

        if operator == "equals":
            return actual_value == expected_value

        elif operator == "not_equals":
            return actual_value != expected_value

        elif operator == "in":
            return (
                actual_value in expected_value if isinstance(expected_value, (list, set)) else False
            )

        elif operator == "not_in":
            return (
                actual_value not in expected_value
                if isinstance(expected_value, (list, set))
                else True
            )

        elif operator == "greater_than":
            try:
                return float(actual_value) > float(expected_value)
            except (TypeError, ValueError):
                return False

        elif operator == "less_than":
            try:
                return float(actual_value) < float(expected_value)
            except (TypeError, ValueError):
                return False

        elif operator == "contains":
            return expected_value in str(actual_value) if actual_value else False

        return False

    def _get_violation_severity(self, policy: GovernancePolicy) -> str:
        """Determine violation severity based on policy."""

        if policy.mandatory or policy.enforcement_action == EnforcementAction.BLOCK:
            return "critical"
        elif policy.enforcement_action in [EnforcementAction.QUARANTINE, EnforcementAction.REVOKE]:
            return "high"
        elif policy.enforcement_action == EnforcementAction.SUSPEND:
            return "medium"
        else:
            return "low"

    @standard_exception_handler
    async def enforce_policy_violations(
        self,
        violations: list[PolicyViolation],
        auto_enforce: bool = True,
    ) -> dict[str, Any]:
        """Enforce policy violations with appropriate actions."""

        enforcement_results = {
            "total_violations": len(violations),
            "enforcements": [],
            "failures": [],
        }

        for violation in violations:
            try:
                policy = self._policies.get(violation.policy_id)
                if not policy:
                    continue

                # Skip if auto-enforcement disabled and policy requires it
                if not auto_enforce and policy.auto_enforce:
                    continue

                # Execute enforcement action
                handler = self._enforcement_handlers.get(policy.enforcement_action)
                if handler:
                    result = await handler(violation, policy)

                    # Update violation record
                    violation.enforcement_taken = policy.enforcement_action
                    violation.enforcement_details = result

                    enforcement_results["enforcements"].append(
                        {
                            "violation_id": violation.violation_id,
                            "action": policy.enforcement_action.value,
                            "result": result,
                        }
                    )

                    audit_logger.info(
                        "Policy enforcement executed",
                        extra={
                            "violation_id": violation.violation_id,
                            "policy_id": violation.policy_id,
                            "plugin_id": violation.plugin_id,
                            "action": policy.enforcement_action.value,
                            "result": result,
                        },
                    )

            except Exception as e:
                logger.error(f"Enforcement failed for violation {violation.violation_id}: {e}")
                enforcement_results["failures"].append(
                    {
                        "violation_id": violation.violation_id,
                        "error": str(e),
                    }
                )

        return enforcement_results

    # Enforcement handlers

    async def _handle_log_enforcement(
        self, violation: PolicyViolation, policy: GovernancePolicy
    ) -> dict[str, Any]:
        """Handle log enforcement action."""

        logger.warning(
            f"Policy violation detected: {violation.description}",
            extra={
                "policy_id": policy.policy_id,
                "plugin_id": violation.plugin_id,
                "violation_type": violation.violation_type,
            },
        )

        return {"action": "logged", "timestamp": datetime.now(timezone.utc).isoformat()}

    async def _handle_warn_enforcement(
        self, violation: PolicyViolation, policy: GovernancePolicy
    ) -> dict[str, Any]:
        """Handle warning enforcement action."""

        # Would send warning notification to administrators
        logger.warning(f"WARNING: {violation.description}")

        return {
            "action": "warning_sent",
            "recipients": ["admin@example.com"],  # Placeholder
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _handle_block_enforcement(
        self, violation: PolicyViolation, policy: GovernancePolicy
    ) -> dict[str, Any]:
        """Handle block enforcement action."""

        # Would prevent plugin execution/installation
        logger.error(f"BLOCKED: {violation.description}")

        # Integration with access control system
        if self.access_control and violation.tenant_id:
            # Would revoke plugin execution permissions
            pass

        return {
            "action": "blocked",
            "plugin_id": violation.plugin_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _handle_quarantine_enforcement(
        self, violation: PolicyViolation, policy: GovernancePolicy
    ) -> dict[str, Any]:
        """Handle quarantine enforcement action."""

        # Would isolate plugin in secure environment
        logger.critical(f"QUARANTINED: {violation.description}")

        return {
            "action": "quarantined",
            "plugin_id": violation.plugin_id,
            "quarantine_location": f"/quarantine/{violation.plugin_id}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _handle_revoke_enforcement(
        self, violation: PolicyViolation, policy: GovernancePolicy
    ) -> dict[str, Any]:
        """Handle revoke enforcement action."""

        # Would revoke plugin certificates/permissions
        logger.critical(f"REVOKED: {violation.description}")

        if self.certification and violation.plugin_id:
            # Would revoke plugin certificate
            pass

        return {
            "action": "revoked",
            "plugin_id": violation.plugin_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _handle_suspend_enforcement(
        self, violation: PolicyViolation, policy: GovernancePolicy
    ) -> dict[str, Any]:
        """Handle suspend enforcement action."""

        # Would temporarily suspend plugin
        logger.error(f"SUSPENDED: {violation.description}")

        return {
            "action": "suspended",
            "plugin_id": violation.plugin_id,
            "suspension_duration": "24h",  # Default suspension
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @standard_exception_handler
    async def generate_compliance_report(
        self,
        tenant_id: Optional[UUID] = None,
        assessment_period_days: int = 30,
    ) -> ComplianceReport:
        """Generate comprehensive compliance report."""

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=assessment_period_days)

        report = ComplianceReport(
            tenant_id=tenant_id,
            assessment_period_start=start_time,
            assessment_period_end=end_time,
        )

        # Get violations in period
        period_violations = [
            v
            for v in self._violations.values()
            if start_time <= v.detected_at <= end_time
            and (not tenant_id or v.tenant_id == tenant_id)
        ]

        # Calculate metrics
        report.total_violations = len(period_violations)
        report.critical_violations = len([v for v in period_violations if v.severity == "critical"])
        report.high_violations = len([v for v in period_violations if v.severity == "high"])
        report.medium_violations = len([v for v in period_violations if v.severity == "medium"])
        report.low_violations = len([v for v in period_violations if v.severity == "low"])

        # Get unique plugins
        plugin_ids = {v.plugin_id for v in period_violations}
        report.total_plugins = len(plugin_ids)

        # Calculate compliance score
        if report.total_plugins > 0:
            violation_weight = {
                "critical": 10,
                "high": 5,
                "medium": 2,
                "low": 1,
            }

            total_weight = sum(violation_weight.get(v.severity, 0) for v in period_violations)
            max_possible_weight = report.total_plugins * 10  # Assuming max critical violations

            report.compliance_score = max(
                0, 100 - (total_weight / max(max_possible_weight, 1)) * 100
            )
        else:
            report.compliance_score = 100.0

        # Policy-specific compliance
        for policy_id, policy in self._policies.items():
            policy_violations = [v for v in period_violations if v.policy_id == policy_id]

            report.policy_compliance[policy_id] = {
                "policy_name": policy.name,
                "violations": len(policy_violations),
                "compliance_rate": (
                    max(0, 100 - len(policy_violations)) if report.total_plugins > 0 else 100
                ),
            }

        # Generate recommendations
        report.recommendations = await self._generate_compliance_recommendations(
            report, period_violations
        )

        # Store report
        self._compliance_reports[report.report_id] = report

        audit_logger.info(
            "Compliance report generated",
            extra={
                "report_id": report.report_id,
                "tenant_id": str(tenant_id) if tenant_id else None,
                "compliance_score": report.compliance_score,
                "total_violations": report.total_violations,
                "assessment_period_days": assessment_period_days,
            },
        )

        return report

    async def _generate_compliance_recommendations(
        self,
        report: ComplianceReport,
        violations: list[PolicyViolation],
    ) -> list[str]:
        """Generate compliance recommendations based on violations."""

        recommendations = []

        # Critical violations
        if report.critical_violations > 0:
            recommendations.append(
                f"Address {report.critical_violations} critical violations immediately"
            )

        # High violation patterns
        if report.high_violations > 5:
            recommendations.append(
                "Consider implementing automated policy enforcement for high-severity violations"
            )

        # Compliance score
        if report.compliance_score < 80:
            recommendations.append(
                "Compliance score is below acceptable threshold (80%). Review and remediate violations."
            )

        # Policy-specific recommendations
        for policy_id, compliance_info in report.policy_compliance.items():
            if compliance_info["violations"] > 0:
                policy = self._policies.get(policy_id)
                if policy and policy.mandatory:
                    recommendations.append(
                        f"Mandatory policy '{policy.name}' has violations - immediate attention required"
                    )

        return recommendations

    # Query methods

    def get_policy(self, policy_id: str) -> Optional[GovernancePolicy]:
        """Get governance policy by ID."""
        return self._policies.get(policy_id)

    def list_policies(self, policy_type: Optional[PolicyType] = None) -> list[GovernancePolicy]:
        """List governance policies."""
        policies = list(self._policies.values())

        if policy_type:
            policies = [p for p in policies if p.policy_type == policy_type]

        return policies

    def get_violation(self, violation_id: str) -> Optional[PolicyViolation]:
        """Get policy violation by ID."""
        return self._violations.get(violation_id)

    def get_tenant_violations(self, tenant_id: UUID) -> list[PolicyViolation]:
        """Get violations for specific tenant."""
        return [v for v in self._violations.values() if v.tenant_id == tenant_id]

    def get_compliance_report(self, report_id: str) -> Optional[ComplianceReport]:
        """Get compliance report by ID."""
        return self._compliance_reports.get(report_id)

# Factory function for dependency injection
def create_enterprise_governance_system(
    access_control_system: Optional[AccessControlManager] = None,
    certification_system: Optional[PluginCertificationSystem] = None,
    validation_pipeline: Optional[MarketplaceValidationPipeline] = None,
    audit_monitor: Optional[UnifiedAuditMonitor] = None,
) -> EnterprisePluginGovernanceSystem:
    """Create enterprise plugin governance system."""
    return EnterprisePluginGovernanceSystem(
        access_control_system, certification_system, validation_pipeline, audit_monitor
    )

__all__ = [
    "PolicyType",
    "EnforcementAction",
    "GovernanceLevel",
    "GovernancePolicy",
    "PolicyViolation",
    "ComplianceReport",
    "EnterprisePluginGovernanceSystem",
    "create_enterprise_governance_system",
]
