"""
Observability middleware for FastAPI and other web frameworks.

Provides:
- Request/response logging
- Distributed tracing integration
- Performance metrics collection
- Error tracking and correlation
- Security event monitoring
- Multi-tenant context propagation
"""

import threading
import time
from collections.abc import Callable
from typing import Any
from uuid import uuid4

try:
    from fastapi import FastAPI, Request, Response
    from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

    _fastapi_available = True
except ImportError:
    _fastapi_available = False
    # Provide minimal fallback
    BaseHTTPMiddleware = object
    Request = Response = RequestResponseEndpoint = None

import contextlib

from .config import ObservabilityConfig
from .logging import LogContext, PerformanceLogger, StructuredLogger
from .metrics.registry import (
    MetricDefinition,
    MetricsRegistry,
    MetricType,
    initialize_metrics_registry,
)
from .tracing import TraceCorrelator, TracingManager


class MetricsCollector:
    """
    Centralized metrics collection for middleware.
    """

    def __init__(self, service_name: str = "api") -> None:
        self.service_name = service_name
        # Initialize a metrics registry (OTLP-backed)
        self.registry: MetricsRegistry = initialize_metrics_registry(service_name)
        # Ensure instruments exist
        self._ensure_metric(
            MetricDefinition(
                name="http_requests_total",
                type=MetricType.COUNTER,
                description="Total HTTP requests",
                labels=["method", "endpoint", "status_code", "tenant_id"],
            )
        )
        self._ensure_metric(
            MetricDefinition(
                name="http_request_duration_seconds",
                type=MetricType.HISTOGRAM,
                description="HTTP request duration",
                labels=["method", "endpoint", "tenant_id"],
                buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
                unit="s",
            )
        )
        self._ensure_metric(
            MetricDefinition(
                name="http_requests_active",
                type=MetricType.GAUGE,
                description="Active HTTP requests",
                labels=["method", "endpoint", "tenant_id"],
            )
        )
        self._ensure_metric(
            MetricDefinition(
                name="http_request_size_bytes",
                type=MetricType.HISTOGRAM,
                description="HTTP request size in bytes",
                labels=["method", "endpoint", "tenant_id"],
                unit="byte",
            )
        )
        self._ensure_metric(
            MetricDefinition(
                name="http_response_size_bytes",
                type=MetricType.HISTOGRAM,
                description="HTTP response size in bytes",
                labels=["method", "endpoint", "status_code", "tenant_id"],
                unit="byte",
            )
        )
        self._ensure_metric(
            MetricDefinition(
                name="http_errors_total",
                type=MetricType.COUNTER,
                description="Total HTTP errors",
                labels=["method", "endpoint", "error_type", "tenant_id"],
            )
        )
        self._ensure_metric(
            MetricDefinition(
                name="business_operations_total",
                type=MetricType.COUNTER,
                description="Business operation counter",
                labels=["operation", "tenant_id", "status"],
            )
        )
        self._ensure_metric(
            MetricDefinition(
                name="security_events_total",
                type=MetricType.COUNTER,
                description="Security events counter",
                labels=["event_type", "severity", "client_ip"],
            )
        )

    def _ensure_metric(self, definition: MetricDefinition) -> None:
        if self.registry.get_metric(definition.name) is None:
            self.registry.register_metric(definition)

    def record_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float,
        tenant_id: str = "unknown",
    ) -> None:
        """Record HTTP request metrics."""
        labels = {
            "method": method,
            "endpoint": endpoint,
            "status_code": str(status_code),
            "tenant_id": tenant_id,
        }
        self.registry.increment_counter("http_requests_total", 1, labels)
        self.registry.observe_histogram(
            "http_request_duration_seconds",
            duration,
            {"method": method, "endpoint": endpoint, "tenant_id": tenant_id},
        )

    def record_active_request(
        self, method: str, endpoint: str, tenant_id: str = "unknown", delta: int = 1
    ) -> None:
        """Record active request change."""
        # Gauges adjusted by setting current value; here we approximate with inc semantics
        # Consumers can set explicit values via set_gauge if needed
        # For compatibility, we increment/decrement via current value fetch not available; record delta as set
        # Simplified approach: adjust gauge by delta using set operation
        self.registry.set_gauge(
            "http_requests_active",
            delta,
            {"method": method, "endpoint": endpoint, "tenant_id": tenant_id},
        )

    def record_request_size(
        self, method: str, endpoint: str, size: int, tenant_id: str = "unknown"
    ) -> None:
        """Record request size."""
        self.registry.observe_histogram(
            "http_request_size_bytes",
            size,
            {"method": method, "endpoint": endpoint, "tenant_id": tenant_id},
        )

    def record_response_size(
        self, method: str, endpoint: str, status_code: int, size: int, tenant_id: str = "unknown"
    ) -> None:
        """Record response size."""
        self.registry.observe_histogram(
            "http_response_size_bytes",
            size,
            {
                "method": method,
                "endpoint": endpoint,
                "status_code": str(status_code),
                "tenant_id": tenant_id,
            },
        )

    def record_error(
        self, method: str, endpoint: str, error_type: str, tenant_id: str = "unknown"
    ) -> None:
        """Record error metric."""
        self.registry.increment_counter(
            "http_errors_total",
            1,
            {
                "method": method,
                "endpoint": endpoint,
                "error_type": error_type,
                "tenant_id": tenant_id,
            },
        )

    def record_business_operation(
        self, operation: str, status: str, tenant_id: str = "unknown"
    ) -> None:
        """Record business operation metric."""
        self.registry.increment_counter(
            "business_operations_total",
            1,
            {"operation": operation, "tenant_id": tenant_id, "status": status},
        )

    def record_security_event(
        self, event_type: str, severity: str, client_ip: str = "unknown"
    ) -> None:
        """Record security event metric."""
        self.registry.increment_counter(
            "security_events_total",
            1,
            {"event_type": event_type, "severity": severity, "client_ip": client_ip},
        )

    def get_metrics(self) -> str:
        """Get metrics info string (export via OTLP)."""
        return "# Metrics exported via OTLP\n"


