"""Configuration for Audit Trail Aggregator."""

from typing import Optional
from pydantic import BaseModel, Field


class AuditTrailConfig(BaseModel):
    """Configuration for audit trail aggregation and analysis."""

    # Storage configuration
    postgres_url: str = Field(
        "postgresql+asyncpg://user:pass@localhost:5432/dotmac",
        description="PostgreSQL URL for audit trail storage"
    )

    redis_url: str = Field(
        "redis://localhost:6379/0",
        description="Redis URL for caching and real-time aggregation"
    )

    # Retention settings
    retention_days: int = Field(
        365,
        description="Number of days to retain audit events"
    )

    cleanup_interval_hours: int = Field(
        24,
        description="Interval between cleanup operations in hours"
    )

    # Performance settings
    batch_size: int = Field(
        1000,
        description="Batch size for bulk operations"
    )

    cache_ttl: int = Field(
        300,
        description="Cache TTL for aggregated data in seconds"
    )

    # Anomaly detection
    anomaly_detection_enabled: bool = Field(
        True,
        description="Enable anomaly detection"
    )

    anomaly_threshold_multiplier: float = Field(
        3.0,
        description="Multiplier for anomaly detection threshold"
    )

    # Alert settings
    alert_enabled: bool = Field(
        True,
        description="Enable alerting for critical events"
    )

    alert_threshold_critical: int = Field(
        10,
        description="Number of critical events to trigger alert"
    )

    alert_threshold_warning: int = Field(
        50,
        description="Number of warning events to trigger alert"
    )

    # Compliance and reporting
    compliance_enabled: bool = Field(
        True,
        description="Enable compliance reporting features"
    )

    export_formats: list[str] = Field(
        ["json", "csv", "pdf"],
        description="Supported export formats for reports"
    )


class AuditEventConfig(BaseModel):
    """Configuration for audit event processing."""

    # Event filtering
    categories_to_track: list[str] = Field(
        ["AUTHENTICATION", "AUTHORIZATION", "DATA_ACCESS", "SYSTEM_CHANGE"],
        description="Audit categories to track"
    )

    levels_to_track: list[str] = Field(
        ["INFO", "WARNING", "ERROR", "CRITICAL"],
        description="Audit levels to track"
    )

    # Event enrichment
    enrich_with_geolocation: bool = Field(
        True,
        description="Enrich events with geolocation data"
    )

    enrich_with_user_agent: bool = Field(
        True,
        description="Enrich events with user agent data"
    )

    # Rate limiting
    max_events_per_minute: int = Field(
        1000,
        description="Maximum events per minute per source"
    )


__all__ = ["AuditTrailConfig", "AuditEventConfig"]