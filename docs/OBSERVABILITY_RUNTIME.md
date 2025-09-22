# Observability Runtime Guide

This document describes the streamlined observability stack after refactoring.

## Configuration

- `dotmac.platform.observability.config.ObservabilityConfig` is the canonical runtime configuration.
- Domain-specific configs wrap or extend it:
  - `PlatformObservabilitySettings`
  - `APIGatewayObservabilityConfig`
  - `WebSocketObservabilityConfig`

Use `create_default_config()` to produce a properly normalized `ObservabilityConfig`.

## Building the Runtime

```python
from dotmac.platform.observability.config import create_default_config
from dotmac.platform.observability.runtime import build_runtime

cfg = create_default_config(service_name="my-service", environment="production")
runtime = build_runtime(cfg)
```

`ObservabilityRuntime` holds:
- `logger`: structured logger with OTEL integration
- `otel`: optional `OTelBootstrap`
- `metrics_registry` / `tenant_metrics`
- `tracing_manager`

Call `runtime.shutdown()` during teardown.

## FastAPI Middleware

Middleware classes accept an optional `ObservabilityRuntime`; when supplied they reuse its logger, registry, and tracing manager.

Example (manual wiring):

```python
runtime = build_runtime(cfg)
app.add_middleware(LoggingMiddleware, runtime=runtime, config=runtime.config)
app.add_middleware(TracingMiddleware, runtime=runtime, config=runtime.config)
app.add_middleware(MetricsMiddleware, runtime=runtime)
```

```

## Legacy Helpers

Compatibility wrappers (e.g. `StructuredLogger`, `LogContext`) live in `observability/unified_logging` but are backed by the unified logging pipeline. Prefer the modern functions (`get_logger`, `set_context`, `log_performance`).

## Tests

- `tests/observability/test_runtime_smoke.py` verifies the runtime builder.
- Core config/logging tests ensure compatibility with legacy helpers.

## Module-Level Helpers

```python
from dotmac.platform import observability

# Initialize once (defaults to service_name="dotmac-service")
observability.initialize({"service_name": "svc"})

logger = observability.get_logger(__name__)
metrics = observability.get_metrics_registry()

# When shutting down the process
observability.shutdown()
```

## Initialization Patterns

Most components should call `observability.initialize()` once during application startup and use the module helpers (`get_logger`, `get_metrics_registry`, etc.) thereafter. Avoid importing `initialize_otel` or `initialize_metrics_registry` directly; the runtime takes care of them.
