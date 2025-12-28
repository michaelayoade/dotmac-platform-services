"""Create licensing tables.

Revision ID: create_licensing_tables
Revises: create_billing_tables
Create Date: 2025-12-26 19:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "create_licensing_tables"
down_revision: str | None = "create_billing_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # licenses
    if "licenses" not in existing_tables:
        op.create_table(
            "licenses",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
            sa.Column("license_key", sa.Text(), nullable=False, unique=True),
            sa.Column("product_id", sa.String(50), nullable=True),
            sa.Column("product_name", sa.String(255), nullable=True),
            sa.Column("product_version", sa.String(50), nullable=True),
            sa.Column("license_type", sa.String(50), nullable=False),
            sa.Column("license_model", sa.String(50), nullable=False),
            sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("reseller_id", sa.String(50), nullable=True),
            sa.Column("issued_to", sa.String(255), nullable=True),
            sa.Column("max_activations", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("current_activations", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("features", postgresql.JSON(), nullable=True),
            sa.Column("restrictions", postgresql.JSON(), nullable=True),
            sa.Column("issued_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("activation_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expiry_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("maintenance_expiry", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE"),
            sa.Column("auto_renewal", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("trial_period_days", sa.Integer(), nullable=True),
            sa.Column("grace_period_days", sa.Integer(), nullable=True),
            sa.Column("metadata", postgresql.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # license_templates
    if "license_templates" not in existing_tables:
        op.create_table(
            "license_templates",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
            sa.Column("template_name", sa.String(255), nullable=False),
            sa.Column("product_id", sa.String(50), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("license_type", sa.String(50), nullable=False),
            sa.Column("license_model", sa.String(50), nullable=False),
            sa.Column("default_duration", sa.Integer(), nullable=True),
            sa.Column("max_activations", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("features", postgresql.JSON(), nullable=True),
            sa.Column("restrictions", postgresql.JSON(), nullable=True),
            sa.Column("pricing", postgresql.JSON(), nullable=True),
            sa.Column("auto_renewal_enabled", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("trial_allowed", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("trial_duration_days", sa.Integer(), nullable=True),
            sa.Column("grace_period_days", sa.Integer(), nullable=True),
            sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # license_activations
    if "license_activations" not in existing_tables:
        op.create_table(
            "license_activations",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
            sa.Column("license_id", sa.String(36), nullable=False, index=True),
            sa.Column("activation_token", sa.Text(), nullable=False, unique=True),
            sa.Column("device_fingerprint", sa.String(255), nullable=True),
            sa.Column("machine_name", sa.String(255), nullable=True),
            sa.Column("hardware_id", sa.String(255), nullable=True),
            sa.Column("mac_address", sa.String(50), nullable=True),
            sa.Column("ip_address", sa.String(50), nullable=True),
            sa.Column("operating_system", sa.String(100), nullable=True),
            sa.Column("user_agent", sa.Text(), nullable=True),
            sa.Column("application_version", sa.String(50), nullable=True),
            sa.Column("activation_type", sa.String(50), nullable=False, server_default="ONLINE"),
            sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE"),
            sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deactivation_reason", sa.Text(), nullable=True),
            sa.Column("location", sa.String(255), nullable=True),
            sa.Column("usage_metrics", postgresql.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["license_id"], ["licenses.id"], ondelete="CASCADE"),
        )

    # license_orders
    if "license_orders" not in existing_tables:
        op.create_table(
            "license_orders",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
            sa.Column("order_number", sa.String(50), nullable=False, unique=True),
            sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("reseller_id", sa.String(50), nullable=True),
            sa.Column("template_id", sa.String(36), nullable=True),
            sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("custom_features", postgresql.JSON(), nullable=True),
            sa.Column("custom_restrictions", postgresql.JSON(), nullable=True),
            sa.Column("duration_override", sa.Integer(), nullable=True),
            sa.Column("pricing_override", postgresql.JSON(), nullable=True),
            sa.Column("special_instructions", sa.Text(), nullable=True),
            sa.Column("status", sa.String(50), nullable=False, server_default="PENDING"),
            sa.Column("total_amount", sa.Numeric(15, 2), nullable=True),
            sa.Column("discount_applied", sa.Numeric(15, 2), nullable=True),
            sa.Column("payment_status", sa.String(50), nullable=False, server_default="PENDING"),
            sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("subscription_id", sa.String(50), nullable=True),
            sa.Column("fulfillment_method", sa.String(50), nullable=False, server_default="AUTO"),
            sa.Column("generated_licenses", postgresql.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("fulfilled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # subscription_plans (licensing v2)
    if "subscription_plans" not in existing_tables:
        op.create_table(
            "subscription_plans",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("plan_name", sa.String(255), nullable=False, unique=True),
            sa.Column("plan_code", sa.String(50), nullable=False, unique=True),
            sa.Column("tier", sa.String(50), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("monthly_price", sa.Numeric(15, 2), nullable=False),
            sa.Column("annual_price", sa.Numeric(15, 2), nullable=True),
            sa.Column("setup_fee", sa.Numeric(15, 2), nullable=True),
            sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
            sa.Column("trial_days", sa.Integer(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("is_public", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("custom_metadata", postgresql.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # plan_features
    if "plan_features" not in existing_tables:
        op.create_table(
            "plan_features",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("feature_code", sa.String(100), nullable=False),
            sa.Column("feature_category", sa.String(50), nullable=True),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("config", postgresql.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["plan_id"], ["subscription_plans.id"], ondelete="CASCADE"),
        )

    # plan_quotas
    if "plan_quotas" not in existing_tables:
        op.create_table(
            "plan_quotas",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("quota_type", sa.String(50), nullable=False),
            sa.Column("quota_limit", sa.Integer(), nullable=False, server_default="-1"),
            sa.Column("soft_limit", sa.Integer(), nullable=True),
            sa.Column("overage_allowed", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("overage_rate", sa.Numeric(15, 4), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["plan_id"], ["subscription_plans.id"], ondelete="CASCADE"),
        )

    # tenant_subscriptions
    if "tenant_subscriptions" not in existing_tables:
        op.create_table(
            "tenant_subscriptions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, unique=True),
            sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE"),
            sa.Column("billing_cycle", sa.String(50), nullable=False, server_default="MONTHLY"),
            sa.Column("trial_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("billing_email", sa.String(255), nullable=True),
            sa.Column("payment_method_id", sa.String(255), nullable=True),
            sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
            sa.Column("paypal_subscription_id", sa.String(255), nullable=True),
            sa.Column("custom_metadata", postgresql.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["plan_id"], ["subscription_plans.id"]),
        )

    # tenant_quota_usage
    if "tenant_quota_usage" not in existing_tables:
        op.create_table(
            "tenant_quota_usage",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("quota_type", sa.String(50), nullable=False),
            sa.Column("current_usage", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("quota_limit", sa.Integer(), nullable=False),
            sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("overage_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("overage_charges", sa.Numeric(15, 2), nullable=False, server_default="0"),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["subscription_id"], ["tenant_subscriptions.id"], ondelete="CASCADE"),
        )

    # licensing_feature_modules (composable framework)
    if "licensing_feature_modules" not in existing_tables:
        op.create_table(
            "licensing_feature_modules",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("module_code", sa.String(100), nullable=False, unique=True),
            sa.Column("module_name", sa.String(255), nullable=False),
            sa.Column("category", sa.String(50), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("dependencies", postgresql.JSON(), nullable=True),
            sa.Column("pricing_model", sa.String(50), nullable=False),
            sa.Column("base_price", sa.Numeric(15, 2), nullable=True),
            sa.Column("price_per_unit", sa.Numeric(15, 2), nullable=True),
            sa.Column("config_schema", postgresql.JSON(), nullable=True),
            sa.Column("default_config", postgresql.JSON(), nullable=True),
            sa.Column("custom_config", postgresql.JSON(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("is_public", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("extra_metadata", postgresql.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # licensing_quota_definitions
    if "licensing_quota_definitions" not in existing_tables:
        op.create_table(
            "licensing_quota_definitions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("quota_code", sa.String(100), nullable=False, unique=True),
            sa.Column("quota_name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("unit_name", sa.String(50), nullable=True),
            sa.Column("unit_plural", sa.String(50), nullable=True),
            sa.Column("pricing_model", sa.String(50), nullable=True),
            sa.Column("overage_rate", sa.Numeric(15, 4), nullable=True),
            sa.Column("is_metered", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("reset_period", sa.String(50), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("extra_metadata", postgresql.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )


def downgrade() -> None:
    tables = [
        "licensing_quota_definitions",
        "licensing_feature_modules",
        "tenant_quota_usage",
        "tenant_subscriptions",
        "plan_quotas",
        "plan_features",
        "subscription_plans",
        "license_orders",
        "license_activations",
        "license_templates",
        "licenses",
    ]
    for table in tables:
        op.drop_table(table)
