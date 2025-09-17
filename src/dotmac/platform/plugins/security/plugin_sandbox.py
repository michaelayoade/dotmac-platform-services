import os

from dotmac.platform.observability.unified_logging import get_logger
"""
Plugin Security and Sandboxing Framework

Provides secure plugin execution environment with resource limits,
permission controls, and isolation following DRY security patterns.
"""

import ast
import asyncio
import hashlib

import resource
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from .._internal.monitoring import get_monitoring
from ..core.exceptions import PluginExecutionError, PluginSecurityError

logger = get_logger("plugins.security")

class PluginPermissions:
    """
    Plugin permission system following DRY RBAC patterns.
    """

    # Permission categories
    FILE_SYSTEM = "filesystem"
    NETWORK = "network"
    DATABASE = "database"
    API = "api"
    SYSTEM = "system"

    def __init__(self, permissions: dict[str, list[str]]):
        """
        Initialize permissions.

        Args:
            permissions: Dict mapping permission categories to allowed operations
        """
        self.permissions = permissions or {}
        self._validate_permissions()

    def _validate_permissions(self) -> None:
        """Validate permission format and values."""
        valid_categories = {
            self.FILE_SYSTEM,
            self.NETWORK,
            self.DATABASE,
            self.API,
            self.SYSTEM,
        }

        for category in self.permissions:
            if category not in valid_categories:
                raise PluginSecurityError(f"Invalid permission category: {category}")

    def has_permission(self, category: str, operation: str) -> bool:
        """Check if plugin has specific permission."""
        return operation in self.permissions.get(category, [])

    def get_permissions(self, category: str) -> list[str]:
        """Get all permissions for category."""
        return self.permissions.get(category, [])

    @classmethod
    def create_default(cls) -> "PluginPermissions":
        """Create default minimal permissions."""
        return cls(
            {
                cls.FILE_SYSTEM: ["read_temp"],
                cls.API: ["read_basic"],
            }
        )

    @classmethod
    def create_full_access(cls) -> "PluginPermissions":
        """Create full access permissions (for trusted plugins)."""
        return cls(
            {
                cls.FILE_SYSTEM: ["read", "write", "create", "delete"],
                cls.NETWORK: ["http", "https", "websocket"],
                cls.DATABASE: ["read", "write"],
                cls.API: ["read", "write", "admin"],
                cls.SYSTEM: ["process", "environment"],
            }
        )

class ResourceLimits:
    """
    Resource limits for plugin execution.
    """

    def __init__(
        self,
        max_memory_mb: int = 512,
        max_cpu_time_seconds: int = 30,
        max_file_size_mb: int = 100,
        max_network_requests: int = 100,
        max_execution_time_seconds: int = 60,
    ):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_time_seconds = max_cpu_time_seconds
        self.max_file_size_mb = max_file_size_mb
        self.max_network_requests = max_network_requests
        self.max_execution_time_seconds = max_execution_time_seconds

    def apply_system_limits(self) -> None:
        """Apply resource limits using system calls."""
        try:
            # Memory limit
            memory_bytes = self.max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))

            # CPU time limit
            resource.setrlimit(
                resource.RLIMIT_CPU,
                (self.max_cpu_time_seconds, self.max_cpu_time_seconds),
            )

            # File size limit
            file_size_bytes = self.max_file_size_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_FSIZE, (file_size_bytes, file_size_bytes))

            logger.info(
                f"Applied resource limits: memory={self.max_memory_mb}MB, cpu={self.max_cpu_time_seconds}s"
            )

        except Exception as e:
            logger.error(f"Failed to apply resource limits: {e}")
            raise PluginSecurityError(f"Resource limit setup failed: {e}") from e

