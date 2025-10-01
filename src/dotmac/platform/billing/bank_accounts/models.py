"""
Bank account and manual payment models
"""

from datetime import datetime
from typing import Any, Optional, List
from enum import Enum

from pydantic import BaseModel, Field, field_validator, ConfigDict

from dotmac.platform.billing.core.models import BillingBaseModel


class BankAccountStatus(str, Enum):
    """Bank account verification status"""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    SUSPENDED = "suspended"


class AccountType(str, Enum):
    """Bank account types"""
    CHECKING = "checking"
    SAVINGS = "savings"
    BUSINESS = "business"
    MONEY_MARKET = "money_market"


class PaymentMethodType(str, Enum):
    """Payment method types for manual entries"""
    BANK_TRANSFER = "bank_transfer"
    WIRE_TRANSFER = "wire_transfer"
    ACH = "ach"
    CASH = "cash"
    CHECK = "check"
    MONEY_ORDER = "money_order"
    MOBILE_MONEY = "mobile_money"
    CRYPTO = "crypto"
    OTHER = "other"


class CompanyBankAccountBase(BaseModel):
    """Base model for company bank account"""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    account_name: str = Field(..., min_length=1, max_length=200, description="Account holder name")
    account_nickname: Optional[str] = Field(None, max_length=100, description="User-friendly name")

    bank_name: str = Field(..., min_length=1, max_length=200, description="Bank name")
    bank_address: Optional[str] = Field(None, description="Bank address")
    bank_country: str = Field(..., min_length=2, max_length=2, description="ISO country code")

    account_type: AccountType = Field(AccountType.BUSINESS, description="Account type")
    currency: str = Field("USD", min_length=3, max_length=3, description="Currency code")

    routing_number: Optional[str] = Field(None, max_length=50, description="ABA routing number")
    swift_code: Optional[str] = Field(None, max_length=11, description="SWIFT/BIC code")
    iban: Optional[str] = Field(None, max_length=34, description="IBAN")

    is_primary: bool = Field(False, description="Primary account for payouts")
    accepts_deposits: bool = Field(True, description="Can receive deposits")
    notes: Optional[str] = Field(None, description="Internal notes")

    @field_validator("bank_country")
    @classmethod
    def validate_country(cls, v: str) -> str:
        """Validate country code"""
        if v and len(v) != 2:
            raise ValueError("Country must be 2-letter ISO code")
        return v.upper()

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code"""
        return v.upper()


class CompanyBankAccountCreate(CompanyBankAccountBase):
    """Create company bank account request"""
    account_number: str = Field(..., min_length=4, description="Full account number")

    @field_validator("account_number")
    @classmethod
    def validate_account_number(cls, v: str) -> str:
        """Basic account number validation"""
        # Remove spaces and dashes
        cleaned = v.replace(" ", "").replace("-", "")
        if not cleaned.isdigit() and not cleaned.isalnum():
            raise ValueError("Account number contains invalid characters")
        return v


class CompanyBankAccountUpdate(BaseModel):
    """Update company bank account request"""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    account_nickname: Optional[str] = Field(None, max_length=100)
    bank_address: Optional[str] = None
    is_primary: Optional[bool] = None
    accepts_deposits: Optional[bool] = None
    notes: Optional[str] = None


class CompanyBankAccountResponse(BillingBaseModel):
    """Company bank account response"""
    id: int
    account_name: str
    account_nickname: Optional[str]

    bank_name: str
    bank_address: Optional[str]
    bank_country: str

    account_number_last_four: str
    account_type: AccountType
    currency: str

    routing_number: Optional[str]
    swift_code: Optional[str]
    iban: Optional[str]

    status: BankAccountStatus
    is_primary: bool
    is_active: bool
    accepts_deposits: bool

    verified_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    notes: Optional[str]
    metadata: dict[str, Any] = Field(default_factory=dict)


class ManualPaymentBase(BaseModel):
    """Base model for manual payment"""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    customer_id: str = Field(..., description="Customer ID")
    invoice_id: Optional[str] = Field(None, description="Related invoice ID")
    bank_account_id: Optional[int] = Field(None, description="Deposit account")

    payment_method: PaymentMethodType = Field(..., description="Payment method")
    amount: float = Field(..., gt=0, description="Payment amount")
    currency: str = Field("USD", min_length=3, max_length=3)

    payment_date: datetime = Field(..., description="When payment was made")
    received_date: Optional[datetime] = Field(None, description="When payment was received")

    external_reference: Optional[str] = Field(None, max_length=255, description="External reference")
    notes: Optional[str] = Field(None, description="Payment notes")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        """Validate payment amount"""
        if v <= 0:
            raise ValueError("Amount must be positive")
        # Round to 2 decimal places
        return round(v, 2)


class CashPaymentCreate(ManualPaymentBase):
    """Create cash payment request"""
    payment_method: PaymentMethodType = Field(PaymentMethodType.CASH)
    cash_register_id: Optional[str] = Field(None, description="Register ID")
    cashier_name: Optional[str] = Field(None, max_length=100, description="Cashier name")


class CheckPaymentCreate(ManualPaymentBase):
    """Create check payment request"""
    payment_method: PaymentMethodType = Field(PaymentMethodType.CHECK)
    check_number: str = Field(..., max_length=50, description="Check number")
    check_bank_name: Optional[str] = Field(None, max_length=200, description="Bank name on check")


class BankTransferCreate(ManualPaymentBase):
    """Create bank transfer request"""
    payment_method: PaymentMethodType = Field(PaymentMethodType.BANK_TRANSFER)
    sender_name: Optional[str] = Field(None, max_length=200, description="Sender name")
    sender_bank: Optional[str] = Field(None, max_length=200, description="Sender bank")
    sender_account_last_four: Optional[str] = Field(None, max_length=4, description="Sender account last 4")


class MobileMoneyCreate(ManualPaymentBase):
    """Create mobile money payment request"""
    payment_method: PaymentMethodType = Field(PaymentMethodType.MOBILE_MONEY)
    mobile_number: str = Field(..., max_length=20, description="Mobile number")
    mobile_provider: str = Field(..., max_length=50, description="Provider (M-Pesa, etc.)")


class ManualPaymentResponse(BillingBaseModel):
    """Manual payment response"""
    id: int
    payment_reference: str
    external_reference: Optional[str]

    customer_id: str
    invoice_id: Optional[str]
    bank_account_id: Optional[int]

    payment_method: PaymentMethodType
    amount: float
    currency: str

    payment_date: datetime
    received_date: Optional[datetime]
    cleared_date: Optional[datetime]

    # Method-specific fields
    cash_register_id: Optional[str]
    cashier_name: Optional[str]
    check_number: Optional[str]
    check_bank_name: Optional[str]
    sender_name: Optional[str]
    sender_bank: Optional[str]
    sender_account_last_four: Optional[str]
    mobile_number: Optional[str]
    mobile_provider: Optional[str]

    status: str
    reconciled: bool
    reconciled_at: Optional[datetime]
    reconciled_by: Optional[str]

    notes: Optional[str]
    receipt_url: Optional[str]
    attachments: List[str] = Field(default_factory=list)

    recorded_by: str
    approved_by: Optional[str]
    approved_at: Optional[datetime]

    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReconcilePaymentRequest(BaseModel):
    """Request to reconcile a payment"""
    payment_ids: List[int] = Field(..., description="Payment IDs to reconcile")
    reconciliation_notes: Optional[str] = Field(None, description="Reconciliation notes")


class PaymentSearchFilters(BaseModel):
    """Filters for searching payments"""
    customer_id: Optional[str] = None
    invoice_id: Optional[str] = None
    payment_method: Optional[PaymentMethodType] = None
    status: Optional[str] = None
    reconciled: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None


class CashRegisterCreate(BaseModel):
    """Create cash register request"""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    register_id: str = Field(..., min_length=1, max_length=50, description="Unique register ID")
    register_name: str = Field(..., min_length=1, max_length=100, description="Register name")
    location: Optional[str] = Field(None, max_length=200, description="Physical location")
    initial_float: float = Field(0.00, ge=0, description="Initial float amount")
    requires_daily_reconciliation: bool = Field(True, description="Requires daily reconciliation")
    max_cash_limit: Optional[float] = Field(None, ge=0, description="Maximum cash limit")


class CashRegisterResponse(BaseModel):
    """Cash register response"""
    id: int
    register_id: str
    register_name: str
    location: Optional[str]

    is_active: bool
    current_float: float
    last_reconciled: Optional[datetime]

    requires_daily_reconciliation: bool
    max_cash_limit: Optional[float]

    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class CashTransactionCreate(BaseModel):
    """Create cash transaction for register"""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    register_id: str = Field(..., description="Cash register ID")
    transaction_type: str = Field(..., description="Type: sale, refund, deposit, withdrawal")
    amount: float = Field(..., ge=0, description="Transaction amount")
    reference: Optional[str] = Field(None, description="Transaction reference")
    description: Optional[str] = Field(None, description="Transaction description")
    metadata: dict[str, Any] = Field(default_factory=dict)


class CashTransactionResponse(BaseModel):
    """Cash transaction response"""
    id: str
    register_id: str
    transaction_type: str
    amount: float
    reference: Optional[str]
    description: Optional[str]
    balance_after: float
    created_at: datetime
    created_by: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class CashRegisterReconciliationCreate(BaseModel):
    """Create cash register reconciliation request"""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    actual_cash: float = Field(..., ge=0, description="Actual cash counted")
    reconciliation_date: Optional[datetime] = Field(None, description="Reconciliation date")
    shift_id: Optional[str] = Field(None, description="Shift identifier")
    notes: Optional[str] = Field(None, description="Reconciliation notes")
    metadata: dict[str, Any] = Field(default_factory=dict)


class CashRegisterReconciliationResponse(BaseModel):
    """Cash register reconciliation response"""
    id: str
    register_id: str
    reconciliation_date: datetime
    opening_float: float
    closing_float: float
    expected_cash: float
    actual_cash: float
    discrepancy: float
    reconciled_by: str
    notes: Optional[str]
    shift_id: Optional[str]
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReconciliationCreate(BaseModel):
    """Create reconciliation request"""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    bank_account_id: int = Field(..., description="Bank account ID")
    period_start: datetime = Field(..., description="Period start date")
    period_end: datetime = Field(..., description="Period end date")

    opening_balance: float = Field(..., description="Opening balance")
    closing_balance: float = Field(..., description="Expected closing balance")
    statement_balance: float = Field(..., description="Bank statement balance")

    notes: Optional[str] = Field(None, description="Reconciliation notes")
    statement_file_url: Optional[str] = Field(None, description="Bank statement file URL")


class ReconciliationResponse(BaseModel):
    """Reconciliation response"""
    id: int
    reconciliation_date: datetime
    period_start: datetime
    period_end: datetime

    bank_account_id: int

    opening_balance: float
    closing_balance: float
    statement_balance: float

    total_deposits: float
    total_withdrawals: float
    unreconciled_count: int
    discrepancy_amount: float

    status: str

    completed_by: Optional[str]
    completed_at: Optional[datetime]
    approved_by: Optional[str]
    approved_at: Optional[datetime]

    notes: Optional[str]
    statement_file_url: Optional[str]

    reconciled_items: List[dict] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class BankAccountSummary(BaseModel):
    """Bank account summary with stats"""
    account: CompanyBankAccountResponse
    total_deposits_mtd: float = Field(0.00, description="Month-to-date deposits")
    total_deposits_ytd: float = Field(0.00, description="Year-to-date deposits")
    pending_payments: int = Field(0, description="Number of pending payments")
    last_reconciliation: Optional[datetime] = None
    current_balance: Optional[float] = None  # If integrated with bank