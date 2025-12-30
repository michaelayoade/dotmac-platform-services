"""Create licensing enum types in PostgreSQL.

Revision ID: create_licensing_enums
Revises: create_dunning_enums
Create Date: 2025-12-27 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "create_licensing_enums"
down_revision: str | None = "create_dunning_enums"
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
    # Create subscriptionstatus enum for licensing if it doesn't exist
    if not enum_exists("subscriptionstatus"):
        op.execute("""
            CREATE TYPE subscriptionstatus AS ENUM (
                'trial', 'active', 'past_due', 'suspended', 'cancelled', 'expired'
            )
        """)

    # Alter licensing_tenant_subscriptions.status column from varchar to enum
    op.execute("""
        ALTER TABLE licensing_tenant_subscriptions ALTER COLUMN status DROP DEFAULT;
        ALTER TABLE licensing_tenant_subscriptions ALTER COLUMN status TYPE subscriptionstatus USING status::subscriptionstatus;
        ALTER TABLE licensing_tenant_subscriptions ALTER COLUMN status SET DEFAULT 'active';
    """)


def downgrade() -> None:
    # Revert licensing_tenant_subscriptions.status column back to varchar
    op.execute("""
        ALTER TABLE licensing_tenant_subscriptions ALTER COLUMN status DROP DEFAULT;
        ALTER TABLE licensing_tenant_subscriptions ALTER COLUMN status TYPE character varying(50) USING status::text;
        ALTER TABLE licensing_tenant_subscriptions ALTER COLUMN status SET DEFAULT 'active';
    """)

    # Drop the enum types if they exist
    if enum_exists("subscriptionstatus"):
        op.execute("DROP TYPE subscriptionstatus")
