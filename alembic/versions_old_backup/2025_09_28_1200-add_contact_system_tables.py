"""Add contact system tables

Revision ID: add_contact_system_tables
Revises: 2025_09_25_1000-add_audit_activities_table
Create Date: 2025-09-28 12:00:00

"""

from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_contact_system_tables"
down_revision = "add_audit_activities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create contact system tables."""

    # Create contacts table
    op.create_table(
        "contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id", ondelete="CASCADE"),
            nullable=True,
        ),
        # Name fields
        sa.Column("first_name", sa.String(100), nullable=True),
        sa.Column("middle_name", sa.String(100), nullable=True),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("prefix", sa.String(20), nullable=True),
        sa.Column("suffix", sa.String(20), nullable=True),
        # Organization
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("job_title", sa.String(255), nullable=True),
        sa.Column("department", sa.String(255), nullable=True),
        # Status and lifecycle
        sa.Column("status", sa.String(50), nullable=False, default="active"),
        sa.Column("stage", sa.String(50), nullable=False, default="prospect"),
        # Ownership
        sa.Column(
            "owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column(
            "assigned_team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("teams.id"),
            nullable=True,
        ),
        # Notes and metadata
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("tags", sa.JSON, nullable=True, default=list),
        sa.Column("custom_fields", postgresql.JSONB, nullable=True, default=dict),
        sa.Column("metadata", postgresql.JSONB, nullable=True, default=dict),
        # Important dates
        sa.Column("birthday", sa.DateTime(timezone=True), nullable=True),
        sa.Column("anniversary", sa.DateTime(timezone=True), nullable=True),
        # Flags
        sa.Column("is_primary", sa.Boolean, nullable=False, default=False),
        sa.Column("is_decision_maker", sa.Boolean, nullable=False, default=False),
        sa.Column("is_billing_contact", sa.Boolean, nullable=False, default=False),
        sa.Column("is_technical_contact", sa.Boolean, nullable=False, default=False),
        sa.Column("is_verified", sa.Boolean, nullable=False, default=False),
        # Preferences
        sa.Column("preferred_contact_method", sa.String(50), nullable=True),
        sa.Column("preferred_language", sa.String(10), nullable=True),
        sa.Column("timezone", sa.String(50), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("last_contacted_at", sa.DateTime(timezone=True), nullable=True),
        # Soft delete
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.CheckConstraint(
            "display_name IS NOT NULL AND display_name != ''", name="check_display_name_not_empty"
        ),
    )

    # Create indexes for contacts
    op.create_index("ix_contacts_tenant_id", "contacts", ["tenant_id"])
    op.create_index("ix_contacts_customer_id", "contacts", ["customer_id"])
    op.create_index("ix_contacts_display_name", "contacts", ["display_name"])
    op.create_index("ix_contacts_company", "contacts", ["company"])
    op.create_index("ix_contacts_status", "contacts", ["status"])
    op.create_index("ix_contacts_stage", "contacts", ["stage"])
    op.create_index("ix_contacts_owner_id", "contacts", ["owner_id"])
    op.create_index("ix_contacts_deleted_at", "contacts", ["deleted_at"])

    # Create contact_methods table
    op.create_table(
        "contact_methods",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column(
            "contact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("contacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Contact method details
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("value", sa.String(500), nullable=False),
        sa.Column("label", sa.String(50), nullable=True),
        # For addresses
        sa.Column("address_line1", sa.String(255), nullable=True),
        sa.Column("address_line2", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state_province", sa.String(100), nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("country", sa.String(2), nullable=True),
        # Flags
        sa.Column("is_primary", sa.Boolean, nullable=False, default=False),
        sa.Column("is_verified", sa.Boolean, nullable=False, default=False),
        sa.Column("is_public", sa.Boolean, nullable=False, default=True),
        # Verification
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "verified_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column("verification_token", sa.String(255), nullable=True),
        # Display order
        sa.Column("display_order", sa.Integer, nullable=False, default=0),
        # Metadata
        sa.Column("metadata", sa.JSON, nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint("contact_id", "type", "value", name="uq_contact_method"),
    )

    # Create indexes for contact_methods
    op.create_index("ix_contact_methods_contact_id", "contact_methods", ["contact_id"])
    op.create_index("ix_contact_methods_type", "contact_methods", ["type"])
    op.create_index("ix_contact_methods_value", "contact_methods", ["value"])
    op.create_index("ix_contact_methods_is_primary", "contact_methods", ["is_primary"])

    # Create contact_label_definitions table
    op.create_table(
        "contact_label_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Label details
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        # Visual
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column("icon", sa.String(50), nullable=True),
        # Category
        sa.Column("category", sa.String(50), nullable=True),
        # Display
        sa.Column("display_order", sa.Integer, nullable=False, default=0),
        sa.Column("is_visible", sa.Boolean, nullable=False, default=True),
        # System flags
        sa.Column("is_system", sa.Boolean, nullable=False, default=False),
        sa.Column("is_default", sa.Boolean, nullable=False, default=False),
        # Metadata
        sa.Column("metadata", sa.JSON, nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.UniqueConstraint("tenant_id", "slug", name="uq_tenant_label_slug"),
    )

    # Create indexes for label definitions
    op.create_index(
        "ix_contact_label_definitions_tenant_id", "contact_label_definitions", ["tenant_id"]
    )
    op.create_index("ix_contact_label_definitions_slug", "contact_label_definitions", ["slug"])
    op.create_index(
        "ix_contact_label_definitions_category", "contact_label_definitions", ["category"]
    )

    # Create contact_to_labels association table
    op.create_table(
        "contact_to_labels",
        sa.Column(
            "contact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("contacts.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "label_definition_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("contact_label_definitions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "assigned_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.UniqueConstraint("contact_id", "label_definition_id", name="uq_contact_label"),
    )

    # Create indexes for contact labels
    op.create_index("ix_contact_labels_contact_id", "contact_to_labels", ["contact_id"])
    op.create_index(
        "ix_contact_labels_label_definition_id", "contact_to_labels", ["label_definition_id"]
    )

    # Create contact_field_definitions table
    op.create_table(
        "contact_field_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Field details
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("field_key", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        # Field type and validation
        sa.Column("field_type", sa.String(50), nullable=False),
        sa.Column("is_required", sa.Boolean, nullable=False, default=False),
        sa.Column("is_unique", sa.Boolean, nullable=False, default=False),
        sa.Column("is_searchable", sa.Boolean, nullable=False, default=True),
        # Default value
        sa.Column("default_value", sa.JSON, nullable=True),
        # Validation rules
        sa.Column("validation_rules", sa.JSON, nullable=True),
        # Options for select fields
        sa.Column("options", sa.JSON, nullable=True),
        # Display configuration
        sa.Column("display_order", sa.Integer, nullable=False, default=0),
        sa.Column("placeholder", sa.String(255), nullable=True),
        sa.Column("help_text", sa.Text, nullable=True),
        # Grouping
        sa.Column("field_group", sa.String(100), nullable=True),
        # Visibility and permissions
        sa.Column("is_visible", sa.Boolean, nullable=False, default=True),
        sa.Column("is_editable", sa.Boolean, nullable=False, default=True),
        sa.Column("required_permission", sa.String(100), nullable=True),
        # System flags
        sa.Column("is_system", sa.Boolean, nullable=False, default=False),
        sa.Column("is_encrypted", sa.Boolean, nullable=False, default=False),
        # Metadata
        sa.Column("metadata", sa.JSON, nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.UniqueConstraint("tenant_id", "field_key", name="uq_tenant_field_key"),
    )

    # Create indexes for field definitions
    op.create_index(
        "ix_contact_field_definitions_tenant_id", "contact_field_definitions", ["tenant_id"]
    )
    op.create_index(
        "ix_contact_field_definitions_field_key", "contact_field_definitions", ["field_key"]
    )
    op.create_index(
        "ix_contact_field_definitions_field_group", "contact_field_definitions", ["field_group"]
    )

    # Create contact_activities table
    op.create_table(
        "contact_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column(
            "contact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("contacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Activity details
        sa.Column("activity_type", sa.String(50), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        # Timing
        sa.Column("activity_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer, nullable=True),
        # Status
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("outcome", sa.String(100), nullable=True),
        # User tracking
        sa.Column(
            "performed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        # Metadata
        sa.Column("metadata", sa.JSON, nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Create indexes for activities
    op.create_index("ix_contact_activities_contact_id", "contact_activities", ["contact_id"])
    op.create_index("ix_contact_activities_activity_type", "contact_activities", ["activity_type"])
    op.create_index("ix_contact_activities_activity_date", "contact_activities", ["activity_date"])
    op.create_index("ix_contact_activities_performed_by", "contact_activities", ["performed_by"])


def downgrade() -> None:
    """Drop contact system tables."""

    # Drop tables in reverse order
    op.drop_table("contact_activities")
    op.drop_table("contact_field_definitions")
    op.drop_table("contact_to_labels")
    op.drop_table("contact_label_definitions")
    op.drop_table("contact_methods")
    op.drop_table("contacts")
