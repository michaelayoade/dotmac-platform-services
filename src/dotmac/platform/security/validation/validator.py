from dotmac.platform.logging import get_logger

"""
Security validation using standard libraries.

For production use, consider: bleach, sqlparse, or dedicated security scanners.
"""

import html
import re
from typing import Any

# Try to import bleach for XSS protection (recommended: pip install bleach)
try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False

# Try to import sqlparse for SQL validation (recommended: pip install sqlparse)
try:
    import sqlparse
    SQLPARSE_AVAILABLE = True
except ImportError:
    SQLPARSE_AVAILABLE = False

from dotmac.platform.logging import get_logger

logger = get_logger(__name__)

class SecurityValidator:
    """Security validator using standard libraries when available."""

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
        Sanitize input data using bleach if available, html.escape as fallback.
        """
        if isinstance(data, str):
            if BLEACH_AVAILABLE:
                # Use bleach for comprehensive XSS protection
                return bleach.clean(data, tags=[], attributes={}, strip=True)
            else:
                # Fallback to html.escape
                return html.escape(data).strip()

        elif isinstance(data, dict):
            return {k: self.sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_data(item) for item in data]

        return data

    def check_sql_injection(self, data: str) -> bool:
        """
        Check for SQL injection using sqlparse if available.
        """
        if SQLPARSE_AVAILABLE:
            try:
                # Parse SQL to detect injection patterns
                parsed = sqlparse.parse(data)
                for statement in parsed:
                    if any(token.ttype is sqlparse.tokens.Keyword
                          for token in statement.flatten()
                          if str(token).upper() in ('UNION', 'SELECT', 'DROP', 'DELETE')):
                        logger.warning("Potential SQL injection detected via sqlparse", data=data[:100])
                        return True
            except Exception:
                pass

        # Basic fallback patterns
        dangerous = ['union', 'select', 'drop', 'delete', '--', '/*', '*/', 'xp_']
        data_lower = data.lower()
        if any(pattern in data_lower for pattern in dangerous):
            logger.warning("Potential SQL injection detected", data=data[:100])
            return True

        return False

    def check_xss(self, data: str) -> bool:
        """
        Check for XSS using bleach if available.
        """
        if BLEACH_AVAILABLE:
            # Use bleach to detect potentially harmful content
            cleaned = bleach.clean(data, tags=[], attributes={}, strip=True)
            if cleaned != data:
                logger.warning("Potential XSS detected via bleach", data=data[:100])
                return True
        else:
            # Basic pattern matching fallback
            patterns = ['<script', 'javascript:', 'on\w+\s*=', '<iframe', '<object']
            if any(re.search(pattern, data, re.IGNORECASE) for pattern in patterns):
                logger.warning("Potential XSS detected", data=data[:100])
                return True

        return False
