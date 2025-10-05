"""
Tests for billing/core/models.py applying fake implementation pattern.

This test file focuses on:
1. Actually importing the module for real coverage
2. Testing Pydantic validators and field constraints
3. Testing model behavior and validation logic
4. Avoiding over-mocking
"""

import pytest
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

# Import module for coverage
import dotmac.platform.billing.core.models as core_models
from dotmac.platform.billing.core.models import (
    BillingBaseModel,
    Invoice,
    InvoiceLineItem,
    Payment,
    PaymentMethod,
    Transaction,
    CreditNote,
    CreditNoteLineItem,
    CreditApplication,
    CustomerCredit,
    Customer,
    Subscription,
    Product,
    Price,
    InvoiceItem,
)
from dotmac.platform.billing.core.enums import (
    BankAccountType,
    CreditApplicationType,
    CreditNoteStatus,
    CreditReason,
    CreditType,
    PaymentMethodStatus,
    PaymentMethodType,
    PaymentStatus,
    TransactionType,
)


class TestBillingBaseModel:
    """Test BillingBaseModel configuration."""

    def test_billing_base_model_config(self):
        """Test model configuration settings."""
        config = BillingBaseModel.model_config
        assert config["from_attributes"] is True
        assert config["validate_assignment"] is True
        assert config["str_strip_whitespace"] is True
        assert config["extra"] == "forbid"
        assert config["use_enum_values"] is True

    def test_billing_base_model_requires_tenant_id(self):
        """Test that tenant_id is required."""
        with pytest.raises(ValueError):
            BillingBaseModel()  # Missing tenant_id


class TestInvoiceLineItem:
    """Test InvoiceLineItem model."""

    def test_invoice_line_item_creation(self):
        """Test creating invoice line item."""
        item = InvoiceLineItem(
            description="Software License",
            quantity=2,
            unit_price=5000,  # $50.00
            total_price=10000,  # $100.00
            tax_rate=10.0,
            tax_amount=1000,  # $10.00
        )

        assert item.quantity == 2
        assert item.unit_price == 5000
        assert item.total_price == 10000
        assert item.tax_rate == 10.0

    def test_to_minor_units_converter_decimal(self):
        """Test Decimal to minor units conversion."""
        item = InvoiceLineItem(
            description="Test",
            quantity=1,
            unit_price=100,
            total_price=100,
            tax_amount=Decimal("15.50"),  # Should convert to 1550 cents
        )
        assert item.tax_amount == 1550

    def test_to_minor_units_converter_float(self):
        """Test float to minor units conversion."""
        item = InvoiceLineItem(
            description="Test",
            quantity=1,
            unit_price=100,
            total_price=100,
            discount_amount=12.25,  # Should convert to 1225 cents
        )
        assert item.discount_amount == 1225

    def test_total_price_validation_success(self):
        """Test total_price validation passes with correct value."""
        item = InvoiceLineItem(
            description="Test",
            quantity=3,
            unit_price=1000,
            total_price=3000,  # Correct: 3 * 1000
        )
        assert item.total_price == 3000

    def test_total_price_validation_failure(self):
        """Test total_price validation fails with incorrect value."""
        with pytest.raises(ValueError, match="Total price must equal"):
            InvoiceLineItem(
                description="Test",
                quantity=3,
                unit_price=1000,
                total_price=2500,  # Incorrect: should be 3000
            )

    def test_invoice_line_item_with_optional_fields(self):
        """Test line item with all optional fields."""
        item = InvoiceLineItem(
            line_item_id="line-123",
            description="Premium Support",
            quantity=1,
            unit_price=20000,
            total_price=20000,
            product_id="prod-456",
            subscription_id="sub-789",
            tax_rate=8.5,
            tax_amount=1700,
            discount_percentage=10.0,
            discount_amount=2000,
            extra_data={"category": "services"},
        )

        assert item.line_item_id == "line-123"
        assert item.product_id == "prod-456"
        assert item.discount_percentage == 10.0
        assert item.extra_data["category"] == "services"


class TestInvoice:
    """Test Invoice model."""

    def test_invoice_creation_minimal(self):
        """Test creating invoice with minimal fields."""
        invoice = Invoice(
            tenant_id="tenant-123",
            total_amount=10000,
        )

        assert invoice.tenant_id == "tenant-123"
        assert invoice.total_amount == 10000
        assert invoice.currency == "USD"
        assert invoice.status == "draft"

    def test_invoice_with_line_items(self):
        """Test invoice with multiple line items."""
        line_items = [
            InvoiceLineItem(
                description="Item 1",
                quantity=2,
                unit_price=5000,
                total_price=10000,
            ),
            InvoiceLineItem(
                description="Item 2",
                quantity=1,
                unit_price=3000,
                total_price=3000,
            ),
        ]

        invoice = Invoice(
            tenant_id="tenant-123",
            customer_id="cust-456",
            subtotal=13000,
            total_amount=13000,
            line_items=line_items,
        )

        assert len(invoice.line_items) == 2
        assert invoice.subtotal == 13000

    def test_invoice_net_amount_due_property(self):
        """Test net_amount_due calculated property."""
        # Case 1: With credits applied
        invoice = Invoice(
            tenant_id="tenant-123",
            total_amount=10000,
            total_credits_applied=3000,
        )
        assert invoice.net_amount_due == 7000

        # Case 2: Credits exceed total (should return 0)
        invoice2 = Invoice(
            tenant_id="tenant-123",
            total_amount=10000,
            total_credits_applied=15000,
        )
        assert invoice2.net_amount_due == 0

    def test_invoice_currency_validation(self):
        """Test currency field validation."""
        # Valid 3-letter currency
        invoice = Invoice(tenant_id="tenant-123", total_amount=100, currency="EUR")
        assert invoice.currency == "EUR"

        # Invalid currency length
        with pytest.raises(ValueError):
            Invoice(tenant_id="tenant-123", total_amount=100, currency="US")  # Too short

        with pytest.raises(ValueError):
            Invoice(tenant_id="tenant-123", total_amount=100, currency="USDD")  # Too long


