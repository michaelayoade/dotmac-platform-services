"""
Thin adapter for Signoz integration.

Provides a minimal interface used by legacy code paths without imposing a hard dependency.
"""

from __future__ import annotations

from typing import Any


class _SignozAdapter:
    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled

    def record_business_event(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
        # No-op; integrate with platform metrics if needed in future iterations
        return None


def get_signoz() -> _SignozAdapter:
    """Return a best-effort Signoz adapter.

    In environments without Signoz, returns a disabled adapter to avoid import errors.
    """
    return _SignozAdapter(enabled=False)
