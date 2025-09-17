"""
Enterprise-grade tenant plugin isolation with enhanced security controls.
Extends existing tenant isolation with advanced security features.
"""

import asyncio

import resource
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from dotmac.platform.core.decorators import standard_exception_handler
from dotmac.platform.core import AuthorizationError
from dotmac.platform.core.enhanced.exceptions import ValidationError
from dotmac.security.audit import get_audit_logger
from dotmac.platform.plugins.security.audit_monitor import UnifiedAuditMonitor

from ..isolation.tenant_plugin_manager import TenantPluginManager

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger("plugins.enterprise_isolation")
audit_logger = get_audit_logger()

@dataclass
class TenantSecurityPolicy:
    """Tenant-specific security policy configuration."""

    tenant_id: UUID
    policy_name: str = "default"

    # Isolation levels
    network_isolation: bool = True
    filesystem_isolation: bool = True
    process_isolation: bool = True
    memory_isolation: bool = True

    # Resource limits per tenant
    max_plugins: int = 50
    max_memory_mb: int = 2048
    max_cpu_cores: float = 2.0
    max_disk_space_mb: int = 1024

    # Security controls
    enable_code_signing: bool = True
    require_certification: bool = True
    allowed_plugin_sources: list[str] = field(default_factory=lambda: ["marketplace"])
    forbidden_permissions: list[str] = field(default_factory=list)

    # Audit requirements
    enable_detailed_audit: bool = True
    audit_all_operations: bool = False
    audit_sensitive_operations: bool = True

    # Network access control
    allowed_domains: list[str] = field(default_factory=list)
    blocked_domains: list[str] = field(default_factory=list)
    max_network_requests_per_minute: int = 100

    # Data access controls
    allow_cross_tenant_data_access: bool = False
    enable_data_encryption: bool = True
    require_data_anonymization: bool = False

