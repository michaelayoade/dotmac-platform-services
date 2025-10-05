"""Add webhook subscriptions and deliveries tables

Revision ID: add_webhook_tables
Revises: 2025_09_28_2031-e24194971426_merge_rbac_and_contact_migrations
Create Date: 2025-09-30 15:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "add_webhook_tables"
down_revision: Union[str, None] = "e24194971426"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create webhook_subscriptions table
    op.create_table(
        "webhook_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=False, index=True),
        # Endpoint configuration
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        # Event filtering
        sa.Column("events", sa.JSON(), nullable=False),
        # Security
        sa.Column("secret", sa.String(length=255), nullable=False),
        sa.Column("headers", sa.JSON(), nullable=False, server_default="{}"),
        # Delivery configuration
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("retry_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False, server_default="30"),
        # Statistics
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_triggered_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=False), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=True),
        # Metadata
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
    )

    # Create indexes for webhook_subscriptions
    op.create_index("ix_webhook_subscriptions_tenant_id", "webhook_subscriptions", ["tenant_id"])
    op.create_index("ix_webhook_subscriptions_is_active", "webhook_subscriptions", ["is_active"])

    # Create webhook_deliveries table
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=False, index=True),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        # Event details
        sa.Column("event_type", sa.String(length=255), nullable=False, index=True),
        sa.Column("event_id", sa.String(length=255), nullable=False, index=True),
        sa.Column("event_data", sa.JSON(), nullable=False),
        # Delivery details
        sa.Column("status", sa.String(length=50), nullable=False, index=True),
        sa.Column("response_code", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        # Retry tracking
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("next_retry_at", sa.DateTime(timezone=False), nullable=True),
        # Timing
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=True),
        # Foreign key
        sa.ForeignKeyConstraint(
            ["subscription_id"], ["webhook_subscriptions.id"], ondelete="CASCADE"
        ),
    )

    # Create indexes for webhook_deliveries
    op.create_index("ix_webhook_deliveries_tenant_id", "webhook_deliveries", ["tenant_id"])
    op.create_index(
        "ix_webhook_deliveries_subscription_id", "webhook_deliveries", ["subscription_id"]
    )
    op.create_index("ix_webhook_deliveries_event_type", "webhook_deliveries", ["event_type"])
    op.create_index("ix_webhook_deliveries_event_id", "webhook_deliveries", ["event_id"])
    op.create_index("ix_webhook_deliveries_status", "webhook_deliveries", ["status"])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index("ix_webhook_deliveries_status", table_name="webhook_deliveries")
    op.drop_index("ix_webhook_deliveries_event_id", table_name="webhook_deliveries")
    op.drop_index("ix_webhook_deliveries_event_type", table_name="webhook_deliveries")
    op.drop_index("ix_webhook_deliveries_subscription_id", table_name="webhook_deliveries")
    op.drop_index("ix_webhook_deliveries_tenant_id", table_name="webhook_deliveries")

    op.drop_index("ix_webhook_subscriptions_is_active", table_name="webhook_subscriptions")
    op.drop_index("ix_webhook_subscriptions_tenant_id", table_name="webhook_subscriptions")

    # Drop tables
    op.drop_table("webhook_deliveries")
    op.drop_table("webhook_subscriptions")
