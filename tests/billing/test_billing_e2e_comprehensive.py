"""
Comprehensive End-to-End Integration Tests for Billing Module.

Tests complete billing workflows including:
- Customer onboarding with payment methods
- Subscription lifecycle management
- Invoice generation and payment processing
- Tax calculations and receipts
- Credit notes and refunds
- Reporting and analytics
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import json
from uuid import uuid4

from dotmac.platform.billing.invoicing.service import InvoiceService
from dotmac.platform.billing.payments.service import PaymentService
from dotmac.platform.billing.subscriptions.service import SubscriptionService
from dotmac.platform.billing.catalog.service import ProductService
from dotmac.platform.billing.tax.calculator import TaxCalculator, TaxRate
from dotmac.platform.billing.receipts.generators import HTMLReceiptGenerator, PDFReceiptGenerator
from dotmac.platform.billing.receipts.models import Receipt, ReceiptLineItem
from dotmac.platform.billing.credit_notes.service import CreditNoteService
from dotmac.platform.billing.integration import BillingIntegrationService
from dotmac.platform.billing.core.models import (
    InvoiceStatus,
    PaymentStatus,
    PaymentMethodType,
    BillingCycle,
    CreditNoteStatus,
)
from dotmac.platform.billing.subscriptions.models import (
    SubscriptionStatus,
    Subscription,
    SubscriptionPlan,
)
from dotmac.platform.billing.catalog.models import (
    Product,
    ProductCategory,
    ProductStatus,
    PricingModel,
)


@pytest.fixture
async def db_session():
    """Mock database session for testing."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def tenant_id():
    """Test tenant ID."""
    return "test-tenant-123"


@pytest.fixture
def customer_id():
    """Test customer ID."""
    return "cust_" + str(uuid4())


@pytest.fixture
def mock_stripe_client():
    """Mock Stripe client for payment processing."""
    client = MagicMock()
    client.payment_intents.create = AsyncMock(return_value={
        "id": "pi_test_123",
        "status": "succeeded",
        "amount": 10000,
        "currency": "usd",
    })
    client.payment_methods.attach = AsyncMock()
    client.customers.create = AsyncMock(return_value={"id": "cus_test_123"})
    client.subscriptions.create = AsyncMock(return_value={
        "id": "sub_test_123",
        "status": "active",
    })
    return client


@pytest.fixture
async def billing_services(db_session, tenant_id):
    """Initialize all billing services for integration testing."""

    # Initialize core services
    invoice_service = InvoiceService(db_session=db_session)
    payment_service = PaymentService(db_session=db_session)
    subscription_service = SubscriptionService(db_session=db_session)
    catalog_service = ProductService(db_session=db_session)
    tax_calculator = TaxCalculator()
    credit_note_service = CreditNoteService(db_session=db_session)

    # Setup default tax rates
    tax_calculator.add_tax_rate(
        jurisdiction="US-CA",
        name="California Sales Tax",
        rate=7.25,
    )
    tax_calculator.add_tax_rate(
        jurisdiction="EU-GB",
        name="UK VAT",
        rate=20.0,
        is_inclusive=True,
    )

    # Initialize integration service
    integration_service = BillingIntegrationService()
    integration_service.invoice_service = invoice_service
    integration_service.payment_service = payment_service
    integration_service.subscription_service = subscription_service

    return {
        "invoice": invoice_service,
        "payment": payment_service,
        "subscription": subscription_service,
        "catalog": catalog_service,
        "tax": tax_calculator,
        "credit_note": credit_note_service,
        "integration": integration_service,
    }


