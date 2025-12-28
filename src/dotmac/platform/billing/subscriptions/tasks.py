"""
Background tasks for subscription management.

This module contains Celery tasks for:
- Processing scheduled plan changes
- Subscription renewal reminders
- Trial expiration notifications
- Subscription status updates
- Grace period enforcement
"""

import structlog

from dotmac.platform.celery_app import app
from dotmac.platform.database import get_async_session_context

from .service import SubscriptionService

logger = structlog.get_logger(__name__)


def _run_async(coro):
    """Helper to run async code from sync Celery tasks."""
    import asyncio

    try:
        return asyncio.run(coro)
    except RuntimeError as exc:
        # Fallback for environments that already have a running loop
        if "asyncio.run() cannot be called" not in str(exc):
            raise
        loop = asyncio.new_event_loop()
        policy = asyncio.get_event_loop_policy()
        try:
            previous_loop = policy.get_event_loop()
        except RuntimeError:
            previous_loop = None
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)
        finally:
            asyncio.set_event_loop(previous_loop)
            loop.close()


@app.task(name="subscriptions.process_scheduled_plan_changes")
def process_scheduled_plan_changes_task() -> dict[str, int]:
    """
    Process all scheduled plan changes that are due.

    This task should be scheduled to run periodically (e.g., every hour or every 15 minutes)
    to check for and apply any plan changes that were scheduled for a future date.

    Returns:
        Dictionary with processing statistics:
        - processed: Number of plan changes successfully applied
        - failed: Number of plan changes that failed
        - skipped: Number of changes skipped (invalid state)
    """

    async def _process():
        async with get_async_session_context() as session:
            service = SubscriptionService(session)
            return await service.process_scheduled_plan_changes()

    result = _run_async(_process())

    logger.info(
        "Scheduled plan changes task completed",
        processed=result["processed"],
        failed=result["failed"],
        skipped=result["skipped"],
    )

    return result


@app.task(name="subscriptions.enforce_grace_periods")
def enforce_grace_periods_task() -> dict[str, int]:
    """
    Enforce grace periods for subscriptions with failed payments.

    This task:
    1. Finds all PAST_DUE subscriptions that have exceeded their grace period
    2. Suspends (PAUSED) each subscription
    3. Publishes webhook events for downstream notification

    The grace period is configured via settings.billing.grace_period_days (default: 3 days).

    This task should run hourly to ensure timely enforcement without being too aggressive.

    Returns:
        Dictionary with processing statistics:
        - suspended: Number of subscriptions suspended
        - failed: Number of suspensions that failed
        - total_checked: Total subscriptions checked
    """

    async def _enforce():
        stats = {"suspended": 0, "failed": 0, "total_checked": 0}

        async with get_async_session_context() as session:
            service = SubscriptionService(session)

            # Get all subscriptions past their grace period (across all tenants)
            subscriptions = await service.get_subscriptions_past_grace_period()
            stats["total_checked"] = len(subscriptions)

            for subscription in subscriptions:
                try:
                    await service.suspend_for_nonpayment(
                        subscription_id=subscription.subscription_id,
                        tenant_id=subscription.tenant_id,
                    )
                    stats["suspended"] += 1

                except Exception as e:
                    logger.error(
                        "Failed to suspend subscription for non-payment",
                        subscription_id=subscription.subscription_id,
                        tenant_id=subscription.tenant_id,
                        error=str(e),
                    )
                    stats["failed"] += 1

        return stats

    result = _run_async(_enforce())

    logger.info(
        "Grace period enforcement task completed",
        suspended=result["suspended"],
        failed=result["failed"],
        total_checked=result["total_checked"],
    )

    return result


# Schedule this task to run periodically
# Example: Run every 15 minutes to check for due plan changes
# This can be configured in celerybeat_schedule or via Celery Beat
@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    """Set up periodic task schedules."""
    # Run scheduled plan changes every 15 minutes
    sender.add_periodic_task(
        900.0,  # 15 minutes in seconds
        process_scheduled_plan_changes_task.s(),
        name="process-scheduled-plan-changes-every-15min",
    )

    # Enforce grace periods every hour
    sender.add_periodic_task(
        3600.0,  # 1 hour in seconds
        enforce_grace_periods_task.s(),
        name="enforce-grace-periods-hourly",
    )
