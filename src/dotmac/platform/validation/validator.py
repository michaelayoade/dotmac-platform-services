"""
Security validation framework.
"""

import html
import re
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class SecurityValidator:
    """Comprehensive security validator for input validation and sanitization."""

    def __init__(self):
        self.sql_injection_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\s+.+\s*=\s*.+)",
            r"(--|#|\/\*|\*\/)",
            r"(\bUNION\b.+\bSELECT\b)",
        ]

        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>.*?</iframe>",
            r"<object[^>]*>.*?</object>",
            r"<embed[^>]*>",
        ]

    def validate_input(self, data: Any, rules: dict[str, Any]) -> dict[str, Any]:
        """
        Validate input data against security rules.

        Args:
            data: Input data to validate
            rules: Validation rules dictionary

        Returns:
            Dict with validation results
        """
        result = {
            "valid": True,
            "errors": [],
            "sanitized_data": data,
        }

        try:
            # Check for SQL injection
            if rules.get("check_sql_injection", False):
                if self.check_sql_injection(str(data)):
                    result["valid"] = False
                    result["errors"].append("Potential SQL injection detected")

            # Check for XSS
            if rules.get("check_xss", False):
                if self.check_xss(str(data)):
                    result["valid"] = False
                    result["errors"].append("Potential XSS attack detected")

            # Sanitize data if requested
            if rules.get("sanitize", False):
                result["sanitized_data"] = self.sanitize_data(data)

            # Length validation
            max_length = rules.get("max_length")
            if max_length and len(str(data)) > max_length:
                result["valid"] = False
                result["errors"].append(f"Input exceeds maximum length of {max_length}")

            # Pattern validation
            pattern = rules.get("pattern")
            if pattern and not re.match(pattern, str(data)):
                result["valid"] = False
                result["errors"].append("Input does not match required pattern")

        except Exception as e:
            logger.error("Input validation error", error=str(e))
            result["valid"] = False
            result["errors"].append(f"Validation error: {e}")

        return result

    def sanitize_data(self, data: Any) -> Any:
        """
        Sanitize input data to remove potentially harmful content.

        Args:
            data: Input data to sanitize

        Returns:
            Sanitized data
        """
        if isinstance(data, str):
            # HTML escape
            sanitized = html.escape(data)

            # Remove potentially harmful patterns
            for pattern in self.xss_patterns:
                sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

            return sanitized.strip()

        elif isinstance(data, dict):
            return {k: self.sanitize_data(v) for k, v in data.items()}

        elif isinstance(data, list):
            return [self.sanitize_data(item) for item in data]

        return data

    def check_sql_injection(self, data: str) -> bool:
        """
        Check if input contains potential SQL injection attempts.

        Args:
            data: Input string to check

        Returns:
            True if potential SQL injection detected
        """
        data_lower = data.lower()

        for pattern in self.sql_injection_patterns:
            if re.search(pattern, data_lower, re.IGNORECASE):
                logger.warning("Potential SQL injection detected", pattern=pattern, data=data[:100])
                return True

        return False

    def check_xss(self, data: str) -> bool:
        """
        Check if input contains potential XSS attempts.

        Args:
            data: Input string to check

        Returns:
            True if potential XSS detected
        """
        for pattern in self.xss_patterns:
            if re.search(pattern, data, re.IGNORECASE):
                logger.warning("Potential XSS detected", pattern=pattern, data=data[:100])
                return True

        return False
