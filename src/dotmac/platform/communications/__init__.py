"""
Clean communications module initialization.

Provides a simple, clean API for the communications system using standard libraries.
This replaces the complex 392-line __init__.py with a much simpler implementation.
"""

from .email_service import (
    EmailMessage,
    EmailResponse,
    EmailService,
    get_email_service,
    send_email,
)

from .template_service import (
    TemplateData,
    RenderedTemplate,
    TemplateService,
    get_template_service,
    create_template,
    render_template,
    quick_render,
)

from .task_service import (
    BulkEmailJob,
    BulkEmailResult,
    TaskService,
    get_task_service,
    queue_email,
    queue_bulk_emails,
)

from .router import router

# Version info
__version__ = "2.0.0-simplified"

# Public API
__all__ = [
    # Email
    "EmailMessage",
    "EmailResponse",
    "EmailService",
    "get_email_service",
    "send_email",

    # Templates
    "TemplateData",
    "RenderedTemplate",
    "TemplateService",
    "get_template_service",
    "create_template",
    "render_template",
    "quick_render",

    # Tasks
    "BulkEmailJob",
    "BulkEmailResult",
    "TaskService",
    "get_task_service",
    "queue_email",
    "queue_bulk_emails",

    # Router
    "router",

    # Version
    "__version__",
]