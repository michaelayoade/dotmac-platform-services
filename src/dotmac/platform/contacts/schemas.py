"""
Contact System Pydantic Schemas

Request/response models for contact management.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict

from dotmac.platform.contacts.models import (
    ContactStatus, ContactStage, ContactMethodType, ContactFieldType
)


# Contact Method Schemas
class ContactMethodBase(BaseModel):
    """Base contact method schema."""
    type: ContactMethodType
    value: str = Field(min_length=1, max_length=500)
    label: Optional[str] = Field(None, max_length=50)
    is_primary: bool = False
    is_verified: bool = False
    is_public: bool = True
    display_order: int = 0
    metadata: Optional[Dict[str, Any]] = None

    # Address fields
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state_province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=2)  # ISO code


class ContactMethodCreate(ContactMethodBase):
    """Schema for creating contact method."""
    pass


class ContactMethodUpdate(BaseModel):
    """Schema for updating contact method."""
    value: Optional[str] = Field(None, min_length=1, max_length=500)
    label: Optional[str] = Field(None, max_length=50)
    is_primary: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_public: Optional[bool] = None
    display_order: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

    # Address fields
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state_province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=2)


class ContactMethodResponse(ContactMethodBase):
    """Contact method response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    contact_id: UUID
    verified_at: Optional[datetime] = None
    verified_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


# Contact Schemas
class ContactBase(BaseModel):
    """Base contact schema."""
    # Name fields
    first_name: Optional[str] = Field(None, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=255)
    prefix: Optional[str] = Field(None, max_length=20)
    suffix: Optional[str] = Field(None, max_length=20)

    # Organization
    company: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)
    department: Optional[str] = Field(None, max_length=255)

    # Status
    status: Optional[ContactStatus] = None
    stage: Optional[ContactStage] = None

    # Ownership
    owner_id: Optional[UUID] = None
    assigned_team_id: Optional[UUID] = None

    # Notes and metadata
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    # Important dates
    birthday: Optional[datetime] = None
    anniversary: Optional[datetime] = None

    # Flags
    is_primary: bool = False
    is_decision_maker: bool = False
    is_billing_contact: bool = False
    is_technical_contact: bool = False

    # Preferences
    preferred_contact_method: Optional[ContactMethodType] = None
    preferred_language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)


class ContactCreate(ContactBase):
    """Schema for creating contact."""
    customer_id: Optional[UUID] = None
    contact_methods: Optional[List[ContactMethodCreate]] = None
    label_ids: Optional[List[UUID]] = None

    @field_validator('display_name')
    @classmethod
    def validate_display_name(cls, v, values):
        """Ensure display name is set."""
        if v:
            return v

        # Generate from name fields
        parts = []
        if 'first_name' in values.data and values.data['first_name']:
            parts.append(values.data['first_name'])
        if 'last_name' in values.data and values.data['last_name']:
            parts.append(values.data['last_name'])

        if parts:
            return " ".join(parts)

        # Fall back to company
        if 'company' in values.data and values.data['company']:
            return values.data['company']

        return None  # Will be handled in service


class ContactUpdate(BaseModel):
    """Schema for updating contact."""
    # Name fields
    first_name: Optional[str] = Field(None, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=255)
    prefix: Optional[str] = Field(None, max_length=20)
    suffix: Optional[str] = Field(None, max_length=20)

    # Organization
    company: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)
    department: Optional[str] = Field(None, max_length=255)

    # Status
    status: Optional[ContactStatus] = None
    stage: Optional[ContactStage] = None

    # Ownership
    owner_id: Optional[UUID] = None
    assigned_team_id: Optional[UUID] = None

    # Notes and metadata
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    # Important dates
    birthday: Optional[datetime] = None
    anniversary: Optional[datetime] = None

    # Flags
    is_primary: Optional[bool] = None
    is_decision_maker: Optional[bool] = None
    is_billing_contact: Optional[bool] = None
    is_technical_contact: Optional[bool] = None
    is_verified: Optional[bool] = None

    # Preferences
    preferred_contact_method: Optional[ContactMethodType] = None
    preferred_language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)