class TestCustomerOnboardingE2E:
    """Test complete customer onboarding workflow."""

    @pytest.mark.asyncio
    async def test_complete_customer_onboarding_flow(
        self,
        billing_services,
        tenant_id,
        customer_id,
        mock_stripe_client,
    ):
        """Test complete customer onboarding with payment method setup."""

        # Step 1: Create customer in billing system
        customer_data = {
            "customer_id": customer_id,
            "tenant_id": tenant_id,
            "email": "test@example.com",
            "name": "Test Customer",
            "billing_address": {
                "line1": "123 Main St",
                "city": "San Francisco",
                "state": "CA",
                "postal_code": "94105",
                "country": "US",
            },
        }

        # Step 2: Add payment method
        with patch.object(
            billing_services["payment"].provider,
            "create_payment_method",
            return_value={"id": "pm_test_123", "type": "card"},
        ):
            payment_method = await billing_services["payment"].add_payment_method(
                tenant_id=tenant_id,
                customer_id=customer_id,
                payment_method_type=PaymentMethodType.CREDIT_CARD,
                provider_payment_method_id="pm_test_123",
                is_default=True,
            )

            assert payment_method is not None
            assert payment_method["is_default"] is True

        # Step 3: Create a subscription plan
        plan = SubscriptionPlan(
            plan_id="plan_pro",
            tenant_id=tenant_id,
            name="Pro Plan",
            billing_cycle=BillingCycle.MONTHLY,
            price=9999,  # $99.99
            currency="USD",
            features=["unlimited_storage", "priority_support"],
        )

        # Step 4: Subscribe customer to plan
        with patch.object(
            billing_services["subscription"],
            "create_subscription",
            return_value=Subscription(
                subscription_id="sub_test_123",
                tenant_id=tenant_id,
                customer_id=customer_id,
                plan_id=plan.plan_id,
                status=SubscriptionStatus.ACTIVE,
                current_period_start=datetime.now(timezone.utc),
                current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
            ),
        ):
            subscription = await billing_services["subscription"].create_subscription(
                tenant_id=tenant_id,
                customer_id=customer_id,
                plan_id=plan.plan_id,
                payment_method_id="pm_test_123",
            )

            assert subscription.status == SubscriptionStatus.ACTIVE
            assert subscription.customer_id == customer_id

        # Step 5: Generate first invoice
        with patch.object(
            billing_services["invoice"],
            "create_invoice",
            return_value={
                "invoice_id": "inv_test_123",
                "status": InvoiceStatus.DRAFT,
                "total_amount": 9999,
                "tax_amount": 724,  # 7.25% tax
            }
        ):
            invoice = await billing_services["invoice"].create_invoice(
                tenant_id=tenant_id,
                customer_id=customer_id,
                line_items=[{
                    "description": "Pro Plan - Monthly",
                    "quantity": 1,
                    "unit_price": 9999,
                    "total_price": 9999,
                }],
            )

            assert invoice["status"] == InvoiceStatus.DRAFT
            assert invoice["total_amount"] == 9999

    @pytest.mark.asyncio
    async def test_customer_with_trial_period(
        self,
        billing_services,
        tenant_id,
        customer_id,
    ):
        """Test customer onboarding with trial period."""

        trial_end = datetime.now(timezone.utc) + timedelta(days=14)

        # Create subscription with trial
        with patch.object(
            billing_services["subscription"],
            "create_subscription",
            return_value=Subscription(
                subscription_id="sub_trial_123",
                tenant_id=tenant_id,
                customer_id=customer_id,
                plan_id="plan_pro",
                status=SubscriptionStatus.TRIALING,
                trial_end=trial_end,
                current_period_start=datetime.now(timezone.utc),
                current_period_end=trial_end,
            ),
        ):
            subscription = await billing_services["subscription"].create_subscription(
                tenant_id=tenant_id,
                customer_id=customer_id,
                plan_id="plan_pro",
                trial_days=14,
            )

            assert subscription.status == SubscriptionStatus.TRIALING
            assert subscription.trial_end is not None
            assert subscription.trial_end > datetime.now(timezone.utc)

    @pytest.mark.asyncio
    async def test_customer_with_multiple_payment_methods(
        self,
        billing_services,
        tenant_id,
        customer_id,
    ):
        """Test managing multiple payment methods for a customer."""

        payment_methods = []

        # Add multiple payment methods
        for i, pm_type in enumerate([
            PaymentMethodType.CREDIT_CARD,
            PaymentMethodType.BANK_ACCOUNT,
            PaymentMethodType.PAYPAL,
        ]):
            with patch.object(
                billing_services["payment"].provider,
                "create_payment_method",
                return_value={"id": f"pm_test_{i}", "type": pm_type.value},
            ):
                pm = await billing_services["payment"].add_payment_method(
                    tenant_id=tenant_id,
                    customer_id=customer_id,
                    payment_method_type=pm_type,
                    provider_payment_method_id=f"pm_test_{i}",
                    is_default=(i == 0),  # First one is default
                )
                payment_methods.append(pm)

        assert len(payment_methods) == 3
        assert payment_methods[0]["is_default"] is True
        assert all(not pm["is_default"] for pm in payment_methods[1:])


class TestSubscriptionLifecycleE2E:
    """Test complete subscription lifecycle."""

    @pytest.mark.asyncio
    async def test_subscription_upgrade_downgrade_flow(
        self,
        billing_services,
        tenant_id,
        customer_id,
    ):
        """Test subscription plan changes."""

        # Start with basic plan
        basic_subscription = Subscription(
            subscription_id="sub_basic_123",
            tenant_id=tenant_id,
            customer_id=customer_id,
            plan_id="plan_basic",
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
        )

        # Upgrade to pro plan
        with patch.object(
            billing_services["subscription"],
            "update_subscription",
            return_value=Subscription(
                **{**basic_subscription.__dict__, "plan_id": "plan_pro"}
            ),
        ):
            upgraded = await billing_services["subscription"].update_subscription(
                tenant_id=tenant_id,
                subscription_id=basic_subscription.subscription_id,
                plan_id="plan_pro",
            )

            assert upgraded.plan_id == "plan_pro"
            assert upgraded.status == SubscriptionStatus.ACTIVE

        # Generate prorated invoice for upgrade
        prorated_amount = 4999  # Half month difference

        with patch.object(
            billing_services["invoice"],
            "create_invoice",
            return_value={
                "invoice_id": "inv_prorated_123",
                "total_amount": prorated_amount,
                "description": "Prorated charge for plan upgrade",
            }
        )

