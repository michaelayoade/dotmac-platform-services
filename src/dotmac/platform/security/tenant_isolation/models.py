"""
Tenant isolation models and data structures.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TenantStatus(Enum):
    """Tenant status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TRIAL = "trial"


@dataclass
class TenantContext:
    """Tenant context extracted from request."""

    tenant_id: str
    source: str  # gateway_header, container_context, jwt_token, subdomain
    validated: bool = False
    gateway_validated: bool = False


@dataclass
class TenantInfo:
    """Tenant information from database."""

    tenant_id: str
    name: str
    status: TenantStatus
    plan: Optional[str] = None
    created_at: Optional[str] = None
    features: set[str] = None

    def __post_init__(self):
        if self.features is None:
            self.features = set()
