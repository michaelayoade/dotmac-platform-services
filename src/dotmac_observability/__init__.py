"""Compatibility shim for observability imports used in tests.

Exposes a minimal API that mirrors expected names and falls back gracefully
when optional submodules are not available.
"""

MIDDLEWARE_AVAILABLE = False
OTEL_AVAILABLE = False

# Defaults for middleware symbols
create_audit_middleware = None
timing_middleware = None

# Default for otel bridge
enable_otel_bridge = None

try:
    # Try to import middleware from the platform package
    from dotmac.platform.observability import middleware as _mw  # type: ignore

    create_audit_middleware = getattr(_mw, "create_audit_middleware", None)
    timing_middleware = getattr(_mw, "timing_middleware", None)
    MIDDLEWARE_AVAILABLE = create_audit_middleware is not None or timing_middleware is not None
except Exception:
    MIDDLEWARE_AVAILABLE = False

try:
    # If an OTEL bridge exists under platform observability, expose a toggle
    from dotmac.platform.observability import tracing as _otel  # type: ignore

    enable_otel_bridge = getattr(_otel, "enable_otel_bridge", None)
    OTEL_AVAILABLE = enable_otel_bridge is not None
except Exception:
    OTEL_AVAILABLE = False

