"""Database configuration module."""


from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """Database configuration."""

    # Connection string or components
    url: str | None = None
    host: str = "localhost"
    port: int = 5432
    database: str = "dotmac"
    username: str = "dotmac"
    password: str = ""
    driver: str = "postgresql+asyncpg"

    # Connection pool settings
    pool_size: int = Field(10, description="Number of connections to maintain in pool")
    max_overflow: int = Field(20, description="Maximum overflow connections above pool_size")
    pool_timeout: int = Field(30, description="Timeout for acquiring connection from pool")
    pool_recycle: int = Field(3600, description="Recycle connections after this many seconds")
    pool_pre_ping: bool = Field(True, description="Test connections before using")

    # Other settings
    echo: bool = Field(False, description="Echo SQL statements")
    echo_pool: bool = Field(False, description="Echo pool events")

    @property
    def build_url(self) -> str:
        """Build database URL from components."""
        if self.url:
            return self.url
        return f"{self.driver}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
