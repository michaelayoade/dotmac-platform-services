"""
Shared DateTime Utilities for DotMac Platform Services.

Eliminates timezone import duplication and provides consistent datetime handling
across all middleware and services.
"""

import logging
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from typing import Optional

logger = logging.getLogger(__name__)


class DateTimeUtils:
    """Centralized datetime utilities to eliminate duplication."""

    @staticmethod
    def utc_now() -> datetime:
        """Get current UTC datetime.

        Returns:
            Current datetime in UTC timezone
        """
        return datetime.now(dt_timezone.utc)

    @staticmethod
    def utc_datetime(dt: Optional[datetime] = None) -> datetime:
        """Ensure datetime is in UTC timezone.

        Args:
            dt: Optional datetime to convert. If None, returns current UTC time

        Returns:
            Datetime in UTC timezone
        """
        if dt is None:
            return DateTimeUtils.utc_now()

        if dt.tzinfo is None:
            # Naive datetime - assume it's already UTC
            return dt.replace(tzinfo=dt_timezone.utc)

        # Convert to UTC if needed
        return dt.astimezone(dt_timezone.utc)

    @staticmethod
    def utc_timestamp() -> float:
        """Get current UTC timestamp.

        Returns:
            UTC timestamp as float
        """
        return DateTimeUtils.utc_now().timestamp()

    @staticmethod
    def utc_from_timestamp(timestamp: float) -> datetime:
        """Create UTC datetime from timestamp.

        Args:
            timestamp: Unix timestamp

        Returns:
            UTC datetime object
        """
        return datetime.fromtimestamp(timestamp, dt_timezone.utc)

    @staticmethod
    def add_timedelta(dt: Optional[datetime] = None, **kwargs) -> datetime:
        """Add timedelta to datetime (or current time).

        Args:
            dt: Optional base datetime. If None, uses current UTC time
            **kwargs: Timedelta arguments (days, hours, minutes, seconds, etc.)

        Returns:
            New datetime with timedelta added
        """
        base_dt = dt or DateTimeUtils.utc_now()
        return DateTimeUtils.utc_datetime(base_dt) + timedelta(**kwargs)

    @staticmethod
    def is_expired(expiry_time: datetime, current_time: Optional[datetime] = None) -> bool:
        """Check if a datetime has expired.

        Args:
            expiry_time: Time to check for expiration
            current_time: Optional current time. If None, uses UTC now

        Returns:
            True if expired, False otherwise
        """
        current = current_time or DateTimeUtils.utc_now()
        return DateTimeUtils.utc_datetime(current) > DateTimeUtils.utc_datetime(expiry_time)

    @staticmethod
    def format_iso(dt: Optional[datetime] = None) -> str:
        """Format datetime as ISO string.

        Args:
            dt: Optional datetime to format. If None, uses current UTC time

        Returns:
            ISO formatted datetime string
        """
        target_dt = dt or DateTimeUtils.utc_now()
        return DateTimeUtils.utc_datetime(target_dt).isoformat()

    @staticmethod
    def parse_iso(iso_string: str) -> datetime:
        """Parse ISO datetime string to UTC datetime.

        Args:
            iso_string: ISO formatted datetime string

        Returns:
            UTC datetime object
        """
        try:
            dt = datetime.fromisoformat(iso_string)
            return DateTimeUtils.utc_datetime(dt)
        except ValueError as e:
            logger.error(f"Failed to parse ISO datetime '{iso_string}': {e}")
            raise

    @staticmethod
    def time_until_expiry(expiry_time: datetime, current_time: Optional[datetime] = None) -> timedelta:
        """Get time remaining until expiry.

        Args:
            expiry_time: Expiration datetime
            current_time: Optional current time. If None, uses UTC now

        Returns:
            Timedelta until expiry (negative if already expired)
        """
        current = current_time or DateTimeUtils.utc_now()
        return DateTimeUtils.utc_datetime(expiry_time) - DateTimeUtils.utc_datetime(current)

    @staticmethod
    def create_expiry(ttl_seconds: int, base_time: Optional[datetime] = None) -> datetime:
        """Create expiry datetime from TTL seconds.

        Args:
            ttl_seconds: Time to live in seconds
            base_time: Optional base time. If None, uses current UTC time

        Returns:
            Expiry datetime
        """
        base = base_time or DateTimeUtils.utc_now()
        return DateTimeUtils.utc_datetime(base) + timedelta(seconds=ttl_seconds)


# Convenience functions for common operations
utc_now = DateTimeUtils.utc_now
utc_datetime = DateTimeUtils.utc_datetime
utc_timestamp = DateTimeUtils.utc_timestamp
format_iso = DateTimeUtils.format_iso
parse_iso = DateTimeUtils.parse_iso
is_expired = DateTimeUtils.is_expired


# Common timedelta constants
class TimeDeltas:
    """Common time intervals for reuse."""

    MINUTE = timedelta(minutes=1)
    FIVE_MINUTES = timedelta(minutes=5)
    FIFTEEN_MINUTES = timedelta(minutes=15)
    THIRTY_MINUTES = timedelta(minutes=30)
    HOUR = timedelta(hours=1)
    DAY = timedelta(days=1)
    WEEK = timedelta(weeks=1)
    MONTH = timedelta(days=30)  # Approximate

    # Idempotency key TTLs
    IDEMPOTENCY_SHORT = timedelta(hours=1)
    IDEMPOTENCY_DEFAULT = timedelta(hours=24)
    IDEMPOTENCY_LONG = timedelta(days=7)

    # Session timeouts
    SESSION_IDLE = timedelta(minutes=30)
    SESSION_ABSOLUTE = timedelta(hours=8)

    # API versioning
    DEPRECATION_WARNING = timedelta(days=90)
    SUNSET_PERIOD = timedelta(days=180)


def get_common_expiry(expiry_type: str) -> datetime:
    """Get common expiry times.

    Args:
        expiry_type: Type of expiry ('idempotency', 'session', 'cache', etc.)

    Returns:
        Expiry datetime
    """
    expiry_map = {
        "idempotency": TimeDeltas.IDEMPOTENCY_DEFAULT,
        "idempotency_short": TimeDeltas.IDEMPOTENCY_SHORT,
        "idempotency_long": TimeDeltas.IDEMPOTENCY_LONG,
        "session_idle": TimeDeltas.SESSION_IDLE,
        "session_absolute": TimeDeltas.SESSION_ABSOLUTE,
        "cache": TimeDeltas.HOUR,
        "short_cache": TimeDeltas.FIVE_MINUTES,
        "deprecation": TimeDeltas.DEPRECATION_WARNING,
        "sunset": TimeDeltas.SUNSET_PERIOD,
    }

    ttl = expiry_map.get(expiry_type, TimeDeltas.DAY)
    return DateTimeUtils.utc_now() + ttl