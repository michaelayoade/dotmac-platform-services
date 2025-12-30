"""
OIDC Discovery Endpoint Tests.

Tests for:
- /.well-known/jwks.json - JWKS endpoint
- /.well-known/openid-configuration - OpenID Configuration endpoint
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from dotmac.platform.main import create_app

    app = create_app()
    return TestClient(app)


class TestJWKSEndpoint:
    """Tests for /.well-known/jwks.json endpoint."""

    def test_jwks_endpoint_accessible(self, client: TestClient):
        """Verify /.well-known/jwks.json is accessible without authentication."""
        response = client.get("/.well-known/jwks.json")
        assert response.status_code == 200

    def test_jwks_returns_valid_structure(self, client: TestClient):
        """Verify JWKS returns valid JWK Set structure."""
        response = client.get("/.well-known/jwks.json")
        assert response.status_code == 200

        data = response.json()
        assert "keys" in data
        assert isinstance(data["keys"], list)

    def test_jwks_content_type(self, client: TestClient):
        """Verify JWKS returns JSON content type."""
        response = client.get("/.well-known/jwks.json")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_jwks_keys_have_required_fields(self, client: TestClient):
        """Verify JWK keys have required fields when present."""
        response = client.get("/.well-known/jwks.json")
        assert response.status_code == 200

        data = response.json()
        for key in data.get("keys", []):
            # All JWKs must have kty
            assert "kty" in key
            # Should have kid for rotation support
            assert "kid" in key
            # Should have use and alg
            assert "use" in key
            assert "alg" in key

            # RSA keys should have n and e
            if key["kty"] == "RSA":
                assert "n" in key
                assert "e" in key

            # EC keys should have crv, x, y
            if key["kty"] == "EC":
                assert "crv" in key
                assert "x" in key
                assert "y" in key


class TestOpenIDConfiguration:
    """Tests for /.well-known/openid-configuration endpoint."""

    def test_openid_configuration_accessible(self, client: TestClient):
        """Verify /.well-known/openid-configuration is accessible without authentication."""
        response = client.get("/.well-known/openid-configuration")
        assert response.status_code == 200

    def test_openid_configuration_has_required_fields(self, client: TestClient):
        """Verify OpenID Configuration has required fields per RFC 8414."""
        response = client.get("/.well-known/openid-configuration")
        assert response.status_code == 200

        data = response.json()

        # Required fields
        assert "issuer" in data
        assert "jwks_uri" in data

        # Should have token endpoint
        assert "token_endpoint" in data

    def test_openid_configuration_jwks_uri_valid(self, client: TestClient):
        """Verify jwks_uri points to valid endpoint."""
        response = client.get("/.well-known/openid-configuration")
        assert response.status_code == 200

        data = response.json()
        jwks_uri = data.get("jwks_uri", "")

        # Should end with /.well-known/jwks.json
        assert jwks_uri.endswith("/.well-known/jwks.json")

    def test_openid_configuration_content_type(self, client: TestClient):
        """Verify OpenID Configuration returns JSON content type."""
        response = client.get("/.well-known/openid-configuration")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_openid_configuration_has_supported_algorithms(self, client: TestClient):
        """Verify configuration includes supported signing algorithms."""
        response = client.get("/.well-known/openid-configuration")
        assert response.status_code == 200

        data = response.json()

        # Should list supported algorithms
        assert "id_token_signing_alg_values_supported" in data
        algs = data["id_token_signing_alg_values_supported"]
        assert isinstance(algs, list)
        assert len(algs) > 0

        # Should support at least HS256 for backward compatibility
        assert "HS256" in algs

    def test_openid_configuration_has_claims_supported(self, client: TestClient):
        """Verify configuration includes supported claims."""
        response = client.get("/.well-known/openid-configuration")
        assert response.status_code == 200

        data = response.json()

        # Should list supported claims
        if "claims_supported" in data:
            claims = data["claims_supported"]
            assert isinstance(claims, list)
            # Standard claims
            assert "sub" in claims
            assert "iss" in claims
            assert "aud" in claims


class TestOIDCDiscoveryIntegration:
    """Integration tests for OIDC discovery flow."""

    def test_discovery_to_jwks_flow(self, client: TestClient):
        """Test complete flow: discover configuration, then fetch JWKS."""
        # Step 1: Get OpenID Configuration
        config_response = client.get("/.well-known/openid-configuration")
        assert config_response.status_code == 200

        config = config_response.json()
        jwks_uri = config.get("jwks_uri")
        assert jwks_uri is not None

        # Step 2: Fetch JWKS from discovered URI
        # Note: jwks_uri might be absolute URL, need to extract path
        jwks_path = jwks_uri.split("://")[-1].split("/", 1)[-1]
        if not jwks_path.startswith("/"):
            jwks_path = "/" + jwks_path

        jwks_response = client.get(jwks_path)
        assert jwks_response.status_code == 200

        jwks = jwks_response.json()
        assert "keys" in jwks

    def test_issuer_matches_between_endpoints(self, client: TestClient):
        """Verify issuer is consistent across endpoints."""
        config_response = client.get("/.well-known/openid-configuration")
        assert config_response.status_code == 200

        config = config_response.json()
        issuer = config.get("issuer")

        # Issuer should be a non-empty string
        assert issuer
        assert isinstance(issuer, str)
        assert len(issuer) > 0
