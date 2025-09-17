"""
Service Registry implementation for microservices discovery.

Provides service registration, discovery, health checking, and load balancing.
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

import redis.asyncio as redis
from pydantic import BaseModel, Field

from dotmac.platform.core.decorators import standard_exception_handler
from dotmac.platform.observability.unified_logging import get_logger

from .models import ServiceHealth, ServiceInfo, ServiceStatus

logger = get_logger(__name__)


class ServiceRegistry:
    """
    Centralized service registry for microservices.

    Features:
    - Service registration with TTL
    - Service discovery by name/tags
    - Health check aggregation
    - Load balancing support
    - Circuit breaker integration
    """

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        namespace: str = "service_registry",
        ttl_seconds: int = 60,
    ):
        """Initialize service registry."""
        self.redis = redis_client
        self.namespace = namespace
        self.ttl_seconds = ttl_seconds
        self._local_cache: dict[str, ServiceInfo] = {}
        self._health_check_tasks: dict[str, asyncio.Task] = {}

    async def connect(self, redis_url: str = "redis://localhost:6379/0"):
        """Connect to Redis if not already connected."""
        if not self.redis:
            self.redis = redis.from_url(redis_url)
            await self.redis.ping()
            logger.info("Service registry connected to Redis")

    @standard_exception_handler
    async def register_service(
        self,
        name: str,
        version: str,
        host: str,
        port: int,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        health_check_url: Optional[str] = None,
    ) -> ServiceInfo:
        """Register a service in the registry."""
        service_id = str(uuid4())

        service = ServiceInfo(
            id=service_id,
            name=name,
            version=version,
            host=host,
            port=port,
            tags=tags or [],
            metadata=metadata or {},
            health_check_url=health_check_url or f"http://{host}:{port}/health",
            status=ServiceStatus.HEALTHY,
            registered_at=datetime.now(timezone.utc),
            last_heartbeat=datetime.now(timezone.utc),
        )

        # Store in Redis with TTL
        key = f"{self.namespace}:service:{service_id}"
        await self.redis.setex(
            key,
            self.ttl_seconds,
            service.model_dump_json(),
        )

        # Add to service name index
        await self.redis.sadd(f"{self.namespace}:services:{name}", service_id)

        # Add to tags index
        for tag in service.tags:
            await self.redis.sadd(f"{self.namespace}:tag:{tag}", service_id)

        # Update local cache
        self._local_cache[service_id] = service

        # Start health check task
        if health_check_url:
            self._health_check_tasks[service_id] = asyncio.create_task(
                self._monitor_service_health(service_id)
            )

        logger.info(f"Registered service: {name} ({service_id}) at {host}:{port}")
        return service

    @standard_exception_handler
    async def deregister_service(self, service_id: str) -> bool:
        """Deregister a service from the registry."""
        # Get service info first
        service = await self.get_service(service_id)
        if not service:
            return False

        # Remove from Redis
        key = f"{self.namespace}:service:{service_id}"
        await self.redis.delete(key)

        # Remove from indices
        await self.redis.srem(f"{self.namespace}:services:{service.name}", service_id)
        for tag in service.tags:
            await self.redis.srem(f"{self.namespace}:tag:{tag}", service_id)

        # Cancel health check task
        if service_id in self._health_check_tasks:
            self._health_check_tasks[service_id].cancel()
            del self._health_check_tasks[service_id]

        # Remove from local cache
        self._local_cache.pop(service_id, None)

        logger.info(f"Deregistered service: {service.name} ({service_id})")
        return True

    @standard_exception_handler
    async def get_service(self, service_id: str) -> Optional[ServiceInfo]:
        """Get service info by ID."""
        # Check local cache first
        if service_id in self._local_cache:
            return self._local_cache[service_id]

        # Fetch from Redis
        key = f"{self.namespace}:service:{service_id}"
        data = await self.redis.get(key)

        if data:
            service = ServiceInfo.model_validate_json(data)
            self._local_cache[service_id] = service
            return service

        return None

    @standard_exception_handler
    async def discover_services(
        self,
        name: Optional[str] = None,
        tags: Optional[list[str]] = None,
        status: Optional[ServiceStatus] = None,
    ) -> list[ServiceInfo]:
        """Discover services by name, tags, or status."""
        service_ids = set()

        if name:
            # Get services by name
            ids = await self.redis.smembers(f"{self.namespace}:services:{name}")
            service_ids.update(ids)

        if tags:
            # Get services by tags (intersection)
            tag_sets = []
            for tag in tags:
                tag_ids = await self.redis.smembers(f"{self.namespace}:tag:{tag}")
                tag_sets.append(tag_ids)

            if tag_sets:
                service_ids = service_ids.intersection(*tag_sets) if service_ids else set.intersection(*tag_sets)

        if not name and not tags:
            # Get all services
            pattern = f"{self.namespace}:service:*"
            keys = await self.redis.keys(pattern)
            service_ids = {key.decode().split(":")[-1] for key in keys}

        # Fetch service info
        services = []
        for service_id in service_ids:
            service = await self.get_service(service_id.decode() if isinstance(service_id, bytes) else service_id)
            if service:
                if status is None or service.status == status:
                    services.append(service)

        return services

    @standard_exception_handler
    async def update_heartbeat(self, service_id: str) -> bool:
        """Update service heartbeat timestamp."""
        service = await self.get_service(service_id)
        if not service:
            return False

        service.last_heartbeat = datetime.now(timezone.utc)

        # Update in Redis with renewed TTL
        key = f"{self.namespace}:service:{service_id}"
        await self.redis.setex(
            key,
            self.ttl_seconds,
            service.model_dump_json(),
        )

        # Update local cache
        self._local_cache[service_id] = service

        return True

    @standard_exception_handler
    async def update_service_status(
        self,
        service_id: str,
        status: ServiceStatus,
        health: Optional[ServiceHealth] = None,
    ) -> bool:
        """Update service status and health info."""
        service = await self.get_service(service_id)
        if not service:
            return False

        service.status = status
        if health:
            service.health = health

        # Update in Redis
        key = f"{self.namespace}:service:{service_id}"
        await self.redis.setex(
            key,
            self.ttl_seconds,
            service.model_dump_json(),
        )

        # Update local cache
        self._local_cache[service_id] = service

        logger.debug(f"Updated service status: {service.name} ({service_id}) -> {status}")
        return True

    async def _monitor_service_health(self, service_id: str):
        """Monitor service health in background."""
        import aiohttp

        while True:
            try:
                service = await self.get_service(service_id)
                if not service:
                    break

                # Perform health check
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(
                            service.health_check_url,
                            timeout=aiohttp.ClientTimeout(total=5),
                        ) as response:
                            if response.status == 200:
                                health_data = await response.json()
                                health = ServiceHealth(
                                    status="healthy",
                                    latency_ms=response.headers.get("X-Response-Time", 0),
                                    details=health_data,
                                )
                                await self.update_service_status(
                                    service_id,
                                    ServiceStatus.HEALTHY,
                                    health,
                                )
                            else:
                                await self.update_service_status(
                                    service_id,
                                    ServiceStatus.UNHEALTHY,
                                )
                    except Exception as e:
                        logger.warning(f"Health check failed for {service.name}: {e}")
                        await self.update_service_status(
                            service_id,
                            ServiceStatus.UNHEALTHY,
                        )

                # Wait before next check
                await asyncio.sleep(30)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitor for {service_id}: {e}")
                await asyncio.sleep(30)

    @standard_exception_handler
    async def get_healthy_service(self, name: str) -> Optional[ServiceInfo]:
        """Get a healthy service instance for load balancing."""
        services = await self.discover_services(name=name, status=ServiceStatus.HEALTHY)

        if not services:
            return None

        # Simple round-robin selection
        # Could be enhanced with weighted selection based on load
        import random
        return random.choice(services)

    @standard_exception_handler
    async def get_service_metrics(self) -> dict[str, Any]:
        """Get registry metrics."""
        all_services = await self.discover_services()

        healthy = sum(1 for s in all_services if s.status == ServiceStatus.HEALTHY)
        unhealthy = sum(1 for s in all_services if s.status == ServiceStatus.UNHEALTHY)
        degraded = sum(1 for s in all_services if s.status == ServiceStatus.DEGRADED)

        # Group by service name
        by_name = {}
        for service in all_services:
            if service.name not in by_name:
                by_name[service.name] = []
            by_name[service.name].append(service)

        return {
            "total_services": len(all_services),
            "healthy": healthy,
            "unhealthy": unhealthy,
            "degraded": degraded,
            "services_by_name": {
                name: {
                    "count": len(services),
                    "healthy": sum(1 for s in services if s.status == ServiceStatus.HEALTHY),
                }
                for name, services in by_name.items()
            },
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    async def cleanup(self):
        """Cleanup resources."""
        # Cancel all health check tasks
        for task in self._health_check_tasks.values():
            task.cancel()

        self._health_check_tasks.clear()

        if self.redis:
            await self.redis.close()


# Global registry instance
_registry: Optional[ServiceRegistry] = None


async def get_service_registry() -> ServiceRegistry:
    """Get global service registry instance."""
    global _registry

    if _registry is None:
        _registry = ServiceRegistry()
        await _registry.connect()

    return _registry