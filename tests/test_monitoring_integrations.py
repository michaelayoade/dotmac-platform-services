"""
Comprehensive tests for monitoring integrations.
"""

import logging

logger = logging.getLogger(__name__)
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from dotmac.platform.monitoring.integrations import (
    IntegrationConfig,
    IntegrationManager,
    IntegrationStatus,
    MetricData,
    MonitoringIntegration,
    SigNozIntegration,
)


class TestIntegrationConfig:
    """Test IntegrationConfig dataclass."""

    def test_integration_config_defaults(self):
        """Test default values are set correctly."""
        config = IntegrationConfig(name="test", endpoint="http://test.com")

        assert config.name == "test"
        assert config.endpoint == "http://test.com"
        assert config.api_key is None
        assert config.timeout == 30
        assert config.retry_count == 3
        assert config.enabled is True
        assert config.metadata == {}

    def test_integration_config_custom_values(self):
        """Test custom values are set correctly."""
        metadata = {"custom": "value"}
        config = IntegrationConfig(
            name="custom_test",
            endpoint="https://custom.com",
            api_key="secret_key",
            timeout=60,
            retry_count=5,
            enabled=False,
            metadata=metadata,
        )

        assert config.name == "custom_test"
        assert config.endpoint == "https://custom.com"
        assert config.api_key == "secret_key"
        assert config.timeout == 60
        assert config.retry_count == 5
        assert config.enabled is False
        assert config.metadata == metadata


class TestMetricData:
    """Test MetricData dataclass."""

    def test_metric_data_defaults(self):
        """Test default values are set correctly."""
        metric = MetricData(name="test_metric", value=42.5)

        assert metric.name == "test_metric"
        assert metric.value == 42.5
        assert isinstance(metric.timestamp, datetime)
        assert metric.labels == {}
        assert metric.metadata == {}

    def test_metric_data_custom_values(self):
        """Test custom values are set correctly."""
        timestamp = datetime.utcnow()
        labels = {"service": "api", "env": "prod"}
        metadata = {"source": "benchmark"}

        metric = MetricData(
            name="response_time", value=150, timestamp=timestamp, labels=labels, metadata=metadata
        )

        assert metric.name == "response_time"
        assert metric.value == 150
        assert metric.timestamp == timestamp
        assert metric.labels == labels
        assert metric.metadata == metadata


