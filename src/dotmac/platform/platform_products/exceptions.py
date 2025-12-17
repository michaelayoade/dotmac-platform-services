"""
Platform Products Exceptions.

Custom exceptions for platform product operations.
"""

from typing import Any

from ..core.exceptions import DotMacError


class PlatformProductError(DotMacError):
    """Base exception for platform product errors."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        status_code: int = 400,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code or "PLATFORM_PRODUCT_ERROR",
            details=details,
            status_code=status_code,
            **kwargs,
        )


class ProductNotFoundError(PlatformProductError):
    """Raised when a platform product is not found."""

    def __init__(
        self,
        message: str = "Platform product not found",
        product_id: str | None = None,
        slug: str | None = None,
        **kwargs: Any,
    ) -> None:
        details: dict[str, Any] = {}
        if product_id:
            details["product_id"] = product_id
        if slug:
            details["slug"] = slug

        super().__init__(
            message=message,
            error_code="PRODUCT_NOT_FOUND",
            details=details,
            status_code=404,
            recovery_hint="Check the product ID or slug and try again",
            **kwargs,
        )


class DuplicateProductError(PlatformProductError):
    """Raised when attempting to create a product with a duplicate slug."""

    def __init__(
        self,
        message: str = "A product with this slug already exists",
        slug: str | None = None,
        **kwargs: Any,
    ) -> None:
        details: dict[str, Any] = {}
        if slug:
            details["slug"] = slug

        super().__init__(
            message=message,
            error_code="DUPLICATE_PRODUCT",
            details=details,
            status_code=409,
            recovery_hint="Use a different slug or update the existing product",
            **kwargs,
        )


class InvalidProductDataError(PlatformProductError):
    """Raised when product data validation fails."""

    def __init__(
        self,
        message: str = "Invalid product data",
        field: str | None = None,
        value: Any = None,
        **kwargs: Any,
    ) -> None:
        details: dict[str, Any] = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)

        super().__init__(
            message=message,
            error_code="INVALID_PRODUCT_DATA",
            details=details,
            status_code=400,
            **kwargs,
        )


class TemplateNotFoundError(PlatformProductError):
    """Raised when the referenced deployment template is not found."""

    def __init__(
        self,
        message: str = "Deployment template not found",
        template_id: int | None = None,
        **kwargs: Any,
    ) -> None:
        details: dict[str, Any] = {}
        if template_id:
            details["template_id"] = template_id

        super().__init__(
            message=message,
            error_code="TEMPLATE_NOT_FOUND",
            details=details,
            status_code=400,
            recovery_hint="Provide a valid deployment template ID",
            **kwargs,
        )


class ProductInUseError(PlatformProductError):
    """Raised when attempting to delete a product that is in use."""

    def __init__(
        self,
        message: str = "Product cannot be deleted because it is in use",
        product_id: str | None = None,
        active_subscriptions: int | None = None,
        **kwargs: Any,
    ) -> None:
        details: dict[str, Any] = {}
        if product_id:
            details["product_id"] = product_id
        if active_subscriptions is not None:
            details["active_subscriptions"] = active_subscriptions

        super().__init__(
            message=message,
            error_code="PRODUCT_IN_USE",
            details=details,
            status_code=409,
            recovery_hint="Deactivate the product instead of deleting it",
            **kwargs,
        )
