"""
Comprehensive tests for auth.edge_validation module.

Tests the EdgeJWTValidator and EdgeAuthMiddleware classes for edge authentication.
"""

import re
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import Request
from starlette.responses import JSONResponse

from dotmac.platform.auth.edge_validation import (
    COMMON_SENSITIVITY_PATTERNS,
    DEVELOPMENT_PATTERNS,
    PRODUCTION_PATTERNS,
    EdgeAuthMiddleware,
    EdgeJWTValidator,
    SensitivityLevel,
    create_edge_validator,
)
from dotmac.platform.auth.exceptions import (
    AuthError,
    InsufficientRole,
    InsufficientScope,
    TenantMismatch,
    TokenNotFound,
)
from dotmac.platform.auth.jwt_service import JWTService


class TestSensitivityLevel:
    """Test SensitivityLevel constants."""

    def test_sensitivity_levels_defined(self):
        """Test that all sensitivity levels are defined correctly."""
        assert SensitivityLevel.PUBLIC == "public"
        assert SensitivityLevel.AUTHENTICATED == "authenticated"
        assert SensitivityLevel.SENSITIVE == "sensitive"
        assert SensitivityLevel.ADMIN == "admin"
        assert SensitivityLevel.INTERNAL == "internal"

    def test_sensitivity_levels_are_strings(self):
        """Test that all sensitivity levels are string constants."""
        levels = [
            SensitivityLevel.PUBLIC,
            SensitivityLevel.AUTHENTICATED,
            SensitivityLevel.SENSITIVE,
            SensitivityLevel.ADMIN,
            SensitivityLevel.INTERNAL,
        ]

        for level in levels:
            assert isinstance(level, str)
            assert len(level) > 0


