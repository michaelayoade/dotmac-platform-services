"""
Central task registration module for Celery.

This module imports all task definitions to ensure they are registered
with the main Celery application instance.
"""

# Import communication tasks to register them
from dotmac.platform.communications.task_service import (  # noqa: F401
    send_bulk_email_task,
    send_single_email_task,
)

__all__ = [
    "send_bulk_email_task",
    "send_single_email_task",
]
