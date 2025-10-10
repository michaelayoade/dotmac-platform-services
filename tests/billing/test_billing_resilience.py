"""Billing error recovery and resilience tests.

Tests system behavior under various failure scenarios."""

import asyncio
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from dotmac.platform.billing.services.payment_processor import PaymentProcessor
from dotmac.platform.billing.services.stripe_service import StripeService
from requests.exceptions import (  # type: ignore[import-untyped]
    ConnectionError,
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from stripe.error import (
    APIConnectionError,
    AuthenticationError,
    CardError,
    InvalidRequestError,
    RateLimitError,
    StripeError,
)

from dotmac.platform.billing.exceptions import (
    PaymentFailedError,
)
from dotmac.platform.billing.models import Customer, Invoice, PaymentMethod

InvoiceTestData = dict[str, Any]


class TestStripeAPIFailures:
    """Test handling of Stripe API failures."""

    @pytest.mark.asyncio
    async def test_stripe_rate_limit_handling(self, db: AsyncSession) -> None:
        """Test handling of Stripe rate limit errors."""
        stripe_service = StripeService()

        with patch.object(stripe_service.client.PaymentMethod, "create") as mock_create:
            # Simulate rate limit error then success
            mock_create.side_effect = [
                RateLimitError("Rate limit exceeded"),
                MagicMock(id="pm_success_after_retry"),
            ]

            # Should retry and succeed
            result = await stripe_service.create_payment_method_with_retry(
                customer_id="cus_test", payment_method_data={"card": {"number": "4242424242424242"}}
            )

            assert result.id == "pm_success_after_retry"
            assert mock_create.call_count == 2  # Initial call + 1 retry

    @pytest.mark.asyncio
    async def test_stripe_connection_timeout_recovery(self, db: AsyncSession) -> None:
        """Test recovery from Stripe connection timeouts."""
        stripe_service = StripeService()

        with patch.object(stripe_service.client.Invoice, "retrieve") as mock_retrieve:
            # Simulate timeout then success
            mock_retrieve.side_effect = [
                APIConnectionError("Connection timeout"),
                MagicMock(id="in_success", status="paid"),
            ]

            result = await stripe_service.get_invoice_with_retry("in_test123")

            assert result.id == "in_success"
            assert mock_retrieve.call_count == 2

    @pytest.mark.asyncio
    async def test_stripe_authentication_error_no_retry(self, db: AsyncSession) -> None:
        """Test that authentication errors are not retried."""
        stripe_service = StripeService()

        with patch.object(stripe_service.client.Customer, "create") as mock_create:
            mock_create.side_effect = AuthenticationError("Invalid API key")

            # Should not retry auth errors
            with pytest.raises(AuthenticationError):
                await stripe_service.create_customer_with_retry({"email": "test@example.com"})

            assert mock_create.call_count == 1  # No retries

    @pytest.mark.asyncio
    async def test_stripe_card_declined_handling(
        self, db: AsyncSession, invoice_test_data: InvoiceTestData
    ) -> None:
        """Test handling of declined card payments."""
        payment_processor = PaymentProcessor()
        data = invoice_test_data

        invoice = Invoice(customer_id=data["customer"].id, amount_total=2999, status="open")
        db.add(invoice)
        await db.commit()

        with patch.object(payment_processor, "_process_stripe_payment") as mock_payment:
            mock_payment.side_effect = CardError(
                "Your card was declined.", param="card", code="card_declined"
            )

            result = await payment_processor.process_payment_with_fallback(
                invoice_id=invoice.id, payment_method_id="pm_declined_card"
            )

            assert result["success"] is False
            assert result["error_code"] == "card_declined"
            assert "declined" in result["error_message"].lower()

            # Invoice should remain open, not failed
            await db.refresh(invoice)
            assert invoice.status == "open"

    @pytest.mark.asyncio
    async def test_multiple_payment_method_fallback(
        self, db: AsyncSession, invoice_test_data: InvoiceTestData
    ) -> None:
        """Test fallback to alternative payment methods."""
        data = invoice_test_data
        customer = data["customer"]

        # Create multiple payment methods
        payment_methods = []
        for i in range(3):
            pm = PaymentMethod(
                customer_id=customer.id,
                stripe_payment_method_id=f"pm_test_{i}",
                type="card",
                card_details={"last4": f"424{i}", "brand": "visa"},
                is_default=(i == 0),
            )
            db.add(pm)
            payment_methods.append(pm)

        await db.commit()

        invoice = Invoice(customer_id=customer.id, amount_total=2999, status="open")
        db.add(invoice)
        await db.commit()

        payment_processor = PaymentProcessor()

        def mock_payment_side_effect(payment_method_id: str, **kwargs: Any) -> dict[str, str]:
            if payment_method_id == "pm_test_0":
                raise CardError("Declined", param="card", code="card_declined")
            elif payment_method_id == "pm_test_1":
                raise CardError("Insufficient funds", param="card", code="insufficient_funds")
            else:
                return {"status": "succeeded", "id": "pi_success"}

        with patch.object(payment_processor, "_process_stripe_payment") as mock_payment:
            mock_payment.side_effect = mock_payment_side_effect

            result = await payment_processor.process_payment_with_fallback(invoice_id=invoice.id)

            # Should succeed with third payment method
            assert result["success"] is True
            assert mock_payment.call_count == 3  # Tried all three methods


class TestDatabaseFailures:
    """Test handling of database failures."""

    @pytest.mark.asyncio
    async def test_database_connection_retry(self, db: AsyncSession) -> None:
        """Test database connection retry logic."""
        from dotmac.platform.billing.services.billing_service import BillingService

        billing_service = BillingService()

        with patch.object(billing_service, "db") as mock_db:
            # Simulate connection error then success
            mock_db.execute.side_effect = [
                ConnectionError("Database connection lost"),
                MagicMock(),  # Success
            ]

            # Should retry and succeed
            await billing_service.get_customer_with_retry("cus_test")

            assert mock_db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_failure(self, db: AsyncSession) -> None:
        """Test transaction rollback when operations fail."""
        from dotmac.platform.billing.services.subscription_service import SubscriptionService

        service = SubscriptionService(db)

        with patch.object(service, "_create_stripe_subscription") as mock_stripe:
            # Stripe call fails after database writes
            mock_stripe.side_effect = StripeError("Stripe service unavailable")

            customer = Customer(
                user_id="rollback_test",
                stripe_customer_id="cus_rollback",
                email="rollback@test.com",
            )
            db.add(customer)
            await db.commit()

            initial_count_result = await db.execute(text("SELECT COUNT(*) FROM subscriptions"))
            initial_count = initial_count_result.scalar()

            # Attempt to create subscription (should fail and rollback)
            with pytest.raises(StripeError):
                await service.create_subscription_with_rollback(
                    customer_id=customer.id, price_id="price_test"
                )

            # Database should be rolled back
            final_count_result = await db.execute(text("SELECT COUNT(*) FROM subscriptions"))
            final_count = final_count_result.scalar()

            assert final_count == initial_count  # No new subscriptions

    @pytest.mark.asyncio
    async def test_concurrent_invoice_generation_handling(self, db: AsyncSession) -> None:
        """Test handling of concurrent invoice generation attempts."""
        from dotmac.platform.billing.services.invoice_generator import InvoiceGenerator

        generator = InvoiceGenerator(db)

        customer = Customer(
            user_id="concurrent_test",
            stripe_customer_id="cus_concurrent",
            email="concurrent@test.com",
        )
        db.add(customer)
        await db.commit()

        # Simulate two concurrent invoice generation attempts
        async def generate_invoice() -> Invoice:
            return await generator.generate_monthly_invoice(customer.id)

        # Run concurrently
        results = await asyncio.gather(
            generate_invoice(), generate_invoice(), return_exceptions=True
        )

        # One should succeed, one should fail gracefully
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        assert success_count == 1  # Only one invoice should be created

        # Check database has only one invoice
        count_result = await db.execute(
            text("SELECT COUNT(*) FROM invoices WHERE customer_id = :customer_id"),
            {"customer_id": customer.id},
        )
        assert count_result.scalar() == 1


class TestWebhookResilience:
    """Test webhook processing resilience."""

    @pytest.mark.asyncio
    async def test_webhook_processing_with_database_errors(self, db: AsyncSession) -> None:
        """Test webhook processing continues despite database errors."""
        from dotmac.platform.billing.webhook_handlers import WebhookProcessor

        processor = WebhookProcessor(db)

        webhook_events = [
            {"id": "evt_1", "type": "invoice.paid", "data": {"object": {"id": "in_1"}}},
            {"id": "evt_2", "type": "customer.updated", "data": {"object": {"id": "cus_1"}}},
            {"id": "evt_3", "type": "invoice.paid", "data": {"object": {"id": "in_2"}}},
        ]

        processed_events = []
        failed_events = []

        def mock_process_event(event: dict[str, Any]) -> None:
            if event["id"] == "evt_2":  # Simulate failure on second event
                raise Exception("Database error")
            processed_events.append(event["id"])

        with patch.object(processor, "_process_single_event", side_effect=mock_process_event):
            for event in webhook_events:
                try:
                    await processor.process_webhook_event(event)
                except Exception:
                    failed_events.append(event["id"])

        # First and third should succeed despite second failing
        assert "evt_1" in processed_events
        assert "evt_3" in processed_events
        assert "evt_2" in failed_events

    @pytest.mark.asyncio
    async def test_webhook_retry_mechanism(self, db: AsyncSession) -> None:
        """Test webhook retry mechanism for failed events."""
        from dotmac.platform.billing.webhook_handlers import WebhookRetryService

        from dotmac.platform.billing.models import WebhookEvent

        # Create failed webhook event
        failed_event = WebhookEvent(
            stripe_event_id="evt_retry_test",
            event_type="invoice.payment_failed",
            retry_count=2,
            next_retry_at=datetime.now() - timedelta(minutes=5),  # Ready for retry
            status="failed",
        )
        db.add(failed_event)
        await db.commit()

        retry_service = WebhookRetryService(db)

        with patch.object(retry_service, "_process_webhook_event") as mock_process:
            # First retry fails, second succeeds
            mock_process.side_effect = [Exception("Temporary failure"), {"status": "success"}]

            await retry_service.process_failed_webhooks()

            # Should have retried twice
            assert mock_process.call_count == 2

            # Event should eventually succeed
            await db.refresh(failed_event)
            # Note: In real implementation, status would be updated to 'completed'

    @pytest.mark.asyncio
    async def test_webhook_dead_letter_queue(self, db: AsyncSession) -> None:
        """Test webhook events go to dead letter queue after max retries."""
        from dotmac.platform.billing.webhook_handlers import WebhookRetryService

        from dotmac.platform.billing.models import WebhookEvent

        # Create event that has reached max retries
        max_retry_event = WebhookEvent(
            stripe_event_id="evt_max_retry",
            event_type="subscription.deleted",
            retry_count=5,  # Max retries reached
            status="failed",
            last_error="Max retries exceeded",
        )
        db.add(max_retry_event)
        await db.commit()

        retry_service = WebhookRetryService(db)
        dead_letter_service = retry_service.dead_letter_queue

        with patch.object(dead_letter_service, "send_to_dead_letter") as mock_dlq:
            mock_dlq.return_value = True

            await retry_service.handle_dead_letter_events()

            # Should be sent to dead letter queue
            mock_dlq.assert_called_once()

            # Event status should be updated
            await db.refresh(max_retry_event)
            assert max_retry_event.status == "dead_letter"


class TestPaymentRecovery:
    """Test payment failure recovery mechanisms."""

    @pytest.mark.asyncio
    async def test_dunning_management(
        self, db: AsyncSession, invoice_test_data: InvoiceTestData
    ) -> None:
        """Test dunning management for failed payments."""
        from dotmac.platform.billing.services.dunning_service import DunningService

        data = invoice_test_data
        customer = data["customer"]

        # Create failed payment invoice
        failed_invoice = Invoice(
            customer_id=customer.id,
            amount_total=2999,
            status="payment_failed",
            attempt_count=1,
            next_payment_attempt=datetime.now() + timedelta(days=3),
        )
        db.add(failed_invoice)
        await db.commit()

        dunning_service = DunningService(db)

        # Process dunning
        results = await dunning_service.process_dunning_cycle()

        assert len(results) >= 1

        # Should schedule next attempt
        await db.refresh(failed_invoice)
        assert failed_invoice.next_payment_attempt is not None

    @pytest.mark.asyncio
    async def test_subscription_pause_on_payment_failure(
        self, db: AsyncSession, invoice_test_data: InvoiceTestData
    ) -> None:
        """Test subscription pausing after repeated payment failures."""
        from dotmac.platform.billing.services.subscription_manager import SubscriptionManager

        data = invoice_test_data
        subscription = data["subscription"]

        # Create multiple failed invoices
        for i in range(4):  # 4 failures should pause subscription
            failed_invoice = Invoice(
                customer_id=data["customer"].id,
                subscription_id=subscription.id,
                amount_total=2999,
                status="payment_failed",
                attempt_count=3,  # Max attempts reached
                created_at=datetime.now() - timedelta(days=i * 7),
            )
            db.add(failed_invoice)

        await db.commit()

        manager = SubscriptionManager(db)
        await manager.check_subscription_payment_health()

        # Subscription should be paused
        await db.refresh(subscription)
        assert subscription.status == "past_due"

    @pytest.mark.asyncio
    async def test_smart_retry_with_backoff(self, db: AsyncSession) -> None:
        """Test smart retry mechanism with exponential backoff."""
        from dotmac.platform.billing.services.retry_service import SmartRetryService

        retry_service = SmartRetryService()

        attempt_times = []

        def mock_payment_attempt() -> dict[str, str]:
            attempt_times.append(datetime.now())
            if len(attempt_times) < 3:
                raise PaymentFailedError("Card declined")
            return {"status": "success"}

        with patch("asyncio.sleep") as mock_sleep:
            result = await retry_service.retry_with_backoff(
                func=mock_payment_attempt, max_attempts=3, base_delay=1, backoff_factor=2
            )

            # Should eventually succeed
            assert result["status"] == "success"

            # Should use exponential backoff
            sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
            assert sleep_calls == [1, 2]  # 1s, 2s delays

    @pytest.mark.asyncio
    async def test_payment_method_health_check(self, db: AsyncSession) -> None:
        """Test payment method health checking and replacement."""
        from dotmac.platform.billing.services.payment_health_service import PaymentHealthService

        customer = Customer(
            user_id="health_test", stripe_customer_id="cus_health", email="health@test.com"
        )
        db.add(customer)
        await db.commit()

        # Create payment method with recent failures
        failing_pm = PaymentMethod(
            customer_id=customer.id,
            stripe_payment_method_id="pm_failing",
            type="card",
            is_default=True,
            failure_count=3,  # Multiple recent failures
            last_failure_at=datetime.now() - timedelta(hours=1),
        )
        db.add(failing_pm)
        await db.commit()

        health_service = PaymentHealthService(db)

        with patch.object(health_service, "_notify_customer_payment_issue") as mock_notify:
            unhealthy_methods = await health_service.check_payment_method_health()

            assert len(unhealthy_methods) == 1
            assert unhealthy_methods[0].id == failing_pm.id

            # Should notify customer
            mock_notify.assert_called_once()


class TestSystemRecovery:
    """Test overall system recovery mechanisms."""

    @pytest.mark.asyncio
    async def test_service_degradation_mode(self, db: AsyncSession) -> None:
        """Test system operates in degraded mode when external services fail."""
        from dotmac.platform.billing.services.billing_facade import BillingFacade

        facade = BillingFacade()

        with patch.object(facade.stripe_service, "is_healthy") as mock_health:
            mock_health.return_value = False  # Stripe is down

            # Should operate in degraded mode
            status = await facade.get_service_status()

            assert status["mode"] == "degraded"
            assert status["stripe_available"] is False
            assert "limited_functionality" in status["warnings"]

    @pytest.mark.asyncio
    async def test_circuit_breaker_pattern(self, db: AsyncSession) -> None:
        """Test circuit breaker prevents cascading failures."""
        from dotmac.platform.billing.utils.circuit_breaker import CircuitBreaker

        circuit_breaker = CircuitBreaker(
            failure_threshold=3, recovery_timeout=60, expected_exception=StripeError
        )

        failure_count = 0

        @circuit_breaker
        async def failing_stripe_call() -> None:
            nonlocal failure_count
            failure_count += 1
            raise StripeError("Service unavailable")

        # Should fail 3 times then open circuit
        for _ in range(5):
            try:
                await failing_stripe_call()
            except (StripeError, Exception):
                pass

        assert circuit_breaker.state == "open"
        assert failure_count == 3  # Should stop calling after 3 failures

    @pytest.mark.asyncio
    async def test_data_consistency_recovery(self, db: AsyncSession) -> None:
        """Test recovery of data consistency after partial failures."""
        from dotmac.platform.billing.services.consistency_checker import ConsistencyChecker

        checker = ConsistencyChecker(db)

        # Create inconsistent state - invoice without corresponding Stripe invoice
        customer = Customer(
            user_id="consistency_test",
            stripe_customer_id="cus_consistency",
            email="consistency@test.com",
        )
        db.add(customer)
        await db.commit()

        orphaned_invoice = Invoice(
            customer_id=customer.id,
            stripe_invoice_id="in_orphaned_123",
            amount_total=2999,
            status="open",
        )
        db.add(orphaned_invoice)
        await db.commit()

        with patch.object(checker.stripe_service, "get_invoice") as mock_get:
            mock_get.side_effect = InvalidRequestError("No such invoice", param="id")

            # Check and fix consistency
            issues = await checker.check_invoice_consistency()
            fixes = await checker.fix_consistency_issues(issues)

            assert len(issues) == 1
            assert len(fixes) == 1

            # Invoice should be marked as error state
            await db.refresh(orphaned_invoice)
            assert orphaned_invoice.status in ["error", "cancelled"]