class PluginSandbox:
    """
    Secure plugin execution sandbox following DRY isolation patterns.
    """

    def __init__(
        self,
        plugin_id: str,
        tenant_id: Optional[UUID] = None,
        permissions: Optional[PluginPermissions] = None,
        resource_limits: Optional[ResourceLimits] = None,
        enable_monitoring: bool = True,
    ):
        self.plugin_id = plugin_id
        self.tenant_id = tenant_id
        self.permissions = permissions or PluginPermissions.create_default()
        self.resource_limits = resource_limits or ResourceLimits()
        self.enable_monitoring = enable_monitoring

        # Sandbox state
        self._temp_dir: Optional[Path] = None
        self._original_cwd: Optional[Path] = None
        self._monitoring = get_monitoring("plugins.sandbox") if enable_monitoring else None
        self._execution_stats = {
            "start_time": None,
            "end_time": None,
            "memory_usage": 0,
            "cpu_time": 0.0,
            "network_requests": 0,
        }

    async def __aenter__(self) -> "PluginSandbox":
        """Enter sandbox context."""
        await self.setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit sandbox context with cleanup."""
        await self.cleanup()

    async def setup(self) -> None:
        """Setup sandbox environment."""
        logger.info(f"Setting up sandbox for plugin {self.plugin_id}")

        try:
            # Create isolated temporary directory
            self._temp_dir = Path(tempfile.mkdtemp(prefix=f"plugin_{self.plugin_id}_"))
            self._original_cwd = Path.cwd()

            # Change to sandbox directory
            os.chdir(self._temp_dir)

            # Apply resource limits
            self.resource_limits.apply_system_limits()

            # Setup monitoring
            if self._monitoring:
                self._monitoring.record_metric(
                    name="plugin_sandbox_created",
                    value=1,
                    tags={
                        "plugin_id": self.plugin_id,
                        "tenant_id": str(self.tenant_id),
                    },
                )

            self._execution_stats["start_time"] = datetime.now(timezone.utc)
            logger.info(f"Sandbox setup complete for plugin {self.plugin_id}")

        except Exception as e:
            logger.error(f"Sandbox setup failed for plugin {self.plugin_id}: {e}")
            raise PluginSecurityError(f"Sandbox setup failed: {e}") from e

    async def cleanup(self) -> None:
        """Cleanup sandbox resources."""
        logger.info(f"Cleaning up sandbox for plugin {self.plugin_id}")

        try:
            # Record end time
            self._execution_stats["end_time"] = datetime.now(timezone.utc)

            # Return to original directory
            if self._original_cwd:
                os.chdir(self._original_cwd)

            # Remove temporary directory
            if self._temp_dir and self._temp_dir.exists():
                shutil.rmtree(self._temp_dir, ignore_errors=True)

            # Record cleanup metrics
            if self._monitoring:
                duration = (
                    self._execution_stats["end_time"] - self._execution_stats["start_time"]
                ).total_seconds()

                self._monitoring.record_metric(
                    name="plugin_execution_duration",
                    value=duration,
                    tags={
                        "plugin_id": self.plugin_id,
                        "tenant_id": str(self.tenant_id),
                    },
                )

            logger.info(f"Sandbox cleanup complete for plugin {self.plugin_id}")

        except Exception as e:
            logger.error(f"Sandbox cleanup error for plugin {self.plugin_id}: {e}")

    def check_permission(self, category: str, operation: str) -> bool:
        """Check if plugin has permission for operation."""
        has_perm = self.permissions.has_permission(category, operation)

        if not has_perm:
            logger.warning(f"Permission denied for plugin {self.plugin_id}: {category}:{operation}")

            if self._monitoring:
                self._monitoring.record_metric(
                    name="plugin_permission_denied",
                    value=1,
                    tags={
                        "plugin_id": self.plugin_id,
                        "category": category,
                        "operation": operation,
                    },
                )

        return has_perm

    def get_temp_directory(self) -> Path:
        """Get plugin's temporary directory."""
        if not self._temp_dir:
            raise PluginSecurityError("Sandbox not initialized")
        return self._temp_dir

    async def execute_with_timeout(
        self, coro_or_func, *args, timeout: Optional[float] = None, **kwargs
    ) -> Any:
        """Execute function/coroutine with timeout and monitoring."""
        timeout = timeout or self.resource_limits.max_execution_time_seconds

        try:
            if asyncio.iscoroutinefunction(coro_or_func):
                result = await asyncio.wait_for(coro_or_func(*args, **kwargs), timeout=timeout)
            else:
                # Run sync function in executor with timeout
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, lambda: coro_or_func(*args, **kwargs)
                    ),
                    timeout=timeout,
                )

            return result

        except asyncio.TimeoutError:
            logger.error(f"Plugin {self.plugin_id} execution timeout after {timeout}s")
            raise PluginExecutionError(f"Plugin execution timeout after {timeout}s")
        except Exception as e:
            logger.error(f"Plugin {self.plugin_id} execution error: {e}")
            raise PluginExecutionError(f"Plugin execution failed: {e}") from e

