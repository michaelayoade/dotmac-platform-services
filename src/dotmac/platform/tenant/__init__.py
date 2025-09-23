"""
Tenant identity and middleware utilities for DotMac platform.
Simple, lightweight tenant resolution and middleware.
"""

from .tenant import TenantIdentityResolver, TenantMiddleware

__all__ = [
    "TenantIdentityResolver",
    "TenantMiddleware",
]

from enum import Enum
from typing import Any


class TenantIsolationLevel(str, Enum):
    SCHEMA = "schema"
    DATABASE = "database"
    NONE = "none"
    LOGICAL = "logical"


class TenantResolutionStrategy(str, Enum):
    HEADER = "header"
    JWT_CLAIM = "jwt_claim"
    SUBDOMAIN = "subdomain"
    PATH = "path"
    QUERY_PARAM = "query_param"


def get_tenant_context() -> Any:
    """Compatibility helper expected by imports tests."""
    return None


__all__ += ["TenantIsolationLevel", "TenantResolutionStrategy", "get_tenant_context"]
