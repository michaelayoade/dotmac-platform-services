"""Payment router for billing management."""

from datetime import UTC, datetime, timedelta

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.core import UserInfo
from dotmac.platform.auth.dependencies import get_current_user
from dotmac.platform.billing.core.entities import PaymentEntity
from dotmac.platform.billing.core.models import PaymentStatus
from dotmac.platform.db import get_session_dependency

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/payments", tags=["Billing - Payments"])


class FailedPaymentsSummary(BaseModel):
    """Summary of failed payments."""

    count: int
    total_amount: float
    oldest_failure: datetime | None = None
    newest_failure: datetime | None = None


@router.get("/failed", response_model=FailedPaymentsSummary)
async def get_failed_payments(
    session: AsyncSession = Depends(get_session_dependency),
    current_user: UserInfo = Depends(get_current_user),
) -> FailedPaymentsSummary:
    """
    Get summary of failed payments for monitoring.

    Returns count and total amount of payments that have failed.
    """
    try:
        # Query failed payments from last 30 days
        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)

        # Count and sum failed payments
        query = select(
            func.count(PaymentEntity.payment_id).label("count"),
            func.sum(PaymentEntity.amount).label("total_amount"),
            func.min(PaymentEntity.created_at).label("oldest"),
            func.max(PaymentEntity.created_at).label("newest"),
        ).where(
            PaymentEntity.status == PaymentStatus.FAILED,
            PaymentEntity.created_at >= thirty_days_ago,
        )

        result = await session.execute(query)
        row = result.one()

        return FailedPaymentsSummary(
            count=row.count or 0,
            total_amount=float(row.total_amount or 0),
            oldest_failure=row.oldest,
            newest_failure=row.newest,
        )

    except Exception as e:
        logger.error("Failed to fetch failed payments", error=str(e), exc_info=True)
        # Return empty summary on error
        return FailedPaymentsSummary(
            count=0,
            total_amount=0.0,
        )


__all__ = ["router"]
