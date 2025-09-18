"""Health check helper utilities for the API Gateway."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, Iterable

from dotmac.platform.observability.unified_logging import get_logger

logger = get_logger(__name__)


_STATUS_PRIORITY = {"unhealthy": 2, "degraded": 1, "unknown": 1, "healthy": 0}


@dataclass
class HealthResult:
    """Structured result produced for each health check."""

    status: str
    response_time: float | None = None
    details: Dict[str, Any] | None = None
    error: str | None = None

    def as_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"status": self.status}
        if self.response_time is not None:
            payload["response_time"] = self.response_time
        if self.details:
            payload["details"] = self.details
        if self.error:
            payload["error"] = self.error
        return payload


class HealthChecker:
    """Performs the individual health checks exposed by the gateway."""

    def __init__(self, gateway: "APIGateway", timeout: float = 2.0) -> None:
        from .gateway import APIGateway  # Local import to avoid cycle at module import

        if not isinstance(gateway, APIGateway):  # pragma: no cover - defensive programming
            raise TypeError("gateway must be an APIGateway instance")

        self.gateway = gateway
        self.timeout = timeout

    async def run_checks(self) -> Dict[str, Dict[str, Any]]:
        """Run all configured health checks and return the individual results."""

        checks: Dict[str, Dict[str, Any]] = {}
        for name, coroutine in self._health_checks():
            checks[name] = await self._run_single_check(name, coroutine)
        return checks

    def aggregate_health(self, checks: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate individual check results into an overall status."""

        overall_status = "healthy"
        for result in checks.values():
            status = result.get("status", "unknown").lower()
            if _STATUS_PRIORITY.get(status, 1) > _STATUS_PRIORITY.get(overall_status, 0):
                overall_status = status
                if overall_status == "unhealthy":
                    break

        summary = {
            "total": len(checks),
            "healthy": sum(1 for c in checks.values() if c.get("status") == "healthy"),
            "degraded": sum(1 for c in checks.values() if c.get("status") == "degraded"),
            "unhealthy": sum(1 for c in checks.values() if c.get("status") == "unhealthy"),
        }

        return {"status": overall_status, "checks": checks, "summary": summary}

    async def _run_single_check(
        self, name: str, coroutine_factory: Callable[[], Awaitable[Any]]
    ) -> Dict[str, Any]:
        start = time.perf_counter()
        try:
            result = await asyncio.wait_for(coroutine_factory(), timeout=self.timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Health check '{name}' timed out")
            return HealthResult(status="unhealthy", error="timeout").as_dict()
        except Exception as exc:  # pragma: no cover - defensive path
            logger.error(f"Health check '{name}' failed: {exc}")
            return HealthResult(status="unhealthy", error=str(exc)).as_dict()

        elapsed = time.perf_counter() - start

        if isinstance(result, HealthResult):
            payload = result.as_dict()
        elif isinstance(result, dict):
            payload = result.copy()
        else:  # pragma: no cover - runtime guard
            payload = {"status": "healthy", "details": {"value": result}}

        payload.setdefault("status", "healthy")
        payload.setdefault("response_time", elapsed)
        return payload

    def _health_checks(self) -> Iterable[tuple[str, Any]]:
        return (
            ("database", self.check_database),
            ("cache", self.check_cache),
            ("auth", self.check_auth_service),
            ("metrics", self.check_metrics_backend),
        )

    async def check_database(self) -> Dict[str, Any]:
        """Placeholder database health check."""
        if not getattr(self.gateway, "config", None):
            return {"status": "healthy", "details": {"message": "no database configured"}}
        return {"status": "healthy"}

    async def check_cache(self) -> Dict[str, Any]:
        cache = getattr(self.gateway, "cache_service", None)
        if not cache:
            return {"status": "degraded", "details": {"enabled": False}}

        try:
            await cache.get("gateway:health-ping")  # type: ignore[func-returns-value]
            return {"status": "healthy"}
        except Exception as exc:  # pragma: no cover - external dependency
            return {"status": "unhealthy", "error": str(exc)}

    async def check_auth_service(self) -> Dict[str, Any]:
        jwt_service = getattr(self.gateway, "jwt_service", None)
        if not jwt_service:
            return {"status": "degraded", "details": {"enabled": False}}
        return {"status": "healthy"}

    async def check_metrics_backend(self) -> Dict[str, Any]:
        analytics = getattr(self.gateway, "analytics", None)
        if not analytics:
            return {"status": "degraded", "details": {"message": "analytics disabled"}}

        try:
            summary = await analytics.get_metrics_summary()
            return {
                "status": "healthy",
                "details": {
                    "counters": len(summary.get("counters", {})) if isinstance(summary, dict) else 0,
                },
            }
        except Exception as exc:  # pragma: no cover - defensive
            return {"status": "unhealthy", "error": str(exc)}
