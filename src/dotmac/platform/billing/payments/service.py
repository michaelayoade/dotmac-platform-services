"""
Payment processing service with tenant support and idempotency
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.billing.core.entities import (
    PaymentEntity,
    PaymentInvoiceEntity,
    PaymentMethodEntity,
    TransactionEntity,
)
from dotmac.platform.billing.core.enums import (
    PaymentMethodStatus,
    PaymentMethodType,
    PaymentStatus,
    TransactionType,
)
from dotmac.platform.billing.core.exceptions import (
    PaymentError,
    PaymentMethodNotFoundError,
    PaymentNotFoundError,
)
from dotmac.platform.billing.core.models import Payment, PaymentMethod
from dotmac.platform.billing.payments.providers import PaymentProvider
from dotmac.platform.webhooks.events import get_event_bus
from dotmac.platform.webhooks.models import WebhookEvent

logger = logging.getLogger(__name__)


class PaymentService:
    """Payment processing service with tenant isolation"""

    def __init__(
        self,
        db_session: AsyncSession,
        payment_providers: dict[str, PaymentProvider] | None = None,
    ):
        self.db = db_session
        self.providers = payment_providers or {}

    async def create_payment(
        self,
        tenant_id: str,
        amount: int,
        currency: str,
        customer_id: str,
        payment_method_id: str,
        provider: str = "stripe",
        idempotency_key: str | None = None,
        invoice_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Payment:
        """Create and process a payment with idempotency"""

        # Check for existing payment with same idempotency key
        if idempotency_key:
            existing = await self._get_payment_by_idempotency_key(tenant_id, idempotency_key)
            if existing:
                return Payment.model_validate(existing)

        # Get payment method
        payment_method = await self._get_payment_method(tenant_id, payment_method_id)
        if not payment_method:
            raise PaymentMethodNotFoundError(f"Payment method {payment_method_id} not found")

        if payment_method.status != PaymentMethodStatus.ACTIVE:
            raise PaymentError(f"Payment method {payment_method_id} is not active")

        # Create payment record
        payment_entity = PaymentEntity(
            tenant_id=tenant_id,
            amount=amount,
            currency=currency,
            customer_id=customer_id,
            idempotency_key=idempotency_key,
            provider=provider,
            status=PaymentStatus.PENDING,
            payment_method_type=payment_method.type,
            payment_method_details={
                "payment_method_id": payment_method_id,
                "last_four": payment_method.last_four,
                "brand": payment_method.brand,
            },
            extra_data=metadata or {},
        )

        # Save to database first
        self.db.add(payment_entity)
        await self.db.commit()

        try:
            # Process with payment provider
            if provider in self.providers:
                provider_instance = self.providers[provider]
                result = await provider_instance.charge_payment_method(
                    amount=amount,
                    currency=currency,
                    payment_method_id=payment_method.provider_payment_method_id,
                    metadata={"payment_id": payment_entity.payment_id},
                )

                # Update payment with provider response
                payment_entity.provider_payment_id = result.provider_payment_id
                payment_entity.provider_fee = result.provider_fee
                payment_entity.status = PaymentStatus.SUCCEEDED if result.success else PaymentStatus.FAILED
                payment_entity.failure_reason = result.error_message if not result.success else None
                payment_entity.processed_at = datetime.now(timezone.utc)
            else:
                # Mock success for testing
                payment_entity.status = PaymentStatus.SUCCEEDED
                payment_entity.processed_at = datetime.now(timezone.utc)
                logger.warning(f"Payment provider {provider} not configured, mocking success")

        except Exception as e:
            payment_entity.status = PaymentStatus.FAILED
            payment_entity.failure_reason = str(e)
            payment_entity.processed_at = datetime.now(timezone.utc)
            logger.error(f"Payment processing error: {e}")

        # Update payment record
        await self.db.commit()
        await self.db.refresh(payment_entity)

        # Create transaction record
        if payment_entity.status == PaymentStatus.SUCCEEDED:
            await self._create_transaction(payment_entity, TransactionType.PAYMENT)

            # Link to invoices if provided
            if invoice_ids:
                await self._link_payment_to_invoices(payment_entity, invoice_ids)

            # Publish webhook event for successful payment
            try:
                await get_event_bus().publish(
                    event_type=WebhookEvent.PAYMENT_SUCCEEDED.value,
                    event_data={
                        "payment_id": payment_entity.payment_id,
                        "customer_id": customer_id,
                        "amount": float(amount / 100),  # Convert to decimal
                        "currency": currency,
                        "payment_method_id": payment_method_id,
                        "provider": provider,
                        "provider_payment_id": payment_entity.provider_payment_id,
                        "invoice_ids": invoice_ids,
                        "processed_at": payment_entity.processed_at.isoformat() if payment_entity.processed_at else None,
                    },
                    tenant_id=tenant_id,
                    db=self.db,
                )
            except Exception as e:
                logger.warning(f"Failed to publish payment.succeeded event: {e}")
        elif payment_entity.status == PaymentStatus.FAILED:
            # Publish webhook event for failed payment
            try:
                await get_event_bus().publish(
                    event_type=WebhookEvent.PAYMENT_FAILED.value,
                    event_data={
                        "payment_id": payment_entity.payment_id,
                        "customer_id": customer_id,
                        "amount": float(amount / 100),
                        "currency": currency,
                        "payment_method_id": payment_method_id,
                        "provider": provider,
                        "failure_reason": payment_entity.failure_reason,
                        "processed_at": payment_entity.processed_at.isoformat() if payment_entity.processed_at else None,
                    },
                    tenant_id=tenant_id,
                    db=self.db,
                )
            except Exception as e:
                logger.warning(f"Failed to publish payment.failed event: {e}")

        return Payment.model_validate(payment_entity)

    async def refund_payment(
        self,
        tenant_id: str,
        payment_id: str,
        amount: int | None = None,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> Payment:
        """Refund a payment with idempotency"""

        original_payment = await self._get_payment_entity(tenant_id, payment_id)
        if not original_payment:
            raise PaymentNotFoundError(f"Payment {payment_id} not found")

        if original_payment.status != PaymentStatus.SUCCEEDED:
            raise PaymentError("Can only refund successful payments")

        refund_amount = amount or original_payment.amount

        if refund_amount > original_payment.amount:
            raise PaymentError("Refund amount cannot exceed original payment amount")

        # Check idempotency
        if idempotency_key:
            existing_refund = await self._get_payment_by_idempotency_key(tenant_id, idempotency_key)
            if existing_refund:
                return Payment.model_validate(existing_refund)

        # Create refund payment record
        refund = PaymentEntity(
            tenant_id=tenant_id,
            amount=-refund_amount,  # Negative amount for refund
            currency=original_payment.currency,
            customer_id=original_payment.customer_id,
            idempotency_key=idempotency_key,
            provider=original_payment.provider,
            status=PaymentStatus.PENDING,
            payment_method_type=original_payment.payment_method_type,
            payment_method_details=original_payment.payment_method_details,
            extra_data={
                "refund_reason": reason,
                "original_payment_id": payment_id,
            },
        )

        self.db.add(refund)
        await self.db.commit()

        try:
            # Process refund with provider
            if original_payment.provider in self.providers:
                provider_instance = self.providers[original_payment.provider]
                result = await provider_instance.refund_payment(
                    original_payment.provider_payment_id,
                    refund_amount,
                    reason,
                )

                refund.provider_payment_id = result.provider_refund_id
                refund.status = PaymentStatus.REFUNDED if result.success else PaymentStatus.FAILED
                refund.failure_reason = result.error_message if not result.success else None
            else:
                # Mock success for testing
                refund.status = PaymentStatus.REFUNDED
                logger.warning(f"Payment provider {original_payment.provider} not configured, mocking refund")

            refund.processed_at = datetime.now(timezone.utc)

        except Exception as e:
            refund.status = PaymentStatus.FAILED
            refund.failure_reason = str(e)
            refund.processed_at = datetime.now(timezone.utc)
            logger.error(f"Refund processing error: {e}")

        await self.db.commit()
        await self.db.refresh(refund)

        if refund.status == PaymentStatus.REFUNDED:
            await self._create_transaction(refund, TransactionType.REFUND)

            # Update original payment status
            if refund_amount == original_payment.amount:
                original_payment.status = PaymentStatus.REFUNDED
            else:
                original_payment.status = PaymentStatus.PARTIALLY_REFUNDED
            await self.db.commit()

            # Publish webhook event for successful refund
            try:
                await get_event_bus().publish(
                    event_type=WebhookEvent.PAYMENT_REFUNDED.value,
                    event_data={
                        "refund_id": refund.payment_id,
                        "original_payment_id": payment_id,
                        "customer_id": original_payment.customer_id,
                        "amount": float(abs(refund_amount) / 100),  # Convert to decimal
                        "currency": original_payment.currency,
                        "reason": reason,
                        "provider": original_payment.provider,
                        "provider_refund_id": refund.provider_payment_id,
                        "processed_at": refund.processed_at.isoformat() if refund.processed_at else None,
                        "refund_type": "full" if refund_amount == original_payment.amount else "partial",
                    },
                    tenant_id=tenant_id,
                    db=self.db,
                )
            except Exception as e:
                logger.warning(f"Failed to publish payment.refunded event: {e}")

        return Payment.model_validate(refund)

    async def add_payment_method(
        self,
        tenant_id: str,
        customer_id: str,
        payment_method_type: PaymentMethodType,
        provider: str,
        provider_payment_method_id: str,
        display_name: str,
        last_four: str | None = None,
        brand: str | None = None,
        expiry_month: int | None = None,
        expiry_year: int | None = None,
        bank_name: str | None = None,
        account_type: str | None = None,
        set_as_default: bool = False,
    ) -> PaymentMethod:
        """Add a new payment method for customer"""

        # Create payment method entity
        payment_method = PaymentMethodEntity(
            tenant_id=tenant_id,
            customer_id=customer_id,
            type=payment_method_type,
            status=PaymentMethodStatus.ACTIVE,
            provider=provider,
            provider_payment_method_id=provider_payment_method_id,
            display_name=display_name,
            last_four=last_four,
            brand=brand,
            expiry_month=expiry_month,
            expiry_year=expiry_year,
            bank_name=bank_name,
            is_default=False,
            auto_pay_enabled=False,
            verified_at=datetime.now(timezone.utc) if payment_method_type == PaymentMethodType.CARD else None,
        )

        # Set as default if requested or if it's the first payment method
        if set_as_default:
            await self._clear_default_payment_methods(tenant_id, customer_id)
            payment_method.is_default = True
        else:
            existing_count = await self._count_payment_methods(tenant_id, customer_id)
            if existing_count == 0:
                payment_method.is_default = True

        self.db.add(payment_method)
        await self.db.commit()
        await self.db.refresh(payment_method)

        return PaymentMethod.model_validate(payment_method)

    async def get_payment_method(
        self, tenant_id: str, payment_method_id: str
    ) -> PaymentMethod | None:
        """Get payment method by ID"""

        payment_method = await self._get_payment_method(tenant_id, payment_method_id)
        if payment_method:
            return PaymentMethod.model_validate(payment_method)
        return None

    async def list_payment_methods(
        self, tenant_id: str, customer_id: str, include_inactive: bool = False
    ) -> list[PaymentMethod]:
        """List customer payment methods"""

        query = select(PaymentMethodEntity).where(
            and_(
                PaymentMethodEntity.tenant_id == tenant_id,
                PaymentMethodEntity.customer_id == customer_id,
            )
        )

        if not include_inactive:
            query = query.where(
                PaymentMethodEntity.status.in_(
                    [PaymentMethodStatus.ACTIVE, PaymentMethodStatus.REQUIRES_VERIFICATION]
                )
            )

        query = query.order_by(PaymentMethodEntity.is_default.desc(), PaymentMethodEntity.created_at.desc())

        result = await self.db.execute(query)
        payment_methods = result.scalars().all()

        return [PaymentMethod.model_validate(pm) for pm in payment_methods]

    async def set_default_payment_method(
        self, tenant_id: str, customer_id: str, payment_method_id: str
    ) -> PaymentMethod:
        """Set payment method as default for customer"""

        payment_method = await self._get_payment_method(tenant_id, payment_method_id)
        if not payment_method:
            raise PaymentMethodNotFoundError(f"Payment method {payment_method_id} not found")

        if payment_method.customer_id != customer_id:
            raise PaymentError("Payment method does not belong to customer")

        # Clear other defaults
        await self._clear_default_payment_methods(tenant_id, customer_id)

        # Set new default
        payment_method.is_default = True
        await self.db.commit()
        await self.db.refresh(payment_method)

        return PaymentMethod.model_validate(payment_method)

    async def delete_payment_method(
        self, tenant_id: str, payment_method_id: str
    ) -> bool:
        """Soft delete a payment method"""

        payment_method = await self._get_payment_method(tenant_id, payment_method_id)
        if not payment_method:
            raise PaymentMethodNotFoundError(f"Payment method {payment_method_id} not found")

        # Soft delete
        payment_method.is_active = False
        payment_method.deleted_at = datetime.now(timezone.utc)
        payment_method.status = PaymentMethodStatus.INACTIVE

        await self.db.commit()
        return True

    async def retry_failed_payment(
        self, tenant_id: str, payment_id: str
    ) -> Payment:
        """Retry a failed payment"""

        payment = await self._get_payment_entity(tenant_id, payment_id)
        if not payment:
            raise PaymentNotFoundError(f"Payment {payment_id} not found")

        if payment.status != PaymentStatus.FAILED:
            raise PaymentError("Can only retry failed payments")

        # Check retry limit
        if payment.retry_count >= 3:
            raise PaymentError("Maximum retry attempts reached")

        # Update retry count and schedule
        payment.retry_count += 1
        payment.next_retry_at = datetime.now(timezone.utc) + timedelta(hours=2 ** payment.retry_count)
        payment.status = PaymentStatus.PROCESSING

        await self.db.commit()

        # Attempt payment again
        try:
            if payment.provider in self.providers:
                # Get payment method details
                payment_method_id = payment.payment_method_details.get("payment_method_id")
                payment_method = await self._get_payment_method(tenant_id, payment_method_id)

                if payment_method:
                    provider_instance = self.providers[payment.provider]
                    result = await provider_instance.charge_payment_method(
                        amount=payment.amount,
                        currency=payment.currency,
                        payment_method_id=payment_method.provider_payment_method_id,
                        metadata={"payment_id": payment.payment_id, "retry_attempt": payment.retry_count},
                    )

                    payment.status = PaymentStatus.SUCCEEDED if result.success else PaymentStatus.FAILED
                    payment.failure_reason = result.error_message if not result.success else None
                    payment.processed_at = datetime.now(timezone.utc)

                    if result.success:
                        payment.provider_payment_id = result.provider_payment_id
                        payment.provider_fee = result.provider_fee
                        await self._create_transaction(payment, TransactionType.PAYMENT)
            else:
                # Mock retry
                payment.status = PaymentStatus.SUCCEEDED
                payment.processed_at = datetime.now(timezone.utc)

        except Exception as e:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = str(e)
            logger.error(f"Payment retry error: {e}")

        await self.db.commit()
        await self.db.refresh(payment)

        return Payment.model_validate(payment)

    # ============================================================================
    # Private helper methods
    # ============================================================================

    async def _get_payment_entity(
        self, tenant_id: str, payment_id: str
    ) -> PaymentEntity | None:
        """Get payment entity by ID with tenant isolation"""

        query = select(PaymentEntity).where(
            and_(
                PaymentEntity.tenant_id == tenant_id,
                PaymentEntity.payment_id == payment_id,
            )
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_payment_by_idempotency_key(
        self, tenant_id: str, idempotency_key: str
    ) -> PaymentEntity | None:
        """Get payment by idempotency key"""

        query = select(PaymentEntity).where(
            and_(
                PaymentEntity.tenant_id == tenant_id,
                PaymentEntity.idempotency_key == idempotency_key,
            )
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_payment_method(
        self, tenant_id: str, payment_method_id: str
    ) -> PaymentMethodEntity | None:
        """Get payment method by ID"""

        query = select(PaymentMethodEntity).where(
            and_(
                PaymentMethodEntity.tenant_id == tenant_id,
                PaymentMethodEntity.payment_method_id == payment_method_id,
                PaymentMethodEntity.is_active == True,
            )
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _count_payment_methods(
        self, tenant_id: str, customer_id: str
    ) -> int:
        """Count active payment methods for customer"""

        query = select(PaymentMethodEntity).where(
            and_(
                PaymentMethodEntity.tenant_id == tenant_id,
                PaymentMethodEntity.customer_id == customer_id,
                PaymentMethodEntity.is_active == True,
            )
        )

        result = await self.db.execute(query)
        return len(result.scalars().all())

    async def _clear_default_payment_methods(
        self, tenant_id: str, customer_id: str
    ) -> None:
        """Clear default flag from all customer payment methods"""

        query = select(PaymentMethodEntity).where(
            and_(
                PaymentMethodEntity.tenant_id == tenant_id,
                PaymentMethodEntity.customer_id == customer_id,
                PaymentMethodEntity.is_default == True,
            )
        )

        result = await self.db.execute(query)
        payment_methods = result.scalars().all()

        for pm in payment_methods:
            pm.is_default = False

        await self.db.commit()

    async def _create_transaction(
        self, payment: PaymentEntity, transaction_type: TransactionType
    ) -> None:
        """Create transaction record for payment"""

        transaction = TransactionEntity(
            tenant_id=payment.tenant_id,
            amount=abs(payment.amount),
            currency=payment.currency,
            transaction_type=transaction_type,
            description=f"{transaction_type.value.title()} - {payment.payment_id}",
            customer_id=payment.customer_id,
            payment_id=payment.payment_id,
            extra_data={"provider": payment.provider},
        )

        self.db.add(transaction)
        await self.db.commit()

    async def _link_payment_to_invoices(
        self, payment: PaymentEntity, invoice_ids: list[str]
    ) -> None:
        """Link payment to invoices"""

        amount_per_invoice = payment.amount // len(invoice_ids)

        for invoice_id in invoice_ids:
            link = PaymentInvoiceEntity(
                payment_id=payment.payment_id,
                invoice_id=invoice_id,
                amount_applied=amount_per_invoice,
            )
            self.db.add(link)

        await self.db.commit()