"""Add audit_activities table

Revision ID: add_audit_activities
Revises: c6c1a94cd6c0
Create Date: 2025-09-25 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "add_audit_activities"
down_revision: Union[str, None] = "c6c1a94cd6c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create audit_activities table
    op.create_table(
        "audit_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("activity_type", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("user_id", sa.String(length=255), nullable=True),
        sa.Column("tenant_id", sa.String(length=255), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=True),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("request_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for common queries
    op.create_index("ix_audit_activities_activity_type", "audit_activities", ["activity_type"])
    op.create_index("ix_audit_activities_severity", "audit_activities", ["severity"])
    op.create_index("ix_audit_activities_user_id", "audit_activities", ["user_id"])
    op.create_index("ix_audit_activities_tenant_id", "audit_activities", ["tenant_id"])
    op.create_index("ix_audit_activities_timestamp", "audit_activities", ["timestamp"])
    op.create_index(
        "ix_audit_activities_user_timestamp", "audit_activities", ["user_id", "timestamp"]
    )
    op.create_index(
        "ix_audit_activities_tenant_timestamp", "audit_activities", ["tenant_id", "timestamp"]
    )
    op.create_index(
        "ix_audit_activities_type_timestamp", "audit_activities", ["activity_type", "timestamp"]
    )
    op.create_index(
        "ix_audit_activities_severity_timestamp", "audit_activities", ["severity", "timestamp"]
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_audit_activities_severity_timestamp", table_name="audit_activities")
    op.drop_index("ix_audit_activities_type_timestamp", table_name="audit_activities")
    op.drop_index("ix_audit_activities_tenant_timestamp", table_name="audit_activities")
    op.drop_index("ix_audit_activities_user_timestamp", table_name="audit_activities")
    op.drop_index("ix_audit_activities_timestamp", table_name="audit_activities")
    op.drop_index("ix_audit_activities_tenant_id", table_name="audit_activities")
    op.drop_index("ix_audit_activities_user_id", table_name="audit_activities")
    op.drop_index("ix_audit_activities_severity", table_name="audit_activities")
    op.drop_index("ix_audit_activities_activity_type", table_name="audit_activities")

    # Drop table
    op.drop_table("audit_activities")
