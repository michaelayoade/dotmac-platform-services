"""
Main billing module router aggregating all billing sub-routers
"""

from fastapi import APIRouter

from .invoicing.router import router as invoice_router
from .invoicing.money_router import router as money_invoice_router
from .webhooks.router import router as webhook_router
from .credit_notes.router import router as credit_note_router
from .settings.router import router as settings_router
from .bank_accounts.router import router as bank_accounts_router
from .catalog.router import router as catalog_router
from .subscriptions.router import router as subscriptions_router

# Create main billing router - no prefix here as it's added in main router registration
router = APIRouter(tags=["billing"])

# Include sub-routers - invoice router already has /invoices prefix
router.include_router(invoice_router, prefix="", tags=["invoices"])
router.include_router(money_invoice_router, prefix="", tags=["money-invoices"])
router.include_router(webhook_router, prefix="", tags=["webhooks"])
router.include_router(credit_note_router, prefix="", tags=["credit-notes"])
router.include_router(settings_router, prefix="", tags=["settings"])
router.include_router(bank_accounts_router, prefix="", tags=["bank-accounts"])
router.include_router(catalog_router, prefix="", tags=["catalog"])
router.include_router(subscriptions_router, prefix="", tags=["subscriptions"])

# Additional billing endpoints can be added here

__all__ = ["router"]