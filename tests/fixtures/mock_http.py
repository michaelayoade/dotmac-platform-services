"""
Mock HTTP Client Fixtures for Testing
Provides aiohttp and httpx client mocks for external service testing.
"""

import json
from typing import Any, Dict, List, Optional, Union
from unittest.mock import AsyncMock, Mock
from urllib.parse import parse_qs, urlparse

import pytest


class MockHTTPResponse:
    """Mock HTTP response for both aiohttp and httpx."""

    def __init__(
        self,
        status: int = 200,
        json_data: Optional[Dict[str, Any]] = None,
        text: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        content: Optional[bytes] = None
    ):
        self.status = status
        self.status_code = status  # httpx compatibility
        self._json_data = json_data
        self._text = text or (json.dumps(json_data) if json_data else "")
        self._content = content or self._text.encode() if self._text else b""
        self.headers = headers or {}
        self.url = None
        self.method = None
        self.ok = 200 <= status < 300
        self.is_success = self.ok
        self.encoding = "utf-8"

    async def json(self) -> Dict[str, Any]:
        """Get JSON response."""
        if self._json_data is not None:
            return self._json_data
        return json.loads(self._text) if self._text else {}

    async def text(self) -> str:
        """Get text response."""
        return self._text

    async def read(self) -> bytes:
        """Read raw bytes."""
        return self._content

    @property
    def content(self) -> bytes:
        """Get content (httpx style)."""
        return self._content

    def raise_for_status(self):
        """Raise exception if status is error."""
        if not self.ok:
            raise MockHTTPError(f"HTTP {self.status}: Error", response=self)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass


class MockHTTPError(Exception):
    """Mock HTTP error exception."""

    def __init__(self, message: str, response: Optional[MockHTTPResponse] = None):
        super().__init__(message)
        self.response = response
        self.status = response.status if response else None


class MockHTTPSession:
    """Mock aiohttp-style session."""

    def __init__(self, default_response: Optional[MockHTTPResponse] = None):
        self.default_response = default_response or MockHTTPResponse()
        self.responses: Dict[str, Union[MockHTTPResponse, List[MockHTTPResponse]]] = {}
        self.call_history: List[Dict[str, Any]] = []
        self.closed = False
        self.headers = {}
        self.cookies = {}

    def add_response(
        self,
        url: str,
        response: Union[MockHTTPResponse, List[MockHTTPResponse]],
        method: str = "GET"
    ):
        """Add mock response for URL."""
        key = f"{method}:{url}"
        self.responses[key] = response

    async def request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> MockHTTPResponse:
        """Make HTTP request."""
        self.call_history.append({
            "method": method,
            "url": url,
            "kwargs": kwargs
        })

        key = f"{method}:{url}"

        # Check for exact match
        if key in self.responses:
            response = self.responses[key]
            if isinstance(response, list):
                # Pop first response from list
                if response:
                    return response.pop(0)
                return self.default_response
            return response

        # Check for wildcard matches
        for pattern, response in self.responses.items():
            if "*" in pattern:
                pattern_method, pattern_url = pattern.split(":", 1)
                if pattern_method == method or pattern_method == "*":
                    if pattern_url == "*" or url.startswith(pattern_url.replace("*", "")):
                        if isinstance(response, list) and response:
                            return response.pop(0)
                        elif not isinstance(response, list):
                            return response

        return self.default_response

    async def get(self, url: str, **kwargs) -> MockHTTPResponse:
        """GET request."""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> MockHTTPResponse:
        """POST request."""
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> MockHTTPResponse:
        """PUT request."""
        return await self.request("PUT", url, **kwargs)

    async def patch(self, url: str, **kwargs) -> MockHTTPResponse:
        """PATCH request."""
        return await self.request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> MockHTTPResponse:
        """DELETE request."""
        return await self.request("DELETE", url, **kwargs)

    async def head(self, url: str, **kwargs) -> MockHTTPResponse:
        """HEAD request."""
        return await self.request("HEAD", url, **kwargs)

    async def close(self):
        """Close session."""
        self.closed = True

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class MockAsyncHTTPClient:
    """Mock httpx-style async client."""

    def __init__(self, default_response: Optional[MockHTTPResponse] = None):
        self.default_response = default_response or MockHTTPResponse()
        self.responses: Dict[str, Union[MockHTTPResponse, List[MockHTTPResponse]]] = {}
        self.call_history: List[Dict[str, Any]] = []
        self.closed = False
        self.base_url = None
        self.headers = {}
        self.timeout = None
        self.follow_redirects = True

    def add_response(
        self,
        url: str,
        response: Union[MockHTTPResponse, List[MockHTTPResponse]],
        method: str = "GET"
    ):
        """Add mock response for URL."""
        key = f"{method}:{url}"
        self.responses[key] = response

    async def request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> MockHTTPResponse:
        """Make HTTP request."""
        # Handle base URL
        if self.base_url and not url.startswith(("http://", "https://")):
            url = f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"

        self.call_history.append({
            "method": method,
            "url": url,
            "kwargs": kwargs
        })

        key = f"{method}:{url}"

        # Check for exact match
        if key in self.responses:
            response = self.responses[key]
            if isinstance(response, list):
                if response:
                    return response.pop(0)
                return self.default_response
            return response

        # Check for wildcard matches
        for pattern, response in self.responses.items():
            if "*" in pattern:
                pattern_method, pattern_url = pattern.split(":", 1)
                if pattern_method == method or pattern_method == "*":
                    if pattern_url == "*" or url.startswith(pattern_url.replace("*", "")):
                        if isinstance(response, list) and response:
                            return response.pop(0)
                        elif not isinstance(response, list):
                            return response

        return self.default_response

    async def get(self, url: str, **kwargs) -> MockHTTPResponse:
        """GET request."""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> MockHTTPResponse:
        """POST request."""
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> MockHTTPResponse:
        """PUT request."""
        return await self.request("PUT", url, **kwargs)

    async def patch(self, url: str, **kwargs) -> MockHTTPResponse:
        """PATCH request."""
        return await self.request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> MockHTTPResponse:
        """DELETE request."""
        return await self.request("DELETE", url, **kwargs)

    async def stream(self, method: str, url: str, **kwargs):
        """Stream request (returns async generator)."""
        response = await self.request(method, url, **kwargs)

        async def generator():
            yield response._content

        return generator()

    async def aclose(self):
        """Close client."""
        self.closed = True

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.aclose()