class TestEdgeJWTValidator:
    """Test EdgeJWTValidator class."""

    @pytest.fixture
    def mock_jwt_service(self):
        """Create mock JWT service."""
        jwt_service = Mock(spec=JWTService)
        jwt_service.verify_token = Mock()
        return jwt_service

    @pytest.fixture
    def mock_tenant_resolver(self):
        """Create mock tenant resolver."""
        return Mock(return_value="tenant-123")

    @pytest.fixture
    def validator(self, mock_jwt_service):
        """Create EdgeJWTValidator instance."""
        return EdgeJWTValidator(
            jwt_service=mock_jwt_service,
            default_sensitivity=SensitivityLevel.AUTHENTICATED,
            require_https=True,
        )

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/test"
        request.url.scheme = "https"
        request.method = "GET"
        request.headers = {}
        request.cookies = {}
        request.client = Mock()
        request.client.host = "example.com"
        return request

    def test_validator_initialization(self, mock_jwt_service):
        """Test validator initialization."""
        validator = EdgeJWTValidator(
            jwt_service=mock_jwt_service,
            default_sensitivity=SensitivityLevel.SENSITIVE,
            require_https=False,
        )

        assert validator.jwt_service is mock_jwt_service
        assert validator.default_sensitivity == SensitivityLevel.SENSITIVE
        assert validator.require_https is False
        assert validator.tenant_resolver is None

    def test_validator_initialization_with_tenant_resolver(
        self, mock_jwt_service, mock_tenant_resolver
    ):
        """Test validator initialization with tenant resolver."""
        validator = EdgeJWTValidator(
            jwt_service=mock_jwt_service,
            tenant_resolver=mock_tenant_resolver,
        )

        assert validator.tenant_resolver is mock_tenant_resolver

    def test_configure_sensitivity_patterns(self, validator):
        """Test configuring sensitivity patterns."""
        patterns = {
            (r"/api/public/.*", r"GET"): SensitivityLevel.PUBLIC,
            (r"/api/admin/.*", r".*"): SensitivityLevel.ADMIN,
        }

        validator.configure_sensitivity_patterns(patterns)

        assert len(validator.sensitivity_patterns) == 2
        assert len(validator._compiled_patterns) == 2  # type: ignore[reportPrivateUsage]

        # Check that patterns are stored correctly
        assert (
            r"/api/public/.*",
            r"GET",
            SensitivityLevel.PUBLIC,
        ) in validator.sensitivity_patterns
        assert (r"/api/admin/.*", r".*", SensitivityLevel.ADMIN) in validator.sensitivity_patterns

    def test_add_sensitivity_pattern(self, validator):
        """Test adding individual sensitivity pattern."""
        validator.add_sensitivity_pattern(r"/api/test/.*", r"POST", SensitivityLevel.SENSITIVE)

        assert len(validator.sensitivity_patterns) == 1
        assert len(validator._compiled_patterns) == 1  # type: ignore[reportPrivateUsage]
        assert validator.sensitivity_patterns[0] == (
            r"/api/test/.*",
            r"POST",
            SensitivityLevel.SENSITIVE,
        )

    def test_get_route_sensitivity_default(self, validator):
        """Test getting route sensitivity with default level."""
        sensitivity = validator.get_route_sensitivity("/api/unknown", "GET")
        assert sensitivity == SensitivityLevel.AUTHENTICATED

    def test_get_route_sensitivity_matched_pattern(self, validator):
        """Test getting route sensitivity with matched pattern."""
        validator.add_sensitivity_pattern(r"/api/public/.*", r"GET", SensitivityLevel.PUBLIC)

        sensitivity = validator.get_route_sensitivity("/api/public/info", "GET")
        assert sensitivity == SensitivityLevel.PUBLIC

    def test_get_route_sensitivity_pattern_priority(self, validator):
        """Test that first matching pattern takes priority."""
        validator.add_sensitivity_pattern(r"/api/.*", r".*", SensitivityLevel.PUBLIC)
        validator.add_sensitivity_pattern(r"/api/admin/.*", r".*", SensitivityLevel.ADMIN)

        # First pattern should match
        sensitivity = validator.get_route_sensitivity("/api/admin/users", "POST")
        assert sensitivity == SensitivityLevel.PUBLIC

    def test_extract_token_from_authorization_header(self, validator, mock_request):
        """Test extracting token from Authorization header."""
        mock_request.headers = {"Authorization": "Bearer test-token-123"}

        token = validator.extract_token_from_request(mock_request)
        assert token == "test-token-123"

    def test_extract_token_from_cookies(self, validator, mock_request):
        """Test extracting token from cookies."""
        mock_request.headers = {}
        mock_request.cookies = {"access_token": "cookie-token-456"}

        token = validator.extract_token_from_request(mock_request)
        assert token == "cookie-token-456"

    def test_extract_token_from_custom_header(self, validator, mock_request):
        """Test extracting token from custom header."""
        mock_request.headers = {"X-Auth-Token": "custom-token-789"}
        mock_request.cookies = {}

        token = validator.extract_token_from_request(mock_request)
        assert token == "custom-token-789"

    def test_extract_token_priority_order(self, validator, mock_request):
        """Test token extraction priority order."""
        mock_request.headers = {
            "Authorization": "Bearer auth-token",
            "X-Auth-Token": "custom-token",
        }
        mock_request.cookies = {"access_token": "cookie-token"}

        token = validator.extract_token_from_request(mock_request)
        assert token == "auth-token"  # Authorization header has priority

    def test_extract_token_no_token_found(self, validator, mock_request):
        """Test token extraction when no token is found."""
        mock_request.headers = {}
        mock_request.cookies = {}

        token = validator.extract_token_from_request(mock_request)
        assert token is None

    def test_extract_token_invalid_authorization_header(self, validator, mock_request):
        """Test token extraction with invalid Authorization header."""
        mock_request.headers = {"Authorization": "Basic dGVzdDp0ZXN0"}

        token = validator.extract_token_from_request(mock_request)
        assert token is None

    def test_extract_service_token(self, validator, mock_request):
        """Test extracting service token."""
        mock_request.headers = {"X-Service-Token": "service-token-123"}

        token = validator.extract_service_token(mock_request)
        assert token == "service-token-123"

    def test_extract_service_token_not_found(self, validator, mock_request):
        """Test extracting service token when not found."""
        mock_request.headers = {}

        token = validator.extract_service_token(mock_request)
        assert token is None

    @pytest.mark.asyncio
    async def test_validate_public_route(self, validator, mock_request):
        """Test validating public route."""
        validator.add_sensitivity_pattern(r"/api/public/.*", r".*", SensitivityLevel.PUBLIC)
        mock_request.url.path = "/api/public/info"

        result = await validator.validate(mock_request)

        assert result["user_id"] is None
        assert result["scopes"] == []
        assert result["authenticated"] is False

    @pytest.mark.asyncio
    async def test_validate_https_requirement_success(self, validator, mock_request):
        """Test HTTPS requirement validation success."""
        mock_request.url.scheme = "https"
        validator.add_sensitivity_pattern(r"/api/test", r".*", SensitivityLevel.PUBLIC)

        result = await validator.validate(mock_request)
        assert result is not None

    @pytest.mark.asyncio
    async def test_validate_https_requirement_failure(self, validator, mock_request):
        """Test HTTPS requirement validation failure."""
        mock_request.url.scheme = "http"
        mock_request.client.host = "example.com"  # Not localhost

        with pytest.raises(AuthError, match="HTTPS required"):
            await validator.validate(mock_request)

    @pytest.mark.asyncio
    async def test_validate_https_localhost_exception(self, validator, mock_request):
        """Test HTTPS requirement exception for localhost."""
        mock_request.url.scheme = "http"
        mock_request.client.host = "127.0.0.1"
        validator.add_sensitivity_pattern(r"/api/test", r".*", SensitivityLevel.PUBLIC)

        result = await validator.validate(mock_request)
        assert result is not None

    @pytest.mark.asyncio
    async def test_validate_https_health_endpoint_exception(self, validator, mock_request):
        """Test HTTPS requirement exception for health endpoints."""
        mock_request.url.scheme = "http"
        mock_request.url.path = "/health"
        mock_request.client.host = "example.com"
        validator.add_sensitivity_pattern(r"/health", r".*", SensitivityLevel.PUBLIC)

        result = await validator.validate(mock_request)
        assert result is not None

    @pytest.mark.asyncio
    async def test_validate_internal_route_with_service_token(self, validator, mock_request):
        """Test validating internal route with service token."""
        validator.add_sensitivity_pattern(r"/internal/.*", r".*", SensitivityLevel.INTERNAL)
        mock_request.url.path = "/internal/api"
        mock_request.headers = {"X-Service-Token": "service-token"}

        result = await validator.validate(mock_request)

        assert result["service_name"] == "unknown"
        assert result["authenticated"] is True
        assert result["is_service"] is True

    @pytest.mark.asyncio
    async def test_validate_internal_route_no_service_token(self, validator, mock_request):
        """Test validating internal route without service token."""
        validator.add_sensitivity_pattern(r"/internal/.*", r".*", SensitivityLevel.INTERNAL)
        mock_request.url.path = "/internal/api"

        with pytest.raises(TokenNotFound, match="Service token required"):
            await validator.validate(mock_request)

    @pytest.mark.asyncio
    async def test_validate_user_request_success(self, validator, mock_request, mock_jwt_service):
        """Test successful user request validation."""
        mock_request.headers = {"Authorization": "Bearer test-token"}
        mock_jwt_service.verify_token.return_value = {
            "sub": "user123",
            "scopes": ["read", "write"],
            "tenant_id": "tenant456",
        }

        result = await validator.validate(mock_request)

        assert result["sub"] == "user123"
        assert result["authenticated"] is True
        assert result["is_service"] is False

    @pytest.mark.asyncio
    async def test_validate_user_request_no_token(self, validator, mock_request):
        """Test user request validation without token."""
        with pytest.raises(TokenNotFound, match="Authentication token required"):
            await validator.validate(mock_request)

    @pytest.mark.asyncio
    async def test_validate_user_request_invalid_token(
        self, validator, mock_request, mock_jwt_service
    ):
        """Test user request validation with invalid token."""
        mock_request.headers = {"Authorization": "Bearer invalid-token"}
        mock_jwt_service.verify_token.side_effect = AuthError("Invalid token")

        with pytest.raises(AuthError, match="Invalid token"):
            await validator.validate(mock_request)

    @pytest.mark.asyncio
    async def test_validate_tenant_mismatch(
        self, validator, mock_request, mock_jwt_service, mock_tenant_resolver
    ):
        """Test tenant mismatch validation."""
        validator.tenant_resolver = mock_tenant_resolver
        mock_tenant_resolver.return_value = "expected-tenant"

        mock_request.headers = {"Authorization": "Bearer test-token"}
        mock_jwt_service.verify_token.return_value = {
            "sub": "user123",
            "tenant_id": "wrong-tenant",
        }

        with pytest.raises(TenantMismatch):
            await validator.validate(mock_request)

    @pytest.mark.asyncio
    async def test_check_sensitivity_requirements_authenticated(self, validator):
        """Test sensitivity requirements for authenticated level."""
        claims = {"sub": "user123", "scopes": [], "roles": []}

        # Should not raise any exception
        await validator._check_sensitivity_requirements(claims, SensitivityLevel.AUTHENTICATED)  # type: ignore[reportPrivateUsage]

    @pytest.mark.asyncio
    async def test_check_sensitivity_requirements_sensitive_success(self, validator):
        """Test sensitivity requirements for sensitive level - success."""
        claims = {"sub": "user123", "scopes": ["read:sensitive"], "roles": []}

        # Should not raise any exception
        await validator._check_sensitivity_requirements(claims, SensitivityLevel.SENSITIVE)  # type: ignore[reportPrivateUsage]

    @pytest.mark.asyncio
    async def test_check_sensitivity_requirements_sensitive_failure(self, validator):
        """Test sensitivity requirements for sensitive level - failure."""
        claims = {"sub": "user123", "scopes": ["read:basic"], "roles": []}

        with pytest.raises(InsufficientScope):
            await validator._check_sensitivity_requirements(claims, SensitivityLevel.SENSITIVE)  # type: ignore[reportPrivateUsage]

    @pytest.mark.asyncio
    async def test_check_sensitivity_requirements_admin_role_success(self, validator):
        """Test admin sensitivity requirements with admin role."""
        claims = {"sub": "user123", "scopes": [], "roles": ["admin"]}

        # Should not raise any exception
        await validator._check_sensitivity_requirements(claims, SensitivityLevel.ADMIN)  # type: ignore[reportPrivateUsage]

    @pytest.mark.asyncio
    async def test_check_sensitivity_requirements_admin_scope_success(self, validator):
        """Test admin sensitivity requirements with admin scope."""
        claims = {"sub": "user123", "scopes": ["admin:read"], "roles": []}

        # Should not raise any exception
        await validator._check_sensitivity_requirements(claims, SensitivityLevel.ADMIN)  # type: ignore[reportPrivateUsage]

    @pytest.mark.asyncio
    async def test_check_sensitivity_requirements_admin_failure(self, validator):
        """Test admin sensitivity requirements failure."""
        claims = {"sub": "user123", "scopes": ["read:basic"], "roles": ["user"]}

        with pytest.raises(InsufficientRole):
            await validator._check_sensitivity_requirements(claims, SensitivityLevel.ADMIN)  # type: ignore[reportPrivateUsage]


