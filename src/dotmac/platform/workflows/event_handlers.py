"""
Workflow Event Handlers

Event listeners that trigger workflows based on domain events.
"""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from .service import WorkflowService

logger = logging.getLogger(__name__)


class WorkflowEventHandler:
    """
    Handles domain events and triggers appropriate workflows.
    """

    def __init__(self, db_session: AsyncSession, service_registry: Any = None):
        self.db = db_session
        self.workflow_service = WorkflowService(db_session, service_registry=service_registry)

    async def handle_quote_accepted(self, event: Any) -> None:
        """
        Handle quote.accepted event by triggering quote-to-order workflow.

        Event payload expected:
        {
            "quote_id": int,
            "customer_id": int,
            "tenant_id": str,
            "total_amount": float,
            "payment_type": str,  # "prepaid" or "postpaid"
            "payment_method": str,
            "priority": str,  # "high", "medium", "low"
            "deployment_date": str (ISO format),
            "accepted_by": int (user_id)
        }
        """
        logger.info(f"Handling quote.accepted event: {event.event_id}")

        try:
            # Extract event data
            payload = event.payload
            context = {
                "quote_id": payload.get("quote_id"),
                "customer_id": payload.get("customer_id"),
                "tenant_id": payload.get("tenant_id"),
                "total_amount": payload.get("total_amount"),
                "payment_type": payload.get("payment_type", "postpaid"),
                "payment_method": payload.get("payment_method", "invoice"),
                "priority": payload.get("priority", "medium"),
                "deployment_date": payload.get("deployment_date"),
                "accepted_by": payload.get("accepted_by"),
            }

            # Execute the quote-to-order workflow
            execution = await self.workflow_service.execute_workflow(
                workflow_name="quote_accepted_to_order",
                context=context,
                trigger_type="event",
                trigger_source=event.event_type,
                tenant_id=context.get("tenant_id"),
            )

            logger.info(
                f"Quote-to-order workflow started: execution_id={execution.id}, "
                f"quote_id={context['quote_id']}"
            )

        except Exception as e:
            logger.error(f"Failed to handle quote.accepted event: {e}", exc_info=True)
            raise

    async def handle_subscription_expiring(self, event: Any) -> None:
        """
        Handle subscription.expiring event to trigger renewal workflow.

        Event payload expected:
        {
            "subscription_id": int,
            "renewal_term": int,  # months
            "expiry_date": str (ISO format),
            "tenant_id": str
        }
        """
        logger.info(f"Handling subscription.expiring event: {event.event_id}")

        try:
            payload = event.payload
            context = payload.copy()

            logger.info(
                "Subscription expiry received (no default renewal workflow)",
                subscription_id=context.get("subscription_id"),
            )

        except Exception as e:
            logger.error(f"Failed to handle subscription.expiring event: {e}", exc_info=True)
            raise

    async def handle_workflow_completed(self, event: Any) -> None:
        """
        Handle workflow.execution.completed event for logging and notifications.

        This is a meta-handler that processes workflow completion events.
        """
        logger.info(f"Workflow execution completed: {event.payload.get('execution_id')}")
        # Future: Send notifications, update dashboards, trigger dependent workflows

    async def handle_workflow_failed(self, event: Any) -> None:
        """
        Handle workflow.execution.failed event for error handling.

        This is a meta-handler that processes workflow failure events.
        """
        logger.error(
            f"Workflow execution failed: {event.payload.get('execution_id')}, "
            f"error: {event.payload.get('error')}"
        )
        # Future: Send alerts, create support tickets, retry logic


# Event handler registration mapping
EVENT_HANDLER_MAP = {
    "quote.accepted": "handle_quote_accepted",
    "subscription.expiring": "handle_subscription_expiring",
    "workflow.execution.completed": "handle_workflow_completed",
    "workflow.execution.failed": "handle_workflow_failed",
}


async def register_workflow_event_handlers(
    db_session: AsyncSession, event_bus: Any, service_registry: Any = None
) -> None:
    """
    Register all workflow event handlers with the event bus.

    Args:
        db_session: Database session for workflow operations
        event_bus: Event bus instance to register handlers with
        service_registry: Service registry for workflow execution
    """
    handler = WorkflowEventHandler(db_session, service_registry)

    for event_type, method_name in EVENT_HANDLER_MAP.items():
        method = getattr(handler, method_name)
        event_bus.subscribe(event_type, method)
        logger.info(f"Registered workflow handler for event: {event_type}")

    logger.info(f"Registered {len(EVENT_HANDLER_MAP)} workflow event handlers")
