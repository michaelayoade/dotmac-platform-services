"""Fix licensing table columns.

Revision ID: fix_licensing_columns
Revises: fix_remaining_columns
Create Date: 2025-12-27 03:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "fix_licensing_columns"
down_revision: str | None = "fix_remaining_columns"
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
    """Add is_active columns to licensing tables."""

    tables_needing_is_active = [
        "license_templates",
        "licenses",
        "license_activations",
        "license_orders",
        "licensing_plans",
        "licensing_modules",
        "licensing_tenant_subscriptions",
        "licensing_subscription_items",
        "licensing_usage_records",
        "licensing_invoices",
        "licensing_entitlements",
    ]

    for table in tables_needing_is_active:
        if table_exists(table) and not column_exists(table, "is_active"):
            op.add_column(
                table,
                sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            )


def downgrade() -> None:
    """Remove is_active columns."""
    pass
