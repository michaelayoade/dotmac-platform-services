"""Create billing tables.

Revision ID: create_billing_tables
Revises: create_admin_settings_tables
Create Date: 2025-12-26 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "create_billing_tables"
down_revision: str | None = "create_admin_settings_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Check existing tables to avoid conflicts
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # billing_products
    if "billing_products" not in existing_tables:
        op.create_table(
            "billing_products",
            sa.Column("product_id", sa.String(50), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
            sa.Column("sku", sa.String(100), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("category", sa.String(100), nullable=True),
            sa.Column("product_type", sa.String(50), nullable=False),
            sa.Column("base_price", sa.Numeric(15, 2), nullable=False, server_default="0"),
            sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
            sa.Column("tax_class", sa.String(50), nullable=True),
            sa.Column("usage_type", sa.String(50), nullable=True),
            sa.Column("usage_unit_name", sa.String(50), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.UniqueConstraint("tenant_id", "sku", name="uq_billing_products_tenant_sku"),
        )

    # billing_product_categories
    if "billing_product_categories" not in existing_tables:
        op.create_table(
            "billing_product_categories",
            sa.Column("category_id", sa.String(50), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("default_tax_class", sa.String(50), nullable=True),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # billing_settings
    if "billing_settings" not in existing_tables:
        op.create_table(
            "billing_settings",
            sa.Column("settings_id", sa.String(50), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, unique=True),
            sa.Column("company_info", postgresql.JSON(), nullable=True),
            sa.Column("tax_settings", postgresql.JSON(), nullable=True),
            sa.Column("payment_settings", postgresql.JSON(), nullable=True),
            sa.Column("invoice_settings", postgresql.JSON(), nullable=True),
            sa.Column("notification_settings", postgresql.JSON(), nullable=True),
            sa.Column("features_enabled", postgresql.JSON(), nullable=True),
            sa.Column("custom_settings", postgresql.JSON(), nullable=True),
            sa.Column("api_settings", postgresql.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # billing_subscription_plans
    if "billing_subscription_plans" not in existing_tables:
        op.create_table(
            "billing_subscription_plans",
            sa.Column("plan_id", sa.String(50), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
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
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # billing_subscriptions
    if "billing_subscriptions" not in existing_tables:
        op.create_table(
            "billing_subscriptions",
            sa.Column("subscription_id", sa.String(50), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
            sa.Column("customer_id", sa.String(50), nullable=False, index=True),
            sa.Column("plan_id", sa.String(50), nullable=False),
            sa.Column("status", sa.String(50), nullable=False, server_default="active"),
            sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("custom_price", sa.Numeric(15, 2), nullable=True),
            sa.Column("usage_records", postgresql.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # billing_addons
    if "billing_addons" not in existing_tables:
        op.create_table(
            "billing_addons",
            sa.Column("addon_id", sa.String(50), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("addon_type", sa.String(50), nullable=False),
            sa.Column("billing_type", sa.String(50), nullable=False),
            sa.Column("price", sa.Numeric(15, 2), nullable=False),
            sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
            sa.Column("setup_fee", sa.Numeric(15, 2), nullable=True),
            sa.Column("is_quantity_based", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("min_quantity", sa.Integer(), nullable=True),
            sa.Column("max_quantity", sa.Integer(), nullable=True),
            sa.Column("metered_unit", sa.String(50), nullable=True),
            sa.Column("included_quantity", sa.Integer(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("is_featured", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("compatible_with_all_plans", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("compatible_plan_ids", postgresql.JSON(), nullable=True),
            sa.Column("icon", sa.String(255), nullable=True),
            sa.Column("features", postgresql.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # billing_tenant_addons
    if "billing_tenant_addons" not in existing_tables:
        op.create_table(
            "billing_tenant_addons",
            sa.Column("tenant_addon_id", sa.String(50), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
            sa.Column("addon_id", sa.String(50), nullable=False),
            sa.Column("subscription_id", sa.String(50), nullable=True),
            sa.Column("status", sa.String(50), nullable=False, server_default="active"),
            sa.Column("quantity", sa.Numeric(10, 2), nullable=False, server_default="1"),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("current_usage", sa.Numeric(15, 2), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # credit_notes
    if "credit_notes" not in existing_tables:
        op.create_table(
            "credit_notes",
            sa.Column("credit_note_id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
            sa.Column("customer_id", sa.String(50), nullable=False, index=True),
            sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("credit_note_number", sa.String(50), nullable=False, unique=True),
            sa.Column("idempotency_key", sa.String(255), nullable=True),
            sa.Column("issue_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("currency", sa.String(3), nullable=False),
            sa.Column("subtotal", sa.Integer(), nullable=False),
            sa.Column("tax_amount", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_amount", sa.Integer(), nullable=False),
            sa.Column("credit_type", sa.String(50), nullable=True),
            sa.Column("reason", sa.String(255), nullable=True),
            sa.Column("reason_description", sa.Text(), nullable=True),
            sa.Column("status", sa.String(50), nullable=False, server_default="DRAFT"),
            sa.Column("auto_apply_to_invoice", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("remaining_credit_amount", sa.Integer(), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("internal_notes", sa.Text(), nullable=True),
            sa.Column("extra_data", postgresql.JSON(), nullable=True),
            sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_credit_notes_tenant_idempotency"),
        )

    # credit_note_line_items
    if "credit_note_line_items" not in existing_tables:
        op.create_table(
            "credit_note_line_items",
            sa.Column("line_item_id", postgresql.UUID(as_uuid=True), primary_key=True),
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
            sa.ForeignKeyConstraint(["credit_note_id"], ["credit_notes.credit_note_id"], ondelete="CASCADE"),
        )

    # usage_records
    if "usage_records" not in existing_tables:
        op.create_table(
            "usage_records",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
            sa.Column("subscription_id", sa.String(50), nullable=True, index=True),
            sa.Column("customer_id", sa.String(50), nullable=True, index=True),
            sa.Column("usage_type", sa.String(100), nullable=False),
            sa.Column("quantity", sa.Numeric(20, 6), nullable=False),
            sa.Column("unit", sa.String(50), nullable=True),
            sa.Column("unit_price", sa.Numeric(12, 6), nullable=True),
            sa.Column("total_amount", sa.Integer(), nullable=True),
            sa.Column("currency", sa.String(3), nullable=True),
            sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("billed_status", sa.String(50), nullable=False, server_default="PENDING"),
            sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("billed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("source_system", sa.String(100), nullable=True),
            sa.Column("source_record_id", sa.String(255), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("device_id", sa.String(100), nullable=True),
            sa.Column("service_location", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # usage_aggregates
    if "usage_aggregates" not in existing_tables:
        op.create_table(
            "usage_aggregates",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
            sa.Column("subscription_id", sa.String(50), nullable=True),
            sa.Column("customer_id", sa.String(50), nullable=True),
            sa.Column("usage_type", sa.String(100), nullable=False),
            sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("period_type", sa.String(20), nullable=False),
            sa.Column("total_quantity", sa.Numeric(20, 6), nullable=False),
            sa.Column("total_amount", sa.Integer(), nullable=True),
            sa.Column("record_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("min_quantity", sa.Numeric(20, 6), nullable=True),
            sa.Column("max_quantity", sa.Numeric(20, 6), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # company_bank_accounts
    if "company_bank_accounts" not in existing_tables:
        op.create_table(
            "company_bank_accounts",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
            sa.Column("account_name", sa.String(255), nullable=False),
            sa.Column("account_nickname", sa.String(100), nullable=True),
            sa.Column("bank_name", sa.String(255), nullable=False),
            sa.Column("bank_address", sa.Text(), nullable=True),
            sa.Column("bank_country", sa.String(2), nullable=True),
            sa.Column("account_number_encrypted", sa.Text(), nullable=True),
            sa.Column("account_number_last_four", sa.String(4), nullable=True),
            sa.Column("routing_number", sa.String(50), nullable=True),
            sa.Column("swift_code", sa.String(20), nullable=True),
            sa.Column("iban", sa.String(50), nullable=True),
            sa.Column("account_type", sa.String(50), nullable=True),
            sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
            sa.Column("status", sa.String(50), nullable=False, server_default="PENDING"),
            sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("accepts_deposits", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("verified_by", sa.String(255), nullable=True),
            sa.Column("verification_notes", sa.Text(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("meta_data", postgresql.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # cash_registers
    if "cash_registers" not in existing_tables:
        op.create_table(
            "cash_registers",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
            sa.Column("register_id", sa.String(50), nullable=False, unique=True),
            sa.Column("register_name", sa.String(255), nullable=False),
            sa.Column("location", sa.String(255), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("current_float", sa.Numeric(10, 2), nullable=False, server_default="0"),
            sa.Column("last_reconciled", sa.DateTime(timezone=True), nullable=True),
            sa.Column("requires_daily_reconciliation", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("max_cash_limit", sa.Numeric(10, 2), nullable=True),
            sa.Column("meta_data", postgresql.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # dunning_campaigns
    if "dunning_campaigns" not in existing_tables:
        op.create_table(
            "dunning_campaigns",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("trigger_after_days", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
            sa.Column("retry_interval_days", sa.Integer(), nullable=False, server_default="3"),
            sa.Column("actions", postgresql.JSON(), nullable=False),
            sa.Column("exclusion_rules", postgresql.JSON(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_executions", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("successful_executions", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_recovered_amount", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # dunning_executions
    if "dunning_executions" not in existing_tables:
        op.create_table(
            "dunning_executions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
            sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("subscription_id", sa.String(50), nullable=True),
            sa.Column("customer_id", sa.String(50), nullable=True),
            sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("status", sa.String(50), nullable=False, server_default="PENDING"),
            sa.Column("current_step", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_steps", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("next_action_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("outstanding_amount", sa.Integer(), nullable=True),
            sa.Column("recovered_amount", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("execution_log", postgresql.JSON(), nullable=True),
            sa.Column("canceled_reason", sa.Text(), nullable=True),
            sa.Column("canceled_by_user_id", sa.String(255), nullable=True),
            sa.Column("metadata_", postgresql.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["campaign_id"], ["dunning_campaigns.id"], ondelete="CASCADE"),
        )

    # billing_exchange_rates
    if "billing_exchange_rates" not in existing_tables:
        op.create_table(
            "billing_exchange_rates",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("base_currency", sa.String(3), nullable=False),
            sa.Column("target_currency", sa.String(3), nullable=False),
            sa.Column("provider", sa.String(100), nullable=True),
            sa.Column("rate", sa.Numeric(18, 9), nullable=False),
            sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("effective_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("metadata_json", postgresql.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index("ix_exchange_rates_currencies", "billing_exchange_rates", ["base_currency", "target_currency"])


def downgrade() -> None:
    tables = [
        "billing_exchange_rates",
        "dunning_executions",
        "dunning_campaigns",
        "cash_registers",
        "company_bank_accounts",
        "usage_aggregates",
        "usage_records",
        "credit_note_line_items",
        "credit_notes",
        "billing_tenant_addons",
        "billing_addons",
        "billing_subscriptions",
        "billing_subscription_plans",
        "billing_settings",
        "billing_product_categories",
        "billing_products",
    ]
    for table in tables:
        op.drop_table(table)