class TestEdgeAuthMiddleware:
    """Test EdgeAuthMiddleware class."""

    @pytest.fixture
    def mock_validator(self):
        """Create mock EdgeJWTValidator."""
        validator = Mock(spec=EdgeJWTValidator)
        validator.validate = AsyncMock()
        return validator

    @pytest.fixture
    def mock_app(self):
        """Create mock ASGI app."""
        return Mock()

    @pytest.fixture
    def middleware(self, mock_app, mock_validator):
        """Create EdgeAuthMiddleware instance."""
        return EdgeAuthMiddleware(
            app=mock_app,
            validator=mock_validator,
            service_name="test-service",
        )

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/test"
        request.headers = Mock()
        request.headers.update = Mock()
        request.state = Mock()
        return request

    def test_middleware_initialization(self, mock_app, mock_validator):
        """Test middleware initialization."""
        middleware = EdgeAuthMiddleware(
            app=mock_app,
            validator=mock_validator,
            service_name="test-service",
            skip_paths=["/custom"],
        )

        assert middleware.app is mock_app
        assert middleware.validator is mock_validator
        assert middleware.service_name == "test-service"
        assert "/custom" in middleware.skip_paths

    def test_middleware_default_skip_paths(self, mock_app, mock_validator):
        """Test middleware default skip paths."""
        middleware = EdgeAuthMiddleware(
            app=mock_app,
            validator=mock_validator,
            service_name="test-service",
        )

        expected_paths = ["/docs", "/openapi.json", "/favicon.ico"]
        for path in expected_paths:
            assert path in middleware.skip_paths

    @pytest.mark.asyncio
    async def test_dispatch_skip_path(self, middleware, mock_request):
        """Test middleware skips authentication for configured paths."""
        mock_request.url.path = "/docs"
        call_next = AsyncMock(return_value=JSONResponse({"status": "ok"}))

        await middleware.dispatch(mock_request, call_next)

        # Should call next without validation
        call_next.assert_called_once_with(mock_request)
        middleware.validator.validate.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_successful_authentication(
        self, middleware, mock_request, mock_validator
    ):
        """Test successful authentication through middleware."""
        mock_validator.validate.return_value = {
            "sub": "user123",
            "scopes": ["read", "write"],
            "tenant_id": "tenant456",
            "authenticated": True,
        }
        call_next = AsyncMock(return_value=JSONResponse({"status": "ok"}))

        await middleware.dispatch(mock_request, call_next)

        # Verify claims are set on request state
        assert mock_request.state.user_claims is not None
        assert mock_request.state.authenticated is True

        # Verify headers are NOT updated (middleware doesn't modify headers as they're immutable)
        mock_request.headers.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_unauthenticated_request(self, middleware, mock_request, mock_validator):
        """Test unauthenticated request through middleware."""
        mock_validator.validate.return_value = {
            "user_id": None,
            "authenticated": False,
        }
        call_next = AsyncMock(return_value=JSONResponse({"status": "ok"}))

        await middleware.dispatch(mock_request, call_next)

        # Headers should not be updated for unauthenticated requests
        mock_request.headers.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_authentication_error(self, middleware, mock_request, mock_validator):
        """Test middleware handling authentication errors."""
        mock_validator.validate.side_effect = TokenNotFound("No token")

        response = await middleware.dispatch(mock_request, Mock())

        # Should return error response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_dispatch_unexpected_error(self, middleware, mock_request, mock_validator):
        """Test middleware handling unexpected errors."""
        mock_validator.validate.side_effect = Exception("Unexpected error")

        response = await middleware.dispatch(mock_request, Mock())

        # Should convert to AuthError and return error response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_dispatch_custom_error_handler(self, mock_app, mock_validator, mock_request):
        """Test middleware with custom error handler."""
        custom_error_handler = AsyncMock(return_value=JSONResponse({"custom": "error"}))
        middleware = EdgeAuthMiddleware(
            app=mock_app,
            validator=mock_validator,
            service_name="test-service",
            error_handler=custom_error_handler,
        )

        mock_validator.validate.side_effect = AuthError("Test error")

        response = await middleware.dispatch(mock_request, Mock())

        # Custom error handler should be called
        custom_error_handler.assert_called_once()
        assert response.body == b'{"custom":"error"}'

    @pytest.mark.asyncio
    async def test_default_error_handler(self, middleware, mock_request):
        """Test default error handler."""
        error = TokenNotFound("Token not found")

        response = await middleware._default_error_handler(mock_request, error)  # type: ignore[reportPrivateUsage]

        assert isinstance(response, JSONResponse)
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers
        assert "X-Auth-Error" in response.headers


