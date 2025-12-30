"""Create admin settings tables.

Revision ID: 2025_12_26_1700
Revises: 2025_12_26_1600
Create Date: 2025-12-26 17:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "create_admin_settings_tables"
down_revision: str | None = "create_api_keys_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create admin_settings_store table
    op.create_table(
        "admin_settings_store",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("settings_data", postgresql.JSON(), nullable=False),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category"),
    )
    op.create_index("ix_admin_settings_store_id", "admin_settings_store", ["id"])
    op.create_index("ix_admin_settings_store_category", "admin_settings_store", ["category"])

    # Create admin_settings_audit_log table
    op.create_table(
        "admin_settings_audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("user_id", sa.String(255), nullable=True),
        sa.Column("user_email", sa.String(255), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("changes", postgresql.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_settings_audit_log_id", "admin_settings_audit_log", ["id"])
    op.create_index("ix_admin_settings_audit_log_tenant_id", "admin_settings_audit_log", ["tenant_id"])
    op.create_index("ix_admin_settings_audit_log_category", "admin_settings_audit_log", ["category"])
    op.create_index("ix_admin_settings_audit_log_user_id", "admin_settings_audit_log", ["user_id"])

    # Create admin_settings_backups table
    op.create_table(
        "admin_settings_backups",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("categories", postgresql.JSON(), nullable=False),
        sa.Column("settings_data", postgresql.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_settings_backups_id", "admin_settings_backups", ["id"])


def downgrade() -> None:
    op.drop_table("admin_settings_backups")
    op.drop_table("admin_settings_audit_log")
    op.drop_table("admin_settings_store")
