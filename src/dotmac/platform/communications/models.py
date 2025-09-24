"""
Enhanced communications models with database support and Jinja2 templating.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

try:
    from ..db import Base
except ImportError:
    # Fallback if db module is not available
    from sqlalchemy.orm import DeclarativeBase
    class Base(DeclarativeBase):
        pass
from . import NotificationPriority, NotificationStatus, NotificationType


class BulkJobStatus(str, Enum):
    """Bulk job processing status."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Database Models
class EmailTemplate(Base):
    """Email template database model."""

    __tablename__ = "email_templates"
    __table_args__ = {'extend_existing': True}

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: str(uuid4())[:8])
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Template content
    subject_template: Mapped[str] = mapped_column(Text, nullable=False)
    html_template: Mapped[str] = mapped_column(Text, nullable=False)
    text_template: Mapped[Optional[str]] = mapped_column(Text)

    # Template metadata
    variables: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Required/optional variables
    category: Mapped[Optional[str]] = mapped_column(String(100))  # e.g., 'transactional', 'marketing'
    is_active: Mapped[bool] = mapped_column(default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<EmailTemplate(id={self.id}, name={self.name})>"


class BulkEmailJob(Base):
    """Bulk email job database model."""

    __tablename__ = "bulk_email_jobs"
    __table_args__ = {'extend_existing': True}

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: str(uuid4())[:12])
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_id: Mapped[str] = mapped_column(String(50), nullable=False)

    # Job configuration
    recipients: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False)  # List of recipient data
    template_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Global template variables

    # Job status and metrics
    status: Mapped[BulkJobStatus] = mapped_column(default=BulkJobStatus.QUEUED)
    total_recipients: Mapped[int] = mapped_column(Integer, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)

    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)

    # Timestamps
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<BulkEmailJob(id={self.id}, status={self.status}, recipients={self.total_recipients})>"


class EmailDelivery(Base):
    """Email delivery tracking model."""

    __tablename__ = "email_deliveries"
    __table_args__ = {'extend_existing': True}

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: str(uuid4())[:12])
    job_id: Mapped[Optional[str]] = mapped_column(String(50))  # Reference to bulk job
    template_id: Mapped[Optional[str]] = mapped_column(String(50))

    # Email details
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)

    # Delivery tracking
    status: Mapped[NotificationStatus] = mapped_column(default=NotificationStatus.PENDING)
    priority: Mapped[NotificationPriority] = mapped_column(default=NotificationPriority.NORMAL)
    provider_id: Mapped[Optional[str]] = mapped_column(String(100))  # e.g., sendgrid message ID

    # Timestamps and attempts
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    delivery_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<EmailDelivery(id={self.id}, recipient={self.recipient_email}, status={self.status})>"


# Pydantic Models for API
class EmailTemplateBase(BaseModel):
    """Base email template schema."""

    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    subject_template: str = Field(min_length=1)
    html_template: str = Field(min_length=1)
    text_template: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    is_active: bool = True


class EmailTemplateCreate(EmailTemplateBase):
    """Email template creation schema."""

    @field_validator('subject_template', 'html_template')
    @classmethod
    def validate_templates(cls, v: str) -> str:
        """Validate that templates are not empty."""
        if not v.strip():
            raise ValueError("Template content cannot be empty")
        return v


class EmailTemplateUpdate(BaseModel):
    """Email template update schema."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    subject_template: Optional[str] = Field(None, min_length=1)
    html_template: Optional[str] = Field(None, min_length=1)
    text_template: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


class EmailTemplateResponse(EmailTemplateBase):
    """Email template response schema."""

    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecipientData(BaseModel):
    """Recipient data for bulk emails."""

    email: str = Field(pattern=r'^[^@]+@[^@]+\.[^@]+$')
    name: Optional[str] = None
    custom_data: Optional[Dict[str, Any]] = None  # Additional template variables


class BulkEmailJobCreate(BaseModel):
    """Bulk email job creation schema."""

    name: str = Field(min_length=1, max_length=255)
    template_id: str = Field(min_length=1)
    recipients: List[RecipientData] = Field(min_items=1, max_items=10000)  # Limit bulk size
    template_data: Optional[Dict[str, Any]] = None  # Global template variables
    scheduled_at: Optional[datetime] = None

    @field_validator('recipients')
    @classmethod
    def validate_recipients(cls, v: List[RecipientData]) -> List[RecipientData]:
        """Validate recipient list."""
        if len(v) == 0:
            raise ValueError("Recipients list cannot be empty")

        # Check for duplicate emails
        emails = [recipient.email for recipient in v]
        if len(emails) != len(set(emails)):
            raise ValueError("Duplicate email addresses found in recipients list")

        return v


class BulkEmailJobResponse(BaseModel):
    """Bulk email job response schema."""

    id: str
    name: str
    template_id: str
    status: BulkJobStatus
    total_recipients: int
    sent_count: int
    failed_count: int
    error_message: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    @property
    def progress_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total_recipients == 0:
            return 0.0
        return ((self.sent_count + self.failed_count) / self.total_recipients) * 100

    class Config:
        from_attributes = True


class EmailDeliveryResponse(BaseModel):
    """Email delivery response schema."""

    id: str
    job_id: Optional[str] = None
    template_id: Optional[str] = None
    recipient_email: str
    subject: str
    status: NotificationStatus
    priority: NotificationPriority
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    attempt_count: int
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TemplatePreviewRequest(BaseModel):
    """Template preview request schema."""

    template_data: Dict[str, Any] = Field(default_factory=dict)


class TemplatePreviewResponse(BaseModel):
    """Template preview response schema."""

    subject: str
    html_content: str
    text_content: Optional[str] = None
    variables_used: List[str]
    missing_variables: List[str] = Field(default_factory=list)


class BulkJobStatsResponse(BaseModel):
    """Bulk job statistics response."""

    total_jobs: int
    active_jobs: int
    completed_jobs: int
    failed_jobs: int
    total_emails_sent: int
    success_rate: float