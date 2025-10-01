"""
Audit and activity tracking models for the DotMac platform.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict, field_validator
from sqlalchemy import String, DateTime, Text, Index, JSON
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, TimestampMixin, StrictTenantMixin


class ActivityType(str, Enum):
    """Types of activities that can be audited."""
    # Auth activities
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"

    # RBAC activities
    ROLE_CREATED = "rbac.role.created"
    ROLE_UPDATED = "rbac.role.updated"
    ROLE_DELETED = "rbac.role.deleted"
    ROLE_ASSIGNED = "rbac.role.assigned"
    ROLE_REVOKED = "rbac.role.revoked"
    PERMISSION_GRANTED = "rbac.permission.granted"
    PERMISSION_REVOKED = "rbac.permission.revoked"
    PERMISSION_CREATED = "rbac.permission.created"
    PERMISSION_UPDATED = "rbac.permission.updated"
    PERMISSION_DELETED = "rbac.permission.deleted"

    # Secret activities
    SECRET_CREATED = "secret.created"
    SECRET_ACCESSED = "secret.accessed"
    SECRET_UPDATED = "secret.updated"
    SECRET_DELETED = "secret.deleted"

    # File activities
    FILE_UPLOADED = "file.uploaded"
    FILE_DOWNLOADED = "file.downloaded"
    FILE_DELETED = "file.deleted"

    # API activities
    API_REQUEST = "api.request"
    API_ERROR = "api.error"

    # System activities
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"


class ActivitySeverity(str, Enum):
    """Severity levels for activities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditActivity(Base, TimestampMixin, StrictTenantMixin):
    """Audit activity tracking table."""
    __tablename__ = "audit_activities"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )

    # Activity identification
    activity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), default=ActivitySeverity.LOW, index=True)

    # Who and when
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    # tenant_id is inherited from StrictTenantMixin and is NOT NULL
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    # What and where
    resource_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)

    # Details
    description: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Indexes for common queries
    __table_args__ = (
        Index('ix_audit_activities_user_timestamp', 'user_id', 'timestamp'),
        Index('ix_audit_activities_tenant_timestamp', 'tenant_id', 'timestamp'),
        Index('ix_audit_activities_type_timestamp', 'activity_type', 'timestamp'),
        Index('ix_audit_activities_severity_timestamp', 'severity', 'timestamp'),
    )


# Pydantic models for API

class AuditActivityCreate(BaseModel):
    """Model for creating audit activities."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )

    activity_type: ActivityType
    severity: ActivitySeverity = ActivitySeverity.LOW
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None  # Will be auto-populated by validator
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None

    @field_validator('tenant_id', mode='before')
    @classmethod
    def validate_tenant_id(cls, v):
        """Auto-populate tenant_id from context if not provided."""
        if v is None or v == "":
            from ..tenant import get_current_tenant_id
            v = get_current_tenant_id()
        if not v:
            raise ValueError("tenant_id is required and could not be resolved from context")
        return v
    action: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1)
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None


class AuditActivityResponse(BaseModel):
    """Model for audit activity responses."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    activity_type: str
    severity: str
    user_id: Optional[str]
    tenant_id: str  # Always present
    timestamp: datetime
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: str
    description: str
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]


class AuditActivityList(BaseModel):
    """Model for paginated audit activity lists."""
    activities: list[AuditActivityResponse]
    total: int
    page: int = 1
    per_page: int = 50
    has_next: bool
    has_prev: bool


class AuditFilterParams(BaseModel):
    """Model for audit activity filtering parameters."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )

    user_id: Optional[str] = None
    tenant_id: str  # Required for filtering
    activity_type: Optional[ActivityType] = None
    severity: Optional[ActivitySeverity] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=50, ge=1, le=1000)