"""
Query Handlers - Execute queries and return read models

Handlers optimize for read performance using:
1. Denormalized read models
2. Caching strategies
3. Database query optimization
4. Minimal data transformation
"""

from datetime import UTC, datetime

import structlog
from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dotmac.platform.billing.core.entities import (
    InvoiceEntity,
    PaymentEntity,
)
from dotmac.platform.billing.core.enums import InvoiceStatus, PaymentStatus
from dotmac.platform.billing.models import BillingSubscriptionTable
from dotmac.platform.billing.read_models.invoice_read_models import (
    InvoiceDetail,
    InvoiceListItem,
    InvoiceStatistics,
)
from dotmac.platform.billing.read_models.payment_read_models import (
    PaymentDetail,
    PaymentListItem,
    PaymentStatistics,
)
from dotmac.platform.billing.read_models.subscription_read_models import (
    SubscriptionDetail,
    SubscriptionListItem,
)

from .invoice_queries import (
    GetInvoiceQuery,
    GetInvoiceStatisticsQuery,
    GetOverdueInvoicesQuery,
    ListInvoicesQuery,
)
from .payment_queries import (
    GetPaymentQuery,
    GetPaymentStatisticsQuery,
    ListPaymentsQuery,
)
from .subscription_queries import (
    GetActiveSubscriptionsQuery,
    GetSubscriptionQuery,
    ListSubscriptionsQuery,
)

logger = structlog.get_logger(__name__)


