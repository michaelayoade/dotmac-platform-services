# Webhook Handlers - Complete Implementation

## Summary

The webhook handlers for Stripe and PayPal have been fully implemented with:
1. **Complete subscription service integration** - All subscription events are now properly handled
2. **PayPal signature verification** - Full implementation with API-based verification
3. **Comprehensive event handling** - All critical payment and subscription events are processed

## Key Improvements

### 1. Subscription Service Integration

Both Stripe and PayPal webhook handlers now fully integrate with the subscription service:

#### Stripe Subscription Events
- `customer.subscription.created` - Creates subscription in our system
- `customer.subscription.updated` - Updates subscription status (active, past_due, etc.)
- `customer.subscription.deleted` - Cancels subscription
- `customer.subscription.trial_will_end` - Records trial ending event for notifications

#### PayPal Subscription Events
- `BILLING.SUBSCRIPTION.CREATED` - Creates subscription
- `BILLING.SUBSCRIPTION.ACTIVATED` - Activates subscription
- `BILLING.SUBSCRIPTION.UPDATED` - Updates subscription status
- `BILLING.SUBSCRIPTION.CANCELLED` - Cancels subscription
- `BILLING.SUBSCRIPTION.SUSPENDED` - Suspends subscription
- `BILLING.SUBSCRIPTION.PAYMENT.FAILED` - Marks subscription as past due

### 2. PayPal Signature Verification

Complete implementation of PayPal webhook signature verification:

```python
async def verify_signature(self, payload: bytes, signature: str, headers: Dict[str, str] = None) -> bool:
    # Extract required headers
    transmission_id = headers.get("paypal-transmission-id")
    transmission_time = headers.get("paypal-transmission-time")
    cert_url = headers.get("paypal-cert-url")
    auth_algo = headers.get("paypal-auth-algo")
    transmission_sig = headers.get("paypal-transmission-sig")

    # Get OAuth token
    access_token = await self._get_paypal_access_token()

    # Verify with PayPal API
    verification_data = {
        "auth_algo": auth_algo,
        "cert_url": cert_url,
        "transmission_id": transmission_id,
        "transmission_sig": transmission_sig,
        "transmission_time": transmission_time,
        "webhook_id": self.config.paypal.webhook_id,
        "webhook_event": json.loads(payload)
    }

    # Call PayPal verification endpoint
    response = await client.post(
        f"{base_url}/v1/notifications/verify-webhook-signature",
        json=verification_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )

    return response.json().get("verification_status") == "SUCCESS"
```

### 3. Status Mapping

Both handlers properly map provider statuses to our internal statuses:

#### Stripe → Internal Status Mapping
- `active` → ACTIVE
- `past_due` → PAST_DUE
- `canceled` → CANCELLED
- `incomplete` → PENDING
- `incomplete_expired` → EXPIRED
- `trialing` → TRIALING
- `unpaid` → PAST_DUE

#### PayPal → Internal Status Mapping
- `ACTIVE` → ACTIVE
- `SUSPENDED` → SUSPENDED
- `CANCELLED` → CANCELLED
- `EXPIRED` → EXPIRED

## Configuration Requirements

### Stripe Configuration
```python
stripe_config = StripeConfig(
    api_key="sk_live_...",
    webhook_secret="whsec_...",  # Required for signature verification
    publishable_key="pk_live_..."
)
```

### PayPal Configuration
```python
paypal_config = PayPalConfig(
    client_id="...",
    client_secret="...",
    webhook_id="...",  # Required for signature verification
    environment="production"  # or "sandbox"
)
```

## Metadata Convention

To enable full integration, webhook events should include metadata:

### Stripe Metadata
```json
{
  "tenant_id": "tenant_123",
  "customer_id": "customer_123",
  "plan_id": "plan_123",
  "subscription_id": "sub_123"  // For update/cancel events
}
```

### PayPal Custom ID
PayPal uses a `custom_id` field with colon-separated values:
```
tenant_id:customer_id:plan_id
tenant_id:customer_id:subscription_id  // For existing subscriptions
```

## Event Recording

All subscription events are recorded for audit and analytics:
- CREATED
- ACTIVATED
- STATUS_CHANGED
- CANCELLED
- SUSPENDED
- TRIAL_ENDING
- PAYMENT_FAILED

## Security Features

1. **Signature Verification** - All webhooks are cryptographically verified
2. **Fail Closed** - In production, invalid signatures always reject the webhook
3. **Sandbox Mode** - More lenient verification in sandbox for development
4. **Timeout Protection** - API calls have 10-second timeouts
5. **Error Handling** - Comprehensive error handling with logging

## Testing

The implementation includes comprehensive tests in `test_webhook_handlers.py`:
- Signature verification tests
- Event processing tests
- Integration tests
- Error handling tests

## Usage Example

```python
# In your FastAPI app
from dotmac.platform.billing.webhooks.handlers import StripeWebhookHandler

@app.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    payload = await request.body()
    signature = request.headers.get("Stripe-Signature")

    handler = StripeWebhookHandler(db)
    result = await handler.handle_webhook(payload, signature, dict(request.headers))

    return result
```

## Monitoring

The handlers integrate with the metrics system to track:
- Webhook received count by provider and event type
- Processing success/failure rates
- Processing duration

## Future Enhancements

While the handlers are fully functional, potential enhancements include:
1. Webhook replay protection (idempotency)
2. Dead letter queue for failed webhooks
3. Webhook event batching
4. Custom notification triggers
5. Webhook event filtering/routing

## Migration Notes

If you have existing webhook handlers, migration is straightforward:
1. Update configuration to include webhook secrets/IDs
2. Ensure metadata is included in payment/subscription creation
3. Update webhook endpoints to use new handlers
4. Test signature verification in sandbox first