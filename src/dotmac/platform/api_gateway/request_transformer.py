"""Request and response transformation for API Gateway."""

import asyncio
import re
from typing import Any, Callable, Dict, List, Awaitable, Union
from dataclasses import dataclass, field

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

@dataclass
class TransformationRule:
    """Rule for transforming requests or responses."""

    name: str
    pattern: str  # URL pattern or regex
    transform_type: str  # 'request', 'response', or 'both'
    transformations: List[Dict[str, Any]] = field(default_factory=list)
    enabled: bool = True
    priority: int = 0  # Higher priority rules execute first

class RequestTransformer:
    """Request and response transformation middleware."""

    def __init__(self):
        self.rules: List[TransformationRule] = []
        self.custom_transformers: Dict[
            str,
            Callable[
                [Dict[str, Any], Dict[str, Any], str],
                Union[Dict[str, Any], Awaitable[Dict[str, Any]]],
            ],
        ] = {}
        self._setup_default_transformers()

    def _setup_default_transformers(self):
        """Setup built-in transformation functions."""
        self.custom_transformers.update(
            {
                "add_header": self._add_header,
                "remove_header": self._remove_header,
                "modify_header": self._modify_header,
                "add_query_param": self._add_query_param,
                "remove_query_param": self._remove_query_param,
                "modify_path": self._modify_path,
                "json_path_modify": self._json_path_modify,
                "json_path_remove": self._json_path_remove,
                "json_path_add": self._json_path_add,
                "rename_field": self._rename_field,
                "convert_case": self._convert_case,
                "validate_schema": self._validate_schema,
            }
        )

    def add_rule(self, rule: TransformationRule):
        """Add a transformation rule."""
        self.rules.append(rule)
        self.rules.sort(key=lambda x: x.priority, reverse=True)
        logger.info(f"Added transformation rule: {rule.name}")

    def remove_rule(self, rule_name: str) -> bool:
        """Remove a transformation rule by name."""
        initial_count = len(self.rules)
        self.rules = [r for r in self.rules if r.name != rule_name]
        removed = len(self.rules) < initial_count
        if removed:
            logger.info(f"Removed transformation rule: {rule_name}")
        return removed

    def register_transformer(
        self,
        name: str,
        transformer: Callable[
            [Dict[str, Any], Dict[str, Any], str], Union[Dict[str, Any], Awaitable[Dict[str, Any]]]
        ],
    ) -> None:
        """Register a custom transformer function."""
        self.custom_transformers[name] = transformer
        logger.info(f"Registered custom transformer: {name}")

    async def transform_request(self, request_data: Dict[str, Any], path: str) -> Dict[str, Any]:
        """Transform incoming request."""
        transformed = request_data.copy()

        for rule in self.rules:
            if not rule.enabled:
                continue

            if rule.transform_type not in ["request", "both"]:
                continue

            if self._matches_pattern(path, rule.pattern):
                try:
                    transformed = await self._apply_transformations(
                        transformed, rule.transformations, "request"
                    )
                    logger.debug(f"Applied rule '{rule.name}' to request")
                except Exception as e:
                    logger.error(f"Failed to apply rule '{rule.name}': {e}")

        return transformed

    async def transform_response(self, response_data: Dict[str, Any], path: str) -> Dict[str, Any]:
        """Transform outgoing response."""
        transformed = response_data.copy()

        for rule in self.rules:
            if not rule.enabled:
                continue

            if rule.transform_type not in ["response", "both"]:
                continue

            if self._matches_pattern(path, rule.pattern):
                try:
                    transformed = await self._apply_transformations(
                        transformed, rule.transformations, "response"
                    )
                    logger.debug(f"Applied rule '{rule.name}' to response")
                except Exception as e:
                    logger.error(f"Failed to apply rule '{rule.name}': {e}")

        return transformed

    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches the pattern."""
        if pattern == "*":
            return True

        # Try regex match
        try:
            return bool(re.match(pattern, path))
        except re.error:
            # Fall back to simple string matching
            return pattern in path

    async def _apply_transformations(
        self, data: Dict[str, Any], transformations: List[Dict[str, Any]], context: str
    ) -> Dict[str, Any]:
        """Apply a list of transformations to data."""
        result = data

        for transformation in transformations:
            transform_type = transformation.get("type")
            if transform_type not in self.custom_transformers:
                logger.warning(f"Unknown transformation type: {transform_type}")
                continue

            transformer = self.custom_transformers[transform_type]
            params = transformation.get("params", {})

            try:
                if asyncio.iscoroutinefunction(transformer):
                    result = await transformer(result, params, context)
                else:
                    result = transformer(result, params, context)
            except Exception as e:
                logger.error(f"Transformation '{transform_type}' failed: {e}")

        return result

    # Built-in transformation functions

    def _add_header(
        self, data: Dict[str, Any], params: Dict[str, Any], context: str
    ) -> Dict[str, Any]:
        """Add a header to the request/response."""
        if "headers" not in data:
            data["headers"] = {}

        header_name = params.get("name")
        header_value = params.get("value")

        if header_name and header_value:
            data["headers"][header_name] = header_value

        return data

    def _remove_header(
        self, data: Dict[str, Any], params: Dict[str, Any], context: str
    ) -> Dict[str, Any]:
        """Remove a header from the request/response."""
        if "headers" in data:
            header_name = params.get("name")
            if header_name and header_name in data["headers"]:
                del data["headers"][header_name]

        return data

    def _modify_header(
        self, data: Dict[str, Any], params: Dict[str, Any], context: str
    ) -> Dict[str, Any]:
        """Modify a header value."""
        if "headers" in data:
            header_name = params.get("name")
            new_value = params.get("value")
            transform_func = params.get("transform")  # Optional transformation function

            if header_name and header_name in data["headers"]:
                if transform_func:
                    # Apply transformation function (e.g., 'upper', 'lower')
                    current_value = data["headers"][header_name]
                    if transform_func == "upper":
                        data["headers"][header_name] = current_value.upper()
                    elif transform_func == "lower":
                        data["headers"][header_name] = current_value.lower()
                    elif transform_func == "capitalize":
                        data["headers"][header_name] = current_value.capitalize()
                elif new_value:
                    data["headers"][header_name] = new_value

        return data

    def _add_query_param(
        self, data: Dict[str, Any], params: Dict[str, Any], context: str
    ) -> Dict[str, Any]:
        """Add a query parameter."""
        if "query_params" not in data:
            data["query_params"] = {}

        param_name = params.get("name")
        param_value = params.get("value")

        if param_name and param_value:
            data["query_params"][param_name] = param_value

        return data

    def _remove_query_param(
        self, data: Dict[str, Any], params: Dict[str, Any], context: str
    ) -> Dict[str, Any]:
        """Remove a query parameter."""
        if "query_params" in data:
            param_name = params.get("name")
            if param_name and param_name in data["query_params"]:
                del data["query_params"][param_name]

        return data

    def _modify_path(
        self, data: Dict[str, Any], params: Dict[str, Any], context: str
    ) -> Dict[str, Any]:
        """Modify the request path."""
        if "path" in data:
            pattern = params.get("pattern")
            replacement = params.get("replacement")

            if pattern and replacement:
                data["path"] = re.sub(pattern, replacement, data["path"])

        return data

    def _json_path_modify(
        self, data: Dict[str, Any], params: Dict[str, Any], context: str
    ) -> Dict[str, Any]:
        """Modify a value in JSON body using path notation."""
        if "body" not in data or not isinstance(data["body"], dict):
            return data

        path = params.get("path", "").split(".")
        value = params.get("value")

        if not path or not value:
            return data

        # Navigate to the target location
        current = data["body"]
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set the value
        if path[-1] in current:
            current[path[-1]] = value

        return data

    def _json_path_remove(
        self, data: Dict[str, Any], params: Dict[str, Any], context: str
    ) -> Dict[str, Any]:
        """Remove a field from JSON body using path notation."""
        if "body" not in data or not isinstance(data["body"], dict):
            return data

        path = params.get("path", "").split(".")

        if not path:
            return data

        # Navigate to the target location
        current = data["body"]
        for key in path[:-1]:
            if key not in current:
                return data
            current = current[key]

        # Remove the field
        if path[-1] in current:
            del current[path[-1]]

        return data

    def _json_path_add(
        self, data: Dict[str, Any], params: Dict[str, Any], context: str
    ) -> Dict[str, Any]:
        """Add a field to JSON body using path notation."""
        if "body" not in data:
            data["body"] = {}

        if not isinstance(data["body"], dict):
            return data

        path = params.get("path", "").split(".")
        value = params.get("value")

        if not path:
            return data

        # Navigate to the target location, creating path as needed
        current = data["body"]
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Add the field
        current[path[-1]] = value

        return data

    def _rename_field(
        self, data: Dict[str, Any], params: Dict[str, Any], context: str
    ) -> Dict[str, Any]:
        """Rename a field in the JSON body."""
        if "body" not in data or not isinstance(data["body"], dict):
            return data

        old_name = params.get("old_name")
        new_name = params.get("new_name")

        if old_name and new_name and old_name in data["body"]:
            data["body"][new_name] = data["body"].pop(old_name)

        return data

    def _convert_case(
        self, data: Dict[str, Any], params: Dict[str, Any], context: str
    ) -> Dict[str, Any]:
        """Convert case of keys in JSON body."""
        if "body" not in data or not isinstance(data["body"], dict):
            return data

        case_type = params.get("case", "snake")  # snake, camel, pascal, kebab

        def convert_key(key: str) -> str:
            if case_type == "snake":
                # Convert to snake_case
                return re.sub("([A-Z]+)", r"_\1", key).lower().lstrip("_")
            elif case_type == "camel":
                # Convert to camelCase
                parts = key.split("_")
                return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])
            elif case_type == "pascal":
                # Convert to PascalCase
                return "".join(p.capitalize() for p in key.split("_"))
            elif case_type == "kebab":
                # Convert to kebab-case
                return key.replace("_", "-").lower()
            return key

        def convert_dict(d: Dict) -> Dict:
            result = {}
            for key, value in d.items():
                new_key = convert_key(key) if isinstance(key, str) else key
                if isinstance(value, dict):
                    result[new_key] = convert_dict(value)
                elif isinstance(value, list):
                    result[new_key] = [
                        convert_dict(item) if isinstance(item, dict) else item for item in value
                    ]
                else:
                    result[new_key] = value
            return result

        data["body"] = convert_dict(data["body"])
        return data

    def _validate_schema(
        self, data: Dict[str, Any], params: Dict[str, Any], context: str
    ) -> Dict[str, Any]:
        """Validate JSON body against a schema (basic implementation)."""
        if "body" not in data or not isinstance(data["body"], dict):
            return data

        required_fields = params.get("required_fields", [])
        field_types = params.get("field_types", {})

        # Check required fields
        for field in required_fields:
            if field not in data["body"]:
                raise ValueError(f"Required field '{field}' is missing")

        # Check field types
        for field, expected_type in field_types.items():
            if field in data["body"]:
                value = data["body"][field]
                if expected_type == "string" and not isinstance(value, str):
                    raise TypeError(f"Field '{field}' must be a string")
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    raise TypeError(f"Field '{field}' must be a number")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    raise TypeError(f"Field '{field}' must be a boolean")
                elif expected_type == "array" and not isinstance(value, list):
                    raise TypeError(f"Field '{field}' must be an array")
                elif expected_type == "object" and not isinstance(value, dict):
                    raise TypeError(f"Field '{field}' must be an object")

        return data
