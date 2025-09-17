"""Request validation middleware for API Gateway."""

import json
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union
from dataclasses import dataclass, field
from enum import Enum
import re
from pydantic import BaseModel, ValidationError, Field
from abc import ABC, abstractmethod

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

class ValidationLevel(str, Enum):
    """Validation strictness levels."""

    STRICT = "strict"  # Fail on any validation error
    MODERATE = "moderate"  # Allow unknown fields, fail on type errors
    LENIENT = "lenient"  # Log warnings, pass through

class ContentType(str, Enum):
    """Supported content types for validation."""

    JSON = "application/json"
    FORM = "application/x-www-form-urlencoded"
    MULTIPART = "multipart/form-data"
    XML = "application/xml"
    TEXT = "text/plain"

@dataclass
class ValidationRule:
    """Single validation rule."""

    field_name: str
    rule_type: str  # required, type, pattern, range, enum
    config: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = None

@dataclass
class SchemaDefinition:
    """Schema definition for request validation."""

    name: str
    version: str = "1.0.0"
    content_type: ContentType = ContentType.JSON
    rules: List[ValidationRule] = field(default_factory=list)
    pydantic_model: Optional[Type[BaseModel]] = None
    allow_extra: bool = False
    custom_validators: List[Callable[[Any], bool]] = field(default_factory=list)

class ValidationResult:
    """Result of validation."""

    def __init__(self, valid: bool = True):
        self.valid = valid
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.transformed_data: Optional[Any] = None

    def add_error(self, field: str, message: str, code: str = "validation_error"):
        """Add validation error."""
        self.valid = False
        self.errors.append({"field": field, "message": message, "code": code})

    def add_warning(self, field: str, message: str):
        """Add validation warning."""
        self.warnings.append({"field": field, "message": message})

class SchemaRegistry:
    """Registry for request/response schemas."""

    def __init__(self):
        self._schemas: Dict[str, Dict[str, SchemaDefinition]] = {}
        self._route_schemas: Dict[str, str] = {}  # route -> schema_name mapping

    def register_schema(self, schema: SchemaDefinition):
        """Register a schema."""
        if schema.name not in self._schemas:
            self._schemas[schema.name] = {}
        self._schemas[schema.name][schema.version] = schema
        logger.info(f"Registered schema: {schema.name} v{schema.version}")

    def register_pydantic_model(self, name: str, model: Type[BaseModel], version: str = "1.0.0"):
        """Register a Pydantic model as schema."""
        schema = SchemaDefinition(name=name, version=version, pydantic_model=model)
        self.register_schema(schema)

    def map_route_to_schema(self, route_pattern: str, schema_name: str):
        """Map a route pattern to a schema."""
        self._route_schemas[route_pattern] = schema_name

    def get_schema(self, name: str, version: Optional[str] = None) -> Optional[SchemaDefinition]:
        """Get schema by name and version."""
        if name not in self._schemas:
            return None

        if version:
            return self._schemas[name].get(version)

        # Return latest version
        versions = list(self._schemas[name].keys())
        if versions:
            latest = sorted(versions)[-1]
            return self._schemas[name][latest]

        return None

    def get_schema_for_route(self, route: str) -> Optional[SchemaDefinition]:
        """Get schema for a route."""
        # Direct match
        if route in self._route_schemas:
            schema_name = self._route_schemas[route]
            return self.get_schema(schema_name)

        # Pattern match
        for pattern, schema_name in self._route_schemas.items():
            if re.match(pattern, route):
                return self.get_schema(schema_name)

        return None

class Validator(ABC):
    """Abstract validator interface."""

    @abstractmethod
    async def validate(
        self, data: Any, schema: SchemaDefinition, level: ValidationLevel = ValidationLevel.STRICT
    ) -> ValidationResult:
        """Validate data against schema."""
        pass

