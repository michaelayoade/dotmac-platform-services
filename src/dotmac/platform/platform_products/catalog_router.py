"""
Public Product Catalog Router.

Public API endpoints for browsing the product catalog.
These endpoints do NOT require authentication and are suitable
for marketing pages and signup flows.

Routes: /api/v1/catalog/*
Required Permissions: None (public)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_async_session
from .exceptions import ProductNotFoundError
from .schemas import (
    PublicProductListResponse,
    PublicProductResponse,
)
from .service import PlatformProductService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/catalog", tags=["Public Catalog"])


# =============================================================================
# Dependencies
# =============================================================================


async def get_product_service(
    db: AsyncSession = Depends(get_async_session),
) -> PlatformProductService:
    """Get platform product service instance."""
    return PlatformProductService(db)


# =============================================================================
# Public Catalog Endpoints (No Authentication Required)
# =============================================================================


@router.get(
    "/products",
    response_model=PublicProductListResponse,
    summary="List Public Products",
    description="List all publicly available products. No authentication required.",
)
async def list_public_products(
    service: PlatformProductService = Depends(get_product_service),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
) -> PublicProductListResponse:
    """
    List products available in the public catalog.

    Returns only products where:
    - is_active = True
    - is_public = True

    Response includes limited fields suitable for public display.
    Internal configuration details are not exposed.
    """
    products, total = await service.list_public(page=page, limit=page_size)

    return PublicProductListResponse(
        products=[PublicProductResponse.model_validate(p) for p in products],  # type: ignore[attr-defined]
        total=total,
    )


@router.get(
    "/products/{slug}",
    response_model=PublicProductResponse,
    summary="Get Public Product by Slug",
    description="Get a public product by its slug. No authentication required.",
)
async def get_public_product(
    slug: str,
    service: PlatformProductService = Depends(get_product_service),
) -> PublicProductResponse:
    """
    Get a product from the public catalog by slug.

    Returns only if the product is:
    - is_active = True
    - is_public = True

    Response includes limited fields suitable for public display.
    """
    try:
        product = await service.get_public_by_slug(slug)
        return PublicProductResponse.model_validate(product)
    except ProductNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{slug}' not found in public catalog",
        )
