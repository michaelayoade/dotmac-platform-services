"""
Convenience functions for security validation.
"""

from typing import Any

from .validator import SecurityValidator

_validator = SecurityValidator()


def validate_input(data: Any, rules: dict[str, Any]) -> dict[str, Any]:
    """
    Validate input data against security rules.

    Args:
        data: Input data to validate
        rules: Validation rules dictionary

    Returns:
        Dict with validation results
    """
    return _validator.validate_input(data, rules)


def sanitize_data(data: Any) -> Any:
    """
    Sanitize input data to remove potentially harmful content.

    Args:
        data: Input data to sanitize

    Returns:
        Sanitized data
    """
    return _validator.sanitize_data(data)


def check_sql_injection(data: str) -> bool:
    """
    Check if input contains potential SQL injection attempts.

    Args:
        data: Input string to check

    Returns:
        True if potential SQL injection detected
    """
    return _validator.check_sql_injection(data)


def check_xss(data: str) -> bool:
    """
    Check if input contains potential XSS attempts.

    Args:
        data: Input string to check

    Returns:
        True if potential XSS detected
    """
    return _validator.check_xss(data)
