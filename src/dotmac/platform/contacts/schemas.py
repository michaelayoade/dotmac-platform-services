"""
Contact System Pydantic Schemas

Request/response models for contact management.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from dotmac.platform.contacts.models import (
    ContactFieldType,
    ContactMethodType,
    ContactStage,
    ContactStatus,
)


# Contact Method Schemas
class ContactMethodBase(BaseModel):
    """Base contact method schema."""

    type: ContactMethodType
    value: str = Field(min_length=1, max_length=500)
    label: str | None = Field(None, max_length=50)
    is_primary: bool = False
    is_verified: bool = False
    is_public: bool = True
    display_order: int = 0
    metadata: dict[str, Any] | None = None

    # Address fields
    address_line1: str | None = Field(None, max_length=255)
    address_line2: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    state_province: str | None = Field(None, max_length=100)
    postal_code: str | None = Field(None, max_length=20)
    country: str | None = Field(None, max_length=2)  # ISO code


class ContactMethodCreate(ContactMethodBase):
    """Schema for creating contact method."""

    pass


class ContactMethodUpdate(BaseModel):
    """Schema for updating contact method."""

    value: str | None = Field(None, min_length=1, max_length=500)
    label: str | None = Field(None, max_length=50)
    is_primary: bool | None = None
    is_verified: bool | None = None
    is_public: bool | None = None
    display_order: int | None = None
    metadata: dict[str, Any] | None = None

    # Address fields
    address_line1: str | None = Field(None, max_length=255)
    address_line2: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    state_province: str | None = Field(None, max_length=100)
    postal_code: str | None = Field(None, max_length=20)
    country: str | None = Field(None, max_length=2)


class ContactMethodResponse(ContactMethodBase):
    """Contact method response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    contact_id: UUID
    verified_at: datetime | None = None
    verified_by: UUID | None = None
    created_at: datetime
    updated_at: datetime


# Contact Schemas
class ContactBase(BaseModel):
    """Base contact schema."""

    # Name fields
    first_name: str | None = Field(None, max_length=100)
    middle_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    display_name: str | None = Field(None, max_length=255)
    prefix: str | None = Field(None, max_length=20)
    suffix: str | None = Field(None, max_length=20)

    # Organization
    company: str | None = Field(None, max_length=255)
    job_title: str | None = Field(None, max_length=255)
    department: str | None = Field(None, max_length=255)

    # Status
    status: ContactStatus | None = None
    stage: ContactStage | None = None

    # Ownership
    owner_id: UUID | None = None
    assigned_team_id: UUID | None = None

    # Notes and metadata
    notes: str | None = None
    tags: list[str] | None = None
    custom_fields: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None

    # Important dates
    birthday: datetime | None = None
    anniversary: datetime | None = None

    # Flags
    is_primary: bool = False
    is_decision_maker: bool = False
    is_billing_contact: bool = False
    is_technical_contact: bool = False

    # Preferences
    preferred_contact_method: ContactMethodType | None = None
    preferred_language: str | None = Field(None, max_length=10)
    timezone: str | None = Field(None, max_length=50)


class ContactCreate(ContactBase):
    """Schema for creating contact."""

    customer_id: UUID | None = None
    contact_methods: list[ContactMethodCreate] | None = None
    label_ids: list[UUID] | None = None

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v, values) -> Any:
        """Ensure display name is set."""
        if v:
            return v

        # Generate from name fields
        parts = []
        if "first_name" in values.data and values.data["first_name"]:
            parts.append(values.data["first_name"])
        if "last_name" in values.data and values.data["last_name"]:
            parts.append(values.data["last_name"])

        if parts:
            return " ".join(parts)

        # Fall back to company
        if "company" in values.data and values.data["company"]:
            return values.data["company"]

        return None  # Will be handled in service


class ContactUpdate(BaseModel):
    """Schema for updating contact."""

    # Name fields
    first_name: str | None = Field(None, max_length=100)
    middle_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    display_name: str | None = Field(None, max_length=255)
    prefix: str | None = Field(None, max_length=20)
    suffix: str | None = Field(None, max_length=20)

    # Organization
    company: str | None = Field(None, max_length=255)
    job_title: str | None = Field(None, max_length=255)
    department: str | None = Field(None, max_length=255)

    # Status
    status: ContactStatus | None = None
    stage: ContactStage | None = None

    # Ownership
    owner_id: UUID | None = None
    assigned_team_id: UUID | None = None

    # Notes and metadata
    notes: str | None = None
    tags: list[str] | None = None
    custom_fields: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None

    # Important dates
    birthday: datetime | None = None
    anniversary: datetime | None = None

    # Flags
    is_primary: bool | None = None
    is_decision_maker: bool | None = None
    is_billing_contact: bool | None = None
    is_technical_contact: bool | None = None
    is_verified: bool | None = None

    # Preferences
    preferred_contact_method: ContactMethodType | None = None
    preferred_language: str | None = Field(None, max_length=10)
    timezone: str | None = Field(None, max_length=50)