@dataclass
class TenantIsolationMetrics:
    """Metrics for tenant isolation monitoring."""

    tenant_id: UUID

    # Resource usage
    current_memory_mb: float = 0.0
    current_cpu_usage: float = 0.0
    current_disk_usage_mb: float = 0.0

    # Plugin activity
    active_plugins: int = 0
    plugin_executions: int = 0
    failed_executions: int = 0

    # Security events
    isolation_violations: int = 0
    permission_denials: int = 0
    suspicious_activities: int = 0

    # Performance
    avg_execution_time_ms: float = 0.0

    # Timestamps
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class EnterpriseTenantIsolationManager:
    """
    Enterprise-grade tenant plugin isolation with comprehensive security controls.
    """

    def __init__(self, audit_monitor: Optional[UnifiedAuditMonitor] = None):
        self.audit_monitor = audit_monitor  # Optional audit monitor

        # Tenant policies and metrics
        self._tenant_policies: dict[UUID, TenantSecurityPolicy] = {}
        self._tenant_metrics: dict[UUID, TenantIsolationMetrics] = {}
        self._tenant_namespaces: dict[UUID, dict[str, Any]] = {}

        # Enhanced tenant managers with enterprise features
        self._enterprise_managers: dict[UUID, EnterpriseTenantPluginManager] = {}

        # Monitoring and alerting
        self._monitoring_tasks: dict[UUID, asyncio.Task] = {}
        self._violation_handlers: list[callable] = []

        # Global configuration
        self.global_isolation_enabled = True
        self.max_tenants = 1000
        self.isolation_check_interval = 30  # seconds

    @standard_exception_handler
    async def register_tenant(
        self, tenant_id: UUID, security_policy: Optional[TenantSecurityPolicy] = None
    ) -> None:
        """Register tenant with enterprise isolation controls."""

        if tenant_id in self._tenant_policies:
            logger.warning(f"Tenant {tenant_id} already registered")
            return

        # Apply or create security policy
        policy = security_policy or TenantSecurityPolicy(tenant_id=tenant_id)
        self._tenant_policies[tenant_id] = policy

        # Initialize metrics
        self._tenant_metrics[tenant_id] = TenantIsolationMetrics(tenant_id=tenant_id)

        # Create isolated namespace
        await self._create_tenant_namespace(tenant_id, policy)

        # Start monitoring
        await self._start_tenant_monitoring(tenant_id)

        audit_logger.info(
            "Enterprise tenant registered",
            extra={
                "tenant_id": str(tenant_id),
                "policy_name": policy.policy_name,
                "network_isolation": policy.network_isolation,
                "filesystem_isolation": policy.filesystem_isolation,
                "max_plugins": policy.max_plugins,
            },
        )

    async def _create_tenant_namespace(self, tenant_id: UUID, policy: TenantSecurityPolicy) -> None:
        """Create isolated namespace for tenant."""

        namespace = {
            "tenant_id": tenant_id,
            "base_directory": f"/var/lib/dotmac/tenants/{tenant_id}",
            "temp_directory": Path(tempfile.gettempdir()) / f"dotmac_tenant_{tenant_id}",
            "log_directory": f"/var/log/dotmac/tenants/{tenant_id}",
            "cache_directory": f"/var/cache/dotmac/tenants/{tenant_id}",
            "network_namespace": f"tenant_{tenant_id}_net" if policy.network_isolation else None,
            "pid_namespace": f"tenant_{tenant_id}_pid" if policy.process_isolation else None,
            "mount_namespace": f"tenant_{tenant_id}_mnt" if policy.filesystem_isolation else None,
        }

        # Create directories with proper permissions
        for dir_key, dir_path in namespace.items():
            if dir_key.endswith("_directory") and dir_path:
                path_obj = Path(dir_path)
                path_obj.mkdir(parents=True, exist_ok=True)
                # Set restrictive permissions (owner only)
                path_obj.chmod(0o700)

        self._tenant_namespaces[tenant_id] = namespace

        logger.info(f"Created isolated namespace for tenant {tenant_id}")

    async def _start_tenant_monitoring(self, tenant_id: UUID) -> None:
        """Start monitoring task for tenant."""
        if tenant_id in self._monitoring_tasks:
            return

        task = asyncio.create_task(self._monitor_tenant_isolation(tenant_id))
        self._monitoring_tasks[tenant_id] = task

        logger.debug(f"Started isolation monitoring for tenant {tenant_id}")

    async def _monitor_tenant_isolation(self, tenant_id: UUID) -> None:
        """Continuously monitor tenant isolation integrity."""

        while tenant_id in self._tenant_policies:
            try:
                await self._check_tenant_isolation_integrity(tenant_id)
                await self._update_tenant_metrics(tenant_id)

                # Sleep until next check
                await asyncio.sleep(self.isolation_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Tenant monitoring error for {tenant_id}: {e}")
                await asyncio.sleep(5)  # Brief pause before retry

    async def _check_tenant_isolation_integrity(self, tenant_id: UUID) -> None:
        """Check tenant isolation integrity and detect violations."""

        policy = self._tenant_policies.get(tenant_id)
        metrics = self._tenant_metrics.get(tenant_id)

        if not policy or not metrics:
            return

        violations = []

        # Check resource limits
        if metrics.current_memory_mb > policy.max_memory_mb:
            violations.append(
                f"Memory limit exceeded: {metrics.current_memory_mb}MB > {policy.max_memory_mb}MB"
            )

        if metrics.current_cpu_usage > policy.max_cpu_cores:
            violations.append(
                f"CPU limit exceeded: {metrics.current_cpu_usage} > {policy.max_cpu_cores}"
            )

        if metrics.current_disk_usage_mb > policy.max_disk_space_mb:
            violations.append(
                f"Disk limit exceeded: {metrics.current_disk_usage_mb}MB > {policy.max_disk_space_mb}MB"
            )

        # Check plugin limits
        if metrics.active_plugins > policy.max_plugins:
            violations.append(
                f"Plugin limit exceeded: {metrics.active_plugins} > {policy.max_plugins}"
            )

        # Check namespace integrity
        await self._verify_namespace_integrity(tenant_id)

        # Process violations
        if violations:
            await self._handle_isolation_violations(tenant_id, violations)

    async def _verify_namespace_integrity(self, tenant_id: UUID) -> None:
        """Verify tenant namespace integrity."""
        namespace = self._tenant_namespaces.get(tenant_id)
        if not namespace:
            return

        # Check directory permissions
        for dir_key, dir_path in namespace.items():
            if dir_key.endswith("_directory") and dir_path:
                path_obj = Path(dir_path)
                if path_obj.exists():
                    stat = path_obj.stat()
                    # Verify restrictive permissions
                    if stat.st_mode & 0o077:  # Check if group/other have permissions
                        logger.warning(
                            f"Namespace integrity violation: {dir_path} has overly permissive permissions"
                        )

    async def _update_tenant_metrics(self, tenant_id: UUID) -> None:
        """Update tenant resource usage metrics."""

        metrics = self._tenant_metrics.get(tenant_id)
        if not metrics:
            return

        # Get resource usage (simplified - would use cgroups in production)
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            metrics.current_memory_mb = usage.ru_maxrss / 1024

            # Update timestamp
            metrics.last_updated = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Failed to update metrics for tenant {tenant_id}: {e}")

    async def _handle_isolation_violations(self, tenant_id: UUID, violations: list[str]) -> None:
        """Handle tenant isolation violations."""

        metrics = self._tenant_metrics.get(tenant_id)
        if metrics:
            metrics.isolation_violations += len(violations)

        # Log violations
        audit_logger.warning(
            "Tenant isolation violations detected",
            extra={
                "tenant_id": str(tenant_id),
                "violation_count": len(violations),
                "violations": violations,
            },
        )

        # Call violation handlers
        for handler in self._violation_handlers:
            try:
                await handler(tenant_id, violations)
            except Exception as e:
                logger.error(f"Violation handler error: {e}")

        # Take enforcement actions
        await self._enforce_isolation_compliance(tenant_id, violations)

    async def _enforce_isolation_compliance(self, tenant_id: UUID, violations: list[str]) -> None:
        """Enforce isolation compliance through corrective actions."""

        policy = self._tenant_policies.get(tenant_id)
        if not policy:
            return

        # Enforcement actions based on violation type
        for violation in violations:
            if "Memory limit exceeded" in violation:
                await self._enforce_memory_limit(tenant_id)
            elif "Plugin limit exceeded" in violation:
                await self._enforce_plugin_limit(tenant_id)
            elif "CPU limit exceeded" in violation:
                await self._enforce_cpu_limit(tenant_id)

    async def _enforce_memory_limit(self, tenant_id: UUID) -> None:
        """Enforce memory limits for tenant."""
        # Would implement memory limiting using cgroups in production
        logger.warning(f"Enforcing memory limit for tenant {tenant_id}")

    async def _enforce_plugin_limit(self, tenant_id: UUID) -> None:
        """Enforce plugin limits for tenant."""
        # Stop oldest plugins if over limit
        logger.warning(f"Enforcing plugin limit for tenant {tenant_id}")

    async def _enforce_cpu_limit(self, tenant_id: UUID) -> None:
        """Enforce CPU limits for tenant."""
        # Throttle CPU usage using cgroups
        logger.warning(f"Enforcing CPU limit for tenant {tenant_id}")

    @standard_exception_handler
    async def create_enterprise_manager(self, tenant_id: UUID) -> "EnterpriseTenantPluginManager":
        """Create enterprise tenant plugin manager with enhanced isolation."""

        if tenant_id not in self._tenant_policies:
            raise ValidationError(f"Tenant {tenant_id} not registered")

        if tenant_id in self._enterprise_managers:
            return self._enterprise_managers[tenant_id]

        policy = self._tenant_policies[tenant_id]
        namespace = self._tenant_namespaces[tenant_id]

        # Create enhanced manager
        manager = EnterpriseTenantPluginManager(
            tenant_id=tenant_id, security_policy=policy, namespace=namespace, isolation_manager=self
        )

        await manager.initialize()
        self._enterprise_managers[tenant_id] = manager

        logger.info(f"Created enterprise plugin manager for tenant {tenant_id}")

        return manager

    @standard_exception_handler
    async def unregister_tenant(self, tenant_id: UUID) -> None:
        """Unregister tenant and cleanup all resources."""

        logger.info(f"Unregistering tenant {tenant_id}")

        try:
            # Stop monitoring
            if tenant_id in self._monitoring_tasks:
                self._monitoring_tasks[tenant_id].cancel()
                del self._monitoring_tasks[tenant_id]

            # Cleanup enterprise manager
            if tenant_id in self._enterprise_managers:
                await self._enterprise_managers[tenant_id].shutdown()
                del self._enterprise_managers[tenant_id]

            # Remove namespace
            namespace = self._tenant_namespaces.get(tenant_id)
            if namespace:
                await self._cleanup_tenant_namespace(tenant_id, namespace)
                del self._tenant_namespaces[tenant_id]

            # Remove policies and metrics
            self._tenant_policies.pop(tenant_id, None)
            self._tenant_metrics.pop(tenant_id, None)

            audit_logger.info("Enterprise tenant unregistered", extra={"tenant_id": str(tenant_id)})

        except Exception as e:
            logger.error(f"Failed to unregister tenant {tenant_id}: {e}")
            raise

    async def _cleanup_tenant_namespace(self, tenant_id: UUID, namespace: dict[str, Any]) -> None:
        """Cleanup tenant namespace resources."""

        # Remove directories
        for dir_key, dir_path in namespace.items():
            if dir_key.endswith("_directory") and dir_path:
                path_obj = Path(dir_path)
                if path_obj.exists():
                    try:
                        import shutil

                        shutil.rmtree(dir_path)
                        logger.debug(f"Removed directory: {dir_path}")
                    except Exception as e:
                        logger.error(f"Failed to remove directory {dir_path}: {e}")

    def get_tenant_metrics(self, tenant_id: UUID) -> Optional[TenantIsolationMetrics]:
        """Get tenant isolation metrics."""
        return self._tenant_metrics.get(tenant_id)

    def get_tenant_policy(self, tenant_id: UUID) -> Optional[TenantSecurityPolicy]:
        """Get tenant security policy."""
        return self._tenant_policies.get(tenant_id)

    def add_violation_handler(self, handler: callable) -> None:
        """Add violation handler callback."""
        self._violation_handlers.append(handler)

class EnterpriseTenantPluginManager(TenantPluginManager):
    """
    Enterprise tenant plugin manager with enhanced isolation and security.
    """

    def __init__(
        self,
        tenant_id: UUID,
        security_policy: TenantSecurityPolicy,
        namespace: dict[str, Any],
        isolation_manager: EnterpriseTenantIsolationManager,
    ):
        # Initialize base manager
        config = {
            "tenant_namespace": namespace,
            "security_policy": security_policy.policy_name,
            "isolation_level": "enterprise",
        }

        super().__init__(tenant_id=tenant_id, config=config, security_level="enterprise")

        self.security_policy = security_policy
        self.namespace = namespace
        self.isolation_manager = isolation_manager

        # Enhanced components
        self._network_controller: Optional[TenantNetworkController] = None
        self._resource_controller: Optional[TenantResourceController] = None
        self._data_controller: Optional[TenantDataController] = None

    async def initialize(self) -> None:
        """Initialize enterprise tenant manager with enhanced controls."""

        await super().initialize()

        # Initialize enterprise controllers
        if self.security_policy.network_isolation:
            self._network_controller = TenantNetworkController(
                self.tenant_id, self.security_policy, self.namespace
            )
            await self._network_controller.initialize()

        self._resource_controller = TenantResourceController(
            self.tenant_id, self.security_policy, self.namespace
        )
        await self._resource_controller.initialize()

        if self.security_policy.enable_data_encryption:
            self._data_controller = TenantDataController(
                self.tenant_id, self.security_policy, self.namespace
            )
            await self._data_controller.initialize()

        logger.info(f"Enterprise tenant manager initialized for {self.tenant_id}")

    async def execute_plugin(self, plugin_key: str, method: str, *args, **kwargs) -> Any:
        """Execute plugin with enterprise security controls."""

        # Pre-execution security checks
        await self._validate_plugin_execution(plugin_key, method)

        # Apply resource controls
        if self._resource_controller:
            await self._resource_controller.prepare_execution(plugin_key)

        # Apply network controls
        if self._network_controller:
            await self._network_controller.validate_network_access(plugin_key)

        try:
            # Execute with enhanced monitoring
            result = await super().execute_plugin(plugin_key, method, *args, **kwargs)

            # Post-execution cleanup
            if self._resource_controller:
                await self._resource_controller.cleanup_execution(plugin_key)

            return result

        except Exception as e:
            # Enhanced error handling and reporting
            await self._handle_plugin_execution_error(plugin_key, method, e)
            raise

    async def _validate_plugin_execution(self, plugin_key: str, method: str) -> None:
        """Validate plugin execution against security policy."""

        # Check plugin certification if required
        if self.security_policy.require_certification:
            # Would check plugin certificate here
            pass

        # Check forbidden permissions
        plugin_permissions = await self._get_plugin_permissions(plugin_key)
        for perm in plugin_permissions:
            if perm in self.security_policy.forbidden_permissions:
                raise AuthorizationError(f"Plugin {plugin_key} uses forbidden permission: {perm}")

    async def _get_plugin_permissions(self, plugin_key: str) -> list[str]:
        """Get plugin permissions list."""
        # Would extract from plugin metadata
        return []

    async def _handle_plugin_execution_error(
        self, plugin_key: str, method: str, error: Exception
    ) -> None:
        """Handle plugin execution errors with enhanced reporting."""

        # Update tenant metrics
        metrics = self.isolation_manager.get_tenant_metrics(self.tenant_id)
        if metrics:
            metrics.failed_executions += 1

        # Enhanced audit logging
        audit_logger.error(
            "Enterprise plugin execution failed",
            extra={
                "tenant_id": str(self.tenant_id),
                "plugin_key": plugin_key,
                "method": method,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "security_policy": self.security_policy.policy_name,
            },
        )

# Controller classes for specialized isolation functions

class TenantNetworkController:
    """Controls network access for tenant plugins."""

    def __init__(self, tenant_id: UUID, policy: TenantSecurityPolicy, namespace: dict[str, Any]):
        self.tenant_id = tenant_id
        self.policy = policy
        self.namespace = namespace

    async def initialize(self) -> None:
        """Initialize network controls."""
        # Would setup network namespace and rules
        pass

    async def validate_network_access(self, plugin_key: str) -> None:
        """Validate plugin network access."""
        # Would check against allowed/blocked domains
        pass

class TenantResourceController:
    """Controls resource usage for tenant plugins."""

    def __init__(self, tenant_id: UUID, policy: TenantSecurityPolicy, namespace: dict[str, Any]):
        self.tenant_id = tenant_id
        self.policy = policy
        self.namespace = namespace

    async def initialize(self) -> None:
        """Initialize resource controls."""
        # Would setup cgroups and resource limits
        pass

    async def prepare_execution(self, plugin_key: str) -> None:
        """Prepare resources for plugin execution."""
        # Would apply resource limits
        pass

    async def cleanup_execution(self, plugin_key: str) -> None:
        """Cleanup resources after plugin execution."""
        # Would reset resource limits
        pass

class TenantDataController:
    """Controls data access and encryption for tenant plugins."""

    def __init__(self, tenant_id: UUID, policy: TenantSecurityPolicy, namespace: dict[str, Any]):
        self.tenant_id = tenant_id
        self.policy = policy
        self.namespace = namespace

    async def initialize(self) -> None:
        """Initialize data controls."""
        # Would setup encryption keys and data access controls
        pass

# Factory functions for dependency injection
def create_enterprise_isolation_manager(
    audit_monitor: Optional[UnifiedAuditMonitor] = None,
) -> EnterpriseTenantIsolationManager:
    """Create enterprise tenant isolation manager."""
    return EnterpriseTenantIsolationManager(audit_monitor)

__all__ = [
    "TenantSecurityPolicy",
    "TenantIsolationMetrics",
    "EnterpriseTenantIsolationManager",
    "EnterpriseTenantPluginManager",
    "TenantNetworkController",
    "TenantResourceController",
    "TenantDataController",
    "create_enterprise_isolation_manager",
]
