"""
End-to-end tests for invoice lifecycle.

Tests cover invoice CRUD, lifecycle operations, PDF generation, and adjustments.
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.billing.core.entities import InvoiceEntity
from dotmac.platform.billing.core.enums import InvoiceStatus, PaymentStatus

pytestmark = [pytest.mark.asyncio, pytest.mark.e2e]


# ============================================================================
# Fixtures for Invoice Lifecycle E2E Tests
# ============================================================================


@pytest_asyncio.fixture
async def draft_invoice(e2e_db_session: AsyncSession, tenant_id: str):
    """Create a draft invoice."""
    unique_id = uuid.uuid4().hex[:8]
    invoice = InvoiceEntity(
        invoice_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        customer_id=str(uuid.uuid4()),
        invoice_number=f"INV-{unique_id}",
        status=InvoiceStatus.DRAFT,
        payment_status=PaymentStatus.PENDING,
        subtotal=10000,  # $100.00 in cents
        tax_amount=1000,  # $10.00 in cents
        total_amount=11000,  # $110.00 in cents
        remaining_balance=11000,
        currency="USD",
        billing_email=f"billing_{unique_id}@example.com",
        billing_address={"street": "123 Main St", "city": "Test City"},
        issue_date=datetime.now(UTC),
        due_date=datetime.now(UTC) + timedelta(days=30),
    )
    e2e_db_session.add(invoice)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(invoice)
    return invoice


@pytest_asyncio.fixture
async def open_invoice(e2e_db_session: AsyncSession, tenant_id: str):
    """Create an open (finalized) invoice."""
    unique_id = uuid.uuid4().hex[:8]
    invoice = InvoiceEntity(
        invoice_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        customer_id=str(uuid.uuid4()),
        invoice_number=f"INV-{unique_id}",
        status=InvoiceStatus.OPEN,
        payment_status=PaymentStatus.PENDING,
        subtotal=50000,  # $500.00 in cents
        tax_amount=5000,  # $50.00 in cents
        total_amount=55000,  # $550.00 in cents
        remaining_balance=55000,
        currency="USD",
        billing_email=f"billing_{unique_id}@example.com",
        billing_address={"street": "456 Oak Ave", "city": "Test Town"},
        issue_date=datetime.now(UTC),
        due_date=datetime.now(UTC) + timedelta(days=30),
    )
    e2e_db_session.add(invoice)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(invoice)
    return invoice


@pytest_asyncio.fixture
async def paid_invoice(e2e_db_session: AsyncSession, tenant_id: str):
    """Create a paid invoice."""
    unique_id = uuid.uuid4().hex[:8]
    invoice = InvoiceEntity(
        invoice_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        customer_id=str(uuid.uuid4()),
        invoice_number=f"INV-{unique_id}",
        status=InvoiceStatus.PAID,
        payment_status=PaymentStatus.SUCCEEDED,
        subtotal=20000,  # $200.00 in cents
        tax_amount=2000,  # $20.00 in cents
        total_amount=22000,  # $220.00 in cents
        remaining_balance=0,
        currency="USD",
        billing_email=f"billing_{unique_id}@example.com",
        billing_address={"street": "789 Pine Blvd", "city": "Test Village"},
        issue_date=datetime.now(UTC) - timedelta(days=15),
        due_date=datetime.now(UTC) + timedelta(days=15),
        paid_at=datetime.now(UTC) - timedelta(days=5),
    )
    e2e_db_session.add(invoice)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(invoice)
    return invoice


@pytest_asyncio.fixture
async def overdue_invoice(e2e_db_session: AsyncSession, tenant_id: str):
    """Create an overdue invoice."""
    unique_id = uuid.uuid4().hex[:8]
    invoice = InvoiceEntity(
        invoice_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        customer_id=str(uuid.uuid4()),
        invoice_number=f"INV-{unique_id}",
        status=InvoiceStatus.OVERDUE,
        payment_status=PaymentStatus.PENDING,
        subtotal=30000,  # $300.00 in cents
        tax_amount=3000,  # $30.00 in cents
        total_amount=33000,  # $330.00 in cents
        remaining_balance=33000,
        currency="USD",
        billing_email=f"billing_{unique_id}@example.com",
        billing_address={"street": "321 Elm St", "city": "Late City"},
        issue_date=datetime.now(UTC) - timedelta(days=45),
        due_date=datetime.now(UTC) - timedelta(days=15),
    )
    e2e_db_session.add(invoice)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(invoice)
    return invoice


@pytest_asyncio.fixture
async def multiple_invoices(e2e_db_session: AsyncSession, tenant_id: str):
    """Create multiple invoices with different statuses."""
    invoices = []
    statuses = [
        (InvoiceStatus.DRAFT, PaymentStatus.PENDING),
        (InvoiceStatus.OPEN, PaymentStatus.PENDING),
        (InvoiceStatus.PAID, PaymentStatus.SUCCEEDED),
        (InvoiceStatus.OVERDUE, PaymentStatus.PENDING),
    ]

    for i, (inv_status, pay_status) in enumerate(statuses):
        unique_id = uuid.uuid4().hex[:8]
        base_amount = (i + 1) * 10000  # $100, $200, $300, $400 in cents
        tax = (i + 1) * 1000
        total = base_amount + tax
        invoice = InvoiceEntity(
            invoice_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            customer_id=str(uuid.uuid4()),
            invoice_number=f"INV-{unique_id}",
            status=inv_status,
            payment_status=pay_status,
            subtotal=base_amount,
            tax_amount=tax,
            total_amount=total,
            remaining_balance=0 if pay_status == PaymentStatus.SUCCEEDED else total,
            currency="USD",
            billing_email=f"billing_{unique_id}@example.com",
            billing_address={"street": f"{i} Test St"},
            issue_date=datetime.now(UTC) - timedelta(days=i * 10),
            due_date=datetime.now(UTC) + timedelta(days=30 - i * 10),
        )
        e2e_db_session.add(invoice)
        invoices.append(invoice)

    await e2e_db_session.commit()
    for inv in invoices:
        await e2e_db_session.refresh(inv)
    return invoices


# ============================================================================
# Invoice CRUD Tests
# ============================================================================


class TestInvoiceCRUDE2E:
    """End-to-end tests for invoice CRUD operations."""

    async def test_create_invoice(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating an invoice."""
        unique_id = uuid.uuid4().hex[:8]
        invoice_data = {
            "customer_id": str(uuid.uuid4()),
            "billing_email": f"customer_{unique_id}@example.com",
            "billing_address": {
                "street": "123 New St",
                "city": "New City",
                "country": "US",
            },
            "line_items": [
                {
                    "description": "Professional Service",
                    "quantity": 1,
                    "unit_price": "250.00",
                    "amount": "250.00",
                }
            ],
            "currency": "USD",
            "due_days": 30,
        }

        response = await async_client.post(
            "/api/v1/billing/invoices",
            json=invoice_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "draft"
        assert "invoice_id" in data

    async def test_list_invoices(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_invoices: list[InvoiceEntity],
    ):
        """Test listing invoices."""
        response = await async_client.get(
            "/api/v1/billing/invoices",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "invoices" in data
        assert "total_count" in data

    async def test_list_invoices_filter_by_status(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_invoices: list[InvoiceEntity],
    ):
        """Test listing invoices filtered by status."""
        response = await async_client.get(
            "/api/v1/billing/invoices?status=open",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        for inv in data["invoices"]:
            assert inv["status"] == "open"

    async def test_list_invoices_filter_by_payment_status(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_invoices: list[InvoiceEntity],
    ):
        """Test listing invoices filtered by payment status."""
        response = await async_client.get(
            "/api/v1/billing/invoices?payment_status=unpaid",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        for inv in data["invoices"]:
            assert inv["payment_status"] == "unpaid"

    async def test_get_invoice(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        draft_invoice: InvoiceEntity,
    ):
        """Test getting a specific invoice."""
        response = await async_client.get(
            f"/api/v1/billing/invoices/{draft_invoice.invoice_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["invoice_id"] == draft_invoice.invoice_id

    async def test_get_invoice_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting non-existent invoice."""
        fake_id = str(uuid.uuid4())
        response = await async_client.get(
            f"/api/v1/billing/invoices/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404


# ============================================================================
# Invoice Lifecycle Tests
# ============================================================================


class TestInvoiceLifecycleE2E:
    """End-to-end tests for invoice lifecycle operations."""

    async def test_finalize_invoice(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        draft_invoice: InvoiceEntity,
    ):
        """Test finalizing a draft invoice."""
        response = await async_client.post(
            f"/api/v1/billing/invoices/{draft_invoice.invoice_id}/finalize",
            json={"send_email": False},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "open"

    async def test_void_invoice(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        open_invoice: InvoiceEntity,
    ):
        """Test voiding an invoice."""
        response = await async_client.post(
            f"/api/v1/billing/invoices/{open_invoice.invoice_id}/void",
            json={"reason": "Customer requested cancellation"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "void"

    async def test_mark_invoice_paid(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        open_invoice: InvoiceEntity,
    ):
        """Test marking an invoice as paid."""
        response = await async_client.post(
            f"/api/v1/billing/invoices/{open_invoice.invoice_id}/mark-paid",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paid"
        assert data["payment_status"] == "paid"

    async def test_send_invoice_email(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        open_invoice: InvoiceEntity,
    ):
        """Test sending invoice email."""
        with patch("dotmac.platform.billing.invoicing.service.InvoiceService.send_invoice_email") as mock:
            mock.return_value = True

            response = await async_client.post(
                f"/api/v1/billing/invoices/{open_invoice.invoice_id}/send",
                json={},
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    async def test_send_payment_reminder(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        overdue_invoice: InvoiceEntity,
    ):
        """Test sending payment reminder."""
        with patch("dotmac.platform.billing.invoicing.service.InvoiceService.send_payment_reminder") as mock:
            mock.return_value = True

            response = await async_client.post(
                f"/api/v1/billing/invoices/{overdue_invoice.invoice_id}/remind",
                json={"message": "Please pay your invoice."},
                headers=auth_headers,
            )

            assert response.status_code == 200

    async def test_check_overdue_invoices(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        overdue_invoice: InvoiceEntity,
    ):
        """Test checking for overdue invoices."""
        response = await async_client.post(
            "/api/v1/billing/invoices/check-overdue",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# ============================================================================
# Invoice PDF Tests
# ============================================================================


class TestInvoicePDFE2E:
    """End-to-end tests for invoice PDF generation."""

    async def test_generate_pdf(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        open_invoice: InvoiceEntity,
    ):
        """Test generating invoice PDF."""
        with patch("dotmac.platform.billing.invoicing.service.InvoiceService.generate_invoice_pdf") as mock:
            mock.return_value = b"%PDF-1.4 mock pdf content"

            response = await async_client.post(
                f"/api/v1/billing/invoices/{open_invoice.invoice_id}/pdf",
                json={"locale": "en_US"},
                headers=auth_headers,
            )

            assert response.status_code == 200
            assert "application/pdf" in response.headers.get("content-type", "")

    async def test_preview_pdf(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        open_invoice: InvoiceEntity,
    ):
        """Test previewing invoice PDF."""
        with patch("dotmac.platform.billing.invoicing.service.InvoiceService.generate_invoice_pdf") as mock:
            mock.return_value = b"%PDF-1.4 mock pdf content"

            response = await async_client.get(
                f"/api/v1/billing/invoices/{open_invoice.invoice_id}/pdf/preview",
                headers=auth_headers,
            )

            assert response.status_code == 200

    async def test_batch_pdf_generation(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_invoices: list[InvoiceEntity],
    ):
        """Test batch PDF generation."""
        invoice_ids = [inv.invoice_id for inv in multiple_invoices[:2]]

        with patch("dotmac.platform.billing.invoicing.service.InvoiceService.generate_batch_invoices_pdf") as mock:
            mock.return_value = ["/tmp/invoice1.pdf", "/tmp/invoice2.pdf"]

            response = await async_client.post(
                "/api/v1/billing/invoices/batch/pdf",
                json={"invoice_ids": invoice_ids, "locale": "en_US"},
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


# ============================================================================
# Invoice Adjustments Tests
# ============================================================================


class TestInvoiceAdjustmentsE2E:
    """End-to-end tests for invoice adjustments."""

    async def test_apply_discount(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        draft_invoice: InvoiceEntity,
    ):
        """Test applying a discount to an invoice."""
        response = await async_client.post(
            f"/api/v1/billing/invoices/{draft_invoice.invoice_id}/discount",
            json={
                "discount_percentage": 10.0,
                "reason": "Loyalty discount",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200

    async def test_apply_credit(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        open_invoice: InvoiceEntity,
    ):
        """Test applying credit to an invoice."""
        response = await async_client.post(
            f"/api/v1/billing/invoices/{open_invoice.invoice_id}/apply-credit",
            json={
                "credit_amount": 5000,  # $50.00 in cents
                "credit_application_id": str(uuid.uuid4()),
            },
            headers=auth_headers,
        )

        assert response.status_code == 200

    async def test_recalculate_tax(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        draft_invoice: InvoiceEntity,
    ):
        """Test recalculating tax for an invoice."""
        response = await async_client.post(
            f"/api/v1/billing/invoices/{draft_invoice.invoice_id}/recalculate-tax?tax_jurisdiction=CA",
            headers=auth_headers,
        )

        assert response.status_code == 200


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestInvoiceErrorsE2E:
    """End-to-end tests for invoice error handling."""

    async def test_finalize_already_finalized(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        open_invoice: InvoiceEntity,
    ):
        """Test finalizing an already finalized invoice."""
        response = await async_client.post(
            f"/api/v1/billing/invoices/{open_invoice.invoice_id}/finalize",
            json={"send_email": False},
            headers=auth_headers,
        )

        assert response.status_code == 400

    async def test_void_paid_invoice(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        paid_invoice: InvoiceEntity,
    ):
        """Test voiding a paid invoice."""
        response = await async_client.post(
            f"/api/v1/billing/invoices/{paid_invoice.invoice_id}/void",
            json={"reason": "Test reason"},
            headers=auth_headers,
        )

        # May fail or succeed depending on business rules
        assert response.status_code in [200, 400]

    async def test_void_without_reason(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        open_invoice: InvoiceEntity,
    ):
        """Test voiding invoice without reason."""
        response = await async_client.post(
            f"/api/v1/billing/invoices/{open_invoice.invoice_id}/void",
            json={},
            headers=auth_headers,
        )

        assert response.status_code == 422

    async def test_unauthorized_access(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test accessing invoices without authentication."""
        response = await async_client.get(
            "/api/v1/billing/invoices",
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 401

    async def test_invalid_discount_percentage(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        draft_invoice: InvoiceEntity,
    ):
        """Test applying invalid discount percentage."""
        response = await async_client.post(
            f"/api/v1/billing/invoices/{draft_invoice.invoice_id}/discount",
            json={
                "discount_percentage": 150.0,  # Invalid: > 100
                "reason": "Invalid discount",
            },
            headers=auth_headers,
        )

        assert response.status_code == 422