class ContactResponse(ContactBase):
    """Contact response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    customer_id: UUID | None = None
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_contacted_at: datetime | None = None
    deleted_at: datetime | None = None

    # Relationships
    contact_methods: list[ContactMethodResponse] | None = None
    labels: list["ContactLabelDefinitionResponse"] | None = None


class ContactListResponse(BaseModel):
    """Response for contact list."""

    contacts: list[ContactResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


# Label Schemas
class ContactLabelDefinitionBase(BaseModel):
    """Base label definition schema."""

    name: str = Field(min_length=1, max_length=100)
    slug: str | None = Field(None, max_length=100)
    description: str | None = None
    color: str | None = Field(None, max_length=7)  # Hex color
    icon: str | None = Field(None, max_length=50)
    category: str | None = Field(None, max_length=50)
    display_order: int = 0
    is_visible: bool = True
    is_system: bool = False
    is_default: bool = False
    metadata: dict[str, Any] | None = None


class ContactLabelDefinitionCreate(ContactLabelDefinitionBase):
    """Schema for creating label definition."""

    pass


class ContactLabelDefinitionUpdate(BaseModel):
    """Schema for updating label definition."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    color: str | None = Field(None, max_length=7)
    icon: str | None = Field(None, max_length=50)
    category: str | None = Field(None, max_length=50)
    display_order: int | None = None
    is_visible: bool | None = None
    is_default: bool | None = None
    metadata: dict[str, Any] | None = None


class ContactLabelDefinitionResponse(ContactLabelDefinitionBase):
    """Label definition response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None


# Field Definition Schemas
class ContactFieldDefinitionBase(BaseModel):
    """Base field definition schema."""

    name: str = Field(min_length=1, max_length=100)
    field_key: str | None = Field(None, max_length=100)
    description: str | None = None
    field_type: ContactFieldType
    is_required: bool = False
    is_unique: bool = False
    is_searchable: bool = True
    default_value: Any | None = None
    validation_rules: dict[str, Any] | None = None
    options: list[dict[str, Any]] | None = None
    display_order: int = 0
    placeholder: str | None = Field(None, max_length=255)
    help_text: str | None = None
    field_group: str | None = Field(None, max_length=100)
    is_visible: bool = True
    is_editable: bool = True
    required_permission: str | None = Field(None, max_length=100)
    is_system: bool = False
    is_encrypted: bool = False
    metadata: dict[str, Any] | None = None


class ContactFieldDefinitionCreate(ContactFieldDefinitionBase):
    """Schema for creating field definition."""

    pass


class ContactFieldDefinitionUpdate(BaseModel):
    """Schema for updating field definition."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    is_required: bool | None = None
    is_unique: bool | None = None
    is_searchable: bool | None = None
    default_value: Any | None = None
    validation_rules: dict[str, Any] | None = None
    options: list[dict[str, Any]] | None = None
    display_order: int | None = None
    placeholder: str | None = Field(None, max_length=255)
    help_text: str | None = None
    field_group: str | None = Field(None, max_length=100)
    is_visible: bool | None = None
    is_editable: bool | None = None
    required_permission: str | None = Field(None, max_length=100)
    is_encrypted: bool | None = None
    metadata: dict[str, Any] | None = None


class ContactFieldDefinitionResponse(ContactFieldDefinitionBase):
    """Field definition response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None


# Activity Schemas
class ContactActivityBase(BaseModel):
    """Base activity schema."""

    activity_type: str = Field(min_length=1, max_length=50)
    subject: str = Field(min_length=1, max_length=255)
    description: str | None = None
    activity_date: datetime | None = None
    duration_minutes: int | None = None
    status: str = Field(min_length=1, max_length=50)
    outcome: str | None = Field(None, max_length=100)
    metadata: dict[str, Any] | None = None


class ContactActivityCreate(ContactActivityBase):
    """Schema for creating activity."""

    pass


class ContactActivityResponse(ContactActivityBase):
    """Activity response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    contact_id: UUID
    performed_by: UUID
    created_at: datetime
    updated_at: datetime


# Search Schemas
class ContactSearchRequest(BaseModel):
    """Contact search request schema."""

    query: str | None = None
    customer_id: UUID | None = None
    status: ContactStatus | None = None
    stage: ContactStage | None = None
    owner_id: UUID | None = None
    tags: list[str] | None = None
    label_ids: list[UUID] | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=500)
    include_deleted: bool = False


# Bulk Operations
class ContactBulkUpdate(BaseModel):
    """Schema for bulk contact updates."""

    contact_ids: list[UUID]
    update_data: ContactUpdate


class ContactBulkDelete(BaseModel):
    """Schema for bulk contact deletion."""

    contact_ids: list[UUID]
    hard_delete: bool = False
