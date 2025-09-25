"""
Webhook router for payment providers
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Header, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.billing.config import get_billing_config
from dotmac.platform.billing.webhooks.handlers import (
    StripeWebhookHandler,
    PayPalWebhookHandler,
)
from dotmac.platform.database import get_async_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe", status_code=status.HTTP_200_OK)
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """Handle Stripe webhook events"""
    
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe-Signature header",
        )
    
    # Get raw payload
    try:
        payload = await request.body()
    except Exception as e:
        logger.error(f"Failed to read request body: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request body",
        )
    
    # Process webhook
    handler = StripeWebhookHandler(db)
    
    try:
        result = await handler.handle_webhook(
            payload=payload,
            signature=stripe_signature,
            headers=dict(request.headers),
        )
        return result
    except ValueError as e:
        logger.error(f"Webhook validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to process webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook",
        )


@router.post("/paypal", status_code=status.HTTP_200_OK)
async def handle_paypal_webhook(
    request: Request,
    paypal_transmission_id: str = Header(None, alias="Paypal-Transmission-Id"),
    paypal_transmission_sig: str = Header(None, alias="Paypal-Transmission-Sig"),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """Handle PayPal webhook events"""
    
    if not paypal_transmission_sig:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing PayPal signature headers",
        )
    
    # Get raw payload
    try:
        payload = await request.body()
    except Exception as e:
        logger.error(f"Failed to read request body: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request body",
        )
    
    # Process webhook
    handler = PayPalWebhookHandler(db)
    
    try:
        result = await handler.handle_webhook(
            payload=payload,
            signature=paypal_transmission_sig,
            headers=dict(request.headers),
        )
        return result
    except ValueError as e:
        logger.error(f"Webhook validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to process webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook",
        )


@router.get("/config", include_in_schema=False)
async def get_webhook_config() -> Dict[str, Any]:
    """Get webhook configuration status (for debugging)"""
    config = get_billing_config()
    
    return {
        "webhooks_enabled": config.enable_webhooks,
        "stripe_configured": bool(config.stripe and config.stripe.webhook_secret),
        "paypal_configured": bool(config.paypal and config.paypal.webhook_id),
        "webhook_endpoint": config.webhook.endpoint_base_url if config.webhook else None,
    }