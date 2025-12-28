"""Add missing columns to usage_records table.

Revision ID: add_usage_cols
Revises: norm_billing_status
Create Date: 2025-12-27 08:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "add_usage_cols"
down_revision: str | None = "norm_billing_status"
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
    # Add missing columns to usage_records if they don't exist
    if not column_exists("usage_records", "customer_id"):
        op.add_column(
            "usage_records",
            sa.Column("customer_id", sa.String(50), nullable=True),
        )

    if not column_exists("usage_records", "usage_type"):
        op.add_column(
            "usage_records",
            sa.Column("usage_type", sa.String(50), nullable=True, server_default="custom"),
        )

    if not column_exists("usage_records", "unit"):
        op.add_column(
            "usage_records",
            sa.Column("unit", sa.String(50), nullable=True),
        )

    if not column_exists("usage_records", "unit_price"):
        op.add_column(
            "usage_records",
            sa.Column("unit_price", sa.Numeric(12, 6), nullable=True),
        )

    if not column_exists("usage_records", "total_amount"):
        op.add_column(
            "usage_records",
            sa.Column("total_amount", sa.Integer(), nullable=True),
        )

    if not column_exists("usage_records", "currency"):
        op.add_column(
            "usage_records",
            sa.Column("currency", sa.String(3), nullable=True),
        )

    if not column_exists("usage_records", "period_start"):
        op.add_column(
            "usage_records",
            sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        )

    if not column_exists("usage_records", "period_end"):
        op.add_column(
            "usage_records",
            sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        )

    if not column_exists("usage_records", "billed_status"):
        op.add_column(
            "usage_records",
            sa.Column("billed_status", sa.String(50), nullable=True, server_default="pending"),
        )

    if not column_exists("usage_records", "invoice_id"):
        op.add_column(
            "usage_records",
            sa.Column("invoice_id", sa.String(50), nullable=True),
        )

    if not column_exists("usage_records", "billed_at"):
        op.add_column(
            "usage_records",
            sa.Column("billed_at", sa.DateTime(timezone=True), nullable=True),
        )

    if not column_exists("usage_records", "source_system"):
        op.add_column(
            "usage_records",
            sa.Column("source_system", sa.String(50), nullable=True),
        )

    if not column_exists("usage_records", "source_record_id"):
        op.add_column(
            "usage_records",
            sa.Column("source_record_id", sa.String(100), nullable=True),
        )

    if not column_exists("usage_records", "description"):
        op.add_column(
            "usage_records",
            sa.Column("description", sa.Text(), nullable=True),
        )

    if not column_exists("usage_records", "device_id"):
        op.add_column(
            "usage_records",
            sa.Column("device_id", sa.String(100), nullable=True),
        )

    if not column_exists("usage_records", "service_location"):
        op.add_column(
            "usage_records",
            sa.Column("service_location", sa.String(500), nullable=True),
        )


def downgrade() -> None:
    # Remove added columns
    columns_to_remove = [
        "customer_id", "usage_type", "unit", "unit_price", "total_amount",
        "currency", "period_start", "period_end", "billed_status", "invoice_id",
        "billed_at", "source_system", "source_record_id", "description",
        "device_id", "service_location",
    ]
    for col in columns_to_remove:
        if column_exists("usage_records", col):
            op.drop_column("usage_records", col)
