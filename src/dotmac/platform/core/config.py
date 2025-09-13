"""Application configuration module."""

from pydantic import BaseModel, Field


class ApplicationConfig(BaseModel):
    """Main application configuration."""

    # Application settings
    name: str = Field("dotmac-platform", description="Application name")
    version: str = Field("1.0.0", description="Application version")
    debug: bool = Field(False, description="Debug mode")
    testing: bool = Field(False, description="Testing mode")

    # Server settings
    host: str = Field("0.0.0.0", description="Server host")  # nosec B104
    port: int = Field(8000, description="Server port")
    workers: int = Field(4, description="Number of worker processes")
    reload: bool = Field(False, description="Auto-reload on code changes")

    # CORS settings
    cors_enabled: bool = Field(True, description="Enable CORS")
    cors_origins: list[str] = Field(["*"], description="Allowed CORS origins")
    cors_methods: list[str] = Field(["*"], description="Allowed CORS methods")
    cors_headers: list[str] = Field(["*"], description="Allowed CORS headers")

    # Security settings
    secret_key: str = Field("change-me-in-production", description="Application secret key")
    jwt_algorithm: str = Field("HS256", description="JWT algorithm")
    jwt_expiration_minutes: int = Field(30, description="JWT token expiration in minutes")
