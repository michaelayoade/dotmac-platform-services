"""
Webhook handlers for payment providers
"""

import hashlib
import hmac
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.billing.config import BillingConfig, get_billing_config
from dotmac.platform.billing.core.enums import PaymentStatus, InvoiceStatus
from dotmac.platform.billing.invoicing.service import InvoiceService
from dotmac.platform.billing.payments.service import PaymentService
from dotmac.platform.billing.metrics import get_billing_metrics

logger = logging.getLogger(__name__)


class WebhookHandler(ABC):
    """Base webhook handler interface"""

    def __init__(self, db: AsyncSession, config: Optional[BillingConfig] = None):
        self.db = db
        self.config = config or get_billing_config()
        self.invoice_service = InvoiceService(db)
        self.payment_service = PaymentService(db)
        self.metrics = get_billing_metrics()

    @abstractmethod
    async def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature"""
        pass

    @abstractmethod
    async def process_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process webhook event"""
        pass

    async def handle_webhook(
        self, payload: bytes, signature: str, headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Handle webhook request"""
        import time
        start_time = time.time()

        # Verify signature
        if not await self.verify_signature(payload, signature):
            logger.warning("Invalid webhook signature")
            raise ValueError("Invalid webhook signature")

        # Parse payload
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse webhook payload: {e}")
            raise ValueError("Invalid webhook payload")

        # Extract event type and data
        event_type = self._extract_event_type(data, headers)
        event_data = self._extract_event_data(data)
        provider = self._get_provider_name()

        # Record webhook received
        self.metrics.record_webhook_received(provider, event_type)

        # Process event
        try:
            result = await self.process_event(event_type, event_data)
            await self.db.commit()

            # Record successful processing
            duration_ms = (time.time() - start_time) * 1000
            self.metrics.record_webhook_processed(provider, event_type, True, duration_ms)

            return result
        except Exception as e:
            logger.error(f"Failed to process webhook event: {e}")
            await self.db.rollback()

            # Record failed processing
            duration_ms = (time.time() - start_time) * 1000
            self.metrics.record_webhook_processed(provider, event_type, False, duration_ms)

            raise

    @abstractmethod
    def _extract_event_type(self, data: Dict[str, Any], headers: Dict[str, str]) -> str:
        """Extract event type from webhook data"""
        pass

    @abstractmethod
    def _extract_event_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract event data from webhook payload"""
        pass

    @abstractmethod
    def _get_provider_name(self) -> str:
        """Get the payment provider name"""
        pass


class StripeWebhookHandler(WebhookHandler):
    """Stripe webhook handler"""

    def _get_provider_name(self) -> str:
        """Get the payment provider name"""
        return "stripe"

    async def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Stripe webhook signature using webhook secret"""
        if not self.config.stripe or not self.config.stripe.webhook_secret:
            logger.error("Stripe webhook secret not configured")
            return False

        try:
            # Parse Stripe signature header
            timestamp = None
            signatures = []
            for item in signature.split(","):
                key, value = item.split("=")
                if key == "t":
                    timestamp = value
                elif key == "v1":
                    signatures.append(value)

            if not timestamp or not signatures:
                return False

            # Construct signed payload
            signed_payload = f"{timestamp}.{payload.decode('utf-8')}"

            # Compute expected signature
            expected_signature = hmac.new(
                self.config.stripe.webhook_secret.encode("utf-8"),
                signed_payload.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            # Check if any signature matches
            return any(hmac.compare_digest(sig, expected_signature) for sig in signatures)

        except Exception as e:
            logger.error(f"Failed to verify Stripe signature: {e}")
            return False

    def _extract_event_type(self, data: Dict[str, Any], headers: Dict[str, str]) -> str:
        """Extract Stripe event type"""
        return data.get("type", "")

    def _extract_event_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract Stripe event data"""
        return data.get("data", {}).get("object", {})

    async def process_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Stripe webhook events"""
        logger.info(f"Processing Stripe event: {event_type}")

        # Payment events
        if event_type == "payment_intent.succeeded":
            return await self._handle_payment_succeeded(event_data)
        elif event_type == "payment_intent.payment_failed":
            return await self._handle_payment_failed(event_data)
        elif event_type == "charge.refunded":
            return await self._handle_charge_refunded(event_data)

        # Invoice events
        elif event_type == "invoice.payment_succeeded":
            return await self._handle_invoice_paid(event_data)
        elif event_type == "invoice.payment_failed":
            return await self._handle_invoice_payment_failed(event_data)
        elif event_type == "invoice.finalized":
            return await self._handle_invoice_finalized(event_data)

        # Customer events
        elif event_type == "customer.subscription.created":
            return await self._handle_subscription_created(event_data)
        elif event_type == "customer.subscription.updated":
            return await self._handle_subscription_updated(event_data)
        elif event_type == "customer.subscription.deleted":
            return await self._handle_subscription_cancelled(event_data)

        else:
            logger.info(f"Unhandled Stripe event type: {event_type}")
            return {"status": "ignored", "event_type": event_type}

    async def _handle_payment_succeeded(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment"""
        payment_intent_id = event_data.get("id")
        amount = event_data.get("amount")
        currency = event_data.get("currency")
        metadata = event_data.get("metadata", {})

        tenant_id = metadata.get("tenant_id")
        invoice_id = metadata.get("invoice_id")
        payment_id = metadata.get("payment_id")

        if payment_id and tenant_id:
            # Update payment status
            payment = await self.payment_service.get_payment(tenant_id, payment_id)
            if payment:
                await self.payment_service.update_payment_status(
                    tenant_id,
                    payment_id,
                    PaymentStatus.SUCCEEDED,
                    provider_payment_id=payment_intent_id,
                )

        if invoice_id and tenant_id:
            # Mark invoice as paid
            await self.invoice_service.mark_invoice_paid(
                tenant_id, invoice_id, payment_id=payment_id
            )

        return {
            "status": "processed",
            "payment_intent_id": payment_intent_id,
            "amount": amount,
            "currency": currency,
        }

    async def _handle_payment_failed(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment"""
        payment_intent_id = event_data.get("id")
        error_message = event_data.get("last_payment_error", {}).get("message")
        metadata = event_data.get("metadata", {})

        tenant_id = metadata.get("tenant_id")
        payment_id = metadata.get("payment_id")

        if payment_id and tenant_id:
            # Update payment status
            await self.payment_service.update_payment_status(
                tenant_id,
                payment_id,
                PaymentStatus.FAILED,
                provider_payment_id=payment_intent_id,
                failure_reason=error_message,
            )

        return {
            "status": "processed",
            "payment_intent_id": payment_intent_id,
            "error": error_message,
        }

    async def _handle_charge_refunded(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle charge refund"""
        charge_id = event_data.get("id")
        amount_refunded = event_data.get("amount_refunded")
        metadata = event_data.get("metadata", {})

        tenant_id = metadata.get("tenant_id")
        payment_id = metadata.get("payment_id")

        if payment_id and tenant_id:
            # Process refund
            await self.payment_service.process_refund(
                tenant_id,
                payment_id,
                amount_refunded,
                reason="Charge refunded via Stripe",
            )

        return {
            "status": "processed",
            "charge_id": charge_id,
            "amount_refunded": amount_refunded,
        }

    async def _handle_invoice_paid(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice payment succeeded"""
        stripe_invoice_id = event_data.get("id")
        metadata = event_data.get("metadata", {})
        tenant_id = metadata.get("tenant_id")
        invoice_id = metadata.get("invoice_id")

        if invoice_id and tenant_id:
            await self.invoice_service.mark_invoice_paid(tenant_id, invoice_id)

        return {
            "status": "processed",
            "stripe_invoice_id": stripe_invoice_id,
            "invoice_id": invoice_id,
        }

    async def _handle_invoice_payment_failed(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice payment failed"""
        stripe_invoice_id = event_data.get("id")
        metadata = event_data.get("metadata", {})
        tenant_id = metadata.get("tenant_id")
        invoice_id = metadata.get("invoice_id")

        if invoice_id and tenant_id:
            # Update invoice status
            invoice = await self.invoice_service.get_invoice(tenant_id, invoice_id)
            if invoice:
                invoice.payment_status = PaymentStatus.FAILED
                await self.db.commit()

        return {
            "status": "processed",
            "stripe_invoice_id": stripe_invoice_id,
            "invoice_id": invoice_id,
        }

    async def _handle_invoice_finalized(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice finalized"""
        stripe_invoice_id = event_data.get("id")
        metadata = event_data.get("metadata", {})
        tenant_id = metadata.get("tenant_id")
        invoice_id = metadata.get("invoice_id")

        if invoice_id and tenant_id:
            # Finalize invoice if still draft
            invoice = await self.invoice_service.get_invoice(tenant_id, invoice_id)
            if invoice and invoice.status == InvoiceStatus.DRAFT:
                await self.invoice_service.finalize_invoice(tenant_id, invoice_id)

        return {
            "status": "processed",
            "stripe_invoice_id": stripe_invoice_id,
            "invoice_id": invoice_id,
        }

    async def _handle_subscription_created(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription created"""
        subscription_id = event_data.get("id")
        customer_id = event_data.get("customer")
        metadata = event_data.get("metadata", {})

        logger.info(f"Subscription created: {subscription_id} for customer {customer_id}")

        # TODO: Integrate with subscription service when implemented
        return {
            "status": "acknowledged",
            "subscription_id": subscription_id,
            "customer_id": customer_id,
        }

    async def _handle_subscription_updated(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription updated"""
        subscription_id = event_data.get("id")
        logger.info(f"Subscription updated: {subscription_id}")

        # TODO: Integrate with subscription service when implemented
        return {"status": "acknowledged", "subscription_id": subscription_id}

    async def _handle_subscription_cancelled(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription cancelled"""
        subscription_id = event_data.get("id")
        logger.info(f"Subscription cancelled: {subscription_id}")

        # TODO: Integrate with subscription service when implemented
        return {"status": "acknowledged", "subscription_id": subscription_id}


class PayPalWebhookHandler(WebhookHandler):
    """PayPal webhook handler"""

    def _get_provider_name(self) -> str:
        """Get the payment provider name"""
        return "paypal"

    async def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify PayPal webhook signature"""
        if not self.config.paypal:
            logger.error("PayPal configuration not found")
            return False

        # PayPal webhook verification requires API call to PayPal
        # For now, return True in sandbox mode
        if self.config.paypal.environment == "sandbox":
            logger.warning("PayPal webhook signature verification skipped in sandbox mode")
            return True

        # TODO: Implement PayPal webhook signature verification
        # This requires calling PayPal's verification endpoint
        logger.warning("PayPal webhook signature verification not fully implemented")
        return True

    def _extract_event_type(self, data: Dict[str, Any], headers: Dict[str, str]) -> str:
        """Extract PayPal event type"""
        return data.get("event_type", "")

    def _extract_event_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract PayPal event data"""
        return data.get("resource", {})

    async def process_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process PayPal webhook events"""
        logger.info(f"Processing PayPal event: {event_type}")

        # Payment events
        if event_type == "PAYMENT.CAPTURE.COMPLETED":
            return await self._handle_payment_completed(event_data)
        elif event_type == "PAYMENT.CAPTURE.DENIED":
            return await self._handle_payment_denied(event_data)
        elif event_type == "PAYMENT.CAPTURE.REFUNDED":
            return await self._handle_payment_refunded(event_data)

        # Subscription events
        elif event_type == "BILLING.SUBSCRIPTION.CREATED":
            return await self._handle_subscription_created(event_data)
        elif event_type == "BILLING.SUBSCRIPTION.CANCELLED":
            return await self._handle_subscription_cancelled(event_data)

        else:
            logger.info(f"Unhandled PayPal event type: {event_type}")
            return {"status": "ignored", "event_type": event_type}

    async def _handle_payment_completed(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment completed"""
        capture_id = event_data.get("id")
        amount = event_data.get("amount", {}).get("value")
        currency = event_data.get("amount", {}).get("currency_code")
        custom_id = event_data.get("custom_id")

        # Parse custom_id for tenant_id and payment_id
        if custom_id:
            parts = custom_id.split(":")
            if len(parts) >= 2:
                tenant_id = parts[0]
                payment_id = parts[1]

                # Update payment status
                await self.payment_service.update_payment_status(
                    tenant_id,
                    payment_id,
                    PaymentStatus.SUCCEEDED,
                    provider_payment_id=capture_id,
                )

        return {
            "status": "processed",
            "capture_id": capture_id,
            "amount": amount,
            "currency": currency,
        }

    async def _handle_payment_denied(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment denied"""
        capture_id = event_data.get("id")
        custom_id = event_data.get("custom_id")

        # Parse custom_id for tenant_id and payment_id
        if custom_id:
            parts = custom_id.split(":")
            if len(parts) >= 2:
                tenant_id = parts[0]
                payment_id = parts[1]

                # Update payment status
                await self.payment_service.update_payment_status(
                    tenant_id,
                    payment_id,
                    PaymentStatus.FAILED,
                    provider_payment_id=capture_id,
                    failure_reason="Payment denied by PayPal",
                )

        return {"status": "processed", "capture_id": capture_id}

    async def _handle_payment_refunded(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment refunded"""
        refund_id = event_data.get("id")
        amount = event_data.get("amount", {}).get("value")
        custom_id = event_data.get("custom_id")

        # Parse custom_id for tenant_id and payment_id
        if custom_id:
            parts = custom_id.split(":")
            if len(parts) >= 2:
                tenant_id = parts[0]
                payment_id = parts[1]

                # Process refund
                await self.payment_service.process_refund(
                    tenant_id,
                    payment_id,
                    int(float(amount) * 100),  # Convert to cents
                    reason="Refunded via PayPal",
                )

        return {"status": "processed", "refund_id": refund_id, "amount": amount}

    async def _handle_subscription_created(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription created"""
        subscription_id = event_data.get("id")
        logger.info(f"PayPal subscription created: {subscription_id}")

        # TODO: Integrate with subscription service when implemented
        return {"status": "acknowledged", "subscription_id": subscription_id}

    async def _handle_subscription_cancelled(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription cancelled"""
        subscription_id = event_data.get("id")
        logger.info(f"PayPal subscription cancelled: {subscription_id}")

        # TODO: Integrate with subscription service when implemented
        return {"status": "acknowledged", "subscription_id": subscription_id}