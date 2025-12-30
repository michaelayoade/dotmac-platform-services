"""Fix billing and licensing tables to match BaseModel structure.

Revision ID: fix_billing_licensing_tables
Revises: create_notifications_tables
Create Date: 2025-12-26 21:00:00.000000

The previous migrations created tables with product_id/plan_id as primary keys,
but the SQLAlchemy models inherit from BaseModel which uses 'id' (UUID) as
the primary key. This migration fixes the table structures.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "fix_billing_licensing_tables"
down_revision: str | None = "create_notifications_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # Tables to fix - they need 'id' as primary key and other BaseModel columns
    tables_to_fix = [
        "credit_note_line_items",  # must be dropped first (depends on credit_notes)
        "billing_products",
        "billing_product_categories",
        "billing_settings",
        "billing_subscription_plans",
        "billing_subscriptions",
        "credit_notes",
        "usage_records",
        "usage_aggregates",
        "billing_bank_accounts",
        "billing_cash_registers",
        "dunning_campaigns",
        "dunning_rules",
        "dunning_executions",
        "dunning_actions",
        "dunning_stats",
        "billing_addons",
    ]

    # Drop all tables first (CASCADE to handle FK deps)
    for table in tables_to_fix:
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')

    # Recreate billing_products with correct structure
    op.create_table(
        "billing_products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("product_id", sa.String(50), nullable=False, unique=True),
        sa.Column("sku", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("product_type", sa.String(20), nullable=False),
        sa.Column("base_price", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("tax_class", sa.String(20), nullable=False, server_default="standard"),
        sa.Column("usage_type", sa.String(50), nullable=True),
        sa.Column("usage_unit_name", sa.String(50), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_billing_products_tenant_sku", "billing_products", ["tenant_id", "sku"], unique=True)
    op.create_index("ix_billing_products_tenant_category", "billing_products", ["tenant_id", "category"])
    op.create_index("ix_billing_products_tenant_type", "billing_products", ["tenant_id", "product_type"])
    op.create_index("ix_billing_products_tenant_active", "billing_products", ["tenant_id", "is_active"])

    # Recreate billing_product_categories
    op.create_table(
        "billing_product_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("category_id", sa.String(50), primary_key=False, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("default_tax_class", sa.String(20), nullable=False, server_default="standard"),
        sa.Column("sort_order", sa.Numeric(10, 0), nullable=False, server_default="0"),
        sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_billing_categories_tenant_name", "billing_product_categories", ["tenant_id", "name"], unique=True)
    op.create_index("ix_billing_categories_sort", "billing_product_categories", ["tenant_id", "sort_order"])

    # Recreate billing_settings
    op.create_table(
        "billing_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(255), nullable=True, index=True, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("settings_id", sa.String(50), nullable=False),
        sa.Column("company_info", postgresql.JSON(), nullable=True),
        sa.Column("tax_settings", postgresql.JSON(), nullable=True),
        sa.Column("payment_settings", postgresql.JSON(), nullable=True),
        sa.Column("invoice_settings", postgresql.JSON(), nullable=True),
        sa.Column("notification_settings", postgresql.JSON(), nullable=True),
        sa.Column("features_enabled", postgresql.JSON(), nullable=True),
        sa.Column("custom_settings", postgresql.JSON(), nullable=True),
        sa.Column("api_settings", postgresql.JSON(), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
    )

    # Recreate billing_subscription_plans
    op.create_table(
        "billing_subscription_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("plan_id", sa.String(50), nullable=False, unique=True),
        sa.Column("product_id", sa.String(50), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("billing_cycle", sa.String(50), nullable=False),
        sa.Column("price", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("setup_fee", sa.Numeric(15, 2), nullable=True),
        sa.Column("trial_days", sa.Integer(), nullable=True),
        sa.Column("included_usage", postgresql.JSON(), nullable=True),
        sa.Column("overage_rates", postgresql.JSON(), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
    )

    # Recreate billing_subscriptions
    op.create_table(
        "billing_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("subscription_id", sa.String(50), nullable=False, unique=True),
        sa.Column("customer_id", sa.String(50), nullable=False, index=True),
        sa.Column("plan_id", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("billing_cycle_anchor", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
    )

    # Recreate credit_notes
    op.create_table(
        "credit_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("credit_note_id", sa.String(50), nullable=False, unique=True),
        sa.Column("invoice_id", sa.String(50), nullable=True),
        sa.Column("customer_id", sa.String(50), nullable=False, index=True),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="issued"),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
    )

    # Recreate usage_records
    op.create_table(
        "usage_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("record_id", sa.String(50), nullable=False, unique=True),
        sa.Column("subscription_id", sa.String(50), nullable=False, index=True),
        sa.Column("product_id", sa.String(50), nullable=False),
        sa.Column("quantity", sa.Numeric(15, 4), nullable=False),
        sa.Column("unit_name", sa.String(50), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
    )

    # Recreate usage_aggregates
    op.create_table(
        "usage_aggregates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("aggregate_id", sa.String(50), nullable=False, unique=True),
        sa.Column("subscription_id", sa.String(50), nullable=False, index=True),
        sa.Column("product_id", sa.String(50), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_quantity", sa.Numeric(15, 4), nullable=False),
        sa.Column("billable_quantity", sa.Numeric(15, 4), nullable=False),
        sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
    )

    # Recreate billing_bank_accounts
    op.create_table(
        "billing_bank_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("account_id", sa.String(50), nullable=False, unique=True),
        sa.Column("account_name", sa.String(255), nullable=False),
        sa.Column("bank_name", sa.String(255), nullable=True),
        sa.Column("account_number_last4", sa.String(4), nullable=True),
        sa.Column("routing_number", sa.String(50), nullable=True),
        sa.Column("iban", sa.String(50), nullable=True),
        sa.Column("swift_code", sa.String(20), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
    )

    # Recreate billing_cash_registers
    op.create_table(
        "billing_cash_registers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("register_id", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
    )

    # Recreate dunning_campaigns
    op.create_table(
        "dunning_campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("campaign_id", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("trigger_days_overdue", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("retry_interval_days", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("escalation_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
    )

    # Recreate dunning_rules
    op.create_table(
        "dunning_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("rule_id", sa.String(50), nullable=False, unique=True),
        sa.Column("campaign_id", sa.String(50), nullable=False, index=True),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("days_after_due", sa.Integer(), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("template_id", sa.String(50), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
    )

    # Recreate dunning_executions
    op.create_table(
        "dunning_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("execution_id", sa.String(50), nullable=False, unique=True),
        sa.Column("invoice_id", sa.String(50), nullable=False, index=True),
        sa.Column("campaign_id", sa.String(50), nullable=False),
        sa.Column("current_step", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("next_action_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
    )

    # Recreate dunning_actions
    op.create_table(
        "dunning_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("action_id", sa.String(50), nullable=False, unique=True),
        sa.Column("execution_id", sa.String(50), nullable=False, index=True),
        sa.Column("rule_id", sa.String(50), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result", postgresql.JSON(), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
    )

    # Recreate dunning_stats
    op.create_table(
        "dunning_stats",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("stat_id", sa.String(50), nullable=False, unique=True),
        sa.Column("campaign_id", sa.String(50), nullable=False, index=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("invoices_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payments_recovered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("amount_recovered", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
    )

    # Recreate billing_addons
    op.create_table(
        "billing_addons",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("addon_id", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("billing_type", sa.String(50), nullable=False, server_default="one_time"),
        sa.Column("applicable_plans", postgresql.JSON(), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
    )

    # Recreate credit_note_line_items (depends on credit_notes.id)
    op.create_table(
        "credit_note_line_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("credit_note_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Numeric(10, 2), nullable=False),
        sa.Column("unit_price", sa.Integer(), nullable=False),
        sa.Column("total_price", sa.Integer(), nullable=False),
        sa.Column("original_invoice_line_item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_id", sa.String(50), nullable=True),
        sa.Column("tax_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("tax_amount", sa.Integer(), nullable=True),
        sa.Column("extra_data", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["credit_note_id"], ["credit_notes.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    # Drop all recreated tables (they'll be recreated by previous migrations on downgrade)
    tables = [
        "credit_note_line_items",
        "billing_addons",
        "dunning_stats",
        "dunning_actions",
        "dunning_executions",
        "dunning_rules",
        "dunning_campaigns",
        "billing_cash_registers",
        "billing_bank_accounts",
        "usage_aggregates",
        "usage_records",
        "credit_notes",
        "billing_subscriptions",
        "billing_subscription_plans",
        "billing_settings",
        "billing_product_categories",
        "billing_products",
    ]
    for table in tables:
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
