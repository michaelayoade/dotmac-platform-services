from dotmac.platform.observability.unified_logging import get_logger

"""
Monitoring service integrations for platform observability.

Provides standardized interfaces for integrating with various monitoring
and observability platforms including SigNoz.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, UTC
from enum import Enum
from typing import Any
from urllib.parse import urljoin

import httpx
import structlog

logger = get_logger(__name__)

class IntegrationStatus(str, Enum):
    """Integration status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"

class IntegrationType(str, Enum):
    """Supported integration types (for enums import tests)."""

    PROMETHEUS = "prometheus"
    DATADOG = "datadog"
    NEWRELIC = "newrelic"
    GRAFANA = "grafana"
    CUSTOM = "custom"

@dataclass
class IntegrationConfig:
    """Configuration for monitoring integrations."""

    name: str
    endpoint: str
    api_key: str | None = None
    timeout: int = 30
    retry_count: int = 3
    enabled: bool = True
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class MetricData:
    """Structured metric data for integrations."""

    name: str
    value: int | float
    timestamp: datetime | None = None
    labels: dict[str, str] = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)
        if self.labels is None:
            self.labels = {}
        if self.metadata is None:
            self.metadata = {}

class MonitoringIntegration(ABC):
    """Abstract base class for monitoring service integrations."""

    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.status = IntegrationStatus.PENDING
        # Allow injecting lightweight fakes in tests by widening type
        self.client: Any | None = None
        self.logger = logger.bind(integration=config.name)

    async def initialize(self) -> bool:
        """Initialize the integration connection."""
        try:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout), headers=self._get_headers()
            )

            if await self.health_check():
                self.status = IntegrationStatus.ACTIVE
                self.logger.info("Integration initialized successfully")
                return True
            else:
                self.status = IntegrationStatus.ERROR
                self.logger.error("Integration health check failed")
                return False

        except Exception as e:
            self.status = IntegrationStatus.ERROR
            self.logger.error("Integration initialization failed", error=str(e))
            return False

    async def shutdown(self):
        """Shutdown the integration and clean up resources."""
        if self.client:
            await self.client.aclose()
            self.client = None
        self.status = IntegrationStatus.INACTIVE
        self.logger.info("Integration shutdown complete")

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the integration service is healthy."""
        pass

    @abstractmethod
    async def send_metrics(self, metrics: list[MetricData]) -> bool:
        """Send metrics to the monitoring service."""
        pass

    @abstractmethod
    async def send_alert(self, alert_data: dict[str, Any]) -> bool:
        """Send alert to the monitoring service."""
        pass

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for requests."""
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    async def _make_request(
        self, method: str, endpoint: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Make HTTP request with error handling and retries."""
        if not self.client:
            self.logger.error("Client not initialized")
            return None

        url = urljoin(self.config.endpoint, endpoint)

        for attempt in range(self.config.retry_count):
            try:
                response = await self.client.request(method, url, json=data)
                # Some test fakes won't have raise_for_status; treat as OK
                rfs = getattr(response, "raise_for_status", None)
                if callable(rfs):
                    rfs()
                # Prefer json() if available; else empty dict if content falsy
                if hasattr(response, "json"):
                    return response.json()
                return {} if not getattr(response, "content", b"") else {"ok": True}

            except httpx.HTTPStatusError as e:
                self.logger.warning(
                    "HTTP error on attempt",
                    attempt=attempt + 1,
                    status_code=e.response.status_code,
                    error=str(e),
                )
                if attempt == self.config.retry_count - 1:
                    raise

            except Exception as e:
                self.logger.error("Request failed on attempt", attempt=attempt + 1, error=str(e))
                if attempt == self.config.retry_count - 1:
                    raise

            await asyncio.sleep(2**attempt)  # Exponential backoff

        return None

class SigNozIntegration(MonitoringIntegration):
    """SigNoz monitoring integration."""

    async def health_check(self) -> bool:
        """Check SigNoz service health."""
        try:
            response = await self._make_request("GET", "/api/v1/health")
            return response is not None and response.get("status") == "ok"
        except Exception as e:
            self.logger.error("SigNoz health check failed", error=str(e))
            return False

    async def send_metrics(self, metrics: list[MetricData]) -> bool:
        """Send metrics to SigNoz."""
        try:
            metric_payload = {
                "metrics": [
                    {
                        "name": metric.name,
                        "value": metric.value,
                        "timestamp": int(metric.timestamp.timestamp()),
                        "labels": metric.labels,
                        **metric.metadata,
                    }
                    for metric in metrics
                ]
            }

            response = await self._make_request("POST", "/api/v1/metrics", metric_payload)
            return response is not None

        except Exception as e:
            self.logger.error("Failed to send metrics to SigNoz", error=str(e))
            return False

    async def send_alert(self, alert_data: dict[str, Any]) -> bool:
        """Send alert to SigNoz."""
        try:
            response = await self._make_request("POST", "/api/v1/alerts", alert_data)
            return response is not None
        except Exception as e:
            self.logger.error("Failed to send alert to SigNoz", error=str(e))
            return False

class IntegrationManager:
    """Manages multiple monitoring integrations."""

    def __init__(self):
        self.integrations: dict[str, MonitoringIntegration] = {}
        self.logger = logger.bind(component="integration_manager")

    async def add_integration(self, integration: MonitoringIntegration) -> bool:
        """Add and initialize a monitoring integration."""
        try:
            success = await integration.initialize()
            if success:
                self.integrations[integration.config.name] = integration
                self.logger.info(
                    "Integration added successfully", integration=integration.config.name
                )
            return success
        except Exception as e:
            self.logger.error(
                "Failed to add integration", integration=integration.config.name, error=str(e)
            )
            return False

    async def remove_integration(self, name: str) -> bool:
        """Remove and shutdown a monitoring integration."""
        if name in self.integrations:
            try:
                await self.integrations[name].shutdown()
                del self.integrations[name]
                self.logger.info("Integration removed successfully", integration=name)
                return True
            except Exception as e:
                self.logger.error("Failed to remove integration", integration=name, error=str(e))
                return False
        return False

    async def broadcast_metrics(self, metrics: list[MetricData]) -> dict[str, bool]:
        """Broadcast metrics to all active integrations."""
        results = {}

        for name, integration in self.integrations.items():
            if integration.status == IntegrationStatus.ACTIVE:
                try:
                    success = await integration.send_metrics(metrics)
                    results[name] = success
                except Exception as e:
                    self.logger.error(
                        "Failed to send metrics to integration", integration=name, error=str(e)
                    )
                    results[name] = False
            else:
                results[name] = False

        return results

    async def broadcast_alert(self, alert_data: dict[str, Any]) -> dict[str, bool]:
        """Broadcast alert to all active integrations."""
        results = {}

        for name, integration in self.integrations.items():
            if integration.status == IntegrationStatus.ACTIVE:
                try:
                    success = await integration.send_alert(alert_data)
                    results[name] = success
                except Exception as e:
                    self.logger.error(
                        "Failed to send alert to integration", integration=name, error=str(e)
                    )
                    results[name] = False
            else:
                results[name] = False

        return results

    async def get_integration_status(self) -> dict[str, IntegrationStatus]:
        """Get status of all integrations."""
        return {name: integration.status for name, integration in self.integrations.items()}

    async def health_check_all(self) -> dict[str, bool]:
        """Run health check on all integrations."""
        results = {}

        for name, integration in self.integrations.items():
            try:
                healthy = await integration.health_check()
                results[name] = healthy

                # Update status based on health check
                if healthy and integration.status == IntegrationStatus.ERROR:
                    integration.status = IntegrationStatus.ACTIVE
                elif not healthy and integration.status == IntegrationStatus.ACTIVE:
                    integration.status = IntegrationStatus.ERROR

            except Exception as e:
                self.logger.error(
                    "Health check failed for integration", integration=name, error=str(e)
                )
                results[name] = False
                integration.status = IntegrationStatus.ERROR

        return results

    async def shutdown_all(self):
        """Shutdown all integrations."""
        for name, integration in self.integrations.items():
            try:
                await integration.shutdown()
                self.logger.info("Integration shutdown", integration=name)
            except Exception as e:
                self.logger.error("Failed to shutdown integration", integration=name, error=str(e))

        self.integrations.clear()
        self.logger.info("All integrations shutdown complete")