class MetricsMiddleware(BaseHTTPMiddleware if _fastapi_available else object):
    """
    Detailed metrics collection middleware.
    """

    def __init__(self, app, service_name: str = "api") -> None:
        if _fastapi_available:
            super().__init__(app)

        self.service_name = service_name
        self.metrics = MetricsCollector(service_name)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Collect detailed metrics for requests."""
        if not _fastapi_available:
            return await call_next(request)

        method = request.method
        endpoint = request.url.path
        tenant_id = request.headers.get("X-Tenant-ID", "unknown")

        # Record request start
        start_time = time.time()
        self.metrics.record_active_request(method, endpoint, tenant_id, 1)

        # Record request size
        content_length = request.headers.get("content-length")
        if content_length:
            with contextlib.suppress(ValueError):
                self.metrics.record_request_size(method, endpoint, int(content_length), tenant_id)

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Record response metrics
            self.metrics.record_request(method, endpoint, response.status_code, duration, tenant_id)

            # Record response size
            response_size = response.headers.get("content-length")
            if response_size:
                with contextlib.suppress(ValueError):
                    self.metrics.record_response_size(
                        method, endpoint, response.status_code, int(response_size), tenant_id
                    )

            # Record errors
            if response.status_code >= 400:
                error_type = "client_error" if response.status_code < 500 else "server_error"
                self.metrics.record_error(method, endpoint, error_type, tenant_id)

            return response

        except Exception as e:
            duration = time.time() - start_time

            # Record error metrics
            self.metrics.record_request(method, endpoint, 500, duration, tenant_id)
            self.metrics.record_error(method, endpoint, type(e).__name__, tenant_id)

            raise

        finally:
            # Record request end
            self.metrics.record_active_request(method, endpoint, tenant_id, -1)


class TracingMiddleware(BaseHTTPMiddleware if _fastapi_available else object):
    """
    Request tracing middleware with correlation.
    """

    def __init__(
        self, app, config: ObservabilityConfig | None = None, service_name: str = "api"
    ) -> None:
        if _fastapi_available:
            super().__init__(app)

        self.config = config or ObservabilityConfig()
        self.service_name = service_name
        self.tracing_manager = TracingManager(config)
        self.trace_correlator = TraceCorrelator()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Add distributed tracing to requests."""
        if not _fastapi_available:
            return await call_next(request)

        # Extract or create trace context
        headers = dict(request.headers)
        trace_context = self.trace_correlator.extract_trace_headers(headers)

        # Create correlation context
        correlation_id = headers.get("x-correlation-id", str(uuid4()))
        tenant_id = headers.get("x-tenant-id")
        user_id = headers.get("x-user-id")

        # Create trace context if not exists
        if not trace_context:
            trace_id = self.trace_correlator.create_trace_context(
                correlation_id=correlation_id, tenant_id=tenant_id, user_id=user_id
            )
            trace_context = {"trace_id": trace_id}

        # Get tracer
        tracer = self.tracing_manager.get_tracer(self.service_name, tenant_id)

        # Start span
        span_attributes = {
            "http.method": request.method,
            "http.url": str(request.url),
            "http.route": request.url.path,
            "http.user_agent": headers.get("user-agent", ""),
            "correlation_id": correlation_id,
        }

        if tenant_id:
            span_attributes["tenant.id"] = tenant_id
        if user_id:
            span_attributes["user.id"] = user_id

        with tracer.trace("http.request", attributes=span_attributes) as span:
            try:
                # Add trace context to request state
                request.state.trace_id = trace_context["trace_id"]
                request.state.span = span
                request.state.tracer = tracer

                # Process request
                response = await call_next(request)

                # Update span with response info
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("response.size", len(getattr(response, "body", b"")))

                # Inject trace headers into response
                trace_headers = self.trace_correlator.inject_trace_headers(span)
                for key, value in trace_headers.items():
                    response.headers[key] = value

                if response.status_code >= 400:
                    span.set_status("error", f"HTTP {response.status_code}")

                return response

            except Exception as e:
                span.record_exception(e)
                span.set_status("error", str(e))
                raise


