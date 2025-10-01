"""
Data mappers for customer management.

Transforms between database models, API schemas, and import formats.
Reusable by import scripts, tests, and API endpoints.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict

from dotmac.platform.customer_management.models import (
    Customer,
    CustomerStatus,
    CustomerType,
    CustomerTier,
    CommunicationChannel
)


class CustomerImportSchema(BaseModel):
    """Schema for importing customer data from CSV/JSON."""

    # Required fields
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=255)

    # Optional identification
    customer_number: Optional[str] = Field(None, max_length=50)
    external_id: Optional[str] = Field(None, max_length=100)

    # Optional name fields
    middle_name: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    company_name: Optional[str] = Field(None, max_length=200)

    # Account information
    status: Optional[CustomerStatus] = CustomerStatus.PROSPECT
    customer_type: Optional[CustomerType] = CustomerType.INDIVIDUAL
    tier: Optional[CustomerTier] = CustomerTier.FREE

    # Contact information
    phone: Optional[str] = Field(None, max_length=30)
    mobile: Optional[str] = Field(None, max_length=30)

    # Address (accepts both snake_case and camelCase)
    address_line1: Optional[str] = Field(None, max_length=200, alias="addressLine1")
    address_line2: Optional[str] = Field(None, max_length=200, alias="addressLine2")
    city: Optional[str] = Field(None, max_length=100)
    state_province: Optional[str] = Field(None, max_length=100, alias="stateProvince")
    postal_code: Optional[str] = Field(None, max_length=20, alias="postalCode")
    country: Optional[str] = Field(None, max_length=2)  # ISO 3166-1 alpha-2

    # Business information
    tax_id: Optional[str] = Field(None, max_length=50, alias="taxId")
    vat_number: Optional[str] = Field(None, max_length=50, alias="vatNumber")
    industry: Optional[str] = Field(None, max_length=100)
    employee_count: Optional[int] = Field(None, ge=0)
    annual_revenue: Optional[float] = Field(None, ge=0)

    # Communication preferences
    preferred_channel: Optional[CommunicationChannel] = CommunicationChannel.EMAIL
    preferred_language: Optional[str] = Field(default="en", max_length=10)
    timezone: Optional[str] = Field(default="UTC", max_length=50)
    opt_in_marketing: Optional[bool] = False
    opt_in_updates: Optional[bool] = True

    # Metrics (for existing customers)
    lifetime_value: Optional[float] = Field(default=0, ge=0)
    total_purchases: Optional[int] = Field(default=0, ge=0)
    average_order_value: Optional[float] = Field(default=0, ge=0)

    # Custom fields and tags
    tags: Optional[List[str]] = Field(default_factory=list)
    custom_fields: Optional[Dict[str, Any]] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    # Import metadata
    source_system: Optional[str] = Field(None, max_length=50)
    import_batch_id: Optional[str] = Field(None, max_length=100)

    model_config = ConfigDict(
        populate_by_name=True,  # Allow both snake_case and camelCase field names
        str_strip_whitespace=True,
        validate_assignment=True
    )

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation."""
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()

    @field_validator('country')
    @classmethod
    def validate_country(cls, v: Optional[str]) -> Optional[str]:
        """Validate country code."""
        if v and len(v) != 2:
            raise ValueError('Country must be 2-letter ISO code')
        return v.upper() if v else None


class CustomerExportSchema(BaseModel):
    """Schema for exporting customer data to frontend format."""

    id: str
    customer_number: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    display_name: Optional[str] = None
    company_name: Optional[str] = None

    # Status and type
    status: str
    customer_type: str
    tier: str

    # Contact
    email: str
    phone: Optional[str] = None
    mobile: Optional[str] = None

    # Address (using snake_case to match frontend)
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    # Business
    tax_id: Optional[str] = None
    vat_number: Optional[str] = None

    # Metrics
    lifetime_value: float = 0
    total_purchases: int = 0
    average_order_value: float = 0
    last_purchase_date: Optional[datetime] = None
    first_purchase_date: Optional[datetime] = None

    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            UUID: str,
            Decimal: float
        }
    )