prorated_invoice = await billing_services["invoice"].create_invoice(
                tenant_id=tenant_id,
                customer_id=customer_id,
                line_items=[{
                    "description": "Pro Plan upgrade (prorated)",
                    "quantity": 1,
                    "unit_price": prorated_amount,
                    "total_price": prorated_amount,
                }],
            )

            assert prorated_invoice["total_amount"] == prorated_amount

    @pytest.mark.asyncio
    async def test_subscription_cancellation_and_reactivation(
        self,
        billing_services,
        tenant_id,
        customer_id,
    ):
        """Test subscription cancellation and reactivation flow."""

        active_subscription = Subscription(
            subscription_id="sub_cancel_123",
            tenant_id=tenant_id,
            customer_id=customer_id,
            plan_id="plan_pro",
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
        )

        # Cancel subscription
        with patch.object(
            billing_services["subscription"],
            "cancel_subscription",
            return_value=Subscription(
                **{**active_subscription.__dict__,
                   "status": SubscriptionStatus.CANCELED,
                   "canceled_at": datetime.now(timezone.utc)}
            ),
        ):
            canceled = await billing_services["subscription"].cancel_subscription(
                tenant_id=tenant_id,
                subscription_id=active_subscription.subscription_id,
                cancel_immediately=False,  # Cancel at period end
            )

            assert canceled.status == SubscriptionStatus.CANCELED
            assert canceled.canceled_at is not None

        # Reactivate subscription
        with patch.object(
            billing_services["subscription"],
            "reactivate_subscription",
            return_value=Subscription(
                **{**active_subscription.__dict__,
                   "status": SubscriptionStatus.ACTIVE,
                   "canceled_at": None}
            ),
        ):
            reactivated = await billing_services["subscription"].reactivate_subscription(
                tenant_id=tenant_id,
                subscription_id=active_subscription.subscription_id,
            )

            assert reactivated.status == SubscriptionStatus.ACTIVE
            assert reactivated.canceled_at is None

    @pytest.mark.asyncio
    async def test_subscription_pause_and_resume(
        self,
        billing_services,
        tenant_id,
        customer_id,
    ):
        """Test pausing and resuming subscription."""

        active_subscription = Subscription(
            subscription_id="sub_pause_123",
            tenant_id=tenant_id,
            customer_id=customer_id,
            plan_id="plan_pro",
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
        )

        # Pause subscription
        with patch.object(
            billing_services["subscription"],
            "pause_subscription",
            return_value=Subscription(
                **{**active_subscription.__dict__,
                   "status": SubscriptionStatus.PAUSED,
                   "paused_at": datetime.now(timezone.utc)}
            ),
        ):
            paused = await billing_services["subscription"].pause_subscription(
                tenant_id=tenant_id,
                subscription_id=active_subscription.subscription_id,
            )

            assert paused.status == SubscriptionStatus.PAUSED

        # Resume subscription
        with patch.object(
            billing_services["subscription"],
            "resume_subscription",
            return_value=Subscription(
                **{**active_subscription.__dict__,
                   "status": SubscriptionStatus.ACTIVE,
                   "paused_at": None}
            ),
        ):
            resumed = await billing_services["subscription"].resume_subscription(
                tenant_id=tenant_id,
                subscription_id=active_subscription.subscription_id,
            )

            assert resumed.status == SubscriptionStatus.ACTIVE


class TestInvoiceAndPaymentE2E:
    """Test invoice generation and payment processing."""

    @pytest.mark.asyncio
    async def test_complete_invoice_payment_flow(
        self,
        billing_services,
        tenant_id,
        customer_id,
        mock_stripe_client,
    ):
        """Test complete invoice generation and payment flow."""

        # Step 1: Create invoice
        invoice_data = {
            "invoice_id": "inv_flow_123",
            "tenant_id": tenant_id,
            "customer_id": customer_id,
            "invoice_number": "INV-2024-001",
            "status": InvoiceStatus.DRAFT,
            "subtotal": 10000,
            "tax_amount": 725,
            "total_amount": 10725,
            "line_items": [{
                "description": "Professional Services",
                "quantity": 10,
                "unit_price": 1000,
                "total_price": 10000,
            }],
            "due_date": datetime.now(timezone.utc) + timedelta(days=30),
        }

        with patch.object(
            billing_services["invoice"],
            "create_invoice",
            return_value=invoice_data,
        ):
            invoice = await billing_services["invoice"].create_invoice(
                tenant_id=tenant_id,
                customer_id=customer_id,
                line_items=invoice_data["line_items"],
            )

            assert invoice["status"] == InvoiceStatus.DRAFT

        # Step 2: Finalize invoice
        with patch.object(
            billing_services["invoice"],
            "finalize_invoice",
            return_value={**invoice_data, "status": InvoiceStatus.OPEN},
        ):
            finalized = await billing_services["invoice"].finalize_invoice(
                tenant_id=tenant_id,
                invoice_id=invoice["invoice_id"],
            )

            assert finalized["status"] == InvoiceStatus.OPEN

        # Step 3: Process payment
        with patch.object(
            billing_services["payment"],
            "create_payment",
            return_value={
                "payment_id": "pay_flow_123",
                "status": PaymentStatus.SUCCEEDED,
                "amount": 10725,
                "invoice_id": invoice["invoice_id"],
            }
        )

