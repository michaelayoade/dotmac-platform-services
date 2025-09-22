"""
Simple service discovery using Consul + httpx - no bloat.

Replace 900 lines of service mesh with ~100 lines using Consul directly.
"""

import asyncio
import random
from typing import List, Dict, Any, Optional

import consul.aio
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from dotmac.platform.settings import settings
from dotmac.platform.logging import get_logger

logger = get_logger(__name__)

# Global Consul client
_consul_client: Optional[consul.aio.Consul] = None


async def get_consul_client() -> consul.aio.Consul:
    """Get Consul client for service discovery."""
    global _consul_client
    if _consul_client is None:
        _consul_client = consul.aio.Consul(
            host=settings.consul.host if hasattr(settings, 'consul') else 'localhost',
            port=settings.consul.port if hasattr(settings, 'consul') else 8500
        )
    return _consul_client


class ServiceClient:
    """Simple HTTP client with service discovery and retry."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self._client = httpx.AsyncClient()

    async def _get_service_url(self) -> str:
        """Get healthy service instance URL."""
        consul_client = await get_consul_client()

        # Get healthy services
        _, services = await consul_client.health.service(
            self.service_name,
            passing=True
        )

        if not services:
            raise ConnectionError(f"No healthy instances for service: {self.service_name}")

        # Simple random load balancing
        service = random.choice(services)
        host = service['Service']['Address']
        port = service['Service']['Port']

        return f"http://{host}:{port}"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def get(self, path: str, **kwargs) -> httpx.Response:
        """GET request with service discovery and retry."""
        base_url = await self._get_service_url()
        url = f"{base_url}{path}"

        logger.debug("Service request", service=self.service_name, url=url)
        response = await self._client.get(url, **kwargs)
        response.raise_for_status()
        return response

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def post(self, path: str, **kwargs) -> httpx.Response:
        """POST request with service discovery and retry."""
        base_url = await self._get_service_url()
        url = f"{base_url}{path}"

        logger.debug("Service request", service=self.service_name, url=url)
        response = await self._client.post(url, **kwargs)
        response.raise_for_status()
        return response

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()


async def register_service(
    name: str,
    port: int,
    host: str = "localhost",
    health_check_url: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> None:
    """Register service with Consul."""
    consul_client = await get_consul_client()

    service_def = {
        'name': name,
        'service_id': f"{name}-{host}-{port}",
        'address': host,
        'port': port,
        'tags': tags or []
    }

    if health_check_url:
        service_def['check'] = {
            'http': f"http://{host}:{port}{health_check_url}",
            'interval': '10s',
            'timeout': '5s'
        }

    await consul_client.agent.service.register(**service_def)
    logger.info("Service registered", name=name, host=host, port=port)


async def deregister_service(name: str, host: str = "localhost", port: int = 8000) -> None:
    """Deregister service from Consul."""
    consul_client = await get_consul_client()
    service_id = f"{name}-{host}-{port}"

    await consul_client.agent.service.deregister(service_id)
    logger.info("Service deregistered", service_id=service_id)


# Usage examples:
#
# # Register your service
# await register_service(
#     name="user-service",
#     port=8001,
#     health_check_url="/health",
#     tags=["api", "v1"]
# )
#
# # Call another service
# client = ServiceClient("auth-service")
# response = await client.get("/api/verify-token", params={"token": "..."})
# user_data = response.json()
#
# # For even simpler cases, use consul-python + httpx directly:
# import consul.aio
# import httpx
#
# consul_client = consul.aio.Consul()
# _, services = await consul_client.health.service("my-service", passing=True)
# service_url = f"http://{services[0]['Service']['Address']}:{services[0]['Service']['Port']}"
#
# async with httpx.AsyncClient() as client:
#     response = await client.get(f"{service_url}/api/data")