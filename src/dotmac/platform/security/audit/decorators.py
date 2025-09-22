"""
Simple audit logging decorator.
For complex use cases, use get_audit_logger() directly.
"""

import functools
from typing import Any, Optional

from dotmac.platform.logging import get_logger
from .logger import get_audit_logger
from .models import AuditEventType, AuditOutcome, AuditSeverity

logger = get_logger(__name__)

def audit_log(event_type: AuditEventType, severity: AuditSeverity = AuditSeverity.MEDIUM):
    """Simple audit logging decorator"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            audit_logger = get_audit_logger()
            if not audit_logger:
                return func(*args, **kwargs)

            outcome = AuditOutcome.SUCCESS
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                outcome = AuditOutcome.FAILURE
                raise
            finally:
                try:
                    # Simple logging - use audit_logger methods directly for complex cases
                    audit_logger.log_security_event(
                        event_type=event_type,
                        message=f"{func.__name__} executed",
                        severity=severity,
                        outcome=outcome,
                    )
                except Exception:
                    pass  # Don't fail function due to logging issues

        return wrapper
    return decorator

# For complex audit logging, use the audit logger directly:
#
# audit_logger = get_audit_logger()
# await audit_logger.log_security_event(
#     event_type=AuditEventType.ACCESS_GRANTED,
#     message="User accessed resource",
#     actor_id="user123",
#     resource_id="resource456"
# )