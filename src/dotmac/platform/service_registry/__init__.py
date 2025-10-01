"""
Service Registry using HashiCorp Consul.
Provides service registration, deregistration, discovery, and health checking.
"""

from .consul_registry import (
    ConsulServiceInfo,
    deregister_service,
    discover_services,
    get_healthy_services,
    register_service,
)

# Optional HTTP client with service discovery
try:
    from .client import ServiceClient
except ImportError:
    ServiceClient = None

# Backward compatibility exports
from .consul_registry import ConsulServiceRegistry as ServiceRegistry
from .consul_registry import get_consul_registry as get_service_registry
from .models import ServiceHealth, ServiceInfo, ServiceStatus

__all__ = [
    # New Consul-based API
    "register_service",
    "deregister_service",
    "discover_services",
    "get_healthy_services",
    "ConsulServiceInfo",
    # HTTP client with service discovery
    "ServiceClient",
    # Backward compatibility
    "ServiceRegistry",
    "get_service_registry",
    "ServiceInfo",
    "ServiceHealth",
    "ServiceStatus",
]
