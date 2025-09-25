"""
Main billing module router aggregating all billing sub-routers
"""

from fastapi import APIRouter

from .invoicing.router import router as invoice_router
from .webhooks.router import router as webhook_router
from .credit_notes.router import router as credit_note_router

# Create main billing router - no prefix here as it's added in main router registration
router = APIRouter(tags=["billing"])

# Include sub-routers - invoice router already has /invoices prefix
router.include_router(invoice_router, prefix="", tags=["invoices"])
router.include_router(webhook_router, prefix="", tags=["webhooks"])
router.include_router(credit_note_router, prefix="", tags=["credit-notes"])

# Additional billing endpoints can be added here

__all__ = ["router"]