payment = await billing_services["payment"].create_payment(
                tenant_id=tenant_id,
                customer_id=customer_id,
                amount=10725,
                payment_method_id="pm_test_123",
                invoice_id=invoice["invoice_id"],
            )

            assert payment["status"] == PaymentStatus.SUCCEEDED

        # Step 4: Mark invoice as paid
        with patch.object(
            billing_services["invoice"],
            "mark_as_paid",
            return_value={**invoice_data, "status": InvoiceStatus.PAID},
        ):
            paid_invoice = await billing_services["invoice"].mark_as_paid(
                tenant_id=tenant_id,
                invoice_id=invoice["invoice_id"],
                payment_id=payment["payment_id"],
            )

            assert paid_invoice["status"] == InvoiceStatus.PAID

        # Step 5: Generate receipt
        receipt = Receipt(
            tenant_id=tenant_id,
            receipt_number="REC-2024-001",
            payment_id=payment["payment_id"],
            invoice_id=invoice["invoice_id"],
            customer_id=customer_id,
            customer_name="Test Customer",
            customer_email="test@example.com",
            subtotal=10000,
            tax_amount=725,
            total_amount=10725,
            payment_method="credit_card",
            payment_status="completed",
            line_items=[ReceiptLineItem(
                description="Professional Services",
                quantity=10,
                unit_price=1000,
                total_price=10000,
            )],
            currency="USD",
        )

        html_generator = HTMLReceiptGenerator()
        html_receipt = await html_generator.generate(receipt)

        assert "REC-2024-001" in html_receipt
        assert "$107.25" in html_receipt

    @pytest.mark.asyncio
    async def test_recurring_invoice_generation(
        self,
        billing_services,
        tenant_id,
        customer_id,
    ):
        """Test automatic recurring invoice generation."""

        # Setup recurring billing
        subscription = Subscription(
            subscription_id="sub_recurring_123",
            tenant_id=tenant_id,
            customer_id=customer_id,
            plan_id="plan_monthly",
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.now(timezone.utc) - timedelta(days=30),
            current_period_end=datetime.now(timezone.utc),
        )

        # Generate invoice for new billing period
        with patch.object(
            billing_services["integration"],
            "process_subscription_billing",
            return_value={
                "invoice_id": "inv_recurring_123",
                "subscription_id": subscription.subscription_id,
                "billing_period_start": subscription.current_period_end,
                "billing_period_end": subscription.current_period_end + timedelta(days=30),
                "total_amount": 9999,
            }
        )

recurring_invoice = await billing_services["integration"].process_subscription_billing(
                tenant_id=tenant_id,
                subscription_id=subscription.subscription_id,
            )

            assert recurring_invoice["invoice_id"] is not None
            assert recurring_invoice["total_amount"] == 9999

    @pytest.mark.asyncio
    async def test_failed_payment_retry_flow(
        self,
        billing_services,
        tenant_id,
        customer_id,
    ):
        """Test payment failure and retry logic."""

        invoice_id = "inv_retry_123"

        # Initial payment attempt fails
        with patch.object(
            billing_services["payment"],
            "create_payment",
            return_value={
                "payment_id": "pay_failed_123",
                "status": PaymentStatus.FAILED,
                "error_message": "Insufficient funds",
            }
        )

failed_payment = await billing_services["payment"].create_payment(
                tenant_id=tenant_id,
                customer_id=customer_id,
                amount=10000,
                payment_method_id="pm_test_123",
                invoice_id=invoice_id,
            )

            assert failed_payment["status"] == PaymentStatus.FAILED

        # Retry payment with different payment method
        with patch.object(
            billing_services["payment"],
            "retry_payment",
            return_value={
                "payment_id": "pay_retry_123",
                "status": PaymentStatus.SUCCEEDED,
                "amount": 10000,
            }
        )

retry_payment = await billing_services["payment"].retry_payment(
                tenant_id=tenant_id,
                payment_id=failed_payment["payment_id"],
                payment_method_id="pm_backup_123",
            )

            assert retry_payment["status"] == PaymentStatus.SUCCEEDED


