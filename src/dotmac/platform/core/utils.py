"""Core utilities for platform services."""

import hashlib
import re
import uuid
from datetime import datetime, timezone
from typing import Any, TypeVar

T = TypeVar("T")


# ID Generation
def new_uuid() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())


def new_uuid_hex() -> str:
    """Generate a new UUID4 as hex string (no dashes)."""
    return uuid.uuid4().hex


def generate_id(prefix: str = "") -> str:
    """
    Generate a prefixed unique ID.

    Args:
        prefix: Optional prefix for the ID

    Returns:
        Unique ID string
    """
    uid = new_uuid()
    return f"{prefix}{uid}" if prefix else uid


# Time Utilities
def utcnow() -> datetime:
    """Get current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def to_utc(dt: datetime) -> datetime:
    """Convert datetime to UTC (timezone-aware)."""
    if dt.tzinfo is None:
        # Assume naive datetime is UTC
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def isoformat(dt: datetime | None = None) -> str:
    """
    Get ISO format string for datetime.

    Args:
        dt: Datetime to format (uses current UTC if None)

    Returns:
        ISO format string
    """
    if dt is None:
        dt = utcnow()
    return dt.isoformat()


def timestamp() -> float:
    """Get current Unix timestamp."""
    return utcnow().timestamp()


# String Utilities
def slugify(text: str) -> str:
    """
    Convert text to URL-safe slug.

    Args:
        text: Text to slugify

    Returns:
        URL-safe slug
    """
    # Convert to lowercase
    text = text.lower()
    # Replace spaces and underscores with hyphens
    text = re.sub(r"[\s_]+", "-", text)
    # Remove non-alphanumeric characters except hyphens
    text = re.sub(r"[^a-z0-9\-]", "", text)
    # Remove multiple consecutive hyphens
    text = re.sub(r"-+", "-", text)
    # Strip hyphens from start and end
    return text.strip("-")


def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    if max_length <= len(suffix):
        return text[:max_length]

    return text[: max_length - len(suffix)] + suffix


def sanitize_text(text: str) -> str:
    """
    Sanitize text for safe storage/display.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text
    """
    # Remove control characters
    text = re.sub(r"[\x00-\x1F\x7F]", "", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# Hash Utilities
def hash_string(text: str, algorithm: str = "sha256") -> str:
    """
    Hash a string using specified algorithm.

    Args:
        text: Text to hash
        algorithm: Hash algorithm (sha256, sha512, md5)

    Returns:
        Hex digest of hash
    """
    hasher = hashlib.new(algorithm)
    hasher.update(text.encode("utf-8"))
    return hasher.hexdigest()


def hash_dict(data: dict[str, Any]) -> str:
    """
    Create hash of dictionary contents.

    Args:
        data: Dictionary to hash

    Returns:
        SHA256 hex digest
    """
    import json

    # Sort keys for consistent hashing
    json_str = json.dumps(data, sort_keys=True, default=str)
    return hash_string(json_str)


# Validation Helpers
def is_uuid(value: str) -> bool:
    """Check if string is a valid UUID."""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def is_email(value: str) -> bool:
    """Basic email validation."""
    pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    return bool(pattern.match(value))


def is_url(value: str) -> bool:
    """Basic URL validation."""
    pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return bool(pattern.match(value))


# Range Utilities
def ensure_range(
    value: int | float,
    min_value: int | float | None = None,
    max_value: int | float | None = None,
) -> int | float:
    """
    Ensure value is within range.

    Args:
        value: Value to check
        min_value: Minimum value (inclusive)
        max_value: Maximum value (inclusive)

    Returns:
        Clamped value within range
    """
    if min_value is not None:
        value = max(value, min_value)
    if max_value is not None:
        value = min(value, max_value)
    return value


def ensure_in(value: T, allowed: list[T]) -> T:
    """
    Ensure value is in allowed list.

    Args:
        value: Value to check
        allowed: Allowed values

    Returns:
        Value if allowed

    Raises:
        ValueError: If value not in allowed list
    """
    if value not in allowed:
        raise ValueError(f"Value {value} not in allowed values: {allowed}")
    return value
