"""Add missing columns to billing_subscriptions table.

Revision ID: add_billing_subs_cols
Revises: add_credit_cols
Create Date: 2025-12-27 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "add_billing_subs_cols"
down_revision: str | None = "add_credit_cols"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def column_exists(table_name: str, column_name: str) -> bool:
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


def upgrade() -> None:
    # Add usage_records column to billing_subscriptions
    if not column_exists("billing_subscriptions", "usage_records"):
        op.add_column(
            "billing_subscriptions",
            sa.Column("usage_records", sa.JSON(), nullable=False, server_default="{}"),
        )

    # Add scheduled_plan_id for future plan changes
    if not column_exists("billing_subscriptions", "scheduled_plan_id"):
        op.add_column(
            "billing_subscriptions",
            sa.Column("scheduled_plan_id", sa.String(50), nullable=True),
        )

    # Add scheduled_plan_change_date for future plan changes
    if not column_exists("billing_subscriptions", "scheduled_plan_change_date"):
        op.add_column(
            "billing_subscriptions",
            sa.Column("scheduled_plan_change_date", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    columns_to_remove = ["usage_records", "scheduled_plan_id", "scheduled_plan_change_date"]
    for col in columns_to_remove:
        if column_exists("billing_subscriptions", col):
            op.drop_column("billing_subscriptions", col)