class PydanticValidator(Validator):
    """Validator using Pydantic models."""

    async def validate(
        self, data: Any, schema: SchemaDefinition, level: ValidationLevel = ValidationLevel.STRICT
    ) -> ValidationResult:
        """Validate using Pydantic model."""
        result = ValidationResult()

        if not schema.pydantic_model:
            result.add_error("schema", "No Pydantic model defined")
            return result

        try:
            if level == ValidationLevel.LENIENT:
                # In lenient mode, just try to parse
                instance = schema.pydantic_model.model_validate(data)
            else:
                # Strict/moderate validation
                config = {}
                if level == ValidationLevel.MODERATE or schema.allow_extra:
                    config["extra"] = "allow"
                else:
                    config["extra"] = "forbid"

                # Create dynamic model with config
                instance = schema.pydantic_model.model_validate(data)

            result.transformed_data = instance.model_dump()

        except ValidationError as e:
            if level == ValidationLevel.LENIENT:
                # Log as warnings in lenient mode
                for error in e.errors():
                    field_path = ".".join(str(loc) for loc in error["loc"])
                    result.add_warning(field_path, error["msg"])
                result.valid = True  # Still pass in lenient mode
            else:
                # Add as errors
                for error in e.errors():
                    field_path = ".".join(str(loc) for loc in error["loc"])
                    result.add_error(field_path, error["msg"], error["type"])

        return result

class RuleBasedValidator(Validator):
    """Validator using validation rules."""

    async def validate(
        self, data: Any, schema: SchemaDefinition, level: ValidationLevel = ValidationLevel.STRICT
    ) -> ValidationResult:
        """Validate using rules."""
        result = ValidationResult()

        if not isinstance(data, dict):
            result.add_error("data", "Data must be a dictionary")
            return result

        for rule in schema.rules:
            self._apply_rule(data, rule, result, level)

        # Check for extra fields if not allowed
        if not schema.allow_extra and level == ValidationLevel.STRICT:
            defined_fields = {rule.field_name for rule in schema.rules}
            extra_fields = set(data.keys()) - defined_fields
            for field in extra_fields:
                result.add_error(field, f"Unknown field: {field}")

        result.transformed_data = data
        return result

    def _apply_rule(
        self, data: Dict, rule: ValidationRule, result: ValidationResult, level: ValidationLevel
    ):
        """Apply a single validation rule."""
        field_value = data.get(rule.field_name)

        if rule.rule_type == "required":
            if field_value is None:
                if level == ValidationLevel.LENIENT:
                    result.add_warning(
                        rule.field_name, rule.message or f"Field {rule.field_name} is required"
                    )
                else:
                    result.add_error(
                        rule.field_name, rule.message or f"Field {rule.field_name} is required"
                    )

        elif rule.rule_type == "type":
            expected_type = rule.config.get("type")
            if (
                field_value is not None
                and expected_type
                and not isinstance(field_value, expected_type)
            ):
                type_name = (
                    expected_type.__name__
                    if hasattr(expected_type, "__name__")
                    else str(expected_type)
                )
                msg = rule.message or f"Field {rule.field_name} must be of type {type_name}"
                if level == ValidationLevel.LENIENT:
                    result.add_warning(rule.field_name, msg)
                else:
                    result.add_error(rule.field_name, msg)

        elif rule.rule_type == "pattern":
            pattern = rule.config.get("pattern")
            if field_value and pattern and not re.match(pattern, str(field_value)):
                msg = rule.message or f"Field {rule.field_name} does not match pattern {pattern}"
                if level == ValidationLevel.LENIENT:
                    result.add_warning(rule.field_name, msg)
                else:
                    result.add_error(rule.field_name, msg)

        elif rule.rule_type == "range":
            min_val = rule.config.get("min")
            max_val = rule.config.get("max")
            if field_value is not None:
                if min_val is not None and field_value < min_val:
                    msg = rule.message or f"Field {rule.field_name} must be >= {min_val}"
                    if level == ValidationLevel.LENIENT:
                        result.add_warning(rule.field_name, msg)
                    else:
                        result.add_error(rule.field_name, msg)
                if max_val is not None and field_value > max_val:
                    msg = rule.message or f"Field {rule.field_name} must be <= {max_val}"
                    if level == ValidationLevel.LENIENT:
                        result.add_warning(rule.field_name, msg)
                    else:
                        result.add_error(rule.field_name, msg)

        elif rule.rule_type == "enum":
            allowed_values = rule.config.get("values", [])
            if field_value not in allowed_values:
                msg = rule.message or f"Field {rule.field_name} must be one of {allowed_values}"
                if level == ValidationLevel.LENIENT:
                    result.add_warning(rule.field_name, msg)
                else:
                    result.add_error(rule.field_name, msg)

