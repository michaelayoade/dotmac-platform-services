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

# Core platform models
import dotmac.platform.analytics.models  # noqa: F401
import dotmac.platform.communications.models  # noqa: F401
import dotmac.platform.deployment.models  # noqa: F401
import dotmac.platform.webhooks.models  # noqa: F401
import dotmac.platform.workflows.models  # noqa: F401

# Audit and analytics
from dotmac.platform.audit.models import AuditActivity  # noqa: F401

# Auth models
from dotmac.platform.auth.models import (  # noqa: F401
    Permission,
    Role,
)

# Billing models
from dotmac.platform.billing.core.models import (  # noqa: F401
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
from dotmac.platform.contacts.models import Contact  # noqa: F401

# Customer and user management
from dotmac.platform.customer_management.models import Customer  # noqa: F401

# Jobs
from dotmac.platform.jobs.models import Job, JobChain  # noqa: F401

# Notifications
from dotmac.platform.notifications.models import Notification  # noqa: F401

from dotmac.platform.tenant.models import Tenant, TenantInvitation  # noqa: F401

# Ticketing
from dotmac.platform.ticketing.models import Ticket, TicketMessage  # noqa: F401
from dotmac.platform.user_management.models import User  # noqa: F401

# Import additional billing sub-models
try:
    import dotmac.platform.billing.subscriptions.models  # noqa: F401
except ImportError:
    pass

try:
    import dotmac.platform.billing.catalog.models  # noqa: F401
except ImportError:
    pass

try:
    import dotmac.platform.billing.pricing.models  # noqa: F401
except ImportError:
    pass

try:
    import dotmac.platform.billing.dunning.models  # noqa: F401
except ImportError:
    pass

try:
    import dotmac.platform.billing.bank_accounts.models  # noqa: F401
except ImportError:
    pass

# All models are now registered with SQLAlchemy Base
__all__ = [
    "Tenant",
    "Customer",
    "User",
    "Invoice",
    "Payment",
]
