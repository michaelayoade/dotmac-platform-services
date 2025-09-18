"""
Data models for service registry.
"""

from datetime import datetime, UTC
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ServiceStatus(str, Enum):
    """Service health status."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    STARTING = "starting"
    STOPPING = "stopping"
    UNKNOWN = "unknown"


class ServiceHealth(BaseModel):
    """Service health information."""

    status: str
    latency_ms: Optional[float] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    error_rate: Optional[float] = None
    request_count: Optional[int] = None
    details: dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ServiceInfo(BaseModel):
    """Service registration information."""

    id: str
    name: str
    version: str
    host: str
    port: int
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    health_check_url: str
    status: ServiceStatus = ServiceStatus.UNKNOWN
    health: Optional[ServiceHealth] = None
    registered_at: datetime
    last_heartbeat: datetime
    weight: int = Field(default=100, description="Load balancing weight")
    region: Optional[str] = None
    zone: Optional[str] = None