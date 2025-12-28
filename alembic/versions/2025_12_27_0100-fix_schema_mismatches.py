"""Fix schema mismatches - add missing columns.

Revision ID: fix_schema_mismatches
Revises: correct_missing_tables
Create Date: 2025-12-27 01:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "fix_schema_mismatches"
down_revision: str | None = "correct_missing_tables"
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
    """Add missing columns to fix schema mismatches."""

    # 1. notifications.is_active - Boolean, default True
    if table_exists("notifications") and not column_exists("notifications", "is_active"):
        op.add_column(
            "notifications",
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        )

    # 2. dunning_campaigns - fix column names and add missing columns
    if table_exists("dunning_campaigns"):
        # Rename trigger_days_overdue to trigger_after_days if it exists
        if column_exists("dunning_campaigns", "trigger_days_overdue") and not column_exists(
            "dunning_campaigns", "trigger_after_days"
        ):
            op.alter_column(
                "dunning_campaigns",
                "trigger_days_overdue",
                new_column_name="trigger_after_days",
            )
        elif not column_exists("dunning_campaigns", "trigger_after_days"):
            op.add_column(
                "dunning_campaigns",
                sa.Column("trigger_after_days", sa.Integer(), nullable=False, server_default="1"),
            )

        # Rename max_attempts to max_retries if it exists
        if column_exists("dunning_campaigns", "max_attempts") and not column_exists(
            "dunning_campaigns", "max_retries"
        ):
            op.alter_column(
                "dunning_campaigns",
                "max_attempts",
                new_column_name="max_retries",
            )
        elif not column_exists("dunning_campaigns", "max_retries"):
            op.add_column(
                "dunning_campaigns",
                sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
            )

        # Add actions JSON column
        if not column_exists("dunning_campaigns", "actions"):
            op.add_column(
                "dunning_campaigns",
                sa.Column("actions", postgresql.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
            )

        # Add exclusion_rules JSON column
        if not column_exists("dunning_campaigns", "exclusion_rules"):
            op.add_column(
                "dunning_campaigns",
                sa.Column("exclusion_rules", postgresql.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
            )

        # Add priority column
        if not column_exists("dunning_campaigns", "priority"):
            op.add_column(
                "dunning_campaigns",
                sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
            )

        # Add total_executions column
        if not column_exists("dunning_campaigns", "total_executions"):
            op.add_column(
                "dunning_campaigns",
                sa.Column("total_executions", sa.Integer(), nullable=False, server_default="0"),
            )

        # Add successful_executions column
        if not column_exists("dunning_campaigns", "successful_executions"):
            op.add_column(
                "dunning_campaigns",
                sa.Column("successful_executions", sa.Integer(), nullable=False, server_default="0"),
            )

        # Add total_recovered_amount column
        if not column_exists("dunning_campaigns", "total_recovered_amount"):
            op.add_column(
                "dunning_campaigns",
                sa.Column("total_recovered_amount", sa.Integer(), nullable=False, server_default="0"),
            )

        # Add created_by column (from AuditMixin)
        if not column_exists("dunning_campaigns", "created_by"):
            op.add_column(
                "dunning_campaigns",
                sa.Column("created_by", sa.String(255), nullable=True),
            )

        # Add updated_by column (from AuditMixin)
        if not column_exists("dunning_campaigns", "updated_by"):
            op.add_column(
                "dunning_campaigns",
                sa.Column("updated_by", sa.String(255), nullable=True),
            )

    # 3. dunning_executions - add subscription_id and other missing columns
    if table_exists("dunning_executions"):
        if not column_exists("dunning_executions", "subscription_id"):
            op.add_column(
                "dunning_executions",
                sa.Column("subscription_id", sa.String(50), nullable=False, server_default="''"),
            )
            op.create_index(
                "ix_dunning_executions_subscription_id",
                "dunning_executions",
                ["subscription_id"],
            )

        if not column_exists("dunning_executions", "customer_id"):
            op.add_column(
                "dunning_executions",
                sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
            )

        if not column_exists("dunning_executions", "invoice_id"):
            op.add_column(
                "dunning_executions",
                sa.Column("invoice_id", sa.String(50), nullable=True),
            )

        if not column_exists("dunning_executions", "total_steps"):
            op.add_column(
                "dunning_executions",
                sa.Column("total_steps", sa.Integer(), nullable=False, server_default="1"),
            )

        if not column_exists("dunning_executions", "outstanding_amount"):
            op.add_column(
                "dunning_executions",
                sa.Column("outstanding_amount", sa.Integer(), nullable=False, server_default="0"),
            )

        if not column_exists("dunning_executions", "recovered_amount"):
            op.add_column(
                "dunning_executions",
                sa.Column("recovered_amount", sa.Integer(), nullable=False, server_default="0"),
            )

        if not column_exists("dunning_executions", "execution_log"):
            op.add_column(
                "dunning_executions",
                sa.Column("execution_log", postgresql.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
            )

        if not column_exists("dunning_executions", "canceled_reason"):
            op.add_column(
                "dunning_executions",
                sa.Column("canceled_reason", sa.Text(), nullable=True),
            )

        if not column_exists("dunning_executions", "canceled_by_user_id"):
            op.add_column(
                "dunning_executions",
                sa.Column("canceled_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
            )

        # Add AuditMixin columns
        if not column_exists("dunning_executions", "created_by"):
            op.add_column(
                "dunning_executions",
                sa.Column("created_by", sa.String(255), nullable=True),
            )

        if not column_exists("dunning_executions", "updated_by"):
            op.add_column(
                "dunning_executions",
                sa.Column("updated_by", sa.String(255), nullable=True),
            )

    # 4. rate_limit_rules - add created_by_id and updated_by_id
    if table_exists("rate_limit_rules"):
        if not column_exists("rate_limit_rules", "created_by_id"):
            op.add_column(
                "rate_limit_rules",
                sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
            )

        if not column_exists("rate_limit_rules", "updated_by_id"):
            op.add_column(
                "rate_limit_rules",
                sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
            )

    # 5. rate_limit_logs - add updated_at
    if table_exists("rate_limit_logs") and not column_exists("rate_limit_logs", "updated_at"):
        op.add_column(
            "rate_limit_logs",
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )

    # 6. billing_subscriptions - add custom_price
    if table_exists("billing_subscriptions") and not column_exists(
        "billing_subscriptions", "custom_price"
    ):
        op.add_column(
            "billing_subscriptions",
            sa.Column("custom_price", sa.Numeric(10, 2), nullable=True),
        )

    # 7. licenses - add deleted_at
    if table_exists("licenses") and not column_exists("licenses", "deleted_at"):
        op.add_column(
            "licenses",
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )

    # 8. license_templates - add deleted_at
    if table_exists("license_templates") and not column_exists("license_templates", "deleted_at"):
        op.add_column(
            "license_templates",
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )

    # 9. license_orders - add deleted_at
    if table_exists("license_orders") and not column_exists("license_orders", "deleted_at"):
        op.add_column(
            "license_orders",
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )

    # 10. license_activations - add deleted_at
    if table_exists("license_activations") and not column_exists(
        "license_activations", "deleted_at"
    ):
        op.add_column(
            "license_activations",
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )

    # 11. credit_notes - add credit_note_number
    if table_exists("credit_notes") and not column_exists("credit_notes", "credit_note_number"):
        op.add_column(
            "credit_notes",
            sa.Column("credit_note_number", sa.String(50), nullable=True),
        )

    # 12. contact_field_definitions - add display_order
    if table_exists("contact_field_definitions") and not column_exists(
        "contact_field_definitions", "display_order"
    ):
        op.add_column(
            "contact_field_definitions",
            sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        )

    # 13. jobs - add description
    if table_exists("jobs") and not column_exists("jobs", "description"):
        op.add_column(
            "jobs",
            sa.Column("description", sa.Text(), nullable=True),
        )

    # 14. company_bank_accounts - add created_by
    if table_exists("company_bank_accounts") and not column_exists(
        "company_bank_accounts", "created_by"
    ):
        op.add_column(
            "company_bank_accounts",
            sa.Column("created_by", sa.String(255), nullable=True),
        )

    # Additional fixes for notification_templates - add is_active
    if table_exists("notification_templates") and not column_exists(
        "notification_templates", "is_active"
    ):
        op.add_column(
            "notification_templates",
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        )


def downgrade() -> None:
    """Remove added columns."""
    # The downgrade is intentionally left empty as removing columns
    # could cause data loss. If needed, implement specific column drops.
    pass
