"""Fix remaining column mismatches.

Revision ID: fix_remaining_columns
Revises: fix_schema_mismatches
Create Date: 2025-12-27 02:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "fix_remaining_columns"
down_revision: str | None = "fix_schema_mismatches"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = :table AND column_name = :column
            )
            """
        ),
        {"table": table_name, "column": column_name},
    )
    return result.scalar()


def table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = :table
            )
            """
        ),
        {"table": table_name},
    )
    return result.scalar()


def upgrade() -> None:
    """Add remaining missing columns."""

    # dunning_executions - add retry_count and started_at
    if table_exists("dunning_executions"):
        if not column_exists("dunning_executions", "retry_count"):
            op.add_column(
                "dunning_executions",
                sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            )

        if not column_exists("dunning_executions", "started_at"):
            op.add_column(
                "dunning_executions",
                sa.Column(
                    "started_at",
                    sa.DateTime(timezone=True),
                    nullable=False,
                    server_default=sa.text("now()"),
                ),
            )

    # push_subscriptions - add missing columns
    if table_exists("push_subscriptions"):
        if not column_exists("push_subscriptions", "is_active"):
            op.add_column(
                "push_subscriptions",
                sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            )

    # billing_settings - check and add columns
    if table_exists("billing_settings"):
        if not column_exists("billing_settings", "is_active"):
            op.add_column(
                "billing_settings",
                sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            )

    # billing_usage_records - add missing columns
    if table_exists("billing_usage_records"):
        if not column_exists("billing_usage_records", "is_active"):
            op.add_column(
                "billing_usage_records",
                sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            )

    # notification_preferences - ensure is_active exists
    if table_exists("notification_preferences"):
        if not column_exists("notification_preferences", "is_active"):
            op.add_column(
                "notification_preferences",
                sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            )

    # notification_stats - add is_active if missing
    if table_exists("notification_stats"):
        if not column_exists("notification_stats", "is_active"):
            op.add_column(
                "notification_stats",
                sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            )

    # company_bank_accounts - add updated_by if missing
    if table_exists("company_bank_accounts"):
        if not column_exists("company_bank_accounts", "updated_by"):
            op.add_column(
                "company_bank_accounts",
                sa.Column("updated_by", sa.String(255), nullable=True),
            )

    # Fix subscription_id default value in dunning_executions (remove the malformed default)
    if table_exists("dunning_executions"):
        op.execute(
            """
            ALTER TABLE dunning_executions
            ALTER COLUMN subscription_id SET DEFAULT ''
            """
        )


def downgrade() -> None:
    """Remove added columns."""
    pass