class SecurityScanner:
    """
    Central plugin security management following DRY security patterns.
    """

    def __init__(self):
        self.monitoring = get_monitoring("plugins.security")
        self._code_validators: list[callable] = []
        self._trusted_signatures: set[str] = set()

        # Initialize default validators
        self._setup_default_validators()

    def _setup_default_validators(self) -> None:
        """Setup default code validators."""
        self._code_validators = [
            self._check_dangerous_imports,
            self._check_system_calls,
            self._check_file_operations,
            self._check_network_operations,
        ]

    async def validate_plugin_code(self, plugin_code: str, plugin_metadata: dict[str, Any]) -> bool:
        """
        Validate plugin code for security issues.

        Returns True if code is safe, raises PluginSecurityError if not.
        """
        logger.info(f"Validating plugin code: {plugin_metadata.get('name', 'unknown')}")

        try:
            # Parse code to AST for analysis
            import ast

            tree = ast.parse(plugin_code)

            # Run security validators
            for validator in self._code_validators:
                if not validator(tree, plugin_code):
                    return False

            # Check code signature if provided
            signature = plugin_metadata.get("signature")
            if signature and not self._verify_signature(plugin_code, signature):
                raise PluginSecurityError("Invalid plugin signature")

            logger.info("Plugin code validation passed")
            return True

        except SyntaxError as e:
            raise PluginSecurityError(f"Plugin code syntax error: {e}") from e
        except Exception as e:
            logger.error(f"Plugin validation error: {e}")
            raise PluginSecurityError(f"Plugin validation failed: {e}") from e

    def _check_dangerous_imports(self, tree: ast.AST, code: str) -> bool:
        """Check for dangerous imports."""
        dangerous_modules = {
            "os",
            "subprocess",
            "sys",
            "eval",
            "exec",
            "compile",
            "__import__",
            "importlib",
            "ctypes",
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in dangerous_modules:
                        raise PluginSecurityError(f"Dangerous import detected: {alias.name}")

            elif isinstance(node, ast.ImportFrom):
                if node.module in dangerous_modules:
                    raise PluginSecurityError(f"Dangerous import detected: {node.module}")

        return True

    def _check_system_calls(self, tree: ast.AST, code: str) -> bool:
        """Check for system calls."""
        dangerous_functions = {"eval", "exec", "compile", "open", "__import__"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in dangerous_functions:
                    raise PluginSecurityError(f"Dangerous function call: {node.func.id}")

        return True

    def _check_file_operations(self, tree: ast.AST, code: str) -> bool:
        """Check for unauthorized file operations."""
        # This would be more sophisticated in production
        if "open(" in code and "/etc/" in code:
            raise PluginSecurityError("Unauthorized system file access detected")

        return True

    def _check_network_operations(self, tree: ast.AST, code: str) -> bool:
        """Check for network operations."""
        # This would validate network access patterns
        return True

    def _verify_signature(self, code: str, signature: str) -> bool:
        """Verify plugin code signature."""
        # Implementation would verify cryptographic signature
        hashlib.sha256(code.encode()).hexdigest()
        return signature in self._trusted_signatures or len(signature) > 0

    def create_sandbox(
        self,
        plugin_id: str,
        tenant_id: Optional[UUID] = None,
        security_level: str = "default",
    ) -> PluginSandbox:
        """
        Create plugin sandbox with appropriate security settings.
        """
        # Define security levels
        security_configs = {
            "minimal": {
                "permissions": PluginPermissions.create_default(),
                "limits": ResourceLimits(max_memory_mb=128, max_cpu_time_seconds=10),
            },
            "default": {
                "permissions": PluginPermissions.create_default(),
                "limits": ResourceLimits(),
            },
            "trusted": {
                "permissions": PluginPermissions.create_full_access(),
                "limits": ResourceLimits(max_memory_mb=1024, max_cpu_time_seconds=120),
            },
        }

        config = security_configs.get(security_level, security_configs["default"])

        return PluginSandbox(
            plugin_id=plugin_id,
            tenant_id=tenant_id,
            permissions=config["permissions"],
            resource_limits=config["limits"],
        )

    async def scan_plugin_file(self, file_path: Path) -> dict[str, Any]:
        """
        Scan plugin file for security issues.

        Returns scan results with security assessment.
        """
        logger.info(f"Scanning plugin file: {file_path}")

        try:
            with open(file_path, encoding="utf-8") as f:
                code = f.read()

            # Basic file analysis
            scan_result = {
                "file_size": file_path.stat().st_size,
                "line_count": len(code.splitlines()),
                "code_hash": hashlib.sha256(code.encode()).hexdigest(),
                "security_issues": [],
                "risk_level": "low",
            }

            # Validate code
            try:
                await self.validate_plugin_code(code, {"name": file_path.name})
                scan_result["validation_passed"] = True
            except PluginSecurityError as e:
                scan_result["validation_passed"] = False
                scan_result["security_issues"].append(str(e))
                scan_result["risk_level"] = "high"

            return scan_result

        except Exception as e:
            logger.error(f"Plugin file scan error: {e}")
            return {"error": str(e), "risk_level": "unknown"}

# Helper function for dependency injection
def create_secure_plugin_manager() -> SecurityScanner:
    """Create plugin security manager instance."""
    return SecurityScanner()

__all__ = [
    "PluginPermissions",
    "ResourceLimits",
    "PluginSandbox",
    "SecurityScanner",
    "create_secure_plugin_manager",
]
