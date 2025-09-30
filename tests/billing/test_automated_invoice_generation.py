"""
Automated invoice generation testing.
Tests invoice creation, scheduling, formatting, and delivery.
"""

import pytest
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta
from decimal import Decimal
import asyncio
from freezegun import freeze_time

from dotmac.platform.billing.models import (
    Customer, Subscription, Invoice, InvoiceItem, Product, Price
)
from dotmac.platform.billing.services.invoice_generator import InvoiceGenerator
from dotmac.platform.billing.services.pdf_generator import PDFGenerator


@pytest.fixture
async def invoice_test_data(db):
    """Create test data for invoice generation."""
    # Create product and price
    product = Product(
        name="Professional Plan",
        description="Advanced features",
        stripe_product_id="prod_test123"
    )
    db.add(product)
    await db.commit()

    price = Price(
        product_id=product.id,
        stripe_price_id="price_test123",
        amount=2999,  # $29.99
        currency="USD",
        interval="month"
    )
    db.add(price)
    await db.commit()

    # Create customer
    customer = Customer(
        user_id="test_user_123",
        stripe_customer_id="cus_test123",
        email="test@example.com",
        name="Test Customer",
        billing_address={
            "line1": "123 Test Street",
            "city": "Test City",
            "state": "CA",
            "postal_code": "12345",
            "country": "US"
        }
    )
    db.add(customer)
    await db.commit()

    # Create subscription
    subscription = Subscription(
        customer_id=customer.id,
        price_id=price.id,
        stripe_subscription_id="sub_test123",
        status="active",
        current_period_start=datetime(2024, 1, 1),
        current_period_end=datetime(2024, 2, 1)
    )
    db.add(subscription)
    await db.commit()

    return {
        "customer": customer,
        "subscription": subscription,
        "product": product,
        "price": price
    }


