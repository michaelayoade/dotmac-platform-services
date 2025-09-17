"""
Data models for audit trail service.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class AuditLevel(str, Enum):
    """Audit event severity level."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    ALERT = "alert"


class AuditCategory(str, Enum):
    """Audit event category."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SYSTEM = "system"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    FINANCIAL = "financial"
    USER_MANAGEMENT = "user_management"
    CONFIGURATION = "configuration"
    API_CALL = "api_call"
    WORKFLOW = "workflow"


class AuditEvent(BaseModel):
    """Audit trail event."""

    id: str
    timestamp: datetime
    category: AuditCategory
    action: str
    level: AuditLevel = AuditLevel.INFO
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    service_name: Optional[str] = None
    correlation_id: Optional[str] = None
    parent_event_id: Optional[str] = None
    duration_ms: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None