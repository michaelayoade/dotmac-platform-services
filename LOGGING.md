# Logging Best Practices for DotMac Platform Services

## Quick Start

All modules should use the unified logging system:

```python
from dotmac.platform.observability.unified_logging import get_logger, set_context

logger = get_logger(__name__)

# Basic logging
logger.info("Service started", port=8000, environment="production")
logger.error("Database connection failed", error=str(e), exc_info=True)

# Set request context
set_context(
    correlation_id="abc-123",
    tenant_id="tenant-001",
    user_id="user-456"
)
```

## Logging Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for potentially harmful situations
- **ERROR**: Error events that might still allow the application to continue
- **CRITICAL**: Critical problems that require immediate attention

## Structured Logging

Always use structured logging with key-value pairs:

```python
# ✅ Good - Structured
logger.info("user_login", user_id=user_id, ip_address=ip, success=True)

# ❌ Bad - Unstructured
logger.info(f"User {user_id} logged in from {ip}")
```

## Common Patterns

### 1. Service Initialization

```python
logger = get_logger(__name__)

class MyService:
    def __init__(self):
        logger.info("service_initialized",
                   service="MyService",
                   config=self.config.dict())
```

### 2. API Request Handling

```python
from dotmac.platform.observability.unified_logging import log_performance

@log_performance
async def handle_request(request: Request):
    logger.info("request_received",
               method=request.method,
               path=request.url.path,
               client_ip=request.client.host)
    # ... handle request ...
```

### 3. Error Handling

```python
try:
    result = await process_data(data)
except ValidationError as e:
    logger.warning("validation_failed",
                  error=str(e),
                  data_sample=data[:100])
    raise
except Exception as e:
    logger.error("unexpected_error",
                error=str(e),
                exc_info=True,
                context={"data_size": len(data)})
    raise
```

### 4. Audit Logging

```python
from dotmac.platform.observability.unified_logging import audit_log

# Log security-relevant events
audit_log(
    action="secret.access",
    resource=f"vault/{secret_path}",
    outcome="success",
    details={"ip": request.client.host}
)
```

### 5. Performance Tracking

```python
from dotmac.platform.observability.unified_logging import log_performance

@log_performance
async def expensive_operation(data):
    # Function execution time will be automatically logged
    return await process_data(data)
```

## Integration with OpenTelemetry

The unified logging system automatically correlates logs with traces:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("process_order") as span:
    # Logs within this span will automatically include trace_id and span_id
    logger.info("processing_order", order_id=order_id)
```

## Environment-Specific Configuration

### Development
- Console output with colors
- DEBUG level logging
- All logs included

### Production
- JSON formatted output
- INFO level and above
- OpenTelemetry export enabled
- Rate limiting and sampling applied

## DO's and DON'Ts

### DO's
- ✅ Use structured logging with key-value pairs
- ✅ Include relevant context (user_id, tenant_id, correlation_id)
- ✅ Use appropriate log levels
- ✅ Log at boundaries (API entry/exit, service calls)
- ✅ Include error details with exc_info=True for exceptions
- ✅ Use audit_log for security-relevant events

### DON'Ts
- ❌ Don't log sensitive information (passwords, tokens, PII)
- ❌ Don't use f-strings or % formatting for log messages
- ❌ Don't log excessively in loops
- ❌ Don't use print() statements
- ❌ Don't create new logger instances repeatedly

## Migration from Old Logging

Replace old logging patterns:

```python
# Old pattern
import logging
logger = logging.getLogger(__name__)
logger.info(f"Processing {item_id}")

# New pattern
from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)
logger.info("processing_item", item_id=item_id)
```

## Testing with Logs

In tests, you can capture and assert on logs:

```python
import structlog
from structlog.testing import capture_logs

def test_my_function():
    with capture_logs() as cap_logs:
        my_function()

    assert cap_logs[0]["event"] == "expected_event"
    assert cap_logs[0]["level"] == "info"
```

## Performance Considerations

1. **Rate Limiting**: The logging system includes automatic rate limiting to prevent log flooding
2. **Sampling**: In production, not all debug/trace logs are exported
3. **Async Export**: Logs are exported asynchronously to avoid blocking
4. **Aggregation**: Similar log entries are automatically aggregated

## Troubleshooting

### Logs not appearing in OpenTelemetry Collector?

1. Check OTEL_EXPORTER_OTLP_ENDPOINT environment variable
2. Verify the collector is running: `docker ps | grep otel`
3. Check log level configuration

### Too many logs?

1. Adjust log level: `LOG_LEVEL=WARNING`
2. Enable sampling in production
3. Use rate limiting configuration

### Missing correlation IDs?

Ensure context is set at request boundaries:
```python
from dotmac.platform.observability.unified_logging import set_context

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
    set_context(correlation_id=correlation_id)
    response = await call_next(request)
    clear_context()
    return response
```