class TestPredefinedPatterns:
    """Test predefined sensitivity patterns."""

    def test_common_sensitivity_patterns(self):
        """Test common sensitivity patterns are defined."""
        assert isinstance(COMMON_SENSITIVITY_PATTERNS, dict)
        assert len(COMMON_SENSITIVITY_PATTERNS) > 0

        # Test some expected patterns
        health_pattern = (r"/health", r"GET")
        assert health_pattern in COMMON_SENSITIVITY_PATTERNS
        assert COMMON_SENSITIVITY_PATTERNS[health_pattern] == SensitivityLevel.PUBLIC

    def test_development_patterns(self):
        """Test development patterns include common patterns."""
        assert isinstance(DEVELOPMENT_PATTERNS, dict)

        # Should include all common patterns
        for pattern, sensitivity in COMMON_SENSITIVITY_PATTERNS.items():
            assert pattern in DEVELOPMENT_PATTERNS
            assert DEVELOPMENT_PATTERNS[pattern] == sensitivity

    def test_production_patterns(self):
        """Test production patterns include common patterns."""
        assert isinstance(PRODUCTION_PATTERNS, dict)

        # Should include all common patterns
        for pattern, sensitivity in COMMON_SENSITIVITY_PATTERNS.items():
            assert pattern in PRODUCTION_PATTERNS
            assert PRODUCTION_PATTERNS[pattern] == sensitivity


