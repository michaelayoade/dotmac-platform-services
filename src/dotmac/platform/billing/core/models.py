"""
Billing module Pydantic models with tenant support
"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from pydantic import ConfigDict, Field, field_validator

from dotmac.platform.core.models import BaseModel

from .enums import (
    BankAccountType,
    BillingCycle,
    CreditApplicationType,
    CreditNoteStatus,
    CreditReason,
    CreditType,
    InvoiceStatus,
    PaymentMethodStatus,
    PaymentMethodType,
    PaymentStatus,
    TransactionType,
    VerificationStatus,
)


class BillingBaseModel(BaseModel):
    """Base model for all billing entities with tenant support"""

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        str_strip_whitespace=True,
        extra="forbid",
        use_enum_values=True,
    )

    tenant_id: str = Field(..., description="Tenant identifier for multi-tenant isolation")


# ============================================================================
# Invoice Models
# ============================================================================


class InvoiceLineItem(BaseModel):
    """Invoice line item"""

    line_item_id: str = Field(default_factory=lambda: str(uuid4()))
    description: str = Field(..., min_length=1, max_length=500)
    quantity: int = Field(ge=1)
    unit_price: int = Field(..., description="Unit price in minor currency units")
    total_price: int = Field(..., description="Total price (quantity * unit_price)")

    # Optional references
    product_id: str | None = Field(None, description="Reference to product/service")
    subscription_id: str | None = Field(None, description="Reference to subscription")

    # Tax
    tax_rate: float = Field(0.0, ge=0, le=100)
    tax_amount: int = Field(0, ge=0)

    # Discount
    discount_percentage: float = Field(0.0, ge=0, le=100)
    discount_amount: int = Field(0, ge=0)

    extra_data: dict[str, Any] = Field(default_factory=dict)

    @field_validator("total_price")
    @classmethod
    def validate_total_price(cls, v: int, info) -> int:
        if "quantity" in info.data and "unit_price" in info.data:
            expected = info.data["quantity"] * info.data["unit_price"]
            if v != expected:
                raise ValueError(f"Total price must equal quantity * unit_price ({expected})")
        return v


class Invoice(BillingBaseModel):
    """Core invoice model with idempotency support"""

    invoice_id: str = Field(default_factory=lambda: str(uuid4()))
    invoice_number: str | None = Field(None, description="Human-readable invoice number")

    # Idempotency
    idempotency_key: str | None = None
    created_by: str = Field(..., description="User/system that created invoice")

    # Customer
    customer_id: str = Field(..., description="Customer identifier")
    billing_email: str = Field(..., description="Billing email address")
    billing_address: dict[str, str] = Field(..., description="Billing address")

    # Invoice details
    issue_date: datetime = Field(default_factory=datetime.utcnow)
    due_date: datetime
    currency: str = Field("USD", min_length=3, max_length=3)

    # Amounts in minor units (cents)
    subtotal: int = Field(ge=0)
    tax_amount: int = Field(0, ge=0)
    discount_amount: int = Field(0, ge=0)
    total_amount: int = Field(ge=0)

    # Credits
    total_credits_applied: int = Field(0, ge=0)
    remaining_balance: int = Field(ge=0)
    credit_applications: list[str] = Field(default_factory=list)

    # Status
    status: InvoiceStatus = Field(InvoiceStatus.DRAFT)
    payment_status: PaymentStatus = Field(PaymentStatus.PENDING)

    # Line items
    line_items: list[InvoiceLineItem] = Field(min_length=1)

    # References
    subscription_id: str | None = None
    proforma_invoice_id: str | None = None

    # Metadata
    notes: str | None = Field(None, max_length=2000)
    internal_notes: str | None = Field(None, max_length=2000)
    extra_data: dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    paid_at: datetime | None = None
    voided_at: datetime | None = None

    @property
    def net_amount_due(self) -> int:
        """Calculate net amount due after payments and credits"""
        return max(0, self.total_amount - self.total_credits_applied)


# ============================================================================
# Payment Models
# ============================================================================


class Payment(BillingBaseModel):
    """Payment record with idempotency"""

    payment_id: str = Field(default_factory=lambda: str(uuid4()))

    # Idempotency
    idempotency_key: str | None = None

    # Payment details
    amount: int = Field(..., description="Amount in minor currency units")
    currency: str = Field("USD", min_length=3, max_length=3)
    customer_id: str

    # Status
    status: PaymentStatus = Field(PaymentStatus.PENDING)

    # Payment method
    payment_method_type: PaymentMethodType
    payment_method_details: dict[str, Any] = Field(default_factory=dict)

    # Provider info
    provider: str = Field(..., description="Payment provider (stripe, paypal, etc.)")
    provider_payment_id: str | None = None
    provider_fee: int | None = Field(None, ge=0)

    # Related entities
    invoice_ids: list[str] = Field(default_factory=list)

    # Failure handling
    failure_reason: str | None = Field(None, max_length=500)
    retry_count: int = Field(0, ge=0)
    next_retry_at: datetime | None = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: datetime | None = None

    extra_data: dict[str, Any] = Field(default_factory=dict)


class PaymentMethod(BillingBaseModel):
    """Customer payment method"""

    payment_method_id: str = Field(default_factory=lambda: str(uuid4()))
    customer_id: str

    # Payment method details
    type: PaymentMethodType
    status: PaymentMethodStatus = Field(PaymentMethodStatus.ACTIVE)

    # Provider info
    provider: str
    provider_payment_method_id: str

    # Display info (no sensitive data)
    display_name: str = Field(..., max_length=100)
    last_four: str | None = Field(None, min_length=4, max_length=4)
    brand: str | None = Field(None, max_length=50)
    expiry_month: int | None = Field(None, ge=1, le=12)
    expiry_year: int | None = Field(None, ge=2024, le=2099)

    # Bank account specific
    bank_name: str | None = Field(None, max_length=100)
    account_type: BankAccountType | None = None
    routing_number_last_four: str | None = Field(None, min_length=4, max_length=4)

    # Settings
    is_default: bool = Field(False)
    auto_pay_enabled: bool = Field(False)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    verified_at: datetime | None = None

    extra_data: dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Transaction Models
# ============================================================================


class Transaction(BillingBaseModel):
    """Financial transaction ledger entry"""

    transaction_id: str = Field(default_factory=lambda: str(uuid4()))

    # Transaction details
    amount: int = Field(..., description="Amount in minor currency units")
    currency: str = Field("USD", min_length=3, max_length=3)
    transaction_type: TransactionType
    description: str = Field(..., max_length=500)

    # References
    customer_id: str
    invoice_id: str | None = None
    payment_id: str | None = None
    credit_note_id: str | None = None

    # Timestamp
    transaction_date: datetime = Field(default_factory=datetime.utcnow)

    extra_data: dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Credit Note Models
# ============================================================================


class CreditNoteLineItem(BaseModel):
    """Credit note line item"""

    line_item_id: str = Field(default_factory=lambda: str(uuid4()))
    description: str = Field(..., min_length=1, max_length=500)
    quantity: int = Field(1, ge=1)
    unit_price: int = Field(..., description="Unit price (negative for credit)")
    total_price: int = Field(..., description="Total price (quantity * unit_price)")

    # References to original invoice line item
    original_invoice_line_item_id: str | None = None

    # Tax
    tax_rate: float = Field(0.0, ge=0, le=100)
    tax_amount: int = Field(0)

    # Product reference
    product_id: str | None = None

    extra_data: dict[str, Any] = Field(default_factory=dict)


class CreditNote(BillingBaseModel):
    """Credit note for refunds, adjustments, and corrections"""

    credit_note_id: str = Field(default_factory=lambda: str(uuid4()))
    credit_note_number: str | None = Field(None, description="Human-readable credit note number")

    # Idempotency
    idempotency_key: str | None = None
    created_by: str

    # Customer and reference
    customer_id: str
    invoice_id: str | None = Field(None, description="Original invoice if applicable")

    # Credit note details
    issue_date: datetime = Field(default_factory=datetime.utcnow)
    currency: str = Field("USD", min_length=3, max_length=3)

    # Amounts in minor units (cents)
    subtotal: int
    tax_amount: int = Field(0)
    total_amount: int

    # Credit note type and reason
    credit_type: CreditType
    reason: CreditReason
    reason_description: str | None = Field(None, max_length=500)

    # Status
    status: CreditNoteStatus = Field(CreditNoteStatus.DRAFT)

    # Line items
    line_items: list[CreditNoteLineItem] = Field(min_length=1)

    # Application
    auto_apply_to_invoice: bool = Field(True)
    remaining_credit_amount: int = Field(0, ge=0)

    # Metadata
    notes: str | None = Field(None, max_length=2000)
    internal_notes: str | None = Field(None, max_length=2000)
    extra_data: dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    voided_at: datetime | None = None


class CreditApplication(BillingBaseModel):
    """Credit note application to invoices or customer account"""

    application_id: str = Field(default_factory=lambda: str(uuid4()))
    credit_note_id: str

    # Application target
    applied_to_type: CreditApplicationType
    applied_to_id: str = Field(..., description="Invoice ID or customer account ID")

    # Application details
    applied_amount: int = Field(..., gt=0, description="Amount applied in minor currency units")
    application_date: datetime = Field(default_factory=datetime.utcnow)

    # Reference
    applied_by: str
    notes: str | None = Field(None, max_length=500)

    extra_data: dict[str, Any] = Field(default_factory=dict)


class CustomerCredit(BillingBaseModel):
    """Customer account credit balance"""

    customer_id: str

    # Credit balance
    total_credit_amount: int = Field(0, ge=0, description="Available credit balance")
    currency: str = Field("USD", min_length=3, max_length=3)

    # Credit sources
    credit_notes: list[str] = Field(default_factory=list, description="Credit note IDs")

    # Auto-apply settings
    auto_apply_to_new_invoices: bool = Field(True)

    # Timestamps
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    extra_data: dict[str, Any] = Field(default_factory=dict)