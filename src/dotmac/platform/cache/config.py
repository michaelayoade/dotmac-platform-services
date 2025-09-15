"""Cache configuration module."""

from pydantic import BaseModel, ConfigDict, Field


class CacheConfig(BaseModel):
    """Configuration for cache service."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    # Backend configuration
    backend: str = Field(
        default="memory",
        pattern="^(memory|redis|null)$",
        description="Cache backend type: memory, redis, or null",
    )

    # Redis configuration
    redis_url: str | None = Field(
        default=None,
        description="Redis connection URL (overrides host/port if set)",
    )
    redis_host: str = Field(
        default="localhost",
        description="Redis host",
    )
    redis_port: int = Field(
        default=6379,
        ge=1,
        le=65535,
        description="Redis port",
    )
    redis_db: int = Field(
        default=0,
        ge=0,
        description="Redis database number",
    )
    redis_password: str | None = Field(
        default=None,
        description="Redis password",
    )
    redis_ssl: bool = Field(
        default=False,
        description="Use SSL for Redis connection",
    )

    # Memory backend configuration
    max_size: int = Field(
        default=1000,
        gt=0,
        description="Maximum number of entries for memory backend",
    )

    # General configuration
    default_ttl: int = Field(
        default=300,
        gt=0,
        description="Default TTL in seconds",
    )
    key_prefix: str = Field(
        default="",
        description="Global key prefix for all cache keys",
    )

    # Connection pool settings
    max_connections: int = Field(
        default=50,
        gt=0,
        description="Maximum connections in pool (Redis)",
    )
    connection_timeout: int = Field(
        default=20,
        gt=0,
        description="Connection timeout in seconds",
    )

    @property
    def redis_connection_url(self) -> str:
        """Get Redis connection URL."""
        if self.redis_url:
            return self.redis_url

        scheme = "rediss" if self.redis_ssl else "redis"
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"{scheme}://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
