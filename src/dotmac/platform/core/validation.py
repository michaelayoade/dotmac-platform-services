"""
Common validation patterns for DotMac Platform Services.

Provides reusable validators for common data types and patterns.
"""

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ValidationError(Exception):
    """Base validation error."""

    pass


class CommonValidators:
    """Collection of common validation utilities."""

    # Regex patterns
    SUBDOMAIN_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?$")
    TENANT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9\-_]{2,31}$")
    PHONE_PATTERN = re.compile(r"^\+?1?\d{9,15}$")
    URL_PATTERN = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    @staticmethod
    def validate_email_address(email: str) -> str:
        """
        Validate email address format.

        Args:
            email: Email address to validate

        Returns:
            Normalized email address

        Raises:
            ValidationError: If email is invalid
        """
        if not email:
            raise ValidationError("Email address cannot be empty")

        email = email.lower().strip()

        # Basic email validation pattern
        email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        if not email_pattern.match(email):
            raise ValidationError(f"Invalid email address format: {email}")

        # Additional checks
        if email.count("@") != 1:
            raise ValidationError("Email must contain exactly one @ symbol")

        local, domain = email.split("@")
        if not local:
            raise ValidationError("Email local part cannot be empty")
        if not domain:
            raise ValidationError("Email domain cannot be empty")

        # Check for consecutive dots
        if ".." in email:
            raise ValidationError("Email cannot contain consecutive dots")

        return email

    @staticmethod
    def validate_subdomain(subdomain: str) -> str:
        """
        Validate subdomain format.

        Args:
            subdomain: Subdomain to validate

        Returns:
            Normalized subdomain

        Raises:
            ValidationError: If subdomain is invalid
        """
        if not subdomain:
            raise ValidationError("Subdomain cannot be empty")

        subdomain = subdomain.lower().strip()

        if not CommonValidators.SUBDOMAIN_PATTERN.match(subdomain):
            raise ValidationError(
                "Subdomain must contain only lowercase letters, numbers, and hyphens. "
                "Cannot start or end with a hyphen."
            )

        if len(subdomain) > 63:
            raise ValidationError("Subdomain cannot exceed 63 characters")

        # Check for reserved subdomains
        reserved = ["www", "api", "admin", "mail", "ftp", "localhost", "app", "dashboard"]
        if subdomain in reserved:
            raise ValidationError(f"Subdomain '{subdomain}' is reserved")

        return subdomain

    @staticmethod
    def validate_tenant_id(tenant_id: str) -> str:
        """
        Validate tenant ID format.

        Args:
            tenant_id: Tenant ID to validate

        Returns:
            Normalized tenant ID

        Raises:
            ValidationError: If tenant ID is invalid
        """
        if not tenant_id:
            raise ValidationError("Tenant ID cannot be empty")

        tenant_id = tenant_id.lower().strip()

        if not CommonValidators.TENANT_ID_PATTERN.match(tenant_id):
            raise ValidationError(
                "Tenant ID must start with alphanumeric character and contain only "
                "lowercase letters, numbers, hyphens, and underscores (3-32 characters)"
            )

        return tenant_id

    @staticmethod
    def validate_phone_number(phone: str) -> str:
        """
        Validate phone number format.

        Args:
            phone: Phone number to validate

        Returns:
            Normalized phone number

        Raises:
            ValidationError: If phone number is invalid
        """
        if not phone:
            raise ValidationError("Phone number cannot be empty")

        # Remove all non-digit characters except +
        cleaned = re.sub(r"[^\d+]", "", phone)

        if not CommonValidators.PHONE_PATTERN.match(cleaned):
            raise ValidationError(
                "Invalid phone number format. Must be 9-15 digits, optionally starting with +"
            )

        return cleaned

    @staticmethod
    def validate_required_fields(data: dict, required_fields: list[str]) -> None:
        """
        Validate that all required fields are present and not empty.

        Args:
            data: Data dictionary to validate
            required_fields: List of required field names

        Raises:
            ValidationError: If any required field is missing or empty
        """
        missing_fields = []
        empty_fields = []

        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
            elif data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
                empty_fields.append(field)

        errors = []
        if missing_fields:
            errors.append(f"Missing required fields: {', '.join(missing_fields)}")
        if empty_fields:
            errors.append(f"Empty required fields: {', '.join(empty_fields)}")

        if errors:
            raise ValidationError("; ".join(errors))

    @staticmethod
    def validate_string_length(
        value: str,
        min_length: int | None = None,
        max_length: int | None = None,
        field_name: str = "value",
    ) -> str:
        """
        Validate string length constraints.

        Args:
            value: String to validate
            min_length: Minimum length (inclusive)
            max_length: Maximum length (inclusive)
            field_name: Field name for error messages

        Returns:
            Validated string

        Raises:
            ValidationError: If string length is invalid
        """
        if value is None:
            raise ValidationError(f"{field_name} cannot be None")

        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string")

        length = len(value)

        if min_length is not None and length < min_length:
            raise ValidationError(
                f"{field_name} must be at least {min_length} characters long"
            )

        if max_length is not None and length > max_length:
            raise ValidationError(
                f"{field_name} cannot exceed {max_length} characters"
            )

        return value

    @staticmethod
    def validate_pattern(
        value: str,
        pattern: str | re.Pattern,
        field_name: str = "value",
        error_message: str | None = None,
    ) -> str:
        """
        Validate string against regex pattern.

        Args:
            value: String to validate
            pattern: Regex pattern (string or compiled)
            field_name: Field name for error messages
            error_message: Custom error message

        Returns:
            Validated string

        Raises:
            ValidationError: If string doesn't match pattern
        """
        if value is None:
            raise ValidationError(f"{field_name} cannot be None")

        if isinstance(pattern, str):
            pattern = re.compile(pattern)

        if not pattern.match(value):
            if error_message:
                raise ValidationError(error_message)
            else:
                raise ValidationError(
                    f"{field_name} does not match required pattern"
                )

        return value

    @staticmethod
    def validate_url(url: str) -> str:
        """
        Validate URL format.

        Args:
            url: URL to validate

        Returns:
            Validated URL

        Raises:
            ValidationError: If URL is invalid
        """
        if not url:
            raise ValidationError("URL cannot be empty")

        if not CommonValidators.URL_PATTERN.match(url):
            raise ValidationError(f"Invalid URL format: {url}")

        return url

    @staticmethod
    def validate_range(
        value: int | float,
        min_value: int | float | None = None,
        max_value: int | float | None = None,
        field_name: str = "value",
    ) -> int | float:
        """
        Validate numeric range.

        Args:
            value: Number to validate
            min_value: Minimum value (inclusive)
            max_value: Maximum value (inclusive)
            field_name: Field name for error messages

        Returns:
            Validated number

        Raises:
            ValidationError: If number is out of range
        """
        if value is None:
            raise ValidationError(f"{field_name} cannot be None")

        if not isinstance(value, (int, float)):
            raise ValidationError(f"{field_name} must be a number")

        if min_value is not None and value < min_value:
            raise ValidationError(f"{field_name} must be at least {min_value}")

        if max_value is not None and value > max_value:
            raise ValidationError(f"{field_name} cannot exceed {max_value}")

        return value


# Pydantic models with built-in validation
class EmailModel(BaseModel):
    """Model with email validation."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    email: str = Field(..., min_length=3, max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        return CommonValidators.validate_email_address(v)


class PhoneModel(BaseModel):
    """Model with phone validation."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    phone: str = Field(..., min_length=9, max_length=20)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone format."""
        return CommonValidators.validate_phone_number(v)


class TenantModel(BaseModel):
    """Model with tenant validation."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    tenant_id: str = Field(..., min_length=3, max_length=32)
    subdomain: str | None = Field(None, min_length=1, max_length=63)

    @field_validator("tenant_id")
    @classmethod
    def validate_tenant_id(cls, v: str) -> str:
        """Validate tenant ID format."""
        return CommonValidators.validate_tenant_id(v)

    @field_validator("subdomain")
    @classmethod
    def validate_subdomain(cls, v: str | None) -> str | None:
        """Validate subdomain format."""
        if v is not None:
            return CommonValidators.validate_subdomain(v)
        return v


# Export validators
__all__ = [
    "ValidationError",
    "CommonValidators",
    "EmailModel",
    "PhoneModel",
    "TenantModel",
]