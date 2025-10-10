"""Create billing module tables

Revision ID: billing_001
Revises: 9d6a492bf126
Create Date: 2025-09-24 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "billing_001"
down_revision: str | None = "9d6a492bf126"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create billing module tables"""

    # Create invoices table
    op.create_table(
        "invoices",
        sa.Column("invoice_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("invoice_number", sa.String(50), nullable=True),
        sa.Column("tenant_id", sa.String(255), nullable=True),
        sa.Column("idempotency_key", sa.String(255), nullable=True),
        sa.Column("customer_id", sa.String(255), nullable=False),
        sa.Column("billing_email", sa.String(255), nullable=False),
        sa.Column("billing_address", sa.JSON(), nullable=False),
        sa.Column("issue_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("subtotal", sa.Integer(), nullable=False),
        sa.Column("tax_amount", sa.Integer(), nullable=False, default=0),
        sa.Column("discount_amount", sa.Integer(), nullable=False, default=0),
        sa.Column("total_amount", sa.Integer(), nullable=False),
        sa.Column("total_credits_applied", sa.Integer(), nullable=False, default=0),
        sa.Column("remaining_balance", sa.Integer(), nullable=False),
        sa.Column("credit_applications", sa.JSON(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT", "OPEN", "PAID", "VOID", "OVERDUE", "PARTIALLY_PAID", name="invoicestatus"
            ),
            nullable=False,
        ),
        sa.Column(
            "payment_status",
            sa.Enum(
                "PENDING",
                "PROCESSING",
                "SUCCEEDED",
                "FAILED",
                "REFUNDED",
                "PARTIALLY_REFUNDED",
                "CANCELLED",
                name="paymentstatus",
            ),
            nullable=False,
        ),
        sa.Column("subscription_id", sa.String(255), nullable=True),
        sa.Column("proforma_invoice_id", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("invoice_id"),
    )
    op.create_index("idx_invoice_tenant_customer", "invoices", ["tenant_id", "customer_id"])
    op.create_index("idx_invoice_tenant_status", "invoices", ["tenant_id", "status"])
    op.create_index("idx_invoice_tenant_due_date", "invoices", ["tenant_id", "due_date"])
    op.create_unique_constraint(
        "uq_invoice_idempotency", "invoices", ["tenant_id", "idempotency_key"]
    )
    op.create_unique_constraint("uq_invoice_number", "invoices", ["invoice_number"])

    # Create invoice line items table
    op.create_table(
        "invoice_line_items",
        sa.Column("line_item_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Integer(), nullable=False),
        sa.Column("total_price", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.String(255), nullable=True),
        sa.Column("subscription_id", sa.String(255), nullable=True),
        sa.Column("tax_rate", sa.Float(), nullable=False, default=0.0),
        sa.Column("tax_amount", sa.Integer(), nullable=False, default=0),
        sa.Column("discount_percentage", sa.Float(), nullable=False, default=0.0),
        sa.Column("discount_amount", sa.Integer(), nullable=False, default=0),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.invoice_id"]),
        sa.PrimaryKeyConstraint("line_item_id"),
    )

    # Create payments table
    op.create_table(
        "payments",
        sa.Column("payment_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", sa.String(255), nullable=True),
        sa.Column("idempotency_key", sa.String(255), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("customer_id", sa.String(255), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "PROCESSING",
                "SUCCEEDED",
                "FAILED",
                "REFUNDED",
                "PARTIALLY_REFUNDED",
                "CANCELLED",
                name="paymentstatus",
            ),
            nullable=False,
        ),
        sa.Column(
            "payment_method_type",
            sa.Enum(
                "CARD",
                "BANK_ACCOUNT",
                "DIGITAL_WALLET",
                "CRYPTO",
                "CHECK",
                "WIRE_TRANSFER",
                "CASH",
                name="paymentmethodtype",
            ),
            nullable=False,
        ),
        sa.Column("payment_method_details", sa.JSON(), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("provider_payment_id", sa.String(255), nullable=True),
        sa.Column("provider_fee", sa.Integer(), nullable=True),
        sa.Column("failure_reason", sa.String(500), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, default=0),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("payment_id"),
    )
    op.create_index("idx_payment_tenant_customer", "payments", ["tenant_id", "customer_id"])
    op.create_index("idx_payment_tenant_status", "payments", ["tenant_id", "status"])
    op.create_unique_constraint(
        "uq_payment_idempotency", "payments", ["tenant_id", "idempotency_key"]
    )

    # Create payment_invoices association table
    op.create_table(
        "payment_invoices",
        sa.Column("payment_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("amount_applied", sa.Integer(), nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.payment_id"]),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.invoice_id"]),
        sa.PrimaryKeyConstraint("payment_id", "invoice_id"),
    )

    # Create payment methods table
    op.create_table(
        "payment_methods",
        sa.Column("payment_method_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", sa.String(255), nullable=True),
        sa.Column("customer_id", sa.String(255), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "CARD",
                "BANK_ACCOUNT",
                "DIGITAL_WALLET",
                "CRYPTO",
                "CHECK",
                "WIRE_TRANSFER",
                "CASH",
                name="paymentmethodtype",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "ACTIVE",
                "INACTIVE",
                "EXPIRED",
                "REQUIRES_VERIFICATION",
                "VERIFICATION_FAILED",
                name="paymentmethodstatus",
            ),
            nullable=False,
        ),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("provider_payment_method_id", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("last_four", sa.String(4), nullable=True),
        sa.Column("brand", sa.String(50), nullable=True),
        sa.Column("expiry_month", sa.Integer(), nullable=True),
        sa.Column("expiry_year", sa.Integer(), nullable=True),
        sa.Column("bank_name", sa.String(100), nullable=True),
        sa.Column(
            "account_type",
            sa.Enum(
                "CHECKING",
                "SAVINGS",
                "BUSINESS_CHECKING",
                "BUSINESS_SAVINGS",
                name="bankaccounttype",
            ),
            nullable=True,
        ),
        sa.Column("routing_number_last_four", sa.String(4), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, default=False),
        sa.Column("auto_pay_enabled", sa.Boolean(), nullable=False, default=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("payment_method_id"),
    )
    op.create_index(
        "idx_payment_method_tenant_customer", "payment_methods", ["tenant_id", "customer_id"]
    )

    # Create transactions table
    op.create_table(
        "transactions",
        sa.Column("transaction_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", sa.String(255), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column(
            "transaction_type",
            sa.Enum(
                "CHARGE",
                "PAYMENT",
                "REFUND",
                "CREDIT",
                "ADJUSTMENT",
                "FEE",
                "WRITE_OFF",
                name="transactiontype",
            ),
            nullable=False,
        ),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("customer_id", sa.String(255), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("payment_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("credit_note_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("transaction_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("transaction_id"),
    )
    op.create_index("idx_transaction_tenant_customer", "transactions", ["tenant_id", "customer_id"])
    op.create_index(
        "idx_transaction_tenant_date", "transactions", ["tenant_id", "transaction_date"]
    )

    # Create credit notes table
    op.create_table(
        "credit_notes",
        sa.Column("credit_note_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("credit_note_number", sa.String(50), nullable=True),
        sa.Column("tenant_id", sa.String(255), nullable=True),
        sa.Column("idempotency_key", sa.String(255), nullable=True),
        sa.Column("customer_id", sa.String(255), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("issue_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("subtotal", sa.Integer(), nullable=False),
        sa.Column("tax_amount", sa.Integer(), nullable=False, default=0),
        sa.Column("total_amount", sa.Integer(), nullable=False),
        sa.Column(
            "credit_type",
            sa.Enum(
                "REFUND",
                "ADJUSTMENT",
                "WRITE_OFF",
                "DISCOUNT",
                "ERROR_CORRECTION",
                "OVERPAYMENT",
                "GOODWILL",
                name="credittype",
            ),
            nullable=False,
        ),
        sa.Column(
            "reason",
            sa.Enum(
                "CUSTOMER_REQUEST",
                "BILLING_ERROR",
                "PRODUCT_DEFECT",
                "SERVICE_ISSUE",
                "DUPLICATE_CHARGE",
                "CANCELLATION",
                "GOODWILL",
                "OVERPAYMENT_REFUND",
                "PRICE_ADJUSTMENT",
                "TAX_ADJUSTMENT",
                "OTHER",
                name="creditreason",
            ),
            nullable=False,
        ),
        sa.Column("reason_description", sa.String(500), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT", "ISSUED", "APPLIED", "VOIDED", "PARTIALLY_APPLIED", name="creditnotestatus"
            ),
            nullable=False,
        ),
        sa.Column("auto_apply_to_invoice", sa.Boolean(), nullable=False, default=True),
        sa.Column("remaining_credit_amount", sa.Integer(), nullable=False, default=0),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("credit_note_id"),
    )
    op.create_index("idx_credit_note_tenant_customer", "credit_notes", ["tenant_id", "customer_id"])
    op.create_index("idx_credit_note_tenant_status", "credit_notes", ["tenant_id", "status"])
    op.create_unique_constraint(
        "uq_credit_note_idempotency", "credit_notes", ["tenant_id", "idempotency_key"]
    )
    op.create_unique_constraint("uq_credit_note_number", "credit_notes", ["credit_note_number"])

    # Create credit note line items table
    op.create_table(
        "credit_note_line_items",
        sa.Column("line_item_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("credit_note_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, default=1),
        sa.Column("unit_price", sa.Integer(), nullable=False),
        sa.Column("total_price", sa.Integer(), nullable=False),
        sa.Column("original_invoice_line_item_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("product_id", sa.String(255), nullable=True),
        sa.Column("tax_rate", sa.Float(), nullable=False, default=0.0),
        sa.Column("tax_amount", sa.Integer(), nullable=False, default=0),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["credit_note_id"], ["credit_notes.credit_note_id"]),
        sa.PrimaryKeyConstraint("line_item_id"),
    )

    # Create credit applications table
    op.create_table(
        "credit_applications",
        sa.Column("application_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("credit_note_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", sa.String(255), nullable=True),
        sa.Column(
            "applied_to_type",
            sa.Enum("INVOICE", "CUSTOMER_ACCOUNT", "REFUND", name="creditapplicationtype"),
            nullable=False,
        ),
        sa.Column("applied_to_id", sa.String(255), nullable=False),
        sa.Column("applied_amount", sa.Integer(), nullable=False),
        sa.Column("application_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("applied_by", sa.String(255), nullable=False),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["credit_note_id"], ["credit_notes.credit_note_id"]),
        sa.PrimaryKeyConstraint("application_id"),
    )
    op.create_index(
        "idx_credit_application_tenant_target",
        "credit_applications",
        ["tenant_id", "applied_to_id"],
    )

    # Create customer credits table
    op.create_table(
        "customer_credits",
        sa.Column("customer_id", sa.String(255), nullable=False),
        sa.Column("tenant_id", sa.String(255), nullable=False),
        sa.Column("total_credit_amount", sa.Integer(), nullable=False, default=0),
        sa.Column("currency", sa.String(3), nullable=False, default="USD"),
        sa.Column("credit_notes", sa.JSON(), nullable=True),
        sa.Column("auto_apply_to_new_invoices", sa.Boolean(), nullable=False, default=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("customer_id", "tenant_id"),
    )
    op.create_index("idx_customer_credit_tenant", "customer_credits", ["tenant_id", "customer_id"])


def downgrade() -> None:
    """Drop billing module tables"""

    # Drop tables in reverse order of creation
    op.drop_table("customer_credits")
    op.drop_table("credit_applications")
    op.drop_table("credit_note_line_items")
    op.drop_table("credit_notes")
    op.drop_table("transactions")
    op.drop_table("payment_methods")
    op.drop_table("payment_invoices")
    op.drop_table("payments")
    op.drop_table("invoice_line_items")
    op.drop_table("invoices")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS invoicestatus")
    op.execute("DROP TYPE IF EXISTS paymentstatus")
    op.execute("DROP TYPE IF EXISTS paymentmethodtype")
    op.execute("DROP TYPE IF EXISTS paymentmethodstatus")
    op.execute("DROP TYPE IF EXISTS bankaccounttype")
    op.execute("DROP TYPE IF EXISTS transactiontype")
    op.execute("DROP TYPE IF EXISTS credittype")
    op.execute("DROP TYPE IF EXISTS creditreason")
    op.execute("DROP TYPE IF EXISTS creditnotestatus")
    op.execute("DROP TYPE IF EXISTS creditapplicationtype")
