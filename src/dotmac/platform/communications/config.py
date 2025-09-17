"""Configuration validation and management for dotmac-communications."""

from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class NotificationConfig(BaseModel):
    """Configuration for notification services."""

    retry_attempts: int = Field(default=3, ge=1, le=10, description="Number of retry attempts")
    retry_delay: int = Field(default=60, ge=1, description="Delay between retries in seconds")
    delivery_timeout: int = Field(default=300, ge=30, description="Delivery timeout in seconds")
    track_delivery: bool = Field(default=True, description="Enable delivery tracking")
    batch_size: int = Field(
        default=100, ge=1, le=1000, description="Batch size for bulk operations"
    )
    rate_limit_per_minute: int = Field(default=1000, ge=1, description="Rate limit per minute")

    providers: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Provider configurations"
    )

    @field_validator("providers")
    def validate_providers(cls, v):
        """Validate provider configurations."""
        allowed_providers = ["email", "sms", "push", "webhook", "slack", "discord"]
        for provider, config in v.items():
            if provider not in allowed_providers:
                raise ValueError(f"Unknown provider: {provider}")
            if not isinstance(config, dict):
                raise ValueError(f"Provider {provider} config must be a dictionary")
        return v


class WebSocketConfig(BaseModel):
    """Configuration for WebSocket services."""

    connection_timeout: int = Field(default=60, ge=10, description="Connection timeout in seconds")
    heartbeat_interval: int = Field(default=30, ge=5, description="Heartbeat interval in seconds")
    max_connections_per_tenant: int = Field(
        default=1000, ge=1, description="Max connections per tenant"
    )
    max_connections: int = Field(default=10000, ge=1, description="Global max connections")
    message_size_limit: int = Field(
        default=1048576, ge=1024, description="Message size limit in bytes"
    )
    message_buffer_size: int = Field(default=1000, ge=10, description="Message buffer size")
    enable_compression: bool = Field(default=True, description="Enable message compression")
    compression_threshold: int = Field(
        default=1024, ge=256, description="Compression threshold in bytes"
    )

    redis_url: Optional[str] = Field(default=None, description="Redis URL for scaling")

    @field_validator("redis_url")
    def validate_redis_url(cls, v):
        """Validate Redis URL format."""
        if v and not (v.startswith("redis://") or v.startswith("rediss://")):
            raise ValueError("Redis URL must start with redis:// or rediss://")
        return v


class EventsConfig(BaseModel):
    """Configuration for event services."""

    default_adapter: str = Field(default="memory", description="Default event adapter")
    retry_policy: str = Field(default="exponential_backoff", description="Retry policy")
    max_retries: int = Field(default=5, ge=1, le=20, description="Maximum retry attempts")
    dead_letter_enabled: bool = Field(default=True, description="Enable dead letter queue")
    event_ttl: int = Field(default=3600, ge=60, description="Event TTL in seconds")
    batch_publish_size: int = Field(default=100, ge=1, description="Batch publish size")
    consumer_concurrency: int = Field(default=10, ge=1, description="Consumer concurrency")
    prefetch_count: int = Field(default=10, ge=1, description="Message prefetch count")

    redis_url: Optional[str] = Field(default=None, description="Redis URL for events")

    @field_validator("default_adapter")
    def validate_adapter(cls, v):
        """Validate adapter type."""
        allowed_adapters = ["memory", "redis", "kafka"]
        if v not in allowed_adapters:
            raise ValueError(f"Unknown adapter: {v}. Allowed: {allowed_adapters}")
        return v

    @field_validator("retry_policy")
    def validate_retry_policy(cls, v):
        """Validate retry policy."""
        allowed_policies = ["simple", "exponential_backoff", "linear_backoff"]
        if v not in allowed_policies:
            raise ValueError(f"Unknown retry policy: {v}. Allowed: {allowed_policies}")
        return v


class RedisConfig(BaseModel):
    """Redis configuration for shared resources."""

    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis port")
    db: int = Field(default=0, ge=0, le=15, description="Redis database number")
    password: Optional[str] = Field(default=None, description="Redis password")
    connection_pool_size: int = Field(default=10, ge=1, description="Connection pool size")
    socket_timeout: int = Field(default=30, ge=1, description="Socket timeout in seconds")
    socket_connect_timeout: int = Field(default=30, ge=1, description="Socket connect timeout")
    retry_on_timeout: bool = Field(default=True, description="Retry on timeout")
    decode_responses: bool = Field(default=True, description="Decode responses to strings")


