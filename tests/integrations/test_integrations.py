"""Tests for integrations module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from dotmac.platform.integrations import (
    IntegrationStatus,
    IntegrationType,
    IntegrationConfig,
    IntegrationHealth,
    BaseIntegration
)


class TestIntegrationStatus:
    """Test IntegrationStatus enum."""

    def test_status_values(self):
        """Test all status values are defined."""
        assert IntegrationStatus.DISABLED == "disabled"
        assert IntegrationStatus.CONFIGURING == "configuring"
        assert IntegrationStatus.READY == "ready"
        assert IntegrationStatus.ERROR == "error"
        assert IntegrationStatus.DEPRECATED == "deprecated"

    def test_status_enum_iteration(self):
        """Test enum can be iterated."""
        statuses = list(IntegrationStatus)
        assert len(statuses) >= 5
        assert IntegrationStatus.READY in statuses


class TestIntegrationType:
    """Test IntegrationType enum."""

    def test_type_values(self):
        """Test all integration types are defined."""
        assert IntegrationType.EMAIL == "email"
        assert IntegrationType.SMS == "sms"
        assert IntegrationType.STORAGE == "storage"
        assert IntegrationType.SEARCH == "search"
        assert IntegrationType.ANALYTICS == "analytics"
        assert IntegrationType.MONITORING == "monitoring"
        assert IntegrationType.SECRETS == "secrets"
        assert IntegrationType.CACHE == "cache"
        assert IntegrationType.QUEUE == "queue"

    def test_type_enum_iteration(self):
        """Test enum can be iterated."""
        types = list(IntegrationType)
        assert len(types) >= 9
        assert IntegrationType.EMAIL in types


class TestIntegrationConfig:
    """Test IntegrationConfig dataclass."""

    def test_config_creation(self):
        """Test creating integration config."""
        config = IntegrationConfig(
            name="sendgrid",
            type=IntegrationType.EMAIL,
            provider="sendgrid",
            enabled=True,
            settings={"api_version": "v3"}
        )

        assert config.name == "sendgrid"
        assert config.type == IntegrationType.EMAIL
        assert config.provider == "sendgrid"
        assert config.enabled is True
        assert config.settings["api_version"] == "v3"

    def test_config_with_secrets_path(self):
        """Test config with secrets path."""
        config = IntegrationConfig(
            name="sendgrid",
            type=IntegrationType.EMAIL,
            provider="sendgrid",
            enabled=True,
            settings={},
            secrets_path="email/sendgrid"
        )

        assert config.secrets_path == "email/sendgrid"

    def test_config_with_required_packages(self):
        """Test config with required packages."""
        config = IntegrationConfig(
            name="sendgrid",
            type=IntegrationType.EMAIL,
            provider="sendgrid",
            enabled=True,
            settings={},
            required_packages=["sendgrid", "python-dotenv"]
        )

        assert len(config.required_packages) == 2
        assert "sendgrid" in config.required_packages

    def test_config_default_health_check_interval(self):
        """Test default health check interval."""
        config = IntegrationConfig(
            name="test",
            type=IntegrationType.EMAIL,
            provider="test",
            enabled=True,
            settings={}
        )

        assert config.health_check_interval == 300  # 5 minutes default


class TestIntegrationHealth:
    """Test IntegrationHealth dataclass."""

    def test_health_creation(self):
        """Test creating health status."""
        health = IntegrationHealth(
            name="sendgrid",
            status=IntegrationStatus.READY,
            message="Healthy"
        )

        assert health.name == "sendgrid"
        assert health.status == IntegrationStatus.READY
        assert health.message == "Healthy"

    def test_health_with_metadata(self):
        """Test health with metadata."""
        health = IntegrationHealth(
            name="redis",
            status=IntegrationStatus.READY,
            metadata={"connections": 10, "memory_used": "1.5MB"}
        )

        assert health.metadata["connections"] == 10
        assert health.metadata["memory_used"] == "1.5MB"

    def test_health_error_status(self):
        """Test health with error status."""
        health = IntegrationHealth(
            name="postgres",
            status=IntegrationStatus.ERROR,
            message="Connection timeout",
            metadata={"error_code": "TIMEOUT"}
        )

        assert health.status == IntegrationStatus.ERROR
        assert "timeout" in health.message.lower()


class TestBaseIntegration:
    """Test BaseIntegration base class."""

    def test_base_integration_is_abstract(self):
        """Test BaseIntegration cannot be instantiated directly."""
        config = IntegrationConfig(
            name="test",
            type=IntegrationType.EMAIL,
            provider="test",
            enabled=True,
            settings={}
        )

        # BaseIntegration is abstract, so we need to create a concrete implementation
        with pytest.raises(TypeError):
            BaseIntegration(config)

    def test_concrete_integration_can_be_created(self):
        """Test concrete integration implementation."""
        config = IntegrationConfig(
            name="test",
            type=IntegrationType.EMAIL,
            provider="test",
            enabled=True,
            settings={}
        )

        class TestIntegration(BaseIntegration):
            async def initialize(self):
                pass

            async def health_check(self):
                return IntegrationHealth(
                    name=self.config.name,
                    status=IntegrationStatus.READY
                )

            async def shutdown(self):
                pass

        integration = TestIntegration(config)
        assert integration.config.name == "test"

    @pytest.mark.asyncio
    async def test_integration_lifecycle(self):
        """Test integration initialization and shutdown."""
        config = IntegrationConfig(
            name="test",
            type=IntegrationType.EMAIL,
            provider="test",
            enabled=True,
            settings={}
        )

        class TestIntegration(BaseIntegration):
            def __init__(self, config):
                super().__init__(config)
                self.initialized = False
                self.shutdown_called = False

            async def initialize(self):
                self.initialized = True

            async def health_check(self):
                return IntegrationHealth(
                    name=self.config.name,
                    status=IntegrationStatus.READY if self.initialized else IntegrationStatus.CONFIGURING
                )

            async def shutdown(self):
                self.shutdown_called = True

        integration = TestIntegration(config)
        assert not integration.initialized

        await integration.initialize()
        assert integration.initialized

        health = await integration.health_check()
        assert health.status == IntegrationStatus.READY

        await integration.shutdown()
        assert integration.shutdown_called

    @pytest.mark.asyncio
    async def test_integration_error_handling(self):
        """Test integration error handling."""
        config = IntegrationConfig(
            name="failing",
            type=IntegrationType.EMAIL,
            provider="test",
            enabled=True,
            settings={}
        )

        class FailingIntegration(BaseIntegration):
            async def initialize(self):
                raise ValueError("Initialization failed")

            async def health_check(self):
                return IntegrationHealth(
                    name=self.config.name,
                    status=IntegrationStatus.ERROR,
                    message="Health check failed"
                )

            async def shutdown(self):
                pass

        integration = FailingIntegration(config)

        with pytest.raises(ValueError, match="Initialization failed"):
            await integration.initialize()

        health = await integration.health_check()
        assert health.status == IntegrationStatus.ERROR