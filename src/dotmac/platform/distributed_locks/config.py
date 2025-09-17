"""Configuration for Distributed Lock Manager."""

from typing import Optional
from pydantic import BaseModel, Field


class DistributedLockConfig(BaseModel):
    """Configuration for distributed lock management."""

    # Redis connection for lock storage
    redis_url: str = Field(
        "redis://localhost:6379/0",
        description="Redis URL for distributed lock storage"
    )

    # Lock settings
    default_timeout: float = Field(
        10.0,
        description="Default lock timeout in seconds"
    )

    default_blocking_timeout: Optional[float] = Field(
        None,
        description="Default blocking timeout in seconds (None for non-blocking)"
    )

    # Auto-renewal settings
    auto_renewal_enabled: bool = Field(
        True,
        description="Enable automatic lock renewal"
    )

    renewal_interval: float = Field(
        3.0,
        description="Renewal interval in seconds"
    )

    renewal_threshold: float = Field(
        0.3,
        description="Renew when TTL drops below this fraction of timeout"
    )

    # Deadlock detection
    deadlock_detection_enabled: bool = Field(
        True,
        description="Enable deadlock detection"
    )

    deadlock_check_interval: float = Field(
        1.0,
        description="Deadlock check interval in seconds"
    )

    max_wait_time: float = Field(
        30.0,
        description="Maximum wait time for deadlock detection"
    )

    # Fair queueing
    fair_queueing_enabled: bool = Field(
        True,
        description="Enable fair queueing for lock acquisition"
    )

    queue_timeout: float = Field(
        60.0,
        description="Timeout for queue entries in seconds"
    )

    # Performance settings
    max_retries: int = Field(
        5,
        description="Maximum retries for lock operations"
    )

    retry_delay: float = Field(
        0.1,
        description="Base delay between retries in seconds"
    )

    backoff_multiplier: float = Field(
        2.0,
        description="Backoff multiplier for retry delays"
    )

    # Monitoring and observability
    metrics_enabled: bool = Field(
        True,
        description="Enable lock metrics collection"
    )

    slow_lock_threshold: float = Field(
        5.0,
        description="Threshold for logging slow lock operations"
    )


class LockSecurityConfig(BaseModel):
    """Security configuration for distributed locks."""

    # Access control
    require_authentication: bool = Field(
        True,
        description="Require authentication for lock operations"
    )

    tenant_isolation: bool = Field(
        True,
        description="Enable tenant isolation for locks"
    )

    # Rate limiting
    rate_limiting_enabled: bool = Field(
        True,
        description="Enable rate limiting for lock operations"
    )

    max_locks_per_minute: int = Field(
        100,
        description="Maximum lock operations per minute per client"
    )

    max_concurrent_locks: int = Field(
        50,
        description="Maximum concurrent locks per client"
    )


__all__ = ["DistributedLockConfig", "LockSecurityConfig"]