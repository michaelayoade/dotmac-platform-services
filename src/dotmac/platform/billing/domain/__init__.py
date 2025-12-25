"""
Billing Domain Layer - Domain-Driven Design Components.

This module contains domain aggregates, value objects, and business logic
for the billing bounded context, following DDD principles.
"""

from .aggregates import (
    Invoice,
    Payment,
    Subscription,
)
from .event_handlers import (
    register_billing_domain_event_handlers,
)
from .mappers import (
    InvoiceMapper,
    PaymentMapper,
    SubscriptionMapper,
)
from .repositories import (
    InvoiceRepository,
    PaymentRepository,
    SQLAlchemyInvoiceRepository,
    SQLAlchemyPaymentRepository,
)

__all__ = [
    # Aggregates
    "Invoice",
    "Payment",
    "Subscription",
    # Mappers
    "InvoiceMapper",
    "PaymentMapper",
    "SubscriptionMapper",
    # Event Handlers
    "register_billing_domain_event_handlers",
    # Repositories
    "SQLAlchemyInvoiceRepository",
    "SQLAlchemyPaymentRepository",
    "InvoiceRepository",
    "PaymentRepository",
]
