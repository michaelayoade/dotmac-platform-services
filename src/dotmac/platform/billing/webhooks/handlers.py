"""
Webhook handlers for payment providers with complete subscription integration
"""

import hashlib
import hmac
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import httpx
import base64

from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.billing.config import BillingConfig, get_billing_config
from dotmac.platform.billing.core.enums import PaymentStatus, InvoiceStatus
from dotmac.platform.billing.invoicing.service import InvoiceService
from dotmac.platform.billing.payments.service import PaymentService
from dotmac.platform.billing.subscriptions.service import SubscriptionService
from dotmac.platform.billing.subscriptions.models import (
    SubscriptionCreateRequest,
    SubscriptionUpdateRequest,
    SubscriptionStatus,
    SubscriptionEventType,
)
from dotmac.platform.billing.metrics import get_billing_metrics

logger = logging.getLogger(__name__)


class WebhookHandler(ABC):
    """Base webhook handler interface with subscription support"""

    def __init__(self, db: AsyncSession, config: Optional[BillingConfig] = None):
        self.db = db
        self.config = config or get_billing_config()
        self.invoice_service = InvoiceService(db)
        self.payment_service = PaymentService(db)
        self.subscription_service = SubscriptionService()  # Initialize subscription service
        self.metrics = get_billing_metrics()

    @abstractmethod
    async def verify_signature(self, payload: bytes, signature: str, headers: Dict[str, str] = None) -> bool:
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
        if not await self.verify_signature(payload, signature, headers):
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
    """Stripe webhook handler with full subscription integration"""

    def _get_provider_name(self) -> str:
        """Get the payment provider name"""
        return "stripe"

    async def verify_signature(self, payload: bytes, signature: str, headers: Dict[str, str] = None) -> bool:
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

        # Customer subscription events
        elif event_type == "customer.subscription.created":
            return await self._handle_subscription_created(event_data)
        elif event_type == "customer.subscription.updated":
            return await self._handle_subscription_updated(event_data)
        elif event_type == "customer.subscription.deleted":
            return await self._handle_subscription_cancelled(event_data)
        elif event_type == "customer.subscription.trial_will_end":
            return await self._handle_subscription_trial_ending(event_data)

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
        """Handle subscription created with full integration"""
        subscription_id = event_data.get("id")
        customer_id = event_data.get("customer")
        metadata = event_data.get("metadata", {})

        tenant_id = metadata.get("tenant_id")
        customer_id_internal = metadata.get("customer_id")
        plan_id = metadata.get("plan_id")

        logger.info(f"Subscription created: {subscription_id} for customer {customer_id}")

        if tenant_id and customer_id_internal and plan_id:
            try:
                # Create subscription in our system
                subscription_request = SubscriptionCreateRequest(
                    customer_id=customer_id_internal,
                    plan_id=plan_id,
                    provider_subscription_id=subscription_id,
                    metadata={
                        "stripe_customer_id": customer_id,
                        "stripe_subscription_id": subscription_id,
                        "created_via": "stripe_webhook"
                    }
                )

                subscription = await self.subscription_service.create_subscription(
                    subscription_data=subscription_request,
                    tenant_id=tenant_id
                )

                # Record subscription created event
                await self.subscription_service.record_event(
                    subscription_id=subscription.subscription_id,
                    tenant_id=tenant_id,
                    event_type=SubscriptionEventType.CREATED,
                    event_data={
                        "source": "stripe_webhook",
                        "stripe_subscription_id": subscription_id
                    }
                )

                logger.info(f"Created subscription {subscription.subscription_id} from Stripe webhook")

                return {
                    "status": "processed",
                    "subscription_id": subscription.subscription_id,
                    "stripe_subscription_id": subscription_id,
                }
            except Exception as e:
                logger.error(f"Failed to create subscription from webhook: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "stripe_subscription_id": subscription_id,
                }

        return {
            "status": "acknowledged",
            "subscription_id": subscription_id,
            "message": "Missing metadata for full integration"
        }

    async def _handle_subscription_updated(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription updated with full integration"""
        stripe_subscription_id = event_data.get("id")
        status = event_data.get("status")
        metadata = event_data.get("metadata", {})

        tenant_id = metadata.get("tenant_id")
        subscription_id = metadata.get("subscription_id")

        logger.info(f"Subscription updated: {stripe_subscription_id}, status: {status}")

        if tenant_id and subscription_id:
            try:
                # Map Stripe status to our status
                status_map = {
                    "active": SubscriptionStatus.ACTIVE,
                    "past_due": SubscriptionStatus.PAST_DUE,
                    "canceled": SubscriptionStatus.CANCELLED,
                    "incomplete": SubscriptionStatus.PENDING,
                    "incomplete_expired": SubscriptionStatus.EXPIRED,
                    "trialing": SubscriptionStatus.TRIALING,
                    "unpaid": SubscriptionStatus.PAST_DUE,
                }

                new_status = status_map.get(status)

                if new_status:
                    # Update subscription status
                    subscription = await self.subscription_service.get_subscription(
                        subscription_id=subscription_id,
                        tenant_id=tenant_id
                    )

                    if subscription and subscription.status != new_status:
                        update_request = SubscriptionUpdateRequest(
                            status=new_status,
                            metadata=subscription.metadata or {}
                        )
                        update_request.metadata["last_stripe_update"] = datetime.now(timezone.utc).isoformat()

                        await self.subscription_service.update_subscription(
                            subscription_id=subscription_id,
                            tenant_id=tenant_id,
                            update_data=update_request
                        )

                        # Record status change event
                        await self.subscription_service.record_event(
                            subscription_id=subscription_id,
                            tenant_id=tenant_id,
                            event_type=SubscriptionEventType.STATUS_CHANGED,
                            event_data={
                                "old_status": subscription.status.value,
                                "new_status": new_status.value,
                                "source": "stripe_webhook"
                            }
                        )

                        logger.info(f"Updated subscription {subscription_id} status to {new_status.value}")

                return {
                    "status": "processed",
                    "subscription_id": subscription_id,
                    "new_status": new_status.value if new_status else status
                }
            except Exception as e:
                logger.error(f"Failed to update subscription from webhook: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "stripe_subscription_id": stripe_subscription_id,
                }

        return {"status": "acknowledged", "subscription_id": stripe_subscription_id}

    async def _handle_subscription_cancelled(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription cancelled with full integration"""
        stripe_subscription_id = event_data.get("id")
        metadata = event_data.get("metadata", {})

        tenant_id = metadata.get("tenant_id")
        subscription_id = metadata.get("subscription_id")

        logger.info(f"Subscription cancelled: {stripe_subscription_id}")

        if tenant_id and subscription_id:
            try:
                # Cancel subscription in our system
                await self.subscription_service.cancel_subscription(
                    subscription_id=subscription_id,
                    tenant_id=tenant_id,
                    reason="Cancelled via Stripe",
                    immediate=True  # Stripe already cancelled it
                )

                # Record cancellation event
                await self.subscription_service.record_event(
                    subscription_id=subscription_id,
                    tenant_id=tenant_id,
                    event_type=SubscriptionEventType.CANCELLED,
                    event_data={
                        "source": "stripe_webhook",
                        "stripe_subscription_id": stripe_subscription_id,
                        "reason": "Cancelled via Stripe"
                    }
                )

                logger.info(f"Cancelled subscription {subscription_id} from Stripe webhook")

                return {
                    "status": "processed",
                    "subscription_id": subscription_id,
                    "message": "Subscription cancelled"
                }
            except Exception as e:
                logger.error(f"Failed to cancel subscription from webhook: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "stripe_subscription_id": stripe_subscription_id,
                }

        return {"status": "acknowledged", "subscription_id": stripe_subscription_id}

    async def _handle_subscription_trial_ending(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription trial ending notification"""
        stripe_subscription_id = event_data.get("id")
        trial_end = event_data.get("trial_end")
        metadata = event_data.get("metadata", {})

        tenant_id = metadata.get("tenant_id")
        subscription_id = metadata.get("subscription_id")

        logger.info(f"Subscription trial ending: {stripe_subscription_id}")

        if tenant_id and subscription_id:
            # Record trial ending event
            await self.subscription_service.record_event(
                subscription_id=subscription_id,
                tenant_id=tenant_id,
                event_type=SubscriptionEventType.TRIAL_ENDING,
                event_data={
                    "trial_end": trial_end,
                    "source": "stripe_webhook"
                }
            )

            # Could trigger notifications to customer here

            return {
                "status": "processed",
                "subscription_id": subscription_id,
                "trial_end": trial_end
            }

        return {"status": "acknowledged", "subscription_id": stripe_subscription_id}


class PayPalWebhookHandler(WebhookHandler):
    """PayPal webhook handler with signature verification and subscription integration"""

    def _get_provider_name(self) -> str:
        """Get the payment provider name"""
        return "paypal"

    async def verify_signature(self, payload: bytes, signature: str, headers: Dict[str, str] = None) -> bool:
        """Verify PayPal webhook signature with full implementation"""
        if not self.config.paypal:
            logger.error("PayPal configuration not found")
            return False

        # PayPal webhook verification requires API call to PayPal
        if self.config.paypal.environment == "sandbox":
            logger.warning("PayPal webhook signature verification in sandbox mode")
            # In sandbox, optionally verify if webhook_id is configured
            if not self.config.paypal.webhook_id:
                logger.warning("PayPal webhook ID not configured, skipping verification in sandbox")
                return True

        try:
            # Extract required headers for PayPal verification
            if not headers:
                logger.error("Missing headers for PayPal webhook verification")
                return False

            transmission_id = headers.get("paypal-transmission-id", "")
            transmission_time = headers.get("paypal-transmission-time", "")
            cert_url = headers.get("paypal-cert-url", "")
            auth_algo = headers.get("paypal-auth-algo", "")
            transmission_sig = headers.get("paypal-transmission-sig", signature)

            if not all([transmission_id, transmission_time, cert_url, auth_algo, transmission_sig]):
                logger.error("Missing required PayPal webhook headers")
                return False

            # Construct verification request
            verification_url = f"{self._get_paypal_base_url()}/v1/notifications/verify-webhook-signature"

            verification_data = {
                "auth_algo": auth_algo,
                "cert_url": cert_url,
                "transmission_id": transmission_id,
                "transmission_sig": transmission_sig,
                "transmission_time": transmission_time,
                "webhook_id": self.config.paypal.webhook_id,
                "webhook_event": json.loads(payload)
            }

            # Get PayPal access token
            access_token = await self._get_paypal_access_token()

            # Make verification request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    verification_url,
                    json=verification_data,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    },
                    timeout=10.0
                )

                if response.status_code == 200:
                    result = response.json()
                    verification_status = result.get("verification_status")

                    if verification_status == "SUCCESS":
                        logger.info("PayPal webhook signature verified successfully")
                        return True
                    else:
                        logger.warning(f"PayPal webhook verification failed: {verification_status}")
                        return False
                else:
                    logger.error(f"PayPal verification API error: {response.status_code}")
                    # In production, we should fail closed (return False)
                    # But for development/testing, we might want to be more lenient
                    if self.config.paypal.environment == "sandbox":
                        logger.warning("Allowing webhook in sandbox despite verification failure")
                        return True
                    return False

        except Exception as e:
            logger.error(f"Failed to verify PayPal signature: {e}")
            # Fail closed in production
            if self.config.paypal.environment == "production":
                return False
            # Be lenient in sandbox for development
            logger.warning("Allowing webhook in sandbox despite verification error")
            return True

    def _get_paypal_base_url(self) -> str:
        """Get PayPal API base URL based on environment"""
        if self.config.paypal.environment == "sandbox":
            return "https://api.sandbox.paypal.com"
        return "https://api.paypal.com"

    async def _get_paypal_access_token(self) -> str:
        """Get PayPal OAuth access token"""
        auth_url = f"{self._get_paypal_base_url()}/v1/oauth2/token"

        # Create basic auth header
        credentials = f"{self.config.paypal.client_id}:{self.config.paypal.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                auth_url,
                data={"grant_type": "client_credentials"},
                headers={
                    "Authorization": f"Basic {encoded_credentials}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                timeout=10.0
            )

            if response.status_code == 200:
                token_data = response.json()
                return token_data.get("access_token")
            else:
                raise Exception(f"Failed to get PayPal access token: {response.status_code}")

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
        elif event_type == "BILLING.SUBSCRIPTION.ACTIVATED":
            return await self._handle_subscription_activated(event_data)
        elif event_type == "BILLING.SUBSCRIPTION.UPDATED":
            return await self._handle_subscription_updated(event_data)
        elif event_type == "BILLING.SUBSCRIPTION.CANCELLED":
            return await self._handle_subscription_cancelled(event_data)
        elif event_type == "BILLING.SUBSCRIPTION.SUSPENDED":
            return await self._handle_subscription_suspended(event_data)
        elif event_type == "BILLING.SUBSCRIPTION.PAYMENT.FAILED":
            return await self._handle_subscription_payment_failed(event_data)

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
        """Handle subscription created with full integration"""
        paypal_subscription_id = event_data.get("id")
        plan_id = event_data.get("plan_id")
        custom_id = event_data.get("custom_id")

        logger.info(f"PayPal subscription created: {paypal_subscription_id}")

        # Parse custom_id for tenant_id and customer_id
        if custom_id:
            parts = custom_id.split(":")
            if len(parts) >= 2:
                tenant_id = parts[0]
                customer_id = parts[1]
                internal_plan_id = parts[2] if len(parts) > 2 else plan_id

                try:
                    # Create subscription in our system
                    subscription_request = SubscriptionCreateRequest(
                        customer_id=customer_id,
                        plan_id=internal_plan_id,
                        provider_subscription_id=paypal_subscription_id,
                        metadata={
                            "paypal_subscription_id": paypal_subscription_id,
                            "paypal_plan_id": plan_id,
                            "created_via": "paypal_webhook"
                        }
                    )

                    subscription = await self.subscription_service.create_subscription(
                        subscription_data=subscription_request,
                        tenant_id=tenant_id
                    )

                    # Record subscription created event
                    await self.subscription_service.record_event(
                        subscription_id=subscription.subscription_id,
                        tenant_id=tenant_id,
                        event_type=SubscriptionEventType.CREATED,
                        event_data={
                            "source": "paypal_webhook",
                            "paypal_subscription_id": paypal_subscription_id
                        }
                    )

                    logger.info(f"Created subscription {subscription.subscription_id} from PayPal webhook")

                    return {
                        "status": "processed",
                        "subscription_id": subscription.subscription_id,
                        "paypal_subscription_id": paypal_subscription_id,
                    }
                except Exception as e:
                    logger.error(f"Failed to create subscription from PayPal webhook: {e}")
                    return {
                        "status": "error",
                        "error": str(e),
                        "paypal_subscription_id": paypal_subscription_id,
                    }

        return {"status": "acknowledged", "subscription_id": paypal_subscription_id}

    async def _handle_subscription_activated(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription activated"""
        paypal_subscription_id = event_data.get("id")
        custom_id = event_data.get("custom_id")

        if custom_id:
            parts = custom_id.split(":")
            if len(parts) >= 3:
                tenant_id = parts[0]
                subscription_id = parts[2]  # Our internal subscription ID

                try:
                    # Update subscription status to active
                    update_request = SubscriptionUpdateRequest(
                        status=SubscriptionStatus.ACTIVE,
                        metadata={"paypal_activated": datetime.now(timezone.utc).isoformat()}
                    )

                    await self.subscription_service.update_subscription(
                        subscription_id=subscription_id,
                        tenant_id=tenant_id,
                        update_data=update_request
                    )

                    # Record activation event
                    await self.subscription_service.record_event(
                        subscription_id=subscription_id,
                        tenant_id=tenant_id,
                        event_type=SubscriptionEventType.ACTIVATED,
                        event_data={
                            "source": "paypal_webhook",
                            "paypal_subscription_id": paypal_subscription_id
                        }
                    )

                    return {
                        "status": "processed",
                        "subscription_id": subscription_id,
                        "message": "Subscription activated"
                    }
                except Exception as e:
                    logger.error(f"Failed to activate subscription: {e}")
                    return {"status": "error", "error": str(e)}

        return {"status": "acknowledged", "subscription_id": paypal_subscription_id}

    async def _handle_subscription_updated(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription updated"""
        paypal_subscription_id = event_data.get("id")
        status = event_data.get("status")
        custom_id = event_data.get("custom_id")

        logger.info(f"PayPal subscription updated: {paypal_subscription_id}, status: {status}")

        if custom_id:
            parts = custom_id.split(":")
            if len(parts) >= 3:
                tenant_id = parts[0]
                subscription_id = parts[2]

                try:
                    # Map PayPal status to our status
                    status_map = {
                        "ACTIVE": SubscriptionStatus.ACTIVE,
                        "SUSPENDED": SubscriptionStatus.SUSPENDED,
                        "CANCELLED": SubscriptionStatus.CANCELLED,
                        "EXPIRED": SubscriptionStatus.EXPIRED,
                    }

                    new_status = status_map.get(status)

                    if new_status:
                        update_request = SubscriptionUpdateRequest(
                            status=new_status,
                            metadata={"last_paypal_update": datetime.now(timezone.utc).isoformat()}
                        )

                        await self.subscription_service.update_subscription(
                            subscription_id=subscription_id,
                            tenant_id=tenant_id,
                            update_data=update_request
                        )

                        # Record status change event
                        await self.subscription_service.record_event(
                            subscription_id=subscription_id,
                            tenant_id=tenant_id,
                            event_type=SubscriptionEventType.STATUS_CHANGED,
                            event_data={
                                "new_status": new_status.value,
                                "source": "paypal_webhook"
                            }
                        )

                        return {
                            "status": "processed",
                            "subscription_id": subscription_id,
                            "new_status": new_status.value
                        }
                except Exception as e:
                    logger.error(f"Failed to update subscription: {e}")
                    return {"status": "error", "error": str(e)}

        return {"status": "acknowledged", "subscription_id": paypal_subscription_id}

    async def _handle_subscription_cancelled(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription cancelled with full integration"""
        paypal_subscription_id = event_data.get("id")
        custom_id = event_data.get("custom_id")

        logger.info(f"PayPal subscription cancelled: {paypal_subscription_id}")

        if custom_id:
            parts = custom_id.split(":")
            if len(parts) >= 3:
                tenant_id = parts[0]
                subscription_id = parts[2]

                try:
                    # Cancel subscription in our system
                    await self.subscription_service.cancel_subscription(
                        subscription_id=subscription_id,
                        tenant_id=tenant_id,
                        reason="Cancelled via PayPal",
                        immediate=True  # PayPal already cancelled it
                    )

                    # Record cancellation event
                    await self.subscription_service.record_event(
                        subscription_id=subscription_id,
                        tenant_id=tenant_id,
                        event_type=SubscriptionEventType.CANCELLED,
                        event_data={
                            "source": "paypal_webhook",
                            "paypal_subscription_id": paypal_subscription_id,
                            "reason": "Cancelled via PayPal"
                        }
                    )

                    return {
                        "status": "processed",
                        "subscription_id": subscription_id,
                        "message": "Subscription cancelled"
                    }
                except Exception as e:
                    logger.error(f"Failed to cancel subscription: {e}")
                    return {"status": "error", "error": str(e)}

        return {"status": "acknowledged", "subscription_id": paypal_subscription_id}

    async def _handle_subscription_suspended(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription suspended"""
        paypal_subscription_id = event_data.get("id")
        custom_id = event_data.get("custom_id")

        if custom_id:
            parts = custom_id.split(":")
            if len(parts) >= 3:
                tenant_id = parts[0]
                subscription_id = parts[2]

                try:
                    # Update subscription status to suspended
                    update_request = SubscriptionUpdateRequest(
                        status=SubscriptionStatus.SUSPENDED,
                        metadata={"paypal_suspended": datetime.now(timezone.utc).isoformat()}
                    )

                    await self.subscription_service.update_subscription(
                        subscription_id=subscription_id,
                        tenant_id=tenant_id,
                        update_data=update_request
                    )

                    # Record suspension event
                    await self.subscription_service.record_event(
                        subscription_id=subscription_id,
                        tenant_id=tenant_id,
                        event_type=SubscriptionEventType.SUSPENDED,
                        event_data={
                            "source": "paypal_webhook",
                            "paypal_subscription_id": paypal_subscription_id
                        }
                    )

                    return {
                        "status": "processed",
                        "subscription_id": subscription_id,
                        "message": "Subscription suspended"
                    }
                except Exception as e:
                    logger.error(f"Failed to suspend subscription: {e}")
                    return {"status": "error", "error": str(e)}

        return {"status": "acknowledged", "subscription_id": paypal_subscription_id}

    async def _handle_subscription_payment_failed(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription payment failed"""
        paypal_subscription_id = event_data.get("id")
        custom_id = event_data.get("custom_id")

        if custom_id:
            parts = custom_id.split(":")
            if len(parts) >= 3:
                tenant_id = parts[0]
                subscription_id = parts[2]

                try:
                    # Update subscription status to past due
                    update_request = SubscriptionUpdateRequest(
                        status=SubscriptionStatus.PAST_DUE,
                        metadata={"last_payment_failed": datetime.now(timezone.utc).isoformat()}
                    )

                    await self.subscription_service.update_subscription(
                        subscription_id=subscription_id,
                        tenant_id=tenant_id,
                        update_data=update_request
                    )

                    # Record payment failed event
                    await self.subscription_service.record_event(
                        subscription_id=subscription_id,
                        tenant_id=tenant_id,
                        event_type=SubscriptionEventType.PAYMENT_FAILED,
                        event_data={
                            "source": "paypal_webhook",
                            "paypal_subscription_id": paypal_subscription_id
                        }
                    )

                    return {
                        "status": "processed",
                        "subscription_id": subscription_id,
                        "message": "Subscription payment failed, status updated to past_due"
                    }
                except Exception as e:
                    logger.error(f"Failed to update subscription after payment failure: {e}")
                    return {"status": "error", "error": str(e)}

        return {"status": "acknowledged", "subscription_id": paypal_subscription_id}