"""Create missing tables aligned with SQLAlchemy models.

Revision ID: create_missing_tables
Revises: fix_billing_licensing_tables
Create Date: 2025-12-26 22:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "create_missing_tables"
down_revision: str | None = "fix_billing_licensing_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _ensure_enum(bind: sa.engine.Connection, enum: postgresql.ENUM) -> None:
    result = bind.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = :name"), {"name": enum.name})
    if not result.fetchone():
        enum.create(bind, checkfirst=True)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # =====================================================================
    # Enum types
    # =====================================================================

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
    ]
    for enum in enums:
        _ensure_enum(bind, enum)

    # =====================================================================
    # Billing Core
    # =====================================================================

    if "invoices" not in existing_tables:
        op.create_table(
            "invoices",
            sa.Column("invoice_id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "tenant_id",
                sa.String(255),
                sa.ForeignKey("tenants.id"),
                nullable=True,
                index=True,
            ),
            sa.Column("invoice_number", sa.String(50), nullable=True, index=True),
            sa.Column("idempotency_key", sa.String(255), nullable=True, index=True),
            sa.Column("customer_id", sa.String(255), nullable=False, index=True),
            sa.Column("billing_email", sa.String(255), nullable=False),
            sa.Column("billing_address", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("issue_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("due_date", sa.DateTime(timezone=True), nullable=False, index=True),
            sa.Column("currency", sa.String(3), nullable=False),
            sa.Column("subtotal", sa.Integer(), nullable=False),
            sa.Column("tax_amount", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("discount_amount", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_amount", sa.Integer(), nullable=False),
            sa.Column("total_credits_applied", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("remaining_balance", sa.Integer(), nullable=False),
            sa.Column("credit_applications", postgresql.JSON(), nullable=False, server_default="[]"),
            sa.Column("status", invoice_status_enum, nullable=False, server_default="draft", index=True),
            sa.Column(
                "payment_status",
                payment_status_enum,
                nullable=False,
                server_default="pending",
                index=True,
            ),
            sa.Column("subscription_id", sa.String(255), nullable=True, index=True),
            sa.Column("proforma_invoice_id", sa.String(255), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("internal_notes", sa.Text(), nullable=True),
            sa.Column("extra_data", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("created_by", sa.String(255), nullable=True),
            sa.Column("updated_by", sa.String(255), nullable=True),
            sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_invoice_idempotency"),
            sa.UniqueConstraint("tenant_id", "invoice_number", name="uq_invoice_number_by_tenant"),
        )
        op.create_index("idx_invoice_tenant_customer", "invoices", ["tenant_id", "customer_id"])
        op.create_index("idx_invoice_tenant_status", "invoices", ["tenant_id", "status"])
        op.create_index("idx_invoice_tenant_due_date", "invoices", ["tenant_id", "due_date"])

    if "invoice_line_items" not in existing_tables:
        op.create_table(
            "invoice_line_items",
            sa.Column("line_item_id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "invoice_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("invoices.invoice_id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("description", sa.String(500), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("unit_price", sa.Integer(), nullable=False),
            sa.Column("total_price", sa.Integer(), nullable=False),
            sa.Column("product_id", sa.String(255), nullable=True),
            sa.Column("subscription_id", sa.String(255), nullable=True),
            sa.Column("tax_rate", sa.Float(), nullable=False, server_default="0"),
            sa.Column("tax_amount", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("discount_percentage", sa.Float(), nullable=False, server_default="0"),
            sa.Column("discount_amount", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("extra_data", postgresql.JSON(), nullable=False, server_default="{}"),
        )

    if "payments" not in existing_tables:
        op.create_table(
            "payments",
            sa.Column("payment_id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
            sa.Column("idempotency_key", sa.String(255), nullable=True, index=True),
            sa.Column("amount", sa.Integer(), nullable=False),
            sa.Column("currency", sa.String(3), nullable=False),
            sa.Column("customer_id", sa.String(255), nullable=False, index=True),
            sa.Column("status", payment_status_enum, nullable=False, server_default="pending", index=True),
            sa.Column("payment_method_type", payment_method_type_enum, nullable=False),
            sa.Column("payment_method_details", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("provider", sa.String(50), nullable=False),
            sa.Column("provider_payment_id", sa.String(255), nullable=True, index=True),
            sa.Column("provider_fee", sa.Integer(), nullable=True),
            sa.Column("provider_payment_data", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("failure_reason", sa.String(500), nullable=True),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("refund_amount", sa.Numeric(18, 2), nullable=True),
            sa.Column("extra_data", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_payment_idempotency"),
        )
        op.create_index("idx_payment_tenant_customer", "payments", ["tenant_id", "customer_id"])
        op.create_index("idx_payment_tenant_status", "payments", ["tenant_id", "status"])

    if "payment_invoices" not in existing_tables:
        op.create_table(
            "payment_invoices",
            sa.Column(
                "payment_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("payments.payment_id", ondelete="CASCADE"),
                primary_key=True,
            ),
            sa.Column(
                "invoice_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("invoices.invoice_id", ondelete="CASCADE"),
                primary_key=True,
            ),
            sa.Column("amount_applied", sa.Integer(), nullable=False),
            sa.Column(
                "applied_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )

    if "payment_methods" not in existing_tables:
        op.create_table(
            "payment_methods",
            sa.Column("payment_method_id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
            sa.Column("customer_id", sa.String(255), nullable=False, index=True),
            sa.Column("type", payment_method_type_enum, nullable=False),
            sa.Column("status", payment_method_status_enum, nullable=False, server_default="active"),
            sa.Column("provider", sa.String(50), nullable=False),
            sa.Column("provider_payment_method_id", sa.String(255), nullable=False),
            sa.Column("display_name", sa.String(100), nullable=False),
            sa.Column("last_four", sa.String(4), nullable=True),
            sa.Column("brand", sa.String(50), nullable=True),
            sa.Column("expiry_month", sa.Integer(), nullable=True),
            sa.Column("expiry_year", sa.Integer(), nullable=True),
            sa.Column("bank_name", sa.String(100), nullable=True),
            sa.Column("account_type", bank_account_type_enum, nullable=True),
            sa.Column("routing_number_last_four", sa.String(4), nullable=True),
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("auto_pay_enabled", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("extra_data", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        )
        op.create_index("idx_payment_method_tenant_customer", "payment_methods", ["tenant_id", "customer_id"])

    if "transactions" not in existing_tables:
        op.create_table(
            "transactions",
            sa.Column("transaction_id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
            sa.Column("amount", sa.Integer(), nullable=False),
            sa.Column("currency", sa.String(3), nullable=False),
            sa.Column("transaction_type", transaction_type_enum, nullable=False, index=True),
            sa.Column("description", sa.String(500), nullable=False),
            sa.Column("customer_id", sa.String(255), nullable=False, index=True),
            sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
            sa.Column("payment_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
            sa.Column("credit_note_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
            sa.Column(
                "transaction_date",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
                index=True,
            ),
            sa.Column("extra_data", postgresql.JSON(), nullable=False, server_default="{}"),
        )
        op.create_index("idx_transaction_tenant_customer", "transactions", ["tenant_id", "customer_id"])
        op.create_index("idx_transaction_tenant_date", "transactions", ["tenant_id", "transaction_date"])

    # =====================================================================
    # Contacts
    # =====================================================================

    if "contact_label_definitions" not in existing_tables:
        op.create_table(
            "contact_label_definitions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "tenant_id",
                sa.String(255),
                sa.ForeignKey("tenants.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("slug", sa.String(100), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("color", sa.String(7), nullable=True),
            sa.Column("icon", sa.String(50), nullable=True),
            sa.Column("category", sa.String(50), nullable=True),
            sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_visible", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("metadata", postgresql.JSON(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "created_by",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id"),
                nullable=True,
            ),
            sa.UniqueConstraint("tenant_id", "slug", name="uq_tenant_label_slug"),
        )
        op.create_index(
            "ix_contact_label_definitions_slug", "contact_label_definitions", ["slug"]
        )
        op.create_index(
            "ix_contact_label_definitions_category", "contact_label_definitions", ["category"]
        )

    if "contact_field_definitions" not in existing_tables:
        op.create_table(
            "contact_field_definitions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "tenant_id",
                sa.String(255),
                sa.ForeignKey("tenants.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("field_key", sa.String(100), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("field_type", sa.String(50), nullable=False),
            sa.Column("is_required", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("is_unique", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("is_searchable", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("default_value", postgresql.JSON(), nullable=True),
            sa.Column("validation_rules", postgresql.JSON(), nullable=True),
            sa.Column("options", postgresql.JSON(), nullable=True),
            sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("placeholder", sa.String(255), nullable=True),
            sa.Column("help_text", sa.Text(), nullable=True),
            sa.Column("field_group", sa.String(100), nullable=True),
            sa.Column("is_visible", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("is_editable", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("required_permission", sa.String(100), nullable=True),
            sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("is_encrypted", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("metadata", postgresql.JSON(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "created_by",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id"),
                nullable=True,
            ),
            sa.UniqueConstraint("tenant_id", "field_key", name="uq_tenant_field_key"),
        )
        op.create_index(
            "ix_contact_field_definitions_field_key", "contact_field_definitions", ["field_key"]
        )
        op.create_index(
            "ix_contact_field_definitions_field_group",
            "contact_field_definitions",
            ["field_group"],
        )

    # =====================================================================
    # Rate Limits
    # =====================================================================

    if "rate_limit_rules" not in existing_tables:
        op.create_table(
            "rate_limit_rules",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "tenant_id",
                sa.String(255),
                sa.ForeignKey("tenants.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("scope", ratelimit_scope_enum, nullable=False, index=True),
            sa.Column("endpoint_pattern", sa.String(500), nullable=True),
            sa.Column("max_requests", sa.Integer(), nullable=False),
            sa.Column("window", ratelimit_window_enum, nullable=False),
            sa.Column("window_seconds", sa.Integer(), nullable=False),
            sa.Column("action", ratelimit_action_enum, nullable=False, server_default="block"),
            sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("exempt_user_ids", postgresql.JSON(), nullable=False, server_default="[]"),
            sa.Column("exempt_ip_addresses", postgresql.JSON(), nullable=False, server_default="[]"),
            sa.Column("exempt_api_keys", postgresql.JSON(), nullable=False, server_default="[]"),
            sa.Column("config", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", sa.String(255), nullable=True),
            sa.Column("updated_by", sa.String(255), nullable=True),
        )

    if "rate_limit_logs" not in existing_tables:
        op.create_table(
            "rate_limit_logs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "tenant_id",
                sa.String(255),
                sa.ForeignKey("tenants.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column(
                "rule_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("rate_limit_rules.id", ondelete="SET NULL"),
                nullable=True,
                index=True,
            ),
            sa.Column("rule_name", sa.String(255), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
            sa.Column("ip_address", sa.String(45), nullable=True, index=True),
            sa.Column("api_key_id", sa.String(255), nullable=True, index=True),
            sa.Column("endpoint", sa.String(500), nullable=False, index=True),
            sa.Column("method", sa.String(10), nullable=False),
            sa.Column("current_count", sa.Integer(), nullable=False),
            sa.Column("limit", sa.Integer(), nullable=False),
            sa.Column("window", ratelimit_window_enum, nullable=False),
            sa.Column("action", ratelimit_action_enum, nullable=False),
            sa.Column("was_blocked", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("user_agent", sa.Text(), nullable=True),
            sa.Column("request_metadata", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # =====================================================================
    # Jobs
    # =====================================================================

    if "scheduled_jobs" not in existing_tables:
        op.create_table(
            "scheduled_jobs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(255), nullable=False, index=True),
            sa.Column("name", sa.String(255), nullable=False, index=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("job_type", sa.String(50), nullable=False),
            sa.Column("cron_expression", sa.String(100), nullable=True),
            sa.Column("interval_seconds", sa.Integer(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true", index=True),
            sa.Column("max_concurrent_runs", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("timeout_seconds", sa.Integer(), nullable=True),
            sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
            sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
            sa.Column("retry_delay_seconds", sa.Integer(), nullable=False, server_default="60"),
            sa.Column("parameters", postgresql.JSON(), nullable=True),
            sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True, index=True),
            sa.Column("total_runs", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("successful_runs", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("failed_runs", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_by", sa.String(255), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.CheckConstraint(
                "(cron_expression IS NOT NULL AND interval_seconds IS NULL) OR "
                "(cron_expression IS NULL AND interval_seconds IS NOT NULL)",
                name="check_schedule_type",
            ),
        )
        op.create_index("ix_scheduled_jobs_tenant_active", "scheduled_jobs", ["tenant_id", "is_active"])
        op.create_index("ix_scheduled_jobs_next_run", "scheduled_jobs", ["is_active", "next_run_at"])

    if "jobs" not in existing_tables:
        op.create_table(
            "jobs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(255), nullable=False, index=True),
            sa.Column("job_type", sa.String(50), nullable=False, index=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending", index=True),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("items_total", sa.Integer(), nullable=True),
            sa.Column("items_processed", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("items_succeeded", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("items_failed", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("current_item", sa.String(500), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("error_details", postgresql.JSON(), nullable=True),
            sa.Column("error_traceback", sa.Text(), nullable=True),
            sa.Column("failed_items", postgresql.JSON(), nullable=True),
            sa.Column("parameters", postgresql.JSON(), nullable=True),
            sa.Column("result", postgresql.JSON(), nullable=True),
            sa.Column("max_retries", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("retry_delay_seconds", sa.Integer(), nullable=True),
            sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
            sa.Column("timeout_seconds", sa.Integer(), nullable=True),
            sa.Column("assigned_technician_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("scheduled_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("actual_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("actual_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("location_lat", sa.Float(), nullable=True),
            sa.Column("location_lng", sa.Float(), nullable=True),
            sa.Column("service_address", sa.String(500), nullable=True),
            sa.Column("customer_signature", sa.Text(), nullable=True),
            sa.Column("completion_notes", sa.Text(), nullable=True),
            sa.Column("photos", postgresql.JSON(), nullable=True),
            sa.Column("parent_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id"), nullable=True),
            sa.Column(
                "scheduled_job_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("scheduled_jobs.id"),
                nullable=True,
            ),
            sa.Column("created_by", sa.String(255), nullable=False),
            sa.Column("cancelled_by", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        )

    # =====================================================================
    # Webhooks
    # =====================================================================

    if "webhook_subscriptions" not in existing_tables:
        op.create_table(
            "webhook_subscriptions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("url", sa.String(2048), nullable=False),
            sa.Column("secret", sa.String(255), nullable=True),
            sa.Column("event_types", postgresql.JSON(), nullable=False, server_default="[]"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("headers", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("retry_config", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_by", sa.String(255), nullable=True),
            sa.Column("updated_by", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_webhook_subscriptions_tenant", "webhook_subscriptions", ["tenant_id"])
        op.create_index("ix_webhook_subscriptions_active", "webhook_subscriptions", ["is_active"])

    if "webhook_deliveries" not in existing_tables:
        op.create_table(
            "webhook_deliveries",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "subscription_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
            sa.Column("event_type", sa.String(255), nullable=False, index=True),
            sa.Column("event_id", sa.String(255), nullable=False, index=True),
            sa.Column("event_data", postgresql.JSON(), nullable=False),
            sa.Column("status", sa.String(50), nullable=False, server_default="pending", index=True),
            sa.Column("response_code", sa.Integer(), nullable=True),
            sa.Column("response_body", sa.Text(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("duration_ms", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # =====================================================================
    # Communications
    # =====================================================================

    if "communication_logs" not in existing_tables:
        op.create_table(
            "communication_logs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
            sa.Column("type", communication_type_enum, nullable=False, index=True),
            sa.Column("recipient", sa.String(500), nullable=False, index=True),
            sa.Column("sender", sa.String(500), nullable=True),
            sa.Column("subject", sa.String(500), nullable=True),
            sa.Column("text_body", sa.Text(), nullable=True),
            sa.Column("html_body", sa.Text(), nullable=True),
            sa.Column("status", communication_status_enum, nullable=False, server_default="pending", index=True),
            sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("provider", sa.String(100), nullable=True),
            sa.Column("provider_message_id", sa.String(500), nullable=True),
            sa.Column("template_id", sa.String(255), nullable=True),
            sa.Column("template_name", sa.String(255), nullable=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
            sa.Column("job_id", sa.String(255), nullable=True, index=True),
            sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("headers", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    if "communication_stats" not in existing_tables:
        op.create_table(
            "communication_stats",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
            sa.Column("stats_date", sa.DateTime(timezone=True), nullable=False, index=True),
            sa.Column("type", communication_type_enum, nullable=False, index=True),
            sa.Column("total_sent", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_delivered", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_failed", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_bounced", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_pending", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("avg_delivery_time_seconds", sa.Float(), nullable=True),
            sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # =====================================================================
    # Workflows
    # =====================================================================

    if "workflows" not in existing_tables:
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

    if "workflow_executions" not in existing_tables:
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

    if "workflow_steps" not in existing_tables:
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
    # Monitoring
    # =====================================================================

    if "monitoring_alert_channels" not in existing_tables:
        op.create_table(
            "monitoring_alert_channels",
            sa.Column("id", sa.String(120), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("channel_type", sa.String(32), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
            sa.Column("config", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_by", sa.String(255), nullable=True),
            sa.Column("updated_by", sa.String(255), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # =====================================================================
    # Data Import / Transfer
    # =====================================================================

    if "data_import_jobs" not in existing_tables:
        op.create_table(
            "data_import_jobs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
            sa.Column("job_type", import_job_type_enum, nullable=False, index=True),
            sa.Column("status", import_job_status_enum, nullable=False, server_default="pending", index=True),
            sa.Column("file_name", sa.String(255), nullable=False),
            sa.Column("file_size", sa.Integer(), nullable=False),
            sa.Column("file_format", sa.String(20), nullable=False),
            sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("processed_records", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("successful_records", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("failed_records", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "initiated_by",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("config", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("summary", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("celery_task_id", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index("ix_import_jobs_tenant_status", "data_import_jobs", ["tenant_id", "status"])
        op.create_index("ix_import_jobs_tenant_type", "data_import_jobs", ["tenant_id", "job_type"])
        op.create_index("ix_import_jobs_created", "data_import_jobs", ["created_at"])

    if "data_import_failures" not in existing_tables:
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

    if "data_transfer_jobs" not in existing_tables:
        op.create_table(
            "data_transfer_jobs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("job_type", sa.String(50), nullable=False, index=True),
            sa.Column("status", sa.String(50), nullable=False, server_default="pending", index=True),
            sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("processed_records", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("failed_records", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("progress_percentage", sa.Float(), nullable=False, server_default="0"),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("celery_task_id", sa.String(255), nullable=True, index=True),
            sa.Column("import_source", sa.String(50), nullable=True),
            sa.Column("source_path", sa.String(1024), nullable=True),
            sa.Column("export_target", sa.String(50), nullable=True),
            sa.Column("target_path", sa.String(1024), nullable=True),
            sa.Column("config", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("summary", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # =====================================================================
    # Deployment
    # =====================================================================

    if "deployment_instances" not in existing_tables:
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

    if "deployment_executions" not in existing_tables:
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

    if "deployment_health" not in existing_tables:
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
    # Audit
    # =====================================================================

    if "audit_activities" not in existing_tables:
        op.create_table(
            "audit_activities",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
            sa.Column("activity_type", sa.String(100), nullable=False),
            sa.Column("severity", sa.String(20), nullable=False, server_default="low"),
            sa.Column("user_id", sa.String(255), nullable=True),
            sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, index=True),
            sa.Column("resource_type", sa.String(100), nullable=True),
            sa.Column("resource_id", sa.String(255), nullable=True),
            sa.Column("action", sa.String(100), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("details", postgresql.JSON(), nullable=True),
            sa.Column("ip_address", sa.String(45), nullable=True),
            sa.Column("user_agent", sa.String(500), nullable=True),
            sa.Column("request_id", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index("ix_audit_activities_user_timestamp", "audit_activities", ["user_id", "timestamp"])
        op.create_index("ix_audit_activities_tenant_timestamp", "audit_activities", ["tenant_id", "timestamp"])
        op.create_index("ix_audit_activities_type_timestamp", "audit_activities", ["activity_type", "timestamp"])
        op.create_index("ix_audit_activities_severity_timestamp", "audit_activities", ["severity", "timestamp"])

    # =====================================================================
    # Teams
    # =====================================================================

    if "team_members" not in existing_tables:
        op.create_table(
            "team_members",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(255), nullable=False, index=True),
            sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column("role", sa.String(50), nullable=False, server_default="member", index=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("metadata", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.UniqueConstraint("tenant_id", "team_id", "user_id", name="uq_team_members_tenant_team_user"),
        )

    # =====================================================================
    # Agent Availability
    # =====================================================================

    if "agent_availability" not in existing_tables:
        op.create_table(
            "agent_availability",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
            sa.Column("tenant_id", sa.String(100), nullable=True, index=True),
            sa.Column("status", agent_status_enum, nullable=False, server_default="available", index=True),
            sa.Column("status_message", sa.Text(), nullable=True),
            sa.Column("last_activity_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # =====================================================================
    # Licensing Framework
    # =====================================================================

    if "licensing_module_capabilities" not in existing_tables:
        op.create_table(
            "licensing_module_capabilities",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "module_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("licensing_feature_modules.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column("capability_code", sa.String(100), nullable=False, index=True),
            sa.Column("capability_name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("api_endpoints", postgresql.JSON(), nullable=False, server_default="[]"),
            sa.Column("ui_routes", postgresql.JSON(), nullable=False, server_default="[]"),
            sa.Column("permissions", postgresql.JSON(), nullable=False, server_default="[]"),
            sa.Column("config", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.UniqueConstraint("module_id", "capability_code", name="ix_module_capabilities_module_capability"),
        )

    if "licensing_tenant_subscriptions" not in existing_tables:
        op.create_table(
            "licensing_tenant_subscriptions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("tenant_id", sa.String(255), nullable=False, unique=True, index=True),
            sa.Column(
                "plan_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("licensing_service_plans.id"),
                nullable=False,
                index=True,
            ),
            sa.Column("status", subscription_status_enum, nullable=False, server_default="trial", index=True),
            sa.Column("billing_cycle", billing_cycle_enum, nullable=False, server_default="monthly"),
            sa.Column("monthly_price", sa.Numeric(15, 2), nullable=False),
            sa.Column("annual_price", sa.Numeric(15, 2), nullable=True),
            sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
            sa.Column("trial_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("billing_email", sa.String(255), nullable=True),
            sa.Column("payment_method_id", sa.String(100), nullable=True),
            sa.Column("stripe_subscription_id", sa.String(100), nullable=True, index=True),
            sa.Column("paypal_subscription_id", sa.String(100), nullable=True, index=True),
            sa.Column("extra_metadata", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index(
            "ix_tenant_subscriptions_tenant_status",
            "licensing_tenant_subscriptions",
            ["tenant_id", "status"],
        )
        op.create_index(
            "ix_tenant_subscriptions_plan_status",
            "licensing_tenant_subscriptions",
            ["plan_id", "status"],
        )

    if "licensing_subscription_modules" not in existing_tables:
        op.create_table(
            "licensing_subscription_modules",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "subscription_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("licensing_tenant_subscriptions.id", ondelete="CASCADE"),
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
            sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("source", sa.String(20), nullable=False),
            sa.Column("addon_price", sa.Numeric(15, 2), nullable=True),
            sa.Column("trial_only", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("config", postgresql.JSON(), nullable=False, server_default="{}"),
            sa.Column("activated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint(
                "subscription_id",
                "module_id",
                name="ix_subscription_modules_subscription_module",
            ),
        )


def downgrade() -> None:
    tables = [
        "licensing_subscription_modules",
        "licensing_tenant_subscriptions",
        "licensing_module_capabilities",
        "agent_availability",
        "team_members",
        "audit_activities",
        "deployment_health",
        "deployment_executions",
        "deployment_instances",
        "data_transfer_jobs",
        "data_import_failures",
        "data_import_jobs",
        "monitoring_alert_channels",
        "workflow_steps",
        "workflow_executions",
        "workflows",
        "communication_stats",
        "communication_logs",
        "webhook_deliveries",
        "webhook_subscriptions",
        "scheduled_jobs",
        "jobs",
        "rate_limit_logs",
        "rate_limit_rules",
        "contact_field_definitions",
        "contact_label_definitions",
        "transactions",
        "payment_methods",
        "payment_invoices",
        "payments",
        "invoice_line_items",
        "invoices",
    ]
    for table in tables:
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')

    enums = [
        "importjobstatus",
        "importjobtype",
        "billingcycle",
        "subscriptionstatus",
        "agentstatus",
        "deploymentstate",
        "workflowstepstatus",
        "workflowstatus",
        "communicationstatus",
        "communicationtype",
        "ratelimitaction",
        "ratelimitwindow",
        "ratelimitscope",
        "bankaccounttype",
        "transactiontype",
        "paymentmethodstatus",
        "paymentmethodtype",
        "paymentstatus",
        "invoicestatus",
    ]
    for enum_name in enums:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
