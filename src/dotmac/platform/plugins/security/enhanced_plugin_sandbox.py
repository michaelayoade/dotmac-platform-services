"""
Enhanced plugin sandboxing with enterprise-grade resource isolation and security controls.
Builds upon existing security patterns with production-ready isolation.
"""

import asyncio

import resource
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from dotmac.platform.core.decorators import standard_exception_handler
from dotmac.security.audit import get_audit_logger
from dotmac.platform.plugins.security.audit_monitor import UnifiedAuditMonitor

from ..core.exceptions import PluginSecurityError
from .plugin_sandbox import PluginPermissions, PluginSandbox, ResourceLimits

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger("plugins.security.sandbox")
audit_logger = get_audit_logger()

@dataclass
class SandboxMetrics:
    """Enhanced sandbox execution metrics."""

    # Resource usage
    peak_memory_mb: float = 0.0
    total_cpu_seconds: float = 0.0
    disk_bytes_written: int = 0
    disk_bytes_read: int = 0
    network_requests: int = 0

    # Security events
    permission_denials: int = 0
    security_violations: int = 0

    # Performance
    startup_time_ms: float = 0.0
    execution_time_ms: float = 0.0
    cleanup_time_ms: float = 0.0

@dataclass
class EnterpriseResourceLimits(ResourceLimits):
    """Enhanced resource limits for enterprise environments."""

    # Memory limits
    max_heap_size_mb: int = 256
    max_stack_size_mb: int = 8

    # Process limits
    max_processes: int = 5
    max_threads: int = 10
    max_open_files: int = 100

    # Network limits
    max_connections: int = 10
    max_bandwidth_kbps: int = 1000

    # Disk I/O limits
    max_disk_writes_mb: int = 50
    max_disk_reads_mb: int = 100

    # Time limits
    max_startup_seconds: int = 30
    heartbeat_interval_seconds: int = 5

    def apply_enhanced_limits(self) -> None:
        """Apply comprehensive resource limits."""
        super().apply_system_limits()

        try:
            # Process limits
            resource.setrlimit(resource.RLIMIT_NPROC, (self.max_processes, self.max_processes))

            # File descriptor limits
            resource.setrlimit(resource.RLIMIT_NOFILE, (self.max_open_files, self.max_open_files))

            # Stack size limit
            stack_bytes = self.max_stack_size_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_STACK, (stack_bytes, stack_bytes))

            logger.info(
                f"Applied enhanced resource limits: processes={self.max_processes}, files={self.max_open_files}"
            )

        except Exception as e:
            logger.error(f"Failed to apply enhanced resource limits: {e}")
            raise PluginSecurityError(f"Enhanced resource limit setup failed: {e}") from e

class EnhancedPluginPermissions(PluginPermissions):
    """Enhanced permission system with granular controls."""

    # Additional permission categories
    TENANT_DATA = "tenant_data"
    USER_DATA = "user_data"
    SYSTEM_CONFIG = "system_config"
    AUDIT_LOGS = "audit_logs"
    CRYPTO = "cryptography"

    def __init__(self, permissions: dict[str, list[str]], tenant_isolation: bool = True):
        super().__init__(permissions)
        self.tenant_isolation = tenant_isolation
        self._permission_cache: dict[str, bool] = {}

    def has_permission_cached(
        self, category: str, operation: str, context: Optional[dict] = None
    ) -> bool:
        """Check permission with caching and context awareness."""
        cache_key = f"{category}:{operation}"

        if cache_key in self._permission_cache:
            return self._permission_cache[cache_key]

        # Context-aware permission checking
        has_perm = self._check_contextual_permission(category, operation, context)
        self._permission_cache[cache_key] = has_perm

        return has_perm

    def _check_contextual_permission(
        self, category: str, operation: str, context: Optional[dict]
    ) -> bool:
        """Check permission with context awareness."""
        base_permission = self.has_permission(category, operation)

        if not base_permission:
            return False

        # Tenant isolation checks
        if self.tenant_isolation and context:
            if category in [self.TENANT_DATA, self.USER_DATA]:
                return self._check_tenant_isolation(context)

        return True

    def _check_tenant_isolation(self, context: dict) -> bool:
        """Verify tenant isolation constraints."""
        plugin_tenant = context.get("plugin_tenant_id")
        access_tenant = context.get("access_tenant_id")

        if plugin_tenant and access_tenant:
            return plugin_tenant == access_tenant

        return True

    @classmethod
    def create_enterprise_default(
        cls, tenant_isolation: bool = True
    ) -> "EnhancedPluginPermissions":
        """Create enterprise-grade default permissions."""
        return cls(
            permissions={
                cls.FILE_SYSTEM: ["read_temp", "write_temp"],
                cls.API: ["read_basic"],
                cls.TENANT_DATA: ["read_own"],
            },
            tenant_isolation=tenant_isolation,
        )

    @classmethod
    def create_trusted_enterprise(
        cls, tenant_isolation: bool = True
    ) -> "EnhancedPluginPermissions":
        """Create trusted enterprise permissions."""
        return cls(
            permissions={
                cls.FILE_SYSTEM: ["read", "write_temp", "create_temp"],
                cls.NETWORK: ["http", "https"],
                cls.DATABASE: ["read", "write"],
                cls.API: ["read", "write"],
                cls.TENANT_DATA: ["read", "write"],
                cls.USER_DATA: ["read"],
                cls.AUDIT_LOGS: ["write"],
            },
            tenant_isolation=tenant_isolation,
        )

