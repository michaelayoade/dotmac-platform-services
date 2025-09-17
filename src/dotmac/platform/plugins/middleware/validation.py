"""
Input/output validation middleware for plugin execution.

Validates plugin method arguments and return values against schemas.
"""


from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Optional

from ..core.exceptions import PluginValidationError
from ..core.plugin_base import BasePlugin

from dotmac.platform.observability.unified_logging import get_logger
@dataclass
class ValidationRule:
    """Single validation rule configuration."""

    field_name: str
    field_type: type
    required: bool = True
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    custom_validator: Optional[Callable[[Any], bool]] = None
    error_message: Optional[str] = None

@dataclass
class ValidationSchema:
    """Validation schema for plugin method."""

    method_name: str
    input_rules: list[ValidationRule]
    output_rules: Optional[list[ValidationRule]] = None
    validate_output: bool = False

class BaseValidator(ABC):
    """Base class for value validators."""

    @abstractmethod
    def validate(self, value: Any, rule: ValidationRule) -> bool:
        """Validate a value against a rule."""
        pass

    @abstractmethod
    def get_error_message(self, value: Any, rule: ValidationRule) -> str:
        """Get validation error message."""
        pass

class TypeValidator(BaseValidator):
    """Validates value types."""

    def validate(self, value: Any, rule: ValidationRule) -> bool:
        return isinstance(value, rule.field_type)

    def get_error_message(self, value: Any, rule: ValidationRule) -> str:
        return f"Expected type {rule.field_type.__name__}, got {type(value).__name__}"

class RangeValidator(BaseValidator):
    """Validates numeric ranges."""

    def validate(self, value: Any, rule: ValidationRule) -> bool:
        if rule.min_value is not None and value < rule.min_value:
            return False
        if rule.max_value is not None and value > rule.max_value:
            return False
        return True

    def get_error_message(self, value: Any, rule: ValidationRule) -> str:
        if rule.min_value is not None and rule.max_value is not None:
            return f"Value {value} must be between {rule.min_value} and {rule.max_value}"
        elif rule.min_value is not None:
            return f"Value {value} must be at least {rule.min_value}"
        elif rule.max_value is not None:
            return f"Value {value} must be at most {rule.max_value}"
        return f"Value {value} is out of range"

class LengthValidator(BaseValidator):
    """Validates string/collection lengths."""

    def validate(self, value: Any, rule: ValidationRule) -> bool:
        if not hasattr(value, "__len__"):
            return True  # Skip if no length method

        length = len(value)

        if rule.min_length is not None and length < rule.min_length:
            return False
        if rule.max_length is not None and length > rule.max_length:
            return False
        return True

    def get_error_message(self, value: Any, rule: ValidationRule) -> str:
        length = len(value) if hasattr(value, "__len__") else 0

        if rule.min_length is not None and rule.max_length is not None:
            return f"Length {length} must be between {rule.min_length} and {rule.max_length}"
        elif rule.min_length is not None:
            return f"Length {length} must be at least {rule.min_length}"
        elif rule.max_length is not None:
            return f"Length {length} must be at most {rule.max_length}"
        return f"Length {length} is invalid"

class PatternValidator(BaseValidator):
    """Validates string patterns using regex."""

    def validate(self, value: Any, rule: ValidationRule) -> bool:
        if not isinstance(value, str) or not rule.pattern:
            return True

        import re

        return bool(re.match(rule.pattern, value))

    def get_error_message(self, value: Any, rule: ValidationRule) -> str:
        return f"Value '{value}' does not match pattern '{rule.pattern}'"

class CustomValidator(BaseValidator):
    """Uses custom validation functions."""

    def validate(self, value: Any, rule: ValidationRule) -> bool:
        if not rule.custom_validator:
            return True

        try:
            return rule.custom_validator(value)
        except Exception:
            return False

    def get_error_message(self, value: Any, rule: ValidationRule) -> str:
        if rule.error_message:
            return rule.error_message
        return f"Custom validation failed for value: {value}"