class TestInvoiceGeneration:
    """Test automatic invoice generation."""

    @pytest.mark.asyncio
    async def test_monthly_invoice_generation(self, db, invoice_test_data):
        """Test monthly recurring invoice generation."""
        data = invoice_test_data
        generator = InvoiceGenerator(db)

        # Freeze time to billing date
        with freeze_time("2024-02-01T00:00:00Z"):
            invoices = await generator.generate_monthly_invoices()

            assert len(invoices) == 1
            invoice = invoices[0]

            assert invoice.customer_id == data["customer"].id
            assert invoice.subscription_id == data["subscription"].id
            assert invoice.amount_total == 2999
            assert invoice.currency == "USD"
            assert invoice.status == "draft"

    @pytest.mark.asyncio
    async def test_usage_based_invoice_calculation(self, db, invoice_test_data):
        """Test usage-based billing in invoice generation."""
        from dotmac.platform.billing.models import UsageRecord

        data = invoice_test_data
        customer = data["customer"]

        # Create usage records
        usage_records = [
            UsageRecord(
                customer_id=customer.id,
                metric="api_calls",
                quantity=15000,  # Over 10k limit
                recorded_at=datetime(2024, 1, 15)
            ),
            UsageRecord(
                customer_id=customer.id,
                metric="storage_gb",
                quantity=150,  # Over 100GB limit
                recorded_at=datetime(2024, 1, 20)
            )
        ]

        for record in usage_records:
            db.add(record)
        await db.commit()

        generator = InvoiceGenerator(db)

        # Generate invoice with usage
        with freeze_time("2024-02-01T00:00:00Z"):
            invoice = await generator.generate_invoice_with_usage(
                customer.id,
                billing_period_start=datetime(2024, 1, 1),
                billing_period_end=datetime(2024, 2, 1)
            )

            # Should include base subscription + overage charges
            assert invoice.amount_total > 2999  # Base price + overages

            # Check invoice items
            items = await db.execute(
                "SELECT * FROM invoice_items WHERE invoice_id = ?",
                (invoice.id,)
            )
            invoice_items = items.fetchall()

            # Should have base subscription + usage items
            assert len(invoice_items) >= 3  # Base + API + Storage overage

            # Verify overage calculations
            api_overage_item = next(
                (item for item in invoice_items if "API" in item.description),
                None
            )
            assert api_overage_item is not None
            assert api_overage_item.quantity == 5000  # 15k - 10k limit

    @pytest.mark.asyncio
    async def test_proration_calculation(self, db, invoice_test_data):
        """Test prorated billing for mid-cycle changes."""
        data = invoice_test_data
        subscription = data["subscription"]

        # Simulate plan upgrade mid-cycle
        upgrade_date = datetime(2024, 1, 15)  # Half-way through month
        old_amount = 2999  # $29.99
        new_amount = 9999  # $99.99

        generator = InvoiceGenerator(db)

        proration = await generator.calculate_proration(
            subscription_id=subscription.id,
            old_amount=old_amount,
            new_amount=new_amount,
            change_date=upgrade_date,
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 2, 1)
        )

        # Should prorate for remaining days in period
        days_remaining = (datetime(2024, 2, 1) - upgrade_date).days
        total_days = (datetime(2024, 2, 1) - datetime(2024, 1, 1)).days

        expected_proration = ((new_amount - old_amount) * days_remaining) // total_days

        assert abs(proration - expected_proration) <= 100  # Allow small rounding difference

    @pytest.mark.asyncio
    async def test_invoice_numbering_sequence(self, db, invoice_test_data):
        """Test invoice numbers are sequential and unique."""
        data = invoice_test_data
        generator = InvoiceGenerator(db)

        # Generate multiple invoices
        invoices = []
        for i in range(5):
            with freeze_time(f"2024-0{i+1}-01T00:00:00Z"):
                invoice = await generator.generate_invoice(
                    customer_id=data["customer"].id,
                    amount=1000 + i * 500
                )
                invoices.append(invoice)

        # Check numbers are sequential
        numbers = [invoice.invoice_number for invoice in invoices]
        assert len(set(numbers)) == 5  # All unique

        # Should follow format INV-YYYY-NNN
        import re
        for number in numbers:
            assert re.match(r"INV-\d{4}-\d{3,}", number)

        # Should be in order
        for i in range(1, len(numbers)):
            current_num = int(numbers[i].split('-')[-1])
            previous_num = int(numbers[i-1].split('-')[-1])
            assert current_num > previous_num

    @pytest.mark.asyncio
    async def test_tax_calculation_in_invoices(self, db, invoice_test_data):
        """Test tax calculations are included in invoices."""
        from dotmac.platform.billing.services.tax_calculator import TaxCalculator

        data = invoice_test_data
        customer = data["customer"]

        # Update customer with tax location
        customer.billing_address["state"] = "CA"  # California has tax
        db.add(customer)
        await db.commit()

        generator = InvoiceGenerator(db)

        with patch.object(TaxCalculator, 'calculate_tax') as mock_tax:
            mock_tax.return_value = {
                "amount": 240,  # $2.40 tax on $29.99
                "rate": 0.08,   # 8% tax rate
                "jurisdiction": "CA"
            }

            invoice = await generator.generate_invoice_with_tax(
                customer_id=customer.id,
                subtotal=2999
            )

            # Should include tax
            assert invoice.tax_amount == 240
            assert invoice.amount_total == 2999 + 240  # Subtotal + tax

            # Verify tax calculation was called
            mock_tax.assert_called_once()

    @pytest.mark.asyncio
    async def test_invoice_scheduling(self, db, invoice_test_data):
        """Test invoice scheduling for future billing dates."""
        from dotmac.platform.billing.scheduler import InvoiceScheduler

        data = invoice_test_data
        scheduler = InvoiceScheduler(db)

        # Schedule monthly invoices for next 3 months
        future_dates = [
            datetime(2024, 2, 1),
            datetime(2024, 3, 1),
            datetime(2024, 4, 1)
        ]

        scheduled_count = 0
        for date in future_dates:
            with freeze_time(date):
                result = await scheduler.schedule_subscription_invoices()
                scheduled_count += len(result)

        assert scheduled_count == 3

        # Check scheduled invoices exist
        scheduled_invoices = await db.execute(
            "SELECT * FROM invoices WHERE status = 'scheduled'"
        )
        invoices = scheduled_invoices.fetchall()
        assert len(invoices) >= 3

    @pytest.mark.asyncio
    async def test_failed_payment_retry_invoices(self, db, invoice_test_data):
        """Test retry invoices for failed payments."""
        data = invoice_test_data
        customer = data["customer"]

        # Create failed invoice
        failed_invoice = Invoice(
            customer_id=customer.id,
            subscription_id=data["subscription"].id,
            stripe_invoice_id="in_failed_123",
            amount_total=2999,
            status="payment_failed",
            attempt_count=1,
            next_payment_attempt=datetime.now() + timedelta(days=3)
        )
        db.add(failed_invoice)
        await db.commit()

        generator = InvoiceGenerator(db)

        # Process retry
        with freeze_time(datetime.now() + timedelta(days=4)):
            retry_results = await generator.process_payment_retries()

            assert len(retry_results) == 1
            result = retry_results[0]

            # Should update attempt count
            await db.refresh(failed_invoice)
            assert failed_invoice.attempt_count == 2

    @pytest.mark.asyncio
    async def test_invoice_finalization(self, db, invoice_test_data):
        """Test invoice finalization process."""
        data = invoice_test_data
        generator = InvoiceGenerator(db)

        # Create draft invoice
        draft_invoice = Invoice(
            customer_id=data["customer"].id,
            stripe_invoice_id="in_draft_123",
            amount_total=2999,
            status="draft"
        )
        db.add(draft_invoice)
        await db.commit()

        # Add items to invoice
        invoice_items = [
            InvoiceItem(
                invoice_id=draft_invoice.id,
                description="Professional Plan - Monthly",
                amount=2999,
                quantity=1
            )
        ]

        for item in invoice_items:
            db.add(item)
        await db.commit()

        # Finalize invoice
        finalized = await generator.finalize_invoice(draft_invoice.id)

        assert finalized.status == "open"
        assert finalized.invoice_number is not None
        assert finalized.finalized_at is not None

    @pytest.mark.asyncio
    async def test_bulk_invoice_generation(self, db):
        """Test generating invoices for multiple customers at once."""
        # Create multiple customers and subscriptions
        customers = []
        for i in range(10):
            customer = Customer(
                user_id=f"bulk_user_{i}",
                stripe_customer_id=f"cus_bulk_{i}",
                email=f"bulk{i}@example.com",
                name=f"Bulk Customer {i}"
            )
            db.add(customer)
            customers.append(customer)

        await db.commit()

        # Create subscriptions
        subscriptions = []
        for i, customer in enumerate(customers):
            subscription = Subscription(
                customer_id=customer.id,
                stripe_subscription_id=f"sub_bulk_{i}",
                status="active",
                current_period_start=datetime(2024, 1, 1),
                current_period_end=datetime(2024, 2, 1)
            )
            db.add(subscription)
            subscriptions.append(subscription)

        await db.commit()

        generator = InvoiceGenerator(db)

        # Generate bulk invoices
        with freeze_time("2024-02-01T00:00:00Z"):
            invoices = await generator.generate_bulk_invoices(
                customer_ids=[c.id for c in customers]
            )

            assert len(invoices) == 10

            # All should be created successfully
            for invoice in invoices:
                assert invoice.id is not None
                assert invoice.amount_total > 0


