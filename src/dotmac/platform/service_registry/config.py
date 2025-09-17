"""Configuration for Service Registry."""

from typing import Optional
from pydantic import BaseModel, Field


class ServiceRegistryConfig(BaseModel):
    """Configuration for service registry and discovery."""

    # Redis connection for service registry
    redis_url: str = Field(
        "redis://localhost:6379/0",
        description="Redis URL for service registry storage"
    )

    # Service registration settings
    default_ttl: int = Field(
        60,
        description="Default TTL for service registrations in seconds"
    )

    health_check_interval: int = Field(
        30,
        description="Health check interval in seconds"
    )

    health_check_timeout: int = Field(
        5,
        description="Health check timeout in seconds"
    )

    # Service discovery settings
    max_retries: int = Field(
        3,
        description="Maximum retries for service discovery"
    )

    retry_delay: float = Field(
        1.0,
        description="Delay between retries in seconds"
    )

    # Load balancing settings
    load_balancing_strategy: str = Field(
        "round_robin",
        description="Load balancing strategy (round_robin, least_connections, random)"
    )

    # Cleanup settings
    cleanup_interval: int = Field(
        300,
        description="Cleanup interval for expired services in seconds"
    )


class ServiceHealthConfig(BaseModel):
    """Configuration for service health monitoring."""

    enabled: bool = Field(
        True,
        description="Enable service health monitoring"
    )

    check_interval: int = Field(
        30,
        description="Health check interval in seconds"
    )

    failure_threshold: int = Field(
        3,
        description="Number of consecutive failures before marking unhealthy"
    )

    recovery_threshold: int = Field(
        2,
        description="Number of consecutive successes before marking healthy"
    )

    timeout: int = Field(
        5,
        description="Health check timeout in seconds"
    )


__all__ = ["ServiceRegistryConfig", "ServiceHealthConfig"]