class ValidationMiddleware:
    """
    Plugin method validation middleware.

    Validates input arguments and optionally output values for plugin methods.
    """

    def __init__(self):
        self._schemas: dict[str, dict[str, ValidationSchema]] = {}  # plugin_key -> method -> schema
        self._validators = [
            TypeValidator(),
            RangeValidator(),
            LengthValidator(),
            PatternValidator(),
            CustomValidator(),
        ]
        self._logger = get_logger("plugins.validation_middleware")

    def add_validation_schema(self, plugin_key: str, schema: ValidationSchema) -> None:
        """
        Add validation schema for a plugin method.

        Args:
            plugin_key: Plugin key in format "domain.name"
            schema: Validation schema for the method
        """
        if plugin_key not in self._schemas:
            self._schemas[plugin_key] = {}

        self._schemas[plugin_key][schema.method_name] = schema
        self._logger.debug(f"Added validation schema for {plugin_key}.{schema.method_name}")

    def remove_validation_schema(self, plugin_key: str, method_name: str) -> None:
        """Remove validation schema for a plugin method."""
        if plugin_key in self._schemas and method_name in self._schemas[plugin_key]:
            del self._schemas[plugin_key][method_name]
            self._logger.debug(f"Removed validation schema for {plugin_key}.{method_name}")

    def validate_input(
        self, plugin: BasePlugin, method_name: str, args: tuple, kwargs: dict
    ) -> None:
        """
        Validate input arguments for a plugin method.

        Args:
            plugin: Plugin instance
            method_name: Method being called
            args: Positional arguments
            kwargs: Keyword arguments

        Raises:
            PluginValidationError: If validation fails
        """
        plugin_key = f"{plugin.domain}.{plugin.name}"

        # Get validation schema
        schema = self._get_schema(plugin_key, method_name)
        if not schema:
            return  # No validation configured

        # Validate input arguments
        errors = []

        # Create a combined arguments dict for validation
        combined_args = dict(kwargs)

        # Add positional arguments (would need method signature inspection for proper names)
        for i, arg_value in enumerate(args):
            combined_args[f"arg_{i}"] = arg_value

        # Validate each input rule
        for rule in schema.input_rules:
            field_value = combined_args.get(rule.field_name)

            # Check required fields
            if rule.required and field_value is None:
                errors.append(f"Required field '{rule.field_name}' is missing")
                continue

            # Skip validation for None values on optional fields
            if field_value is None and not rule.required:
                continue

            # Run validators
            validation_errors = self._validate_value(field_value, rule)
            errors.extend(validation_errors)

        # Raise validation error if any errors found
        if errors:
            raise PluginValidationError(plugin.name, errors, field_name=method_name)

    def validate_output(self, plugin: BasePlugin, method_name: str, output: Any) -> None:
        """
        Validate output value from a plugin method.

        Args:
            plugin: Plugin instance
            method_name: Method that was called
            output: Return value from the method

        Raises:
            PluginValidationError: If validation fails
        """
        plugin_key = f"{plugin.domain}.{plugin.name}"

        # Get validation schema
        schema = self._get_schema(plugin_key, method_name)
        if not schema or not schema.validate_output or not schema.output_rules:
            return  # No output validation configured

        errors = []

        # Handle different output types
        if isinstance(output, dict):
            # Dictionary output - validate each field
            for rule in schema.output_rules:
                field_value = output.get(rule.field_name)

                if rule.required and field_value is None:
                    errors.append(f"Required output field '{rule.field_name}' is missing")
                    continue

                if field_value is None and not rule.required:
                    continue

                validation_errors = self._validate_value(field_value, rule)
                errors.extend(validation_errors)

        else:
            # Single value output - validate against first rule
            if schema.output_rules:
                rule = schema.output_rules[0]
                validation_errors = self._validate_value(output, rule)
                errors.extend(validation_errors)

        # Raise validation error if any errors found
        if errors:
            raise PluginValidationError(plugin.name, errors, field_name=f"{method_name}_output")

    def _get_schema(self, plugin_key: str, method_name: str) -> Optional[ValidationSchema]:
        """Get validation schema for plugin method."""
        return self._schemas.get(plugin_key, {}).get(method_name)

    def _validate_value(self, value: Any, rule: ValidationRule) -> list[str]:
        """Validate a single value against a rule."""
        errors = []

        # Run all applicable validators
        for validator in self._validators:
            try:
                if not validator.validate(value, rule):
                    error_msg = validator.get_error_message(value, rule)
                    if error_msg not in errors:  # Avoid duplicates
                        errors.append(error_msg)
            except Exception as e:
                self._logger.warning(f"Validator {validator.__class__.__name__} failed: {e}")

        return errors

    def get_validation_stats(self) -> dict[str, Any]:
        """Get validation statistics."""
        total_schemas = sum(len(methods) for methods in self._schemas.values())
        plugins_with_validation = len(self._schemas)

        # Count rules by type
        rule_counts = {
            "input_rules": 0,
            "output_rules": 0,
            "required_rules": 0,
            "optional_rules": 0,
        }

        for plugin_schemas in self._schemas.values():
            for schema in plugin_schemas.values():
                rule_counts["input_rules"] += len(schema.input_rules)
                rule_counts["required_rules"] += sum(
                    1 for rule in schema.input_rules if rule.required
                )
                rule_counts["optional_rules"] += sum(
                    1 for rule in schema.input_rules if not rule.required
                )

                if schema.output_rules:
                    rule_counts["output_rules"] += len(schema.output_rules)

        return {
            "total_schemas": total_schemas,
            "plugins_with_validation": plugins_with_validation,
            "rule_counts": rule_counts,
            "validators_available": len(self._validators),
        }

    @staticmethod
    def create_email_validation_schema() -> ValidationSchema:
        """Create a sample validation schema for email plugin."""
        return ValidationSchema(
            method_name="send_email",
            input_rules=[
                ValidationRule(
                    field_name="to_address",
                    field_type=str,
                    required=True,
                    pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                    error_message="Invalid email address format",
                ),
                ValidationRule(
                    field_name="subject",
                    field_type=str,
                    required=True,
                    max_length=200,
                    error_message="Subject must be less than 200 characters",
                ),
                ValidationRule(
                    field_name="body",
                    field_type=str,
                    required=True,
                    min_length=1,
                    max_length=10000,
                    error_message="Email body must be between 1 and 10000 characters",
                ),
            ],
            output_rules=[
                ValidationRule(field_name="success", field_type=bool, required=True),
                ValidationRule(field_name="message_id", field_type=str, required=False),
            ],
            validate_output=True,
        )

    @staticmethod
    def create_file_storage_validation_schema() -> ValidationSchema:
        """Create a sample validation schema for file storage plugin."""
        return ValidationSchema(
            method_name="save_file",
            input_rules=[
                ValidationRule(
                    field_name="filename",
                    field_type=str,
                    required=True,
                    pattern=r"^[a-zA-Z0-9._-]+$",
                    max_length=255,
                    error_message="Invalid filename format",
                ),
                ValidationRule(
                    field_name="content",
                    field_type=bytes,
                    required=True,
                    max_length=100 * 1024 * 1024,  # 100MB
                    error_message="File content too large",
                ),
                ValidationRule(field_name="overwrite", field_type=bool, required=False),
            ],
            output_rules=[
                ValidationRule(field_name="success", field_type=bool, required=True),
                ValidationRule(field_name="file_path", field_type=str, required=True),
                ValidationRule(field_name="file_size", field_type=int, required=True, min_value=0),
            ],
            validate_output=True,
        )
