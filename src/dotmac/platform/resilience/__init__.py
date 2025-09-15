"""
Service Mesh Module

Provides comprehensive service-to-service communication management for the
DotMac framework including service discovery, load balancing, circuit breakers,
and observability.
"""

from .service_mesh import (
    CircuitBreakerState,
    EncryptionLevel,
    LoadBalancer,
    RetryPolicy,
    ServiceCall,
    ServiceEndpoint,
    ServiceMesh,
    ServiceMeshFactory,
    ServiceRegistry,
    TrafficPolicy,
    TrafficRule,
    setup_service_mesh_for_consolidated_services,
)

__all__ = [
    "ServiceMesh",
    "ServiceMeshFactory",
    "ServiceEndpoint",
    "TrafficRule",
    "TrafficPolicy",
    "RetryPolicy",
    "EncryptionLevel",
    "LoadBalancer",
    "ServiceRegistry",
    "CircuitBreakerState",
    "ServiceCall",
    "setup_service_mesh_for_consolidated_services",
]
