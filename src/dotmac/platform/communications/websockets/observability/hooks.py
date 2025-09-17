"""
Observability hooks for WebSocket gateway.
"""


import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

# Try to import OpenTelemetry (optional dependency)
try:
    from opentelemetry import metrics, trace
    from opentelemetry.trace import Status, StatusCode

    OTEL_AVAILABLE = True
except ImportError:
    trace = None
    metrics = None
    Status = None
    StatusCode = None
    OTEL_AVAILABLE = False

class WebSocketObservabilityHooks(ABC):
    """Abstract base class for WebSocket observability hooks."""

    @abstractmethod
    async def on_server_start(self, config):
        """Called when WebSocket server starts."""
        pass

    @abstractmethod
    async def on_server_stop(self):
        """Called when WebSocket server stops."""
        pass

    @abstractmethod
    async def on_connection(self, session):
        """Called when a new WebSocket connection is established."""
        pass

    @abstractmethod
    async def on_disconnection(self, session):
        """Called when a WebSocket connection is closed."""
        pass

    @abstractmethod
    async def on_authentication(self, session, auth_result):
        """Called when authentication occurs."""
        pass

    @abstractmethod
    async def on_message(self, session, raw_message: str):
        """Called when a message is received."""
        pass

    @abstractmethod
    async def on_message_sent(self, session, message_type: str, data: Any):
        """Called when a message is sent."""
        pass

    @abstractmethod
    async def on_channel_subscription(self, session, channel_name: str):
        """Called when a session subscribes to a channel."""
        pass

    @abstractmethod
    async def on_channel_unsubscription(self, session, channel_name: str):
        """Called when a session unsubscribes from a channel."""
        pass

    @abstractmethod
    async def on_broadcast(self, channel_name: str, message_type: str, subscriber_count: int):
        """Called when a broadcast is sent to a channel."""
        pass

    @abstractmethod
    async def on_error(self, session, error: Exception, context: dict[str, Any]):
        """Called when an error occurs."""
        pass

class DefaultObservabilityHooks(WebSocketObservabilityHooks):
    """Default observability hooks with basic logging."""

    def __init__(self, logger_name: str = "dotmac.websockets"):
        self.logger = get_logger(logger_name)

        # Statistics
        self._stats = {
            "connections_total": 0,
            "disconnections_total": 0,
            "messages_received_total": 0,
            "messages_sent_total": 0,
            "authentication_attempts_total": 0,
            "authentication_successes_total": 0,
            "channel_subscriptions_total": 0,
            "channel_unsubscriptions_total": 0,
            "broadcasts_total": 0,
            "errors_total": 0,
        }

        # Current state
        self._current_connections = 0
        self._server_start_time: Optional[float] = None

    async def on_server_start(self, config):
        """Called when WebSocket server starts."""
        self._server_start_time = time.time()
        self.logger.info(f"WebSocket server started on {config.host}:{config.port}{config.path}")

    async def on_server_stop(self):
        """Called when WebSocket server stops."""
        uptime = time.time() - self._server_start_time if self._server_start_time else 0
        self.logger.info(f"WebSocket server stopped after {uptime:.1f}s uptime")

    async def on_connection(self, session):
        """Called when a new WebSocket connection is established."""
        self._stats["connections_total"] += 1
        self._current_connections += 1

        self.logger.info(
            f"WebSocket connected: {session.session_id} "
            f"from {session.metadata.ip_address} "
            f"(total: {self._current_connections})"
        )

    async def on_disconnection(self, session):
        """Called when a WebSocket connection is closed."""
        self._stats["disconnections_total"] += 1
        self._current_connections = max(0, self._current_connections - 1)

        duration = time.time() - session.metadata.connected_at
        self.logger.info(
            f"WebSocket disconnected: {session.session_id} "
            f"after {duration:.1f}s, sent {session.metadata.messages_sent}, "
            f"received {session.metadata.messages_received} "
            f"(remaining: {self._current_connections})"
        )

    async def on_authentication(self, session, auth_result):
        """Called when authentication occurs."""
        self._stats["authentication_attempts_total"] += 1

        if auth_result.success:
            self._stats["authentication_successes_total"] += 1
            self.logger.info(
                f"Authentication successful for session {session.session_id}: "
                f"user={auth_result.user_info.user_id}, tenant={auth_result.user_info.tenant_id}"
            )
        else:
            self.logger.warning(
                f"Authentication failed for session {session.session_id}: " f"{auth_result.error}"
            )

    async def on_message(self, session, raw_message: str):
        """Called when a message is received."""
        self._stats["messages_received_total"] += 1

        self.logger.debug(
            f"Message received from {session.session_id}: " f"{len(raw_message)} bytes"
        )

    async def on_message_sent(self, session, message_type: str, data: Any):
        """Called when a message is sent."""
        self._stats["messages_sent_total"] += 1

        self.logger.debug(f"Message sent to {session.session_id}: type={message_type}")

    async def on_channel_subscription(self, session, channel_name: str):
        """Called when a session subscribes to a channel."""
        self._stats["channel_subscriptions_total"] += 1

        self.logger.debug(
            f"Channel subscription: session={session.session_id}, " f"channel={channel_name}"
        )

    async def on_channel_unsubscription(self, session, channel_name: str):
        """Called when a session unsubscribes from a channel."""
        self._stats["channel_unsubscriptions_total"] += 1

        self.logger.debug(
            f"Channel unsubscription: session={session.session_id}, " f"channel={channel_name}"
        )

    async def on_broadcast(self, channel_name: str, message_type: str, subscriber_count: int):
        """Called when a broadcast is sent to a channel."""
        self._stats["broadcasts_total"] += 1

        self.logger.debug(
            f"Broadcast sent: channel={channel_name}, "
            f"type={message_type}, subscribers={subscriber_count}"
        )

    async def on_error(self, session, error: Exception, context: dict[str, Any]):
        """Called when an error occurs."""
        self._stats["errors_total"] += 1

        session_id = session.session_id if session else "unknown"
        self.logger.error(
            f"WebSocket error in session {session_id}: {error}", extra={"context": context}
        )

    def get_stats(self) -> dict[str, Any]:
        """Get observability statistics."""
        uptime = time.time() - self._server_start_time if self._server_start_time else 0

        return {
            "uptime_seconds": uptime,
            "current_connections": self._current_connections,
            **self._stats,
        }

