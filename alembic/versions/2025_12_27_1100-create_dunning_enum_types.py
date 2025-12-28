"""Create dunning enum types in PostgreSQL.

Revision ID: create_dunning_enums
Revises: add_billing_subs_cols
Create Date: 2025-12-27 11:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "create_dunning_enums"
down_revision: str | None = "add_billing_subs_cols"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def enum_exists(enum_name: str) -> bool:
    """Check if PostgreSQL enum type exists."""
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            """
            SELECT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = :enum_name
            )
            """
        ),
        {"enum_name": enum_name},
    )
    return result.scalar()


def upgrade() -> None:
    # Create dunningexecutionstatus enum if it doesn't exist
    if not enum_exists("dunningexecutionstatus"):
        op.execute("""
            CREATE TYPE dunningexecutionstatus AS ENUM (
                'pending', 'in_progress', 'completed', 'failed', 'canceled'
            )
        """)

    # Create dunningactiontype enum if it doesn't exist
    if not enum_exists("dunningactiontype"):
        op.execute("""
            CREATE TYPE dunningactiontype AS ENUM (
                'email_reminder', 'sms_reminder', 'payment_retry',
                'late_fee', 'service_suspension', 'service_termination',
                'send_to_collections', 'custom'
            )
        """)

    # Create dunningrulestatus enum if it doesn't exist
    if not enum_exists("dunningrulestatus"):
        op.execute("""
            CREATE TYPE dunningrulestatus AS ENUM (
                'active', 'inactive', 'draft'
            )
        """)

    # Alter dunning_executions.status column from varchar to enum
    # Drop default first, change type, then set default
    op.execute("""
        ALTER TABLE dunning_executions ALTER COLUMN status DROP DEFAULT;
        ALTER TABLE dunning_executions ALTER COLUMN status TYPE dunningexecutionstatus USING status::dunningexecutionstatus;
        ALTER TABLE dunning_executions ALTER COLUMN status SET DEFAULT 'pending';
    """)


def downgrade() -> None:
    # Revert dunning_executions.status column back to varchar
    op.execute("""
        ALTER TABLE dunning_executions ALTER COLUMN status DROP DEFAULT;
        ALTER TABLE dunning_executions ALTER COLUMN status TYPE character varying(50) USING status::text;
        ALTER TABLE dunning_executions ALTER COLUMN status SET DEFAULT 'pending';
    """)

    # Drop the enum types if they exist
    if enum_exists("dunningexecutionstatus"):
        op.execute("DROP TYPE dunningexecutionstatus")
    if enum_exists("dunningactiontype"):
        op.execute("DROP TYPE dunningactiontype")
    if enum_exists("dunningrulestatus"):
        op.execute("DROP TYPE dunningrulestatus")
