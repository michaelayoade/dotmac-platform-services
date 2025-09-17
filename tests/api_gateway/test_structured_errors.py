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

        # Verify structured error format
        assert "error" in error_data
        assert "message" in error_data["error"]
        assert "type" in error_data["error"]
        assert "code" in error_data["error"]
        assert "timestamp" in error_data["error"]
        assert "request_id" in error_data["error"]

        assert error_data["error"]["message"] == "Invalid request parameter"
        assert error_data["error"]["type"] == "HTTP_EXCEPTION"
        assert error_data["error"]["code"] == 400

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

        # Verify structured error format for validation errors
        assert "error" in error_data
        assert "message" in error_data["error"]
        assert "type" in error_data["error"]
        assert "code" in error_data["error"]
        assert "details" in error_data["error"]
        assert "timestamp" in error_data["error"]
        assert "request_id" in error_data["error"]

        assert error_data["error"]["type"] == "VALIDATION_ERROR"
        assert error_data["error"]["code"] == 422
        assert isinstance(error_data["error"]["details"], list)

    def test_internal_server_error_structured_response(self, test_client):
        """Test that internal server errors return structured payload."""
        @test_client.app.get("/test/server-error")
        async def test_server_error():
            raise ValueError("Internal processing error")

        response = test_client.get("/test/server-error")

        assert response.status_code == 500
        error_data = response.json()

        # Verify structured error format
        assert "error" in error_data
        assert "message" in error_data["error"]
        assert "type" in error_data["error"]
        assert "code" in error_data["error"]
        assert "timestamp" in error_data["error"]
        assert "request_id" in error_data["error"]

        assert error_data["error"]["type"] == "INTERNAL_ERROR"
        assert error_data["error"]["code"] == 500

        # In development mode, detailed errors might be shown
        # In production, generic message should be used
        if "detailed_errors" in test_client.app.state and test_client.app.state.detailed_errors:
            assert "Internal processing error" in error_data["error"]["message"]
        else:
            assert error_data["error"]["message"] == "Internal server error"

    def test_authentication_error_structured_response(self, test_client):
        """Test that authentication errors return structured payload."""
        from dotmac.platform.auth.exceptions import AuthError

        @test_client.app.get("/test/auth-error")
        async def test_auth_error():
            raise AuthError("Invalid token")

        response = test_client.get("/test/auth-error")

        # AuthError should be mapped to 401
        assert response.status_code == 401
        error_data = response.json()

        assert "error" in error_data
        assert error_data["error"]["message"] == "Invalid token"
        assert error_data["error"]["type"] == "AUTHENTICATION_ERROR"
        assert error_data["error"]["code"] == 401

    def test_authorization_error_structured_response(self, test_client):
        """Test that authorization errors return structured payload."""
        from dotmac.platform.auth.exceptions import InsufficientScope

        @test_client.app.get("/test/authz-error")
        async def test_authz_error():
            raise InsufficientScope("Insufficient permissions")

        response = test_client.get("/test/authz-error")

        # InsufficientScope should be mapped to 403
        assert response.status_code == 403
        error_data = response.json()

        assert "error" in error_data
        assert error_data["error"]["message"] == "Insufficient permissions"
        assert error_data["error"]["type"] == "AUTHORIZATION_ERROR"
        assert error_data["error"]["code"] == 403

    def test_rate_limit_error_structured_response(self, test_client):
        """Test that rate limit errors return structured payload."""
        # Mock rate limiting to trigger error
        with patch('dotmac.platform.api_gateway.middleware.rate_limit_middleware') as mock_middleware:
            mock_middleware.side_effect = HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": "60"}
            )

            @test_client.app.get("/test/rate-limit")
            async def test_rate_limit():
                return {"message": "success"}

            response = test_client.get("/test/rate-limit")

            assert response.status_code == 429
            error_data = response.json()

            assert "error" in error_data
            assert error_data["error"]["message"] == "Rate limit exceeded"
            assert error_data["error"]["type"] == "RATE_LIMIT_ERROR"
            assert error_data["error"]["code"] == 429

            # Check that Retry-After header is preserved
            assert response.headers.get("Retry-After") == "60"

    def test_request_id_in_error_response(self, test_client):
        """Test that request ID is included in error responses."""
        @test_client.app.get("/test/error-with-request-id")
        async def test_error():
            raise HTTPException(status_code=400, detail="Test error")

        response = test_client.get("/test/error-with-request-id")

        error_data = response.json()
        request_id = error_data["error"]["request_id"]

        # Request ID should be present and non-empty
        assert request_id
        assert isinstance(request_id, str)
        assert len(request_id) > 0

        # Request ID should also be in response headers
        assert response.headers.get("X-Request-ID") == request_id

    def test_error_correlation_with_logs(self, test_client, caplog):
        """Test that errors are properly logged with correlation IDs."""
        @test_client.app.get("/test/logged-error")
        async def test_logged_error():
            raise ValueError("Test internal error")

        response = test_client.get("/test/logged-error")

        error_data = response.json()
        request_id = error_data["error"]["request_id"]

        # Check that error was logged with request ID
        log_records = [record for record in caplog.records if record.levelname == "ERROR"]
        assert len(log_records) > 0

        # At least one log record should contain the request ID
        assert any(request_id in record.getMessage() for record in log_records)

    def test_error_sanitization_in_production(self, gateway_config):
        """Test that sensitive information is sanitized in production."""
        # Configure for production
        production_config = GatewayConfig.for_production()
        production_config.observability.detailed_errors = False

        gateway = APIGateway(config=production_config)
        test_client = TestClient(gateway.app)

        @test_client.app.get("/test/sensitive-error")
        async def test_sensitive_error():
            # Simulate error with sensitive information
            raise ValueError("Database connection failed: password=secret123")

        response = test_client.get("/test/sensitive-error")

        assert response.status_code == 500
        error_data = response.json()

        # Sensitive information should be sanitized
        assert "password" not in error_data["error"]["message"]
        assert "secret123" not in error_data["error"]["message"]
        assert error_data["error"]["message"] == "Internal server error"

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
                    "error": {
                        "message": exc.message,
                        "type": "BUSINESS_LOGIC_ERROR",
                        "code": 422,
                        "error_code": exc.error_code,
                        "timestamp": "2024-01-01T00:00:00Z",  # Would be actual timestamp
                        "request_id": "test-request-id",
                    }
                }
            )

        @test_client.app.get("/test/custom-error")
        async def test_custom_error():
            raise CustomBusinessError("Invalid business rule", "RULE_001")

        response = test_client.get("/test/custom-error")

        assert response.status_code == 422
        error_data = response.json()

        assert error_data["error"]["type"] == "BUSINESS_LOGIC_ERROR"
        assert error_data["error"]["error_code"] == "RULE_001"
        assert error_data["error"]["message"] == "Invalid business rule"

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
        test_client = TestClient(gateway.app)

        @test_client.app.get("/test/cors-error")
        async def test_cors_error():
            raise HTTPException(status_code=400, detail="Test error")

        response = test_client.get(
            "/test/cors-error",
            headers={"Origin": "https://example.com"}
        )

        assert response.status_code == 400

        # CORS headers should be present even in error responses
        assert "Access-Control-Allow-Origin" in response.headers