class TestMonitoringIntegration:
    """Test base MonitoringIntegration class."""

    class MockIntegration(MonitoringIntegration):
        """Mock implementation for testing."""

        def __init__(self, config, health_check_result=True):
            super().__init__(config)
            self._health_check_result = health_check_result
            self._metrics_sent = []
            self._alerts_sent = []

        async def health_check(self) -> bool:
            return self._health_check_result

        async def send_metrics(self, metrics) -> bool:
            self._metrics_sent.extend(metrics)
            return True

        async def send_alert(self, alert_data) -> bool:
            self._alerts_sent.append(alert_data)
            return True

        async def initialize(self) -> bool:
            # Use a simple fake client that never performs network IO
            self.client = FakeAsyncClient()
            ok = await self.health_check()
            self.status = IntegrationStatus.ACTIVE if ok else IntegrationStatus.ERROR
            return ok

    class FakeResponse:
        def __init__(self, payload: dict | None = None):
            self._payload = payload or {}
            self.content = b"{}" if payload is not None else b""

        def json(self):
            return self._payload

    class FakeAsyncClient:
        def __init__(self, sequence: list | None = None):
            self._sequence = sequence or []
            self.calls = 0

        async def request(self, method, url, json=None):
            self.calls += 1
            if self._sequence:
                item = self._sequence.pop(0)
                if isinstance(item, Exception):
                    raise item
                return TestMonitoringIntegration.FakeResponse(item)
            return TestMonitoringIntegration.FakeResponse({"status": "ok"})

        async def aclose(self):
            return None

    def test_initialization(self):
        """Test integration initialization."""
        config = IntegrationConfig(name="test", endpoint="http://test.com")
        integration = self.MockIntegration(config)

        assert integration.config == config
        assert integration.status == IntegrationStatus.PENDING
        assert integration.client is None

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful integration initialization."""
        config = IntegrationConfig(name="test", endpoint="http://test.com")
        integration = self.MockIntegration(config, health_check_result=True)

        result = await integration.initialize()
        assert result is True
        assert integration.status == IntegrationStatus.ACTIVE
        assert integration.client is not None

    @pytest.mark.asyncio
    async def test_initialize_health_check_failure(self):
        """Test initialization failure due to health check."""
        config = IntegrationConfig(name="test", endpoint="http://test.com")
        integration = self.MockIntegration(config, health_check_result=False)

        result = await integration.initialize()
        assert result is False
        assert integration.status == IntegrationStatus.ERROR

    @pytest.mark.asyncio
    async def test_shutdown(self):
        """Test integration shutdown."""
        config = IntegrationConfig(name="test", endpoint="http://test.com")
        integration = self.MockIntegration(config)

        # Use fake client
        integration.client = self.FakeAsyncClient()
        await integration.shutdown()
        assert integration.client is None
        assert integration.status == IntegrationStatus.INACTIVE

    def test_get_headers_without_api_key(self):
        """Test header generation without API key."""
        config = IntegrationConfig(name="test", endpoint="http://test.com")
        integration = self.MockIntegration(config)

        headers = integration._get_headers()

        expected_headers = {"Content-Type": "application/json"}
        assert headers == expected_headers

    def test_get_headers_with_api_key(self):
        """Test header generation with API key."""
        config = IntegrationConfig(name="test", endpoint="http://test.com", api_key="secret_key")
        integration = self.MockIntegration(config)

        headers = integration._get_headers()

        expected_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer secret_key",
        }
        assert headers == expected_headers

    @pytest.mark.asyncio
    async def test_make_request_success(self):
        """Test successful HTTP request."""
        config = IntegrationConfig(name="test", endpoint="http://test.com")
        integration = self.MockIntegration(config)

        # Fake client returns ok payload
        integration.client = self.FakeAsyncClient(sequence=[{"status": "ok"}])
        result = await integration._make_request("GET", "/api/health")
        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_make_request_no_client(self):
        """Test request when client is not initialized."""
        config = IntegrationConfig(name="test", endpoint="http://test.com")
        integration = self.MockIntegration(config)

        result = await integration._make_request("GET", "/api/health")

        assert result is None

    @pytest.mark.asyncio
    async def test_make_request_with_retries(self):
        """Test request retry logic."""
        config = IntegrationConfig(name="test", endpoint="http://test.com", retry_count=2)
        integration = self.MockIntegration(config)

        # Fake client: first raise HTTPStatusError, then succeed
        err = httpx.HTTPStatusError("Server Error", request=Mock(), response=Mock())
        integration.client = self.FakeAsyncClient(sequence=[err, {"status": "ok"}])
        result = await integration._make_request("GET", "/api/health")
        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_make_request_all_retries_fail_http_error(self):
        """Test request retries exhaust and raise on final HTTP error."""
        config = IntegrationConfig(name="test", endpoint="http://test.com", retry_count=2)
        integration = self.MockIntegration(config)

        # Always raise HTTPStatusError
        err = httpx.HTTPStatusError("Server Error", request=Mock(), response=Mock())
        integration.client = self.FakeAsyncClient(sequence=[err, err])
        with pytest.raises(httpx.HTTPStatusError):
            await integration._make_request("GET", "/api")

    @pytest.mark.asyncio
    async def test_make_request_all_retries_fail_exception(self):
        """Test request retries exhaust and raise on generic exception."""
        config = IntegrationConfig(name="test", endpoint="http://test.com", retry_count=2)
        integration = self.MockIntegration(config)

        integration.client = self.FakeAsyncClient(sequence=[RuntimeError("boom"), RuntimeError("boom")])
        with pytest.raises(RuntimeError):
            await integration._make_request("GET", "/api")


class TestSigNozIntegration:
    """Test SigNoz integration implementation."""

    def test_initialization(self):
        """Test SigNoz integration initialization."""
        config = IntegrationConfig(name="signoz", endpoint="http://signoz.com")
        integration = SigNozIntegration(config)

        assert integration.config == config
        assert integration.status == IntegrationStatus.PENDING

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful SigNoz health check."""
        config = IntegrationConfig(name="signoz", endpoint="http://signoz.com")
        integration = SigNozIntegration(config)

        # Use fake client with ok response
        integration.client = TestMonitoringIntegration.FakeAsyncClient(sequence=[{"status": "ok"}])
        result = await integration.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test SigNoz health check failure."""
        config = IntegrationConfig(name="signoz", endpoint="http://signoz.com")
        integration = SigNozIntegration(config)

        integration.client = TestMonitoringIntegration.FakeAsyncClient(sequence=[{"status": "error"}])
        result = await integration.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_send_metrics_success(self):
        """Test successful metric sending to SigNoz."""
        config = IntegrationConfig(name="signoz", endpoint="http://signoz.com")
        integration = SigNozIntegration(config)

        metrics = [
            MetricData(name="cpu_usage", value=75.5, labels={"host": "server1"}),
            MetricData(name="memory_usage", value=60.2, labels={"host": "server1"}),
        ]

        # Fake client accepts metrics payload and returns empty dict
        integration.client = TestMonitoringIntegration.FakeAsyncClient(sequence=[{}])
        result = await integration.send_metrics(metrics)
        assert result is True

    @pytest.mark.asyncio
    async def test_send_alert_success(self):
        """Test successful alert sending to SigNoz."""
        config = IntegrationConfig(name="signoz", endpoint="http://signoz.com")
        integration = SigNozIntegration(config)

        alert_data = {
            "alert_name": "High CPU Usage",
            "severity": "critical",
            "message": "CPU usage is above 90%",
        }

        integration.client = TestMonitoringIntegration.FakeAsyncClient(sequence=[{}])
        result = await integration.send_alert(alert_data)
        assert result is True

    @pytest.mark.asyncio
    async def test_send_metrics_failure_on_exception(self):
        """send_metrics returns False on exception path."""
        config = IntegrationConfig(name="signoz", endpoint="http://signoz.com")
        integration = SigNozIntegration(config)

        with patch.object(integration, "_make_request", side_effect=RuntimeError("boom")):
            metrics = [MetricData(name="x", value=1)]
            ok = await integration.send_metrics(metrics)
            assert ok is False


class TestIntegrationManager:
    """Test IntegrationManager functionality."""

    def test_initialization(self):
        """Test integration manager initialization."""
        manager = IntegrationManager()

        assert manager.integrations == {}
        assert manager.logger is not None

    @pytest.mark.asyncio
    async def test_add_integration_success(self):
        """Test successful integration addition."""
        manager = IntegrationManager()

        config = IntegrationConfig(name="test", endpoint="http://test.com")
        integration = Mock()
        integration.config = config
        integration.initialize = AsyncMock(return_value=True)

        result = await manager.add_integration(integration)

        assert result is True
        assert "test" in manager.integrations
        assert manager.integrations["test"] == integration
        integration.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_integration_failure(self):
        """Test integration addition failure."""
        manager = IntegrationManager()

        config = IntegrationConfig(name="test", endpoint="http://test.com")
        integration = Mock()
        integration.config = config
        integration.initialize = AsyncMock(return_value=False)

        result = await manager.add_integration(integration)

        assert result is False
        assert "test" not in manager.integrations

    @pytest.mark.asyncio
    async def test_remove_integration_success(self):
        """Test successful integration removal."""
        manager = IntegrationManager()

        # Add integration first
        integration = Mock()
        integration.shutdown = AsyncMock()
        manager.integrations["test"] = integration

        result = await manager.remove_integration("test")

        assert result is True
        assert "test" not in manager.integrations
        integration.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_integration_not_found(self):
        """Test integration removal when integration doesn't exist."""
        manager = IntegrationManager()

        result = await manager.remove_integration("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_broadcast_metrics(self):
        """Test broadcasting metrics to all integrations."""
        manager = IntegrationManager()

        # Setup mock integrations
        integration1 = Mock()
        integration1.status = IntegrationStatus.ACTIVE
        integration1.send_metrics = AsyncMock(return_value=True)

        integration2 = Mock()
        integration2.status = IntegrationStatus.ACTIVE
        integration2.send_metrics = AsyncMock(return_value=False)

        integration3 = Mock()
        integration3.status = IntegrationStatus.ERROR
        integration3.send_metrics = AsyncMock()

        manager.integrations = {
            "integration1": integration1,
            "integration2": integration2,
            "integration3": integration3,
        }

        metrics = [MetricData(name="test", value=42)]
        results = await manager.broadcast_metrics(metrics)

        # Verify results
        assert results["integration1"] is True
        assert results["integration2"] is False
        assert results["integration3"] is False  # Not active, so False

        # Verify calls
        integration1.send_metrics.assert_called_once_with(metrics)
        integration2.send_metrics.assert_called_once_with(metrics)
        integration3.send_metrics.assert_not_called()  # Not active

    @pytest.mark.asyncio
    async def test_broadcast_alert(self):
        """Test broadcasting alerts to all integrations."""
        manager = IntegrationManager()

        # Setup mock integrations
        integration1 = Mock()
        integration1.status = IntegrationStatus.ACTIVE
        integration1.send_alert = AsyncMock(return_value=True)

        integration2 = Mock()
        integration2.status = IntegrationStatus.INACTIVE
        integration2.send_alert = AsyncMock()

        manager.integrations = {"integration1": integration1, "integration2": integration2}

        alert_data = {"message": "Test alert"}
        results = await manager.broadcast_alert(alert_data)

        # Verify results
        assert results["integration1"] is True
        assert results["integration2"] is False  # Not active

        # Verify calls
        integration1.send_alert.assert_called_once_with(alert_data)
        integration2.send_alert.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_integration_status(self):
        """Test getting status of all integrations."""
        manager = IntegrationManager()

        integration1 = Mock()
        integration1.status = IntegrationStatus.ACTIVE

        integration2 = Mock()
        integration2.status = IntegrationStatus.ERROR

        manager.integrations = {"integration1": integration1, "integration2": integration2}

        status = await manager.get_integration_status()

        assert status == {
            "integration1": IntegrationStatus.ACTIVE,
            "integration2": IntegrationStatus.ERROR,
        }

    @pytest.mark.asyncio
    async def test_health_check_all(self):
        """Test health check for all integrations."""
        manager = IntegrationManager()

        # Setup mock integrations
        integration1 = Mock()
        integration1.status = IntegrationStatus.ACTIVE
        integration1.health_check = AsyncMock(return_value=True)

        integration2 = Mock()
        integration2.status = IntegrationStatus.ERROR
        integration2.health_check = AsyncMock(return_value=False)

        manager.integrations = {"integration1": integration1, "integration2": integration2}

        results = await manager.health_check_all()

        # Verify results
        assert results["integration1"] is True
        assert results["integration2"] is False

        # Verify calls
        integration1.health_check.assert_called_once()
        integration2.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_all_handles_exception_and_sets_error_status(self):
        """Exception during health_check should mark integration as error and return False."""
        manager = IntegrationManager()

        broken = Mock()
        broken.status = IntegrationStatus.ACTIVE
        broken.health_check = AsyncMock(side_effect=RuntimeError("boom"))

        manager.integrations = {"broken": broken}

        res = await manager.health_check_all()
        assert res["broken"] is False
        assert broken.status == IntegrationStatus.ERROR

    @pytest.mark.asyncio
    async def test_shutdown_all(self):
        """Test shutting down all integrations."""
        manager = IntegrationManager()

        # Setup mock integrations
        integration1 = Mock()
        integration1.shutdown = AsyncMock()

        integration2 = Mock()
        integration2.shutdown = AsyncMock()

        manager.integrations = {"integration1": integration1, "integration2": integration2}

        await manager.shutdown_all()

        # Verify calls
        integration1.shutdown.assert_called_once()
        integration2.shutdown.assert_called_once()

        # Verify integrations are cleared
        assert manager.integrations == {}