class OpenTelemetryObservabilityHooks(WebSocketObservabilityHooks):
    """OpenTelemetry-based observability hooks."""

    def __init__(self, service_name: str = "dotmac-websockets"):
        if not OTEL_AVAILABLE:
            raise ImportError("OpenTelemetry not available")

        self.service_name = service_name

        # Get tracer and meter
        self.tracer = trace.get_tracer(__name__)
        self.meter = metrics.get_meter(__name__)

        # Create metrics
        self._create_metrics()

        # Statistics
        self._current_connections = 0

    def _create_metrics(self):
        """Create OpenTelemetry metrics."""
        # Counters
        self.connections_counter = self.meter.create_counter(
            name="websocket_connections_total",
            description="Total number of WebSocket connections",
            unit="1",
        )

        self.disconnections_counter = self.meter.create_counter(
            name="websocket_disconnections_total",
            description="Total number of WebSocket disconnections",
            unit="1",
        )

        self.messages_received_counter = self.meter.create_counter(
            name="websocket_messages_received_total",
            description="Total number of messages received",
            unit="1",
        )

        self.messages_sent_counter = self.meter.create_counter(
            name="websocket_messages_sent_total",
            description="Total number of messages sent",
            unit="1",
        )

        self.authentication_counter = self.meter.create_counter(
            name="websocket_authentication_attempts_total",
            description="Total number of authentication attempts",
            unit="1",
        )

        self.channel_subscriptions_counter = self.meter.create_counter(
            name="websocket_channel_subscriptions_total",
            description="Total number of channel subscriptions",
            unit="1",
        )

        self.broadcasts_counter = self.meter.create_counter(
            name="websocket_broadcasts_total", description="Total number of broadcasts", unit="1"
        )

        self.errors_counter = self.meter.create_counter(
            name="websocket_errors_total", description="Total number of errors", unit="1"
        )

        # Gauges
        self.current_connections_gauge = self.meter.create_up_down_counter(
            name="websocket_current_connections",
            description="Current number of WebSocket connections",
            unit="1",
        )

        # Histograms
        self.connection_duration_histogram = self.meter.create_histogram(
            name="websocket_connection_duration_seconds",
            description="Duration of WebSocket connections",
            unit="s",
        )

        self.message_size_histogram = self.meter.create_histogram(
            name="websocket_message_size_bytes", description="Size of WebSocket messages", unit="by"
        )

    async def on_server_start(self, config):
        """Called when WebSocket server starts."""
        with self.tracer.start_as_current_span(
            "websocket_server_start",
            attributes={
                "service.name": self.service_name,
                "websocket.host": config.host,
                "websocket.port": config.port,
                "websocket.path": config.path,
                "websocket.backend": config.backend_type.value,
            },
        ) as span:
            span.set_status(Status(StatusCode.OK))

    async def on_server_stop(self):
        """Called when WebSocket server stops."""
        with self.tracer.start_as_current_span("websocket_server_stop") as span:
            span.set_status(Status(StatusCode.OK))

    async def on_connection(self, session):
        """Called when a new WebSocket connection is established."""
        self._current_connections += 1

        # Metrics
        self.connections_counter.add(
            1,
            {
                "tenant_id": session.tenant_id or "default",
                "ip_address": session.metadata.ip_address or "unknown",
            },
        )
        self.current_connections_gauge.add(1)

        # Span
        with self.tracer.start_as_current_span(
            "websocket_connection",
            attributes={
                "websocket.session_id": session.session_id,
                "websocket.ip_address": session.metadata.ip_address,
                "websocket.user_agent": session.metadata.user_agent,
                "websocket.tenant_id": session.tenant_id,
            },
        ) as span:
            span.set_status(Status(StatusCode.OK))

    async def on_disconnection(self, session):
        """Called when a WebSocket connection is closed."""
        self._current_connections = max(0, self._current_connections - 1)

        duration = time.time() - session.metadata.connected_at

        # Metrics
        self.disconnections_counter.add(1, {"tenant_id": session.tenant_id or "default"})
        self.current_connections_gauge.add(-1)
        self.connection_duration_histogram.record(
            duration, {"tenant_id": session.tenant_id or "default"}
        )

        # Span
        with self.tracer.start_as_current_span(
            "websocket_disconnection",
            attributes={
                "websocket.session_id": session.session_id,
                "websocket.duration_seconds": duration,
                "websocket.messages_sent": session.metadata.messages_sent,
                "websocket.messages_received": session.metadata.messages_received,
                "websocket.bytes_sent": session.metadata.bytes_sent,
                "websocket.bytes_received": session.metadata.bytes_received,
            },
        ) as span:
            span.set_status(Status(StatusCode.OK))

    async def on_authentication(self, session, auth_result):
        """Called when authentication occurs."""
        # Metrics
        self.authentication_counter.add(
            1,
            {
                "success": str(auth_result.success).lower(),
                "method": auth_result.auth_method or "unknown",
                "tenant_id": session.tenant_id or "default",
            },
        )

        # Span
        with self.tracer.start_as_current_span(
            "websocket_authentication",
            attributes={
                "websocket.session_id": session.session_id,
                "websocket.auth_method": auth_result.auth_method,
                "websocket.auth_success": auth_result.success,
                "websocket.user_id": (
                    auth_result.user_info.user_id if auth_result.user_info else None
                ),
                "websocket.tenant_id": (
                    auth_result.user_info.tenant_id if auth_result.user_info else None
                ),
            },
        ) as span:
            if auth_result.success:
                span.set_status(Status(StatusCode.OK))
            else:
                span.set_status(Status(StatusCode.ERROR, auth_result.error))

    async def on_message(self, session, raw_message: str):
        """Called when a message is received."""
        message_size = len(raw_message.encode("utf-8"))

        # Metrics
        self.messages_received_counter.add(
            1,
            {
                "tenant_id": session.tenant_id or "default",
                "authenticated": str(session.is_authenticated).lower(),
            },
        )
        self.message_size_histogram.record(
            message_size, {"direction": "received", "tenant_id": session.tenant_id or "default"}
        )

    async def on_message_sent(self, session, message_type: str, data: Any):
        """Called when a message is sent."""
        # Metrics
        self.messages_sent_counter.add(
            1, {"message_type": message_type, "tenant_id": session.tenant_id or "default"}
        )

    async def on_channel_subscription(self, session, channel_name: str):
        """Called when a session subscribes to a channel."""
        # Metrics
        self.channel_subscriptions_counter.add(
            1, {"channel": channel_name, "tenant_id": session.tenant_id or "default"}
        )

        # Span
        with self.tracer.start_as_current_span(
            "websocket_channel_subscription",
            attributes={
                "websocket.session_id": session.session_id,
                "websocket.channel": channel_name,
                "websocket.user_id": session.user_id,
            },
        ) as span:
            span.set_status(Status(StatusCode.OK))

    async def on_channel_unsubscription(self, session, channel_name: str):
        """Called when a session unsubscribes from a channel."""
        # Span
        with self.tracer.start_as_current_span(
            "websocket_channel_unsubscription",
            attributes={
                "websocket.session_id": session.session_id,
                "websocket.channel": channel_name,
                "websocket.user_id": session.user_id,
            },
        ) as span:
            span.set_status(Status(StatusCode.OK))

    async def on_broadcast(self, channel_name: str, message_type: str, subscriber_count: int):
        """Called when a broadcast is sent to a channel."""
        # Metrics
        self.broadcasts_counter.add(1, {"channel": channel_name, "message_type": message_type})

        # Span
        with self.tracer.start_as_current_span(
            "websocket_broadcast",
            attributes={
                "websocket.channel": channel_name,
                "websocket.message_type": message_type,
                "websocket.subscriber_count": subscriber_count,
            },
        ) as span:
            span.set_status(Status(StatusCode.OK))

    async def on_error(self, session, error: Exception, context: dict[str, Any]):
        """Called when an error occurs."""
        session_id = session.session_id if session else "unknown"
        tenant_id = session.tenant_id if session else "unknown"

        # Metrics
        self.errors_counter.add(1, {"error_type": type(error).__name__, "tenant_id": tenant_id})

        # Span
        with self.tracer.start_as_current_span(
            "websocket_error",
            attributes={
                "websocket.session_id": session_id,
                "error.type": type(error).__name__,
                "error.message": str(error),
                **{f"context.{k}": str(v) for k, v in context.items()},
            },
        ) as span:
            span.record_exception(error)
            span.set_status(Status(StatusCode.ERROR, str(error)))