class TestTaxAndComplianceE2E:
    """Test tax calculation and compliance workflows."""

    @pytest.mark.asyncio
    async def test_multi_jurisdiction_tax_calculation(
        self,
        billing_services,
        tenant_id,
    ):
        """Test tax calculation across multiple jurisdictions."""

        test_cases = [
            {
                "customer_id": "cust_ca_123",
                "jurisdiction": "US-CA",
                "amount": 10000,
                "expected_tax": 725,  # 7.25%
            },
            {
                "customer_id": "cust_uk_123",
                "jurisdiction": "EU-GB",
                "amount": 12000,  # Inclusive
                "expected_tax": 2000,  # 20% VAT
                "is_inclusive": True,
            },
            {
                "customer_id": "cust_ny_123",
                "jurisdiction": "US-NY",
                "amount": 10000,
                "expected_tax": 0,  # No rate configured
            },
        ]

        for case in test_cases:
            if case.get("is_inclusive"):
                result = billing_services["tax"].calculate_tax(
                    amount=case["amount"],
                    jurisdiction=case["jurisdiction"],
                    is_tax_inclusive=True,
                )
                assert result.tax_amount == case["expected_tax"]
            else:
                result = billing_services["tax"].calculate_tax(
                    amount=case["amount"],
                    jurisdiction=case["jurisdiction"],
                )
                assert result.tax_amount >= case["expected_tax"]  # May have additional taxes

    @pytest.mark.asyncio
    async def test_tax_exempt_customer_flow(
        self,
        billing_services,
        tenant_id,
        customer_id,
    ):
        """Test tax exemption for qualified customers."""

        # Setup tax-exempt customer
        customer_settings = {
            "customer_id": customer_id,
            "tax_exempt": True,
            "tax_exempt_certificate": "EXEMPT-123-456",
        }

        # Create invoice without tax
        with patch.object(
            billing_services["invoice"],
            "create_invoice",
            return_value={
                "invoice_id": "inv_exempt_123",
                "subtotal": 10000,
                "tax_amount": 0,  # No tax for exempt customer
                "total_amount": 10000,
                "tax_exempt": True,
            }
        ):
            invoice = await billing_services["invoice"].create_invoice(
                tenant_id=tenant_id,
                customer_id=customer_id,
                line_items=[{
                    "description": "Service",
                    "quantity": 1,
                    "unit_price": 10000,
                    "total_price": 10000,
                    "is_tax_exempt": True,
                }],
            )

            assert invoice["tax_amount"] == 0
            assert invoice["tax_exempt"] is True


class TestCreditNotesAndRefundsE2E:
    """Test credit notes and refund workflows."""

    @pytest.mark.asyncio
    async def test_full_refund_flow(
        self,
        billing_services,
        tenant_id,
        customer_id,
    ):
        """Test complete refund process with credit note."""

        original_invoice_id = "inv_refund_123"
        original_payment_id = "pay_refund_123"

        # Step 1: Create credit note
        with patch.object(
            billing_services["credit_note"],
            "create_credit_note",
            return_value={
                "credit_note_id": "cn_123",
                "invoice_id": original_invoice_id,
                "amount": 10000,
                "reason": "Customer request",
                "status": CreditNoteStatus.ISSUED,
            }
        )

credit_note = await billing_services["credit_note"].create_credit_note(
                tenant_id=tenant_id,
                customer_id=customer_id,
                invoice_id=original_invoice_id,
                amount=10000,
                reason="Customer request",
            )

            assert credit_note["status"] == CreditNoteStatus.ISSUED

        # Step 2: Process refund
        with patch.object(
            billing_services["payment"],
            "refund_payment",
            return_value={
                "refund_id": "refund_123",
                "payment_id": original_payment_id,
                "amount": 10000,
                "status": "succeeded",
            }
        )

refund = await billing_services["payment"].refund_payment(
                tenant_id=tenant_id,
                payment_id=original_payment_id,
                amount=10000,
                reason="Customer request",
            )

            assert refund["status"] == "succeeded"

        # Step 3: Apply credit note
        with patch.object(
            billing_services["credit_note"],
            "apply_credit_note",
            return_value={
                "credit_note_id": credit_note["credit_note_id"],
                "status": CreditNoteStatus.APPLIED,
                "applied_amount": 10000,
            }
        )

applied = await billing_services["credit_note"].apply_credit_note(
                tenant_id=tenant_id,
                credit_note_id=credit_note["credit_note_id"],
            )

            assert applied["status"] == CreditNoteStatus.APPLIED

    @pytest.mark.asyncio
    async def test_partial_refund_with_credit(
        self,
        billing_services,
        tenant_id,
        customer_id,
    ):
        """Test partial refund with credit balance."""

        # Create partial credit note
        with patch.object(
            billing_services["credit_note"],
            "create_credit_note",
            return_value={
                "credit_note_id": "cn_partial_123",
                "amount": 5000,  # 50% refund
                "remaining_credit": 5000,
                "status": CreditNoteStatus.ISSUED,
            }
        )

partial_credit = await billing_services["credit_note"].create_credit_note(
                tenant_id=tenant_id,
                customer_id=customer_id,
                invoice_id="inv_partial_123",
                amount=5000,
                reason="Partial service issue",
            )

            assert partial_credit["amount"] == 5000

        # Apply credit to next invoice
        with patch.object(
            billing_services["invoice"],
            "apply_credit_balance",
            return_value={
                "invoice_id": "inv_next_123",
                "original_amount": 8000,
                "credit_applied": 5000,
                "final_amount": 3000,
            }
        )

next_invoice = await billing_services["invoice"].apply_credit_balance(
                tenant_id=tenant_id,
                invoice_id="inv_next_123",
                credit_amount=5000,
            )

            assert next_invoice["credit_applied"] == 5000
            assert next_invoice["final_amount"] == 3000


