from dotmac.platform.logging import get_logger

"""
Plugin security scanner and manager.
"""

import ast
import base64
import hashlib
import hmac
from pathlib import Path
from typing import Any, Optional, Set
from uuid import UUID

import structlog

from .models import PluginPermissions, ResourceLimits
from .sandbox import PluginSandbox, PluginSecurityError

logger = get_logger(__name__)

class SecurityScanner:
    """Central plugin security scanner."""

    def __init__(self, trusted_keys_file: Optional[Path] = None):
        self._code_validators: list[callable] = []
        self.trusted_signatures: set[str] = set()
        self.trusted_hashes: dict[str, str] = {}
        self.hmac_keys: dict[str, bytes] = {}

        # Load trusted keys if provided
        if trusted_keys_file and trusted_keys_file.exists():
            self._load_trusted_keys(trusted_keys_file)

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
        logger.info("Validating plugin code", plugin_name=plugin_metadata.get("name", "unknown"))

        try:
            # Parse code to AST for analysis
            tree = ast.parse(plugin_code)

            # Run security validators
            for validator in self._code_validators:
                if not validator(tree, plugin_code):
                    return False

            # Check code signature if provided
            signature = plugin_metadata.get("signature")
            if signature and not self._verify_signature(plugin_code, signature):
                raise PluginSecurityError("Invalid plugin signature")
            elif signature is None:
                logger.warning(
                    "No signature provided for plugin validation",
                    plugin_name=plugin_metadata.get("name", "unknown"),
                )

            logger.info("Plugin code validation passed")
            return True

        except SyntaxError as e:
            raise PluginSecurityError(f"Plugin code syntax error: {e}") from e
        except Exception as e:
            logger.error("Plugin validation error", error=str(e))
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

    def _load_trusted_keys(self, keys_file: Path) -> None:
        """Load trusted keys and signatures from file."""
        try:
            with open(keys_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    if ":" in line:
                        key_type, value = line.split(":", 1)
                        if key_type == "signature":
                            self.trusted_signatures.add(value)
                        elif key_type == "hash":
                            parts = value.split(",", 1)
                            if len(parts) == 2:
                                self.trusted_hashes[parts[0]] = parts[1]
                        elif key_type == "hmac_key":
                            parts = value.split(",", 1)
                            if len(parts) == 2:
                                self.hmac_keys[parts[0]] = base64.b64decode(parts[1])

            logger.info(
                "Loaded trusted keys",
                signatures_count=len(self.trusted_signatures),
                hashes_count=len(self.trusted_hashes),
                hmac_keys_count=len(self.hmac_keys),
            )

        except Exception as e:
            logger.error("Failed to load trusted keys", error=str(e))
            raise PluginSecurityError(f"Failed to load trusted keys: {e}") from e

    def _verify_signature(self, code: str, signature: str) -> bool:
        """Verify plugin code signature using multiple methods."""
        if not signature:
            logger.warning("No signature provided for verification")
            return False

        # Try different verification methods
        verification_methods = [
            self._verify_trusted_signature,
            self._verify_hash_signature,
            self._verify_hmac_signature,
        ]

        for method in verification_methods:
            try:
                if method(code, signature, {}):
                    logger.info("Signature verification successful", method=method.__name__)
                    return True
            except Exception as e:
                logger.debug(
                    "Signature verification method failed", method=method.__name__, error=str(e)
                )
                continue

        logger.warning("All signature verification methods failed")
        return False

    def _verify_trusted_signature(self, code: str, signature: str, metadata: dict) -> bool:
        """Verify against pre-trusted signatures."""
        return signature in self.trusted_signatures

    def _verify_hash_signature(self, code: str, signature: str, metadata: dict) -> bool:
        """Verify using SHA-256 hash whitelist."""
        # Calculate code hash
        code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()

        # Check if signature matches expected hash for this plugin
        plugin_name = metadata.get("name", "")
        expected_hash = self.trusted_hashes.get(plugin_name)

        if expected_hash and expected_hash == code_hash:
            return signature == code_hash

        return False

    def _verify_hmac_signature(self, code: str, signature: str, metadata: dict) -> bool:
        """Verify HMAC signature."""
        plugin_name = metadata.get("name", "")
        hmac_key = self.hmac_keys.get(plugin_name)

        if not hmac_key:
            return False

        try:
            # Calculate expected HMAC
            expected_hmac = hmac.new(hmac_key, code.encode("utf-8"), hashlib.sha256).hexdigest()

            # Compare with provided signature
            return hmac.compare_digest(expected_hmac, signature)

        except Exception as e:
            logger.debug("HMAC verification failed", error=str(e))
            return False

    def create_sandbox(
        self,
        plugin_id: str,
        tenant_id: Optional[UUID] = None,
        security_level: str = "default",
    ) -> PluginSandbox:
        """Create plugin sandbox with appropriate security settings."""
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
        logger.info("Scanning plugin file", file_path=str(file_path))

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
            logger.error("Plugin file scan error", error=str(e))
            return {"error": str(e), "risk_level": "unknown"}
