"""
Models and schemas for admin settings management.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict


class SettingsCategory(str, Enum):
    """Available settings categories."""

    DATABASE = "database"
    JWT = "jwt"
    REDIS = "redis"
    VAULT = "vault"
    STORAGE = "storage"
    EMAIL = "email"
    TENANT = "tenant"
    CORS = "cors"
    RATE_LIMIT = "rate_limit"
    OBSERVABILITY = "observability"
    CELERY = "celery"
    FEATURES = "features"
    BILLING = "billing"

    @classmethod
    def get_display_name(cls, category: "SettingsCategory") -> str:
        """Get human-readable display name for category."""
        display_names = {
            cls.DATABASE: "Database Configuration",
            cls.JWT: "JWT & Authentication",
            cls.REDIS: "Redis Cache",
            cls.VAULT: "Vault/Secrets Management",
            cls.STORAGE: "Object Storage (MinIO/S3)",
            cls.EMAIL: "Email & SMTP",
            cls.TENANT: "Multi-tenancy",
            cls.CORS: "CORS Configuration",
            cls.RATE_LIMIT: "Rate Limiting",
            cls.OBSERVABILITY: "Logging & Monitoring",
            cls.CELERY: "Background Tasks",
            cls.FEATURES: "Feature Flags",
            cls.BILLING: "Billing & Subscriptions",
        }
        return display_names.get(category, category.value)


class SettingField(BaseModel):
    """Individual setting field metadata."""

    name: str = Field(description="Field name")
    value: Any = Field(description="Current value")
    type: str = Field(description="Field type (str, int, bool, etc.)")
    description: Optional[str] = Field(None, description="Field description")
    default: Any = Field(None, description="Default value")
    required: bool = Field(True, description="Is field required")
    sensitive: bool = Field(False, description="Is this a sensitive field (password, key, etc.)")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Validation rules")

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )


class SettingsResponse(BaseModel):
    """Response model for settings retrieval."""

    category: SettingsCategory = Field(description="Settings category")
    display_name: str = Field(description="Category display name")
    fields: List[SettingField] = Field(description="List of settings fields")
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")
    updated_by: Optional[str] = Field(None, description="Last updated by user")

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )


class SettingsUpdateRequest(BaseModel):
    """Request model for updating settings."""

    updates: Dict[str, Any] = Field(description="Field updates as key-value pairs")
    validate_only: bool = Field(
        False,
        description="Only validate without applying changes"
    )
    restart_required: bool = Field(
        False,
        description="Whether these changes require service restart"
    )
    reason: Optional[str] = Field(
        None,
        description="Reason for settings update (for audit log)"
    )

    @field_validator("updates")
    @classmethod
    def validate_updates_not_empty(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure updates dict is not empty."""
        if not v:
            raise ValueError("Updates cannot be empty")
        return v


class SettingsValidationResult(BaseModel):
    """Result of settings validation."""

    valid: bool = Field(description="Whether all settings are valid")
    errors: Dict[str, str] = Field(
        default_factory=dict,
        description="Validation errors by field"
    )
    warnings: Dict[str, str] = Field(
        default_factory=dict,
        description="Validation warnings by field"
    )
    restart_required: bool = Field(
        False,
        description="Whether changes require restart"
    )


class AuditLog(BaseModel):
    """Audit log entry for settings changes."""

    id: UUID = Field(description="Audit log ID")
    timestamp: datetime = Field(description="Change timestamp")
    user_id: str = Field(description="User who made the change")
    user_email: str = Field(description="User email")
    category: SettingsCategory = Field(description="Settings category")
    action: str = Field(description="Action performed (update, reset, etc.)")
    changes: Dict[str, Dict[str, Any]] = Field(
        description="Changes made (field: {old, new})"
    )
    reason: Optional[str] = Field(None, description="Reason for change")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    )


class SettingsBackup(BaseModel):
    """Settings backup model."""

    id: UUID = Field(description="Backup ID")
    created_at: datetime = Field(description="Backup creation time")
    created_by: str = Field(description="User who created backup")
    name: str = Field(description="Backup name")
    description: Optional[str] = Field(None, description="Backup description")
    categories: List[SettingsCategory] = Field(
        description="Categories included in backup"
    )
    settings_data: Dict[str, Any] = Field(description="Backup data")

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    )


class SettingsCategoryInfo(BaseModel):
    """Information about a settings category."""

    category: SettingsCategory = Field(description="Category identifier")
    display_name: str = Field(description="Display name")
    description: str = Field(description="Category description")
    fields_count: int = Field(description="Number of fields")
    has_sensitive_fields: bool = Field(description="Contains sensitive fields")
    restart_required: bool = Field(description="Changes require restart")
    last_updated: Optional[datetime] = Field(None, description="Last update time")


class BulkSettingsUpdate(BaseModel):
    """Request for updating multiple categories at once."""

    updates: Dict[SettingsCategory, Dict[str, Any]] = Field(
        description="Updates by category"
    )
    validate_only: bool = Field(
        False,
        description="Only validate without applying"
    )
    reason: Optional[str] = Field(
        None,
        description="Reason for bulk update"
    )


class SettingsExportRequest(BaseModel):
    """Request for exporting settings."""

    categories: Optional[List[SettingsCategory]] = Field(
        None,
        description="Categories to export (all if None)"
    )
    include_sensitive: bool = Field(
        False,
        description="Include sensitive fields in export"
    )
    format: str = Field(
        "json",
        description="Export format (json, yaml, env)"
    )


class SettingsImportRequest(BaseModel):
    """Request for importing settings."""

    data: Dict[str, Any] = Field(description="Settings data to import")
    categories: Optional[List[SettingsCategory]] = Field(
        None,
        description="Limit import to specific categories"
    )
    validate_only: bool = Field(
        True,
        description="Validate before importing"
    )
    overwrite: bool = Field(
        False,
        description="Overwrite existing settings"
    )
    reason: Optional[str] = Field(
        None,
        description="Reason for import"
    )