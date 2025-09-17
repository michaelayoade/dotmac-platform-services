"""Service discovery and routing for API Gateway."""

import asyncio
import secrets
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

# Use cryptographically secure random for load balancing
_secure_random = secrets.SystemRandom()

class ServiceStatus(str, Enum):
    """Service health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class RouteStrategy(str, Enum):
    """Routing strategies for load balancing."""

    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED = "weighted"
    HEALTH_BASED = "health_based"
    STICKY_SESSION = "sticky_session"
    RANDOM = "random"
    RESPONSE_TIME = "response_time"

@dataclass
class ServiceInstance:
    """Represents a service instance."""

    instance_id: str
    service_name: str
    host: str
    port: int
    version: str = "1.0.0"
    status: ServiceStatus = ServiceStatus.UNKNOWN
    weight: int = 100  # For weighted routing
    metadata: Dict[str, Any] = field(default_factory=dict)
    health_check_url: Optional[str] = None
    last_health_check: Optional[datetime] = None
    consecutive_failures: int = 0
    response_times: List[float] = field(default_factory=list)
    active_connections: int = 0

    def get_average_response_time(self) -> float:
        """Get average response time for this instance."""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

    def record_response_time(self, response_time: float, max_history: int = 100):
        """Record a response time, maintaining limited history."""
        self.response_times.append(response_time)
        if len(self.response_times) > max_history:
            self.response_times.pop(0)

@dataclass
class ServiceDefinition:
    """Service definition with routing configuration."""

    name: str
    path_prefix: str
    instances: List[ServiceInstance] = field(default_factory=list)
    route_strategy: RouteStrategy = RouteStrategy.HEALTH_BASED
    health_check_interval: int = 30  # seconds
    timeout: int = 10  # seconds
    retry_count: int = 3
    circuit_breaker_threshold: int = 5
    sticky_session_cookie: Optional[str] = None

    def get_healthy_instances(self) -> List[ServiceInstance]:
        """Get list of healthy instances."""
        return [
            i for i in self.instances if i.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]
        ]

class ServiceDiscovery:
    """Service discovery and routing manager."""

    def __init__(self, discovery_interval: int = 30, health_check_interval: int = 15):
        self.services: Dict[str, ServiceDefinition] = {}
        self.discovery_interval = discovery_interval
        self.health_check_interval = health_check_interval
        self.round_robin_counters: Dict[str, int] = {}
        self.session_affinity: Dict[str, str] = {}  # session_id -> instance_id
        self.discovery_sources: List[Any] = []  # External discovery sources
        self._running = False
        self._tasks: Set[asyncio.Task[None]] = set()

    def register_service(self, service: ServiceDefinition):
        """Register a service definition."""
        self.services[service.name] = service
        self.round_robin_counters[service.name] = 0
        logger.info(f"Registered service: {service.name} with {len(service.instances)} instances")

    def register_instance(self, service_name: str, instance: ServiceInstance):
        """Register a service instance."""
        if service_name not in self.services:
            self.services[service_name] = ServiceDefinition(
                name=service_name, path_prefix=f"/{service_name}"
            )

        service = self.services[service_name]
        # Check if instance already exists
        existing = [i for i in service.instances if i.instance_id == instance.instance_id]
        if existing:
            # Update existing instance
            idx = service.instances.index(existing[0])
            service.instances[idx] = instance
        else:
            service.instances.append(instance)

        logger.info(f"Registered instance {instance.instance_id} for service {service_name}")

    def deregister_instance(self, service_name: str, instance_id: str) -> bool:
        """Deregister a service instance."""
        if service_name not in self.services:
            return False

        service = self.services[service_name]
        initial_count = len(service.instances)
        service.instances = [i for i in service.instances if i.instance_id != instance_id]

        if len(service.instances) < initial_count:
            logger.info(f"Deregistered instance {instance_id} from service {service_name}")
            return True
        return False

    async def select_instance(
        self,
        service_name: str,
        session_id: Optional[str] = None,
        request_metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ServiceInstance]:
        """Select a service instance based on routing strategy."""
        if service_name not in self.services:
            return None

        service = self.services[service_name]
        healthy_instances = service.get_healthy_instances()

        if not healthy_instances:
            # Fall back to any instance if no healthy ones
            if service.instances:
                logger.warning(f"No healthy instances for {service_name}, using degraded instance")
                return service.instances[0]
            return None

        # Apply routing strategy
        strategy = service.route_strategy

        if strategy == RouteStrategy.STICKY_SESSION and session_id:
            return self._sticky_session_routing(service_name, session_id, healthy_instances)
        elif strategy == RouteStrategy.ROUND_ROBIN:
            return self._round_robin_routing(service_name, healthy_instances)
        elif strategy == RouteStrategy.LEAST_CONNECTIONS:
            return self._least_connections_routing(healthy_instances)
        elif strategy == RouteStrategy.WEIGHTED:
            return self._weighted_routing(healthy_instances)
        elif strategy == RouteStrategy.RESPONSE_TIME:
            return self._response_time_routing(healthy_instances)
        elif strategy == RouteStrategy.RANDOM:
            return _secure_random.choice(healthy_instances)
        else:  # HEALTH_BASED or default
            return self._health_based_routing(healthy_instances)

    def _sticky_session_routing(
        self, service_name: str, session_id: str, instances: List[ServiceInstance]
    ) -> ServiceInstance:
        """Route based on session affinity."""
        # Check if session already has affinity
        if session_id in self.session_affinity:
            instance_id = self.session_affinity[session_id]
            # Find the instance
            for instance in instances:
                if instance.instance_id == instance_id:
                    return instance

        # No existing affinity or instance not available, select new one
        instance = self._health_based_routing(instances)
        if instance:
            self.session_affinity[session_id] = instance.instance_id
        return instance

    def _round_robin_routing(
        self, service_name: str, instances: List[ServiceInstance]
    ) -> ServiceInstance:
        """Round-robin routing."""
        if service_name not in self.round_robin_counters:
            self.round_robin_counters[service_name] = 0

        counter = self.round_robin_counters[service_name]
        instance = instances[counter % len(instances)]
        self.round_robin_counters[service_name] = counter + 1
        return instance

    def _least_connections_routing(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Route to instance with least active connections."""
        return min(instances, key=lambda x: x.active_connections)

    def _weighted_routing(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Weighted random routing."""
        weights = [i.weight for i in instances]
        return _secure_random.choices(instances, weights=weights)[0]

    def _response_time_routing(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Route to instance with best response time."""
        # Filter instances with response time data
        instances_with_data = [i for i in instances if i.response_times]
        if not instances_with_data:
            return _secure_random.choice(instances)

        return min(instances_with_data, key=lambda x: x.get_average_response_time())

    def _health_based_routing(self, instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """Route based on health status, preferring healthy over degraded."""
        healthy = [i for i in instances if i.status == ServiceStatus.HEALTHY]
        if healthy:
            return _secure_random.choice(healthy)

        # Fall back to degraded instances
        degraded = [i for i in instances if i.status == ServiceStatus.DEGRADED]
        if degraded:
            return _secure_random.choice(degraded)

        # Last resort: any instance
        return _secure_random.choice(instances) if instances else None

    async def perform_health_check(self, instance: ServiceInstance) -> ServiceStatus:
        """Perform health check on a service instance."""
        try:
            # Simulate health check (in real implementation, would make HTTP request)
            # For now, use a simple probability model
            if instance.consecutive_failures >= 3:
                # More likely to stay unhealthy
                if _secure_random.random() > 0.3:
                    instance.consecutive_failures += 1
                    return ServiceStatus.UNHEALTHY
                else:
                    instance.consecutive_failures = 0
                    return ServiceStatus.HEALTHY
            else:
                # Usually healthy
                if _secure_random.random() > 0.95:
                    instance.consecutive_failures += 1
                    return (
                        ServiceStatus.DEGRADED
                        if instance.consecutive_failures < 2
                        else ServiceStatus.UNHEALTHY
                    )
                else:
                    instance.consecutive_failures = 0
                    return ServiceStatus.HEALTHY

        except Exception as e:
            logger.error(f"Health check failed for {instance.instance_id}: {e}")
            instance.consecutive_failures += 1
            return ServiceStatus.UNHEALTHY

    async def _health_check_loop(self):
        """Background task for health checking."""
        while self._running:
            try:
                tasks = []
                for service in self.services.values():
                    for instance in service.instances:
                        # Check if health check is due
                        if (
                            instance.last_health_check is None
                            or (datetime.now(timezone.utc) - instance.last_health_check).seconds
                            > service.health_check_interval
                        ):
                            tasks.append(self._check_instance_health(instance))

                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

                await asyncio.sleep(self.health_check_interval)

            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(self.health_check_interval)

    async def _check_instance_health(self, instance: ServiceInstance):
        """Check health of a single instance."""
        try:
            old_status = instance.status
            instance.status = await self.perform_health_check(instance)
            instance.last_health_check = datetime.now(timezone.utc)

            if old_status != instance.status:
                logger.info(
                    f"Instance {instance.instance_id} status changed from {old_status} to {instance.status}"
                )

        except Exception as e:
            logger.error(f"Failed to check health of {instance.instance_id}: {e}")
            instance.status = ServiceStatus.UNKNOWN

    async def _discovery_loop(self):
        """Background task for service discovery."""
        while self._running:
            try:
                # In a real implementation, this would query external discovery sources
                # For now, just log current state
                total_instances = sum(len(s.instances) for s in self.services.values())
                healthy_instances = sum(
                    len([i for i in s.instances if i.status == ServiceStatus.HEALTHY])
                    for s in self.services.values()
                )

                logger.info(
                    f"Service discovery: {len(self.services)} services, "
                    f"{total_instances} total instances, {healthy_instances} healthy"
                )

                await asyncio.sleep(self.discovery_interval)

            except Exception as e:
                logger.error(f"Discovery loop error: {e}")
                await asyncio.sleep(self.discovery_interval)

    async def start(self):
        """Start background tasks."""
        if self._running:
            return

        self._running = True
        self._tasks.add(asyncio.create_task(self._health_check_loop()))
        self._tasks.add(asyncio.create_task(self._discovery_loop()))
        logger.info("Service discovery started")

    async def stop(self):
        """Stop background tasks."""
        self._running = False

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("Service discovery stopped")

    def get_service_status(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Get status of services."""
        if service_name:
            if service_name not in self.services:
                return {"error": f"Service {service_name} not found"}

            service = self.services[service_name]
            return {
                "name": service.name,
                "total_instances": len(service.instances),
                "healthy_instances": len(
                    [i for i in service.instances if i.status == ServiceStatus.HEALTHY]
                ),
                "degraded_instances": len(
                    [i for i in service.instances if i.status == ServiceStatus.DEGRADED]
                ),
                "unhealthy_instances": len(
                    [i for i in service.instances if i.status == ServiceStatus.UNHEALTHY]
                ),
                "route_strategy": service.route_strategy,
                "instances": [
                    {
                        "id": i.instance_id,
                        "host": i.host,
                        "port": i.port,
                        "status": i.status,
                        "active_connections": i.active_connections,
                        "avg_response_time": i.get_average_response_time(),
                    }
                    for i in service.instances
                ],
            }

        # Return all services status
        return {
            "total_services": len(self.services),
            "services": [
                {
                    "name": s.name,
                    "instances": len(s.instances),
                    "healthy": len([i for i in s.instances if i.status == ServiceStatus.HEALTHY]),
                }
                for s in self.services.values()
            ],
        }
