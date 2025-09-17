"""Tenant configuration module."""

from pydantic import BaseModel, Field


class TenantConfig(BaseModel):
    """Multi-tenant configuration."""

    # Tenant identification
    enable_multitenancy: bool = Field(True, description="Enable multi-tenant support")
    tenant_header: str = Field("X-Tenant-ID", description="HTTP header for tenant ID")
    tenant_id_field: str = Field("tenant_id", description="Field name for tenant ID in models")

    # Isolation settings
    isolation_level: str = Field("schema", description="Isolation level: schema, database, or row")
    default_tenant: str | None = Field(None, description="Default tenant ID")

    # Tenant limits
    max_users_per_tenant: int = Field(1000, description="Maximum users per tenant")
    max_storage_per_tenant: int = Field(10737418240, description="Max storage in bytes (10GB)")
    max_api_calls_per_day: int = Field(100000, description="API rate limit per tenant per day")

    # Tenant features
    enable_custom_domains: bool = Field(False, description="Allow custom domains per tenant")
    enable_tenant_branding: bool = Field(True, description="Allow custom branding per tenant")
