"""Webhook service for HTTP notifications."""

import hashlib
import hmac
import json
import logging
import time
from typing import Any

import httpx
from pydantic import BaseModel, Field, field_validator

from .config import WebhookConfig

logger = logging.getLogger(__name__)


class WebhookRequest(BaseModel):
    """Webhook request model."""

    url: str = Field(..., description="Webhook endpoint URL")
    method: str = Field("POST", pattern="^(GET|POST|PUT|DELETE|PATCH)$")
    headers: dict[str, str] = Field(default_factory=dict)
    payload: dict[str, Any] | None = Field(None, description="JSON payload")
    params: dict[str, str] | None = Field(None, description="Query parameters")
    timeout: int | None = Field(None, gt=0, description="Request timeout in seconds")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate webhook URL."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class WebhookResponse(BaseModel):
    """Webhook response model."""

    success: bool
    status_code: int | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    body: str | None = None
    error: str | None = None
    duration_ms: float | None = None


class WebhookService:
    """
    Generic webhook service for HTTP notifications.

    Supports:
    - Any HTTP endpoint
    - Request signing (HMAC)
    - Retries with exponential backoff
    - Rate limiting
    """

    def __init__(self, config: WebhookConfig):
        """
        Initialize webhook service.

        Args:
            config: Webhook configuration
        """
        self.config = config
        self._client = httpx.Client(
            timeout=config.timeout,
            verify=config.verify_ssl,
        )

    def _sign_request(self, payload: bytes) -> str:
        """
        Sign request payload with HMAC-SHA256.

        Args:
            payload: Request payload

        Returns:
            Signature string
        """
        if not self.config.signature_secret:
            return ""

        signature = hmac.new(
            self.config.signature_secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        return f"sha256={signature}"

    def _prepare_request(self, webhook: WebhookRequest) -> dict[str, Any]:
        """Prepare request parameters."""
        # Validate URL scheme
        from urllib.parse import urlparse

        parsed = urlparse(webhook.url)
        if parsed.scheme not in self.config.allowed_schemes:
            raise ValueError(
                f"URL scheme {parsed.scheme} not in allowed schemes: "
                f"{self.config.allowed_schemes}"
            )

        # Prepare headers
        headers = webhook.headers.copy()
        headers["User-Agent"] = "DotMac-Platform-Webhook/1.0"

        # Prepare payload
        json_payload = None
        data = None

        if webhook.payload:
            if webhook.method in ("POST", "PUT", "PATCH"):
                json_payload = webhook.payload
                headers["Content-Type"] = "application/json"

                # Add signature if configured
                if self.config.sign_requests:
                    payload_bytes = json.dumps(webhook.payload).encode()
                    signature = self._sign_request(payload_bytes)
                    headers[self.config.signature_header] = signature

        return {
            "method": webhook.method,
            "url": webhook.url,
            "headers": headers,
            "json": json_payload,
            "params": webhook.params,
            "timeout": webhook.timeout or self.config.timeout,
        }

    def send(self, webhook: WebhookRequest) -> WebhookResponse:
        """
        Send webhook request.

        Args:
            webhook: Webhook request

        Returns:
            Webhook response
        """
        start_time = time.time()

        try:
            request_params = self._prepare_request(webhook)
            response = self._client.request(**request_params)

            duration_ms = (time.time() - start_time) * 1000

            logger.info(
                "Webhook sent to %s: status=%d, duration=%.2fms",
                webhook.url,
                response.status_code,
                duration_ms,
            )

            return WebhookResponse(
                success=response.status_code < 400,
                status_code=response.status_code,
                headers=dict(response.headers),
                body=response.text[:1000],  # Limit response size
                duration_ms=duration_ms,
            )

        except httpx.HTTPError as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error("HTTP error sending webhook to %s: %s", webhook.url, str(e))

            return WebhookResponse(
                success=False,
                error=str(e),
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error("Error sending webhook to %s: %s", webhook.url, str(e))

            return WebhookResponse(
                success=False,
                error=str(e),
                duration_ms=duration_ms,
            )

    async def send_async(self, webhook: WebhookRequest) -> WebhookResponse:
        """
        Send webhook request asynchronously.

        Args:
            webhook: Webhook request

        Returns:
            Webhook response
        """
        start_time = time.time()

        try:
            async with httpx.AsyncClient(
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            ) as client:
                request_params = self._prepare_request(webhook)
                response = await client.request(**request_params)

                duration_ms = (time.time() - start_time) * 1000

                logger.info(
                    "Webhook sent to %s: status=%d, duration=%.2fms",
                    webhook.url,
                    response.status_code,
                    duration_ms,
                )

                return WebhookResponse(
                    success=response.status_code < 400,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    body=response.text[:1000],
                    duration_ms=duration_ms,
                )

        except httpx.HTTPError as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error("HTTP error sending webhook to %s: %s", webhook.url, str(e))

            return WebhookResponse(
                success=False,
                error=str(e),
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error("Error sending webhook to %s: %s", webhook.url, str(e))

            return WebhookResponse(
                success=False,
                error=str(e),
                duration_ms=duration_ms,
            )

    def send_with_retry(
        self,
        webhook: WebhookRequest,
        max_retries: int | None = None,
    ) -> WebhookResponse:
        """
        Send webhook with retry logic.

        Args:
            webhook: Webhook request
            max_retries: Maximum retry attempts (uses config default if None)

        Returns:
            Webhook response
        """
        max_retries = max_retries or self.config.max_retries
        retry_delay = self.config.retry_delay

        for attempt in range(max_retries + 1):
            response = self.send(webhook)

            if response.success:
                return response

            if attempt < max_retries:
                # Exponential backoff
                delay = retry_delay * (2**attempt)
                logger.info(
                    "Webhook failed, retrying in %.1fs (attempt %d/%d)",
                    delay,
                    attempt + 1,
                    max_retries,
                )
                time.sleep(delay)

        return response

    async def send_with_retry_async(
        self,
        webhook: WebhookRequest,
        max_retries: int | None = None,
    ) -> WebhookResponse:
        """
        Send webhook with retry logic (async).

        Args:
            webhook: Webhook request
            max_retries: Maximum retry attempts

        Returns:
            Webhook response
        """
        import asyncio

        max_retries = max_retries or self.config.max_retries
        retry_delay = self.config.retry_delay

        for attempt in range(max_retries + 1):
            response = await self.send_async(webhook)

            if response.success:
                return response

            if attempt < max_retries:
                # Exponential backoff
                delay = retry_delay * (2**attempt)
                logger.info(
                    "Webhook failed, retrying in %.1fs (attempt %d/%d)",
                    delay,
                    attempt + 1,
                    max_retries,
                )
                await asyncio.sleep(delay)

        return response

    def test_endpoint(self, url: str) -> bool:
        """
        Test if webhook endpoint is reachable.

        Args:
            url: Webhook URL

        Returns:
            True if reachable
        """
        try:
            response = self._client.head(url, timeout=10.0)
            return response.status_code < 500
        except Exception as e:
            logger.error("Webhook endpoint test failed for %s: %s", url, str(e))
            return False

    def __del__(self):
        """Cleanup HTTP client."""
        if hasattr(self, "_client"):
            self._client.close()