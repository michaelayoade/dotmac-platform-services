"""
Standalone communication service for notifications
Replaces dependency on dotmac_shared.utils.universal_communication
"""


from typing import Any, Optional, Protocol

import httpx

from dotmac.platform.logging import get_logger
logger = get_logger(__name__)

class CommunicationProvider(Protocol):
    """Protocol for communication providers"""

    async def send(self, recipient: str, message: str, **kwargs) -> dict[str, Any]:
        """Send a message via this provider"""
        ...

class HttpWebhookProvider:
    """HTTP webhook communication provider"""

    def __init__(self, webhook_url: str, headers: Optional[dict[str, str]] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {}

    async def send(self, recipient: str, message: str, **kwargs) -> dict[str, Any]:
        """Send via HTTP webhook"""
        payload = {
            "recipient": recipient,
            "message": message,
            "timestamp": kwargs.get("timestamp"),
            "metadata": kwargs.get("metadata", {}),
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url, json=payload, headers=self.headers, timeout=30.0
                )
                response.raise_for_status()

                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response": response.text,
                }

        except Exception as e:
            logger.error(f"Webhook delivery failed: {e}")
            return {"success": False, "error": str(e)}

class LoggingProvider:
    """Logging-only provider for testing/fallback"""

    async def send(self, recipient: str, message: str, **kwargs) -> dict[str, Any]:
        """Log the message instead of sending"""
        logger.info(f"Mock send to {recipient}: {message}")
        return {"success": True, "method": "logging", "recipient": recipient}

class UniversalCommunicationService:
    """
    Standalone communication service
    Simplified version of the original dotmac_shared service
    """

    def __init__(self):
        self._providers: dict[str, CommunicationProvider] = {}
        self._default_provider = "logging"

        # Register default logging provider
        self.register_provider("logging", LoggingProvider())

    def register_provider(self, name: str, provider: CommunicationProvider):
        """Register a communication provider"""
        self._providers[name] = provider

    def register_webhook_provider(
        self, name: str, webhook_url: str, headers: Optional[dict[str, str]] = None
    ):
        """Register a webhook provider"""
        provider = HttpWebhookProvider(webhook_url, headers)
        self.register_provider(name, provider)

    async def send_notification(
        self, provider_name: str, recipient: str, message: str, **kwargs
    ) -> dict[str, Any]:
        """Send notification via specified provider"""
        provider = self._providers.get(provider_name)
        if not provider:
            logger.warning(f"Provider '{provider_name}' not found, using default")
            provider = self._providers[self._default_provider]

        try:
            result = await provider.send(recipient, message, **kwargs)
            result["provider"] = provider_name
            return result

        except Exception as e:
            logger.error(f"Communication failed via {provider_name}: {e}")
            return {"success": False, "provider": provider_name, "error": str(e)}

    async def broadcast(
        self, provider_names: list[str], recipient: str, message: str, **kwargs
    ) -> dict[str, dict[str, Any]]:
        """Broadcast message via multiple providers"""
        tasks = []
        for provider_name in provider_names:
            task = self.send_notification(provider_name, recipient, message, **kwargs)
            tasks.append((provider_name, task))

        results = {}
        for provider_name, task in tasks:
            try:
                results[provider_name] = await task
            except Exception as e:
                results[provider_name] = {"success": False, "error": str(e)}

        return results

    def get_available_providers(self) -> list[str]:
        """Get list of available provider names"""
        return list(self._providers.keys())

    def set_default_provider(self, provider_name: str):
        """Set default provider"""
        if provider_name in self._providers:
            self._default_provider = provider_name
        else:
            raise ValueError(f"Provider '{provider_name}' not registered")