class MockWebSocket:
    """Mock WebSocket connection."""

    def __init__(self):
        self.messages_to_receive: List[Any] = []
        self.sent_messages: List[Any] = []
        self.closed = False
        self.close_code = None
        self.close_reason = None

    async def send(self, message: Union[str, bytes]):
        """Send message."""
        self.sent_messages.append(message)

    async def send_str(self, message: str):
        """Send string message."""
        await self.send(message)

    async def send_bytes(self, message: bytes):
        """Send bytes message."""
        await self.send(message)

    async def send_json(self, data: Any):
        """Send JSON message."""
        await self.send(json.dumps(data))

    async def receive(self) -> Union[str, bytes]:
        """Receive message."""
        if self.messages_to_receive:
            return self.messages_to_receive.pop(0)
        raise Exception("No messages to receive")

    async def receive_str(self) -> str:
        """Receive string message."""
        message = await self.receive()
        return message if isinstance(message, str) else message.decode()

    async def receive_bytes(self) -> bytes:
        """Receive bytes message."""
        message = await self.receive()
        return message if isinstance(message, bytes) else message.encode()

    async def receive_json(self) -> Any:
        """Receive JSON message."""
        message = await self.receive_str()
        return json.loads(message)

    async def close(self, code: int = 1000, reason: str = ""):
        """Close WebSocket."""
        self.closed = True
        self.close_code = code
        self.close_reason = reason

    def add_message(self, message: Union[str, bytes]):
        """Add message to be received."""
        self.messages_to_receive.append(message)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if not self.closed:
            await self.close()


class MockOAuth2Client:
    """Mock OAuth2 client for testing OAuth flows."""

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.refresh_token = None
        self.call_history: List[Dict[str, Any]] = []

    async def get_authorization_url(
        self,
        redirect_uri: str,
        scope: Optional[List[str]] = None,
        state: Optional[str] = None
    ) -> str:
        """Get authorization URL."""
        self.call_history.append({
            "method": "get_authorization_url",
            "args": {"redirect_uri": redirect_uri, "scope": scope, "state": state}
        })
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(scope or []),
        }
        if state:
            params["state"] = state

        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"https://oauth.example.com/authorize?{query}"

    async def exchange_code(
        self,
        code: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """Exchange authorization code for token."""
        self.call_history.append({
            "method": "exchange_code",
            "args": {"code": code, "redirect_uri": redirect_uri}
        })

        self.token = f"access_token_{code}"
        self.refresh_token = f"refresh_token_{code}"

        return {
            "access_token": self.token,
            "refresh_token": self.refresh_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "read write",
        }

    async def refresh(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token."""
        self.call_history.append({
            "method": "refresh",
            "args": {"refresh_token": refresh_token}
        })

        self.token = f"new_access_token_{refresh_token}"

        return {
            "access_token": self.token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "read write",
        }

    async def revoke(self, token: str) -> bool:
        """Revoke token."""
        self.call_history.append({
            "method": "revoke",
            "args": {"token": token}
        })

        if token == self.token:
            self.token = None
        elif token == self.refresh_token:
            self.refresh_token = None

        return True

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user info with access token."""
        self.call_history.append({
            "method": "get_user_info",
            "args": {"access_token": access_token}
        })

        return {
            "id": "user123",
            "email": "user@example.com",
            "name": "Test User",
            "picture": "https://example.com/picture.jpg",
        }


@pytest.fixture
def mock_http_response():
    """Fixture providing a mock HTTP response."""
    return MockHTTPResponse()


@pytest.fixture
def mock_http_session():
    """Fixture providing a mock aiohttp-style session."""
    return MockHTTPSession()


@pytest.fixture
def mock_async_http_client():
    """Fixture providing a mock httpx-style client."""
    return MockAsyncHTTPClient()


@pytest.fixture
def mock_websocket():
    """Fixture providing a mock WebSocket connection."""
    return MockWebSocket()


@pytest.fixture
def mock_oauth2_client():
    """Fixture providing a mock OAuth2 client."""
    return MockOAuth2Client(
        client_id="test_client_id",
        client_secret="test_client_secret"
    )


@pytest.fixture
def mock_http_session_with_responses():
    """Fixture providing a mock session with pre-configured responses."""
    session = MockHTTPSession()

    # Add common API responses
    session.add_response(
        "https://api.example.com/users/me",
        MockHTTPResponse(json_data={"id": "123", "name": "Test User"})
    )

    session.add_response(
        "https://api.example.com/auth/token",
        MockHTTPResponse(json_data={"token": "test_token", "expires_in": 3600}),
        method="POST"
    )

    # Add error response
    session.add_response(
        "https://api.example.com/error",
        MockHTTPResponse(status=500, text="Internal Server Error")
    )

    return session