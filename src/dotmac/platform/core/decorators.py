"""Common decorators exposed at the core package level.

These decorators are re-exported from the communications notifications module so
that higher-level services can depend on a stable import path without reaching
into feature-specific internals.
"""

from dotmac.platform.communications.notifications.internal.decorators import (
    rate_limit,
    retry_on_failure,
    standard_exception_handler,
)

__all__ = ["rate_limit", "retry_on_failure", "standard_exception_handler"]
