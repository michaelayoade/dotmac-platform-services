"""Use tenacity directly - no wrappers needed.

Just import tenacity and use it:
    from tenacity import retry, stop_after_attempt, wait_exponential

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def resilient_function():
        # your code
        pass
"""

# Re-export tenacity for convenience
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

__all__ = [
    "retry",
    "stop_after_attempt",
    "wait_exponential",
    "retry_if_exception_type",
]
