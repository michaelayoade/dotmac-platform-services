"""Add missing columns to credit_notes table.

Revision ID: add_credit_cols
Revises: add_usage_cols
Create Date: 2025-12-27 09:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "add_credit_cols"
down_revision: str | None = "add_usage_cols"
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
    # Add missing columns to credit_notes
    columns_to_add = [
        ("idempotency_key", sa.String(100), True, None),
        ("issue_date", sa.DateTime(timezone=True), True, None),
        ("subtotal", sa.Numeric(15, 2), True, None),
        ("tax_amount", sa.Numeric(15, 2), True, None),
        ("total_amount", sa.Numeric(15, 2), True, None),
        ("credit_type", sa.String(50), True, "'refund'"),
        ("reason_description", sa.Text(), True, None),
        ("auto_apply_to_invoice", sa.Boolean(), True, "false"),
        ("remaining_credit_amount", sa.Numeric(15, 2), True, None),
        ("notes", sa.Text(), True, None),
        ("internal_notes", sa.Text(), True, None),
        ("extra_data", sa.JSON(), True, None),
        ("voided_at", sa.DateTime(timezone=True), True, None),
        ("created_by", sa.String(255), True, None),
        ("updated_by", sa.String(255), True, None),
    ]

    for col_name, col_type, nullable, default in columns_to_add:
        if not column_exists("credit_notes", col_name):
            op.add_column(
                "credit_notes",
                sa.Column(col_name, col_type, nullable=nullable, server_default=default),
            )


def downgrade() -> None:
    columns_to_remove = [
        "idempotency_key", "issue_date", "subtotal", "tax_amount", "total_amount",
        "credit_type", "reason_description", "auto_apply_to_invoice",
        "remaining_credit_amount", "notes", "internal_notes", "extra_data",
        "voided_at", "created_by", "updated_by",
    ]
    for col in columns_to_remove:
        if column_exists("credit_notes", col):
            op.drop_column("credit_notes", col)
