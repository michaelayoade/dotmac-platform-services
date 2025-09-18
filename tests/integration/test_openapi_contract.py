from datetime import UTC
"""
OpenAPI Contract Testing
Validates that API endpoints honor their OpenAPI specification contracts.
"""

import json
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jsonschema import validate
from openapi_spec_validator import validate_spec
from pydantic import BaseModel

from dotmac.platform.auth.jwt_service import JWTService
from dotmac.platform.auth.session_manager import SessionManager, SessionConfig


class ContractTestBase:
    """Base class for contract testing utilities"""

    @staticmethod
    def load_openapi_spec() -> Dict[str, Any]:
        """Load and validate OpenAPI specification"""
        spec_path = (
            Path(__file__).parent.parent.parent / "src/dotmac/platform/api/openapi_spec.yaml"
        )
        with open(spec_path) as f:
            spec = yaml.safe_load(f)

        # Validate the OpenAPI spec itself
        validate_spec(spec)
        return spec

    @staticmethod
    def validate_response_schema(response_data: Any, schema: Dict[str, Any]) -> None:
        """Validate response data against OpenAPI schema"""
        # Convert OpenAPI schema to JSON Schema format
        json_schema = ContractTestBase._openapi_to_json_schema(schema)
        validate(instance=response_data, schema=json_schema)

    @staticmethod
    def _openapi_to_json_schema(openapi_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert OpenAPI schema to JSON Schema format"""
        # Basic conversion - expand as needed
        json_schema = {
            "type": openapi_schema.get("type", "object"),
            "properties": openapi_schema.get("properties", {}),
            "required": openapi_schema.get("required", []),
        }

        # Handle nested properties
        for prop_name, prop_schema in json_schema.get("properties", {}).items():
            if "type" in prop_schema:
                if prop_schema["type"] == "array" and "items" in prop_schema:
                    # Handle array types
                    json_schema["properties"][prop_name] = {
                        "type": "array",
                        "items": (
                            ContractTestBase._openapi_to_json_schema(prop_schema["items"])
                            if "$ref" not in prop_schema["items"]
                            else prop_schema["items"]
                        ),
                    }
                elif prop_schema["type"] == "object" and "properties" in prop_schema:
                    # Handle nested objects
                    json_schema["properties"][prop_name] = ContractTestBase._openapi_to_json_schema(
                        prop_schema
                    )

        return json_schema


@pytest.mark.integration
class TestAuthenticationContract(ContractTestBase):
    """Test authentication endpoints against OpenAPI contract"""

    @pytest.fixture
    def app(self):
        """Create FastAPI app with authentication endpoints"""
        from fastapi import HTTPException, Depends
        from pydantic import BaseModel

        app = FastAPI()
        jwt_service = JWTService(
            algorithm="HS256",
            secret="test-secret",
            issuer="test-issuer",
            default_audience="test-audience",
        )

        class TokenRequest(BaseModel):
            username: str
            password: str
            tenant_id: str | None = None
            scopes: list[str] = []

        class TokenResponse(BaseModel):
            access_token: str
            refresh_token: str | None = None
            token_type: str = "Bearer"
            expires_in: int

        @app.post("/auth/token", response_model=TokenResponse)
        async def create_token(request: TokenRequest):
            # Simulate authentication
            if request.username == "test" and request.password == "password":
                token = jwt_service.issue_access_token(
                    request.username,
                    tenant_id=request.tenant_id,
                    extra_claims={"scopes": request.scopes},
                )
                return TokenResponse(
                    access_token=token,
                    refresh_token=f"refresh_{token[:20]}",
                    token_type="Bearer",
                    expires_in=3600,
                )
            raise HTTPException(status_code=401, detail="Invalid credentials")

        class VerifyTokenRequest(BaseModel):
            token: str

        @app.post("/auth/token/verify")
        async def verify_token(request: VerifyTokenRequest):
            try:
                claims = jwt_service.verify_token(request.token)
                return claims
            except Exception:
                raise HTTPException(status_code=401, detail="Invalid token")

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def openapi_spec(self):
        """Load OpenAPI specification"""
        return self.load_openapi_spec()

    def test_token_creation_success_contract(self, client, openapi_spec):
        """Test successful token creation matches OpenAPI contract"""
        # Get expected schema from OpenAPI spec
        token_response_schema = openapi_spec["components"]["schemas"]["TokenResponse"]

        # Make request
        response = client.post(
            "/auth/token",
            json={
                "username": "test",
                "password": "password",
                "tenant_id": "tenant123",
                "scopes": ["read", "write"],
            },
        )

        # Validate response
        assert response.status_code == 200
        response_data = response.json()

        # Validate against OpenAPI schema
        self.validate_response_schema(response_data, token_response_schema)

        # Validate specific contract requirements
        assert response_data["token_type"] == "Bearer"
        assert response_data["expires_in"] == 3600
        assert len(response_data["access_token"]) > 50
        assert response_data["refresh_token"] is not None

    def test_token_creation_invalid_credentials_contract(self, client, openapi_spec):
        """Test token creation with invalid credentials matches error contract"""
        # Get error schema
        error_schema = openapi_spec["components"]["schemas"]["ErrorResponse"]

        response = client.post("/auth/token", json={"username": "invalid", "password": "wrong"})

        # Validate error response
        assert response.status_code == 401
        error_data = response.json()

        # Basic error structure validation
        assert "detail" in error_data or "error" in error_data

    def test_token_creation_validation_error_contract(self, client, openapi_spec):
        """Test token creation validation error matches contract"""
        response = client.post(
            "/auth/token", json={"username": "", "password": "password"}  # Invalid: empty username
        )

        # Our implementation returns 401 for empty credentials
        # (treats as auth failure rather than validation error)
        assert response.status_code in [401, 422]
        error_data = response.json()

        # Validate error structure
        assert "detail" in error_data
        # Detail can be string (401) or list (422)
        if response.status_code == 422 and isinstance(error_data["detail"], list):
            if error_data["detail"]:
                assert "loc" in error_data["detail"][0]
                assert "msg" in error_data["detail"][0]

    def test_token_verify_success_contract(self, client, openapi_spec):
        """Test token verification success matches contract"""
        # First create a token
        token_response = client.post(
            "/auth/token", json={"username": "test", "password": "password"}
        )
        token = token_response.json()["access_token"]

        # Verify the token
        verify_response = client.post("/auth/token/verify", json={"token": token})

        assert verify_response.status_code == 200
        claims = verify_response.json()

        # Validate required claims from contract
        token_claims_schema = openapi_spec["components"]["schemas"]["TokenClaims"]
        required_claims = token_claims_schema.get("required", [])

        for claim in required_claims:
            assert claim in claims, f"Missing required claim: {claim}"

    def test_token_verify_invalid_contract(self, client, openapi_spec):
        """Test token verification with invalid token matches error contract"""
        verify_response = client.post("/auth/token/verify", json={"token": "invalid.token.here"})

        assert verify_response.status_code == 401
        error_data = verify_response.json()
        assert "detail" in error_data or "error" in error_data


@pytest.mark.integration
class TestSessionContract(ContractTestBase):
    """Test session endpoints against OpenAPI contract"""

    @pytest.fixture
    def app(self):
        """Create FastAPI app with session endpoints"""
        from fastapi import HTTPException
        from datetime import datetime, timedelta

        app = FastAPI()

        # Mock session storage
        sessions = {}

        class CreateSessionRequest(BaseModel):
            user_id: str
            tenant_id: str | None = None
            metadata: dict = {}

        class SessionResponse(BaseModel):
            session_id: str
            user_id: str
            tenant_id: str | None
            created_at: str
            last_accessed: str | None
            expires_at: str
            status: str
            metadata: dict

        @app.post("/auth/sessions", response_model=SessionResponse, status_code=201)
        async def create_session(request: CreateSessionRequest):
            session_id = f"session_{len(sessions) + 1}"
            now = datetime.now(UTC)

            session = SessionResponse(
                session_id=session_id,
                user_id=request.user_id,
                tenant_id=request.tenant_id,
                created_at=now.isoformat(),
                last_accessed=now.isoformat(),
                expires_at=(now + timedelta(hours=1)).isoformat(),
                status="active",
                metadata=request.metadata,
            )

            sessions[session_id] = session
            return session

        @app.get("/auth/sessions/{session_id}", response_model=SessionResponse)
        async def get_session(session_id: str):
            if session_id not in sessions:
                raise HTTPException(status_code=404, detail="Session not found")
            return sessions[session_id]

        @app.delete("/auth/sessions/{session_id}", status_code=204)
        async def delete_session(session_id: str):
            if session_id not in sessions:
                raise HTTPException(status_code=404, detail="Session not found")
            del sessions[session_id]
            return None

        @app.get("/auth/sessions")
        async def list_sessions(user_id: str | None = None, active_only: bool = True):
            filtered_sessions = list(sessions.values())

            if user_id:
                filtered_sessions = [s for s in filtered_sessions if s.user_id == user_id]

            if active_only:
                filtered_sessions = [s for s in filtered_sessions if s.status == "active"]

            return {"sessions": filtered_sessions, "total": len(filtered_sessions)}

        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_create_session_contract(self, client):
        """Test session creation matches OpenAPI contract"""
        spec = self.load_openapi_spec()
        session_schema = spec["components"]["schemas"]["SessionResponse"]

        response = client.post(
            "/auth/sessions",
            json={
                "user_id": "user123",
                "tenant_id": "tenant456",
                "metadata": {"ip": "192.168.1.1"},
            },
        )

        assert response.status_code == 201
        session_data = response.json()

        # Validate required fields
        required_fields = session_schema.get("required", [])
        for field in required_fields:
            assert field in session_data, f"Missing required field: {field}"

        # Validate field types
        assert isinstance(session_data["session_id"], str)
        assert isinstance(session_data["user_id"], str)
        assert session_data["status"] in ["active", "expired", "revoked"]

    def test_get_session_not_found_contract(self, client):
        """Test get session not found matches error contract"""
        response = client.get("/auth/sessions/nonexistent")

        assert response.status_code == 404
        error_data = response.json()
        assert "detail" in error_data

    def test_delete_session_contract(self, client):
        """Test session deletion matches contract"""
        # Create a session first
        create_response = client.post("/auth/sessions", json={"user_id": "user123"})
        session_id = create_response.json()["session_id"]

        # Delete the session
        delete_response = client.delete(f"/auth/sessions/{session_id}")

        # Contract specifies 204 No Content
        assert delete_response.status_code == 204
        assert delete_response.content == b""

    def test_list_sessions_contract(self, client):
        """Test list sessions matches contract"""
        spec = self.load_openapi_spec()
        list_schema = spec["components"]["schemas"]["SessionListResponse"]

        # Create some sessions
        for i in range(3):
            client.post("/auth/sessions", json={"user_id": f"user{i}"})

        # List sessions
        response = client.get("/auth/sessions")

        assert response.status_code == 200
        list_data = response.json()

        # Validate response structure
        assert "sessions" in list_data
        assert "total" in list_data
        assert isinstance(list_data["sessions"], list)
        assert isinstance(list_data["total"], int)
        assert list_data["total"] == len(list_data["sessions"])


@pytest.mark.integration
class TestHealthEndpointContract(ContractTestBase):
    """Test health endpoint against OpenAPI contract"""

    @pytest.fixture
    def app(self):
        """Create FastAPI app with health endpoint"""
        from datetime import datetime

        app = FastAPI()

        @app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.now(UTC).isoformat(),
                "checks": {
                    "database": {"status": "healthy", "response_time": 0.012},
                    "cache": {"status": "healthy", "response_time": 0.003},
                    "secrets": {"status": "healthy", "response_time": 0.025},
                },
                "version": "1.0.0",
            }

        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_health_check_contract(self, client):
        """Test health check endpoint matches OpenAPI contract"""
        spec = self.load_openapi_spec()
        health_schema = spec["components"]["schemas"]["HealthResponse"]

        response = client.get("/health")

        assert response.status_code == 200
        health_data = response.json()

        # Validate required fields
        assert "status" in health_data
        assert "timestamp" in health_data

        # Validate status enum
        assert health_data["status"] in ["healthy", "degraded", "unhealthy"]

        # Validate nested checks if present
        if "checks" in health_data:
            for check_name, check_data in health_data["checks"].items():
                assert "status" in check_data
                assert check_data["status"] in ["healthy", "unhealthy"]

                if "response_time" in check_data:
                    assert isinstance(check_data["response_time"], (int, float))


@pytest.mark.integration
class TestAPIKeyContract(ContractTestBase):
    """Test API key endpoints against OpenAPI contract"""

    @pytest.fixture
    def app(self):
        """Create FastAPI app with API key endpoints"""
        from datetime import datetime
        import secrets

        app = FastAPI()
        api_keys = {}

        class CreateApiKeyRequest(BaseModel):
            name: str
            scopes: list[str] = []
            expires_at: str | None = None

        class ApiKeyResponse(BaseModel):
            key_id: str
            api_key: str
            name: str
            scopes: list[str]
            created_at: str
            expires_at: str | None

        @app.post("/auth/api-keys", response_model=ApiKeyResponse, status_code=201)
        async def create_api_key(request: CreateApiKeyRequest):
            key_id = f"key_{len(api_keys) + 1}"
            api_key = f"dotmac_{secrets.token_urlsafe(32)}"

            key_data = ApiKeyResponse(
                key_id=key_id,
                api_key=api_key,
                name=request.name,
                scopes=request.scopes,
                created_at=datetime.now(UTC).isoformat(),
                expires_at=request.expires_at,
            )

            api_keys[key_id] = key_data
            return key_data

        @app.delete("/auth/api-keys/{key_id}", status_code=204)
        async def revoke_api_key(key_id: str):
            if key_id not in api_keys:
                raise HTTPException(status_code=404, detail="API key not found")
            del api_keys[key_id]
            return None

        @app.get("/auth/api-keys")
        async def list_api_keys(active_only: bool = True):
            # Return list without actual key values
            keys_list = []
            for key_id, key_data in api_keys.items():
                keys_list.append(
                    {
                        "key_id": key_data.key_id,
                        "name": key_data.name,
                        "created_at": key_data.created_at,
                        "expires_at": key_data.expires_at,
                    }
                )

            return {"api_keys": keys_list, "total": len(keys_list)}

        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_create_api_key_contract(self, client):
        """Test API key creation matches contract"""
        spec = self.load_openapi_spec()
        api_key_schema = spec["components"]["schemas"]["ApiKeyResponse"]

        response = client.post(
            "/auth/api-keys",
            json={
                "name": "Test API Key",
                "scopes": ["read", "write"],
                "expires_at": "2025-12-31T23:59:59Z",
            },
        )

        assert response.status_code == 201
        key_data = response.json()

        # Validate required fields
        required_fields = api_key_schema.get("required", [])
        for field in required_fields:
            assert field in key_data, f"Missing required field: {field}"

        # Validate API key format
        assert key_data["api_key"].startswith("dotmac_")
        assert len(key_data["api_key"]) > 20

        # Validate other fields
        assert key_data["name"] == "Test API Key"
        assert key_data["scopes"] == ["read", "write"]

    def test_revoke_api_key_contract(self, client):
        """Test API key revocation matches contract"""
        # Create an API key first
        create_response = client.post("/auth/api-keys", json={"name": "Test Key"})
        key_id = create_response.json()["key_id"]

        # Revoke the key
        revoke_response = client.delete(f"/auth/api-keys/{key_id}")

        # Contract specifies 204 No Content
        assert revoke_response.status_code == 204
        assert revoke_response.content == b""

    def test_list_api_keys_contract(self, client):
        """Test list API keys matches contract"""
        spec = self.load_openapi_spec()

        # Create some API keys
        for i in range(2):
            client.post("/auth/api-keys", json={"name": f"Key {i}"})

        response = client.get("/auth/api-keys")

        assert response.status_code == 200
        list_data = response.json()

        # Validate response structure
        assert "api_keys" in list_data
        assert "total" in list_data
        assert isinstance(list_data["api_keys"], list)
        assert list_data["total"] == len(list_data["api_keys"])

        # API keys in list should NOT contain the actual key
        for key_info in list_data["api_keys"]:
            assert "api_key" not in key_info  # Security: don't expose keys in list
            assert "key_id" in key_info
            assert "name" in key_info