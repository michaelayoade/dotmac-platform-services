"""Pagination utilities for API responses."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for API requests."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    page: int = Field(1, ge=1, description="Page number (1-based)")
    size: int = Field(20, ge=1, le=100, description="Items per page")

    @property
    def skip(self) -> int:
        """Calculate skip value for database queries."""
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        """Get limit value for database queries."""
        return self.size


class Page(BaseModel, Generic[T]):
    """
    Generic page container for paginated responses.

    Provides consistent pagination metadata across all APIs.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    items: list[T] = Field(..., description="Page items")
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    size: int = Field(..., ge=1, description="Items per page")
    pages: int = Field(..., ge=0, description="Total number of pages")

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        size: int,
    ) -> "Page[T]":
        """
        Create a page with calculated metadata.

        Args:
            items: Page items
            total: Total count of all items
            page: Current page number (1-based)
            size: Items per page

        Returns:
            Page instance with metadata
        """
        pages = (total + size - 1) // size if size > 0 else 0

        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.pages

    @property
    def has_prev(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1

    @property
    def next_page(self) -> int | None:
        """Get next page number."""
        return self.page + 1 if self.has_next else None

    @property
    def prev_page(self) -> int | None:
        """Get previous page number."""
        return self.page - 1 if self.has_prev else None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with metadata."""
        return {
            "items": self.items,
            "metadata": {
                "total": self.total,
                "page": self.page,
                "size": self.size,
                "pages": self.pages,
                "has_next": self.has_next,
                "has_prev": self.has_prev,
                "next_page": self.next_page,
                "prev_page": self.prev_page,
            },
        }


def create_page(
    items: list[T],
    total: int,
    params: PaginationParams,
) -> Page[T]:
    """
    Helper to create a page from pagination parameters.

    Args:
        items: Page items
        total: Total count
        params: Pagination parameters

    Returns:
        Page instance
    """
    return Page.create(
        items=items,
        total=total,
        page=params.page,
        size=params.size,
    )


def get_pagination_bounds(
    params: PaginationParams,
    total: int,
) -> tuple[int, int]:
    """
    Get start and end indices for pagination.

    Args:
        params: Pagination parameters
        total: Total items

    Returns:
        Tuple of (start_index, end_index)
    """
    start = params.skip
    end = min(start + params.limit, total)
    return start, end