class TestInvoicePDFGeneration:
    """Test PDF invoice generation."""

    @pytest.mark.asyncio
    async def test_pdf_generation_basic(self, db, invoice_test_data):
        """Test basic PDF generation for invoice."""
        data = invoice_test_data
        customer = data["customer"]

        # Create invoice with items
        invoice = Invoice(
            customer_id=customer.id,
            invoice_number="INV-2024-001",
            amount_total=2999,
            tax_amount=240,
            status="paid",
            paid_at=datetime.now()
        )
        db.add(invoice)
        await db.commit()

        # Add invoice item
        item = InvoiceItem(
            invoice_id=invoice.id,
            description="Professional Plan - Monthly",
            amount=2999,
            quantity=1
        )
        db.add(item)
        await db.commit()

        pdf_generator = PDFGenerator()

        # Generate PDF
        pdf_data = await pdf_generator.generate_invoice_pdf(invoice.id)

        assert pdf_data is not None
        assert len(pdf_data) > 1000  # Should be reasonable PDF size
        assert pdf_data.startswith(b'%PDF')  # PDF header

    @pytest.mark.asyncio
    async def test_pdf_content_validation(self, db, invoice_test_data):
        """Test PDF contains correct invoice information."""
        # This would require a PDF parsing library like PyPDF2
        pytest.skip("PDF content validation requires PyPDF2 - implement if needed")

    @pytest.mark.asyncio
    async def test_pdf_generation_performance(self, db, invoice_test_data):
        """Test PDF generation performance."""
        import time

        data = invoice_test_data
        invoices = []

        # Create 10 test invoices
        for i in range(10):
            invoice = Invoice(
                customer_id=data["customer"].id,
                invoice_number=f"INV-2024-{i:03d}",
                amount_total=2999,
                status="paid"
            )
            db.add(invoice)
            invoices.append(invoice)

        await db.commit()

        pdf_generator = PDFGenerator()

        # Generate PDFs and measure time
        start_time = time.time()

        pdf_tasks = [
            pdf_generator.generate_invoice_pdf(invoice.id)
            for invoice in invoices
        ]

        pdfs = await asyncio.gather(*pdf_tasks)

        end_time = time.time()
        duration = end_time - start_time

        # Should generate all PDFs reasonably quickly
        assert duration < 10.0  # 10 seconds for 10 PDFs
        assert all(pdf is not None for pdf in pdfs)
        assert all(len(pdf) > 100 for pdf in pdfs)


