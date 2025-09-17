"""
Comprehensive plugin security framework for DotMac platform.

This module provides enterprise-grade security features for plugin management:

- Advanced security scanning with threat detection
- Production-ready sandboxing with resource isolation
- Marketplace validation pipeline with automated testing
- Certificate-based code review and approval processes
- Multi-tenant isolation with enterprise controls
- Fine-grained access control and permissions (RBAC/ABAC)
- Policy-driven governance with automated enforcement
- Comprehensive audit logging with compliance support

All components follow DRY patterns and integrate with existing security infrastructure.
"""

from .audit_monitor import UnifiedAuditMonitor
from .access_control_system import (
    AccessControlEntry,
    AccessControlManager,
    AccessDecision,
    AccessRequest,
    ActionType,
    Permission,
    PermissionType,
    ResourceType,
    Role,
    create_plugin_access_control_system,
)
from .advanced_plugin_scanner import (
    AdvancedPluginSecurityScanner,
    PluginSecurityReport,
    SecurityThreat,
    create_advanced_plugin_scanner,
)
from .certification_system import (
    CodeReview,
    PluginCertificate,
    PluginCertificationSystem,
    ReviewComment,
    ReviewerLevel,
    ReviewStatus,
    create_certification_system,
)
from .enhanced_plugin_sandbox import (
    EnhancedPluginPermissions,
    EnterprisePluginSandbox,
    EnterprisePluginSandboxManager,
    EnterpriseResourceLimits,
    ResourceMonitor,
    SandboxMetrics,
    create_enterprise_sandbox_manager,
)
from .enterprise_governance import (
    ComplianceReport,
    EnforcementAction,
    EnterprisePluginGovernanceSystem,
    GovernanceLevel,
    GovernancePolicy,
    PolicyType,
    PolicyViolation,
    create_enterprise_governance_system,
)
from .enterprise_tenant_isolation import (
    EnterpriseTenantIsolationManager,
    EnterpriseTenantPluginManager,
    TenantIsolationMetrics,
    TenantSecurityPolicy,
    create_enterprise_isolation_manager,
)
from .marketplace_validation_pipeline import (
    CertificationLevel,
    MarketplaceValidationPipeline,
    PluginSubmission,
    ValidationRequirement,
    ValidationResult,
    ValidationStatus,
    create_marketplace_validation_pipeline,
)
from .plugin_audit_system import (
    AdvancedPluginAuditSystem,
    AuditChannel,
    AuditConfiguration,
    AuditEvent,
    AuditEventType,
    AuditLevel,
    AuditSession,
    create_plugin_audit_system,
)

__all__ = [
    # Access Control System
    "ActionType",
    "AccessControlEntry",
    "AccessDecision",
    "AccessRequest",
    "Permission",
    "PermissionType",
    "AccessControlManager",
    "ResourceType",
    "Role",
    "create_plugin_access_control_system",
    # Advanced Scanner
    "AdvancedPluginSecurityScanner",
    "PluginSecurityReport",
    "SecurityThreat",
    "create_advanced_plugin_scanner",
    # Certification System
    "CodeReview",
    "PluginCertificate",
    "PluginCertificationSystem",
    "ReviewComment",
    "ReviewStatus",
    "ReviewerLevel",
    "create_certification_system",
    # Enhanced Sandbox
    "EnhancedPluginPermissions",
    "EnterprisePluginSandbox",
    "EnterprisePluginSandboxManager",
    "EnterpriseResourceLimits",
    "ResourceMonitor",
    "SandboxMetrics",
    "create_enterprise_sandbox_manager",
    # Enterprise Governance
    "ComplianceReport",
    "EnforcementAction",
    "EnterprisePluginGovernanceSystem",
    "GovernanceLevel",
    "GovernancePolicy",
    "PolicyType",
    "PolicyViolation",
    "create_enterprise_governance_system",
    # Tenant Isolation
    "EnterpriseTenantIsolationManager",
    "EnterpriseTenantPluginManager",
    "TenantIsolationMetrics",
    "TenantSecurityPolicy",
    "create_enterprise_isolation_manager",
    # Validation Pipeline
    "CertificationLevel",
    "MarketplaceValidationPipeline",
    "PluginSubmission",
    "ValidationRequirement",
    "ValidationResult",
    "ValidationStatus",
    "create_marketplace_validation_pipeline",
    # Audit System
    "AdvancedPluginAuditSystem",
    "AuditChannel",
    "AuditConfiguration",
    "AuditEvent",
    "AuditEventType",
    "AuditLevel",
    "AuditSession",
    "create_plugin_audit_system",
    "UnifiedAuditMonitor",
]


# Integration helper functions


def create_integrated_security_framework(
    enable_advanced_scanning: bool = True,
    enable_enterprise_sandbox: bool = True,
    enable_marketplace_validation: bool = True,
    enable_certification: bool = True,
    enable_access_control: bool = True,
    enable_governance: bool = True,
    enable_tenant_isolation: bool = True,
    enable_audit_logging: bool = True,
) -> dict:
    """
    Create fully integrated plugin security framework.

    Returns dictionary with all security components configured and integrated.
    """

    components = {}

    # Core scanner
    if enable_advanced_scanning:
        components["scanner"] = create_advanced_plugin_scanner()

    # Enterprise sandbox
    if enable_enterprise_sandbox:
        components["sandbox_manager"] = create_enterprise_sandbox_manager()

    # Access control
    if enable_access_control:
        components["access_control"] = create_plugin_access_control_system()

    # Certification system
    if enable_certification:
        components["certification"] = create_certification_system()

    # Marketplace validation
    if enable_marketplace_validation:
        components["validation_pipeline"] = create_marketplace_validation_pipeline(
            scanner=components.get("scanner"),
            sandbox_manager=components.get("sandbox_manager"),
        )

    # Enterprise governance
    if enable_governance:
        components["governance"] = create_enterprise_governance_system(
            access_control_system=components.get("access_control"),
            certification_system=components.get("certification"),
            validation_pipeline=components.get("validation_pipeline"),
        )

    # Tenant isolation
    if enable_tenant_isolation:
        components["tenant_isolation"] = create_enterprise_isolation_manager()

    # Audit logging
    if enable_audit_logging:
        components["audit_system"] = create_plugin_audit_system()

    return components


__version__ = "1.0.0"
__author__ = "DotMac Platform Team"
__description__ = "Enterprise plugin security framework with comprehensive threat protection"
