"""Rename metadata to custom_metadata in webhook_subscriptions

Revision ID: 2ca86f545cee
Revises: add_webhook_tables
Create Date: 2025-09-30 04:50:02.412441

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2ca86f545cee"
down_revision = "add_webhook_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Rename metadata column to custom_metadata in webhook_subscriptions table."""
    # Check if column exists before renaming
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='webhook_subscriptions'
                AND column_name='metadata'
            ) THEN
                ALTER TABLE webhook_subscriptions
                RENAME COLUMN metadata TO custom_metadata;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Rename custom_metadata back to metadata."""
    # Check if column exists before renaming
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='webhook_subscriptions'
                AND column_name='custom_metadata'
            ) THEN
                ALTER TABLE webhook_subscriptions
                RENAME COLUMN custom_metadata TO metadata;
            END IF;
        END $$;
    """)
