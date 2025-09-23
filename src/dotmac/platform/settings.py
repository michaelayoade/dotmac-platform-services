from __future__ import annotations

"""Centralized configuration using pydantic-settings.

All configuration is loaded from environment variables and .env files.
This is the single source of truth for all platform configuration.
"""

from enum import Enum
from typing import Any, Optional

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
    host: str = Field("0.0.0.0", description="Server host")
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

        url: Optional[PostgresDsn] = Field(None, description="Full database URL")
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

        url: Optional[RedisDsn] = Field(None, description="Full Redis URL")
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
        origins: list[str] = Field(default_factory=lambda: ["*"], description="Allowed origins")
        methods: list[str] = Field(default_factory=lambda: ["*"], description="Allowed methods")
        headers: list[str] = Field(default_factory=lambda: ["*"], description="Allowed headers")
        credentials: bool = Field(True, description="Allow credentials")
        max_age: int = Field(3600, description="Max age for preflight")

    cors: CORSSettings = CORSSettings()  # type: ignore[call-arg]

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
        otel_enabled: bool = Field(False, description="Enable OpenTelemetry")
        otel_endpoint: Optional[str] = Field(None, description="OTLP endpoint")
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

        # Sentry
        sentry_enabled: bool = Field(False, description="Enable Sentry")
        sentry_dsn: Optional[str] = Field(None, description="Sentry DSN")
        sentry_environment: Optional[str] = Field(None, description="Sentry environment")
        sentry_traces_sample_rate: float = Field(0.1, description="Sentry traces sample rate")

    observability: ObservabilitySettings = ObservabilitySettings()  # type: ignore[call-arg]

    # ============================================================
    # Rate Limiting
    # ============================================================

    class RateLimitSettings(BaseModel):
        """Rate limiting configuration."""

        enabled: bool = Field(True, description="Enable rate limiting")
        default_limit: str = Field("100/hour", description="Default rate limit")
        storage_url: Optional[str] = Field(
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
        token: Optional[str] = Field(None, description="Vault token")
        namespace: Optional[str] = Field(None, description="Vault namespace")
        mount_path: str = Field("secret", description="Mount path")
        kv_version: int = Field(2, description="KV version (1 or 2)")

    vault: VaultSettings = VaultSettings()  # type: ignore[call-arg]

    # ============================================================
    # Object Storage (S3/MinIO)
    # ============================================================

    class StorageSettings(BaseModel):
        """Object storage configuration."""

        provider: str = Field("minio", description="Storage provider (s3, minio, local)")
        endpoint: Optional[str] = Field(None, description="Storage endpoint")
        access_key: Optional[str] = Field(None, description="Access key")
        secret_key: Optional[str] = Field(None, description="Secret key")
        bucket: str = Field("dotmac", description="Default bucket")
        region: str = Field("us-east-1", description="AWS region")
        use_ssl: bool = Field(False, description="Use SSL")

        # Local storage
        local_path: str = Field("/tmp/storage", description="Local storage path")

    storage: StorageSettings = StorageSettings()  # type: ignore[call-arg]

    # ============================================================
    # Feature Flags
    # ============================================================

    class FeatureFlags(BaseModel):
        """Feature flags for optional dependencies and features."""

        # Core features
        mfa_enabled: bool = Field(False, description="Enable MFA")
        audit_logging: bool = Field(True, description="Enable audit logging")
        experimental_features: bool = Field(False, description="Enable experimental features")

        # Storage backends
        storage_s3_enabled: bool = Field(
            False, description="Enable S3 storage backend (requires boto3)"
        )
        storage_minio_enabled: bool = Field(
            False, description="Enable MinIO storage backend (requires minio)"
        )
        storage_azure_enabled: bool = Field(
            False, description="Enable Azure storage backend (requires azure-storage-blob)"
        )
        storage_gcs_enabled: bool = Field(
            False, description="Enable Google Cloud storage backend (requires google-cloud-storage)"
        )

        # Search backends
        search_enabled: bool = Field(False, description="Enable search functionality")
        search_meilisearch_enabled: bool = Field(
            False, description="Enable MeiliSearch backend (requires meilisearch)"
        )
        search_elasticsearch_enabled: bool = Field(
            False, description="Enable Elasticsearch backend (requires elasticsearch)"
        )

        # Communication features
        websockets_enabled: bool = Field(False, description="Enable WebSockets (requires fastapi)")
        websockets_redis_scaling: bool = Field(
            False, description="Enable Redis scaling for WebSockets (requires redis)"
        )
        email_enabled: bool = Field(
            False, description="Enable email notifications (requires smtplib)"
        )
        slack_enabled: bool = Field(
            False, description="Enable Slack notifications (requires slack-sdk)"
        )

        # GraphQL removed - using REST APIs only

        # Observability
        observability_enabled: bool = Field(True, description="Enable observability features")
        tracing_opentelemetry: bool = Field(
            False, description="Enable OpenTelemetry tracing (requires opentelemetry packages)"
        )
        metrics_prometheus: bool = Field(
            False, description="Enable Prometheus metrics (requires prometheus-client)"
        )
        sentry_enabled: bool = Field(
            False, description="Enable Sentry error tracking (requires sentry-sdk)"
        )

        # Encryption and secrets
        encryption_fernet: bool = Field(
            True, description="Enable Fernet encryption (requires cryptography)"
        )
        secrets_vault: bool = Field(
            False, description="Enable Vault secrets backend (requires hvac)"
        )
        secrets_aws: bool = Field(False, description="Enable AWS Secrets Manager (requires boto3)")

        # Data transfer features
        data_transfer_enabled: bool = Field(True, description="Enable data transfer functionality")
        data_transfer_excel: bool = Field(
            True, description="Enable Excel import/export (requires openpyxl, xlsxwriter)"
        )
        data_transfer_compression: bool = Field(
            True, description="Enable compression support (requires standard library)"
        )
        data_transfer_streaming: bool = Field(True, description="Enable streaming data transfer")

        # File processing
        file_processing_enabled: bool = Field(False, description="Enable file processing")
        file_processing_pdf: bool = Field(
            False, description="Enable PDF processing (requires PyMuPDF)"
        )
        file_processing_images: bool = Field(
            False, description="Enable image processing (requires Pillow)"
        )
        file_processing_office: bool = Field(
            False, description="Enable Office document processing (requires python-docx, openpyxl)"
        )

        # Task queue
        celery_enabled: bool = Field(
            False, description="Enable Celery task queue (requires celery)"
        )
        celery_redis: bool = Field(False, description="Use Redis as Celery broker (requires redis)")
        celery_rabbitmq: bool = Field(
            False, description="Use RabbitMQ as Celery broker (requires pika)"
        )

        # Database features
        db_migrations: bool = Field(
            True, description="Enable database migrations (requires alembic)"
        )
        db_postgresql: bool = Field(
            True, description="Enable PostgreSQL support (requires asyncpg)"
        )
        db_sqlite: bool = Field(True, description="Enable SQLite support (requires aiosqlite)")

        # Testing and development
        testing_factories: bool = Field(
            False, description="Enable test data factories (requires factory-boy)"
        )
        dev_tools: bool = Field(False, description="Enable development tools and debugging")

    features: FeatureFlags = FeatureFlags()  # type: ignore[call-arg]

    # ============================================================
    # Email/SMTP Configuration
    # ============================================================

    class EmailSettings(BaseModel):
        """Email configuration."""

        enabled: bool = Field(False, description="Enable email")
        smtp_host: Optional[str] = Field(None, description="SMTP host")
        smtp_port: int = Field(587, description="SMTP port")
        smtp_user: Optional[str] = Field(None, description="SMTP username")
        smtp_password: Optional[str] = Field(None, description="SMTP password")
        smtp_use_tls: bool = Field(True, description="Use TLS")
        from_address: str = Field("noreply@example.com", description="From address")
        from_name: str = Field("DotMac Platform", description="From name")

    email: EmailSettings = EmailSettings()  # type: ignore[call-arg]

    # ============================================================
    # WebSocket Configuration
    # ============================================================

    class WebSocketSettings(BaseModel):
        """WebSocket configuration."""

        enabled: bool = Field(True, description="Enable WebSockets")
        ping_interval: int = Field(30, description="Ping interval in seconds")
        ping_timeout: int = Field(10, description="Ping timeout in seconds")
        max_connections: int = Field(1000, description="Max connections")
        max_message_size: int = Field(1024 * 1024, description="Max message size in bytes")

    websocket: WebSocketSettings = WebSocketSettings()  # type: ignore[call-arg]

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
_settings: Optional[Settings] = None


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
