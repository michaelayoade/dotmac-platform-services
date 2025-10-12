"""
Central task registration module for Celery.

This module imports all task definitions to ensure they are registered
with the main Celery application instance.
"""

from typing import Any

from dotmac.platform.billing.currency.service import sync_refresh_currency_rates
from dotmac.platform.celery_app import celery_app
from dotmac.platform.communications.task_service import (  # noqa: F401
    send_bulk_email_task,
    send_single_email_task,
)
from dotmac.platform.settings import settings


@celery_app.task(name="currency.refresh_rates")
def refresh_currency_rates_task() -> dict[str, Any]:
    """Periodic task to refresh configured currency exchange rates."""
    if not settings.billing.enable_multi_currency:
        return {"status": "disabled"}

    base_currency = settings.billing.default_currency.upper()
    targets = [
        currency.upper()
        for currency in settings.billing.supported_currencies
        if currency.upper() != base_currency
    ]

    if not targets:
        return {"status": "no_targets"}

    result = sync_refresh_currency_rates(base_currency=base_currency, target_currencies=targets)
    result["status"] = "ok"
    return result


__all__ = [
    "refresh_currency_rates_task",
    "send_bulk_email_task",
    "send_single_email_task",
]
