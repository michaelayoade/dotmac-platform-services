"""API Gateway provider-agnostic interfaces."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from pydantic import BaseModel, Field


class RateLimitAlgorithm(str, Enum):
    """Rate limiting algorithms."""

    TOKEN_BUCKET = "token_bucket"  # nosec B105 - Not a password, just an algorithm name
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"


class VersioningStrategy(str, Enum):
    """API versioning strategies."""

    HEADER = "header"
    PATH = "path"
    QUERY = "query"
    ACCEPT_HEADER = "accept_header"


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool
    remaining: int
    reset_at: datetime
    retry_after: Optional[int] = None  # Seconds until retry


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""

    requests_per_minute: int = Field(default=60, gt=0)
    requests_per_hour: Optional[int] = Field(default=None, gt=0)
    requests_per_day: Optional[int] = Field(default=None, gt=0)
    burst_size: int = Field(default=10, gt=0)
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET

    class Config:
        use_enum_values = True


class APIVersion(BaseModel):
    """API version information."""

    version: str
    deprecated: bool = False
    sunset_date: Optional[datetime] = None
    min_version: Optional[str] = None
    max_version: Optional[str] = None


class RateLimiter(ABC):
    """Abstract base class for rate limiters."""

    @abstractmethod
    async def check_limit(self, identifier: str, resource: Optional[str] = None) -> RateLimitResult:
        """Check if request is within rate limits."""
        pass

    @abstractmethod
    async def consume(
        self, identifier: str, tokens: int = 1, resource: Optional[str] = None
    ) -> bool:
        """Consume tokens from the rate limit."""
        pass

    @abstractmethod
    async def reset(self, identifier: str, resource: Optional[str] = None) -> None:
        """Reset rate limit for an identifier."""
        pass

    @abstractmethod
    async def get_usage(self, identifier: str, resource: Optional[str] = None) -> Dict[str, Any]:
        """Get current usage statistics."""
        pass


class VersionStrategy(ABC):
    """Abstract base class for API versioning strategies."""

    @abstractmethod
    def extract_version(self, request: Any) -> Optional[str]:
        """Extract API version from request."""
        pass

    @abstractmethod
    def inject_version(self, response: Any, version: str) -> None:
        """Inject version information into response."""
        pass

    @abstractmethod
    def is_supported(self, version: str) -> bool:
        """Check if version is supported."""
        pass

    @abstractmethod
    def get_deprecation_info(self, version: str) -> Optional[Dict[str, Any]]:
        """Get deprecation information for a version."""
        pass


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker(ABC):
    """Abstract base class for circuit breakers."""

    @abstractmethod
    async def call(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute function with circuit breaker protection."""
        pass

    @abstractmethod
    def get_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        pass

    @abstractmethod
    async def reset(self) -> None:
        """Reset circuit breaker."""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        pass


class RequestValidator(ABC):
    """Abstract base class for request validation."""

    @abstractmethod
    async def validate(self, request: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate incoming request.

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    @abstractmethod
    def get_schema(self, endpoint: str, method: str) -> Dict[str, Any]:
        """Get validation schema for endpoint."""
        pass
