# mypy: ignore-errors
"""
Central Model Registry

This module imports all SQLAlchemy models to ensure they are registered
with the Base metadata before any queries or entity instantiation occurs.

This solves circular dependency issues where model relationships reference
other models that haven't been imported yet.

Import this module early in your application initialization or in test conftest.py
to ensure all models are registered.
"""

import os


def _is_truthy_env(value: str | None) -> bool:
    return (value or "").lower() in {"1", "true", "yes", "on"}


_SKIP_BILLING_MODELS: bool = _is_truthy_env(
    os.getenv("DOTMAC_SKIP_BILLING_MODELS") or os.getenv("DOTMAC_SKIP_PLATFORM_MODELS")
)

# Core platform models
import dotmac.platform.analytics.models  # noqa: F401,E402
import dotmac.platform.communications.models  # noqa: F401,E402
import dotmac.platform.deployment.models  # noqa: F401,E402
import dotmac.platform.webhooks.models  # noqa: F401,E402
import dotmac.platform.workflows.models  # noqa: F401,E402

# Audit and analytics
from dotmac.platform.audit.models import AuditActivity  # noqa: F401,E402

# Auth models
from dotmac.platform.auth.models import (  # noqa: F401,E402
    Permission,
    Role,
)

# Billing models (guarded for lightweight/unit test runs)
if not _SKIP_BILLING_MODELS:
    from dotmac.platform.billing.core.models import (  # noqa: F401,E402
        CreditApplication,
        CreditNote,
        CreditNoteLineItem,
        CustomerCredit,
        Invoice,
        InvoiceItem,
        InvoiceLineItem,
        Payment,
        PaymentMethod,
        Price,
        Service,
        Subscription,
        Transaction,
    )

    # Import additional billing sub-models
    for _billing_module in (
        "dotmac.platform.billing.subscriptions.models",
        "dotmac.platform.billing.catalog.models",
        "dotmac.platform.billing.pricing.models",
        "dotmac.platform.billing.dunning.models",
        "dotmac.platform.billing.bank_accounts.models",
    ):
        try:
            __import__(_billing_module)
        except ImportError:
            pass

from dotmac.platform.contacts.models import Contact  # noqa: F401,E402

# Customer and user management

# Jobs
from dotmac.platform.jobs.models import Job, JobChain  # noqa: F401,E402

# Notifications
from dotmac.platform.notifications.models import Notification  # noqa: F401,E402

from dotmac.platform.tenant.models import Tenant, TenantInvitation  # noqa: F401,E402

# Ticketing
from dotmac.platform.ticketing.models import Ticket, TicketMessage  # noqa: F401,E402
from dotmac.platform.user_management.models import User  # noqa: F401,E402

# All models are now registered with SQLAlchemy Base
__all__ = [
    "Tenant",
    "User",
    "Invoice",
    "Payment",
]