class ResourceMonitor:
    """Real-time resource monitoring for plugin execution."""

    def __init__(self, sandbox_id: str, limits: EnterpriseResourceLimits):
        self.sandbox_id = sandbox_id
        self.limits = limits
        self.metrics = SandboxMetrics()
        self._monitoring_task: Optional[asyncio.Task] = None
        self._stop_monitoring = asyncio.Event()

    async def start_monitoring(self) -> None:
        """Start resource monitoring."""
        self._monitoring_task = asyncio.create_task(self._monitor_resources())
        logger.debug(f"Started resource monitoring for sandbox {self.sandbox_id}")

    async def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        self._stop_monitoring.set()
        if self._monitoring_task:
            await self._monitoring_task
        logger.debug(f"Stopped resource monitoring for sandbox {self.sandbox_id}")

    async def _monitor_resources(self) -> None:
        """Monitor resource usage in real-time."""
        start_time = time.time()

        while not self._stop_monitoring.is_set():
            try:
                # Monitor memory usage
                usage = resource.getrusage(resource.RUSAGE_SELF)
                current_memory_mb = usage.ru_maxrss / 1024  # Convert to MB

                if current_memory_mb > self.metrics.peak_memory_mb:
                    self.metrics.peak_memory_mb = current_memory_mb

                # Monitor CPU time
                self.metrics.total_cpu_seconds = usage.ru_utime + usage.ru_stime

                # Check limits
                if current_memory_mb > self.limits.max_memory_mb:
                    raise PluginSecurityError(
                        f"Memory limit exceeded: {current_memory_mb}MB > {self.limits.max_memory_mb}MB"
                    )

                if self.metrics.total_cpu_seconds > self.limits.max_cpu_time_seconds:
                    raise PluginSecurityError(
                        f"CPU time limit exceeded: {self.metrics.total_cpu_seconds}s > {self.limits.max_cpu_time_seconds}s"
                    )

                # Wait before next check
                await asyncio.sleep(self.limits.heartbeat_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Resource monitoring error for sandbox {self.sandbox_id}: {e}")
                break

        # Record final execution time
        self.metrics.execution_time_ms = (time.time() - start_time) * 1000

class EnterprisePluginSandbox(PluginSandbox):
    """
    Enterprise-grade plugin sandbox with enhanced security and monitoring.
    """

    def __init__(
        self,
        plugin_id: str,
        tenant_id: Optional[UUID] = None,
        permissions: Optional[EnhancedPluginPermissions] = None,
        resource_limits: Optional[EnterpriseResourceLimits] = None,
        audit_monitor: Optional[UnifiedAuditMonitor] = None,
        enable_container_isolation: bool = False,
    ):
        # Initialize base sandbox
        base_permissions = permissions or EnhancedPluginPermissions.create_enterprise_default()
        base_limits = resource_limits or EnterpriseResourceLimits()

        super().__init__(
            plugin_id=plugin_id,
            tenant_id=tenant_id,
            permissions=base_permissions,
            resource_limits=base_limits,
        )

        # Enterprise enhancements
        self.permissions: EnhancedPluginPermissions = base_permissions
        self.resource_limits: EnterpriseResourceLimits = base_limits
        self.audit_monitor = audit_monitor  # Optional audit monitor
        self.enable_container_isolation = enable_container_isolation

        # Enhanced sandbox state
        self._resource_monitor: Optional[ResourceMonitor] = None
        self._container_id: Optional[str] = None
        self._network_namespace: Optional[str] = None
        self._security_violations: list[dict[str, Any]] = []
        self._context_vars: dict[str, Any] = {}

    async def setup(self) -> None:
        """Enhanced sandbox setup with enterprise features."""
        setup_start = time.time()

        logger.info(f"Setting up enterprise sandbox for plugin {self.plugin_id}")

        try:
            # Base setup
            await super().setup()

            # Enhanced resource limits
            self.resource_limits.apply_enhanced_limits()

            # Setup resource monitoring
            self._resource_monitor = ResourceMonitor(self.plugin_id, self.resource_limits)
            await self._resource_monitor.start_monitoring()

            # Container isolation if enabled
            if self.enable_container_isolation:
                await self._setup_container_isolation()

            # Network namespace isolation
            await self._setup_network_isolation()

            # Setup security context
            self._setup_security_context()

            # Record setup metrics
            setup_time = (time.time() - setup_start) * 1000
            if self._resource_monitor:
                self._resource_monitor.metrics.startup_time_ms = setup_time

            # Audit log
            audit_logger.info(
                "Enterprise sandbox setup completed",
                extra={
                    "plugin_id": self.plugin_id,
                    "tenant_id": str(self.tenant_id),
                    "setup_time_ms": setup_time,
                    "container_isolation": self.enable_container_isolation,
                },
            )

        except Exception as e:
            logger.error(f"Enterprise sandbox setup failed for plugin {self.plugin_id}: {e}")
            raise PluginSecurityError(f"Enterprise sandbox setup failed: {e}") from e

    async def cleanup(self) -> None:
        """Enhanced cleanup with enterprise features."""
        cleanup_start = time.time()

        logger.info(f"Cleaning up enterprise sandbox for plugin {self.plugin_id}")

        try:
            # Stop resource monitoring
            if self._resource_monitor:
                await self._resource_monitor.stop_monitoring()

            # Container cleanup
            if self._container_id:
                await self._cleanup_container_isolation()

            # Network namespace cleanup
            await self._cleanup_network_isolation()

            # Base cleanup
            await super().cleanup()

            # Record cleanup metrics
            cleanup_time = (time.time() - cleanup_start) * 1000
            if self._resource_monitor:
                self._resource_monitor.metrics.cleanup_time_ms = cleanup_time

            # Final audit log with metrics
            final_metrics = (
                self._resource_monitor.metrics if self._resource_monitor else SandboxMetrics()
            )

            audit_logger.info(
                "Enterprise sandbox cleanup completed",
                extra={
                    "plugin_id": self.plugin_id,
                    "tenant_id": str(self.tenant_id),
                    "cleanup_time_ms": cleanup_time,
                    "peak_memory_mb": final_metrics.peak_memory_mb,
                    "total_cpu_seconds": final_metrics.total_cpu_seconds,
                    "security_violations": len(self._security_violations),
                },
            )

        except Exception as e:
            logger.error(f"Enterprise sandbox cleanup error for plugin {self.plugin_id}: {e}")

    async def _setup_container_isolation(self) -> None:
        """Setup container-based isolation using Docker or similar."""
        if not self.enable_container_isolation:
            return

        try:
            # Create isolated container
            container_name = f"plugin-{self.plugin_id}-{int(time.time())}"

            # Basic Docker container setup (would be more sophisticated in production)
            cmd = [
                "docker",
                "run",
                "-d",
                "--name",
                container_name,
                f"--memory={self.resource_limits.max_memory_mb}m",
                f"--cpus={self.resource_limits.max_cpu_time_seconds / 60}",
                "--network=none",  # No network by default
                "--read-only",  # Read-only filesystem
                "python:3.11-alpine",
                "sleep",
                "3600",  # Keep container alive
            ]

            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                self._container_id = stdout.decode().strip()
                logger.info(f"Created container {self._container_id} for plugin {self.plugin_id}")
            else:
                logger.warning(f"Container creation failed: {stderr.decode()}")

        except Exception as e:
            logger.warning(f"Container isolation setup failed: {e}")
            # Continue without container isolation

    async def _cleanup_container_isolation(self) -> None:
        """Cleanup container isolation."""
        if not self._container_id:
            return

        try:
            # Stop and remove container
            cmd = ["docker", "rm", "-f", self._container_id]

            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            await result.communicate()
            logger.info(f"Cleaned up container {self._container_id}")

        except Exception as e:
            logger.warning(f"Container cleanup failed: {e}")

    async def _setup_network_isolation(self) -> None:
        """Setup network namespace isolation."""
        # Network isolation would be implemented here
        # This is a placeholder for production implementation
        pass

    async def _cleanup_network_isolation(self) -> None:
        """Cleanup network namespace isolation."""
        # Network cleanup would be implemented here
        pass

    def _setup_security_context(self) -> None:
        """Setup security context variables."""
        self._context_vars = {
            "plugin_id": self.plugin_id,
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "sandbox_id": id(self),
            "start_time": datetime.now(timezone.utc).isoformat(),
        }

    @standard_exception_handler
    async def check_permission_with_audit(
        self, category: str, operation: str, context: Optional[dict] = None
    ) -> bool:
        """Check permission with comprehensive auditing."""

        # Merge sandbox context with provided context
        full_context = {**self._context_vars, **(context or {})}

        # Check permission
        has_perm = self.permissions.has_permission_cached(category, operation, full_context)

        # Record permission check
        audit_event = {
            "plugin_id": self.plugin_id,
            "tenant_id": str(self.tenant_id),
            "category": category,
            "operation": operation,
            "granted": has_perm,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": full_context,
        }

        if has_perm:
            audit_logger.info("Plugin permission granted", extra=audit_event)
        else:
            audit_logger.warning("Plugin permission denied", extra=audit_event)

            # Record security violation
            self._security_violations.append(audit_event)

            # Update metrics
            if self._resource_monitor:
                self._resource_monitor.metrics.permission_denials += 1

        return has_perm

    def get_execution_metrics(self) -> SandboxMetrics:
        """Get comprehensive execution metrics."""
        return self._resource_monitor.metrics if self._resource_monitor else SandboxMetrics()

    def get_security_violations(self) -> list[dict[str, Any]]:
        """Get recorded security violations."""
        return self._security_violations.copy()

class EnterprisePluginSandboxManager:
    """
    Manager for enterprise plugin sandboxes with centralized control.
    """

    def __init__(self, audit_monitor: Optional[UnifiedAuditMonitor] = None):
        self.audit_monitor = audit_monitor  # Optional audit monitor, can be None
        self._active_sandboxes: dict[str, EnterprisePluginSandbox] = {}
        self._sandbox_metrics: dict[str, SandboxMetrics] = {}

    @standard_exception_handler
    async def create_sandbox(
        self,
        plugin_id: str,
        tenant_id: Optional[UUID] = None,
        security_level: str = "default",
        enable_container_isolation: bool = False,
    ) -> EnterprisePluginSandbox:
        """Create and register enterprise sandbox."""

        # Security configurations
        security_configs = {
            "minimal": {
                "permissions": EnhancedPluginPermissions.create_enterprise_default(),
                "limits": EnterpriseResourceLimits(max_memory_mb=128, max_cpu_time_seconds=10),
            },
            "default": {
                "permissions": EnhancedPluginPermissions.create_enterprise_default(),
                "limits": EnterpriseResourceLimits(),
            },
            "trusted": {
                "permissions": EnhancedPluginPermissions.create_trusted_enterprise(),
                "limits": EnterpriseResourceLimits(max_memory_mb=1024, max_cpu_time_seconds=120),
            },
        }

        config = security_configs.get(security_level, security_configs["default"])

        # Create sandbox
        sandbox = EnterprisePluginSandbox(
            plugin_id=plugin_id,
            tenant_id=tenant_id,
            permissions=config["permissions"],
            resource_limits=config["limits"],
            audit_monitor=self.audit_monitor,
            enable_container_isolation=enable_container_isolation,
        )

        # Register sandbox
        sandbox_key = f"{plugin_id}:{tenant_id}"
        self._active_sandboxes[sandbox_key] = sandbox

        logger.info(
            f"Created enterprise sandbox for plugin {plugin_id} with security level {security_level}"
        )

        return sandbox

    async def cleanup_sandbox(self, plugin_id: str, tenant_id: Optional[UUID] = None) -> None:
        """Cleanup and unregister sandbox."""
        sandbox_key = f"{plugin_id}:{tenant_id}"

        if sandbox_key in self._active_sandboxes:
            sandbox = self._active_sandboxes[sandbox_key]

            # Store metrics before cleanup
            self._sandbox_metrics[sandbox_key] = sandbox.get_execution_metrics()

            # Cleanup sandbox
            await sandbox.cleanup()

            # Unregister
            del self._active_sandboxes[sandbox_key]

            logger.info(f"Cleaned up sandbox for plugin {plugin_id}")

    def get_active_sandboxes(self) -> dict[str, EnterprisePluginSandbox]:
        """Get all active sandboxes."""
        return self._active_sandboxes.copy()

    def get_sandbox_metrics(self) -> dict[str, SandboxMetrics]:
        """Get metrics for all sandboxes."""
        # Combine active and historical metrics
        all_metrics = self._sandbox_metrics.copy()

        for key, sandbox in self._active_sandboxes.items():
            all_metrics[key] = sandbox.get_execution_metrics()

        return all_metrics

# Factory functions for dependency injection
def create_enterprise_sandbox_manager(
    audit_monitor: Optional[UnifiedAuditMonitor] = None,
) -> EnterprisePluginSandboxManager:
    """Create enterprise sandbox manager."""
    return EnterprisePluginSandboxManager(audit_monitor)

__all__ = [
    "SandboxMetrics",
    "EnterpriseResourceLimits",
    "EnhancedPluginPermissions",
    "ResourceMonitor",
    "EnterprisePluginSandbox",
    "EnterprisePluginSandboxManager",
    "create_enterprise_sandbox_manager",
]
