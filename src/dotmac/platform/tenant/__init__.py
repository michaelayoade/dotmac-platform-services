"""
Tenant identity and middleware utilities for DotMac platform.
Also exposes lightweight enums/functions for import-compatibility in tests.
"""

from .config import TenantConfig
from .identity import TenantIdentityResolver
from .middleware import TenantMiddleware

__all__ = [
    "TenantConfig",
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
