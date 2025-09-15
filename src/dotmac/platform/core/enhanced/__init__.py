"""
Enhanced core utilities for DotMac Platform Services.

Provides advanced repository patterns, base schemas, and datetime utilities.
"""

from .base_repository import (
    BaseRepository,
    CreateSchemaType,
    ModelType,
    UpdateSchemaType,
)
from .base_schemas import (
    AuditMixin,
    BaseCreateSchema,
    BaseCreateWithAuditSchema,
    BaseResponseSchema,
    BaseResponseWithAuditSchema,
    BaseSchema,
    BaseTenantCreateSchema,
    BaseTenantResponseSchema,
    BaseTenantUpdateSchema,
    BaseUpdateSchema,
    BaseUpdateWithAuditSchema,
    BulkOperationResponseSchema,
    BulkOperationSchema,
    CommonValidators,
    EntityStatus,
    ErrorResponseSchema,
    FilterParams,
    OperationStatus,
    PaginatedResponseSchema,
    PaginationParams,
    SoftDeleteMixin,
    SortParams,
    SuccessResponseSchema,
    TenantMixin,
    TimestampMixin,
)
from .datetime_utils import (
    DateTimeUtils,
    TimeDeltas,
    format_iso,
    get_common_expiry,
    is_expired,
    parse_iso,
    utc_datetime,
    utc_now,
    utc_timestamp,
)
from .exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
    RepositoryError,
    ValidationError,
)

__all__ = [
    # Repository
    "BaseRepository",
    "ModelType",
    "CreateSchemaType",
    "UpdateSchemaType",
    # Exceptions
    "RepositoryError",
    "EntityNotFoundError",
    "DuplicateEntityError",
    "ValidationError",
    # Schemas
    "BaseSchema",
    "TimestampMixin",
    "AuditMixin",
    "TenantMixin",
    "SoftDeleteMixin",
    "BaseCreateSchema",
    "BaseUpdateSchema",
    "BaseResponseSchema",
    "BaseCreateWithAuditSchema",
    "BaseUpdateWithAuditSchema",
    "BaseResponseWithAuditSchema",
    "BaseTenantCreateSchema",
    "BaseTenantUpdateSchema",
    "BaseTenantResponseSchema",
    "PaginationParams",
    "SortParams",
    "FilterParams",
    "PaginatedResponseSchema",
    "ErrorResponseSchema",
    "SuccessResponseSchema",
    "BulkOperationSchema",
    "BulkOperationResponseSchema",
    "CommonValidators",
    "EntityStatus",
    "OperationStatus",
    # DateTime Utils
    "DateTimeUtils",
    "TimeDeltas",
    "utc_now",
    "utc_datetime",
    "utc_timestamp",
    "format_iso",
    "parse_iso",
    "is_expired",
    "get_common_expiry",
]