class CustomerMapper:
    """Maps between different customer data formats."""

    @staticmethod
    def from_import_to_model(
        import_data: CustomerImportSchema,
        tenant_id: str,
        generate_customer_number: bool = True
    ) -> Dict[str, Any]:
        """
        Convert import schema to database model format.

        Args:
            import_data: Validated import data
            tenant_id: Tenant identifier
            generate_customer_number: Whether to auto-generate customer number

        Returns:
            Dictionary ready for Customer model creation
        """
        from uuid import uuid4

        data = {
            "tenant_id": tenant_id,
            "first_name": import_data.first_name,
            "last_name": import_data.last_name,
            "email": import_data.email,
            "status": import_data.status,
            "customer_type": import_data.customer_type,
            "tier": import_data.tier,
            "preferred_channel": import_data.preferred_channel,
            "preferred_language": import_data.preferred_language,
            "timezone": import_data.timezone,
            "opt_in_marketing": import_data.opt_in_marketing,
            "opt_in_updates": import_data.opt_in_updates,
            "tags": import_data.tags or [],
            "custom_fields": import_data.custom_fields or {},
            "metadata_": import_data.metadata or {}
        }

        # Generate customer number if needed
        if generate_customer_number and not import_data.customer_number:
            data["customer_number"] = f"CUST-{uuid4().hex[:8].upper()}"
        elif import_data.customer_number:
            data["customer_number"] = import_data.customer_number

        # Map optional fields
        optional_fields = [
            "external_id", "middle_name", "display_name", "company_name",
            "phone", "mobile", "address_line1", "address_line2",
            "city", "state_province", "postal_code", "country",
            "tax_id", "vat_number", "industry", "employee_count",
            "source_system"
        ]

        for field in optional_fields:
            value = getattr(import_data, field, None)
            if value is not None:
                data[field] = value

        # Convert numeric fields
        if import_data.annual_revenue is not None:
            data["annual_revenue"] = Decimal(str(import_data.annual_revenue))

        if import_data.lifetime_value is not None:
            data["lifetime_value"] = Decimal(str(import_data.lifetime_value))

        if import_data.average_order_value is not None:
            data["average_order_value"] = Decimal(str(import_data.average_order_value))

        if import_data.total_purchases is not None:
            data["total_purchases"] = import_data.total_purchases

        # Add import metadata
        if import_data.import_batch_id:
            data["metadata_"]["import_batch_id"] = import_data.import_batch_id
            data["metadata_"]["imported_at"] = datetime.utcnow().isoformat()

        return data

    @staticmethod
    def from_model_to_export(customer: Customer) -> CustomerExportSchema:
        """
        Convert database model to export schema.

        Args:
            customer: Customer model instance

        Returns:
            CustomerExportSchema ready for JSON serialization
        """
        return CustomerExportSchema(
            id=str(customer.id),
            customer_number=customer.customer_number,
            first_name=customer.first_name,
            last_name=customer.last_name,
            middle_name=customer.middle_name,
            display_name=customer.display_name,
            company_name=customer.company_name,
            status=customer.status.value if customer.status else "prospect",
            customer_type=customer.customer_type.value if customer.customer_type else "individual",
            tier=customer.tier.value if customer.tier else "free",
            email=customer.email,
            phone=customer.phone,
            mobile=customer.mobile,
            address_line_1=customer.address_line1,
            address_line_2=customer.address_line2,
            city=customer.city,
            state_province=customer.state_province,
            postal_code=customer.postal_code,
            country=customer.country,
            tax_id=customer.tax_id,
            vat_number=customer.vat_number,
            lifetime_value=float(customer.lifetime_value),
            total_purchases=customer.total_purchases,
            average_order_value=float(customer.average_order_value),
            last_purchase_date=customer.last_purchase_date,
            first_purchase_date=customer.first_purchase_date,
            tags=customer.tags or [],
            metadata=customer.metadata_ or {},
            custom_fields=customer.custom_fields or {},
            created_at=customer.created_at,
            updated_at=customer.updated_at
        )

    @staticmethod
    def validate_import_row(
        row: Dict[str, Any],
        row_number: int
    ) -> Union[CustomerImportSchema, Dict[str, Any]]:
        """
        Validate a single row of import data.

        Args:
            row: Raw row data from CSV/JSON
            row_number: Row number for error reporting

        Returns:
            Either validated CustomerImportSchema or error dict
        """
        try:
            # Clean up the row data
            cleaned_row = {}
            for key, value in row.items():
                # Skip empty strings
                if value == "":
                    continue
                # Convert string booleans
                if isinstance(value, str) and value.lower() in ["true", "false"]:
                    value = value.lower() == "true"
                cleaned_row[key] = value

            # Validate using schema
            return CustomerImportSchema(**cleaned_row)
        except Exception as e:
            return {
                "row_number": row_number,
                "error": str(e),
                "data": row
            }

    @staticmethod
    def batch_validate(
        rows: List[Dict[str, Any]]
    ) -> tuple[List[CustomerImportSchema], List[Dict[str, Any]]]:
        """
        Validate multiple rows of import data.

        Args:
            rows: List of raw row data

        Returns:
            Tuple of (valid_rows, error_rows)
        """
        valid_rows = []
        error_rows = []

        for i, row in enumerate(rows, start=1):
            result = CustomerMapper.validate_import_row(row, i)
            if isinstance(result, CustomerImportSchema):
                valid_rows.append(result)
            else:
                error_rows.append(result)

        return valid_rows, error_rows