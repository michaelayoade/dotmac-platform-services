"""
Specialized report generators for billing
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from sqlalchemy import and_, select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.billing.core.entities import (
    InvoiceEntity,
    PaymentEntity,
    CreditNoteEntity,
    TransactionEntity,
)
from dotmac.platform.billing.core.enums import (
    InvoiceStatus,
    PaymentStatus,
    CreditNoteStatus,
    TransactionType,
)

logger = logging.getLogger(__name__)


class RevenueReportGenerator:
    """Generate revenue-related reports"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_revenue_summary(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Get revenue summary for period"""
        
        # Query invoices
        stmt = (
            select(
                func.count(InvoiceEntity.invoice_id).label("invoice_count"),
                func.sum(InvoiceEntity.total_amount).label("total_invoiced"),
                func.sum(
                    case(
                        (InvoiceEntity.payment_status == PaymentStatus.PAID, InvoiceEntity.total_amount),
                        else_=0
                    )
                ).label("total_revenue"),
                func.count(
                    case(
                        (InvoiceEntity.payment_status == PaymentStatus.PAID, 1),
                        else_=None
                    )
                ).label("paid_count"),
            )
            .where(
                and_(
                    InvoiceEntity.tenant_id == tenant_id,
                    InvoiceEntity.issue_date >= start_date,
                    InvoiceEntity.issue_date <= end_date,
                    InvoiceEntity.status != InvoiceStatus.VOIDED,
                )
            )
        )
        
        result = await self.db.execute(stmt)
        row = result.one()
        
        return {
            "invoice_count": row.invoice_count or 0,
            "total_invoiced": row.total_invoiced or 0,
            "total_revenue": row.total_revenue or 0,
            "paid_count": row.paid_count or 0,
            "collection_rate": self._calculate_rate(row.paid_count, row.invoice_count),
        }

    async def get_revenue_trend(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
        group_by: str = "month",
    ) -> List[Dict[str, Any]]:
        """Get revenue trend over time"""
        
        # Determine date truncation based on group_by
        if group_by == "day":
            date_trunc = func.date_trunc("day", InvoiceEntity.issue_date)
        elif group_by == "week":
            date_trunc = func.date_trunc("week", InvoiceEntity.issue_date)
        elif group_by == "month":
            date_trunc = func.date_trunc("month", InvoiceEntity.issue_date)
        else:
            date_trunc = func.date_trunc("month", InvoiceEntity.issue_date)
        
        stmt = (
            select(
                date_trunc.label("period"),
                func.count(InvoiceEntity.invoice_id).label("invoice_count"),
                func.sum(InvoiceEntity.total_amount).label("total_amount"),
                func.sum(
                    case(
                        (InvoiceEntity.payment_status == PaymentStatus.PAID, InvoiceEntity.total_amount),
                        else_=0
                    )
                ).label("paid_amount"),
            )
            .where(
                and_(
                    InvoiceEntity.tenant_id == tenant_id,
                    InvoiceEntity.issue_date >= start_date,
                    InvoiceEntity.issue_date <= end_date,
                    InvoiceEntity.status != InvoiceStatus.VOIDED,
                )
            )
            .group_by(date_trunc)
            .order_by(date_trunc)
        )
        
        result = await self.db.execute(stmt)
        rows = result.all()
        
        trend = []
        for row in rows:
            trend.append({
                "period": row.period.isoformat() if row.period else None,
                "invoice_count": row.invoice_count or 0,
                "total_amount": row.total_amount or 0,
                "paid_amount": row.paid_amount or 0,
            })
        
        return trend

    async def get_payment_method_distribution(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Get distribution of payment methods used"""
        
        stmt = (
            select(
                PaymentEntity.payment_method_type,
                func.count(PaymentEntity.payment_id).label("count"),
                func.sum(PaymentEntity.amount).label("total_amount"),
            )
            .where(
                and_(
                    PaymentEntity.tenant_id == tenant_id,
                    PaymentEntity.created_at >= start_date,
                    PaymentEntity.created_at <= end_date,
                    PaymentEntity.status == PaymentStatus.SUCCEEDED,
                )
            )
            .group_by(PaymentEntity.payment_method_type)
        )
        
        result = await self.db.execute(stmt)
        rows = result.all()
        
        distribution = {}
        total_amount = 0
        
        for row in rows:
            method = row.payment_method_type or "unknown"
            amount = row.total_amount or 0
            distribution[method] = {
                "count": row.count or 0,
                "amount": amount,
            }
            total_amount += amount
        
        # Calculate percentages
        for method, data in distribution.items():
            data["percentage"] = self._calculate_rate(data["amount"], total_amount)
        
        return distribution

    async def generate_detailed_report(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
        group_by: str = "month",
    ) -> Dict[str, Any]:
        """Generate detailed revenue report"""
        
        summary = await self.get_revenue_summary(tenant_id, start_date, end_date)
        trend = await self.get_revenue_trend(tenant_id, start_date, end_date, group_by)
        payment_methods = await self.get_payment_method_distribution(
            tenant_id, start_date, end_date
        )
        
        # Get refunds summary
        refunds = await self.get_refunds_summary(tenant_id, start_date, end_date)
        
        return {
            "report_type": "revenue_detailed",
            "tenant_id": tenant_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "summary": summary,
            "trend": trend,
            "payment_methods": payment_methods,
            "refunds": refunds,
            "net_revenue": summary["total_revenue"] - refunds["total_refunded"],
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def get_refunds_summary(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Get refunds summary"""
        
        stmt = (
            select(
                func.count(CreditNoteEntity.credit_note_id).label("credit_note_count"),
                func.sum(CreditNoteEntity.total_amount).label("total_refunded"),
            )
            .where(
                and_(
                    CreditNoteEntity.tenant_id == tenant_id,
                    CreditNoteEntity.created_at >= start_date,
                    CreditNoteEntity.created_at <= end_date,
                    CreditNoteEntity.status != CreditNoteStatus.VOIDED,
                )
            )
        )
        
        result = await self.db.execute(stmt)
        row = result.one()
        
        return {
            "credit_note_count": row.credit_note_count or 0,
            "total_refunded": row.total_refunded or 0,
        }

    async def generate_refunds_report(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Generate detailed refunds report"""
        
        summary = await self.get_refunds_summary(tenant_id, start_date, end_date)
        
        # Get refund reasons breakdown
        stmt = (
            select(
                CreditNoteEntity.reason,
                func.count(CreditNoteEntity.credit_note_id).label("count"),
                func.sum(CreditNoteEntity.total_amount).label("amount"),
            )
            .where(
                and_(
                    CreditNoteEntity.tenant_id == tenant_id,
                    CreditNoteEntity.created_at >= start_date,
                    CreditNoteEntity.created_at <= end_date,
                    CreditNoteEntity.status != CreditNoteStatus.VOIDED,
                )
            )
            .group_by(CreditNoteEntity.reason)
        )
        
        result = await self.db.execute(stmt)
        rows = result.all()
        
        reasons = []
        for row in rows:
            reasons.append({
                "reason": row.reason.value if row.reason else "unknown",
                "count": row.count or 0,
                "amount": row.amount or 0,
            })
        
        return {
            "report_type": "refunds",
            "tenant_id": tenant_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "summary": summary,
            "by_reason": reasons,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _calculate_rate(self, part: Optional[float], whole: Optional[float]) -> float:
        """Calculate percentage rate"""
        if not whole or whole == 0:
            return 0.0
        return (part / whole * 100) if part else 0.0


class CustomerReportGenerator:
    """Generate customer-related reports"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_customer_metrics(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Get customer metrics for period"""
        
        # Count unique customers with invoices
        stmt = (
            select(
                func.count(func.distinct(InvoiceEntity.customer_id)).label("active_customers"),
            )
            .where(
                and_(
                    InvoiceEntity.tenant_id == tenant_id,
                    InvoiceEntity.issue_date >= start_date,
                    InvoiceEntity.issue_date <= end_date,
                    InvoiceEntity.status != InvoiceStatus.VOIDED,
                )
            )
        )
        
        result = await self.db.execute(stmt)
        row = result.one()
        
        # Get new customers (first invoice in period)
        # This is simplified - in production would track customer creation date
        new_customers = row.active_customers  # Placeholder
        
        return {
            "active_customers": row.active_customers or 0,
            "new_customers": new_customers or 0,
        }

    async def generate_customer_report(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
        top_n: int = 20,
    ) -> Dict[str, Any]:
        """Generate customer analysis report"""
        
        # Get top customers by revenue
        stmt = (
            select(
                InvoiceEntity.customer_id,
                func.count(InvoiceEntity.invoice_id).label("invoice_count"),
                func.sum(InvoiceEntity.total_amount).label("total_amount"),
                func.sum(
                    case(
                        (InvoiceEntity.payment_status == PaymentStatus.PAID, InvoiceEntity.total_amount),
                        else_=0
                    )
                ).label("paid_amount"),
            )
            .where(
                and_(
                    InvoiceEntity.tenant_id == tenant_id,
                    InvoiceEntity.issue_date >= start_date,
                    InvoiceEntity.issue_date <= end_date,
                    InvoiceEntity.status != InvoiceStatus.VOIDED,
                )
            )
            .group_by(InvoiceEntity.customer_id)
            .order_by(func.sum(InvoiceEntity.total_amount).desc())
            .limit(top_n)
        )
        
        result = await self.db.execute(stmt)
        rows = result.all()
        
        top_customers = []
        for row in rows:
            top_customers.append({
                "customer_id": row.customer_id,
                "invoice_count": row.invoice_count or 0,
                "total_amount": row.total_amount or 0,
                "paid_amount": row.paid_amount or 0,
                "outstanding": (row.total_amount or 0) - (row.paid_amount or 0),
            })
        
        metrics = await self.get_customer_metrics(tenant_id, start_date, end_date)
        
        return {
            "report_type": "customer_analysis",
            "tenant_id": tenant_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "metrics": metrics,
            "top_customers": top_customers,
            "generated_at": datetime.utcnow().isoformat(),
        }


class AgingReportGenerator:
    """Generate accounts receivable aging reports"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_aging_summary(self, tenant_id: str) -> Dict[str, Any]:
        """Get aging summary"""
        
        current_date = datetime.utcnow()
        
        # Define aging buckets
        stmt = (
            select(
                func.count(InvoiceEntity.invoice_id).label("invoice_count"),
                func.sum(InvoiceEntity.remaining_balance).label("total_outstanding"),
                func.sum(
                    case(
                        (InvoiceEntity.due_date > current_date, InvoiceEntity.remaining_balance),
                        else_=0
                    )
                ).label("current"),
                func.sum(
                    case(
                        (
                            and_(
                                InvoiceEntity.due_date <= current_date,
                                InvoiceEntity.due_date > current_date - timedelta(days=30),
                            ),
                            InvoiceEntity.remaining_balance
                        ),
                        else_=0
                    )
                ).label("days_1_30"),
                func.sum(
                    case(
                        (
                            and_(
                                InvoiceEntity.due_date <= current_date - timedelta(days=30),
                                InvoiceEntity.due_date > current_date - timedelta(days=60),
                            ),
                            InvoiceEntity.remaining_balance
                        ),
                        else_=0
                    )
                ).label("days_31_60"),
                func.sum(
                    case(
                        (
                            and_(
                                InvoiceEntity.due_date <= current_date - timedelta(days=60),
                                InvoiceEntity.due_date > current_date - timedelta(days=90),
                            ),
                            InvoiceEntity.remaining_balance
                        ),
                        else_=0
                    )
                ).label("days_61_90"),
                func.sum(
                    case(
                        (
                            InvoiceEntity.due_date <= current_date - timedelta(days=90),
                            InvoiceEntity.remaining_balance
                        ),
                        else_=0
                    )
                ).label("over_90_days"),
            )
            .where(
                and_(
                    InvoiceEntity.tenant_id == tenant_id,
                    InvoiceEntity.payment_status != PaymentStatus.PAID,
                    InvoiceEntity.status.in_([InvoiceStatus.OPEN, InvoiceStatus.OVERDUE]),
                    InvoiceEntity.remaining_balance > 0,
                )
            )
        )
        
        result = await self.db.execute(stmt)
        row = result.one()
        
        total_outstanding = row.total_outstanding or 0
        overdue_amount = (
            (row.days_1_30 or 0) +
            (row.days_31_60 or 0) +
            (row.days_61_90 or 0) +
            (row.over_90_days or 0)
        )
        
        return {
            "invoice_count": row.invoice_count or 0,
            "total_outstanding": total_outstanding,
            "overdue_amount": overdue_amount,
            "buckets": {
                "current": row.current or 0,
                "1_30_days": row.days_1_30 or 0,
                "31_60_days": row.days_31_60 or 0,
                "61_90_days": row.days_61_90 or 0,
                "over_90_days": row.over_90_days or 0,
            },
        }

    async def generate_aging_report(
        self,
        tenant_id: str,
        as_of_date: datetime,
    ) -> Dict[str, Any]:
        """Generate detailed aging report"""
        
        summary = await self.get_aging_summary(tenant_id)
        
        # Get detailed invoice list for aging
        # This would include individual invoice details
        # Simplified for now
        
        return {
            "report_type": "aging",
            "tenant_id": tenant_id,
            "as_of_date": as_of_date.isoformat(),
            "summary": summary,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def generate_collections_report(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Generate collections performance report"""
        
        # Get invoices that were paid during the period
        stmt = (
            select(
                func.count(InvoiceEntity.invoice_id).label("collected_count"),
                func.sum(InvoiceEntity.total_amount).label("collected_amount"),
                func.avg(
                    func.extract(
                        "day",
                        InvoiceEntity.updated_at - InvoiceEntity.due_date
                    )
                ).label("avg_days_to_collect"),
            )
            .where(
                and_(
                    InvoiceEntity.tenant_id == tenant_id,
                    InvoiceEntity.payment_status == PaymentStatus.PAID,
                    InvoiceEntity.updated_at >= start_date,
                    InvoiceEntity.updated_at <= end_date,
                )
            )
        )
        
        result = await self.db.execute(stmt)
        row = result.one()
        
        return {
            "report_type": "collections",
            "tenant_id": tenant_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "summary": {
                "collected_count": row.collected_count or 0,
                "collected_amount": row.collected_amount or 0,
                "avg_days_to_collect": float(row.avg_days_to_collect or 0),
            },
            "generated_at": datetime.utcnow().isoformat(),
        }