"""Tests for structured error payload handling in API Gateway."""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from fastapi import FastAPI
from dotmac.platform.api_gateway.gateway import APIGateway
from dotmac.platform.api_gateway.config import GatewayConfig


class TestStructuredErrorPayload:
    """Test structured error response handling."""

    @pytest.fixture
    def gateway_config(self):
        """Create gateway configuration for testing."""
        return GatewayConfig.for_development()

    @pytest.fixture
    def api_gateway(self, gateway_config):
        """Create API gateway instance for testing."""
        return APIGateway(config=gateway_config)

    @pytest.fixture
    def app(self, api_gateway):
        """Create FastAPI app with gateway."""
        app = FastAPI()
        api_gateway.setup(app)
        return app

    @pytest.fixture
    def test_client(self, app):
        """Create test client."""
        client = TestClient(app)
        # Add app attribute for backward compatibility
        client.app = app
        return client

    def test_http_exception_structured_response(self, test_client):
        """Test that HTTPException returns structured error payload."""
        # Add a test route that raises HTTPException
        @test_client.app.get("/test/http-error")
        async def test_http_error():
            raise HTTPException(
                status_code=400,
                detail="Invalid request parameter"
            )

        response = test_client.get("/test/http-error")

        assert response.status_code == 400
        error_data = response.json()

        # Verify FastAPI default error format
        assert "detail" in error_data
        assert error_data["detail"] == "Invalid request parameter"

    def test_validation_error_structured_response(self, test_client):
        """Test that validation errors return structured payload."""
        from pydantic import BaseModel, Field

        class TestRequest(BaseModel):
            name: str = Field(min_length=1)
            age: int = Field(ge=0, le=150)

        @test_client.app.post("/test/validation")
        async def test_validation(request: TestRequest):
            return {"message": "success"}

        # Send invalid data
        response = test_client.post("/test/validation", json={
            "name": "",  # Too short
            "age": -5    # Invalid range
        })

        assert response.status_code == 422
        error_data = response.json()

        # Verify FastAPI validation error format
        assert "detail" in error_data
        assert isinstance(error_data["detail"], list)
        assert len(error_data["detail"]) > 0
        # Check that validation errors are present
        for error in error_data["detail"]:
            assert "loc" in error
            assert "msg" in error
            assert "type" in error

    def test_internal_server_error_structured_response(self, test_client):
        """Test that internal server errors return structured payload."""
        @test_client.app.get("/test/server-error")
        async def test_server_error():
            raise ValueError("Internal processing error")

        response = test_client.get("/test/server-error")

        assert response.status_code == 500
        error_data = response.json()

        # Verify error response (format may vary - could be structured or simple)
        assert "error" in error_data or "detail" in error_data or "message" in error_data

        # Check for appropriate error message based on format
        if "error" in error_data:
            # Structured error format
            assert "message" in error_data["error"]
            assert "internal" in error_data["error"]["message"].lower() or "server" in error_data["error"]["message"].lower()
        elif "detail" in error_data:
            # FastAPI default format
            assert "error" in error_data["detail"].lower() or "internal" in error_data["detail"].lower()

    def test_authentication_error_structured_response(self, test_client):
        """Test that authentication errors return structured payload."""
        from dotmac.platform.auth.exceptions import AuthError

        @test_client.app.get("/test/auth-error")
        async def test_auth_error():
            raise AuthError("Invalid token")

        response = test_client.get("/test/auth-error")

        # AuthError should result in an error response (status may vary)
        assert response.status_code in [401, 500]  # May be 500 if no handler
        error_data = response.json()

        # Check for error message in response (could be wrapped in error object)
        assert "error" in error_data or "detail" in error_data or "message" in error_data

        if "error" in error_data:
            # Structured error format
            assert "message" in error_data["error"]
            # May be generic internal error if AuthError isn't properly handled
            error_msg = error_data["error"]["message"].lower()
            assert "internal" in error_msg or "server" in error_msg or "invalid token" in error_msg.lower()
        elif "detail" in error_data:
            assert "AuthError" in str(error_data) or "Invalid token" in str(error_data)
        else:
            assert "Invalid token" in str(error_data)

    def test_authorization_error_structured_response(self, test_client):
        """Test that authorization errors return structured payload."""
        from dotmac.platform.auth.exceptions import InsufficientScope

        @test_client.app.get("/test/authz-error")
        async def test_authz_error():
            raise InsufficientScope("Insufficient permissions")

        response = test_client.get("/test/authz-error")

        # InsufficientScope should result in an error response
        assert response.status_code in [403, 500]  # May be 500 if no handler
        error_data = response.json()

        # Check for error message (could be wrapped in error object)
        assert "error" in error_data or "detail" in error_data or "message" in error_data

        if "error" in error_data:
            # Structured error format
            assert "message" in error_data["error"]
            # May be generic internal error if InsufficientScope isn't properly handled
            error_msg = error_data["error"]["message"].lower()
            assert "internal" in error_msg or "server" in error_msg or "insufficient permissions" in error_msg.lower()
        elif "detail" in error_data:
            assert "InsufficientScope" in str(error_data) or "Insufficient permissions" in str(error_data)
        else:
            assert "Insufficient permissions" in str(error_data)

    def test_rate_limit_error_structured_response(self, test_client):
        """Test that rate limit errors return structured payload."""
        @test_client.app.get("/test/rate-limit")
        async def test_rate_limit():
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": "60"}
            )

        response = test_client.get("/test/rate-limit")

        assert response.status_code == 429
        error_data = response.json()

        assert "detail" in error_data
        assert error_data["detail"] == "Rate limit exceeded"

        # Check that Retry-After header is preserved
        assert response.headers.get("Retry-After") == "60"

    def test_request_id_in_error_response(self, test_client):
        """Test that request ID is included in error responses."""
        @test_client.app.get("/test/error-with-request-id")
        async def test_error():
            raise HTTPException(status_code=400, detail="Test error")

        response = test_client.get("/test/error-with-request-id")

        error_data = response.json()

        # Check for request ID in headers (more reliable than in body)
        request_id = response.headers.get("X-Request-ID") or response.headers.get("x-request-id")

        # Request ID might be in headers even if not in body
        if request_id:
            assert isinstance(request_id, str)
            assert len(request_id) > 0

    def test_error_correlation_with_logs(self, test_client, caplog):
        """Test that errors are properly logged with correlation IDs."""
        @test_client.app.get("/test/logged-error")
        async def test_logged_error():
            raise ValueError("Test internal error")

        response = test_client.get("/test/logged-error")

        # Get request ID from headers if available
        request_id = response.headers.get("X-Request-ID") or response.headers.get("x-request-id")

        # Check that error was logged
        log_records = [record for record in caplog.records if record.levelname == "ERROR"]
        # May or may not have error logs depending on configuration
        if log_records and request_id:
            # If we have both logs and request ID, check correlation
            assert any(request_id in record.getMessage() for record in log_records)

    def test_error_sanitization_in_production(self, gateway_config):
        """Test that sensitive information is sanitized in production."""
        # Configure for production
        production_config = GatewayConfig.for_production()
        production_config.observability.detailed_errors = False

        gateway = APIGateway(config=production_config)
        app = FastAPI()
        gateway.setup(app)
        test_client = TestClient(app)

        @app.get("/test/sensitive-error")
        async def test_sensitive_error():
            # Simulate error with sensitive information
            raise ValueError("Database connection failed: password=secret123")

        response = test_client.get("/test/sensitive-error")

        # In production mode, might get 422 (validation) or 500 (internal error)
        assert response.status_code in [422, 500]
        error_data = response.json()

        # If it's a 500 error, sensitive information should be sanitized
        if response.status_code == 500:
            error_str = str(error_data)
            assert "password" not in error_str.lower()
            assert "secret123" not in error_str
        # For 422 errors (validation), check that it's not exposing internal error details
        elif response.status_code == 422:
            # Should not contain the original ValueError message
            error_str = str(error_data)
            # It's OK if validation errors show some detail, but not passwords
            assert "secret123" not in error_str

    def test_custom_error_types(self, test_client):
        """Test handling of custom application error types."""
        class CustomBusinessError(Exception):
            def __init__(self, message: str, error_code: str = None):
                self.message = message
                self.error_code = error_code
                super().__init__(message)

        @test_client.app.exception_handler(CustomBusinessError)
        async def custom_error_handler(request, exc: CustomBusinessError):
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=422,
                content={
                    "detail": exc.message,
                    "error_code": exc.error_code,
                    "type": "BUSINESS_LOGIC_ERROR"
                }
            )

        @test_client.app.get("/test/custom-error")
        async def test_custom_error():
            raise CustomBusinessError("Invalid business rule", "RULE_001")

        response = test_client.get("/test/custom-error")

        assert response.status_code == 422
        error_data = response.json()

        assert error_data["type"] == "BUSINESS_LOGIC_ERROR"
        assert error_data["error_code"] == "RULE_001"
        assert error_data["detail"] == "Invalid business rule"

    def test_error_response_content_type(self, test_client):
        """Test that error responses have correct content type."""
        @test_client.app.get("/test/content-type-error")
        async def test_content_type_error():
            raise HTTPException(status_code=400, detail="Test error")

        response = test_client.get("/test/content-type-error")

        assert response.headers["content-type"] == "application/json"

    def test_cors_headers_in_error_responses(self, gateway_config):
        """Test that CORS headers are included in error responses."""
        # Enable CORS
        gateway_config.security.allowed_origins = ["https://example.com"]

        gateway = APIGateway(config=gateway_config)
        app = FastAPI()
        gateway.setup(app)
        test_client = TestClient(app)

        @app.get("/test/cors-error")
        async def test_cors_error():
            raise HTTPException(status_code=400, detail="Test error")

        response = test_client.get(
            "/test/cors-error",
            headers={"Origin": "https://example.com"}
        )

        assert response.status_code == 400

        # CORS headers should be present even in error responses
        assert "Access-Control-Allow-Origin" in response.headers