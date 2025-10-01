"""
Plugin configuration schema definitions.

This module defines the structures for plugin configuration schemas,
allowing plugins to describe their configuration requirements dynamically.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class FieldType(str, Enum):
    """Supported field types for plugin configuration."""

    STRING = "string"
    TEXT = "text"  # Multi-line string
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    SECRET = "secret"  # Write-only sensitive data
    URL = "url"
    EMAIL = "email"
    PHONE = "phone"
    JSON = "json"
    ARRAY = "array"


class ValidationRule(BaseModel):
    """Validation rule for a field."""

    type: str = Field(description="Type of validation rule")
    value: Any = Field(description="Validation parameter")
    message: Optional[str] = Field(None, description="Custom error message")


class SelectOption(BaseModel):
    """Option for select fields."""

    value: str = Field(description="Option value")
    label: str = Field(description="Display label")
    description: Optional[str] = Field(None, description="Option description")


class FieldSpec(BaseModel):
    """Specification for a configuration field."""

    key: str = Field(description="Field identifier")
    label: str = Field(description="Display label")
    type: FieldType = Field(description="Field type")
    description: Optional[str] = Field(None, description="Field description")
    required: bool = Field(False, description="Whether field is required")
    default: Any = Field(None, description="Default value")

    # Validation
    validation_rules: List[ValidationRule] = Field(default_factory=list, description="Validation rules")
    min_length: Optional[int] = Field(None, description="Minimum string length")
    max_length: Optional[int] = Field(None, description="Maximum string length")
    min_value: Optional[Union[int, float]] = Field(None, description="Minimum numeric value")
    max_value: Optional[Union[int, float]] = Field(None, description="Maximum numeric value")
    pattern: Optional[str] = Field(None, description="Regex pattern for validation")

    # Select field options
    options: List[SelectOption] = Field(default_factory=list, description="Options for select fields")

    # UI hints
    placeholder: Optional[str] = Field(None, description="Placeholder text")
    help_text: Optional[str] = Field(None, description="Help text")
    group: Optional[str] = Field(None, description="Field group for organization")
    order: int = Field(0, description="Display order within group")

    # Secret field properties
    is_secret: bool = Field(False, description="Whether field contains sensitive data")

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        """Validate field key format."""
        if not v or not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Field key must be alphanumeric with underscores/hyphens")
        return v

    def __init__(self, **data):
        """Initialize field spec and auto-set is_secret for SECRET type."""
        # Auto-set is_secret for SECRET field type
        if data.get('type') == FieldType.SECRET and 'is_secret' not in data:
            data['is_secret'] = True
        super().__init__(**data)


class PluginType(str, Enum):
    """Types of plugins supported by the system."""

    NOTIFICATION = "notification"
    PAYMENT = "payment"
    STORAGE = "storage"
    SEARCH = "search"
    AUTHENTICATION = "authentication"
    INTEGRATION = "integration"
    ANALYTICS = "analytics"
    WORKFLOW = "workflow"


class PluginStatus(str, Enum):
    """Plugin status states."""

    REGISTERED = "registered"
    CONFIGURED = "configured"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class PluginConfig(BaseModel):
    """Plugin configuration schema."""

    name: str = Field(description="Plugin name")
    type: PluginType = Field(description="Plugin type")
    version: str = Field(description="Plugin version")
    description: str = Field(description="Plugin description")
    author: Optional[str] = Field(None, description="Plugin author")
    homepage: Optional[str] = Field(None, description="Plugin homepage URL")

    # Configuration fields
    fields: List[FieldSpec] = Field(description="Configuration field specifications")

    # Plugin metadata
    dependencies: List[str] = Field(default_factory=list, description="Required dependencies")
    tags: List[str] = Field(default_factory=list, description="Plugin tags")

    # Feature flags
    supports_health_check: bool = Field(True, description="Whether plugin supports health checks")
    supports_test_connection: bool = Field(True, description="Whether plugin supports connection testing")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate plugin name format."""
        if not v or not v.replace("_", "").replace("-", "").replace(" ", "").isalnum():
            raise ValueError("Plugin name must be alphanumeric with spaces, underscores, or hyphens")
        return v

    @field_validator("fields")
    @classmethod
    def validate_unique_field_keys(cls, v: List[FieldSpec]) -> List[FieldSpec]:
        """Ensure field keys are unique."""
        keys = [field.key for field in v]
        if len(keys) != len(set(keys)):
            raise ValueError("Field keys must be unique")
        return v


class PluginInstance(BaseModel):
    """Instance of a registered plugin."""

    id: UUID = Field(description="Plugin instance ID")
    plugin_name: str = Field(description="Plugin name")
    instance_name: str = Field(description="Instance name (for multiple instances)")
    config_schema: PluginConfig = Field(description="Plugin configuration schema")

    # Current state
    status: PluginStatus = Field(PluginStatus.REGISTERED, description="Current plugin status")
    last_health_check: Optional[str] = Field(None, description="Last health check timestamp")
    last_error: Optional[str] = Field(None, description="Last error message")

    # Configuration (values are stored separately in secure storage)
    has_configuration: bool = Field(False, description="Whether plugin has been configured")
    configuration_version: Optional[str] = Field(None, description="Configuration version/hash")


class PluginConfigurationValue(BaseModel):
    """Plugin configuration field value."""

    plugin_instance_id: UUID = Field(description="Plugin instance ID")
    field_key: str = Field(description="Field identifier")
    value: Any = Field(description="Field value (None for secrets)")
    is_secret: bool = Field(False, description="Whether value is stored in secrets manager")
    masked: bool = Field(False, description="Whether value should be masked in responses")

    # Metadata
    created_at: str = Field(description="When value was set")
    updated_at: str = Field(description="When value was last updated")


class PluginHealthCheck(BaseModel):
    """Plugin health check result."""

    plugin_instance_id: UUID = Field(description="Plugin instance ID")
    status: str = Field(description="Health status (healthy/unhealthy/unknown)")
    message: Optional[str] = Field(None, description="Status message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")
    timestamp: str = Field(description="Check timestamp")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")


class PluginTestResult(BaseModel):
    """Plugin connection test result."""

    success: bool = Field(description="Whether test was successful")
    message: str = Field(description="Test result message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Test details")
    timestamp: str = Field(description="Test timestamp")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")


# API Response Models

class PluginConfigurationResponse(BaseModel):
    """Response model for plugin configuration."""

    plugin_instance_id: UUID = Field(description="Plugin instance ID")
    configuration: Dict[str, Any] = Field(description="Configuration values (secrets masked)")
    config_schema: PluginConfig = Field(description="Configuration schema", alias="schema")
    status: PluginStatus = Field(description="Plugin status")
    last_updated: Optional[str] = Field(None, description="Last configuration update")


class PluginListResponse(BaseModel):
    """Response model for plugin list."""

    plugins: List[PluginInstance] = Field(description="Registered plugin instances")
    total: int = Field(description="Total number of plugins")


class PluginSchemaResponse(BaseModel):
    """Response model for plugin schema."""

    config_schema: PluginConfig = Field(description="Plugin configuration schema", alias="schema")
    instance_id: Optional[UUID] = Field(None, description="Plugin instance ID if configured")