"""
Plugin security models and data structures.
"""


class PluginPermissions:
    """Plugin permission system following RBAC patterns."""

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
            permissions: dict mapping permission categories to allowed operations
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
                raise ValueError(f"Invalid permission category: {category}")

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
    """Resource limits for plugin execution."""

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
