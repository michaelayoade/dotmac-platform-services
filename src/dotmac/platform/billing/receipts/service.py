"""
Receipt service for generating and managing payment receipts
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dotmac.platform.billing.core.entities import (
    InvoiceEntity,
    PaymentEntity,
)
from dotmac.platform.billing.core.enums import PaymentStatus
from dotmac.platform.billing.metrics import get_billing_metrics
from dotmac.platform.billing.receipts.generators import HTMLReceiptGenerator, PDFReceiptGenerator
from dotmac.platform.billing.receipts.models import Receipt, ReceiptLineItem

logger = logging.getLogger(__name__)


class ReceiptService:
    """Service for generating and managing receipts"""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session
        self.metrics = get_billing_metrics()
        self.pdf_generator = PDFReceiptGenerator()
        self.html_generator = HTMLReceiptGenerator()

    async def generate_receipt_for_payment(
        self,
        tenant_id: str,
        payment_id: str,
        include_pdf: bool = True,
        include_html: bool = True,
        send_email: bool = False,
    ) -> Receipt:
        """Generate receipt for a payment"""

        # Get payment details
        payment = await self._get_payment(tenant_id, payment_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")

        if payment.status != PaymentStatus.SUCCEEDED:
            raise ValueError(f"Cannot generate receipt for payment with status {payment.status}")

        # Get associated invoice if any
        invoice = None
        if payment.invoice_id:
            invoice = await self._get_invoice(tenant_id, payment.invoice_id)

        # Generate receipt number
        receipt_number = await self._generate_receipt_number(tenant_id)

        # Build line items from payment/invoice
        line_items = await self._build_receipt_line_items(payment, invoice)

        # Create receipt
        receipt = Receipt(
            receipt_id=str(uuid4()),
            receipt_number=receipt_number,
            tenant_id=tenant_id,
            payment_id=payment_id,
            invoice_id=payment.invoice_id,
            customer_id=payment.customer_id,
            issue_date=datetime.now(UTC),
            currency=payment.currency,
            subtotal=payment.subtotal or payment.amount,
            tax_amount=payment.tax_amount or 0,
            total_amount=payment.amount,
            payment_method=payment.payment_method,
            payment_status=payment.status.value,
            line_items=line_items,
            customer_name=payment.customer_name or "Customer",
            customer_email=payment.customer_email or "",
            billing_address=payment.billing_address or {},
            notes=payment.notes,
        )

        # Generate PDF if requested
        if include_pdf:
            pdf_content = await self.pdf_generator.generate_pdf(receipt)
            pdf_url = await self._store_pdf(receipt.receipt_id, pdf_content)
            receipt.pdf_url = pdf_url

        # Generate HTML if requested
        if include_html:
            receipt.html_content = await self.html_generator.generate_html(receipt)

        # Send email if requested
        if send_email and receipt.customer_email:
            await self._send_receipt_email(receipt)
            receipt.sent_at = datetime.now(UTC)
            receipt.delivery_method = "email"

        # Record metrics
        self.metrics.record_receipt_generated(
            tenant_id=tenant_id,
            payment_id=payment_id,
            amount=receipt.total_amount,
            currency=receipt.currency,
        )

        logger.info(f"Receipt {receipt.receipt_number} generated for payment {payment_id}")
        return receipt

    async def generate_receipt_for_invoice(
        self,
        tenant_id: str,
        invoice_id: str,
        payment_details: dict[str, Any],
        include_pdf: bool = True,
        include_html: bool = True,
    ) -> Receipt:
        """Generate receipt for an invoice payment"""

        # Get invoice details
        invoice = await self._get_invoice(tenant_id, invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        # Generate receipt number
        receipt_number = await self._generate_receipt_number(tenant_id)

        # Build line items from invoice
        line_items = []
        for item in invoice.line_items:
            line_items.append(
                ReceiptLineItem(
                    line_item_id=item.line_item_id,
                    description=item.description,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price,
                    tax_rate=item.tax_rate,
                    tax_amount=item.tax_amount,
                    product_id=item.product_id,
                    sku=item.sku,
                )
            )

        # Create receipt
        receipt = Receipt(
            receipt_id=str(uuid4()),
            receipt_number=receipt_number,
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            customer_id=invoice.customer_id,
            issue_date=datetime.now(UTC),
            currency=invoice.currency,
            subtotal=invoice.subtotal,
            tax_amount=invoice.tax_amount,
            total_amount=invoice.total_amount,
            payment_method=payment_details.get("method", "unknown"),
            payment_status="completed",
            line_items=line_items,
            customer_name=invoice.customer_name,
            customer_email=invoice.billing_email,
            billing_address=invoice.billing_address,
            notes=invoice.notes,
        )

        # Generate content if requested
        if include_pdf:
            pdf_content = await self.pdf_generator.generate_pdf(receipt)
            pdf_url = await self._store_pdf(receipt.receipt_id, pdf_content)
            receipt.pdf_url = pdf_url

        if include_html:
            receipt.html_content = await self.html_generator.generate_html(receipt)

        logger.info(f"Receipt {receipt.receipt_number} generated for invoice {invoice_id}")
        return receipt

    async def get_receipt(self, tenant_id: str, receipt_id: str) -> Receipt | None:
        """Get receipt by ID (this would typically be stored in database)"""
        # In a real implementation, this would query a receipts table
        # For now, this is a placeholder
        logger.warning("Receipt storage not implemented - receipts are generated on demand")
        return None

    async def list_receipts(
        self,
        tenant_id: str,
        customer_id: str | None = None,
        payment_id: str | None = None,
        invoice_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Receipt]:
        """List receipts with filtering"""
        # In a real implementation, this would query a receipts table
        # For now, this is a placeholder
        logger.warning("Receipt storage not implemented - use payment/invoice queries instead")
        return []

    # ============================================================================
    # Private helper methods
    # ============================================================================

    async def _get_payment(self, tenant_id: str, payment_id: str) -> PaymentEntity | None:
        """Get payment entity"""
        stmt = select(PaymentEntity).where(
            and_(
                PaymentEntity.tenant_id == tenant_id,
                PaymentEntity.payment_id == payment_id,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_invoice(self, tenant_id: str, invoice_id: str) -> InvoiceEntity | None:
        """Get invoice entity"""
        stmt = (
            select(InvoiceEntity)
            .where(
                and_(
                    InvoiceEntity.tenant_id == tenant_id,
                    InvoiceEntity.invoice_id == invoice_id,
                )
            )
            .options(selectinload(InvoiceEntity.line_items))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _generate_receipt_number(self, tenant_id: str) -> str:
        """Generate unique receipt number"""
        # This would typically query the database for the last receipt number
        # For now, generate a simple sequential number
        from datetime import datetime

        year = datetime.now(UTC).year
        # In production, this would be atomic and check existing numbers
        sequence = 1
        return f"REC-{year}-{sequence:06d}"

    async def _build_receipt_line_items(
        self, payment: PaymentEntity, invoice: InvoiceEntity | None
    ) -> list[ReceiptLineItem]:
        """Build receipt line items from payment/invoice data"""
        line_items = []

        if invoice and invoice.line_items:
            # Use invoice line items
            for item in invoice.line_items:
                line_items.append(
                    ReceiptLineItem(
                        line_item_id=item.line_item_id,
                        description=item.description,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        total_price=item.total_price,
                        tax_rate=item.tax_rate,
                        tax_amount=item.tax_amount,
                        product_id=item.product_id,
                    )
                )
        else:
            # Create simple line item from payment
            line_items.append(
                ReceiptLineItem(
                    description=f"Payment {payment.payment_id}",
                    quantity=1,
                    unit_price=payment.amount,
                    total_price=payment.amount,
                )
            )

        return line_items

    async def _store_pdf(self, receipt_id: str, pdf_content: bytes) -> str:
        """Store PDF content and return URL"""
        # In a real implementation, this would store in S3, filesystem, etc.
        # For now, return a placeholder URL
        return f"/api/receipts/{receipt_id}/pdf"

    async def _send_receipt_email(self, receipt: Receipt) -> None:
        """Send receipt via email"""
        # In a real implementation, this would use an email service
        logger.info(f"Would send receipt {receipt.receipt_number} to {receipt.customer_email}")
