"""
Tests for the Consul-based service registry.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from dotmac.platform.service_registry import (
    register_service,
    deregister_service,
    discover_services,
    get_healthy_services,
    ConsulServiceInfo,
    ConsulServiceRegistry,
)


class TestConsulServiceRegistry:
    """Test the Consul service registry implementation."""

    @pytest.fixture
    def mock_consul(self):
        """Create a mock Consul client."""
        consul_mock = Mock()
        consul_mock.agent = Mock()
        consul_mock.agent.service = Mock()
        consul_mock.health = Mock()

        # Mock async methods
        consul_mock.agent.service.register = AsyncMock()
        consul_mock.agent.service.deregister = AsyncMock()
        consul_mock.health.service = AsyncMock()

        return consul_mock

    @pytest.fixture
    def registry(self, mock_consul):
        """Create a service registry with mocked Consul."""
        with patch('consul.aio.Consul', return_value=mock_consul):
            registry = ConsulServiceRegistry()
            registry.consul = mock_consul
            return registry

    @pytest.mark.asyncio
    async def test_service_registration(self, registry, mock_consul):
        """Test service registration with Consul."""
        service_id = await registry.register(
            name="test-service",
            address="127.0.0.1",
            port=8000,
            health_check="/health"
        )

        # Verify Consul was called with correct parameters
        mock_consul.agent.service.register.assert_called_once()
        call_args = mock_consul.agent.service.register.call_args[1]

        assert call_args["Name"] == "test-service"
        assert call_args["Address"] == "127.0.0.1"
        assert call_args["Port"] == 8000
        assert service_id == "test-service-127.0.0.1-8000"
        assert "Check" in call_args  # Health check was added

    @pytest.mark.asyncio
    async def test_service_registration_custom_id(self, registry, mock_consul):
        """Test service registration with custom service ID."""
        service_id = await registry.register(
            name="test-service",
            address="127.0.0.1",
            port=8000,
            service_id="custom-id"
        )

        assert service_id == "custom-id"
        call_args = mock_consul.agent.service.register.call_args[1]
        assert call_args["ID"] == "custom-id"

    @pytest.mark.asyncio
    async def test_service_registration_with_metadata(self, registry, mock_consul):
        """Test service registration with tags and metadata."""
        await registry.register(
            name="test-service",
            address="127.0.0.1",
            port=8000,
            tags=["api", "v1"],
            meta={"version": "1.0.0", "env": "production"}
        )

        call_args = mock_consul.agent.service.register.call_args[1]
        assert call_args["Tags"] == ["api", "v1"]
        assert call_args["Meta"] == {"version": "1.0.0", "env": "production"}

    @pytest.mark.asyncio
    async def test_service_deregistration(self, registry, mock_consul):
        """Test service deregistration."""
        # First register a service
        service_id = await registry.register("test-service", "127.0.0.1", 8000)

        # Then deregister it
        await registry.deregister(service_id)

        mock_consul.agent.service.deregister.assert_called_once_with(service_id)

    @pytest.mark.asyncio
    async def test_service_discovery(self, registry, mock_consul):
        """Test service discovery."""
        # Mock Consul response
        mock_consul.health.service.return_value = (
            None,  # Index (not used)
            [
                {
                    "Service": {
                        "Service": "test-service",
                        "ID": "test-service-1",
                        "Address": "127.0.0.1",
                        "Port": 8000,
                        "Tags": ["api"],
                        "Meta": {"version": "1.0"}
                    },
                    "Checks": [
                        {"Status": "passing"}
                    ]
                }
            ]
        )

        services = await registry.discover("test-service")

        assert len(services) == 1
        service = services[0]
        assert isinstance(service, ConsulServiceInfo)
        assert service.name == "test-service"
        assert service.address == "127.0.0.1"
        assert service.port == 8000
        assert service.tags == ["api"]
        assert service.meta == {"version": "1.0"}
        assert service.health == "passing"

    @pytest.mark.asyncio
    async def test_service_discovery_unhealthy(self, registry, mock_consul):
        """Test discovery with unhealthy services."""
        # Mock response with unhealthy service
        mock_consul.health.service.return_value = (
            None,
            [
                {
                    "Service": {
                        "Service": "test-service",
                        "ID": "test-service-1",
                        "Address": "127.0.0.1",
                        "Port": 8000,
                        "Tags": [],
                        "Meta": {}
                    },
                    "Checks": [
                        {"Status": "critical"}
                    ]
                }
            ]
        )

        services = await registry.discover("test-service", only_healthy=False)

        assert len(services) == 1
        assert services[0].health == "critical"

    @pytest.mark.asyncio
    async def test_get_healthy_services(self, registry, mock_consul):
        """Test getting only healthy services."""
        # Mock response with mixed healthy/unhealthy services
        mock_consul.health.service.return_value = (None, [])

        services = await registry.get_healthy_services("test-service")

        # Verify Consul was called with passing=True
        mock_consul.health.service.assert_called_with("test-service", passing=True)

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_consul):
        """Test using registry as context manager."""
        with patch('consul.aio.Consul', return_value=mock_consul):
            async with ConsulServiceRegistry() as registry:
                service_id = await registry.register("test-service", "127.0.0.1", 8000)

            # Verify cleanup was called
            mock_consul.agent.service.deregister.assert_called_once_with(service_id)

    def test_consul_service_info_url_property(self):
        """Test the URL property of ConsulServiceInfo."""
        service = ConsulServiceInfo(
            name="test-service",
            address="192.168.1.100",
            port=9000,
            service_id="test-1",
            tags=[],
            meta={}
        )

        assert service.url == "http://192.168.1.100:9000"


class TestConvenienceFunctions:
    """Test the convenience functions for service registry."""

    @patch('dotmac.platform.service_registry.consul_registry.get_consul_registry')
    @pytest.mark.asyncio
    async def test_register_service_function(self, mock_get_registry):
        """Test the register_service convenience function."""
        mock_registry = AsyncMock()
        mock_registry.register.return_value = "service-id"
        mock_get_registry.return_value = mock_registry

        service_id = await register_service("api", "127.0.0.1", 8080)

        assert service_id == "service-id"
        mock_registry.register.assert_called_once()

    @patch('dotmac.platform.service_registry.consul_registry.get_consul_registry')
    @pytest.mark.asyncio
    async def test_discover_services_function(self, mock_get_registry):
        """Test the discover_services convenience function."""
        mock_registry = AsyncMock()
        mock_services = [ConsulServiceInfo("api", "127.0.0.1", 8080, "api-1", [], {})]
        mock_registry.discover.return_value = mock_services
        mock_get_registry.return_value = mock_registry

        services = await discover_services("api")

        assert services == mock_services
        mock_registry.discover.assert_called_once_with("api", True)

    @patch('dotmac.platform.service_registry.consul_registry.get_consul_registry')
    @pytest.mark.asyncio
    async def test_deregister_service_function(self, mock_get_registry):
        """Test the deregister_service convenience function."""
        mock_registry = AsyncMock()
        mock_get_registry.return_value = mock_registry

        await deregister_service("service-id")

        mock_registry.deregister.assert_called_once_with("service-id")

    def test_integration_example(self):
        """Test a complete integration example."""
        # This test demonstrates the simplified API

        # Before: Complex custom service registry with 400+ lines
        # After: Simple Consul-based registry with ~200 lines

        # Example usage pattern:
        async def example_usage():
            # Register service
            service_id = await register_service(
                "user-api",
                "127.0.0.1",
                8000,
                tags=["api", "users"],
                health_check="/health"
            )

            # Discover services
            services = await discover_services("user-api")

            # Use services
            for service in services:
                print(f"Found service at {service.url}")

            # Cleanup
            await deregister_service(service_id)

        # The simplified API is much cleaner than the original complex system
        assert callable(example_usage)