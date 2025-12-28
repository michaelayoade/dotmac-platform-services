"""Correct missing tables to match SQLAlchemy models.

Revision ID: correct_missing_tables
Revises: create_missing_tables
Create Date: 2025-12-27 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "correct_missing_tables"
down_revision: str | None = "create_missing_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _ensure_enum(bind: sa.engine.Connection, enum: postgresql.ENUM) -> None:
    result = bind.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = :name"), {"name": enum.name})
    if not result.fetchone():
        enum.create(bind, checkfirst=True)


def _get_columns(bind: sa.engine.Connection, table: str) -> dict[str, sa.engine.RowMapping]:
    inspector = sa.inspect(bind)
    return {col["name"]: col for col in inspector.get_columns(table)}


def _has_index(bind: sa.engine.Connection, table: str, name: str) -> bool:
    inspector = sa.inspect(bind)
    return any(index["name"] == name for index in inspector.get_indexes(table))


def _has_unique(bind: sa.engine.Connection, table: str, name: str) -> bool:
    inspector = sa.inspect(bind)
    return any(constraint["name"] == name for constraint in inspector.get_unique_constraints(table))


def _table_exists(bind: sa.engine.Connection, table: str) -> bool:
    inspector = sa.inspect(bind)
    return table in inspector.get_table_names()


def _is_uuid_type(column_type: sa.types.TypeEngine) -> bool:
    uuid_type = getattr(sa, "Uuid", None)
    return isinstance(column_type, postgresql.UUID) or (uuid_type is not None and isinstance(column_type, uuid_type))


def _is_integer_type(column_type: sa.types.TypeEngine) -> bool:
    return isinstance(column_type, sa.Integer)


def _find_fk_name(
    bind: sa.engine.Connection, table: str, referred_table: str, constrained_columns: list[str]
) -> str | None:
    inspector = sa.inspect(bind)
    for fk in inspector.get_foreign_keys(table):
        if fk.get("referred_table") == referred_table and fk.get("constrained_columns") == constrained_columns:
            return fk.get("name")
    return None


def _index_exists_global(bind: sa.engine.Connection, index_name: str) -> bool:
    result = bind.execute(
        sa.text(
            "SELECT 1 FROM pg_indexes WHERE schemaname = current_schema() AND indexname = :name"
        ),
        {"name": index_name},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    bind = op.get_bind()

    invoice_status_enum = postgresql.ENUM(
        "draft",
        "open",
        "paid",
        "void",
        "overdue",
        "partially_paid",
        name="invoicestatus",
        create_type=False,
    )
    payment_status_enum = postgresql.ENUM(
        "pending",
        "processing",
        "succeeded",
        "failed",
        "refunded",
        "partially_refunded",
        "cancelled",
        name="paymentstatus",
        create_type=False,
    )
    payment_method_type_enum = postgresql.ENUM(
        "card",
        "bank_account",
        "digital_wallet",
        "crypto",
        "check",
        "wire_transfer",
        "cash",
        name="paymentmethodtype",
        create_type=False,
    )
    payment_method_status_enum = postgresql.ENUM(
        "active",
        "inactive",
        "expired",
        "requires_verification",
        "verification_failed",
        name="paymentmethodstatus",
        create_type=False,
    )
    transaction_type_enum = postgresql.ENUM(
        "charge",
        "payment",
        "refund",
        "credit",
        "adjustment",
        "fee",
        "write_off",
        "tax",
        name="transactiontype",
        create_type=False,
    )
    bank_account_type_enum = postgresql.ENUM(
        "checking",
        "savings",
        "business_checking",
        name="bankaccounttype",
        create_type=False,
    )

    ratelimit_scope_enum = postgresql.ENUM(
        "global",
        "per_user",
        "per_ip",
        "per_api_key",
        "per_tenant",
        "per_endpoint",
        name="ratelimitscope",
        create_type=False,
    )
    ratelimit_window_enum = postgresql.ENUM(
        "second",
        "minute",
        "hour",
        "day",
        name="ratelimitwindow",
        create_type=False,
    )
    ratelimit_action_enum = postgresql.ENUM(
        "block",
        "throttle",
        "log_only",
        "captcha",
        name="ratelimitaction",
        create_type=False,
    )

    communication_type_enum = postgresql.ENUM(
        "email",
        "webhook",
        "sms",
        "push",
        name="communicationtype",
        create_type=False,
    )
    communication_status_enum = postgresql.ENUM(
        "pending",
        "queued",
        "sent",
        "delivered",
        "failed",
        "bounced",
        "cancelled",
        name="communicationstatus",
        create_type=False,
    )

    workflow_status_enum = postgresql.ENUM(
        "pending",
        "running",
        "completed",
        "failed",
        "cancelled",
        name="workflowstatus",
        create_type=False,
    )
    workflow_step_status_enum = postgresql.ENUM(
        "pending",
        "running",
        "completed",
        "failed",
        "skipped",
        name="workflowstepstatus",
        create_type=False,
    )

    deployment_state_enum = postgresql.ENUM(
        "pending",
        "provisioning",
        "active",
        "degraded",
        "suspended",
        "failed",
        "destroying",
        "destroyed",
        "upgrading",
        "rolling_back",
        name="deploymentstate",
        create_type=False,
    )

    agent_status_enum = postgresql.ENUM(
        "available",
        "busy",
        "offline",
        "away",
        name="agentstatus",
        create_type=False,
    )

    subscription_status_enum = postgresql.ENUM(
        "trial",
        "active",
        "past_due",
        "suspended",
        "cancelled",
        "expired",
        name="subscriptionstatus",
        create_type=False,
    )
    billing_cycle_enum = postgresql.ENUM(
        "monthly",
        "quarterly",
        "annually",
        "biennial",
        "triennial",
        name="billingcycle",
        create_type=False,
    )

    import_job_type_enum = postgresql.ENUM(
        "invoices",
        "subscriptions",
        "payments",
        "products",
        "mixed",
        name="importjobtype",
        create_type=False,
    )
    import_job_status_enum = postgresql.ENUM(
        "pending",
        "validating",
        "in_progress",
        "completed",
        "failed",
        "partially_completed",
        "cancelled",
        name="importjobstatus",
        create_type=False,
    )

    dunning_action_type_enum = postgresql.ENUM(
        "email",
        "sms",
        "suspend_service",
        "terminate_service",
        "webhook",
        "custom",
        name="dunningactiontype",
        create_type=False,
    )
    dunning_execution_status_enum = postgresql.ENUM(
        "pending",
        "in_progress",
        "completed",
        "failed",
        "canceled",
        name="dunningexecutionstatus",
        create_type=False,
    )

    pricing_model_enum = postgresql.ENUM(
        "FLAT_FEE",
        "PER_UNIT",
        "TIERED",
        "USAGE_BASED",
        "BUNDLED",
        "FREE",
        name="pricingmodel",
        create_type=False,
    )

    _ensure_enum(bind, pricing_model_enum)

    # =====================================================================
    # Billing credit note type fixes
    # =====================================================================

    credit_notes_needs_uuid = False
    credit_notes_fk_name: str | None = None
    if _table_exists(bind, "credit_notes"):
        columns = _get_columns(bind, "credit_notes")
        credit_notes_needs_uuid = (
            "credit_note_id" in columns and not _is_uuid_type(columns["credit_note_id"]["type"])
        )

    if credit_notes_needs_uuid and _table_exists(bind, "credit_note_line_items"):
        credit_notes_fk_name = _find_fk_name(
            bind,
            "credit_note_line_items",
            "credit_notes",
            ["credit_note_id"],
        )
        if credit_notes_fk_name:
            op.drop_constraint(credit_notes_fk_name, "credit_note_line_items", type_="foreignkey")

    if credit_notes_needs_uuid:
        op.alter_column(
            "credit_notes",
            "credit_note_id",
            type_=postgresql.UUID(as_uuid=True),
            postgresql_using="credit_note_id::uuid",
        )

    if _table_exists(bind, "credit_note_line_items"):
        columns = _get_columns(bind, "credit_note_line_items")
        if "credit_note_id" in columns and not _is_uuid_type(columns["credit_note_id"]["type"]):
            op.alter_column(
                "credit_note_line_items",
                "credit_note_id",
                type_=postgresql.UUID(as_uuid=True),
                postgresql_using="credit_note_id::uuid",
            )

    if credit_notes_fk_name:
        op.create_foreign_key(
            credit_notes_fk_name,
            "credit_note_line_items",
            "credit_notes",
            ["credit_note_id"],
            ["credit_note_id"],
            ondelete="CASCADE",
        )

    enums = [
        invoice_status_enum,
        payment_status_enum,
        payment_method_type_enum,
        payment_method_status_enum,
        transaction_type_enum,
        bank_account_type_enum,
        ratelimit_scope_enum,
        ratelimit_window_enum,
        ratelimit_action_enum,
        communication_type_enum,
        communication_status_enum,
        workflow_status_enum,
        workflow_step_status_enum,
        deployment_state_enum,
        agent_status_enum,
        subscription_status_enum,
        billing_cycle_enum,
        import_job_type_enum,
        import_job_status_enum,
        dunning_action_type_enum,
        dunning_execution_status_enum,
    ]
    for enum in enums:
        _ensure_enum(bind, enum)

    # =====================================================================
    # Billing Core adjustments
    # =====================================================================

    if _table_exists(bind, "invoices"):
        columns = _get_columns(bind, "invoices")
        with op.batch_alter_table("invoices") as batch_op:
            if "created_by" not in columns:
                batch_op.add_column(sa.Column("created_by", sa.String(255), nullable=True))
            if "updated_by" not in columns:
                batch_op.add_column(sa.Column("updated_by", sa.String(255), nullable=True))
            if "credit_applications" not in columns:
                batch_op.add_column(
                    sa.Column("credit_applications", postgresql.JSON(), nullable=False, server_default="[]")
                )
            if "extra_data" not in columns:
                batch_op.add_column(
                    sa.Column("extra_data", postgresql.JSON(), nullable=False, server_default="{}")
                )
            if "payment_status" not in columns:
                batch_op.add_column(
                    sa.Column(
                        "payment_status",
                        payment_status_enum,
                        nullable=False,
                        server_default="pending",
                        index=True,
                    )
                )
        if not _has_unique(bind, "invoices", "uq_invoice_idempotency"):
            op.create_unique_constraint("uq_invoice_idempotency", "invoices", ["tenant_id", "idempotency_key"])
        if not _has_unique(bind, "invoices", "uq_invoice_number_by_tenant"):
            op.create_unique_constraint("uq_invoice_number_by_tenant", "invoices", ["tenant_id", "invoice_number"])

    if _table_exists(bind, "payments"):
        columns = _get_columns(bind, "payments")
        with op.batch_alter_table("payments") as batch_op:
            if "extra_data" not in columns:
                batch_op.add_column(
                    sa.Column("extra_data", postgresql.JSON(), nullable=False, server_default="{}")
                )
        if not _has_unique(bind, "payments", "uq_payment_idempotency"):
            op.create_unique_constraint("uq_payment_idempotency", "payments", ["tenant_id", "idempotency_key"])

    if _table_exists(bind, "payment_methods"):
        columns = _get_columns(bind, "payment_methods")
        with op.batch_alter_table("payment_methods") as batch_op:
            if "deleted_at" not in columns:
                batch_op.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
            if "is_active" not in columns:
                batch_op.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"))
            if "account_type" not in columns:
                batch_op.add_column(sa.Column("account_type", bank_account_type_enum, nullable=True))

    if _table_exists(bind, "transactions"):
        columns = _get_columns(bind, "transactions")
        with op.batch_alter_table("transactions") as batch_op:
            if "transaction_date" not in columns:
                batch_op.add_column(
                    sa.Column(
                        "transaction_date",
                        sa.DateTime(timezone=True),
                        nullable=False,
                        server_default=sa.text("now()"),
                    )
                )
            if "extra_data" not in columns:
                batch_op.add_column(
                    sa.Column("extra_data", postgresql.JSON(), nullable=False, server_default="{}")
                )
        if not _has_index(bind, "transactions", "idx_transaction_tenant_customer"):
            op.create_index("idx_transaction_tenant_customer", "transactions", ["tenant_id", "customer_id"])
        if not _has_index(bind, "transactions", "idx_transaction_tenant_date"):
            op.create_index("idx_transaction_tenant_date", "transactions", ["tenant_id", "transaction_date"])

    if not _table_exists(bind, "credit_applications"):
        op.create_table(
            "credit_applications",
            sa.Column("application_id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "credit_note_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("credit_notes.credit_note_id"),
                nullable=False,
            ),
            sa.Column("applied_to_type", sa.String(50), nullable=False),
            sa.Column("applied_to_id", sa.String(255), nullable=False, index=True),
            sa.Column("applied_amount", sa.Integer(), nullable=False),
            sa.Column(
                "application_date",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column("applied_by", sa.String(255), nullable=False),
            sa.Column("notes", sa.String(500), nullable=True),
            sa.Column("extra_data", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index("idx_credit_application_tenant_target", "credit_applications", ["tenant_id", "applied_to_id"])

    if not _table_exists(bind, "customer_credits"):
        op.create_table(
            "customer_credits",
            sa.Column("customer_id", sa.String(255), primary_key=True),
            sa.Column("tenant_id", sa.String(255), primary_key=True),
            sa.Column("total_credit_amount", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
            sa.Column("credit_notes", postgresql.JSON(), nullable=False, server_default="[]"),
            sa.Column("auto_apply_to_new_invoices", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("extra_data", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index("idx_customer_credit_tenant", "customer_credits", ["tenant_id", "customer_id"])

    # =====================================================================
    # Billing settings, pricing rules, and dunning support
    # =====================================================================

    for table_name in (
        "billing_products",
        "billing_product_categories",
        "billing_subscription_plans",
        "billing_subscriptions",
        "billing_addons",
        "billing_tenant_addons",
        "billing_settings",
    ):
        if _table_exists(bind, table_name):
            columns = _get_columns(bind, table_name)
            if "metadata" not in columns:
                with op.batch_alter_table(table_name) as batch_op:
                    batch_op.add_column(
                        sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}")
                    )
                op.execute(
                    f"UPDATE {table_name} SET metadata = COALESCE(metadata, '{{}}'::json)"
                )

    if _table_exists(bind, "billing_settings"):
        columns = _get_columns(bind, "billing_settings")
        with op.batch_alter_table("billing_settings") as batch_op:
            if "company_info" not in columns:
                batch_op.add_column(sa.Column("company_info", postgresql.JSON(), nullable=False, server_default="{}"))
            if "tax_settings" not in columns:
                batch_op.add_column(sa.Column("tax_settings", postgresql.JSON(), nullable=False, server_default="{}"))
            if "payment_settings" not in columns:
                batch_op.add_column(
                    sa.Column("payment_settings", postgresql.JSON(), nullable=False, server_default="{}")
                )
            if "invoice_settings" not in columns:
                batch_op.add_column(
                    sa.Column("invoice_settings", postgresql.JSON(), nullable=False, server_default="{}")
                )
            if "notification_settings" not in columns:
                batch_op.add_column(
                    sa.Column("notification_settings", postgresql.JSON(), nullable=False, server_default="{}")
                )
            if "features_enabled" not in columns:
                batch_op.add_column(
                    sa.Column("features_enabled", postgresql.JSON(), nullable=False, server_default="{}")
                )
            if "custom_settings" not in columns:
                batch_op.add_column(
                    sa.Column("custom_settings", postgresql.JSON(), nullable=False, server_default="{}")
                )
            if "api_settings" not in columns:
                batch_op.add_column(sa.Column("api_settings", postgresql.JSON(), nullable=False, server_default="{}"))

    if not _table_exists(bind, "billing_subscription_events"):
        op.create_table(
            "billing_subscription_events",
            sa.Column("event_id", sa.String(50), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
            sa.Column("subscription_id", sa.String(50), nullable=False, index=True),
            sa.Column("event_type", sa.String(50), nullable=False, index=True),
            sa.Column("event_data", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("user_id", sa.String(50), nullable=True),
            sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index(
            "ix_billing_events_tenant_subscription",
            "billing_subscription_events",
            ["tenant_id", "subscription_id"],
        )
        op.create_index(
            "ix_billing_events_tenant_type",
            "billing_subscription_events",
            ["tenant_id", "event_type"],
        )
        op.create_index("ix_billing_events_created", "billing_subscription_events", ["created_at"])

    if not _table_exists(bind, "billing_pricing_rules"):
        op.create_table(
            "billing_pricing_rules",
            sa.Column("rule_id", sa.String(50), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("applies_to_product_ids", postgresql.JSON(), nullable=False, server_default="[]"),
            sa.Column("applies_to_categories", postgresql.JSON(), nullable=False, server_default="[]"),
            sa.Column("applies_to_all", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("min_quantity", sa.Numeric(10, 0), nullable=True),
            sa.Column("customer_segments", postgresql.JSON(), nullable=False, server_default="[]"),
            sa.Column("discount_type", sa.String(20), nullable=False),
            sa.Column("discount_value", sa.Numeric(15, 2), nullable=False),
            sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("max_uses", sa.Numeric(10, 0), nullable=True),
            sa.Column("current_uses", sa.Numeric(10, 0), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index(
            "ix_billing_rules_tenant_active",
            "billing_pricing_rules",
            ["tenant_id", "is_active"],
        )
        op.create_index(
            "ix_billing_rules_starts_ends",
            "billing_pricing_rules",
            ["starts_at", "ends_at"],
        )

    if not _table_exists(bind, "billing_rule_usage"):
        op.create_table(
            "billing_rule_usage",
            sa.Column("usage_id", sa.String(50), primary_key=True),
            sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
            sa.Column("rule_id", sa.String(50), nullable=False, index=True),
            sa.Column("customer_id", sa.String(50), nullable=False, index=True),
            sa.Column("invoice_id", sa.String(50), nullable=True),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index("ix_billing_rule_usage_tenant_rule", "billing_rule_usage", ["tenant_id", "rule_id"])
        op.create_index(
            "ix_billing_rule_usage_tenant_customer",
            "billing_rule_usage",
            ["tenant_id", "customer_id"],
        )
        op.create_index("ix_billing_rule_usage_used_at", "billing_rule_usage", ["used_at"])

    if _table_exists(bind, "dunning_campaigns"):
        columns = _get_columns(bind, "dunning_campaigns")
        with op.batch_alter_table("dunning_campaigns") as batch_op:
            if "exclusion_rules" not in columns:
                batch_op.add_column(
                    sa.Column("exclusion_rules", postgresql.JSON(), nullable=False, server_default="{}")
                )
            if "created_by" not in columns:
                batch_op.add_column(sa.Column("created_by", sa.String(255), nullable=True))
            if "updated_by" not in columns:
                batch_op.add_column(sa.Column("updated_by", sa.String(255), nullable=True))
        if "actions" in columns:
            op.execute("UPDATE dunning_campaigns SET actions = COALESCE(actions, '[]'::json)")
        if "exclusion_rules" in columns:
            op.execute(
                "UPDATE dunning_campaigns SET exclusion_rules = COALESCE(exclusion_rules, '{}'::json)"
            )

    if not _table_exists(bind, "dunning_campaigns"):
        op.create_table(
            "dunning_campaigns",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(255), nullable=False, index=True),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("trigger_after_days", sa.Integer(), nullable=False),
            sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
            sa.Column("retry_interval_days", sa.Integer(), nullable=False, server_default="3"),
            sa.Column("actions", postgresql.JSON(), nullable=False, server_default="[]"),
            sa.Column("exclusion_rules", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_executions", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("successful_executions", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_recovered_amount", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_by", sa.String(255), nullable=True),
            sa.Column("updated_by", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index(
            "ix_dunning_campaigns_tenant_active",
            "dunning_campaigns",
            ["tenant_id", "is_active"],
        )
        op.create_index(
            "ix_dunning_campaigns_tenant_priority",
            "dunning_campaigns",
            ["tenant_id", "priority"],
        )

    if _table_exists(bind, "dunning_executions"):
        columns = _get_columns(bind, "dunning_executions")
        with op.batch_alter_table("dunning_executions") as batch_op:
            if "execution_log" not in columns:
                batch_op.add_column(
                    sa.Column("execution_log", postgresql.JSON(), nullable=False, server_default="[]")
                )
            if "metadata" not in columns:
                batch_op.add_column(
                    sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}")
                )
            if "created_by" not in columns:
                batch_op.add_column(sa.Column("created_by", sa.String(255), nullable=True))
            if "updated_by" not in columns:
                batch_op.add_column(sa.Column("updated_by", sa.String(255), nullable=True))
        if "metadata_" in columns:
            op.execute("UPDATE dunning_executions SET metadata = COALESCE(metadata, metadata_)")

    if not _table_exists(bind, "dunning_executions"):
        op.create_table(
            "dunning_executions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(255), nullable=False, index=True),
            sa.Column(
                "campaign_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("dunning_campaigns.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column("subscription_id", sa.String(50), nullable=False, index=True),
            sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
            sa.Column("invoice_id", sa.String(50), nullable=True, index=True),
            sa.Column(
                "status",
                dunning_execution_status_enum,
                nullable=False,
                server_default="pending",
                index=True,
            ),
            sa.Column("current_step", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_steps", sa.Integer(), nullable=False),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("next_action_at", sa.DateTime(timezone=True), nullable=True, index=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("outstanding_amount", sa.Integer(), nullable=False),
            sa.Column("recovered_amount", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("execution_log", postgresql.JSON(), nullable=False, server_default="[]"),
            sa.Column("canceled_reason", sa.Text(), nullable=True),
            sa.Column("canceled_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_by", sa.String(255), nullable=True),
            sa.Column("updated_by", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index(
            "ix_dunning_executions_tenant_status",
            "dunning_executions",
            ["tenant_id", "status"],
        )
        op.create_index(
            "ix_dunning_executions_next_action",
            "dunning_executions",
            ["next_action_at"],
        )
        op.create_index(
            "ix_dunning_executions_subscription",
            "dunning_executions",
            ["subscription_id", "status"],
        )

    if not _table_exists(bind, "dunning_action_logs"):
        op.create_table(
            "dunning_action_logs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(255), nullable=False, index=True),
            sa.Column(
                "execution_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("dunning_executions.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column("action_type", dunning_action_type_enum, nullable=False),
            sa.Column("action_config", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("step_number", sa.Integer(), nullable=False),
            sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("result", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("external_id", sa.String(100), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index(
            "ix_dunning_action_logs_execution",
            "dunning_action_logs",
            ["execution_id", "step_number"],
        )
        op.create_index(
            "ix_dunning_action_logs_action_type",
            "dunning_action_logs",
            ["action_type", "status"],
        )

    # =====================================================================
    # Contacts adjustments
    # =====================================================================

    if _table_exists(bind, "contact_label_definitions"):
        columns = _get_columns(bind, "contact_label_definitions")
        with op.batch_alter_table("contact_label_definitions") as batch_op:
            if "name" not in columns:
                batch_op.add_column(sa.Column("name", sa.String(100), nullable=True))
            if "slug" not in columns:
                batch_op.add_column(sa.Column("slug", sa.String(100), nullable=True))
            if "icon" not in columns:
                batch_op.add_column(sa.Column("icon", sa.String(50), nullable=True))
            if "category" not in columns:
                batch_op.add_column(sa.Column("category", sa.String(50), nullable=True))
            if "display_order" not in columns:
                batch_op.add_column(sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"))
            if "is_visible" not in columns:
                batch_op.add_column(sa.Column("is_visible", sa.Boolean(), nullable=False, server_default="true"))
            if "is_system" not in columns:
                batch_op.add_column(sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"))
            if "is_default" not in columns:
                batch_op.add_column(sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"))
            if "metadata" not in columns:
                batch_op.add_column(sa.Column("metadata", postgresql.JSON(), nullable=True))
            if "created_by" not in columns:
                batch_op.add_column(sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True))
        if "label_name" in columns:
            op.execute("UPDATE contact_label_definitions SET name = COALESCE(name, label_name)")
        op.execute("UPDATE contact_label_definitions SET slug = COALESCE(slug, lower(regexp_replace(name, '[^a-z0-9]+', '-', 'g'))) WHERE name IS NOT NULL")
        op.execute("UPDATE contact_label_definitions SET slug = COALESCE(slug, id::text)")
        if not _has_unique(bind, "contact_label_definitions", "uq_tenant_label_slug"):
            op.create_unique_constraint("uq_tenant_label_slug", "contact_label_definitions", ["tenant_id", "slug"])
        if not _has_index(bind, "contact_label_definitions", "ix_contact_label_definitions_slug"):
            op.create_index("ix_contact_label_definitions_slug", "contact_label_definitions", ["slug"])
        if not _has_index(bind, "contact_label_definitions", "ix_contact_label_definitions_category"):
            op.create_index("ix_contact_label_definitions_category", "contact_label_definitions", ["category"])

    if _table_exists(bind, "contact_field_definitions"):
        columns = _get_columns(bind, "contact_field_definitions")
        with op.batch_alter_table("contact_field_definitions") as batch_op:
            if "name" not in columns:
                batch_op.add_column(sa.Column("name", sa.String(100), nullable=True))
            if "field_key" not in columns:
                batch_op.add_column(sa.Column("field_key", sa.String(100), nullable=True))
            if "default_value" not in columns:
                batch_op.add_column(sa.Column("default_value", postgresql.JSON(), nullable=True))
            if "is_unique" not in columns:
                batch_op.add_column(sa.Column("is_unique", sa.Boolean(), nullable=False, server_default="false"))
            if "is_searchable" not in columns:
                batch_op.add_column(sa.Column("is_searchable", sa.Boolean(), nullable=False, server_default="true"))
            if "placeholder" not in columns:
                batch_op.add_column(sa.Column("placeholder", sa.String(255), nullable=True))
            if "help_text" not in columns:
                batch_op.add_column(sa.Column("help_text", sa.Text(), nullable=True))
            if "field_group" not in columns:
                batch_op.add_column(sa.Column("field_group", sa.String(100), nullable=True))
            if "is_visible" not in columns:
                batch_op.add_column(sa.Column("is_visible", sa.Boolean(), nullable=False, server_default="true"))
            if "is_editable" not in columns:
                batch_op.add_column(sa.Column("is_editable", sa.Boolean(), nullable=False, server_default="true"))
            if "required_permission" not in columns:
                batch_op.add_column(sa.Column("required_permission", sa.String(100), nullable=True))
            if "is_system" not in columns:
                batch_op.add_column(sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"))
            if "is_encrypted" not in columns:
                batch_op.add_column(sa.Column("is_encrypted", sa.Boolean(), nullable=False, server_default="false"))
            if "metadata" not in columns:
                batch_op.add_column(sa.Column("metadata", postgresql.JSON(), nullable=True))
            if "created_by" not in columns:
                batch_op.add_column(sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True))
        if "field_name" in columns:
            op.execute("UPDATE contact_field_definitions SET name = COALESCE(name, field_name)")
            op.execute("UPDATE contact_field_definitions SET field_key = COALESCE(field_key, field_name)")
        if "display_name" in columns:
            op.execute("UPDATE contact_field_definitions SET name = COALESCE(name, display_name)")
        op.execute("UPDATE contact_field_definitions SET field_key = COALESCE(field_key, name)")
        if not _has_unique(bind, "contact_field_definitions", "uq_tenant_field_key"):
            op.create_unique_constraint("uq_tenant_field_key", "contact_field_definitions", ["tenant_id", "field_key"])
        if not _has_index(bind, "contact_field_definitions", "ix_contact_field_definitions_field_key"):
            op.create_index(
                "ix_contact_field_definitions_field_key",
                "contact_field_definitions",
                ["field_key"],
            )
        if not _has_index(bind, "contact_field_definitions", "ix_contact_field_definitions_field_group"):
            op.create_index(
                "ix_contact_field_definitions_field_group",
                "contact_field_definitions",
                ["field_group"],
            )

    # =====================================================================
    # Rate limits adjustments
    # =====================================================================

    if _table_exists(bind, "rate_limit_rules"):
        columns = _get_columns(bind, "rate_limit_rules")
        with op.batch_alter_table("rate_limit_rules") as batch_op:
            if "description" not in columns:
                batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
            if "scope" not in columns:
                batch_op.add_column(sa.Column("scope", ratelimit_scope_enum, nullable=False, server_default="global"))
            if "max_requests" not in columns:
                batch_op.add_column(sa.Column("max_requests", sa.Integer(), nullable=False, server_default="0"))
            if "window" not in columns:
                batch_op.add_column(sa.Column("window", ratelimit_window_enum, nullable=False, server_default="minute"))
            if "action" not in columns:
                batch_op.add_column(sa.Column("action", ratelimit_action_enum, nullable=False, server_default="block"))
            if "exempt_user_ids" not in columns:
                batch_op.add_column(sa.Column("exempt_user_ids", postgresql.JSON(), nullable=False, server_default="[]"))
            if "exempt_ip_addresses" not in columns:
                batch_op.add_column(sa.Column("exempt_ip_addresses", postgresql.JSON(), nullable=False, server_default="[]"))
            if "exempt_api_keys" not in columns:
                batch_op.add_column(sa.Column("exempt_api_keys", postgresql.JSON(), nullable=False, server_default="[]"))
            if "config" not in columns:
                batch_op.add_column(sa.Column("config", postgresql.JSON(), nullable=False, server_default="{}"))
            if "deleted_at" not in columns:
                batch_op.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
            if "created_by" not in columns:
                batch_op.add_column(sa.Column("created_by", sa.String(255), nullable=True))
            if "updated_by" not in columns:
                batch_op.add_column(sa.Column("updated_by", sa.String(255), nullable=True))
        if "requests_per_window" in columns:
            op.execute("UPDATE rate_limit_rules SET max_requests = COALESCE(max_requests, requests_per_window)")

    if _table_exists(bind, "rate_limit_logs"):
        columns = _get_columns(bind, "rate_limit_logs")
        with op.batch_alter_table("rate_limit_logs") as batch_op:
            if "rule_name" not in columns:
                batch_op.add_column(sa.Column("rule_name", sa.String(255), nullable=False, server_default=""))
            if "user_id" not in columns:
                batch_op.add_column(sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True, index=True))
            if "ip_address" not in columns:
                batch_op.add_column(sa.Column("ip_address", sa.String(45), nullable=True, index=True))
            if "api_key_id" not in columns:
                batch_op.add_column(sa.Column("api_key_id", sa.String(255), nullable=True, index=True))
            if "current_count" not in columns:
                batch_op.add_column(sa.Column("current_count", sa.Integer(), nullable=False, server_default="0"))
            if "limit" not in columns:
                batch_op.add_column(sa.Column("limit", sa.Integer(), nullable=False, server_default="0"))
            if "window" not in columns:
                batch_op.add_column(sa.Column("window", ratelimit_window_enum, nullable=False, server_default="minute"))
            if "action" not in columns:
                batch_op.add_column(sa.Column("action", ratelimit_action_enum, nullable=False, server_default="block"))
            if "was_blocked" not in columns:
                batch_op.add_column(sa.Column("was_blocked", sa.Boolean(), nullable=False, server_default="true"))
            if "user_agent" not in columns:
                batch_op.add_column(sa.Column("user_agent", sa.Text(), nullable=True))
            if "request_metadata" not in columns:
                batch_op.add_column(sa.Column("request_metadata", postgresql.JSON(), nullable=False, server_default="{}"))
        if "request_count" in columns:
            op.execute("UPDATE rate_limit_logs SET current_count = COALESCE(current_count, request_count)")
        if "was_limited" in columns:
            op.execute("UPDATE rate_limit_logs SET was_blocked = COALESCE(was_blocked, was_limited)")

    # =====================================================================
    # Jobs adjustments
    # =====================================================================

    if _table_exists(bind, "scheduled_jobs"):
        columns = _get_columns(bind, "scheduled_jobs")
        with op.batch_alter_table("scheduled_jobs") as batch_op:
            if "description" not in columns:
                batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
            if "interval_seconds" not in columns:
                batch_op.add_column(sa.Column("interval_seconds", sa.Integer(), nullable=True))
            if "max_concurrent_runs" not in columns:
                batch_op.add_column(sa.Column("max_concurrent_runs", sa.Integer(), nullable=False, server_default="1"))
            if "timeout_seconds" not in columns:
                batch_op.add_column(sa.Column("timeout_seconds", sa.Integer(), nullable=True))
            if "priority" not in columns:
                batch_op.add_column(sa.Column("priority", sa.String(20), nullable=False, server_default="normal"))
            if "max_retries" not in columns:
                batch_op.add_column(sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"))
            if "retry_delay_seconds" not in columns:
                batch_op.add_column(sa.Column("retry_delay_seconds", sa.Integer(), nullable=False, server_default="60"))
            if "parameters" not in columns:
                batch_op.add_column(sa.Column("parameters", postgresql.JSON(), nullable=True))
            if "total_runs" not in columns:
                batch_op.add_column(sa.Column("total_runs", sa.Integer(), nullable=False, server_default="0"))
            if "successful_runs" not in columns:
                batch_op.add_column(sa.Column("successful_runs", sa.Integer(), nullable=False, server_default="0"))
            if "failed_runs" not in columns:
                batch_op.add_column(sa.Column("failed_runs", sa.Integer(), nullable=False, server_default="0"))
            if "created_by" not in columns:
                batch_op.add_column(sa.Column("created_by", sa.String(255), nullable=False, server_default="system"))
            if "updated_at" not in columns:
                batch_op.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
        if not _has_index(bind, "scheduled_jobs", "ix_scheduled_jobs_tenant_active"):
            op.create_index("ix_scheduled_jobs_tenant_active", "scheduled_jobs", ["tenant_id", "is_active"])
        if not _has_index(bind, "scheduled_jobs", "ix_scheduled_jobs_next_run"):
            op.create_index("ix_scheduled_jobs_next_run", "scheduled_jobs", ["is_active", "next_run_at"])

    if _table_exists(bind, "jobs"):
        columns = _get_columns(bind, "jobs")
        with op.batch_alter_table("jobs") as batch_op:
            if "title" not in columns:
                batch_op.add_column(sa.Column("title", sa.String(255), nullable=True))
            if "progress_percent" not in columns:
                batch_op.add_column(sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"))
            if "items_total" not in columns:
                batch_op.add_column(sa.Column("items_total", sa.Integer(), nullable=True))
            if "items_processed" not in columns:
                batch_op.add_column(sa.Column("items_processed", sa.Integer(), nullable=False, server_default="0"))
            if "items_succeeded" not in columns:
                batch_op.add_column(sa.Column("items_succeeded", sa.Integer(), nullable=False, server_default="0"))
            if "items_failed" not in columns:
                batch_op.add_column(sa.Column("items_failed", sa.Integer(), nullable=False, server_default="0"))
            if "current_item" not in columns:
                batch_op.add_column(sa.Column("current_item", sa.String(500), nullable=True))
            if "error_details" not in columns:
                batch_op.add_column(sa.Column("error_details", postgresql.JSON(), nullable=True))
            if "error_traceback" not in columns:
                batch_op.add_column(sa.Column("error_traceback", sa.Text(), nullable=True))
            if "failed_items" not in columns:
                batch_op.add_column(sa.Column("failed_items", postgresql.JSON(), nullable=True))
            if "parameters" not in columns:
                batch_op.add_column(sa.Column("parameters", postgresql.JSON(), nullable=True))
            if "result" not in columns:
                batch_op.add_column(sa.Column("result", postgresql.JSON(), nullable=True))
            if "max_retries" not in columns:
                batch_op.add_column(sa.Column("max_retries", sa.Integer(), nullable=False, server_default="0"))
            if "retry_count" not in columns:
                batch_op.add_column(sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"))
            if "retry_delay_seconds" not in columns:
                batch_op.add_column(sa.Column("retry_delay_seconds", sa.Integer(), nullable=True))
            if "next_retry_at" not in columns:
                batch_op.add_column(sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True))
            if "timeout_seconds" not in columns:
                batch_op.add_column(sa.Column("timeout_seconds", sa.Integer(), nullable=True))
            if "assigned_technician_id" not in columns:
                batch_op.add_column(sa.Column("assigned_technician_id", postgresql.UUID(as_uuid=True), nullable=True))
            if "scheduled_start" not in columns:
                batch_op.add_column(sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=True))
            if "scheduled_end" not in columns:
                batch_op.add_column(sa.Column("scheduled_end", sa.DateTime(timezone=True), nullable=True))
            if "actual_start" not in columns:
                batch_op.add_column(sa.Column("actual_start", sa.DateTime(timezone=True), nullable=True))
            if "actual_end" not in columns:
                batch_op.add_column(sa.Column("actual_end", sa.DateTime(timezone=True), nullable=True))
            if "location_lat" not in columns:
                batch_op.add_column(sa.Column("location_lat", sa.Float(), nullable=True))
            if "location_lng" not in columns:
                batch_op.add_column(sa.Column("location_lng", sa.Float(), nullable=True))
            if "service_address" not in columns:
                batch_op.add_column(sa.Column("service_address", sa.String(500), nullable=True))
            if "customer_signature" not in columns:
                batch_op.add_column(sa.Column("customer_signature", sa.Text(), nullable=True))
            if "completion_notes" not in columns:
                batch_op.add_column(sa.Column("completion_notes", sa.Text(), nullable=True))
            if "photos" not in columns:
                batch_op.add_column(sa.Column("photos", postgresql.JSON(), nullable=True))
            if "parent_job_id" not in columns:
                batch_op.add_column(sa.Column("parent_job_id", postgresql.UUID(as_uuid=True), nullable=True))
            if "scheduled_job_id" not in columns:
                batch_op.add_column(sa.Column("scheduled_job_id", postgresql.UUID(as_uuid=True), nullable=True))
            if "created_by" not in columns:
                batch_op.add_column(sa.Column("created_by", sa.String(255), nullable=False, server_default="system"))
            if "cancelled_by" not in columns:
                batch_op.add_column(sa.Column("cancelled_by", sa.String(255), nullable=True))
            if "cancelled_at" not in columns:
                batch_op.add_column(sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))
        if "priority" in columns and isinstance(columns["priority"]["type"], sa.Integer):
            op.alter_column(
                "jobs",
                "priority",
                type_=sa.String(20),
                postgresql_using=(
                    "CASE "
                    "WHEN priority >= 3 THEN 'critical' "
                    "WHEN priority = 2 THEN 'high' "
                    "WHEN priority = 1 THEN 'normal' "
                    "ELSE 'low' "
                    "END"
                ),
            )

    if not _table_exists(bind, "job_chains"):
        op.create_table(
            "job_chains",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(255), nullable=False, index=True),
            sa.Column("name", sa.String(255), nullable=False, index=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("execution_mode", sa.String(20), nullable=False, server_default="sequential"),
            sa.Column("chain_definition", postgresql.JSON(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true", index=True),
            sa.Column("stop_on_failure", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("timeout_seconds", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending", index=True),
            sa.Column("current_step", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_steps", sa.Integer(), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("results", postgresql.JSON(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_by", sa.String(255), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index("ix_job_chains_tenant_status", "job_chains", ["tenant_id", "status"])
        op.create_index("ix_job_chains_tenant_active", "job_chains", ["tenant_id", "is_active"])

    # =====================================================================
    # Webhooks adjustments
    # =====================================================================

    if _table_exists(bind, "webhook_deliveries"):
        columns = _get_columns(bind, "webhook_deliveries")
        with op.batch_alter_table("webhook_deliveries") as batch_op:
            if "event_id" not in columns:
                batch_op.add_column(sa.Column("event_id", sa.String(255), nullable=True, index=True))
            if "event_data" not in columns:
                batch_op.add_column(sa.Column("event_data", postgresql.JSON(), nullable=True))
            if "attempt_number" not in columns:
                batch_op.add_column(sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"))
            if "next_retry_at" not in columns:
                batch_op.add_column(sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True))
            if "duration_ms" not in columns:
                batch_op.add_column(sa.Column("duration_ms", sa.Integer(), nullable=True))
            if "response_code" not in columns:
                batch_op.add_column(sa.Column("response_code", sa.Integer(), nullable=True))
            if "response_body" not in columns:
                batch_op.add_column(sa.Column("response_body", sa.Text(), nullable=True))
            if "updated_at" not in columns:
                batch_op.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
        if "payload" in columns:
            op.execute(
                "UPDATE webhook_deliveries "
                "SET event_data = COALESCE(event_data, payload::json)"
            )
        if "attempts" in columns:
            op.execute("UPDATE webhook_deliveries SET attempt_number = COALESCE(attempt_number, attempts)")
        if "response_status" in columns:
            op.execute("UPDATE webhook_deliveries SET response_code = COALESCE(response_code, response_status)")

    # =====================================================================
    # Communications adjustments
    # =====================================================================

    if _table_exists(bind, "communication_logs"):
        columns = _get_columns(bind, "communication_logs")
        with op.batch_alter_table("communication_logs") as batch_op:
            if "type" not in columns:
                batch_op.add_column(sa.Column("type", communication_type_enum, nullable=True, index=True))
            if "sender" not in columns:
                batch_op.add_column(sa.Column("sender", sa.String(500), nullable=True))
            if "text_body" not in columns:
                batch_op.add_column(sa.Column("text_body", sa.Text(), nullable=True))
            if "html_body" not in columns:
                batch_op.add_column(sa.Column("html_body", sa.Text(), nullable=True))
            if "failed_at" not in columns:
                batch_op.add_column(sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True))
            if "retry_count" not in columns:
                batch_op.add_column(sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"))
            if "template_id" not in columns:
                batch_op.add_column(sa.Column("template_id", sa.String(255), nullable=True))
            if "user_id" not in columns:
                batch_op.add_column(sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True, index=True))
            if "job_id" not in columns:
                batch_op.add_column(sa.Column("job_id", sa.String(255), nullable=True, index=True))
            if "headers" not in columns:
                batch_op.add_column(sa.Column("headers", postgresql.JSON(), nullable=False, server_default="{}"))
            if "updated_at" not in columns:
                batch_op.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
        if "channel" in columns:
            op.execute(
                "UPDATE communication_logs "
                "SET type = CASE WHEN type IS NULL THEN channel::communicationtype ELSE type END"
            )

    if _table_exists(bind, "communication_stats"):
        columns = _get_columns(bind, "communication_stats")
        with op.batch_alter_table("communication_stats") as batch_op:
            if "stats_date" not in columns:
                batch_op.add_column(sa.Column("stats_date", sa.DateTime(timezone=True), nullable=True, index=True))
            if "type" not in columns:
                batch_op.add_column(sa.Column("type", communication_type_enum, nullable=True, index=True))
            if "total_sent" not in columns:
                batch_op.add_column(sa.Column("total_sent", sa.Integer(), nullable=False, server_default="0"))
            if "total_delivered" not in columns:
                batch_op.add_column(sa.Column("total_delivered", sa.Integer(), nullable=False, server_default="0"))
            if "total_failed" not in columns:
                batch_op.add_column(sa.Column("total_failed", sa.Integer(), nullable=False, server_default="0"))
            if "total_bounced" not in columns:
                batch_op.add_column(sa.Column("total_bounced", sa.Integer(), nullable=False, server_default="0"))
            if "total_pending" not in columns:
                batch_op.add_column(sa.Column("total_pending", sa.Integer(), nullable=False, server_default="0"))
            if "avg_delivery_time_seconds" not in columns:
                batch_op.add_column(sa.Column("avg_delivery_time_seconds", sa.Float(), nullable=True))
            if "metadata" not in columns:
                batch_op.add_column(sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"))
            if "created_at" not in columns:
                batch_op.add_column(sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
            if "updated_at" not in columns:
                batch_op.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
        if "period_start" in columns:
            op.execute("UPDATE communication_stats SET stats_date = COALESCE(stats_date, period_start)")
        if "channel" in columns:
            op.execute(
                "UPDATE communication_stats "
                "SET type = CASE WHEN type IS NULL THEN channel::communicationtype ELSE type END"
            )
        if "sent_count" in columns:
            op.execute("UPDATE communication_stats SET total_sent = COALESCE(total_sent, sent_count)")
        if "delivered_count" in columns:
            op.execute("UPDATE communication_stats SET total_delivered = COALESCE(total_delivered, delivered_count)")
        if "failed_count" in columns:
            op.execute("UPDATE communication_stats SET total_failed = COALESCE(total_failed, failed_count)")
        if "opened_count" in columns:
            op.execute("UPDATE communication_stats SET total_pending = COALESCE(total_pending, opened_count)")

    # =====================================================================
    # Workflows adjustments
    # =====================================================================

    if _table_exists(bind, "workflows"):
        columns = _get_columns(bind, "workflows")
        if "id" in columns and not _is_integer_type(columns["id"]["type"]) and not _table_exists(
            bind, "workflows_legacy"
        ):
            op.rename_table("workflows", "workflows_legacy")

    if _table_exists(bind, "workflow_executions"):
        columns = _get_columns(bind, "workflow_executions")
        if ("current_step" in columns or "workflow_name" in columns) and not _table_exists(
            bind, "workflow_executions_legacy"
        ):
            op.rename_table("workflow_executions", "workflow_executions_legacy")

    if not _table_exists(bind, "workflows"):
        op.create_table(
            "workflows",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False, unique=True, index=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("definition", postgresql.JSON(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("version", sa.String(20), nullable=False, server_default="1.0.0"),
            sa.Column("tags", postgresql.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    if not _table_exists(bind, "workflow_executions"):
        for index_name in (
            "ix_workflow_executions_tenant_id",
            "ix_workflow_executions_status",
            "ix_workflow_executions_workflow_id",
        ):
            if _index_exists_global(bind, index_name):
                op.execute(f'DROP INDEX IF EXISTS "{index_name}"')
        op.create_table(
            "workflow_executions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "workflow_id",
                sa.Integer(),
                sa.ForeignKey("workflows.id"),
                nullable=False,
                index=True,
            ),
            sa.Column("status", workflow_status_enum, nullable=False, server_default="pending", index=True),
            sa.Column("context", postgresql.JSON(), nullable=True),
            sa.Column("result", postgresql.JSON(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("trigger_type", sa.String(50), nullable=True),
            sa.Column("trigger_source", sa.String(255), nullable=True),
            sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    if not _table_exists(bind, "workflow_steps"):
        op.create_table(
            "workflow_steps",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "execution_id",
                sa.Integer(),
                sa.ForeignKey("workflow_executions.id"),
                nullable=False,
                index=True,
            ),
            sa.Column("step_name", sa.String(255), nullable=False),
            sa.Column("step_type", sa.String(50), nullable=False),
            sa.Column("sequence_number", sa.Integer(), nullable=False),
            sa.Column("status", workflow_step_status_enum, nullable=False, server_default="pending", index=True),
            sa.Column("input_data", postgresql.JSON(), nullable=True),
            sa.Column("output_data", postgresql.JSON(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("error_details", postgresql.JSON(), nullable=True),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("duration_seconds", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # =====================================================================
    # Deployment adjustments
    # =====================================================================

    if _table_exists(bind, "deployment_instances"):
        columns = _get_columns(bind, "deployment_instances")
        if ("instance_type" in columns or "status" in columns) and not _table_exists(
            bind, "deployment_instances_legacy"
        ):
            op.rename_table("deployment_instances", "deployment_instances_legacy")

    if not _table_exists(bind, "deployment_instances"):
        for index_name in (
            "ix_deployment_instances_tenant_id",
            "ix_deployment_instances_environment",
            "ix_deployment_instances_state",
        ):
            if _index_exists_global(bind, index_name):
                op.execute(f'DROP INDEX IF EXISTS "{index_name}"')
        op.create_table(
            "deployment_instances",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
            sa.Column("template_id", sa.Integer(), sa.ForeignKey("deployment_templates.id"), nullable=True),
            sa.Column("environment", sa.String(50), nullable=False, index=True),
            sa.Column("region", sa.String(50), nullable=True),
            sa.Column("availability_zone", sa.String(50), nullable=True),
            sa.Column("state", deployment_state_enum, nullable=False, server_default="pending", index=True),
            sa.Column("state_reason", sa.Text(), nullable=True),
            sa.Column("last_state_change", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("config", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("secrets_path", sa.String(500), nullable=True),
            sa.Column("version", sa.String(50), nullable=False, server_default="1.0.0"),
            sa.Column("endpoints", postgresql.JSON(), nullable=True),
            sa.Column("namespace", sa.String(255), nullable=True),
            sa.Column("cluster_name", sa.String(255), nullable=True),
            sa.Column("backend_job_id", sa.String(255), nullable=True),
            sa.Column("allocated_cpu", sa.Integer(), nullable=True),
            sa.Column("allocated_memory_gb", sa.Integer(), nullable=True),
            sa.Column("allocated_storage_gb", sa.Integer(), nullable=True),
            sa.Column("health_check_url", sa.String(500), nullable=True),
            sa.Column("last_health_check", sa.DateTime(timezone=True), nullable=True),
            sa.Column("health_status", sa.String(50), nullable=True),
            sa.Column("health_details", postgresql.JSON(), nullable=True),
            sa.Column("tags", postgresql.JSON(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("deployed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.UniqueConstraint("tenant_id", "environment", name="uq_tenant_environment"),
        )

    if not _table_exists(bind, "deployment_executions"):
        op.create_table(
            "deployment_executions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "instance_id",
                sa.Integer(),
                sa.ForeignKey("deployment_instances.id"),
                nullable=False,
            ),
            sa.Column("operation", sa.String(50), nullable=False, index=True),
            sa.Column("state", sa.String(50), nullable=False, server_default="running", index=True),
            sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("duration_seconds", sa.Integer(), nullable=True),
            sa.Column("backend_job_id", sa.String(255), nullable=True, index=True),
            sa.Column("backend_job_url", sa.String(500), nullable=True),
            sa.Column("backend_logs", sa.Text(), nullable=True),
            sa.Column("operation_config", postgresql.JSON(), nullable=True),
            sa.Column("from_version", sa.String(50), nullable=True),
            sa.Column("to_version", sa.String(50), nullable=True),
            sa.Column("result", sa.String(50), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column(
                "rollback_execution_id",
                sa.Integer(),
                sa.ForeignKey("deployment_executions.id"),
                nullable=True,
            ),
            sa.Column("triggered_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("trigger_type", sa.String(50), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    if not _table_exists(bind, "deployment_health"):
        op.create_table(
            "deployment_health",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "instance_id",
                sa.Integer(),
                sa.ForeignKey("deployment_instances.id"),
                nullable=False,
                index=True,
            ),
            sa.Column("check_type", sa.String(50), nullable=False),
            sa.Column("endpoint", sa.String(500), nullable=True),
            sa.Column("status", sa.String(50), nullable=False, index=True),
            sa.Column("response_time_ms", sa.Integer(), nullable=True),
            sa.Column("cpu_usage_percent", sa.Integer(), nullable=True),
            sa.Column("memory_usage_percent", sa.Integer(), nullable=True),
            sa.Column("disk_usage_percent", sa.Integer(), nullable=True),
            sa.Column("active_connections", sa.Integer(), nullable=True),
            sa.Column("request_rate", sa.Integer(), nullable=True),
            sa.Column("error_rate", sa.Integer(), nullable=True),
            sa.Column("details", postgresql.JSON(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("alerts_triggered", postgresql.JSON(), nullable=True),
            sa.Column(
                "checked_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
                index=True,
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # =====================================================================
    # Monitoring adjustments
    # =====================================================================

    if _table_exists(bind, "monitoring_alert_channels"):
        columns = _get_columns(bind, "monitoring_alert_channels")
        with op.batch_alter_table("monitoring_alert_channels") as batch_op:
            if "enabled" not in columns:
                batch_op.add_column(sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"))
            if "created_by" not in columns:
                batch_op.add_column(sa.Column("created_by", sa.String(255), nullable=True))
            if "updated_by" not in columns:
                batch_op.add_column(sa.Column("updated_by", sa.String(255), nullable=True))
            if "deleted_at" not in columns:
                batch_op.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
            if "is_active" not in columns:
                batch_op.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"))
        if "id" in columns and isinstance(columns["id"]["type"], postgresql.UUID):
            op.alter_column("monitoring_alert_channels", "id", type_=sa.String(120), postgresql_using="id::text")

    # =====================================================================
    # Data import/transfer adjustments
    # =====================================================================

    if _table_exists(bind, "data_import_jobs"):
        columns = _get_columns(bind, "data_import_jobs")
        with op.batch_alter_table("data_import_jobs") as batch_op:
            if "job_type" not in columns:
                batch_op.add_column(sa.Column("job_type", import_job_type_enum, nullable=False, server_default="mixed"))
            if "status" not in columns:
                batch_op.add_column(sa.Column("status", import_job_status_enum, nullable=False, server_default="pending"))
            if "file_name" not in columns:
                batch_op.add_column(sa.Column("file_name", sa.String(255), nullable=True))
            if "file_size" not in columns:
                batch_op.add_column(sa.Column("file_size", sa.Integer(), nullable=True))
            if "file_format" not in columns:
                batch_op.add_column(sa.Column("file_format", sa.String(20), nullable=True))
            if "successful_records" not in columns:
                batch_op.add_column(sa.Column("successful_records", sa.Integer(), nullable=False, server_default="0"))
            if "failed_records" not in columns:
                batch_op.add_column(sa.Column("failed_records", sa.Integer(), nullable=False, server_default="0"))
            if "initiated_by" not in columns:
                batch_op.add_column(sa.Column("initiated_by", postgresql.UUID(as_uuid=True), nullable=True))
            if "config" not in columns:
                batch_op.add_column(sa.Column("config", postgresql.JSON(), nullable=False, server_default="{}"))
            if "summary" not in columns:
                batch_op.add_column(sa.Column("summary", postgresql.JSON(), nullable=False, server_default="{}"))
            if "error_message" not in columns:
                batch_op.add_column(sa.Column("error_message", sa.Text(), nullable=True))
            if "celery_task_id" not in columns:
                batch_op.add_column(sa.Column("celery_task_id", sa.String(255), nullable=True))

    if not _table_exists(bind, "data_import_failures"):
        op.create_table(
            "data_import_failures",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "job_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("data_import_jobs.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
            sa.Column("row_number", sa.Integer(), nullable=False),
            sa.Column("error_type", sa.String(50), nullable=False),
            sa.Column("error_message", sa.Text(), nullable=False),
            sa.Column("row_data", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("field_errors", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("can_retry", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("resolved", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index(
            "ix_import_failures_job_resolved",
            "data_import_failures",
            ["job_id", "resolved"],
        )
        op.create_index(
            "ix_import_failures_error_type",
            "data_import_failures",
            ["error_type"],
        )

    if _table_exists(bind, "data_transfer_jobs"):
        columns = _get_columns(bind, "data_transfer_jobs")
        with op.batch_alter_table("data_transfer_jobs") as batch_op:
            if "job_type" not in columns:
                batch_op.add_column(sa.Column("job_type", sa.String(50), nullable=True, index=True))
            if "status" not in columns:
                batch_op.add_column(sa.Column("status", sa.String(50), nullable=False, server_default="pending"))
            if "total_records" not in columns:
                batch_op.add_column(sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"))
            if "processed_records" not in columns:
                batch_op.add_column(sa.Column("processed_records", sa.Integer(), nullable=False, server_default="0"))
            if "failed_records" not in columns:
                batch_op.add_column(sa.Column("failed_records", sa.Integer(), nullable=False, server_default="0"))
            if "progress_percentage" not in columns:
                batch_op.add_column(sa.Column("progress_percentage", sa.Float(), nullable=False, server_default="0"))
            if "celery_task_id" not in columns:
                batch_op.add_column(sa.Column("celery_task_id", sa.String(255), nullable=True, index=True))
            if "import_source" not in columns:
                batch_op.add_column(sa.Column("import_source", sa.String(50), nullable=True))
            if "source_path" not in columns:
                batch_op.add_column(sa.Column("source_path", sa.String(1024), nullable=True))
            if "export_target" not in columns:
                batch_op.add_column(sa.Column("export_target", sa.String(50), nullable=True))
            if "target_path" not in columns:
                batch_op.add_column(sa.Column("target_path", sa.String(1024), nullable=True))
            if "config" not in columns:
                batch_op.add_column(sa.Column("config", postgresql.JSON(), nullable=False, server_default="{}"))
            if "summary" not in columns:
                batch_op.add_column(sa.Column("summary", postgresql.JSON(), nullable=False, server_default="{}"))
            if "metadata" not in columns:
                batch_op.add_column(sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"))
        if "transfer_type" in columns:
            op.execute("UPDATE data_transfer_jobs SET job_type = COALESCE(job_type, transfer_type)")
        if "progress_percent" in columns:
            op.execute("UPDATE data_transfer_jobs SET progress_percentage = COALESCE(progress_percentage, progress_percent)")

    # =====================================================================
    # Audit adjustments
    # =====================================================================

    if _table_exists(bind, "audit_activities"):
        columns = _get_columns(bind, "audit_activities")
        with op.batch_alter_table("audit_activities") as batch_op:
            if "activity_type" not in columns:
                batch_op.add_column(sa.Column("activity_type", sa.String(100), nullable=True))
            if "severity" not in columns:
                batch_op.add_column(sa.Column("severity", sa.String(20), nullable=False, server_default="low"))
            if "user_id" not in columns:
                batch_op.add_column(sa.Column("user_id", sa.String(255), nullable=True))
            if "timestamp" not in columns:
                batch_op.add_column(sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True))
            if "description" not in columns:
                batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
            if "details" not in columns:
                batch_op.add_column(sa.Column("details", postgresql.JSON(), nullable=True))
            if "request_id" not in columns:
                batch_op.add_column(sa.Column("request_id", sa.String(255), nullable=True))
            if "created_at" not in columns:
                batch_op.add_column(sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
            if "updated_at" not in columns:
                batch_op.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
        if "action" in columns:
            op.execute("UPDATE audit_activities SET description = COALESCE(description, action)")
        if "created_at" in columns and "timestamp" in columns:
            op.execute("UPDATE audit_activities SET timestamp = COALESCE(timestamp, created_at)")
        if not _has_index(bind, "audit_activities", "ix_audit_activities_user_timestamp"):
            op.create_index("ix_audit_activities_user_timestamp", "audit_activities", ["user_id", "timestamp"])
        if not _has_index(bind, "audit_activities", "ix_audit_activities_tenant_timestamp"):
            op.create_index("ix_audit_activities_tenant_timestamp", "audit_activities", ["tenant_id", "timestamp"])
        if not _has_index(bind, "audit_activities", "ix_audit_activities_type_timestamp"):
            op.create_index("ix_audit_activities_type_timestamp", "audit_activities", ["activity_type", "timestamp"])
        if not _has_index(bind, "audit_activities", "ix_audit_activities_severity_timestamp"):
            op.create_index("ix_audit_activities_severity_timestamp", "audit_activities", ["severity", "timestamp"])

    # =====================================================================
    # Team members adjustments
    # =====================================================================

    if _table_exists(bind, "team_members"):
        columns = _get_columns(bind, "team_members")
        with op.batch_alter_table("team_members") as batch_op:
            if "tenant_id" not in columns:
                batch_op.add_column(sa.Column("tenant_id", sa.String(255), nullable=True, index=True))
            if "is_active" not in columns:
                batch_op.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"))
            if "left_at" not in columns:
                batch_op.add_column(sa.Column("left_at", sa.DateTime(timezone=True), nullable=True))
            if "notes" not in columns:
                batch_op.add_column(sa.Column("notes", sa.Text(), nullable=True))
            if "metadata" not in columns:
                batch_op.add_column(sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"))
            if "created_at" not in columns:
                batch_op.add_column(sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
            if "updated_at" not in columns:
                batch_op.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
        if not _has_unique(bind, "team_members", "uq_team_members_tenant_team_user"):
            op.create_unique_constraint(
                "uq_team_members_tenant_team_user",
                "team_members",
                ["tenant_id", "team_id", "user_id"],
            )

    # =====================================================================
    # Agent availability adjustments
    # =====================================================================

    if _table_exists(bind, "agent_availability"):
        columns = _get_columns(bind, "agent_availability")
        with op.batch_alter_table("agent_availability") as batch_op:
            if "user_id" not in columns:
                batch_op.add_column(sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True, index=True))
            if "status_message" not in columns:
                batch_op.add_column(sa.Column("status_message", sa.Text(), nullable=True))
        if "agent_id" in columns:
            op.execute("UPDATE agent_availability SET user_id = COALESCE(user_id, agent_id)")

    # =====================================================================
    # Licensing framework adjustments
    # =====================================================================

    if _table_exists(bind, "licensing_module_capabilities"):
        columns = _get_columns(bind, "licensing_module_capabilities")
        with op.batch_alter_table("licensing_module_capabilities") as batch_op:
            if "api_endpoints" not in columns:
                batch_op.add_column(sa.Column("api_endpoints", postgresql.JSON(), nullable=False, server_default="[]"))
            if "ui_routes" not in columns:
                batch_op.add_column(sa.Column("ui_routes", postgresql.JSON(), nullable=False, server_default="[]"))
            if "permissions" not in columns:
                batch_op.add_column(sa.Column("permissions", postgresql.JSON(), nullable=False, server_default="[]"))
            if "config" not in columns:
                batch_op.add_column(sa.Column("config", postgresql.JSON(), nullable=False, server_default="{}"))
            if "is_active" not in columns:
                batch_op.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"))
            if "created_at" not in columns:
                batch_op.add_column(sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
        if not _has_unique(bind, "licensing_module_capabilities", "ix_module_capabilities_module_capability"):
            op.create_unique_constraint(
                "ix_module_capabilities_module_capability",
                "licensing_module_capabilities",
                ["module_id", "capability_code"],
            )

    if _table_exists(bind, "licensing_tenant_subscriptions"):
        columns = _get_columns(bind, "licensing_tenant_subscriptions")
        with op.batch_alter_table("licensing_tenant_subscriptions") as batch_op:
            if "status" not in columns:
                batch_op.add_column(sa.Column("status", subscription_status_enum, nullable=False, server_default="trial"))
            if "billing_cycle" not in columns:
                batch_op.add_column(sa.Column("billing_cycle", billing_cycle_enum, nullable=False, server_default="monthly"))
            if "monthly_price" not in columns:
                batch_op.add_column(sa.Column("monthly_price", sa.Numeric(15, 2), nullable=False, server_default="0"))
            if "annual_price" not in columns:
                batch_op.add_column(sa.Column("annual_price", sa.Numeric(15, 2), nullable=True))
            if "currency" not in columns:
                batch_op.add_column(sa.Column("currency", sa.String(3), nullable=False, server_default="USD"))
            if "trial_start" not in columns:
                batch_op.add_column(sa.Column("trial_start", sa.DateTime(timezone=True), nullable=True))
            if "trial_end" not in columns:
                batch_op.add_column(sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True))
            if "current_period_start" not in columns:
                batch_op.add_column(sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True))
            if "current_period_end" not in columns:
                batch_op.add_column(sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True))
            if "cancelled_at" not in columns:
                batch_op.add_column(sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))
            if "ended_at" not in columns:
                batch_op.add_column(sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True))
            if "auto_renew" not in columns:
                batch_op.add_column(sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default="true"))
            if "billing_email" not in columns:
                batch_op.add_column(sa.Column("billing_email", sa.String(255), nullable=True))
            if "payment_method_id" not in columns:
                batch_op.add_column(sa.Column("payment_method_id", sa.String(100), nullable=True))
            if "stripe_subscription_id" not in columns:
                batch_op.add_column(sa.Column("stripe_subscription_id", sa.String(100), nullable=True, index=True))
            if "paypal_subscription_id" not in columns:
                batch_op.add_column(sa.Column("paypal_subscription_id", sa.String(100), nullable=True, index=True))
            if "extra_metadata" not in columns:
                batch_op.add_column(sa.Column("extra_metadata", postgresql.JSON(), nullable=False, server_default="{}"))
        if not _has_index(bind, "licensing_tenant_subscriptions", "ix_tenant_subscriptions_tenant_status"):
            op.create_index(
                "ix_tenant_subscriptions_tenant_status",
                "licensing_tenant_subscriptions",
                ["tenant_id", "status"],
            )
        if not _has_index(bind, "licensing_tenant_subscriptions", "ix_tenant_subscriptions_plan_status"):
            op.create_index(
                "ix_tenant_subscriptions_plan_status",
                "licensing_tenant_subscriptions",
                ["plan_id", "status"],
            )

    if _table_exists(bind, "licensing_subscription_modules"):
        columns = _get_columns(bind, "licensing_subscription_modules")
        with op.batch_alter_table("licensing_subscription_modules") as batch_op:
            if "is_enabled" not in columns:
                batch_op.add_column(sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"))
            if "source" not in columns:
                batch_op.add_column(sa.Column("source", sa.String(20), nullable=True))
            if "addon_price" not in columns:
                batch_op.add_column(sa.Column("addon_price", sa.Numeric(15, 2), nullable=True))
            if "trial_only" not in columns:
                batch_op.add_column(sa.Column("trial_only", sa.Boolean(), nullable=False, server_default="false"))
            if "expires_at" not in columns:
                batch_op.add_column(sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
            if "config" not in columns:
                batch_op.add_column(sa.Column("config", postgresql.JSON(), nullable=False, server_default="{}"))
            if "activated_at" not in columns:
                batch_op.add_column(sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True))
            if "deactivated_at" not in columns:
                batch_op.add_column(sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True))
        if not _has_unique(bind, "licensing_subscription_modules", "ix_subscription_modules_subscription_module"):
            op.create_unique_constraint(
                "ix_subscription_modules_subscription_module",
                "licensing_subscription_modules",
                ["subscription_id", "module_id"],
            )

    if _table_exists(bind, "licensing_service_plans"):
        columns = _get_columns(bind, "licensing_service_plans")
        with op.batch_alter_table("licensing_service_plans") as batch_op:
            if "annual_discount_percent" not in columns:
                batch_op.add_column(sa.Column("annual_discount_percent", sa.Float(), nullable=False, server_default="0"))
            if "trial_days" not in columns:
                batch_op.add_column(sa.Column("trial_days", sa.Integer(), nullable=False, server_default="14"))
            if "trial_modules" not in columns:
                batch_op.add_column(sa.Column("trial_modules", postgresql.JSON(), nullable=False, server_default="[]"))
            if "is_active" not in columns:
                batch_op.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"))
            if "is_archived" not in columns:
                batch_op.add_column(sa.Column("is_archived", sa.Boolean(), nullable=False, server_default="false"))
            if "effective_from" not in columns:
                batch_op.add_column(sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True))
            if "effective_until" not in columns:
                batch_op.add_column(sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True))
            if "extra_metadata" not in columns:
                batch_op.add_column(sa.Column("extra_metadata", postgresql.JSON(), nullable=False, server_default="{}"))
        if "metadata" in columns:
            op.execute(
                "UPDATE licensing_service_plans SET extra_metadata = COALESCE(extra_metadata, metadata)"
            )
        op.execute(
            "UPDATE licensing_service_plans SET annual_discount_percent = COALESCE(annual_discount_percent, 0)"
        )
        op.execute("UPDATE licensing_service_plans SET trial_days = COALESCE(trial_days, 14)")
        op.execute(
            "UPDATE licensing_service_plans SET trial_modules = COALESCE(trial_modules, '[]'::json)"
        )
        op.execute("UPDATE licensing_service_plans SET is_active = COALESCE(is_active, true)")
        op.execute("UPDATE licensing_service_plans SET is_archived = COALESCE(is_archived, false)")
        if not _has_index(bind, "licensing_service_plans", "ix_service_plans_code_version"):
            op.create_index(
                "ix_service_plans_code_version",
                "licensing_service_plans",
                ["plan_code", "version"],
                unique=True,
            )
        if not _has_index(bind, "licensing_service_plans", "ix_service_plans_active"):
            op.create_index(
                "ix_service_plans_active",
                "licensing_service_plans",
                ["is_active", "is_public"],
            )

    if not _table_exists(bind, "licensing_service_plans"):
        op.create_table(
            "licensing_service_plans",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("plan_name", sa.String(255), nullable=False),
            sa.Column("plan_code", sa.String(100), nullable=False, index=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_template", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("is_public", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("is_custom", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("base_price_monthly", sa.Numeric(15, 2), nullable=False),
            sa.Column("base_price_annual", sa.Numeric(15, 2), nullable=True),
            sa.Column("setup_fee", sa.Numeric(15, 2), nullable=False, server_default="0"),
            sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
            sa.Column("annual_discount_percent", sa.Float(), nullable=False, server_default="0"),
            sa.Column("trial_days", sa.Integer(), nullable=False, server_default="14"),
            sa.Column("trial_modules", postgresql.JSON(), nullable=False, server_default="[]"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("is_archived", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
            sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
            sa.Column("extra_metadata", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index(
            "ix_service_plans_code_version",
            "licensing_service_plans",
            ["plan_code", "version"],
            unique=True,
        )
        op.create_index(
            "ix_service_plans_active",
            "licensing_service_plans",
            ["is_active", "is_public"],
        )

    if _table_exists(bind, "licensing_plan_modules"):
        columns = _get_columns(bind, "licensing_plan_modules")
        with op.batch_alter_table("licensing_plan_modules") as batch_op:
            if "included_by_default" not in columns:
                batch_op.add_column(sa.Column("included_by_default", sa.Boolean(), nullable=False, server_default="true"))
            if "is_optional_addon" not in columns:
                batch_op.add_column(sa.Column("is_optional_addon", sa.Boolean(), nullable=False, server_default="false"))
            if "override_price" not in columns:
                batch_op.add_column(sa.Column("override_price", sa.Numeric(15, 2), nullable=True))
            if "override_pricing_model" not in columns:
                batch_op.add_column(sa.Column("override_pricing_model", pricing_model_enum, nullable=True))
            if "config_override" not in columns:
                batch_op.add_column(sa.Column("config_override", postgresql.JSON(), nullable=False, server_default="{}"))
            if "trial_only" not in columns:
                batch_op.add_column(sa.Column("trial_only", sa.Boolean(), nullable=False, server_default="false"))
            if "promotional_until" not in columns:
                batch_op.add_column(sa.Column("promotional_until", sa.DateTime(timezone=True), nullable=True))
        if "is_required" in columns:
            op.execute(
                "UPDATE licensing_plan_modules SET included_by_default = COALESCE(included_by_default, is_required)"
            )
        if "config" in columns:
            op.execute(
                "UPDATE licensing_plan_modules SET config_override = COALESCE(config_override, config)"
            )
        if not _has_index(bind, "licensing_plan_modules", "ix_plan_modules_plan_module"):
            op.create_index(
                "ix_plan_modules_plan_module",
                "licensing_plan_modules",
                ["plan_id", "module_id"],
                unique=True,
            )

    if not _table_exists(bind, "licensing_plan_modules"):
        op.create_table(
            "licensing_plan_modules",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "plan_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("licensing_service_plans.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column(
                "module_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("licensing_feature_modules.id"),
                nullable=False,
                index=True,
            ),
            sa.Column("included_by_default", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("is_optional_addon", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("override_price", sa.Numeric(15, 2), nullable=True),
            sa.Column("override_pricing_model", pricing_model_enum, nullable=True),
            sa.Column("config_override", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("trial_only", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("promotional_until", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index(
            "ix_plan_modules_plan_module",
            "licensing_plan_modules",
            ["plan_id", "module_id"],
            unique=True,
        )

    if _table_exists(bind, "licensing_plan_quota_allocations"):
        columns = _get_columns(bind, "licensing_plan_quota_allocations")
        with op.batch_alter_table("licensing_plan_quota_allocations") as batch_op:
            if "included_quantity" not in columns:
                batch_op.add_column(sa.Column("included_quantity", sa.Integer(), nullable=False, server_default="0"))
            if "soft_limit" not in columns:
                batch_op.add_column(sa.Column("soft_limit", sa.Integer(), nullable=True))
            if "allow_overage" not in columns:
                batch_op.add_column(sa.Column("allow_overage", sa.Boolean(), nullable=False, server_default="false"))
            if "overage_rate_override" not in columns:
                batch_op.add_column(sa.Column("overage_rate_override", sa.Numeric(15, 4), nullable=True))
            if "pricing_tiers" not in columns:
                batch_op.add_column(sa.Column("pricing_tiers", postgresql.JSON(), nullable=False, server_default="[]"))
            if "config_data" not in columns:
                batch_op.add_column(sa.Column("config_data", postgresql.JSON(), nullable=False, server_default="{}"))
        if "allocated_quantity" in columns:
            op.execute(
                "UPDATE licensing_plan_quota_allocations SET included_quantity = COALESCE(included_quantity, allocated_quantity)"
            )
        if "overage_allowed" in columns:
            op.execute(
                "UPDATE licensing_plan_quota_allocations SET allow_overage = COALESCE(allow_overage, overage_allowed)"
            )
        if "overage_rate" in columns:
            op.execute(
                "UPDATE licensing_plan_quota_allocations SET overage_rate_override = COALESCE(overage_rate_override, overage_rate)"
            )
        if "config" in columns:
            op.execute(
                "UPDATE licensing_plan_quota_allocations SET config_data = COALESCE(config_data, config)"
            )
        op.execute(
            "UPDATE licensing_plan_quota_allocations SET pricing_tiers = COALESCE(pricing_tiers, '[]'::json)"
        )
        op.execute(
            "UPDATE licensing_plan_quota_allocations SET config_data = COALESCE(config_data, '{}'::json)"
        )
        if not _has_index(bind, "licensing_plan_quota_allocations", "ix_plan_quotas_plan_quota"):
            op.create_index(
                "ix_plan_quotas_plan_quota",
                "licensing_plan_quota_allocations",
                ["plan_id", "quota_id"],
                unique=True,
            )

    if not _table_exists(bind, "licensing_plan_quota_allocations"):
        op.create_table(
            "licensing_plan_quota_allocations",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "plan_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("licensing_service_plans.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column(
                "quota_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("licensing_quota_definitions.id"),
                nullable=False,
                index=True,
            ),
            sa.Column("included_quantity", sa.Integer(), nullable=False),
            sa.Column("soft_limit", sa.Integer(), nullable=True),
            sa.Column("allow_overage", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("overage_rate_override", sa.Numeric(15, 4), nullable=True),
            sa.Column("pricing_tiers", postgresql.JSON(), nullable=False, server_default="[]"),
            sa.Column("config_data", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index(
            "ix_plan_quotas_plan_quota",
            "licensing_plan_quota_allocations",
            ["plan_id", "quota_id"],
            unique=True,
        )

    if not _table_exists(bind, "licensing_subscription_quota_usage"):
        op.create_table(
            "licensing_subscription_quota_usage",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "subscription_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("licensing_tenant_subscriptions.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column(
                "quota_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("licensing_quota_definitions.id"),
                nullable=False,
                index=True,
            ),
            sa.Column("allocated_quantity", sa.Integer(), nullable=False),
            sa.Column("current_usage", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("period_start", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("overage_quantity", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("overage_charges", sa.Numeric(15, 2), nullable=False, server_default="0"),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index(
            "ix_subscription_quota_usage_subscription_quota",
            "licensing_subscription_quota_usage",
            ["subscription_id", "quota_id"],
            unique=True,
        )
    if _table_exists(bind, "licensing_subscription_quota_usage"):
        if not _has_index(bind, "licensing_subscription_quota_usage", "ix_subscription_quota_usage_subscription_quota"):
            op.create_index(
                "ix_subscription_quota_usage_subscription_quota",
                "licensing_subscription_quota_usage",
                ["subscription_id", "quota_id"],
                unique=True,
            )

    if not _table_exists(bind, "licensing_feature_usage_logs"):
        op.create_table(
            "licensing_feature_usage_logs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(255), nullable=False, index=True),
            sa.Column("module_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("capability_code", sa.String(100), nullable=True, index=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
            sa.Column("action", sa.String(50), nullable=False),
            sa.Column("resource_type", sa.String(100), nullable=True),
            sa.Column("resource_id", sa.String(100), nullable=True),
            sa.Column("extra_metadata", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, index=True),
        )
        op.create_index("ix_feature_usage_tenant_module", "licensing_feature_usage_logs", ["tenant_id", "module_id"])
        op.create_index("ix_feature_usage_tenant_date", "licensing_feature_usage_logs", ["tenant_id", "created_at"])

    if not _table_exists(bind, "licensing_subscription_events"):
        op.create_table(
            "licensing_subscription_events",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "subscription_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("licensing_tenant_subscriptions.id"),
                nullable=False,
                index=True,
            ),
            sa.Column("event_type", sa.String(50), nullable=False, index=True),
            sa.Column("previous_plan_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("new_plan_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("previous_status", sa.String(20), nullable=True),
            sa.Column("new_status", sa.String(20), nullable=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("ip_address", sa.String(50), nullable=True),
            sa.Column("event_data", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index(
            "ix_subscription_events_subscription_type",
            "licensing_subscription_events",
            ["subscription_id", "event_type"],
        )

    if _table_exists(bind, "licensing_subscription_events"):
        columns = _get_columns(bind, "licensing_subscription_events")
        with op.batch_alter_table("licensing_subscription_events") as batch_op:
            if "previous_plan_id" not in columns:
                batch_op.add_column(sa.Column("previous_plan_id", postgresql.UUID(as_uuid=True), nullable=True))
            if "new_plan_id" not in columns:
                batch_op.add_column(sa.Column("new_plan_id", postgresql.UUID(as_uuid=True), nullable=True))
            if "previous_status" not in columns:
                batch_op.add_column(sa.Column("previous_status", sa.String(20), nullable=True))
            if "new_status" not in columns:
                batch_op.add_column(sa.Column("new_status", sa.String(20), nullable=True))
            if "user_id" not in columns:
                batch_op.add_column(sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True))
            if "ip_address" not in columns:
                batch_op.add_column(sa.Column("ip_address", sa.String(50), nullable=True))
            if "event_data" not in columns:
                batch_op.add_column(sa.Column("event_data", postgresql.JSON(), nullable=False, server_default="{}"))
            if "created_at" not in columns:
                batch_op.add_column(sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
        if not _has_index(bind, "licensing_subscription_events", "ix_subscription_events_subscription_type"):
            op.create_index(
                "ix_subscription_events_subscription_type",
                "licensing_subscription_events",
                ["subscription_id", "event_type"],
            )


def downgrade() -> None:
    op.execute("SELECT 1")
