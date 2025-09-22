from dotmac.platform.logging import get_logger

"""
Secure plugin execution sandbox.
"""

import asyncio
import os
import platform
import resource
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

import structlog

from .models import PluginPermissions, ResourceLimits

logger = get_logger(__name__)

class SecurityError(Exception):
    """Security-related error."""

    pass

class PluginSecurityError(SecurityError):
    """Plugin security related error."""

    pass

class PluginExecutionError(SecurityError):
    """Plugin execution error."""

    pass

class PluginSandbox:
    """Secure plugin execution sandbox with isolation."""

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
        logger.info("Setting up sandbox", plugin_id=self.plugin_id)

        try:
            # Create isolated temporary directory with restricted permissions
            self._temp_dir = Path(tempfile.mkdtemp(prefix=f"secure_plugin_{self.plugin_id}_"))

            # Set restrictive permissions (owner only)
            os.chmod(self._temp_dir, 0o700)

            self._execution_stats["start_time"] = datetime.now(timezone.utc)
            logger.info("Secure sandbox setup complete", plugin_id=self.plugin_id)

        except Exception as e:
            logger.error("Sandbox setup failed", plugin_id=self.plugin_id, error=str(e))
            raise PluginSecurityError(f"Sandbox setup failed: {e}") from e

    async def cleanup(self) -> None:
        """Cleanup sandbox resources."""
        logger.info("Cleaning up sandbox", plugin_id=self.plugin_id)

        try:
            # Record end time
            self._execution_stats["end_time"] = datetime.now(timezone.utc)

            # Remove temporary directory
            if self._temp_dir and self._temp_dir.exists():
                shutil.rmtree(self._temp_dir, ignore_errors=True)

            logger.info("Secure sandbox cleanup complete", plugin_id=self.plugin_id)

        except Exception as e:
            logger.error("Sandbox cleanup error", plugin_id=self.plugin_id, error=str(e))

    def check_permission(self, category: str, operation: str) -> bool:
        """Check if plugin has permission for operation."""
        has_perm = self.permissions.has_permission(category, operation)

        if not has_perm:
            logger.warning(
                "Permission denied",
                plugin_id=self.plugin_id,
                category=category,
                operation=operation,
            )

        return has_perm

    def get_temp_directory(self) -> Path:
        """Get plugin's temporary directory."""
        if not self._temp_dir:
            raise PluginSecurityError("Sandbox not initialized")
        return self._temp_dir

    async def execute_in_subprocess(
        self, code: str, timeout: Optional[float] = None, env_vars: Optional[dict[str, str]] = None
    ) -> Any:
        """Execute code in an isolated subprocess with proper resource limits."""
        timeout = timeout or self.resource_limits.max_execution_time_seconds

        if not self._temp_dir:
            raise SecurityError("Sandbox not initialized")

        # Create a secure environment
        secure_env = self._create_secure_environment(env_vars or {})

        # Write code to temp file in sandbox
        code_file = self._temp_dir / "plugin_code.py"
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(code)

        # Set up the subprocess command with resource limits
        cmd = [sys.executable, str(code_file)]

        try:
            # Use subprocess with proper isolation
            proc = subprocess.Popen(
                cmd,
                cwd=str(self._temp_dir),  # Working directory is sandbox temp dir
                env=secure_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=(
                    self._setup_subprocess_limits if platform.system() != "Windows" else None
                ),
            )

            # Wait with timeout
            stdout, stderr = proc.communicate(timeout=timeout)

            if proc.returncode != 0:
                raise PluginExecutionError(f"Plugin execution failed: {stderr.decode()}")

            return {
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "return_code": proc.returncode,
            }

        except subprocess.TimeoutExpired:
            proc.kill()
            logger.error("Plugin execution timeout", plugin_id=self.plugin_id, timeout=timeout)
            raise PluginExecutionError(f"Plugin execution timeout after {timeout}s")
        except Exception as e:
            logger.error("Plugin execution error", plugin_id=self.plugin_id, error=str(e))
            raise PluginExecutionError(f"Plugin execution failed: {e}") from e

    def _setup_subprocess_limits(self) -> None:
        """Setup resource limits for subprocess (POSIX only)."""
        try:
            # Memory limit
            memory_bytes = self.resource_limits.max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))

            # CPU time limit
            cpu_time = self.resource_limits.max_cpu_time_seconds
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_time, cpu_time))

            # File size limit
            file_size_bytes = self.resource_limits.max_file_size_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_FSIZE, (file_size_bytes, file_size_bytes))

            # Number of open files
            max_files = getattr(self.resource_limits, "max_open_files", 64)
            resource.setrlimit(resource.RLIMIT_NOFILE, (max_files, max_files))

            # Number of processes
            max_procs = getattr(self.resource_limits, "max_processes", 8)
            resource.setrlimit(resource.RLIMIT_NPROC, (max_procs, max_procs))

            logger.debug("Applied subprocess resource limits", plugin_id=self.plugin_id)

        except Exception as e:
            logger.error(
                "Failed to apply subprocess resource limits", plugin_id=self.plugin_id, error=str(e)
            )
            # Don't raise - degrade gracefully on unsupported platforms

    def _create_secure_environment(self, additional_env: dict[str, str]) -> dict[str, str]:
        """Create a minimal, secure environment for plugin execution."""
        # Start with minimal environment
        secure_env = {
            "PATH": "/usr/bin:/bin",  # Minimal PATH
            "HOME": str(self._temp_dir),  # Home is sandbox
            "TMPDIR": str(self._temp_dir),  # Temp is sandbox
            "USER": "sandbox",
            "LANG": "en_US.UTF-8",
            "LC_ALL": "en_US.UTF-8",
        }

        # Add Python-specific variables
        secure_env.update(
            {
                "PYTHONPATH": str(self._temp_dir),
                "PYTHONHOME": "",  # Disable to use system Python
                "PYTHONDONTWRITEBYTECODE": "1",  # Don't create .pyc files
                "PYTHONUNBUFFERED": "1",  # Unbuffered output
            }
        )

        # Filter and add additional environment variables
        allowed_keys = {"PLUGIN_CONFIG", "PLUGIN_DATA", "TENANT_ID"}
        for key, value in additional_env.items():
            if key in allowed_keys and isinstance(value, str) and len(value) < 1000:
                secure_env[key] = value

        return secure_env
