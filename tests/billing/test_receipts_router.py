"""Tests for billing receipts router."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from dotmac.platform.auth.core import UserInfo
from dotmac.platform.billing.receipts.models import Receipt, ReceiptLineItem
from dotmac.platform.billing.receipts.router import (
    GenerateReceiptForInvoiceRequest,
    GenerateReceiptForPaymentRequest,
    generate_receipt_for_invoice,
    generate_receipt_for_payment,
    get_receipt,
    get_receipt_html,
    get_receipt_pdf,
    list_receipts,
)
from tests.fixtures.async_db import AsyncSessionShim

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _call_with_status(call, *, success_status=200, **kwargs):
    try:
        result = await call(**kwargs)
        return success_status, result
    except HTTPException as exc:
        return exc.status_code, exc


@pytest.fixture
def mock_user():
    return UserInfo(
        user_id="test-user",
        tenant_id="test-tenant",
        email="test@example.com",
        roles=["admin"],
        permissions=["*"],
    )


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def async_db_session(db_session):
    """Provide async-compatible session for billing autouse fixtures."""
    return AsyncSessionShim(db_session)


@pytest.fixture
def mock_receipt():
    """Create mock receipt."""
    return Receipt(
        receipt_id=str(uuid4()),
        receipt_number="RCT-001",
        tenant_id="test-tenant",
        customer_id="customer-123",
        customer_name="Test Customer",
        customer_email="customer@example.com",
        payment_id="payment-123",
        invoice_id="invoice-123",
        currency="USD",
        subtotal=1000,
        tax_amount=0,
        total_amount=1000,
        payment_method="card",
        payment_status="paid",
        line_items=[
            ReceiptLineItem(
                description="Subscription",
                quantity=1,
                unit_price=1000,
                total_price=1000,
            )
        ],
        html_content="<html>Receipt</html>",
        pdf_url="https://example.com/receipt.pdf",
    )


class TestGenerateReceiptForPayment:
    """Test POST /generate/payment endpoint."""

    @patch("dotmac.platform.billing.receipts.router.ReceiptService")
    async def test_generate_receipt_for_payment_success(
        self,
        mock_service_class,
        mock_session,
        mock_user,
        mock_receipt,
    ):
        """Test successful receipt generation for payment."""
        mock_service = AsyncMock()
        mock_service.generate_receipt_for_payment = AsyncMock(return_value=mock_receipt)
        mock_service_class.return_value = mock_service

        request = GenerateReceiptForPaymentRequest(
            payment_id="payment-123",
            include_pdf=True,
            include_html=True,
            send_email=False,
        )

        status_code, receipt = await _call_with_status(
            generate_receipt_for_payment,
            success_status=201,
            receipt_data=request,
            db=mock_session,
            current_user=mock_user,
            tenant_id="test-tenant",
        )

        assert status_code == 201
        assert receipt.receipt_number == "RCT-001"

    @patch("dotmac.platform.billing.receipts.router.ReceiptService")
    async def test_generate_receipt_for_payment_value_error(
        self,
        mock_service_class,
        mock_session,
        mock_user,
    ):
        """Test receipt generation with value error."""
        mock_service = AsyncMock()
        mock_service.generate_receipt_for_payment = AsyncMock(
            side_effect=ValueError("Invalid payment ID")
        )
        mock_service_class.return_value = mock_service

        request = GenerateReceiptForPaymentRequest(
            payment_id="invalid",
            include_pdf=True,
            include_html=True,
        )

        status_code, exc = await _call_with_status(
            generate_receipt_for_payment,
            receipt_data=request,
            db=mock_session,
            current_user=mock_user,
            tenant_id="test-tenant",
        )

        assert status_code == 400
        assert "Invalid payment ID" in exc.detail

    @patch("dotmac.platform.billing.receipts.router.ReceiptService")
    async def test_generate_receipt_for_payment_exception(
        self,
        mock_service_class,
        mock_session,
        mock_user,
    ):
        """Test receipt generation with unexpected exception."""
        mock_service = AsyncMock()
        mock_service.generate_receipt_for_payment = AsyncMock(
            side_effect=Exception("Database error")
        )
        mock_service_class.return_value = mock_service

        request = GenerateReceiptForPaymentRequest(
            payment_id="payment-123",
            include_pdf=True,
            include_html=True,
        )

        status_code, exc = await _call_with_status(
            generate_receipt_for_payment,
            receipt_data=request,
            db=mock_session,
            current_user=mock_user,
            tenant_id="test-tenant",
        )

        assert status_code == 500
        assert "Failed to generate receipt" in exc.detail


class TestGenerateReceiptForInvoice:
    """Test POST /generate/invoice endpoint."""

    @patch("dotmac.platform.billing.receipts.router.ReceiptService")
    async def test_generate_receipt_for_invoice_success(
        self, mock_service_class, mock_session, mock_user, mock_receipt
    ):
        """Test successful receipt generation for invoice."""
        mock_service = AsyncMock()
        mock_service.generate_receipt_for_invoice = AsyncMock(return_value=mock_receipt)
        mock_service_class.return_value = mock_service

        request = GenerateReceiptForInvoiceRequest(
            invoice_id="invoice-123",
            payment_details={"method": "credit_card", "amount": 1000},
            include_pdf=True,
            include_html=True,
        )

        status_code, receipt = await _call_with_status(
            generate_receipt_for_invoice,
            success_status=201,
            receipt_data=request,
            db=mock_session,
            current_user=mock_user,
            tenant_id="test-tenant",
        )

        assert status_code == 201
        assert receipt.receipt_number == "RCT-001"

    @patch("dotmac.platform.billing.receipts.router.ReceiptService")
    async def test_generate_receipt_for_invoice_value_error(
        self, mock_service_class, mock_session, mock_user
    ):
        """Test receipt generation for invoice with value error."""
        mock_service = AsyncMock()
        mock_service.generate_receipt_for_invoice = AsyncMock(
            side_effect=ValueError("Invalid invoice ID")
        )
        mock_service_class.return_value = mock_service

        request = GenerateReceiptForInvoiceRequest(
            invoice_id="invalid",
            payment_details={},
            include_pdf=True,
            include_html=True,
        )

        status_code, exc = await _call_with_status(
            generate_receipt_for_invoice,
            receipt_data=request,
            db=mock_session,
            current_user=mock_user,
            tenant_id="test-tenant",
        )

        assert status_code == 400
        assert "Invalid invoice ID" in exc.detail

    @patch("dotmac.platform.billing.receipts.router.ReceiptService")
    async def test_generate_receipt_for_invoice_exception(
        self, mock_service_class, mock_session, mock_user
    ):
        """Test receipt generation for invoice with exception."""
        mock_service = AsyncMock()
        mock_service.generate_receipt_for_invoice = AsyncMock(
            side_effect=Exception("Service error")
        )
        mock_service_class.return_value = mock_service

        request = GenerateReceiptForInvoiceRequest(
            invoice_id="invoice-123",
            payment_details={},
            include_pdf=True,
            include_html=True,
        )

        status_code, exc = await _call_with_status(
            generate_receipt_for_invoice,
            receipt_data=request,
            db=mock_session,
            current_user=mock_user,
            tenant_id="test-tenant",
        )

        assert status_code == 500
        assert "Failed to generate receipt" in exc.detail


class TestGetReceipt:
    """Test GET /{receipt_id} endpoint."""

    @patch("dotmac.platform.billing.receipts.router.ReceiptService")
    async def test_get_receipt_success(
        self,
        mock_service_class,
        mock_session,
        mock_user,
        mock_receipt,
    ):
        """Test successful receipt retrieval."""
        mock_service = AsyncMock()
        mock_service.get_receipt = AsyncMock(return_value=mock_receipt)
        mock_service_class.return_value = mock_service

        status_code, receipt = await _call_with_status(
            get_receipt,
            receipt_id="receipt-123",
            db=mock_session,
            current_user=mock_user,
            tenant_id="test-tenant",
        )

        assert status_code == 200
        assert receipt.receipt_number == "RCT-001"

    @patch("dotmac.platform.billing.receipts.router.ReceiptService")
    async def test_get_receipt_not_found(
        self, mock_service_class, mock_session, mock_user
    ):
        """Test receipt not found."""
        mock_service = AsyncMock()
        mock_service.get_receipt = AsyncMock(return_value=None)
        mock_service_class.return_value = mock_service

        status_code, exc = await _call_with_status(
            get_receipt,
            receipt_id="nonexistent",
            db=mock_session,
            current_user=mock_user,
            tenant_id="test-tenant",
        )

        assert status_code == 404
        assert "not found" in exc.detail.lower()


class TestListReceipts:
    """Test GET / endpoint."""

    @patch("dotmac.platform.billing.receipts.router.ReceiptService")
    async def test_list_receipts_success(
        self,
        mock_service_class,
        mock_session,
        mock_user,
        mock_receipt,
    ):
        """Test successful receipt listing."""
        mock_service = AsyncMock()
        mock_service.list_receipts = AsyncMock(return_value=[mock_receipt])
        mock_service_class.return_value = mock_service

        status_code, response = await _call_with_status(
            list_receipts,
            customer_id=None,
            payment_id=None,
            invoice_id=None,
            limit=100,
            offset=0,
            db=mock_session,
            current_user=mock_user,
            tenant_id="test-tenant",
        )

        assert status_code == 200
        assert len(response.receipts) == 1
        assert response.total_count == 1
        assert response.has_more is False

    @patch("dotmac.platform.billing.receipts.router.ReceiptService")
    async def test_list_receipts_with_filters(
        self,
        mock_service_class,
        mock_session,
        mock_user,
        mock_receipt,
    ):
        """Test receipt listing with filters."""
        mock_service = AsyncMock()
        mock_service.list_receipts = AsyncMock(return_value=[mock_receipt])
        mock_service_class.return_value = mock_service

        status_code, _ = await _call_with_status(
            list_receipts,
            customer_id="customer-123",
            payment_id="payment-123",
            invoice_id=None,
            limit=50,
            offset=0,
            db=mock_session,
            current_user=mock_user,
            tenant_id="test-tenant",
        )

        assert status_code == 200

    @patch("dotmac.platform.billing.receipts.router.ReceiptService")
    async def test_list_receipts_has_more(
        self,
        mock_service_class,
        mock_session,
        mock_user,
        mock_receipt,
    ):
        """Test receipt listing with has_more flag."""
        # Return limit + 1 receipts to trigger has_more
        receipts = [mock_receipt] * 11
        mock_service = AsyncMock()
        mock_service.list_receipts = AsyncMock(return_value=receipts)
        mock_service_class.return_value = mock_service

        status_code, response = await _call_with_status(
            list_receipts,
            customer_id=None,
            payment_id=None,
            invoice_id=None,
            limit=10,
            offset=0,
            db=mock_session,
            current_user=mock_user,
            tenant_id="test-tenant",
        )

        assert status_code == 200
        assert response.has_more is True
        assert len(response.receipts) == 10


class TestGetReceiptHTML:
    """Test GET /{receipt_id}/html endpoint."""

    @patch("dotmac.platform.billing.receipts.router.ReceiptService")
    async def test_get_receipt_html_success(
        self,
        mock_service_class,
        mock_session,
        mock_user,
        mock_receipt,
    ):
        """Test successful HTML receipt retrieval."""
        mock_service = AsyncMock()
        mock_service.get_receipt = AsyncMock(return_value=mock_receipt)
        mock_service_class.return_value = mock_service

        status_code, response = await _call_with_status(
            get_receipt_html,
            receipt_id="receipt-123",
            db=mock_session,
            current_user=mock_user,
            tenant_id="test-tenant",
        )

        assert status_code == 200
        assert "text/html" in response.media_type

    @patch("dotmac.platform.billing.receipts.router.ReceiptService")
    async def test_get_receipt_html_not_found(
        self, mock_service_class, mock_session, mock_user
    ):
        """Test HTML receipt not found."""
        mock_service = AsyncMock()
        mock_service.get_receipt = AsyncMock(return_value=None)
        mock_service_class.return_value = mock_service

        status_code, _ = await _call_with_status(
            get_receipt_html,
            receipt_id="nonexistent",
            db=mock_session,
            current_user=mock_user,
            tenant_id="test-tenant",
        )

        assert status_code == 404

    @patch("dotmac.platform.billing.receipts.router.ReceiptService")
    async def test_get_receipt_html_generate_on_demand(
        self,
        mock_service_class,
        mock_session,
        mock_user,
        mock_receipt,
    ):
        """Test HTML generation on demand."""
        mock_receipt.html_content = None
        mock_service = AsyncMock()
        mock_service.get_receipt = AsyncMock(return_value=mock_receipt)
        mock_service.html_generator = AsyncMock()
        mock_service.html_generator.generate_html = AsyncMock(return_value="<html>Generated</html>")
        mock_service_class.return_value = mock_service

        status_code, response = await _call_with_status(
            get_receipt_html,
            receipt_id="receipt-123",
            db=mock_session,
            current_user=mock_user,
            tenant_id="test-tenant",
        )

        assert status_code == 200
        assert "<html>Generated</html>" in response.body.decode("utf-8")


class TestGetReceiptPDF:
    """Test GET /{receipt_id}/pdf endpoint."""

    @patch("dotmac.platform.billing.receipts.router.ReceiptService")
    async def test_get_receipt_pdf_success(
        self,
        mock_service_class,
        mock_session,
        mock_user,
        mock_receipt,
    ):
        """Test successful PDF receipt retrieval."""
        mock_service = AsyncMock()
        mock_service.get_receipt = AsyncMock(return_value=mock_receipt)
        mock_service.pdf_generator = AsyncMock()
        mock_service.pdf_generator.generate_pdf = AsyncMock(return_value=b"PDF content")
        mock_service_class.return_value = mock_service

        status_code, response = await _call_with_status(
            get_receipt_pdf,
            receipt_id="receipt-123",
            db=mock_session,
            current_user=mock_user,
            tenant_id="test-tenant",
        )

        assert status_code == 200
        assert response.media_type == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert "RCT-001" in response.headers["content-disposition"]

    @patch("dotmac.platform.billing.receipts.router.ReceiptService")
    async def test_get_receipt_pdf_not_found(
        self, mock_service_class, mock_session, mock_user
    ):
        """Test PDF receipt not found."""
        mock_service = AsyncMock()
        mock_service.get_receipt = AsyncMock(return_value=None)
        mock_service_class.return_value = mock_service

        status_code, _ = await _call_with_status(
            get_receipt_pdf,
            receipt_id="nonexistent",
            db=mock_session,
            current_user=mock_user,
            tenant_id="test-tenant",
        )

        assert status_code == 404