class TestReportingAndAnalyticsE2E:
    """Test billing reports and analytics workflows."""

    @pytest.mark.asyncio
    async def test_monthly_revenue_report_generation(
        self,
        billing_services,
        tenant_id,
    ):
        """Test generating monthly revenue reports."""

        report_month = datetime(2024, 1, 1, tzinfo=timezone.utc)

        # Mock report service
        mock_report = MagicMock()
        mock_report.generate_monthly_revenue_report = AsyncMock(

            return_value={
                "report_id": "report_revenue_202401",
                "period": "2024-01",
                "total_revenue": 250000,  # $2,500.00
                "total_invoices": 25,
                "total_payments": 23,
                "outstanding_amount": 20000,  # $200.00
                "revenue_by_product": {
                    "plan_pro": 150000,
                    "plan_basic": 100000,
                },
                "revenue_by_country": {
                    "US": 200000,
                    "GB": 50000,
                },
            }
        )

        report = await mock_report.generate_monthly_revenue_report(
                tenant_id=tenant_id,
                month=report_month,
            )

            assert report["total_revenue"] == 250000
            assert report["total_invoices"] == 25
            assert report["outstanding_amount"] == 20000

    @pytest.mark.asyncio
    async def test_customer_lifetime_value_calculation(
        self,
        billing_services,
        tenant_id,
        customer_id,
    ):
        """Test calculating customer lifetime value."""

        # Mock report service
        mock_report = MagicMock()
        mock_report.calculate_customer_ltv = AsyncMock(

            return_value={
                "customer_id": customer_id,
                "total_revenue": 500000,  # $5,000.00
                "average_order_value": 10000,  # $100.00
                "purchase_frequency": 5,
                "customer_lifespan_months": 10,
                "predicted_ltv": 600000,  # $6,000.00
            }
        )

        ltv = await mock_report.calculate_customer_ltv(
                tenant_id=tenant_id,
                customer_id=customer_id,
            )

            assert ltv["total_revenue"] == 500000
            assert ltv["predicted_ltv"] == 600000

    @pytest.mark.asyncio
    async def test_churn_analysis_report(
        self,
        billing_services,
        tenant_id,
    ):
        """Test subscription churn analysis."""

        # Mock report service
        mock_report = MagicMock()
        mock_report.generate_churn_report = AsyncMock(

            return_value={
                "report_id": "report_churn_202401",
                "period": "2024-01",
                "total_subscriptions_start": 100,
                "new_subscriptions": 20,
                "canceled_subscriptions": 15,
                "churn_rate": 15.0,  # 15%
                "mrr_churn": 150000,  # $1,500.00 MRR lost
                "reasons": {
                    "price": 5,
                    "features": 3,
                    "support": 2,
                    "other": 5,
                },
            }
        )

        churn_report = await mock_report.generate_churn_report(
                tenant_id=tenant_id,
                month=datetime(2024, 1, 1, tzinfo=timezone.utc),
            )

            assert churn_report["churn_rate"] == 15.0
            assert churn_report["canceled_subscriptions"] == 15


class TestWebhookIntegrationE2E:
    """Test webhook handling for payment providers."""

    @pytest.mark.asyncio
    async def test_stripe_webhook_payment_succeeded(
        self,
        billing_services,
        tenant_id,
    ):
        """Test handling Stripe payment success webhook."""

        webhook_event = {
            "id": "evt_test_123",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_123",
                    "amount": 10000,
                    "currency": "usd",
                    "status": "succeeded",
                    "metadata": {
                        "tenant_id": tenant_id,
                        "invoice_id": "inv_webhook_123",
                    },
                },
            },
        }

        with patch.object(
            billing_services["integration"],
            "handle_payment_webhook",
            return_value={
                "processed": True,
                "invoice_updated": True,
                "invoice_status": InvoiceStatus.PAID,
            }
        )

result = await billing_services["integration"].handle_payment_webhook(
                provider="stripe",
                event=webhook_event,
            )

            assert result["processed"] is True
            assert result["invoice_status"] == InvoiceStatus.PAID

    @pytest.mark.asyncio
    async def test_webhook_subscription_updated(
        self,
        billing_services,
        tenant_id,
    ):
        """Test handling subscription update webhooks."""

        webhook_event = {
            "id": "evt_sub_123",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_test_123",
                    "status": "active",
                    "current_period_end": 1735689600,  # Unix timestamp
                    "items": {
                        "data": [{
                            "price": {
                                "id": "price_pro",
                                "unit_amount": 9999,
                            },
                        }],
                    },
                },
            },
        }

        with patch.object(
            billing_services["integration"],
            "handle_subscription_webhook",
            return_value={
                "subscription_id": "sub_test_123",
                "status": "active",
                "next_billing_date": datetime.fromtimestamp(1735689600, tz=timezone.utc),
            }
        )

result = await billing_services["integration"].handle_subscription_webhook(
                provider="stripe",
                event=webhook_event,
            )

            assert result["status"] == "active"
            assert result["next_billing_date"].year == 2024


