"""
Platform Products Module.

Manages deployable SaaS products in the Dotmac portfolio.
Products are global/platform-level resources (not tenant-scoped).

Components:
- models: SQLAlchemy PlatformProduct model
- schemas: Pydantic request/response schemas
- service: Business logic layer
- router: Admin REST API endpoints (requires platform permissions)
- catalog_router: Public catalog endpoints (no auth required)
- exceptions: Custom exceptions

Example Products:
- Dotmac Insights (Business Management)
- Dotmac Connect (ISP Billing)
- Dotmac Radius (Network Authentication)
"""

from .exceptions import (
    DuplicateProductError,
    InvalidProductDataError,
    PlatformProductError,
    ProductInUseError,
    ProductNotFoundError,
    TemplateNotFoundError,
)
from .models import PlatformProduct
from .schemas import (
    PlatformProductCreate,
    PlatformProductListResponse,
    PlatformProductResponse,
    PlatformProductUpdate,
    ProductFilters,
    PublicProductListResponse,
    PublicProductResponse,
)
from .service import PlatformProductService

__all__ = [
    # Models
    "PlatformProduct",
    # Schemas
    "PlatformProductCreate",
    "PlatformProductUpdate",
    "PlatformProductResponse",
    "PlatformProductListResponse",
    "ProductFilters",
    "PublicProductResponse",
    "PublicProductListResponse",
    # Service
    "PlatformProductService",
    # Exceptions
    "PlatformProductError",
    "ProductNotFoundError",
    "DuplicateProductError",
    "InvalidProductDataError",
    "TemplateNotFoundError",
    "ProductInUseError",
]
