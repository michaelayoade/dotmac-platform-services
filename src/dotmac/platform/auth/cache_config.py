"""Cache configuration for auth module."""


from pydantic import BaseModel, Field


class CacheConfig(BaseModel):
    """Cache configuration for authentication and sessions."""

    # Cache backend settings
    backend: str = Field("redis", description="Cache backend: redis, memcached, or memory")
    url: str | None = Field(None, description="Cache backend URL")
    host: str = Field("localhost", description="Cache host")
    port: int = Field(6379, description="Cache port")
    db: int = Field(0, description="Redis database number")
    password: str | None = Field(None, description="Cache password")

    # Cache behavior settings
    ttl: int = Field(3600, description="Default TTL in seconds")
    session_ttl: int = Field(86400, description="Session TTL in seconds (24 hours)")
    token_ttl: int = Field(3600, description="Token TTL in seconds (1 hour)")

    # Cache key prefixes
    key_prefix: str = Field("dotmac:", description="Global key prefix")
    session_prefix: str = Field("session:", description="Session key prefix")
    token_prefix: str = Field("token:", description="Token key prefix")

    # Cache pool settings
    max_connections: int = Field(50, description="Maximum connections in pool")
    connection_timeout: int = Field(20, description="Connection timeout in seconds")