class LoggingMiddleware(BaseHTTPMiddleware if _fastapi_available else object):
    """
    Request/response logging middleware.
    """

    def __init__(
        self,
        app,
        config: ObservabilityConfig | None = None,
        service_name: str = "api",
        log_request_body: bool = False,
        log_response_body: bool = False,
        max_body_size: int = 1024,
    ) -> None:
        if _fastapi_available:
            super().__init__(app)

        self.config = config or ObservabilityConfig()
        self.service_name = service_name
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_size = max_body_size
        self.logger = StructuredLogger(f"{service_name}.requests", config)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Log request and response details."""
        if not _fastapi_available:
            return await call_next(request)

        # Create log context
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        log_context = LogContext(
            correlation_id=correlation_id,
            tenant_id=request.headers.get("X-Tenant-ID"),
            user_id=request.headers.get("X-User-ID"),
            session_id=request.headers.get("X-Session-ID"),
            request_id=str(uuid4()),
            operation=f"{request.method} {request.url.path}",
        )

        # Get logger with context
        request_logger = self.logger.with_log_context(log_context)

        # Read request body if needed
        request_body = None
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if len(body) <= self.max_body_size:
                    request_body = body.decode("utf-8", errors="ignore")
                else:
                    request_body = f"<body too large: {len(body)} bytes>"
            except Exception:
                request_body = "<unable to read body>"

        # Log request start
        start_time = time.time()
        request_logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            headers=self._sanitize_headers(dict(request.headers)),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            request_body=request_body,
            request_size=len(request_body or ""),
        )

        try:
            # Store logger in request state
            request.state.logger = request_logger
            request.state.log_context = log_context

            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Read response body if needed
            response_body = None
            if self.log_response_body:
                try:
                    body = getattr(response, "body", b"")
                    if body and len(body) <= self.max_body_size:
                        response_body = body.decode("utf-8", errors="ignore")
                    elif body:
                        response_body = f"<body too large: {len(body)} bytes>"
                except Exception:
                    response_body = "<unable to read response body>"

            # Log successful response
            request_logger.info(
                "Request completed",
                status_code=response.status_code,
                duration_ms=duration_ms,
                response_size=len(getattr(response, "body", b"")),
                response_headers=dict(response.headers),
                response_body=response_body,
            )

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            # Log error
            request_logger.error(
                "Request failed",
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=duration_ms,
                traceback=str(e.__traceback__) if hasattr(e, "__traceback__") else None,
            )

            raise

    def _sanitize_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """Remove sensitive headers from logging."""
        sensitive_headers = {
            "authorization",
            "x-api-key",
            "cookie",
            "x-auth-token",
            "x-vault-token",
            "x-secret-key",
            "x-access-token",
        }

        return {
            key: "***REDACTED***" if key.lower() in sensitive_headers else value
            for key, value in headers.items()
        }


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware if _fastapi_available else object):
    """
    Performance monitoring middleware with detailed analysis.
    """

    def __init__(
        self,
        app,
        config: ObservabilityConfig | None = None,
        service_name: str = "api",
        slow_request_threshold: float = 1000.0,  # ms
        memory_monitoring: bool = True,
    ) -> None:
        if _fastapi_available:
            super().__init__(app)

        self.config = config or ObservabilityConfig()
        self.service_name = service_name
        self.slow_request_threshold = slow_request_threshold
        self.memory_monitoring = memory_monitoring

        self.logger = StructuredLogger(f"{service_name}.performance", config)
        self.performance_logger = PerformanceLogger(self.logger)
        self.metrics = MetricsCollector(service_name)

        # Performance tracking state
        self._request_stats: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Monitor request performance."""
        if not _fastapi_available:
            return await call_next(request)

        endpoint_key = f"{request.method} {request.url.path}"
        tenant_id = request.headers.get("X-Tenant-ID", "unknown")

        # Start performance monitoring
        start_time = time.time()
        start_memory = self._get_memory_usage() if self.memory_monitoring else None

        operation_id = self.performance_logger.start_operation(
            operation=endpoint_key,
            context={
                "tenant_id": tenant_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
            },
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate metrics
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            end_memory = self._get_memory_usage() if self.memory_monitoring else None
            memory_delta = (end_memory - start_memory) if (start_memory and end_memory) else None

            # End performance monitoring
            self.performance_logger.end_operation(
                operation_id=operation_id,
                success=response.status_code < 400,
                result_data={
                    "status_code": response.status_code,
                    "response_size": len(getattr(response, "body", b"")),
                    "memory_delta_mb": memory_delta,
                    "slow_request": duration_ms > self.slow_request_threshold,
                },
            )

            # Update endpoint statistics
            self._update_endpoint_stats(endpoint_key, duration_ms, response.status_code, tenant_id)

            # Log slow requests
            if duration_ms > self.slow_request_threshold:
                self.logger.warning(
                    "Slow request detected",
                    endpoint=endpoint_key,
                    duration_ms=duration_ms,
                    threshold_ms=self.slow_request_threshold,
                    status_code=response.status_code,
                    tenant_id=tenant_id,
                    memory_delta_mb=memory_delta,
                    query_params=dict(request.query_params),
                )

            # Record business metrics
            operation_status = "success" if response.status_code < 400 else "error"
            self.metrics.record_business_operation(
                operation=endpoint_key.replace(" ", "_").lower(),
                status=operation_status,
                tenant_id=tenant_id,
            )

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            end_memory = self._get_memory_usage() if self.memory_monitoring else None
            memory_delta = (end_memory - start_memory) if (start_memory and end_memory) else None

            # End performance monitoring with error
            self.performance_logger.end_operation(
                operation_id=operation_id,
                success=False,
                result_data={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "memory_delta_mb": memory_delta,
                },
            )

            # Update endpoint statistics
            self._update_endpoint_stats(endpoint_key, duration_ms, 500, tenant_id)

            # Record business metrics
            self.metrics.record_business_operation(
                operation=endpoint_key.replace(" ", "_").lower(),
                status="error",
                tenant_id=tenant_id,
            )

            raise

    def _get_memory_usage(self) -> float | None:
        """Get current memory usage in MB."""
        try:
            import psutil

            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / 1024 / 1024  # Convert to MB
        except ImportError:
            return None
        except Exception:
            return None

    def _update_endpoint_stats(
        self, endpoint: str, duration_ms: float, status_code: int, tenant_id: str
    ) -> None:
        """Update endpoint performance statistics."""
        with self._lock:
            if endpoint not in self._request_stats:
                self._request_stats[endpoint] = {
                    "total_requests": 0,
                    "total_duration": 0.0,
                    "min_duration": float("inf"),
                    "max_duration": 0.0,
                    "error_count": 0,
                    "slow_request_count": 0,
                    "tenants": set(),
                    "last_updated": time.time(),
                }

            stats = self._request_stats[endpoint]
            stats["total_requests"] += 1
            stats["total_duration"] += duration_ms
            stats["min_duration"] = min(stats["min_duration"], duration_ms)
            stats["max_duration"] = max(stats["max_duration"], duration_ms)
            stats["last_updated"] = time.time()
            stats["tenants"].add(tenant_id)

            if status_code >= 400:
                stats["error_count"] += 1

            if duration_ms > self.slow_request_threshold:
                stats["slow_request_count"] += 1

    def get_performance_stats(self) -> dict[str, Any]:
        """Get current performance statistics."""
        with self._lock:
            stats = {}
            for endpoint, data in self._request_stats.items():
                if data["total_requests"] > 0:
                    avg_duration = data["total_duration"] / data["total_requests"]
                    error_rate = data["error_count"] / data["total_requests"]
                    slow_rate = data["slow_request_count"] / data["total_requests"]

                    stats[endpoint] = {
                        "total_requests": data["total_requests"],
                        "average_duration_ms": avg_duration,
                        "min_duration_ms": data["min_duration"],
                        "max_duration_ms": data["max_duration"],
                        "error_rate": error_rate,
                        "slow_request_rate": slow_rate,
                        "unique_tenants": len(data["tenants"]),
                        "last_updated": data["last_updated"],
                    }

            return stats


class SecurityMiddleware(BaseHTTPMiddleware if _fastapi_available else object):
    """
    Security-focused middleware for threat detection.
    """

    def __init__(
        self, app, config: ObservabilityConfig | None = None, service_name: str = "security"
    ) -> None:
        if _fastapi_available:
            super().__init__(app)

        self.config = config or ObservabilityConfig()
        self.service_name = service_name
        self.logger = StructuredLogger(f"{service_name}.security", config)

        # Threat detection state
        self._failed_attempts: dict[str, dict[str, Any]] = {}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Security monitoring and threat detection."""
        if not _fastapi_available:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")

        # Detect suspicious patterns
        if self._is_suspicious_request(request):
            self.logger.security(
                "Suspicious request detected",
                risk_level="high",
                ip_address=client_ip,
                user_agent=user_agent,
                path=request.url.path,
                method=request.method,
            )

        # Rate limiting check (basic implementation)
        if self._check_rate_limit(client_ip):
            self.logger.security(
                "Rate limit exceeded",
                risk_level="medium",
                ip_address=client_ip,
                path=request.url.path,
            )

        response = await call_next(request)

        # Track failed authentication attempts
        if response.status_code == 401:
            self._track_failed_attempt(client_ip, request.url.path)

        return response

    def _is_suspicious_request(self, request: Request) -> bool:
        """Detect suspicious request patterns."""
        suspicious_patterns = [
            "SELECT",
            "UNION",
            "DROP",
            "INSERT",
            "UPDATE",
            "DELETE",  # SQL injection
            "<script>",
            "javascript:",
            "onload=",
            "onerror=",  # XSS
            "../",
            "..\\",
            "/etc/passwd",
            "/etc/shadow",  # Path traversal
            "cmd.exe",
            "/bin/sh",
            "powershell",  # Command injection
        ]

        # Check query parameters and path
        query_string = str(request.url.query)
        path = request.url.path

        return any(
            pattern.lower() in query_string.lower() or pattern.lower() in path.lower()
            for pattern in suspicious_patterns
        )

    def _check_rate_limit(self, client_ip: str) -> bool:
        """Basic rate limiting check."""
        current_time = time.time()
        window_size = 60  # 1 minute window
        max_requests = 100  # Max 100 requests per minute

        if client_ip not in self._failed_attempts:
            self._failed_attempts[client_ip] = {"requests": [], "blocked_until": 0}

        client_data = self._failed_attempts[client_ip]

        # Remove old requests outside window
        client_data["requests"] = [
            req_time
            for req_time in client_data["requests"]
            if current_time - req_time < window_size
        ]

        # Add current request
        client_data["requests"].append(current_time)

        return len(client_data["requests"]) > max_requests

    def _track_failed_attempt(self, client_ip: str, path: str) -> None:
        """Track failed authentication attempts."""
        if client_ip not in self._failed_attempts:
            self._failed_attempts[client_ip] = {
                "count": 0,
                "last_attempt": time.time(),
                "paths": [],
            }

        client_data = self._failed_attempts[client_ip]
        client_data["count"] += 1
        client_data["last_attempt"] = time.time()
        client_data["paths"].append(path)

        # Alert on multiple failed attempts
        if client_data["count"] > 5:
            self.logger.security(
                "Multiple failed authentication attempts",
                risk_level="high",
                ip_address=client_ip,
                attempt_count=client_data["count"],
                recent_paths=client_data["paths"][-5:],
            )


# Factory functions and utilities
def setup_observability_middleware(
    app: "FastAPI",
    config: ObservabilityConfig | None = None,
    service_name: str = "api",
    enable_metrics: bool = True,
    enable_tracing: bool = True,
    enable_logging: bool = True,
    enable_performance: bool = True,
    enable_security: bool = True,
) -> None:
    """Set up comprehensive observability middleware for FastAPI app."""
    if not _fastapi_available:
        raise ImportError("FastAPI not available for middleware setup")

    # Add middleware in reverse order (FastAPI processes them in reverse)

    # Security middleware (first to process)
    if enable_security:
        app.add_middleware(SecurityMiddleware, config=config, service_name=service_name)

    # Performance monitoring
    if enable_performance:
        app.add_middleware(
            PerformanceMonitoringMiddleware, config=config, service_name=service_name
        )

    # Detailed logging
    if enable_logging:
        app.add_middleware(LoggingMiddleware, config=config, service_name=service_name)

    # Distributed tracing
    if enable_tracing:
        app.add_middleware(TracingMiddleware, config=config, service_name=service_name)

    # Metrics collection
    if enable_metrics:
        app.add_middleware(MetricsMiddleware, service_name=service_name)

    # Main observability middleware (last to process, first to receive)
    # Note: Using LoggingMiddleware as the main observability middleware
    app.add_middleware(LoggingMiddleware, config=config, service_name=service_name)

    # Metrics endpoint not added; metrics exported via OTLP


def create_observability_middleware(
    config: ObservabilityConfig | None = None, service_name: str = "api"
) -> Callable[[Any], Any]:
    """Create observability middleware factory."""

    def middleware_factory(app):
        return LoggingMiddleware(app, config, service_name)

    return middleware_factory


def create_security_middleware(
    config: ObservabilityConfig | None = None, service_name: str = "security"
) -> Callable[[Any], Any]:
    """Create security middleware factory."""

    def middleware_factory(app):
        return SecurityMiddleware(app, config, service_name)

    return middleware_factory


def create_metrics_middleware(service_name: str = "api") -> Callable[[Any], Any]:
    """Create metrics middleware factory."""

    def middleware_factory(app):
        return MetricsMiddleware(app, service_name)

    return middleware_factory


def create_tracing_middleware(
    config: ObservabilityConfig | None = None, service_name: str = "api"
) -> Callable[[Any], Any]:
    """Create tracing middleware factory."""

    def middleware_factory(app):
        return TracingMiddleware(app, config, service_name)

    return middleware_factory


def create_logging_middleware(
    config: ObservabilityConfig | None = None, service_name: str = "api", **kwargs
) -> Callable[[Any], Any]:
    """Create logging middleware factory."""

    def middleware_factory(app):
        return LoggingMiddleware(app, config, service_name, **kwargs)

    return middleware_factory


def create_performance_middleware(
    config: ObservabilityConfig | None = None, service_name: str = "api", **kwargs
) -> Callable[[Any], Any]:
    """Create performance monitoring middleware factory."""

    def middleware_factory(app):
        return PerformanceMonitoringMiddleware(app, config, service_name, **kwargs)

    return middleware_factory


def create_metrics_collector(service_name: str = "api") -> MetricsCollector:
    """Create metrics collector."""
    return MetricsCollector(service_name)