def create_default_hooks(logger_name: str = "dotmac.websockets") -> DefaultObservabilityHooks:
    """Create default observability hooks."""
    return DefaultObservabilityHooks(logger_name)

def create_opentelemetry_hooks(
    service_name: str = "dotmac-websockets",
) -> Optional[OpenTelemetryObservabilityHooks]:
    """Create OpenTelemetry observability hooks."""
    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not available, falling back to default hooks")
        return None

    return OpenTelemetryObservabilityHooks(service_name)

def create_dotmac_observability_hooks(
    service_name: str = "dotmac-websockets",
) -> WebSocketObservabilityHooks:
    """Create DotMac observability hooks (tries OpenTelemetry first, falls back to default)."""
    otel_hooks = create_opentelemetry_hooks(service_name)
    if otel_hooks:
        return otel_hooks

    return create_default_hooks()

class CompositeObservabilityHooks(WebSocketObservabilityHooks):
    """Composite hooks that combine multiple observability hooks."""

    def __init__(self, hooks: list[WebSocketObservabilityHooks]):
        self.hooks = hooks

    async def on_server_start(self, config):
        """Called when WebSocket server starts."""
        for hook in self.hooks:
            try:
                await hook.on_server_start(config)
            except Exception as e:
                logger.error(f"Hook error in on_server_start: {e}")

    async def on_server_stop(self):
        """Called when WebSocket server stops."""
        for hook in self.hooks:
            try:
                await hook.on_server_stop()
            except Exception as e:
                logger.error(f"Hook error in on_server_stop: {e}")

    async def on_connection(self, session):
        """Called when a new WebSocket connection is established."""
        for hook in self.hooks:
            try:
                await hook.on_connection(session)
            except Exception as e:
                logger.error(f"Hook error in on_connection: {e}")

    async def on_disconnection(self, session):
        """Called when a WebSocket connection is closed."""
        for hook in self.hooks:
            try:
                await hook.on_disconnection(session)
            except Exception as e:
                logger.error(f"Hook error in on_disconnection: {e}")

    async def on_authentication(self, session, auth_result):
        """Called when authentication occurs."""
        for hook in self.hooks:
            try:
                await hook.on_authentication(session, auth_result)
            except Exception as e:
                logger.error(f"Hook error in on_authentication: {e}")

    async def on_message(self, session, raw_message: str):
        """Called when a message is received."""
        for hook in self.hooks:
            try:
                await hook.on_message(session, raw_message)
            except Exception as e:
                logger.error(f"Hook error in on_message: {e}")

    async def on_message_sent(self, session, message_type: str, data: Any):
        """Called when a message is sent."""
        for hook in self.hooks:
            try:
                await hook.on_message_sent(session, message_type, data)
            except Exception as e:
                logger.error(f"Hook error in on_message_sent: {e}")

    async def on_channel_subscription(self, session, channel_name: str):
        """Called when a session subscribes to a channel."""
        for hook in self.hooks:
            try:
                await hook.on_channel_subscription(session, channel_name)
            except Exception as e:
                logger.error(f"Hook error in on_channel_subscription: {e}")

    async def on_channel_unsubscription(self, session, channel_name: str):
        """Called when a session unsubscribes from a channel."""
        for hook in self.hooks:
            try:
                await hook.on_channel_unsubscription(session, channel_name)
            except Exception as e:
                logger.error(f"Hook error in on_channel_unsubscription: {e}")

    async def on_broadcast(self, channel_name: str, message_type: str, subscriber_count: int):
        """Called when a broadcast is sent to a channel."""
        for hook in self.hooks:
            try:
                await hook.on_broadcast(channel_name, message_type, subscriber_count)
            except Exception as e:
                logger.error(f"Hook error in on_broadcast: {e}")

    async def on_error(self, session, error: Exception, context: dict[str, Any]):
        """Called when an error occurs."""
        for hook in self.hooks:
            try:
                await hook.on_error(session, error, context)
            except Exception as e:
                logger.error(f"Hook error in on_error: {e}")

def create_composite_hooks(hooks: list[WebSocketObservabilityHooks]) -> CompositeObservabilityHooks:
    """Create composite observability hooks."""
    return CompositeObservabilityHooks(hooks)
