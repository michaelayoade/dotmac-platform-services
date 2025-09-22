"""
Service Registry using HashiCorp Consul.

Replaces 400+ lines of custom service registry code with industry-standard
Consul service discovery and health checking.

Example usage:

    from dotmac.platform.service_registry import register_service, discover_services

    # Register a service
    await register_service("my-api", "127.0.0.1", 8000, health_check="/health")

    # Discover services
    services = await discover_services("my-api")
    for service in services:
        print(f"Service at {service.address}:{service.port}")

Benefits:
- Uses proven HashiCorp Consul
- Built-in health checking and service mesh
- Automatic load balancing and failover
- Web UI and monitoring tools
- Multi-datacenter support
- 90%+ code reduction
"""

from .consul_registry import (
    register_service,
    deregister_service,
    discover_services,
    get_healthy_services,
    ConsulServiceInfo,
)

# Backward compatibility exports
from .consul_registry import ConsulServiceRegistry as ServiceRegistry
from .consul_registry import get_consul_registry as get_service_registry
from .models import ServiceInfo, ServiceHealth, ServiceStatus

__all__ = [
    # New Consul-based API
    "register_service",
    "deregister_service",
    "discover_services",
    "get_healthy_services",
    "ConsulServiceInfo",
    # Backward compatibility
    "ServiceRegistry",
    "get_service_registry",
    "ServiceInfo",
    "ServiceHealth",
    "ServiceStatus",
]