class TestPayment:
    """Test Payment model."""

    def test_payment_creation(self):
        """Test creating payment."""
        payment = Payment(
            tenant_id="tenant-123",
            amount=10000,
            customer_id="cust-456",
            payment_method_type=PaymentMethodType.CARD.value,  # Use string value
            provider="stripe",
        )

        assert payment.amount == 10000
        assert payment.status == PaymentStatus.PENDING.value  # Compare string value
        assert payment.payment_method_type == PaymentMethodType.CARD.value
        assert payment.provider == "stripe"
        assert payment.retry_count == 0

    def test_payment_id_auto_generated(self):
        """Test payment_id is auto-generated."""
        payment1 = Payment(
            tenant_id="tenant-123",
            amount=5000,
            customer_id="cust-456",
            payment_method_type=PaymentMethodType.BANK_ACCOUNT.value,
            provider="stripe",
        )
        payment2 = Payment(
            tenant_id="tenant-123",
            amount=5000,
            customer_id="cust-456",
            payment_method_type=PaymentMethodType.BANK_ACCOUNT.value,
            provider="stripe",
        )

        # Each payment should have a unique ID
        assert payment1.payment_id is not None
        assert payment2.payment_id is not None
        assert payment1.payment_id != payment2.payment_id

    def test_payment_with_failure_info(self):
        """Test payment with failure information."""
        payment = Payment(
            tenant_id="tenant-123",
            amount=5000,
            customer_id="cust-456",
            payment_method_type=PaymentMethodType.CARD.value,
            provider="stripe",
            status=PaymentStatus.FAILED.value,
            failure_reason="Insufficient funds",
            retry_count=3,
        )

        assert payment.status == PaymentStatus.FAILED.value
        assert payment.failure_reason == "Insufficient funds"
        assert payment.retry_count == 3


class TestPaymentMethod:
    """Test PaymentMethod model."""

    def test_payment_method_credit_card(self):
        """Test credit card payment method."""
        pm = PaymentMethod(
            tenant_id="tenant-123",
            customer_id="cust-456",
            type=PaymentMethodType.CARD.value,
            provider="stripe",
            provider_payment_method_id="pm_123",
            display_name="Visa **** 4242",
            last_four="4242",
            brand="visa",
            expiry_month=12,
            expiry_year=2025,
        )

        assert pm.type == PaymentMethodType.CARD.value
        assert pm.last_four == "4242"
        assert pm.brand == "visa"
        assert pm.expiry_month == 12

    def test_payment_method_bank_account(self):
        """Test bank account payment method."""
        pm = PaymentMethod(
            tenant_id="tenant-123",
            customer_id="cust-456",
            type=PaymentMethodType.BANK_ACCOUNT.value,
            provider="stripe",
            provider_payment_method_id="ba_123",
            display_name="Checking ****1234",
            last_four="1234",
            bank_name="Chase Bank",
            account_type=BankAccountType.CHECKING.value,
            routing_number_last_four="6789",
        )

        assert pm.type == PaymentMethodType.BANK_ACCOUNT.value
        assert pm.bank_name == "Chase Bank"
        assert pm.account_type == BankAccountType.CHECKING.value

    def test_payment_method_validation_expiry(self):
        """Test expiry month/year validation."""
        # Valid expiry
        pm = PaymentMethod(
            tenant_id="tenant-123",
            customer_id="cust-456",
            type=PaymentMethodType.CARD.value,
            provider="stripe",
            provider_payment_method_id="pm_123",
            display_name="Card",
            expiry_month=1,
            expiry_year=2024,
        )
        assert pm.expiry_month == 1

        # Invalid month (too low)
        with pytest.raises(ValueError):
            PaymentMethod(
                tenant_id="tenant-123",
                customer_id="cust-456",
                type=PaymentMethodType.CARD.value,
                provider="stripe",
                provider_payment_method_id="pm_123",
                display_name="Card",
                expiry_month=0,
            )


