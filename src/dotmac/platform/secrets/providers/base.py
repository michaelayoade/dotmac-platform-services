"""
Base provider implementation with common functionality
"""

from __future__ import annotations

import asyncio

import time
from typing import Any
from urllib.parse import urljoin

import httpx

from ..exceptions import (

    ProviderAuthenticationError,
    ProviderAuthorizationError,
    ProviderConnectionError,
    SecretNotFoundError,
    SecretsProviderError,
)
from dotmac.platform.observability.unified_logging import get_logger

from ..interfaces import SecretsProvider
from ..types import SecretData

logger = get_logger(__name__)

class BaseProvider(SecretsProvider):
    """Enhanced base provider with retry logic and error handling"""

    def __init__(
        self,
        timeout: int = 30,
        retry_attempts: int = 3,
        retry_backoff_factor: float = 2.0,
        max_retry_delay: float = 60.0,
    ) -> None:
        super().__init__()
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_backoff_factor = retry_backoff_factor
        self.max_retry_delay = max_retry_delay
        self._client: httpx.AsyncClient | None = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
            )
        return self._client

    async def _close_http_client(self) -> None:
        """Close HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> BaseProvider:
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit"""
        await self._close_http_client()

    async def _retry_with_backoff(self, operation_name: str, coro: Any) -> Any:
        """
        Execute operation with exponential backoff retry

        Args:
            operation_name: Name of operation for logging
            coro: Coroutine to execute

        Returns:
            Operation result

        Raises:
            SecretsProviderError: If all retry attempts fail
        """
        last_exception = None
        delay = 1.0

        for attempt in range(1, self.retry_attempts + 1):
            try:
                start_time = time.time()
                result = await coro
                duration = (time.time() - start_time) * 1000

                if attempt > 1:
                    logger.info(
                        f"{operation_name} succeeded on attempt {attempt} "
                        f"after {duration:.2f}ms"
                    )

                return result

            except (
                ProviderConnectionError,
                httpx.ConnectError,
                httpx.TimeoutException,
                httpx.ReadTimeout,
                httpx.NetworkError,
            ) as e:
                last_exception = e

                if attempt < self.retry_attempts:
                    logger.warning(
                        f"{operation_name} failed on attempt {attempt}: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * self.retry_backoff_factor, self.max_retry_delay)
                else:
                    logger.error(f"{operation_name} failed after {attempt} attempts: {e}")

            except (
                SecretNotFoundError,
                ProviderAuthenticationError,
                ProviderAuthorizationError,
            ):
                # Don't retry these errors
                raise

            except Exception as e:
                logger.error(f"{operation_name} failed with unexpected error: {e}")
                raise SecretsProviderError(f"{operation_name} failed: {e}") from e

        # All retries exhausted
        raise ProviderConnectionError(
            f"{operation_name} failed after {self.retry_attempts} attempts"
        ) from last_exception

    def _handle_http_error(self, response: httpx.Response, path: str) -> None:
        """
        Handle HTTP error responses

        Args:
            response: HTTP response
            path: Secret path that failed

        Raises:
            Appropriate exception based on status code
        """
        if response.status_code == 404:
            raise SecretNotFoundError(f"Secret not found: {path}")
        if response.status_code == 401:
            raise ProviderAuthenticationError(f"Authentication failed for secret: {path}")
        if response.status_code == 403:
            raise ProviderAuthorizationError(f"Access denied for secret: {path}")
        if response.status_code >= 500:
            raise ProviderConnectionError(
                f"Provider server error {response.status_code} for secret: {path}"
            )
        raise SecretsProviderError(
            f"HTTP {response.status_code} error for secret {path}: " f"{response.text}"
        )

    def _validate_secret_data(self, data: Any, path: str) -> SecretData:
        """
        Validate and normalize secret data

        Args:
            data: Raw secret data
            path: Secret path

        Returns:
            Validated secret data

        Raises:
            SecretsProviderError: If data is invalid
        """
        if not isinstance(data, dict):
            raise SecretsProviderError(
                f"Invalid secret data format for {path}: expected dict, got {type(data)}"
            )

        if not data:
            raise SecretNotFoundError(f"Empty secret data for: {path}")

        return data

    async def get_secret(self, path: str) -> SecretData:
        """Base implementation - should be overridden by subclasses"""
        raise NotImplementedError("Subclasses must implement get_secret")

    async def list_secrets(self, path_prefix: str = "") -> list[str]:
        """Base implementation - should be overridden by subclasses"""
        return []

    async def health_check(self) -> bool:
        """Enhanced health check with error handling"""
        try:
            # Attempt a simple operation
            await self.list_secrets()
            self._healthy = True
            return True
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            self._healthy = False
            return False

class HTTPProviderMixin:
    """Mixin for HTTP-based providers"""

    def _build_url(self, base_url: str, path: str, **params: Any) -> str:
        """Build URL with path and query parameters"""
        url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))

        if params:
            query_params = []
            for key, value in params.items():
                if value is not None:
                    query_params.append(f"{key}={value}")

            if query_params:
                separator = "&" if "?" in url else "?"
                url += separator + "&".join(query_params)

        return url

    def _get_headers(
        self, token: str | None = None, additional_headers: dict[str, str] | None = None
    ) -> dict[str, str]:
        """Get HTTP headers with authentication"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "dotmac-secrets/1.0.0",
        }

        if token:
            headers["Authorization"] = f"Bearer {token}"

        if additional_headers:
            headers.update(additional_headers)

        return headers

class RetryableError(Exception):
    """Exception that should trigger retry logic"""

class NonRetryableError(Exception):
    """Exception that should not trigger retry logic"""
