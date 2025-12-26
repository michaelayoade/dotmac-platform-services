"""Payment router for billing management."""

from datetime import UTC, datetime, timedelta

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.core import UserInfo
from dotmac.platform.auth.dependencies import get_current_user
from dotmac.platform.auth.rbac_dependencies import require_permission
from dotmac.platform.billing.core.entities import PaymentEntity
from dotmac.platform.billing.core.models import PaymentStatus
from dotmac.platform.billing.dependencies import enforce_tenant_access, get_tenant_id
from dotmac.platform.db import get_session_dependency

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/payments", tags=["Billing - Payments"])


class FailedPaymentsSummary(BaseModel):
    """Summary of failed payments."""

    model_config = ConfigDict()

    count: int
    total_amount: float
    oldest_failure: datetime | None = None
    newest_failure: datetime | None = None


@router.get("/failed", response_model=FailedPaymentsSummary)
async def get_failed_payments(
    session: AsyncSession = Depends(get_session_dependency),
    current_user: UserInfo = Depends(require_permission("billing.payments.view")),
    tenant_id: str = Depends(get_tenant_id),
) -> FailedPaymentsSummary:
    """
    Get summary of failed payments for monitoring.

    Returns count and total amount of payments that have failed for the current tenant.
    """
    try:
        effective_tenant_id = tenant_id if isinstance(tenant_id, str) else None
        if not effective_tenant_id:
            effective_tenant_id = getattr(current_user, "tenant_id", None)

        if not effective_tenant_id:
            return FailedPaymentsSummary(
                count=0,
                total_amount=0.0,
                oldest_failure=None,
                newest_failure=None,
            )

        enforce_tenant_access(effective_tenant_id, current_user)

        # Query failed payments from last 30 days for current tenant only
        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)

        # Count and sum failed payments scoped by tenant_id
        query = select(
            func.count(PaymentEntity.payment_id).label("count"),
            func.sum(PaymentEntity.amount).label("total_amount"),
            func.min(PaymentEntity.created_at).label("oldest"),
            func.max(PaymentEntity.created_at).label("newest"),
        ).where(
            PaymentEntity.status == PaymentStatus.FAILED,
            PaymentEntity.created_at >= thirty_days_ago,
            PaymentEntity.tenant_id == effective_tenant_id,  # CRITICAL: Scope by tenant
        )

        result = await session.execute(query)
        row = result.one()
        row_mapping = row._mapping

        count_value = int(row_mapping.get("count") or 0)
        # FIXED: Convert from minor units (cents) to major units (dollars/naira)
        # PaymentEntity.amount is stored in cents, so ₦42.50 is stored as 4250
        # Without conversion, would display as "4250.0" instead of "42.50"
        total_amount_minor = float(row_mapping.get("total_amount") or 0)
        total_amount_value = total_amount_minor / 100.0
        oldest = row_mapping.get("oldest")
        newest = row_mapping.get("newest")

        return FailedPaymentsSummary(
            count=count_value,
            total_amount=total_amount_value,
            oldest_failure=oldest,
            newest_failure=newest,
        )

    except Exception as e:
        logger.error("Failed to fetch failed payments", error=str(e), exc_info=True)
        # Return empty summary on error
        return FailedPaymentsSummary(
            count=0,
            total_amount=0.0,
        )


__all__ = ["router"]
