"""
Billing settings API router
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.dependencies import UserInfo, get_current_user
from dotmac.platform.auth.rbac_dependencies import require_permission
from dotmac.platform.billing.dependencies import enforce_tenant_access
from dotmac.platform.billing.settings.models import (
    BillingSettings,
    CompanyInfo,
    InvoiceSettings,
    NotificationSettings,
    PaymentSettings,
    TaxSettings,
)
from dotmac.platform.billing.settings.service import BillingSettingsService
from dotmac.platform.database import get_async_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["Billing - Settings"])


def _require_tenant(current_user: UserInfo) -> str:
    tenant_id = current_user.tenant_id
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context is required",
        )
    enforce_tenant_access(tenant_id, current_user)
    return tenant_id


@router.get("", response_model=BillingSettings)
async def get_billing_settings(
    current_user: UserInfo = Depends(require_permission("billing.settings.view")),
    db: AsyncSession = Depends(get_async_session),
) -> BillingSettings:
    """Get billing settings for the current tenant"""
    service = BillingSettingsService(db)
    tenant_id = _require_tenant(current_user)

    try:
        settings = await service.get_settings(tenant_id)
        return settings
    except Exception as e:
        logger.error(f"Error retrieving billing settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve billing settings",
        )


@router.put("", response_model=BillingSettings)
async def update_billing_settings(
    settings: BillingSettings,
    current_user: UserInfo = Depends(require_permission("billing.settings.manage")),
    db: AsyncSession = Depends(get_async_session),
) -> BillingSettings:
    """Update complete billing settings"""
    service = BillingSettingsService(db)
    tenant_id = _require_tenant(current_user)

    try:
        updated_settings = await service.update_settings(tenant_id, settings)
        return updated_settings
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating billing settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update billing settings",
        )


@router.put("/company", response_model=BillingSettings)
async def update_company_info(
    company_info: CompanyInfo,
    current_user: UserInfo = Depends(require_permission("billing.settings.manage")),
    db: AsyncSession = Depends(get_async_session),
) -> BillingSettings:
    """Update company information settings"""
    service = BillingSettingsService(db)
    tenant_id = _require_tenant(current_user)

    try:
        updated_settings = await service.update_company_info(tenant_id, company_info)
        return updated_settings
    except Exception as e:
        logger.error(f"Error updating company info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update company information",
        )


@router.put("/tax", response_model=BillingSettings)
async def update_tax_settings(
    tax_settings: TaxSettings,
    current_user: UserInfo = Depends(require_permission("billing.settings.manage")),
    db: AsyncSession = Depends(get_async_session),
) -> BillingSettings:
    """Update tax settings"""
    service = BillingSettingsService(db)
    tenant_id = _require_tenant(current_user)

    try:
        updated_settings = await service.update_tax_settings(tenant_id, tax_settings)
        return updated_settings
    except Exception as e:
        logger.error(f"Error updating tax settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update tax settings",
        )


@router.put("/payment", response_model=BillingSettings)
async def update_payment_settings(
    payment_settings: PaymentSettings,
    current_user: UserInfo = Depends(require_permission("billing.settings.manage")),
    db: AsyncSession = Depends(get_async_session),
) -> BillingSettings:
    """Update payment settings"""
    service = BillingSettingsService(db)
    tenant_id = _require_tenant(current_user)

    try:
        updated_settings = await service.update_payment_settings(tenant_id, payment_settings)
        return updated_settings
    except Exception as e:
        logger.error(f"Error updating payment settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update payment settings",
        )


@router.put("/invoice", response_model=BillingSettings)
async def update_invoice_settings(
    invoice_settings: InvoiceSettings,
    current_user: UserInfo = Depends(require_permission("billing.settings.manage")),
    db: AsyncSession = Depends(get_async_session),
) -> BillingSettings:
    """Update invoice settings"""
    service = BillingSettingsService(db)
    tenant_id = _require_tenant(current_user)

    try:
        updated_settings = await service.update_invoice_settings(tenant_id, invoice_settings)
        return updated_settings
    except Exception as e:
        logger.error(f"Error updating invoice settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update invoice settings",
        )


@router.put("/notifications", response_model=BillingSettings)
async def update_notification_settings(
    notification_settings: NotificationSettings,
    current_user: UserInfo = Depends(require_permission("billing.settings.manage")),
    db: AsyncSession = Depends(get_async_session),
) -> BillingSettings:
    """Update notification settings"""
    service = BillingSettingsService(db)
    tenant_id = _require_tenant(current_user)

    try:
        updated_settings = await service.update_notification_settings(
            tenant_id, notification_settings
        )
        return updated_settings
    except Exception as e:
        logger.error(f"Error updating notification settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification settings",
        )


@router.put("/features", response_model=BillingSettings)
async def update_feature_flags(
    features: dict[str, bool],
    current_user: UserInfo = Depends(require_permission("billing.settings.manage")),
    db: AsyncSession = Depends(get_async_session),
) -> BillingSettings:
    """Update feature flags"""
    service = BillingSettingsService(db)
    tenant_id = _require_tenant(current_user)

    try:
        updated_settings = await service.update_feature_flags(tenant_id, features)
        return updated_settings
    except Exception as e:
        logger.error(f"Error updating feature flags: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update feature flags",
        )


@router.post("/reset", response_model=BillingSettings)
async def reset_to_defaults(
    current_user: UserInfo = Depends(require_permission("billing.settings.manage")),
    db: AsyncSession = Depends(get_async_session),
) -> BillingSettings:
    """Reset billing settings to defaults"""
    service = BillingSettingsService(db)
    tenant_id = _require_tenant(current_user)

    try:
        settings = await service.reset_to_defaults(tenant_id)
        return settings
    except Exception as e:
        logger.error(f"Error resetting billing settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset billing settings",
        )


@router.get("/validate")
async def validate_settings(
    current_user: UserInfo = Depends(require_permission("billing.settings.view")),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Validate current billing settings and return validation report"""
    service = BillingSettingsService(db)
    tenant_id = _require_tenant(current_user)

    try:
        validation_report: dict[str, Any] = await service.validate_settings_for_tenant(tenant_id)
        return validation_report
    except Exception as e:
        logger.error(f"Error validating billing settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate billing settings",
        )
