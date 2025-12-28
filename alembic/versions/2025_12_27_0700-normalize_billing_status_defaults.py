"""Normalize billing status defaults to lowercase.

Revision ID: normalize_billing_status_defaults
Revises: drop_legacy_lic
Create Date: 2025-12-27 07:00:00.000000
"""

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op

revision: str = "norm_billing_status"
down_revision: str | None = "drop_legacy_lic"
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


def table_exists(table_name: str) -> bool:
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


def _normalize_status_defaults(
    table_name: str, column_name: str, default_value: str, existing_type: Any
) -> None:
    if not table_exists(table_name):
        return
    if not column_exists(table_name, column_name):
        return

    op.execute(
        sa.text(
            f"""
            UPDATE {table_name}
            SET {column_name} = LOWER({column_name})
            WHERE {column_name} IS NOT NULL
            """
        )
    )
    op.alter_column(
        table_name,
        column_name,
        existing_type=existing_type,
        server_default=default_value,
    )


def upgrade() -> None:
    _normalize_status_defaults(
        "dunning_executions", "status", "pending", sa.String(length=50)
    )
    _normalize_status_defaults("credit_notes", "status", "draft", sa.String(length=50))
    _normalize_status_defaults("usage_records", "billed_status", "pending", sa.String(length=50))
    _normalize_status_defaults(
        "company_bank_accounts", "status", "pending", sa.String(length=50)
    )


def downgrade() -> None:
    # Non-destructive normalization; no downgrade needed.
    pass
