"""Configuration for communications module."""

from pydantic import BaseModel, ConfigDict, Field


class SMTPConfig(BaseModel):
    """SMTP server configuration."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    host: str = Field(..., description="SMTP server hostname")
    port: int = Field(587, ge=1, le=65535, description="SMTP server port")
    username: str | None = Field(None, description="SMTP username")
    password: str | None = Field(None, description="SMTP password")
    use_tls: bool = Field(True, description="Use TLS encryption")
    use_ssl: bool = Field(False, description="Use SSL encryption")
    timeout: int = Field(30, gt=0, description="Connection timeout in seconds")
    from_email: str = Field(..., description="Default sender email address")
    from_name: str | None = Field(None, description="Default sender name")


class SMSConfig(BaseModel):
    """Generic SMS gateway configuration."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    # Generic HTTP gateway settings
    gateway_url: str | None = Field(
        None,
        description="SMS gateway HTTP endpoint (e.g., your own gateway or open-source like Kannel)",
    )
    gateway_method: str = Field("POST", pattern="^(GET|POST|PUT)$")
    gateway_headers: dict[str, str] = Field(default_factory=dict)
    gateway_auth_type: str | None = Field(
        None,
        pattern="^(basic|bearer|api_key|none)$",
        description="Authentication type for gateway",
    )
    gateway_auth_value: str | None = Field(None, description="Authentication value")

    # Generic SMS settings
    from_number: str | None = Field(None, description="Default sender number")
    max_length: int = Field(160, gt=0, description="Maximum SMS length")

    # Rate limiting
    rate_limit: int = Field(10, gt=0, description="Max SMS per minute")


class WebSocketConfig(BaseModel):
    """WebSocket configuration."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    # Connection settings
    max_connections: int = Field(1000, gt=0, description="Maximum concurrent connections")
    ping_interval: int = Field(30, gt=0, description="Ping interval in seconds")
    ping_timeout: int = Field(10, gt=0, description="Ping timeout in seconds")
    max_message_size: int = Field(
        65536, gt=0, description="Maximum message size in bytes"
    )

    # Channel settings
    max_channels_per_connection: int = Field(
        10, gt=0, description="Max channels per connection"
    )

    # Redis backend (optional)
    use_redis: bool = Field(False, description="Use Redis for scaling")
    redis_url: str | None = Field(None, description="Redis URL for pub/sub")


class EventBusConfig(BaseModel):
    """Event bus configuration."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    backend: str = Field(
        "memory",
        pattern="^(memory|redis)$",
        description="Event bus backend",
    )

    # Redis configuration
    redis_url: str | None = Field(None, description="Redis URL for events")
    redis_stream_key: str = Field("events", description="Redis stream key prefix")
    redis_consumer_group: str = Field("platform", description="Redis consumer group")

    # Event settings
    max_retries: int = Field(3, ge=0, description="Max retry attempts")
    retry_delay: int = Field(5, gt=0, description="Retry delay in seconds")
    ttl: int = Field(86400, gt=0, description="Event TTL in seconds")


class WebhookConfig(BaseModel):
    """Webhook configuration."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    # HTTP client settings
    timeout: int = Field(30, gt=0, description="Request timeout in seconds")
    max_retries: int = Field(3, ge=0, description="Max retry attempts")
    retry_delay: int = Field(1, gt=0, description="Initial retry delay in seconds")

    # Security
    verify_ssl: bool = Field(True, description="Verify SSL certificates")
    allowed_schemes: list[str] = Field(
        default_factory=lambda: ["https"],
        description="Allowed URL schemes",
    )

    # Rate limiting
    rate_limit: int = Field(100, gt=0, description="Max webhooks per minute")

    # Signature (optional)
    sign_requests: bool = Field(False, description="Sign webhook requests")
    signature_header: str = Field("X-Webhook-Signature", description="Signature header name")
    signature_secret: str | None = Field(None, description="Secret for signing")


class CommunicationsConfig(BaseModel):
    """Main communications configuration."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    # Component configurations
    smtp: SMTPConfig | None = Field(None, description="SMTP email configuration")
    sms: SMSConfig | None = Field(None, description="SMS gateway configuration")
    websocket: WebSocketConfig = Field(
        default_factory=WebSocketConfig,
        description="WebSocket configuration",
    )
    event_bus: EventBusConfig = Field(
        default_factory=EventBusConfig,
        description="Event bus configuration",
    )
    webhook: WebhookConfig = Field(
        default_factory=WebhookConfig,
        description="Webhook configuration",
    )

    # Global settings
    enabled: bool = Field(True, description="Enable communications module")
    debug: bool = Field(False, description="Debug mode")

    @classmethod
    def from_env(cls) -> "CommunicationsConfig":
        """Create configuration from environment variables."""
        import os

        config_dict = {}

        # SMTP configuration
        if os.getenv("SMTP_HOST"):
            config_dict["smtp"] = {
                "host": os.getenv("SMTP_HOST"),
                "port": int(os.getenv("SMTP_PORT", "587")),
                "username": os.getenv("SMTP_USERNAME"),
                "password": os.getenv("SMTP_PASSWORD"),
                "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
                "use_ssl": os.getenv("SMTP_USE_SSL", "false").lower() == "true",
                "from_email": os.getenv("SMTP_FROM_EMAIL", "noreply@example.com"),
                "from_name": os.getenv("SMTP_FROM_NAME"),
            }

        # SMS configuration
        if os.getenv("SMS_GATEWAY_URL"):
            config_dict["sms"] = {
                "gateway_url": os.getenv("SMS_GATEWAY_URL"),
                "gateway_method": os.getenv("SMS_GATEWAY_METHOD", "POST"),
                "gateway_auth_type": os.getenv("SMS_GATEWAY_AUTH_TYPE"),
                "gateway_auth_value": os.getenv("SMS_GATEWAY_AUTH_VALUE"),
                "from_number": os.getenv("SMS_FROM_NUMBER"),
            }

        # WebSocket configuration
        config_dict["websocket"] = {
            "max_connections": int(os.getenv("WS_MAX_CONNECTIONS", "1000")),
            "use_redis": os.getenv("WS_USE_REDIS", "false").lower() == "true",
            "redis_url": os.getenv("WS_REDIS_URL"),
        }

        # Event bus configuration
        config_dict["event_bus"] = {
            "backend": os.getenv("EVENT_BUS_BACKEND", "memory"),
            "redis_url": os.getenv("EVENT_BUS_REDIS_URL"),
        }

        return cls(**config_dict)