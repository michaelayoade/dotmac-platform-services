"""
Platform Products Admin Router.

REST API endpoints for platform product CRUD operations.
These endpoints are platform-level (not tenant-scoped) and require
platform admin permissions.

Routes: /api/platform/v1/products/*
Required Permissions: platform.product.*
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.core import UserInfo, get_current_user
from ..auth.rbac_dependencies import require_permission
from ..db import get_async_session
from .exceptions import (
    DuplicateProductError,
    InvalidProductDataError,
    ProductNotFoundError,
    TemplateNotFoundError,
)
from .schemas import (
    PlatformProductCreate,
    PlatformProductListResponse,
    PlatformProductResponse,
    PlatformProductUpdate,
    ProductFilters,
)
from .service import PlatformProductService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["Platform - Products"])


# =============================================================================
# Dependencies
# =============================================================================


async def get_product_service(
    db: AsyncSession = Depends(get_async_session),
) -> PlatformProductService:
    """Get platform product service instance."""
    return PlatformProductService(db)


# Type aliases for cleaner signatures
ProductServiceDep = Annotated[PlatformProductService, Depends(get_product_service)]
CurrentUserDep = Annotated[UserInfo, Depends(get_current_user)]


# =============================================================================
# Admin CRUD Endpoints
# =============================================================================


@router.post(
    "",
    response_model=PlatformProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Platform Product",
    description="Create a new platform product. Requires platform.product.create permission.",
)
async def create_product(
    data: PlatformProductCreate,
    service: ProductServiceDep,
    current_user: UserInfo = Depends(require_permission("platform.product.create")),
) -> PlatformProductResponse:
    """Create a new platform product."""
    try:
        product = await service.create(data)
        logger.info(
            f"Product created by user {current_user.user_id}: {product.slug}"
        )
        return PlatformProductResponse.model_validate(product)
    except DuplicateProductError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvalidProductDataError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "",
    response_model=PlatformProductListResponse,
    summary="List Platform Products",
    description="List all platform products with optional filters and pagination.",
)
async def list_products(
    service: ProductServiceDep,
    current_user: UserInfo = Depends(require_permission("platform.product.read")),
    is_active: bool | None = Query(None, description="Filter by active status"),
    is_public: bool | None = Query(None, description="Filter by public visibility"),
    template_id: int | None = Query(None, description="Filter by template ID"),
    search: str | None = Query(None, max_length=100, description="Search in name/description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
) -> PlatformProductListResponse:
    """List platform products with filters and pagination."""
    filters = ProductFilters(
        is_active=is_active,
        is_public=is_public,
        template_id=template_id,
        search=search,
    )

    products, total = await service.list(filters=filters, page=page, limit=page_size)
    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return PlatformProductListResponse(
        products=[PlatformProductResponse.model_validate(p) for p in products],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/{product_id}",
    response_model=PlatformProductResponse,
    summary="Get Platform Product by ID",
    description="Retrieve a platform product by its UUID.",
)
async def get_product_by_id(
    product_id: UUID,
    service: ProductServiceDep,
    current_user: UserInfo = Depends(require_permission("platform.product.read")),
) -> PlatformProductResponse:
    """Get a platform product by ID."""
    try:
        product = await service.get_by_id(product_id)
        return PlatformProductResponse.model_validate(product)
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/slug/{slug}",
    response_model=PlatformProductResponse,
    summary="Get Platform Product by Slug",
    description="Retrieve a platform product by its slug.",
)
async def get_product_by_slug(
    slug: str,
    service: ProductServiceDep,
    current_user: UserInfo = Depends(require_permission("platform.product.read")),
) -> PlatformProductResponse:
    """Get a platform product by slug."""
    try:
        product = await service.get_by_slug(slug)
        return PlatformProductResponse.model_validate(product)
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{product_id}",
    response_model=PlatformProductResponse,
    summary="Update Platform Product",
    description="Update a platform product. Supports partial updates.",
)
async def update_product(
    product_id: UUID,
    data: PlatformProductUpdate,
    service: ProductServiceDep,
    current_user: UserInfo = Depends(require_permission("platform.product.update")),
) -> PlatformProductResponse:
    """Update a platform product."""
    try:
        product = await service.update(product_id, data)
        logger.info(
            f"Product updated by user {current_user.user_id}: {product.slug}"
        )
        return PlatformProductResponse.model_validate(product)
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvalidProductDataError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Platform Product",
    description="Soft delete a platform product.",
)
async def delete_product(
    product_id: UUID,
    service: ProductServiceDep,
    current_user: UserInfo = Depends(require_permission("platform.product.delete")),
) -> None:
    """Soft delete a platform product."""
    try:
        await service.delete(product_id)
        logger.info(
            f"Product deleted by user {current_user.user_id}: {product_id}"
        )
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =============================================================================
# Status Management Endpoints
# =============================================================================


@router.post(
    "/{product_id}/activate",
    response_model=PlatformProductResponse,
    summary="Activate Platform Product",
    description="Activate a platform product to make it available for subscription.",
)
async def activate_product(
    product_id: UUID,
    service: ProductServiceDep,
    current_user: UserInfo = Depends(require_permission("platform.product.update")),
) -> PlatformProductResponse:
    """Activate a platform product."""
    try:
        product = await service.activate(product_id)
        logger.info(
            f"Product activated by user {current_user.user_id}: {product.slug}"
        )
        return PlatformProductResponse.model_validate(product)
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{product_id}/deactivate",
    response_model=PlatformProductResponse,
    summary="Deactivate Platform Product",
    description="Deactivate a platform product to remove it from subscription availability.",
)
async def deactivate_product(
    product_id: UUID,
    service: ProductServiceDep,
    current_user: UserInfo = Depends(require_permission("platform.product.update")),
) -> PlatformProductResponse:
    """Deactivate a platform product."""
    try:
        product = await service.deactivate(product_id)
        logger.info(
            f"Product deactivated by user {current_user.user_id}: {product.slug}"
        )
        return PlatformProductResponse.model_validate(product)
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