class InvoiceQueryHandler:
    """Handles invoice queries with optimized read models"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def handle_get_invoice(self, query: GetInvoiceQuery) -> InvoiceDetail | None:
        """Get single invoice with full details"""
        logger.debug("Handling GetInvoiceQuery", invoice_id=query.invoice_id)

        stmt = select(InvoiceEntity).where(
            and_(
                InvoiceEntity.tenant_id == query.tenant_id,
                InvoiceEntity.invoice_id == query.invoice_id,
            )
        )

        if query.include_line_items:
            stmt = stmt.options(selectinload(InvoiceEntity.line_items))
        if query.include_payments:
            stmt = stmt.options(selectinload(InvoiceEntity.payments))

        result = await self.db.execute(stmt)
        invoice = result.scalar_one_or_none()

        if not invoice:
            return None

        return self._map_to_detail(invoice)

    async def handle_list_invoices(self, query: ListInvoicesQuery) -> dict:
        """List invoices with pagination"""
        logger.debug("Handling ListInvoicesQuery", page=query.page)

        # Build query with filters
        stmt = select(InvoiceEntity).where(InvoiceEntity.tenant_id == query.tenant_id)

        if query.customer_id:
            stmt = stmt.where(InvoiceEntity.customer_id == query.customer_id)
        if query.status:
            stmt = stmt.where(InvoiceEntity.status == query.status)
        if query.created_after:
            stmt = stmt.where(InvoiceEntity.created_at >= query.created_after)
        if query.created_before:
            stmt = stmt.where(InvoiceEntity.created_at <= query.created_before)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = await self.db.scalar(count_stmt)

        # Apply sorting and pagination
        if query.sort_order == "desc":
            stmt = stmt.order_by(getattr(InvoiceEntity, query.sort_by).desc())
        else:
            stmt = stmt.order_by(getattr(InvoiceEntity, query.sort_by).asc())

        offset = (query.page - 1) * query.page_size
        stmt = stmt.offset(offset).limit(query.page_size)

        result = await self.db.execute(stmt)
        invoices = result.scalars().all()

        return {
            "items": [self._map_to_list_item(inv) for inv in invoices],
            "total": total_count,
            "page": query.page,
            "page_size": query.page_size,
            "total_pages": (total_count + query.page_size - 1) // query.page_size,
        }

    async def handle_get_overdue_invoices(
        self, query: GetOverdueInvoicesQuery
    ) -> list[InvoiceListItem]:
        """Get overdue invoices"""
        logger.debug("Handling GetOverdueInvoicesQuery")

        now = datetime.now(UTC)
        stmt = (
            select(InvoiceEntity)
            .where(
                and_(
                    InvoiceEntity.tenant_id == query.tenant_id,
                    InvoiceEntity.status == InvoiceStatus.OPEN,
                    InvoiceEntity.due_date < now,
                    InvoiceEntity.remaining_balance > 0,
                )
            )
            .order_by(InvoiceEntity.due_date.asc())
            .limit(query.limit)
        )

        if query.customer_id:
            stmt = stmt.where(InvoiceEntity.customer_id == query.customer_id)

        result = await self.db.execute(stmt)
        invoices = result.scalars().all()

        return [self._map_to_list_item(inv) for inv in invoices]

    async def handle_get_invoice_statistics(
        self, query: GetInvoiceStatisticsQuery
    ) -> InvoiceStatistics:
        """Get aggregated invoice statistics"""
        logger.debug("Handling GetInvoiceStatisticsQuery")

        stmt = select(
            func.count(InvoiceEntity.invoice_id).label("total_count"),
            func.sum(case((InvoiceEntity.status == InvoiceStatus.DRAFT, 1), else_=0)).label(
                "draft_count"
            ),
            func.sum(case((InvoiceEntity.status == InvoiceStatus.OPEN, 1), else_=0)).label(
                "open_count"
            ),
            func.sum(case((InvoiceEntity.status == InvoiceStatus.PAID, 1), else_=0)).label(
                "paid_count"
            ),
            func.sum(InvoiceEntity.total_amount).label("total_amount"),
            func.sum(InvoiceEntity.remaining_balance).label("outstanding_amount"),
            func.avg(InvoiceEntity.total_amount).label("average_amount"),
        ).where(
            and_(
                InvoiceEntity.tenant_id == query.tenant_id,
                InvoiceEntity.created_at >= query.start_date,
                InvoiceEntity.created_at <= query.end_date,
            )
        )

        if query.customer_id:
            stmt = stmt.where(InvoiceEntity.customer_id == query.customer_id)

        result = await self.db.execute(stmt)
        row = result.one()

        return InvoiceStatistics(
            total_count=row.total_count or 0,
            draft_count=row.draft_count or 0,
            open_count=row.open_count or 0,
            paid_count=row.paid_count or 0,
            total_amount=row.total_amount or 0,
            outstanding_amount=row.outstanding_amount or 0,
            paid_amount=(row.total_amount or 0) - (row.outstanding_amount or 0),
            average_invoice_amount=int(row.average_amount or 0),
            period_start=query.start_date,
            period_end=query.end_date,
            currency="USD",
            formatted_total=f"${(row.total_amount or 0) / 100:.2f}",
            formatted_outstanding=f"${(row.outstanding_amount or 0) / 100:.2f}",
        )

    def _map_to_list_item(self, invoice: InvoiceEntity) -> InvoiceListItem:
        """Map entity to lightweight list item"""
        now = datetime.now(UTC)
        days_until_due = (invoice.due_date - now).days if invoice.due_date else None

        return InvoiceListItem(
            invoice_id=invoice.invoice_id,
            invoice_number=invoice.invoice_number,
            customer_id=invoice.customer_id,
            customer_name=invoice.billing_address.get("name", "Unknown"),
            customer_email=invoice.billing_email,
            total_amount=invoice.total_amount,
            remaining_balance=invoice.remaining_balance,
            currency=invoice.currency,
            status=invoice.status,
            is_overdue=invoice.due_date < now and invoice.status == InvoiceStatus.OPEN,
            created_at=invoice.created_at,
            due_date=invoice.due_date,
            paid_at=invoice.paid_at,
            line_item_count=len(invoice.line_items) if hasattr(invoice, "line_items") else 0,
            payment_count=len(invoice.payments) if hasattr(invoice, "payments") else 0,
            formatted_total=f"${invoice.total_amount / 100:.2f}",
            formatted_balance=f"${invoice.remaining_balance / 100:.2f}",
            days_until_due=days_until_due,
        )

    def _map_to_detail(self, invoice: InvoiceEntity) -> InvoiceDetail:
        """Map entity to detailed view"""
        return InvoiceDetail(
            invoice_id=invoice.invoice_id,
            invoice_number=invoice.invoice_number,
            tenant_id=invoice.tenant_id,
            customer_id=invoice.customer_id,
            customer_name=invoice.billing_address.get("name", "Unknown"),
            customer_email=invoice.billing_email,
            billing_address=invoice.billing_address,
            line_items=invoice.line_items if hasattr(invoice, "line_items") else [],
            subtotal=invoice.subtotal,
            tax_amount=invoice.tax_amount,
            discount_amount=invoice.discount_amount,
            total_amount=invoice.total_amount,
            remaining_balance=invoice.remaining_balance,
            currency=invoice.currency,
            status=invoice.status,
            created_at=invoice.created_at,
            updated_at=invoice.updated_at,
            issue_date=invoice.issue_date,
            due_date=invoice.due_date,
            finalized_at=invoice.finalized_at,
            paid_at=invoice.paid_at,
            voided_at=invoice.voided_at,
            payments=[],
            total_paid=invoice.total_amount - invoice.remaining_balance,
            notes=invoice.notes,
            internal_notes=invoice.internal_notes,
            subscription_id=invoice.subscription_id,
            idempotency_key=invoice.idempotency_key,
            created_by=invoice.created_by,
            extra_data=invoice.extra_data or {},
            is_overdue=invoice.due_date < datetime.now(UTC)
            and invoice.status == InvoiceStatus.OPEN,
        )


class PaymentQueryHandler:
    """Handles payment queries"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def handle_get_payment(self, query: GetPaymentQuery) -> PaymentDetail | None:
        """Get single payment"""
        stmt = select(PaymentEntity).where(
            and_(
                PaymentEntity.tenant_id == query.tenant_id,
                PaymentEntity.payment_id == query.payment_id,
            )
        )

        result = await self.db.execute(stmt)
        payment = result.scalar_one_or_none()

        if not payment:
            return None

        return PaymentDetail.model_validate(payment)

    async def handle_list_payments(self, query: ListPaymentsQuery) -> dict:
        """List payments with pagination"""
        stmt = select(PaymentEntity).where(PaymentEntity.tenant_id == query.tenant_id)

        if query.customer_id:
            stmt = stmt.where(PaymentEntity.customer_id == query.customer_id)
        if query.status:
            stmt = stmt.where(PaymentEntity.status == query.status)

        # Count and paginate
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = await self.db.scalar(count_stmt)

        offset = (query.page - 1) * query.page_size
        stmt = stmt.order_by(PaymentEntity.created_at.desc()).offset(offset).limit(query.page_size)

        result = await self.db.execute(stmt)
        payments = result.scalars().all()

        return {
            "items": [PaymentListItem.model_validate(p) for p in payments],
            "total": total_count,
            "page": query.page,
            "page_size": query.page_size,
        }

    async def handle_get_payment_statistics(
        self, query: GetPaymentStatisticsQuery
    ) -> PaymentStatistics:
        """Get payment statistics"""
        stmt = select(
            func.count(PaymentEntity.payment_id).label("total_count"),
            func.sum(case((PaymentEntity.status == PaymentStatus.SUCCEEDED, 1), else_=0)).label(
                "succeeded_count"
            ),
            func.sum(case((PaymentEntity.status == PaymentStatus.FAILED, 1), else_=0)).label(
                "failed_count"
            ),
            func.sum(PaymentEntity.amount).label("total_amount"),
        ).where(
            and_(
                PaymentEntity.tenant_id == query.tenant_id,
                PaymentEntity.created_at >= query.start_date,
                PaymentEntity.created_at <= query.end_date,
            )
        )

        result = await self.db.execute(stmt)
        row = result.one()

        return PaymentStatistics(
            total_count=row.total_count or 0,
            succeeded_count=row.succeeded_count or 0,
            failed_count=row.failed_count or 0,
            total_amount=row.total_amount or 0,
            success_rate=row.succeeded_count / row.total_count if row.total_count else 0,
            period_start=query.start_date,
            period_end=query.end_date,
        )