class RequestValidator:
    """Main request validator with schema registry."""

    def __init__(self, default_level: ValidationLevel = ValidationLevel.STRICT):
        self.registry = SchemaRegistry()
        self.default_level = default_level
        self.validators: Dict[str, Validator] = {
            "pydantic": PydanticValidator(),
            "rules": RuleBasedValidator(),
        }

    def register_validator(self, name: str, validator: Validator):
        """Register custom validator."""
        self.validators[name] = validator

    async def validate_request(
        self,
        data: Any,
        schema_name: Optional[str] = None,
        route: Optional[str] = None,
        level: Optional[ValidationLevel] = None,
    ) -> ValidationResult:
        """Validate request data."""
        level = level or self.default_level

        # Get schema
        schema = None
        if schema_name:
            schema = self.registry.get_schema(schema_name)
        elif route:
            schema = self.registry.get_schema_for_route(route)

        if not schema:
            result = ValidationResult()
            if level == ValidationLevel.STRICT:
                result.add_error("schema", "No schema found for validation")
            else:
                result.add_warning("schema", "No schema found, skipping validation")
                result.transformed_data = data
            return result

        # Select validator
        if schema.pydantic_model:
            validator = self.validators["pydantic"]
        else:
            validator = self.validators["rules"]

        # Validate
        result = await validator.validate(data, schema, level)

        # Apply custom validators
        if result.valid and schema.custom_validators:
            for custom_validator in schema.custom_validators:
                try:
                    custom_result = await custom_validator(result.transformed_data or data)
                    if not custom_result:
                        result.add_error("custom", "Custom validation failed")
                except Exception as e:
                    logger.error(f"Custom validator error: {e}")
                    if level == ValidationLevel.STRICT:
                        result.add_error("custom", str(e))

        return result

class ValidationMiddleware:
    """Middleware for request/response validation."""

    def __init__(
        self,
        validator: RequestValidator,
        validate_requests: bool = True,
        validate_responses: bool = False,
    ):
        self.validator = validator
        self.validate_requests = validate_requests
        self.validate_responses = validate_responses

    async def __call__(self, request: Any, call_next: Callable[[Any], Any]) -> Any:
        """Process request through validation."""
        if self.validate_requests:
            # Extract route from request
            url_obj = getattr(request, "url", None)
            if url_obj is None:
                route = ""
            elif isinstance(url_obj, dict):
                route = url_obj.get("path", "")
            else:
                route = getattr(url_obj, "path", "")

            # Get request body
            try:
                if hasattr(request, "json"):
                    data = await request.json()
                elif hasattr(request, "form"):
                    data = await request.form()
                else:
                    data = {}
            except:
                data = {}

            # Validate
            result = await self.validator.validate_request(data=data, route=route)

            if not result.valid:
                # Return validation error response (use 400 Bad Request)
                return {"error": "Validation failed", "details": result.errors}, 400

            # Replace request data with transformed data if available
            if result.transformed_data:
                request.validated_data = result.transformed_data

        # Process request
        response = await call_next(request)

        # TODO: Response validation if enabled

        return response
