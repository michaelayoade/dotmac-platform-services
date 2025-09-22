"""
Simple structured logging setup using structlog directly.

No wrappers, just standard structlog configuration.
"""

import structlog
from dotmac.platform.settings import settings


def setup_logging() -> None:
    """
    Setup structured logging with structlog.

    Uses settings from centralized configuration.
    """
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add correlation ID if enabled
    if settings.observability.enable_correlation_ids:
        processors.insert(0, structlog.processors.CallsiteParameterAdder(
            parameters=[structlog.processors.CallsiteParameter.THREAD_NAME]
        ))

    # Use JSON or console output based on settings
    if settings.observability.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """
    Get a structured logger.

    Args:
        name: Logger name, defaults to caller's module name

    Returns:
        Configured structured logger
    """
    return structlog.get_logger(name)


def get_audit_logger() -> structlog.BoundLogger:
    """
    Get a logger specifically for audit events.

    Audit events are just structured logs with specific metadata.
    """
    return structlog.get_logger("audit")


def log_audit_event(
    action: str,
    category: str,
    user_id: str | None = None,
    tenant_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    **kwargs
) -> None:
    """
    Log an audit event as a structured log entry.

    This replaces the entire audit_trail module - audit events
    are just structured logs with specific fields.
    """
    audit_logger = get_audit_logger()

    audit_logger.info(
        action,
        audit_category=category,
        audit_user_id=user_id,
        audit_tenant_id=tenant_id,
        audit_resource_type=resource_type,
        audit_resource_id=resource_id,
        audit_ip_address=ip_address,
        **kwargs
    )


# Initialize on import
setup_logging()

# Convenience export for direct use
logger = get_logger(__name__)