class SubscriptionQueryHandler:
    """Handles subscription queries"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def handle_get_subscription(
        self, query: GetSubscriptionQuery
    ) -> SubscriptionDetail | None:
        """Get single subscription"""
        stmt = select(BillingSubscriptionTable).where(
            and_(
                BillingSubscriptionTable.tenant_id == query.tenant_id,
                BillingSubscriptionTable.subscription_id == query.subscription_id,
            )
        )

        result = await self.db.execute(stmt)
        subscription = result.scalar_one_or_none()

        if not subscription:
            return None

        return SubscriptionDetail.model_validate(subscription)

    async def handle_list_subscriptions(self, query: ListSubscriptionsQuery) -> dict:
        """List subscriptions"""
        stmt = select(BillingSubscriptionTable).where(
            BillingSubscriptionTable.tenant_id == query.tenant_id
        )

        if query.customer_id:
            stmt = stmt.where(BillingSubscriptionTable.customer_id == query.customer_id)
        if query.status:
            stmt = stmt.where(BillingSubscriptionTable.status == query.status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = await self.db.scalar(count_stmt)

        offset = (query.page - 1) * query.page_size
        stmt = (
            stmt.order_by(BillingSubscriptionTable.created_at.desc())
            .offset(offset)
            .limit(query.page_size)
        )

        result = await self.db.execute(stmt)
        subscriptions = result.scalars().all()

        return {
            "items": [SubscriptionListItem.model_validate(s) for s in subscriptions],
            "total": total_count,
            "page": query.page,
            "page_size": query.page_size,
        }

    async def handle_get_active_subscriptions(
        self, query: GetActiveSubscriptionsQuery
    ) -> list[SubscriptionListItem]:
        """Get active subscriptions"""
        stmt = (
            select(BillingSubscriptionTable)
            .where(
                and_(
                    BillingSubscriptionTable.tenant_id == query.tenant_id,
                    BillingSubscriptionTable.status == "active",
                )
            )
            .limit(query.limit)
        )

        if query.customer_id:
            stmt = stmt.where(BillingSubscriptionTable.customer_id == query.customer_id)

        result = await self.db.execute(stmt)
        subscriptions = result.scalars().all()

        return [SubscriptionListItem.model_validate(s) for s in subscriptions]
