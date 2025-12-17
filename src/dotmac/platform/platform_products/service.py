"""
Platform Products Service Layer.

Business logic for platform product CRUD operations.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..deployment.models import DeploymentTemplate
from .exceptions import (
    DuplicateProductError,
    InvalidProductDataError,
    ProductNotFoundError,
    TemplateNotFoundError,
)
from .models import PlatformProduct
from .schemas import (
    PlatformProductCreate,
    PlatformProductUpdate,
    ProductFilters,
)

logger = logging.getLogger(__name__)


class PlatformProductService:
    """Service for managing platform products."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the service with a database session."""
        self.db = db

    async def create(self, data: PlatformProductCreate) -> PlatformProduct:
        """
        Create a new platform product.

        Args:
            data: Product creation data

        Returns:
            Created PlatformProduct

        Raises:
            DuplicateProductError: If slug already exists
            TemplateNotFoundError: If template_id is invalid
            InvalidProductDataError: If validation fails
        """
        # Validate template exists
        template = await self.db.get(DeploymentTemplate, data.template_id)
        if not template:
            raise TemplateNotFoundError(
                message=f"Deployment template with ID {data.template_id} not found",
                template_id=data.template_id,
            )

        # Validate default_modules is subset of available_modules
        if data.default_modules:
            invalid_modules = set(data.default_modules) - set(data.available_modules)
            if invalid_modules:
                raise InvalidProductDataError(
                    message=f"Default modules must be a subset of available modules. "
                    f"Invalid: {invalid_modules}",
                    field="default_modules",
                    value=list(invalid_modules),
                )

        # Check for duplicate slug
        existing = await self._get_by_slug(data.slug)
        if existing:
            raise DuplicateProductError(
                message=f"A product with slug '{data.slug}' already exists",
                slug=data.slug,
            )

        # Create the product
        product = PlatformProduct(
            slug=data.slug.lower(),
            name=data.name,
            template_id=data.template_id,
            description=data.description,
            short_description=data.short_description,
            docker_image=data.docker_image,
            helm_chart_url=data.helm_chart_url,
            helm_chart_version=data.helm_chart_version,
            docker_compose_template=data.docker_compose_template,
            default_resources=data.default_resources,
            required_services=data.required_services,
            available_modules=data.available_modules,
            default_modules=data.default_modules,
            health_check_path=data.health_check_path,
            metrics_path=data.metrics_path,
            icon_url=data.icon_url,
            logo_url=data.logo_url,
            documentation_url=data.documentation_url,
            is_active=data.is_active,
            is_public=data.is_public,
            current_version=data.current_version,
            min_supported_version=data.min_supported_version,
            product_metadata=data.product_metadata,
        )

        try:
            self.db.add(product)
            await self.db.commit()
            await self.db.refresh(product)
            logger.info(f"Created platform product: {product.slug} (ID: {product.id})")
            return product
        except IntegrityError as e:
            await self.db.rollback()
            if "slug" in str(e).lower():
                raise DuplicateProductError(
                    message=f"A product with slug '{data.slug}' already exists",
                    slug=data.slug,
                )
            raise

    async def get_by_id(self, product_id: UUID | str) -> PlatformProduct:
        """
        Get a product by ID.

        Args:
            product_id: Product UUID

        Returns:
            PlatformProduct

        Raises:
            ProductNotFoundError: If product not found
        """
        product_id_str = str(product_id)
        result = await self.db.execute(
            select(PlatformProduct).where(
                PlatformProduct.id == product_id_str,
                PlatformProduct.deleted_at.is_(None),
            )
        )
        product = result.scalar_one_or_none()

        if not product:
            raise ProductNotFoundError(
                message=f"Platform product with ID '{product_id}' not found",
                product_id=product_id_str,
            )
        return product

    async def get_by_slug(self, slug: str) -> PlatformProduct:
        """
        Get a product by slug.

        Args:
            slug: Product slug

        Returns:
            PlatformProduct

        Raises:
            ProductNotFoundError: If product not found
        """
        product = await self._get_by_slug(slug)
        if not product:
            raise ProductNotFoundError(
                message=f"Platform product with slug '{slug}' not found",
                slug=slug,
            )
        return product

    async def _get_by_slug(self, slug: str) -> PlatformProduct | None:
        """Internal helper to get product by slug (returns None if not found)."""
        result = await self.db.execute(
            select(PlatformProduct).where(
                PlatformProduct.slug == slug.lower(),
                PlatformProduct.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        filters: ProductFilters | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[PlatformProduct], int]:
        """
        List products with optional filters and pagination.

        Args:
            filters: Optional filter criteria
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Tuple of (products list, total count)
        """
        query = select(PlatformProduct).where(PlatformProduct.deleted_at.is_(None))

        # Apply filters
        if filters:
            if filters.is_active is not None:
                query = query.where(PlatformProduct.is_active == filters.is_active)  # type: ignore[attr-defined]
            if filters.is_public is not None:
                query = query.where(PlatformProduct.is_public == filters.is_public)
            if filters.template_id is not None:
                query = query.where(PlatformProduct.template_id == filters.template_id)
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.where(
                    or_(
                        PlatformProduct.name.ilike(search_term),
                        PlatformProduct.description.ilike(search_term),
                        PlatformProduct.slug.ilike(search_term),
                    )
                )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * limit
        query = query.order_by(PlatformProduct.name).offset(offset).limit(limit)

        result = await self.db.execute(query)
        products = list(result.scalars().all())

        return products, total

    async def list_public(  # noqa: A003
        self, page: int = 1, limit: int = 50
    ) -> "tuple[list[PlatformProduct], int]":  # type: ignore[valid-type]
        """
        List public products (for catalog).

        Only returns products where is_active=True and is_public=True.

        Args:
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Tuple of (products list, total count)
        """
        return await self.list(
            filters=ProductFilters(is_active=True, is_public=True),
            page=page,
            limit=limit,
        )

    async def get_public_by_slug(self, slug: str) -> PlatformProduct:
        """
        Get a public product by slug.

        Only returns if is_active=True and is_public=True.

        Args:
            slug: Product slug

        Returns:
            PlatformProduct

        Raises:
            ProductNotFoundError: If product not found or not public
        """
        result = await self.db.execute(
            select(PlatformProduct).where(
                PlatformProduct.slug == slug.lower(),
                PlatformProduct.is_active == True,  # type: ignore[attr-defined]  # noqa: E712
                PlatformProduct.is_public == True,  # noqa: E712
                PlatformProduct.deleted_at.is_(None),
            )
        )
        product = result.scalar_one_or_none()

        if not product:
            raise ProductNotFoundError(
                message=f"Public product with slug '{slug}' not found",
                slug=slug,
            )
        return product

    async def update(
        self, product_id: UUID | str, data: PlatformProductUpdate
    ) -> PlatformProduct:
        """
        Update a platform product.

        Args:
            product_id: Product UUID
            data: Update data (partial)

        Returns:
            Updated PlatformProduct

        Raises:
            ProductNotFoundError: If product not found
            TemplateNotFoundError: If new template_id is invalid
            InvalidProductDataError: If validation fails
        """
        product = await self.get_by_id(product_id)

        # Get update data (only set fields)
        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            return product  # Nothing to update

        # Validate template if being updated
        if "template_id" in update_data:
            template = await self.db.get(DeploymentTemplate, update_data["template_id"])
            if not template:
                raise TemplateNotFoundError(
                    message=f"Deployment template with ID {update_data['template_id']} not found",
                    template_id=update_data["template_id"],
                )

        # Validate default_modules if being updated
        if "default_modules" in update_data:
            available = update_data.get("available_modules", product.available_modules)
            invalid_modules = set(update_data["default_modules"]) - set(available)
            if invalid_modules:
                raise InvalidProductDataError(
                    message=f"Default modules must be a subset of available modules. "
                    f"Invalid: {invalid_modules}",
                    field="default_modules",
                    value=list(invalid_modules),
                )

        # Apply updates
        for key, value in update_data.items():
            setattr(product, key, value)

        await self.db.commit()
        await self.db.refresh(product)
        logger.info(f"Updated platform product: {product.slug} (ID: {product.id})")
        return product

    async def delete(self, product_id: UUID | str) -> None:
        """
        Soft delete a platform product.

        Args:
            product_id: Product UUID

        Raises:
            ProductNotFoundError: If product not found
        """
        product = await self.get_by_id(product_id)

        # Soft delete
        product.deleted_at = datetime.now(UTC)
        product.is_active = False  # type: ignore[attr-defined]

        await self.db.commit()
        logger.info(f"Soft deleted platform product: {product.slug} (ID: {product.id})")

    async def activate(self, product_id: UUID | str) -> PlatformProduct:
        """
        Activate a platform product.

        Args:
            product_id: Product UUID

        Returns:
            Updated PlatformProduct

        Raises:
            ProductNotFoundError: If product not found
        """
        product = await self.get_by_id(product_id)
        product.is_active = True  # type: ignore[attr-defined]
        await self.db.commit()
        await self.db.refresh(product)
        logger.info(f"Activated platform product: {product.slug}")
        return product

    async def deactivate(self, product_id: UUID | str) -> PlatformProduct:
        """
        Deactivate a platform product.

        Args:
            product_id: Product UUID

        Returns:
            Updated PlatformProduct

        Raises:
            ProductNotFoundError: If product not found
        """
        product = await self.get_by_id(product_id)
        product.is_active = False  # type: ignore[attr-defined]
        await self.db.commit()
        await self.db.refresh(product)
        logger.info(f"Deactivated platform product: {product.slug}")
        return product
