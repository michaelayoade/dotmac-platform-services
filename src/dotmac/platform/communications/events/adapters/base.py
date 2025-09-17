"""Base adapter interface and metadata."""


from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

from ..bus import EventBus

from dotmac.platform.observability.unified_logging import get_logger

__all__ = [
    "AdapterMetadata",
    "BaseAdapter",
    "AdapterConfig",
]

logger = get_logger(__name__)

@dataclass
class AdapterMetadata:
    """Metadata about an event bus adapter."""

    name: str
    version: str
    description: str
    supported_features: set[str]

    def supports(self, feature: str) -> bool:
        """Check if adapter supports a specific feature."""
        return feature in self.supported_features

@dataclass
class AdapterConfig:
    """Base configuration for event bus adapters."""

    # Common settings
    max_connections: int = 10
    connection_timeout: float = 30.0
    operation_timeout: float = 10.0

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0

    # Observability
    enable_metrics: bool = True
    enable_tracing: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "max_connections": self.max_connections,
            "connection_timeout": self.connection_timeout,
            "operation_timeout": self.operation_timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "enable_metrics": self.enable_metrics,
            "enable_tracing": self.enable_tracing,
        }

class BaseAdapter(EventBus, ABC):
    """
    Base class for event bus adapters.

    Provides common functionality and enforces the adapter interface.
    Concrete adapters should inherit from this class and implement
    the abstract methods.
    """

    def __init__(self, config: Optional[AdapterConfig] = None):
        """
        Initialize the adapter.

        Args:
            config: Adapter configuration
        """
        self.config = config or AdapterConfig()
        self._closed = False
        self._logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    @property
    @abstractmethod
    def metadata(self) -> AdapterMetadata:
        """Get adapter metadata."""
        ...

    @property
    def is_closed(self) -> bool:
        """Check if the adapter is closed."""
        return self._closed

    def _ensure_not_closed(self) -> None:
        """Ensure adapter is not closed."""
        if self._closed:
            raise RuntimeError(f"{self.metadata.name} adapter is closed")

    async def close(self) -> None:
        """Close the adapter and cleanup resources."""
        if not self._closed:
            await self._close_impl()
            self._closed = True
            self._logger.info(f"{self.metadata.name} adapter closed")

    @abstractmethod
    async def _close_impl(self) -> None:
        """Implement adapter-specific cleanup."""
        ...

    def __str__(self) -> str:
        """String representation."""
        return f"{self.metadata.name}Adapter(version={self.metadata.version})"

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"{self.__class__.__name__}("
            f"name='{self.metadata.name}', "
            f"version='{self.metadata.version}', "
            f"closed={self._closed})"
        )