class TestCreditNote:
    """Test CreditNote model."""

    def test_credit_note_creation(self):
        """Test creating credit note."""
        line_items = [
            CreditNoteLineItem(
                description="Refund for item",
                quantity=1,
                unit_price=-5000,
                total_price=-5000,
            )
        ]

        cn = CreditNote(
            tenant_id="tenant-123",
            created_by="user-456",
            customer_id="cust-789",
            subtotal=-5000,
            total_amount=-5000,
            credit_type=CreditType.REFUND.value,
            reason=CreditReason.CUSTOMER_REQUEST.value,  # Fixed enum value
            line_items=line_items,
        )

        assert cn.customer_id == "cust-789"
        assert cn.total_amount == -5000
        assert cn.credit_type == CreditType.REFUND.value
        assert len(cn.line_items) == 1

    def test_credit_note_requires_line_items(self):
        """Test credit note requires at least one line item."""
        with pytest.raises(ValueError):
            CreditNote(
                tenant_id="tenant-123",
                created_by="user-456",
                customer_id="cust-789",
                subtotal=-5000,
                total_amount=-5000,
                credit_type=CreditType.REFUND.value,
                reason=CreditReason.CUSTOMER_REQUEST.value,  # Fixed enum value
                line_items=[],  # Empty list should fail
            )


class TestTransaction:
    """Test Transaction model."""

    def test_transaction_creation(self):
        """Test creating transaction."""
        tx = Transaction(
            tenant_id="tenant-123",
            amount=10000,
            transaction_type=TransactionType.PAYMENT.value,
            description="Payment received",
            customer_id="cust-456",
            payment_id="pay-789",
        )

        assert tx.amount == 10000
        assert tx.transaction_type == TransactionType.PAYMENT.value
        assert tx.customer_id == "cust-456"


class TestCustomer:
    """Test Customer model."""

    def test_customer_creation(self):
        """Test creating customer."""
        customer = Customer(
            tenant_id="tenant-123",
            customer_id="cust-456",
            email="customer@example.com",
            billing_name="John Doe",
            payment_terms=30,
        )

        assert customer.email == "customer@example.com"
        assert customer.payment_terms == 30
        assert customer.is_active is True
        assert customer.currency == "USD"


class TestSubscription:
    """Test Subscription model."""

    def test_subscription_creation(self):
        """Test creating subscription."""
        sub = Subscription(
            tenant_id="tenant-123",
            subscription_id="sub-456",
            customer_id="cust-789",
            plan_id="plan-premium",
            status="active",
            billing_cycle="monthly",
        )

        assert sub.subscription_id == "sub-456"
        assert sub.customer_id == "cust-789"
        assert sub.billing_cycle == "monthly"


class TestProductAndPrice:
    """Test Product and Price models."""

    def test_product_creation(self):
        """Test creating product."""
        product = Product(
            tenant_id="tenant-123",
            product_id="prod-456",
            name="Premium Plan",
            description="Premium subscription plan",
            unit_price=9999,
            currency="USD",
        )

        assert product.name == "Premium Plan"
        assert product.unit_price == 9999

    def test_price_creation(self):
        """Test creating price."""
        price = Price(
            tenant_id="tenant-123",
            price_id="price-789",
            product_id="prod-456",
            unit_amount=9999,
            currency="USD",
        )

        assert price.product_id == "prod-456"
        assert price.unit_amount == 9999


class TestCreditApplication:
    """Test CreditApplication model."""

    def test_credit_application_creation(self):
        """Test creating credit application."""
        app = CreditApplication(
            tenant_id="tenant-123",
            credit_note_id="cn-456",
            applied_to_type=CreditApplicationType.INVOICE.value,
            applied_to_id="inv-789",
            applied_amount=5000,
            applied_by="user-123",
        )

        assert app.credit_note_id == "cn-456"
        assert app.applied_to_type == CreditApplicationType.INVOICE.value
        assert app.applied_amount == 5000

    def test_credit_application_amount_must_be_positive(self):
        """Test applied_amount must be > 0."""
        with pytest.raises(ValueError):
            CreditApplication(
                tenant_id="tenant-123",
                credit_note_id="cn-456",
                applied_to_type=CreditApplicationType.INVOICE.value,
                applied_to_id="inv-789",
                applied_amount=0,  # Must be > 0
                applied_by="user-123",
            )


class TestCustomerCredit:
    """Test CustomerCredit model."""

    def test_customer_credit_creation(self):
        """Test creating customer credit."""
        credit = CustomerCredit(
            tenant_id="tenant-123",
            customer_id="cust-456",
            total_credit_amount=10000,
            credit_notes=["cn-1", "cn-2"],
            auto_apply_to_new_invoices=True,
        )

        assert credit.customer_id == "cust-456"
        assert credit.total_credit_amount == 10000
        assert len(credit.credit_notes) == 2
        assert credit.auto_apply_to_new_invoices is True


class TestInvoiceItem:
    """Test InvoiceItem model."""

    def test_invoice_item_creation(self):
        """Test creating invoice item."""
        item = InvoiceItem(
            tenant_id="tenant-123",
            item_id="item-456",
            invoice_id="inv-789",
            description="Consulting Services",
            quantity=5,
            unit_price=10000,
            total_amount=50000,
        )

        assert item.invoice_id == "inv-789"
        assert item.quantity == 5
        assert item.total_amount == 50000