class CommunicationsConfig(BaseModel):
    """Main configuration for communications services."""

    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    websockets: WebSocketConfig = Field(default_factory=WebSocketConfig)
    events: EventsConfig = Field(default_factory=EventsConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)

    # Global settings
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Log level")

    @field_validator("environment")
    def validate_environment(cls, v):
        """Validate environment."""
        allowed_envs = ["development", "staging", "production", "testing"]
        if v not in allowed_envs:
            raise ValueError(f"Unknown environment: {v}. Allowed: {allowed_envs}")
        return v

    @field_validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Unknown log level: {v}. Allowed: {allowed_levels}")
        return v.upper()

    @model_validator(mode="after")
    def validate_redis_consistency(self):
        """Ensure Redis configuration is consistent."""
        # If Redis URLs are specified, validate they're consistent with redis config
        if self.websockets and self.websockets.redis_url:
            # Redis URL overrides default redis config for websockets
            pass

        if self.events and self.events.redis_url:
            # Redis URL overrides default redis config for events
            pass

        return self


class CommunicationsSettings(BaseSettings):
    """Settings with environment variable support."""

    # Notifications
    dotmac_smtp_host: Optional[str] = None
    dotmac_smtp_port: int = 587
    dotmac_smtp_username: Optional[str] = None
    dotmac_smtp_password: Optional[str] = None
    dotmac_smtp_use_tls: bool = True

    # Twilio SMS
    dotmac_twilio_sid: Optional[str] = None
    dotmac_twilio_token: Optional[str] = None

    # Push notifications
    dotmac_fcm_server_key: Optional[str] = None
    dotmac_apns_key_id: Optional[str] = None
    dotmac_apns_key_file: Optional[str] = None

    # Redis
    dotmac_redis_url: Optional[str] = None
    dotmac_redis_host: str = "localhost"
    dotmac_redis_port: int = 6379
    dotmac_redis_db: int = 0
    dotmac_redis_password: Optional[str] = None

    # Global
    dotmac_environment: str = "development"
    dotmac_debug: bool = False
    dotmac_log_level: str = "INFO"

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    def to_communications_config(self) -> CommunicationsConfig:
        """Convert settings to communications config."""
        # Build provider configs from environment
        email_config = {}
        if self.dotmac_smtp_host:
            email_config = {
                "smtp_host": self.dotmac_smtp_host,
                "smtp_port": self.dotmac_smtp_port,
                "username": self.dotmac_smtp_username,
                "password": self.dotmac_smtp_password,
                "use_tls": self.dotmac_smtp_use_tls,
            }

        sms_config = {}
        if self.dotmac_twilio_sid:
            sms_config = {
                "provider": "twilio",
                "account_sid": self.dotmac_twilio_sid,
                "auth_token": self.dotmac_twilio_token,
            }

        push_config = {}
        if self.dotmac_fcm_server_key:
            push_config = {"provider": "fcm", "server_key": self.dotmac_fcm_server_key}

        providers = {}
        if email_config:
            providers["email"] = email_config
        if sms_config:
            providers["sms"] = sms_config
        if push_config:
            providers["push"] = push_config

        # Redis URL priority: specific URL > constructed from parts
        redis_url = self.dotmac_redis_url
        if not redis_url and self.dotmac_redis_host:
            redis_url = (
                f"redis://{self.dotmac_redis_host}:{self.dotmac_redis_port}/{self.dotmac_redis_db}"
            )
            if self.dotmac_redis_password:
                redis_url = f"redis://:{self.dotmac_redis_password}@{self.dotmac_redis_host}:{self.dotmac_redis_port}/{self.dotmac_redis_db}"

        return CommunicationsConfig(
            notifications=NotificationConfig(providers=providers),
            websockets=WebSocketConfig(redis_url=redis_url),
            events=EventsConfig(redis_url=redis_url),
            redis=RedisConfig(
                host=self.dotmac_redis_host,
                port=self.dotmac_redis_port,
                db=self.dotmac_redis_db,
                password=self.dotmac_redis_password,
            ),
            environment=self.dotmac_environment,
            debug=self.dotmac_debug,
            log_level=self.dotmac_log_level,
        )


def load_config(config_dict: Optional[dict[str, Any]] = None) -> CommunicationsConfig:
    """Load configuration from dictionary or environment."""
    if config_dict:
        # Validate provided config
        return CommunicationsConfig(**config_dict)
    else:
        # Load from environment
        settings = CommunicationsSettings()
        return settings.to_communications_config()


def validate_config(config: Union[dict[str, Any], CommunicationsConfig]) -> CommunicationsConfig:
    """Validate configuration and return validated config object."""
    if isinstance(config, dict):
        return CommunicationsConfig(**config)
    elif isinstance(config, CommunicationsConfig):
        return config
    else:
        raise ValueError("Configuration must be a dictionary or CommunicationsConfig instance")


# Export for easy importing
__all__ = [
    "CommunicationsConfig",
    "NotificationConfig",
    "WebSocketConfig",
    "EventsConfig",
    "RedisConfig",
    "CommunicationsSettings",
    "load_config",
    "validate_config",
]
