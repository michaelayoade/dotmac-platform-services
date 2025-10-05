from __future__ import annotations

"""Centralized configuration using pydantic-settings.

All configuration is loaded from environment variables and .env files.
This is the single source of truth for all platform configuration.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Application environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class LogLevel(str, Enum):
    """Log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """Main application settings.

    All settings can be overridden via environment variables.
    For nested settings, use double underscore: DATABASE__POOL_SIZE=20
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="ignore",
    )

    # ============================================================
    # Core Application Settings
    # ============================================================

    # Application metadata
    app_name: str = Field("dotmac-platform", description="Application name")
    app_version: str = Field("1.0.0", description="Application version")
    environment: Environment = Field(Environment.DEVELOPMENT, description="Deployment environment")
    debug: bool = Field(False, description="Debug mode")
    testing: bool = Field(False, description="Testing mode")

    # Server configuration
    host: str = Field(
        "0.0.0.0", description="Server host"
    )  # nosec B104 - Production deployments use proxy
    port: int = Field(8000, description="Server port")
    workers: int = Field(4, description="Number of worker processes")
    reload: bool = Field(False, description="Auto-reload on changes")

    # Security
    secret_key: str = Field(
        "change-me-in-production", description="Secret key for signing (use Vault in production)"
    )
    trusted_hosts: list[str] = Field(default_factory=lambda: ["*"], description="Trusted hosts")

    # ============================================================
    # Database Configuration
    # ============================================================

    class DatabaseSettings(BaseModel):
        """Database configuration."""

        url: PostgresDsn | None = Field(None, description="Full database URL")
        host: str = Field("localhost", description="Database host")
        port: int = Field(5432, description="Database port")
        database: str = Field("dotmac", description="Database name")
        username: str = Field("dotmac", description="Database username")
        password: str = Field("", description="Database password")

        # Connection pool
        pool_size: int = Field(10, description="Connection pool size")
        max_overflow: int = Field(20, description="Max overflow connections")
        pool_timeout: int = Field(30, description="Pool timeout in seconds")
        pool_recycle: int = Field(3600, description="Recycle connections after seconds")
        pool_pre_ping: bool = Field(True, description="Test connections before use")

        # Options
        echo: bool = Field(False, description="Echo SQL statements")
        echo_pool: bool = Field(False, description="Echo pool events")

        @property
        def sqlalchemy_url(self) -> str:
            """Build SQLAlchemy database URL."""
            if self.url:
                return str(self.url)
            return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    database: DatabaseSettings = DatabaseSettings()  # type: ignore[call-arg]

    # ============================================================
    # Redis Configuration
    # ============================================================

    class RedisSettings(BaseModel):
        """Redis configuration."""

        url: RedisDsn | None = Field(None, description="Full Redis URL")
        host: str = Field("localhost", description="Redis host")
        port: int = Field(6379, description="Redis port")
        password: str = Field("", description="Redis password")
        db: int = Field(0, description="Redis database number")

        # Connection pool
        max_connections: int = Field(50, description="Max connections in pool")
        decode_responses: bool = Field(True, description="Decode responses to strings")

        # Separate URLs for different purposes
        cache_db: int = Field(1, description="Cache database number")
        session_db: int = Field(2, description="Session database number")
        pubsub_db: int = Field(3, description="Pub/sub database number")

        @property
        def redis_url(self) -> str:
            """Build Redis URL."""
            if self.url:
                return str(self.url)
            if self.password:
                return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
            return f"redis://{self.host}:{self.port}/{self.db}"

        @property
        def cache_url(self) -> str:
            """Build cache Redis URL."""
            if self.password:
                return f"redis://:{self.password}@{self.host}:{self.port}/{self.cache_db}"
            return f"redis://{self.host}:{self.port}/{self.cache_db}"

        @property
        def session_url(self) -> str:
            """Build session Redis URL."""
            if self.password:
                return f"redis://:{self.password}@{self.host}:{self.port}/{self.session_db}"
            return f"redis://{self.host}:{self.port}/{self.session_db}"

    redis: RedisSettings = RedisSettings()  # type: ignore[call-arg]

    # ============================================================
    # JWT & Authentication
    # ============================================================

    class JWTSettings(BaseModel):
        """JWT configuration."""

        secret_key: str = Field("change-me", description="JWT secret key")
        algorithm: str = Field("HS256", description="JWT algorithm")
        access_token_expire_minutes: int = Field(30, description="Access token expiration")
        refresh_token_expire_days: int = Field(30, description="Refresh token expiration")
        issuer: str = Field("dotmac-platform", description="JWT issuer")
        audience: str = Field("dotmac-api", description="JWT audience")

    jwt: JWTSettings = JWTSettings()  # type: ignore[call-arg]

    # ============================================================
    # CORS Configuration
    # ============================================================

    class CORSSettings(BaseModel):
        """CORS configuration."""

        enabled: bool = Field(True, description="Enable CORS")
        origins: list[str] = Field(
            default_factory=lambda: [
                "http://localhost:3000",  # Frontend dev server
                "http://localhost:3001",  # Alternative frontend port
                "http://localhost:8000",  # Backend (for Swagger UI)
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8000",
            ],
            description="Allowed origins for CORS",
        )
        methods: list[str] = Field(default_factory=lambda: ["*"], description="Allowed methods")
        headers: list[str] = Field(default_factory=lambda: ["*"], description="Allowed headers")
        credentials: bool = Field(True, description="Allow credentials")
        max_age: int = Field(3600, description="Max age for preflight")

    cors: CORSSettings = CORSSettings()  # type: ignore[call-arg]

    # ============================================================
    # Email & SMTP Settings
    # ============================================================

    class EmailSettings(BaseModel):
        """Email and SMTP configuration."""

        # SMTP Configuration
        smtp_host: str = Field("localhost", description="SMTP server host")
        smtp_port: int = Field(587, description="SMTP server port")
        smtp_username: str = Field("", description="SMTP username")
        smtp_password: str = Field("", description="SMTP password")
        use_tls: bool = Field(True, description="Use TLS for SMTP")
        use_ssl: bool = Field(False, description="Use SSL for SMTP")

        # Email defaults
        from_address: str = Field("noreply@example.com", description="Default from email")
        from_name: str = Field("DotMac Platform", description="Default from name")
        reply_to: str = Field("", description="Reply-to address")

        # Email behavior
        enabled: bool = Field(True, description="Enable email sending")
        max_retries: int = Field(3, description="Max send retries")
        timeout: int = Field(30, description="SMTP timeout in seconds")

        # Template settings
        template_path: str = Field("templates/emails", description="Email template path")
        use_html: bool = Field(True, description="Send HTML emails")

    email: EmailSettings = EmailSettings()  # type: ignore[call-arg]

    # ============================================================
    # Tenant Settings
    # ============================================================

    class TenantSettings(BaseModel):
        """Multi-tenant configuration."""

        # Tenant mode
        mode: str = Field("single", description="Tenant mode: single or multi")
        default_tenant_id: str = Field("default", description="Default tenant ID")

        # Request handling
        require_tenant_header: bool = Field(False, description="Require tenant header")
        tenant_header_name: str = Field("X-Tenant-ID", description="Tenant header name")
        tenant_query_param: str = Field("tenant_id", description="Tenant query parameter")

        # Tenant isolation
        strict_isolation: bool = Field(True, description="Enforce strict tenant isolation")
        allow_cross_tenant_access: bool = Field(
            False, description="Allow cross-tenant access for admins"
        )

        # Tenant limits
        max_users_per_tenant: int = Field(1000, description="Max users per tenant")
        max_storage_per_tenant_gb: int = Field(100, description="Max storage per tenant in GB")

    tenant: TenantSettings = TenantSettings()  # type: ignore[call-arg]

    # ============================================================
    # Celery & Task Queue
    # ============================================================

    class CelerySettings(BaseModel):
        """Celery configuration."""

        broker_url: str = Field("redis://localhost:6379/0", description="Broker URL")
        result_backend: str = Field("redis://localhost:6379/1", description="Result backend")
        task_serializer: str = Field("json", description="Task serializer")
        result_serializer: str = Field("json", description="Result serializer")
        accept_content: list[str] = Field(
            default_factory=lambda: ["json"], description="Accept content types"
        )
        timezone: str = Field("UTC", description="Timezone")
        enable_utc: bool = Field(True, description="Enable UTC")

        # Worker settings
        worker_concurrency: int = Field(4, description="Worker concurrency")
        worker_prefetch_multiplier: int = Field(4, description="Prefetch multiplier")
        worker_max_tasks_per_child: int = Field(1000, description="Max tasks per child")
        task_soft_time_limit: int = Field(300, description="Soft time limit")
        task_time_limit: int = Field(600, description="Hard time limit")

    celery: CelerySettings = CelerySettings()  # type: ignore[call-arg]

    # ============================================================
    # Observability & Monitoring
    # ============================================================

    class ObservabilitySettings(BaseModel):
        """Observability configuration."""

        # Logging
        log_level: LogLevel = Field(LogLevel.INFO, description="Log level")
        log_format: str = Field("json", description="Log format (json or text)")
        enable_structured_logging: bool = Field(True, description="Enable structured logging")
        enable_correlation_ids: bool = Field(True, description="Enable correlation IDs")
        correlation_id_header: str = Field("X-Correlation-ID", description="Correlation ID header")

        # Tracing
        enable_tracing: bool = Field(True, description="Enable distributed tracing")
        tracing_sample_rate: float = Field(1.0, description="Tracing sample rate (0.0-1.0)")

        # Metrics
        enable_metrics: bool = Field(True, description="Enable metrics collection")
        metrics_port: int = Field(9090, description="Metrics port")

        # OpenTelemetry
        otel_enabled: bool = Field(True, description="Enable OpenTelemetry")
        otel_endpoint: str | None = Field(
            "http://localhost:4318/v1/traces",
            description="OTLP endpoint (default: local OTEL collector)",
        )
        otel_service_name: str = Field("dotmac-platform", description="Service name")
        otel_resource_attributes: dict[str, str] = Field(
            default_factory=dict, description="Resource attributes"
        )
        # Instrumentation toggles
        otel_instrument_celery: bool = Field(
            True, description="Enable Celery instrumentation when OTEL is enabled"
        )
        otel_instrument_fastapi: bool = Field(
            True, description="Enable FastAPI instrumentation when OTEL is enabled"
        )
        otel_instrument_sqlalchemy: bool = Field(
            True, description="Enable SQLAlchemy instrumentation when OTEL is enabled"
        )
        otel_instrument_requests: bool = Field(
            True, description="Enable Requests instrumentation when OTEL is enabled"
        )

        # Prometheus metrics endpoint
        prometheus_enabled: bool = Field(True, description="Enable Prometheus metrics")
        prometheus_port: int = Field(8001, description="Prometheus metrics port")

    observability: ObservabilitySettings = ObservabilitySettings()  # type: ignore[call-arg]

    # ============================================================
    # Billing Configuration
    # ============================================================

    class BillingSettings(BaseModel):
        """Billing system configuration."""

        # Product settings
        default_currency: str = Field("USD", description="Default currency for products")
        auto_generate_skus: bool = Field(True, description="Auto-generate SKUs for products")
        sku_prefix: str = Field("PROD", description="Prefix for auto-generated SKUs")
        sku_auto_increment: bool = Field(True, description="Use auto-incrementing SKU numbers")

        # Subscription settings
        default_trial_days: int = Field(14, description="Default trial period in days")
        allow_plan_changes: bool = Field(True, description="Allow subscription plan changes")
        proration_enabled: bool = Field(True, description="Enable mid-cycle proration")
        cancel_at_period_end_default: bool = Field(
            True, description="Default cancellation behavior"
        )

        # Pricing settings
        pricing_rules_enabled: bool = Field(True, description="Enable pricing rules system")
        max_discount_percentage: int = Field(50, description="Maximum discount percentage allowed")
        customer_specific_pricing_enabled: bool = Field(
            True, description="Enable customer-specific pricing"
        )
        volume_discounts_enabled: bool = Field(True, description="Enable volume discount rules")

        # Usage billing settings
        usage_billing_enabled: bool = Field(True, description="Enable usage-based billing")
        usage_calculation_precision: int = Field(
            2, description="Decimal places for usage calculations"
        )
        usage_aggregation_period: str = Field("monthly", description="Usage aggregation period")
        overage_billing_enabled: bool = Field(
            True, description="Enable overage billing for hybrid plans"
        )

        # Processing settings
        auto_invoice_subscriptions: bool = Field(
            True, description="Automatically create subscription invoices"
        )
        auto_process_renewals: bool = Field(
            False, description="Automatically process subscription renewals"
        )
        invoice_due_days: int = Field(30, description="Default invoice due period in days")
        grace_period_days: int = Field(3, description="Grace period for failed payments")
        payment_retry_attempts: int = Field(3, description="Number of payment retry attempts")
        payment_retry_interval_hours: int = Field(24, description="Hours between payment retries")

        # Notification settings
        send_renewal_reminders: bool = Field(
            True, description="Send subscription renewal reminders"
        )
        renewal_reminder_days: int = Field(7, description="Days before renewal to send reminder")
        send_payment_failure_notifications: bool = Field(
            True, description="Send payment failure notifications"
        )
        send_cancellation_confirmations: bool = Field(
            True, description="Send cancellation confirmations"
        )

        # Tax and compliance
        tax_inclusive_pricing: bool = Field(False, description="Display tax-inclusive prices")
        require_tax_id_for_business: bool = Field(
            False, description="Require tax ID for business customers"
        )
        enable_tax_exemptions: bool = Field(True, description="Allow tax exemptions")

        # Feature flags
        enable_promotional_codes: bool = Field(
            True, description="Enable promotional discount codes"
        )
        enable_referral_discounts: bool = Field(
            False, description="Enable referral discount system"
        )
        enable_multi_currency: bool = Field(False, description="Enable multi-currency support")
        enable_dunning_management: bool = Field(
            True, description="Enable dunning management for failed payments"
        )

    billing: BillingSettings = BillingSettings()  # type: ignore[call-arg]

    # ============================================================
    # Rate Limiting
    # ============================================================

    class RateLimitSettings(BaseModel):
        """Rate limiting configuration."""

        enabled: bool = Field(True, description="Enable rate limiting")
        default_limit: str = Field("100/hour", description="Default rate limit")
        storage_url: str | None = Field(
            None, description="Storage URL for distributed rate limiting"
        )
        key_prefix: str = Field("rate_limit", description="Key prefix for storage")

        # Per-endpoint limits
        endpoint_limits: dict[str, str] = Field(
            default_factory=dict, description="Per-endpoint limits"
        )

    rate_limit: RateLimitSettings = RateLimitSettings()  # type: ignore[call-arg]

    # ============================================================
    # Vault/Secrets Management
    # ============================================================

    class VaultSettings(BaseModel):
        """Vault/OpenBao configuration (API-compatible)."""

        enabled: bool = Field(False, description="Enable Vault/OpenBao")
        url: str = Field("http://localhost:8200", description="Vault/OpenBao URL")
        token: str | None = Field(None, description="Vault token")
        namespace: str | None = Field(None, description="Vault namespace")
        mount_path: str = Field("secret", description="Mount path")
        kv_version: int = Field(2, description="KV version (1 or 2)")

    vault: VaultSettings = VaultSettings()  # type: ignore[call-arg]

    # ============================================================
    # Object Storage (S3/MinIO)
    # ============================================================

    class StorageSettings(BaseModel):
        """MinIO object storage configuration."""

        provider: str = Field("minio", description="Storage provider: 'minio' or 'local'")
        enabled: bool = Field(True, description="Enable MinIO storage")
        endpoint: str = Field("localhost:9000", description="MinIO endpoint")
        region: str = Field("us-east-1", description="MinIO region")
        access_key: str = Field("minioadmin", description="MinIO access key")
        secret_key: str = Field("minioadmin", description="MinIO secret key")
        bucket: str = Field("dotmac", description="Default bucket")
        use_ssl: bool = Field(False, description="Use SSL")

        # Local fallback for development
        local_path: str = Field("/tmp/storage", description="Local storage path for dev")

    storage: StorageSettings = StorageSettings()  # type: ignore[call-arg]

    # ============================================================
    # Feature Flags
    # ============================================================

    class FeatureFlags(BaseModel):
        """Feature flags for core platform features."""

        # Core features
        mfa_enabled: bool = Field(False, description="Enable multi-factor authentication")
        audit_logging: bool = Field(True, description="Enable audit logging")
        # Communications
        email_enabled: bool = Field(True, description="Enable email integrations")

        # Storage - MinIO only
        storage_enabled: bool = Field(True, description="Enable MinIO storage")

        # Search functionality (MeiliSearch)
        search_enabled: bool = Field(True, description="Enable search functionality")

        # Data handling
        data_transfer_enabled: bool = Field(True, description="Enable data import/export")
        data_transfer_excel: bool = Field(True, description="Enable Excel import/export support")
        data_transfer_compression: bool = Field(True, description="Enable compression support")
        data_transfer_streaming: bool = Field(True, description="Enable streaming data transfer")

        # File processing
        file_processing_enabled: bool = Field(True, description="Enable file processing")
        file_processing_pdf: bool = Field(True, description="Enable PDF processing")
        file_processing_images: bool = Field(True, description="Enable image processing")
        file_processing_office: bool = Field(True, description="Enable Office document processing")

        # Background tasks
        celery_enabled: bool = Field(True, description="Enable Celery task queue")
        celery_redis: bool = Field(True, description="Use Redis as Celery broker")

        # Encryption and secrets
        encryption_fernet: bool = Field(True, description="Enable Fernet encryption")
        secrets_vault: bool = Field(False, description="Enable Vault/OpenBao secrets backend")

        # Database
        db_migrations: bool = Field(True, description="Enable database migrations")
        db_postgresql: bool = Field(True, description="Enable PostgreSQL support")
        db_sqlite: bool = Field(True, description="Enable SQLite support for dev/test")

    features: FeatureFlags = FeatureFlags()  # type: ignore[call-arg]

    # ============================================================
    # Validation & Helpers
    # ============================================================

    @field_validator("environment")
    def validate_environment(cls, v: str) -> str:
        """Validate environment."""
        if isinstance(v, str):
            return Environment(v.lower())
        return v

    @field_validator("secret_key")
    def validate_secret_key(cls, v: str, info: Any) -> str:
        """Validate secret key."""
        if (
            v == "change-me-in-production"
            and info.data.get("environment") == Environment.PRODUCTION
        ):
            raise ValueError("Secret key must be changed in production")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        """Check if running in test mode."""
        return self.testing or self.environment == Environment.TEST


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get global settings instance (singleton)."""
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore
    return _settings


def reset_settings() -> None:
    """Reset settings (mainly for testing)."""
    global _settings
    _settings = None


# Convenience export
settings = get_settings()