class TestInvoiceDelivery:
    """Test invoice delivery and notifications."""

    @pytest.mark.asyncio
    async def test_email_invoice_delivery(self, db, invoice_test_data):
        """Test invoice delivery via email."""
        from dotmac.platform.billing.services.invoice_delivery import InvoiceDelivery

        data = invoice_test_data
        invoice = Invoice(
            customer_id=data["customer"].id,
            invoice_number="INV-2024-001",
            amount_total=2999,
            status="open"
        )
        db.add(invoice)
        await db.commit()

        delivery_service = InvoiceDelivery()

        with patch.object(delivery_service, 'send_email') as mock_email:
            mock_email.return_value = True

            result = await delivery_service.deliver_invoice_email(invoice.id)

            assert result is True
            mock_email.assert_called_once()

            # Verify email content
            call_args = mock_email.call_args
            assert data["customer"].email in str(call_args)
            assert "INV-2024-001" in str(call_args)

    @pytest.mark.asyncio
    async def test_payment_reminder_scheduling(self, db, invoice_test_data):
        """Test payment reminder scheduling."""
        from dotmac.platform.billing.scheduler import PaymentReminderScheduler

        data = invoice_test_data

        # Create overdue invoice
        overdue_invoice = Invoice(
            customer_id=data["customer"].id,
            invoice_number="INV-2024-OVERDUE",
            amount_total=2999,
            status="open",
            due_date=datetime.now() - timedelta(days=5)  # 5 days overdue
        )
        db.add(overdue_invoice)
        await db.commit()

        scheduler = PaymentReminderScheduler()

        # Process overdue invoices
        reminders_sent = await scheduler.send_overdue_reminders()

        assert len(reminders_sent) == 1
        assert reminders_sent[0]["invoice_id"] == overdue_invoice.id

    @pytest.mark.asyncio
    async def test_webhook_notification_on_invoice_events(self, db, invoice_test_data):
        """Test webhook notifications for invoice events."""
        from dotmac.platform.billing.webhooks import InvoiceWebhookService

        data = invoice_test_data
        webhook_service = InvoiceWebhookService()

        with patch.object(webhook_service, 'send_webhook') as mock_webhook:
            mock_webhook.return_value = True

            # Simulate invoice paid event
            invoice = Invoice(
                customer_id=data["customer"].id,
                amount_total=2999,
                status="paid",
                paid_at=datetime.now()
            )
            db.add(invoice)
            await db.commit()

            # Trigger webhook
            await webhook_service.notify_invoice_paid(invoice.id)

            mock_webhook.assert_called_once()
            webhook_data = mock_webhook.call_args[1]["data"]

            assert webhook_data["event_type"] == "invoice.paid"
            assert webhook_data["invoice"]["id"] == invoice.id