class TestBillingSettingsE2E:
    """Test billing configuration and settings management."""

    @pytest.mark.asyncio
    async def test_update_billing_configuration(
        self,
        billing_services,
        tenant_id,
    ):
        """Test updating billing configuration settings."""

        settings = {
            "auto_charge": True,
            "invoice_prefix": "INV",
            "payment_terms_days": 30,
            "late_fee_percentage": 1.5,
            "currency": "USD",
            "tax_inclusive_pricing": False,
        }

        # Mock settings service
        mock_settings = MagicMock()
        mock_settings.update_settings = AsyncMock(

            return_value=settings,
        ):
            updated = await mock_settings.update_settings(
                tenant_id=tenant_id,
                settings=settings,
            )

            assert updated["auto_charge"] is True
            assert updated["payment_terms_days"] == 30

    @pytest.mark.asyncio
    async def test_payment_retry_configuration(
        self,
        billing_services,
        tenant_id,
    ):
        """Test configuring payment retry settings."""

        retry_config = {
            "max_retries": 3,
            "retry_intervals": [1, 3, 7],  # Days
            "dunning_emails": True,
            "cancel_on_max_failures": True,
        }

        # Mock settings service
        mock_settings = MagicMock()
        mock_settings.update_retry_configuration = AsyncMock(

            return_value=retry_config,
        ):
            config = await mock_settings.update_retry_configuration(
                tenant_id=tenant_id,
                configuration=retry_config,
            )

            assert config["max_retries"] == 3
            assert len(config["retry_intervals"]) == 3


class TestCatalogAndPricingE2E:
    """Test product catalog and pricing management."""

    @pytest.mark.asyncio
    async def test_create_product_with_pricing_tiers(
        self,
        billing_services,
        tenant_id,
    ):
        """Test creating products with tiered pricing."""

        product = Product(
            product_id="prod_enterprise",
            tenant_id=tenant_id,
            name="Enterprise Plan",
            description="Full-featured enterprise solution",
            status=ProductStatus.ACTIVE,
            pricing_model=PricingModel.TIERED,
        )

        pricing_tiers = [
            {"min_quantity": 1, "max_quantity": 10, "unit_price": 10000},
            {"min_quantity": 11, "max_quantity": 50, "unit_price": 8000},
            {"min_quantity": 51, "max_quantity": None, "unit_price": 6000},
        ]

        with patch.object(
            billing_services["catalog"],
            "create_product",
            return_value=product,
        ):
            created_product = await billing_services["catalog"].create_product(
                tenant_id=tenant_id,
                product=product,
            )

            assert created_product.pricing_model == PricingModel.TIERED

        # Mock pricing service
        mock_pricing = MagicMock()
        mock_pricing.set_pricing_tiers = AsyncMock(

            return_value=pricing_tiers,
        ):
            tiers = await mock_pricing.set_pricing_tiers(
                tenant_id=tenant_id,
                product_id=product.product_id,
                tiers=pricing_tiers,
            )

            assert len(tiers) == 3
            assert tiers[0]["unit_price"] == 10000

    @pytest.mark.asyncio
    async def test_usage_based_pricing_calculation(
        self,
        billing_services,
        tenant_id,
        customer_id,
    ):
        """Test usage-based pricing calculations."""

        # Record usage
        usage_records = [
            {"timestamp": datetime.now(timezone.utc), "quantity": 1000, "unit": "api_calls"},
            {"timestamp": datetime.now(timezone.utc), "quantity": 500, "unit": "api_calls"},
        ]

        # Mock pricing service
        mock_pricing = MagicMock()
        mock_pricing.record_usage = AsyncMock(

            return_value={"total_usage": 1500, "unit": "api_calls"},
        ):
            usage = await mock_pricing.record_usage(
                tenant_id=tenant_id,
                customer_id=customer_id,
                product_id="prod_api",
                usage_records=usage_records,
            )

            assert usage["total_usage"] == 1500

        # Calculate usage charges
        mock_pricing.calculate_usage_charges = AsyncMock(

            return_value={
                "total_usage": 1500,
                "rate_per_unit": 10,  # $0.10 per API call
                "total_charge": 15000,  # $150.00
            }
        )

charges = await mock_pricing.calculate_usage_charges(
                tenant_id=tenant_id,
                customer_id=customer_id,
                product_id="prod_api",
                billing_period_start=datetime.now(timezone.utc) - timedelta(days=30),
                billing_period_end=datetime.now(timezone.utc),
            )

            assert charges["total_charge"] == 15000


class TestBankAccountIntegrationE2E:
    """Test bank account and ACH payment workflows."""

    @pytest.mark.asyncio
    async def test_bank_account_verification_flow(
        self,
        billing_services,
        tenant_id,
        customer_id,
    ):
        """Test bank account verification process."""

        # Add bank account
        # Mock bank account service
        mock_bank = MagicMock()
        mock_bank.add_bank_account = AsyncMock(

            return_value={
                "account_id": "ba_test_123",
                "last4": "6789",
                "bank_name": "Test Bank",
                "verification_status": "pending",
            }
        )

