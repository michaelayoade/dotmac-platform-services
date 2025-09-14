"""Generic SMS service with configurable HTTP gateway."""

import base64
import json
import logging
from typing import Any

import httpx
from pydantic import BaseModel, Field, field_validator

from .config import SMSConfig

logger = logging.getLogger(__name__)


class SMSMessage(BaseModel):
    """SMS message model."""

    to: str = Field(..., description="Recipient phone number")
    body: str = Field(..., max_length=1600, description="SMS message body")
    from_number: str | None = Field(None, description="Sender number (if supported)")

    @field_validator("to")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Basic phone validation - just ensure it has digits."""
        # Remove common formatting
        cleaned = "".join(c for c in v if c.isdigit() or c == "+")
        if len(cleaned) < 7:  # Most phone numbers are at least 7 digits
            raise ValueError("Phone number too short")
        return cleaned

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: str) -> str:
        """Validate message body."""
        if not v or not v.strip():
            raise ValueError("Message body cannot be empty")
        return v.strip()


class SMSService:
    """
    Generic SMS service with configurable HTTP gateway.

    Can work with any HTTP-based SMS gateway including:
    - Self-hosted gateways (Kannel, Jasmin, PlaySMS)
    - Generic HTTP APIs
    - Custom implementations
    """

    def __init__(self, config: SMSConfig):
        """
        Initialize SMS service.

        Args:
            config: SMS configuration
        """
        self.config = config
        self._client = httpx.Client(timeout=30.0)

    def _prepare_auth_headers(self) -> dict[str, str]:
        """Prepare authentication headers based on config."""
        headers = self.config.gateway_headers.copy()

        if self.config.gateway_auth_type == "bearer":
            headers["Authorization"] = f"Bearer {self.config.gateway_auth_value}"
        elif self.config.gateway_auth_type == "api_key":
            headers["X-API-Key"] = self.config.gateway_auth_value or ""
        elif self.config.gateway_auth_type == "basic":
            # Assume auth_value is "username:password"
            if self.config.gateway_auth_value and ":" in self.config.gateway_auth_value:
                encoded = base64.b64encode(
                    self.config.gateway_auth_value.encode()
                ).decode()
                headers["Authorization"] = f"Basic {encoded}"

        return headers

    def _prepare_request_data(self, sms: SMSMessage) -> dict[str, Any]:
        """
        Prepare request data for gateway.

        This is a generic format. Override for specific gateways.
        """
        return {
            "to": sms.to,
            "message": sms.body[:self.config.max_length],
            "from": sms.from_number or self.config.from_number,
        }

    def send(self, sms: SMSMessage) -> bool:
        """
        Send SMS via configured gateway.

        Args:
            sms: SMS message to send

        Returns:
            True if sent successfully
        """
        if not self.config.gateway_url:
            logger.warning("SMS gateway not configured")
            return False

        try:
            headers = self._prepare_auth_headers()
            data = self._prepare_request_data(sms)

            # Send request based on configured method
            if self.config.gateway_method == "GET":
                response = self._client.get(
                    self.config.gateway_url,
                    params=data,
                    headers=headers,
                )
            elif self.config.gateway_method == "POST":
                response = self._client.post(
                    self.config.gateway_url,
                    json=data,
                    headers=headers,
                )
            else:  # PUT
                response = self._client.put(
                    self.config.gateway_url,
                    json=data,
                    headers=headers,
                )

            # Check response
            if response.status_code in (200, 201, 202):
                logger.info("SMS sent successfully to %s", sms.to)
                return True
            else:
                logger.error(
                    "SMS gateway returned status %d: %s",
                    response.status_code,
                    response.text[:200],
                )
                return False

        except httpx.HTTPError as e:
            logger.error("HTTP error sending SMS: %s", str(e))
            return False
        except Exception as e:
            logger.error("Error sending SMS: %s", str(e))
            return False

    async def send_async(self, sms: SMSMessage) -> bool:
        """
        Send SMS asynchronously.

        Args:
            sms: SMS message to send

        Returns:
            True if sent successfully
        """
        if not self.config.gateway_url:
            logger.warning("SMS gateway not configured")
            return False

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = self._prepare_auth_headers()
                data = self._prepare_request_data(sms)

                # Send request based on configured method
                if self.config.gateway_method == "GET":
                    response = await client.get(
                        self.config.gateway_url,
                        params=data,
                        headers=headers,
                    )
                elif self.config.gateway_method == "POST":
                    response = await client.post(
                        self.config.gateway_url,
                        json=data,
                        headers=headers,
                    )
                else:  # PUT
                    response = await client.put(
                        self.config.gateway_url,
                        json=data,
                        headers=headers,
                    )

                # Check response
                if response.status_code in (200, 201, 202):
                    logger.info("SMS sent successfully to %s", sms.to)
                    return True
                else:
                    logger.error(
                        "SMS gateway returned status %d: %s",
                        response.status_code,
                        response.text[:200],
                    )
                    return False

        except httpx.HTTPError as e:
            logger.error("HTTP error sending SMS: %s", str(e))
            return False
        except Exception as e:
            logger.error("Error sending SMS: %s", str(e))
            return False

    def send_bulk(self, messages: list[SMSMessage]) -> dict[str, bool]:
        """
        Send multiple SMS messages.

        Args:
            messages: List of SMS messages

        Returns:
            Dictionary mapping phone numbers to success status
        """
        results = {}
        for sms in messages:
            results[sms.to] = self.send(sms)
        return results

    def test_connection(self) -> bool:
        """
        Test SMS gateway connection.

        Returns:
            True if gateway is reachable
        """
        if not self.config.gateway_url:
            logger.warning("SMS gateway not configured")
            return False

        try:
            headers = self._prepare_auth_headers()
            response = self._client.get(
                self.config.gateway_url,
                headers=headers,
                timeout=10.0,
            )
            logger.info(
                "SMS gateway test: status %d",
                response.status_code,
            )
            return response.status_code < 500

        except Exception as e:
            logger.error("SMS gateway test failed: %s", str(e))
            return False

    def __del__(self):
        """Cleanup HTTP client."""
        if hasattr(self, "_client"):
            self._client.close()


class MockSMSService(SMSService):
    """
    Mock SMS service for testing.

    Logs messages instead of sending them.
    """

    def __init__(self):
        """Initialize mock service without config."""
        # Don't call parent __init__
        self.sent_messages: list[SMSMessage] = []

    def send(self, sms: SMSMessage) -> bool:
        """Mock send - just log and store."""
        logger.info("MOCK SMS: To=%s, Body=%s", sms.to, sms.body)
        self.sent_messages.append(sms)
        return True

    async def send_async(self, sms: SMSMessage) -> bool:
        """Mock async send."""
        return self.send(sms)

    def test_connection(self) -> bool:
        """Mock connection test."""
        return True