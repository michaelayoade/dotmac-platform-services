"""
Health monitoring for WebSocket gateway.
"""

import asyncio

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

class HealthStatus(str, Enum):
    """Health check status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """Result of a health check."""

    name: str
    status: HealthStatus
    message: Optional[str] = None

    # Metrics
    response_time_ms: Optional[float] = None
    timestamp: float = field(default_factory=time.time)

    # Additional data
    details: dict[str, Any] = field(default_factory=dict)

@dataclass
class ComponentHealth:
    """Health status of a system component."""

    name: str
    status: HealthStatus
    last_check: float
    last_success: Optional[float] = None
    failure_count: int = 0
    success_count: int = 0

    # Thresholds
    max_failures: int = 3
    check_interval_seconds: int = 30

    # Results history
    recent_results: list[HealthCheckResult] = field(default_factory=list)
    max_history: int = 10

    def add_result(self, result: HealthCheckResult):
        """Add a health check result."""
        self.recent_results.append(result)

        # Trim history
        if len(self.recent_results) > self.max_history:
            self.recent_results = self.recent_results[-self.max_history :]

        # Update counters
        if result.status == HealthStatus.HEALTHY:
            self.success_count += 1
            self.last_success = result.timestamp
            self.failure_count = 0  # Reset failure count on success
        else:
            self.failure_count += 1

        # Update overall status
        self.last_check = result.timestamp

        if result.status == HealthStatus.HEALTHY:
            self.status = HealthStatus.HEALTHY
        elif self.failure_count >= self.max_failures:
            self.status = HealthStatus.UNHEALTHY
        else:
            self.status = HealthStatus.DEGRADED

    def is_due_for_check(self) -> bool:
        """Check if component is due for health check."""
        return (time.time() - self.last_check) >= self.check_interval_seconds

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "status": self.status.value,
            "last_check": self.last_check,
            "last_success": self.last_success,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "recent_results": [
                {
                    "status": r.status.value,
                    "message": r.message,
                    "response_time_ms": r.response_time_ms,
                    "timestamp": r.timestamp,
                }
                for r in self.recent_results[-5:]  # Last 5 results
            ],
        }

class WebSocketHealthCheck:
    """Health monitoring for WebSocket gateway."""

    def __init__(self, gateway):
        self.gateway = gateway
        self.config = gateway.config.observability_config

        # Health checks
        self._health_checks: dict[str, Callable[[], Awaitable[HealthCheckResult]]] = {}
        self._component_health: dict[str, ComponentHealth] = {}

        # Monitoring task
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False

        # Overall health
        self._overall_status = HealthStatus.UNKNOWN
        self._start_time = time.time()

        # Register built-in health checks
        self._register_builtin_checks()

    def _register_builtin_checks(self):
        """Register built-in health checks."""

        async def check_server_status():
            """Check if WebSocket server is running."""
            start_time = time.time()

            try:
                if self.gateway._running:
                    response_time = (time.time() - start_time) * 1000
                    return HealthCheckResult(
                        name="server_status",
                        status=HealthStatus.HEALTHY,
                        message="WebSocket server is running",
                        response_time_ms=response_time,
                        details={
                            "host": self.gateway.config.host,
                            "port": self.gateway.config.port,
                            "path": self.gateway.config.path,
                        },
                    )
                else:
                    return HealthCheckResult(
                        name="server_status",
                        status=HealthStatus.UNHEALTHY,
                        message="WebSocket server is not running",
                    )
            except Exception as e:
                return HealthCheckResult(
                    name="server_status",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Server status check failed: {e}",
                )

        async def check_session_manager():
            """Check session manager health."""
            start_time = time.time()

            try:
                stats = self.gateway.session_manager.get_stats()
                total_sessions = stats.get("total_sessions", 0)

                # Consider unhealthy if too many sessions
                max_sessions = 10000  # Configurable threshold

                if total_sessions > max_sessions:
                    status = HealthStatus.DEGRADED
                    message = f"High session count: {total_sessions}"
                else:
                    status = HealthStatus.HEALTHY
                    message = f"Session manager healthy: {total_sessions} sessions"

                response_time = (time.time() - start_time) * 1000

                return HealthCheckResult(
                    name="session_manager",
                    status=status,
                    message=message,
                    response_time_ms=response_time,
                    details=stats,
                )

            except Exception as e:
                return HealthCheckResult(
                    name="session_manager",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Session manager check failed: {e}",
                )

        async def check_scaling_backend():
            """Check scaling backend health."""
            start_time = time.time()

            try:
                if self.gateway.scaling_backend:
                    health = await self.gateway.scaling_backend.health_check()
                    response_time = (time.time() - start_time) * 1000

                    status_map = {
                        "healthy": HealthStatus.HEALTHY,
                        "degraded": HealthStatus.DEGRADED,
                        "unhealthy": HealthStatus.UNHEALTHY,
                        "stopped": HealthStatus.UNHEALTHY,
                    }

                    return HealthCheckResult(
                        name="scaling_backend",
                        status=status_map.get(health["status"], HealthStatus.UNKNOWN),
                        message=health.get("error", f"Backend status: {health['status']}"),
                        response_time_ms=response_time,
                        details=health,
                    )
                else:
                    return HealthCheckResult(
                        name="scaling_backend",
                        status=HealthStatus.HEALTHY,
                        message="No scaling backend configured",
                    )

            except Exception as e:
                return HealthCheckResult(
                    name="scaling_backend",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Scaling backend check failed: {e}",
                )

        async def check_channel_manager():
            """Check channel manager health."""
            start_time = time.time()

            try:
                stats = self.gateway.channel_manager.get_stats()
                total_channels = stats.get("total_channels", 0)

                # Consider degraded if too many channels
                max_channels = 1000  # Configurable threshold

                if total_channels > max_channels:
                    status = HealthStatus.DEGRADED
                    message = f"High channel count: {total_channels}"
                else:
                    status = HealthStatus.HEALTHY
                    message = f"Channel manager healthy: {total_channels} channels"

                response_time = (time.time() - start_time) * 1000

                return HealthCheckResult(
                    name="channel_manager",
                    status=status,
                    message=message,
                    response_time_ms=response_time,
                    details=stats,
                )

            except Exception as e:
                return HealthCheckResult(
                    name="channel_manager",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Channel manager check failed: {e}",
                )

        async def check_rate_limiting():
            """Check rate limiting health."""
            start_time = time.time()

            try:
                stats = self.gateway.rate_limit_middleware.get_stats()

                if not stats.get("enabled", False):
                    return HealthCheckResult(
                        name="rate_limiting",
                        status=HealthStatus.HEALTHY,
                        message="Rate limiting disabled",
                    )

                response_time = (time.time() - start_time) * 1000

                return HealthCheckResult(
                    name="rate_limiting",
                    status=HealthStatus.HEALTHY,
                    message="Rate limiting operational",
                    response_time_ms=response_time,
                    details=stats,
                )

            except Exception as e:
                return HealthCheckResult(
                    name="rate_limiting",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Rate limiting check failed: {e}",
                )

        # Register checks
        self.register_health_check("server_status", check_server_status)
        self.register_health_check("session_manager", check_session_manager)
        self.register_health_check("scaling_backend", check_scaling_backend)
        self.register_health_check("channel_manager", check_channel_manager)
        self.register_health_check("rate_limiting", check_rate_limiting)

    def register_health_check(
        self, name: str, check_func: Callable[[], Awaitable[HealthCheckResult]]
    ):
        """Register a health check function."""
        self._health_checks[name] = check_func
        self._component_health[name] = ComponentHealth(
            name=name, status=HealthStatus.UNKNOWN, last_check=0
        )

    def unregister_health_check(self, name: str):
        """Unregister a health check."""
        self._health_checks.pop(name, None)
        self._component_health.pop(name, None)

    async def start_monitoring(self):
        """Start health monitoring."""
        if not self.config.health_check_enabled:
            return

        if self._running:
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Health monitoring started")

    async def stop_monitoring(self):
        """Stop health monitoring."""
        if not self._running:
            return

        self._running = False

        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Health monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                # Run health checks for due components
                for name, component in self._component_health.items():
                    if component.is_due_for_check():
                        await self._run_health_check(name)

                # Update overall health status
                self._update_overall_status()

                # Sleep until next check
                await asyncio.sleep(5)  # Check every 5 seconds for due components

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(10)  # Back off on error

    async def _run_health_check(self, name: str):
        """Run a specific health check."""
        check_func = self._health_checks.get(name)
        component = self._component_health.get(name)

        if not check_func or not component:
            return

        try:
            result = await check_func()
            component.add_result(result)

            logger.debug(f"Health check {name}: {result.status.value} - {result.message}")

        except Exception as e:
            error_result = HealthCheckResult(
                name=name, status=HealthStatus.UNHEALTHY, message=f"Health check exception: {e}"
            )
            component.add_result(error_result)
            logger.error(f"Health check {name} failed: {e}")

    def _update_overall_status(self):
        """Update overall health status based on components."""
        if not self._component_health:
            self._overall_status = HealthStatus.UNKNOWN
            return

        statuses = [comp.status for comp in self._component_health.values()]

        # If any component is unhealthy, overall is unhealthy
        if HealthStatus.UNHEALTHY in statuses:
            self._overall_status = HealthStatus.UNHEALTHY
        # If any component is degraded, overall is degraded
        elif HealthStatus.DEGRADED in statuses:
            self._overall_status = HealthStatus.DEGRADED
        # If all components are healthy, overall is healthy
        elif all(status == HealthStatus.HEALTHY for status in statuses):
            self._overall_status = HealthStatus.HEALTHY
        # Otherwise unknown
        else:
            self._overall_status = HealthStatus.UNKNOWN

    async def run_all_checks(self) -> dict[str, HealthCheckResult]:
        """Run all health checks immediately."""
        results = {}

        for name in self._health_checks:
            await self._run_health_check(name)
            component = self._component_health[name]
            if component.recent_results:
                results[name] = component.recent_results[-1]

        self._update_overall_status()
        return results

    async def run_check(self, name: str) -> Optional[HealthCheckResult]:
        """Run a specific health check."""
        if name not in self._health_checks:
            return None

        await self._run_health_check(name)
        component = self._component_health[name]
        return component.recent_results[-1] if component.recent_results else None

    def get_health_status(self) -> dict[str, Any]:
        """Get current health status."""
        uptime_seconds = time.time() - self._start_time

        return {
            "status": self._overall_status.value,
            "timestamp": time.time(),
            "uptime_seconds": uptime_seconds,
            "monitoring_enabled": self._running,
            "components": {
                name: component.to_dict() for name, component in self._component_health.items()
            },
        }

    def is_healthy(self) -> bool:
        """Check if overall status is healthy."""
        return self._overall_status == HealthStatus.HEALTHY

    def get_component_status(self, name: str) -> Optional[ComponentHealth]:
        """Get status of a specific component."""
        return self._component_health.get(name)

    async def wait_for_healthy(self, timeout_seconds: int = 30) -> bool:
        """Wait for system to become healthy."""
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            await self.run_all_checks()

            if self.is_healthy():
                return True

            await asyncio.sleep(1)

        return False