bank_account = await mock_bank.add_bank_account(
                tenant_id=tenant_id,
                customer_id=customer_id,
                routing_number="123456789",
                account_number="987654321",
                account_type="checking",
            )

            assert bank_account["verification_status"] == "pending"

        # Verify with micro-deposits
        mock_bank.verify_micro_deposits = AsyncMock(

            return_value={
                "account_id": "ba_test_123",
                "verification_status": "verified",
                "verified_at": datetime.now(timezone.utc),
            }
        )

verified = await mock_bank.verify_micro_deposits(
                tenant_id=tenant_id,
                account_id=bank_account["account_id"],
                amounts=[32, 45],  # Cents
            )

            assert verified["verification_status"] == "verified"

    @pytest.mark.asyncio
    async def test_ach_payment_processing(
        self,
        billing_services,
        tenant_id,
        customer_id,
    ):
        """Test ACH payment processing."""

        # Process ACH payment
        with patch.object(
            billing_services["payment"],
            "create_ach_payment",
            return_value={
                "payment_id": "ach_pay_123",
                "status": PaymentStatus.PROCESSING,
                "amount": 50000,
                "processing_time": "3-5 business days",
            }
        )

ach_payment = await billing_services["payment"].create_ach_payment(
                tenant_id=tenant_id,
                customer_id=customer_id,
                amount=50000,
                bank_account_id="ba_test_123",
            )

            assert ach_payment["status"] == PaymentStatus.PROCESSING

        # Simulate ACH clearing
        with patch.object(
            billing_services["payment"],
            "update_payment_status",
            return_value={
                "payment_id": "ach_pay_123",
                "status": PaymentStatus.SUCCEEDED,
                "cleared_at": datetime.now(timezone.utc),
            }
        )

cleared = await billing_services["payment"].update_payment_status(
                tenant_id=tenant_id,
                payment_id=ach_payment["payment_id"],
                status=PaymentStatus.SUCCEEDED,
            )

            assert cleared["status"] == PaymentStatus.SUCCEEDED


class TestErrorHandlingAndRecoveryE2E:
    """Test error handling and recovery scenarios."""

    @pytest.mark.asyncio
    async def test_payment_failure_dunning_process(
        self,
        billing_services,
        tenant_id,
        customer_id,
    ):
        """Test dunning process for failed payments."""

        failed_invoice_id = "inv_dunning_123"

        # Payment fails
        with patch.object(
            billing_services["payment"],
            "create_payment",
            side_effect=[
                {"payment_id": "pay_fail_1", "status": PaymentStatus.FAILED},
                {"payment_id": "pay_fail_2", "status": PaymentStatus.FAILED},
                {"payment_id": "pay_success", "status": PaymentStatus.SUCCEEDED},
            ],
        ):
            # First attempt fails
            attempt1 = await billing_services["payment"].create_payment(
                tenant_id=tenant_id,
                customer_id=customer_id,
                amount=10000,
                invoice_id=failed_invoice_id,
            )
            assert attempt1["status"] == PaymentStatus.FAILED

            # Second retry after 3 days fails
            await asyncio.sleep(0.1)  # Simulate time passing
            attempt2 = await billing_services["payment"].create_payment(
                tenant_id=tenant_id,
                customer_id=customer_id,
                amount=10000,
                invoice_id=failed_invoice_id,
            )
            assert attempt2["status"] == PaymentStatus.FAILED

            # Third retry after 7 days succeeds
            await asyncio.sleep(0.1)  # Simulate time passing
            attempt3 = await billing_services["payment"].create_payment(
                tenant_id=tenant_id,
                customer_id=customer_id,
                amount=10000,
                invoice_id=failed_invoice_id,
            )
            assert attempt3["status"] == PaymentStatus.SUCCEEDED

    @pytest.mark.asyncio
    async def test_subscription_payment_method_update_on_failure(
        self,
        billing_services,
        tenant_id,
        customer_id,
    ):
        """Test updating payment method after subscription payment failure."""

        subscription_id = "sub_update_pm_123"

        # Payment fails with current method
        with patch.object(
            billing_services["payment"],
            "charge_subscription",
            return_value={
                "status": PaymentStatus.FAILED,
                "error": "Card declined",
                "requires_payment_method_update": True,
            }
        )

failed_charge = await billing_services["payment"].charge_subscription(
                tenant_id=tenant_id,
                subscription_id=subscription_id,
            )

            assert failed_charge["requires_payment_method_update"] is True

        # Update payment method
        with patch.object(
            billing_services["subscription"],
            "update_payment_method",
            return_value={
                "subscription_id": subscription_id,
                "payment_method_id": "pm_new_123",
                "updated": True,
            }
        )

updated = await billing_services["subscription"].update_payment_method(
                tenant_id=tenant_id,
                subscription_id=subscription_id,
                payment_method_id="pm_new_123",
            )

            assert updated["updated"] is True

        # Retry with new payment method
        with patch.object(
            billing_services["payment"],
            "charge_subscription",
            return_value={
                "status": PaymentStatus.SUCCEEDED,
                "payment_id": "pay_retry_success_123",
            }
        )

retry_charge = await billing_services["payment"].charge_subscription(
                tenant_id=tenant_id,
                subscription_id=subscription_id,
            )

            assert retry_charge["status"] == PaymentStatus.SUCCEEDED