class TestCreateEdgeValidator:
    """Test create_edge_validator factory function."""

    @pytest.fixture
    def mock_jwt_service(self):
        """Create mock JWT service."""
        return Mock(spec=JWTService)

    def test_create_edge_validator_defaults(self, mock_jwt_service):
        """Test creating edge validator with defaults."""
        validator = create_edge_validator(mock_jwt_service)

        assert isinstance(validator, EdgeJWTValidator)
        assert validator.jwt_service is mock_jwt_service
        assert validator.require_https is True  # Default production

    def test_create_edge_validator_development(self, mock_jwt_service):
        """Test creating edge validator for development."""
        validator = create_edge_validator(mock_jwt_service, environment="development")

        assert validator.require_https is False
        # Should use development patterns
        assert len(validator._compiled_patterns) > 0  # type: ignore[reportPrivateUsage]

    def test_create_edge_validator_custom_patterns(self, mock_jwt_service):
        """Test creating edge validator with custom patterns."""
        custom_patterns = {
            (r"/custom/.*", r"GET"): SensitivityLevel.PUBLIC,
        }

        validator = create_edge_validator(mock_jwt_service, patterns=custom_patterns)

        assert len(validator._compiled_patterns) == 1  # type: ignore[reportPrivateUsage]

    def test_create_edge_validator_with_tenant_resolver(self, mock_jwt_service):
        """Test creating edge validator with tenant resolver."""
        tenant_resolver = Mock()
        validator = create_edge_validator(mock_jwt_service, tenant_resolver=tenant_resolver)

        assert validator.tenant_resolver is tenant_resolver


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_sensitivity_pattern_compilation_errors(self):
        """Test handling of invalid regex patterns."""
        validator = EdgeJWTValidator(Mock())

        # Invalid regex should raise an error
        with pytest.raises(re.error):
            validator.add_sensitivity_pattern(r"[invalid regex", r"GET", SensitivityLevel.PUBLIC)

    @pytest.mark.asyncio
    async def test_validator_with_none_jwt_service(self):
        """Test validator behavior with None JWT service."""
        validator = EdgeJWTValidator(None)  # type: ignore[arg-type]

        # Should fail when trying to verify tokens
        mock_request = Mock()
        mock_request.url = Mock(path="/api/test", scheme="https")
        mock_request.method = "GET"
        mock_request.headers = {"Authorization": "Bearer token"}
        mock_request.cookies = {}
        mock_request.client = Mock(host="example.com")

        with pytest.raises(AttributeError):
            await validator.validate(mock_request)

    def test_pattern_matching_case_insensitive(self):
        """Test that pattern matching is case insensitive."""
        validator = EdgeJWTValidator(Mock())
        validator.add_sensitivity_pattern(r"/API/TEST", r"GET", SensitivityLevel.PUBLIC)

        # Should match lowercase path
        sensitivity = validator.get_route_sensitivity("/api/test", "get")
        assert sensitivity == SensitivityLevel.PUBLIC