class ContactResponse(ContactBase):
    """Contact response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    customer_id: Optional[UUID] = None
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_contacted_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    # Relationships
    contact_methods: Optional[List[ContactMethodResponse]] = None
    labels: Optional[List['ContactLabelDefinitionResponse']] = None


class ContactListResponse(BaseModel):
    """Response for contact list."""
    contacts: List[ContactResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


# Label Schemas
class ContactLabelDefinitionBase(BaseModel):
    """Base label definition schema."""
    name: str = Field(min_length=1, max_length=100)
    slug: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, max_length=7)  # Hex color
    icon: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=50)
    display_order: int = 0
    is_visible: bool = True
    is_system: bool = False
    is_default: bool = False
    metadata: Optional[Dict[str, Any]] = None


class ContactLabelDefinitionCreate(ContactLabelDefinitionBase):
    """Schema for creating label definition."""
    pass


class ContactLabelDefinitionUpdate(BaseModel):
    """Schema for updating label definition."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, max_length=7)
    icon: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=50)
    display_order: Optional[int] = None
    is_visible: Optional[bool] = None
    is_default: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class ContactLabelDefinitionResponse(ContactLabelDefinitionBase):
    """Label definition response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None


# Field Definition Schemas
class ContactFieldDefinitionBase(BaseModel):
    """Base field definition schema."""
    name: str = Field(min_length=1, max_length=100)
    field_key: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    field_type: ContactFieldType
    is_required: bool = False
    is_unique: bool = False
    is_searchable: bool = True
    default_value: Optional[Any] = None
    validation_rules: Optional[Dict[str, Any]] = None
    options: Optional[List[Dict[str, Any]]] = None
    display_order: int = 0
    placeholder: Optional[str] = Field(None, max_length=255)
    help_text: Optional[str] = None
    field_group: Optional[str] = Field(None, max_length=100)
    is_visible: bool = True
    is_editable: bool = True
    required_permission: Optional[str] = Field(None, max_length=100)
    is_system: bool = False
    is_encrypted: bool = False
    metadata: Optional[Dict[str, Any]] = None


class ContactFieldDefinitionCreate(ContactFieldDefinitionBase):
    """Schema for creating field definition."""
    pass


class ContactFieldDefinitionUpdate(BaseModel):
    """Schema for updating field definition."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_required: Optional[bool] = None
    is_unique: Optional[bool] = None
    is_searchable: Optional[bool] = None
    default_value: Optional[Any] = None
    validation_rules: Optional[Dict[str, Any]] = None
    options: Optional[List[Dict[str, Any]]] = None
    display_order: Optional[int] = None
    placeholder: Optional[str] = Field(None, max_length=255)
    help_text: Optional[str] = None
    field_group: Optional[str] = Field(None, max_length=100)
    is_visible: Optional[bool] = None
    is_editable: Optional[bool] = None
    required_permission: Optional[str] = Field(None, max_length=100)
    is_encrypted: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class ContactFieldDefinitionResponse(ContactFieldDefinitionBase):
    """Field definition response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None


# Activity Schemas
class ContactActivityBase(BaseModel):
    """Base activity schema."""
    activity_type: str = Field(min_length=1, max_length=50)
    subject: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    activity_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    status: str = Field(min_length=1, max_length=50)
    outcome: Optional[str] = Field(None, max_length=100)
    metadata: Optional[Dict[str, Any]] = None


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
    query: Optional[str] = None
    customer_id: Optional[UUID] = None
    status: Optional[ContactStatus] = None
    stage: Optional[ContactStage] = None
    owner_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    label_ids: Optional[List[UUID]] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=500)
    include_deleted: bool = False


# Bulk Operations
class ContactBulkUpdate(BaseModel):
    """Schema for bulk contact updates."""
    contact_ids: List[UUID]
    update_data: ContactUpdate


class ContactBulkDelete(BaseModel):
    """Schema for bulk contact deletion."""
    contact_ids: List[UUID]
    hard_delete: bool = False