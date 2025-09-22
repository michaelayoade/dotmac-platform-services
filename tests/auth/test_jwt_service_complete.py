"""
Comprehensive tests for JWT Service with full coverage.
Tests token generation, validation, refresh, custom claims, and error scenarios.
"""

import time
from datetime import datetime, timedelta, UTC
from unittest.mock import Mock, patch
import pytest
import jwt as pyjwt

from dotmac.platform.auth.jwt_service import JWTService
from dotmac.platform.auth.exceptions import (
    AuthenticationError,
    TokenExpired,
    InvalidToken,
)


class TestJWTServiceInitialization:
    """Test JWT Service initialization and configuration."""

    def test_default_initialization(self):
        """Test JWT service with default parameters."""
        service = JWTService()
        assert service.algorithm == "HS256"
        assert service.secret is not None
        assert service.access_token_expire_minutes == 15
        assert service.refresh_token_expire_days == 7  # 7 days

    def test_custom_initialization(self):
        """Test JWT service with custom parameters."""
        service = JWTService(
            algorithm="HS512",
            secret="custom-secret-key",
            access_token_expire_minutes=30,
            refresh_token_expire_days=14,  # 14 days
            issuer="test-issuer",
            default_audience="test-audience",
        )
        assert service.algorithm == "HS512"
        assert service.secret == "custom-secret-key"
        assert service.access_token_expire_minutes == 30
        assert service.refresh_token_expire_days == 14
        assert service.issuer == "test-issuer"
        assert service.default_audience == "test-audience"

    def test_rsa_initialization(self):
        """Test JWT service with RSA algorithm."""
        private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAtest_key_content
-----END RSA PRIVATE KEY-----"""
        public_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqtest_key_content
-----END PUBLIC KEY-----"""

        service = JWTService(
            algorithm="RS256",
            private_key=private_key,
            public_key=public_key,
        )
        assert service.algorithm == "RS256"
        assert service.private_key == private_key
        assert service.public_key == public_key


class TestAccessTokenGeneration:
    """Test access token generation."""

    @pytest.fixture
    def jwt_service(self):
        """Create a JWT service instance."""
        return JWTService(
            algorithm="HS256",
            secret="test-secret",
            issuer="test-issuer",
            default_audience="test-api",
        )

    def test_issue_access_token_basic(self, jwt_service):
        """Test basic access token generation."""
        token = jwt_service.issue_access_token(subject="user123")
        assert token is not None
        assert isinstance(token, str)

        # Decode and verify
        decoded = pyjwt.decode(
            token,
            jwt_service.secret,
            algorithms=[jwt_service.algorithm],
            options={"verify_signature": True, "verify_exp": False}
        )
        assert decoded["sub"] == "user123"
        assert decoded["type"] == "access"
        assert "exp" in decoded
        assert "iat" in decoded
        assert "jti" in decoded

    def test_issue_access_token_with_permissions(self, jwt_service):
        """Test access token with permissions."""
        permissions = ["read:users", "write:posts"]
        token = jwt_service.issue_access_token(
            subject="user123",
            permissions=permissions
        )

        decoded = pyjwt.decode(
            token,
            jwt_service.secret,
            algorithms=[jwt_service.algorithm],
            options={"verify_signature": False}
        )
        assert decoded["permissions"] == permissions

    def test_issue_access_token_with_custom_claims(self, jwt_service):
        """Test access token with custom claims."""
        custom_claims = {
            "tenant_id": "tenant-456",
            "role": "admin",
            "department": "engineering"
        }
        token = jwt_service.issue_access_token(
            subject="user123",
            custom_claims=custom_claims
        )

        decoded = pyjwt.decode(
            token,
            jwt_service.secret,
            algorithms=[jwt_service.algorithm],
            options={"verify_signature": False}
        )
        assert decoded["tenant_id"] == "tenant-456"
        assert decoded["role"] == "admin"
        assert decoded["department"] == "engineering"

    def test_issue_access_token_with_custom_expiry(self, jwt_service):
        """Test access token with custom expiry time."""
        token = jwt_service.issue_access_token(
            subject="user123",
            expire_minutes=60
        )

        decoded = pyjwt.decode(
            token,
            jwt_service.secret,
            algorithms=[jwt_service.algorithm],
            options={"verify_signature": False}
        )

        # Check expiry is approximately 60 minutes from now
        exp_time = datetime.fromtimestamp(decoded["exp"], UTC)
        expected_exp = datetime.now(UTC) + timedelta(minutes=60)
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 5  # Within 5 seconds tolerance

    def test_issue_access_token_with_audience(self, jwt_service):
        """Test access token with specific audience."""
        token = jwt_service.issue_access_token(
            subject="user123",
            audience="mobile-app"
        )

        decoded = pyjwt.decode(
            token,
            jwt_service.secret,
            algorithms=[jwt_service.algorithm],
            options={"verify_signature": False}
        )
        assert decoded["aud"] == "mobile-app"


class TestRefreshTokenGeneration:
    """Test refresh token generation."""

    @pytest.fixture
    def jwt_service(self):
        """Create a JWT service instance."""
        return JWTService(secret="test-secret")

    def test_issue_refresh_token_basic(self, jwt_service):
        """Test basic refresh token generation."""
        token = jwt_service.issue_refresh_token(subject="user123")
        assert token is not None

        decoded = pyjwt.decode(
            token,
            jwt_service.secret,
            algorithms=[jwt_service.algorithm],
            options={"verify_signature": False}
        )
        assert decoded["sub"] == "user123"
        assert decoded["type"] == "refresh"

    def test_issue_refresh_token_with_custom_expiry(self, jwt_service):
        """Test refresh token with custom expiry."""
        token = jwt_service.issue_refresh_token(
            subject="user123",
            expire_minutes=20160  # 14 days
        )

        decoded = pyjwt.decode(
            token,
            jwt_service.secret,
            algorithms=[jwt_service.algorithm],
            options={"verify_signature": False}
        )

        exp_time = datetime.fromtimestamp(decoded["exp"], UTC)
        expected_exp = datetime.now(UTC) + timedelta(minutes=20160)
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 5


class TestTokenValidation:
    """Test token validation."""

    @pytest.fixture
    def jwt_service(self):
        """Create a JWT service instance."""
        return JWTService(
            secret="test-secret",
            issuer="test-issuer",
            default_audience="test-api"
        )

    def test_verify_valid_token(self, jwt_service):
        """Test verification of valid token."""
        token = jwt_service.issue_access_token(subject="user123")
        decoded = jwt_service.verify_token(token)

        assert decoded["sub"] == "user123"
        assert decoded["type"] == "access"
        assert decoded["iss"] == "test-issuer"
        assert decoded["aud"] == "test-api"

    def test_verify_expired_token(self, jwt_service):
        """Test verification of expired token."""
        # Create expired token
        expired_token = jwt_service.issue_access_token(
            subject="user123",
            expire_minutes=-1  # Already expired
        )

        with pytest.raises(TokenExpired):
            jwt_service.verify_token(expired_token)

    def test_verify_invalid_signature(self, jwt_service):
        """Test verification of token with invalid signature."""
        token = jwt_service.issue_access_token(subject="user123")
        # Tamper with the token
        tampered_token = token[:-10] + "tampered123"

        with pytest.raises(InvalidToken):
            jwt_service.verify_token(tampered_token)

    def test_verify_malformed_token(self, jwt_service):
        """Test verification of malformed token."""
        with pytest.raises(InvalidToken):
            jwt_service.verify_token("not.a.valid.token")

    def test_verify_token_with_wrong_audience(self, jwt_service):
        """Test token verification with wrong audience."""
        token = jwt_service.issue_access_token(
            subject="user123",
            audience="wrong-audience"
        )

        # Service expects "test-api" audience
        with pytest.raises(InvalidToken):
            jwt_service.verify_token(token, audience="test-api")

    def test_verify_token_with_wrong_issuer(self):
        """Test token verification with wrong issuer."""
        service1 = JWTService(secret="secret", issuer="issuer1")
        service2 = JWTService(secret="secret", issuer="issuer2")

        token = service1.issue_access_token(subject="user123")

        with pytest.raises(InvalidToken):
            service2.verify_token(token)

    def test_verify_token_skip_expiration(self, jwt_service):
        """Test token verification skipping expiration check."""
        expired_token = jwt_service.issue_access_token(
            subject="user123",
            expire_minutes=-1
        )

        decoded = jwt_service.verify_token(
            expired_token,
            verify_exp=False
        )
        assert decoded["sub"] == "user123"


class TestTokenRefresh:
    """Test token refresh functionality."""

    @pytest.fixture
    def jwt_service(self):
        """Create a JWT service instance."""
        return JWTService(secret="test-secret")

    def test_refresh_access_token(self, jwt_service):
        """Test refreshing access token from refresh token."""
        refresh_token = jwt_service.issue_refresh_token(
            subject="user123",
            custom_claims={"role": "admin"}
        )

        new_access_token = jwt_service.refresh_access_token(refresh_token)

        decoded = jwt_service.verify_token(new_access_token)
        assert decoded["sub"] == "user123"
        assert decoded["type"] == "access"
        assert decoded["role"] == "admin"

    def test_refresh_with_invalid_refresh_token(self, jwt_service):
        """Test refresh with invalid refresh token."""
        access_token = jwt_service.issue_access_token(subject="user123")

        # Try to refresh with access token instead of refresh token
        with pytest.raises(InvalidToken):
            jwt_service.refresh_access_token(access_token)

    def test_refresh_with_expired_refresh_token(self, jwt_service):
        """Test refresh with expired refresh token."""
        expired_refresh = jwt_service.issue_refresh_token(
            subject="user123",
            expire_minutes=-1
        )

        with pytest.raises(TokenExpired):
            jwt_service.refresh_access_token(expired_refresh)


class TestTokenRevocation:
    """Test token revocation functionality."""

    @pytest.fixture
    def jwt_service(self):
        """Create a JWT service instance."""
        return JWTService(secret="test-secret")

    def test_revoke_token(self, jwt_service):
        """Test revoking a token."""
        token = jwt_service.issue_access_token(subject="user123")
        decoded = jwt_service.verify_token(token)
        jti = decoded.get("jti")

        # Revoke the token
        jwt_service.revoke_token(jti)

        # Check token is revoked
        assert jwt_service.is_token_revoked(jti) is True

    def test_verify_revoked_token(self, jwt_service):
        """Test verification of revoked token."""
        token = jwt_service.issue_access_token(subject="user123")
        decoded = jwt_service.verify_token(token)
        jti = decoded.get("jti")

        # Revoke the token
        jwt_service.revoke_token(jti)

        # Try to verify revoked token
        with pytest.raises(InvalidToken):
            jwt_service.verify_token(token)

    def test_revoke_all_user_tokens(self, jwt_service):
        """Test revoking all tokens for a user."""
        # Create multiple tokens for the same user
        token1 = jwt_service.issue_access_token(subject="user123")
        token2 = jwt_service.issue_access_token(subject="user123")
        token3 = jwt_service.issue_access_token(subject="user456")

        # Revoke all tokens for user123
        jwt_service.revoke_all_user_tokens("user123")

        # Check user123 tokens are revoked
        with pytest.raises(InvalidToken):
            jwt_service.verify_token(token1)

        with pytest.raises(InvalidToken):
            jwt_service.verify_token(token2)

        # user456 token should still be valid
        decoded = jwt_service.verify_token(token3)
        assert decoded["sub"] == "user456"


class TestTokenDecoding:
    """Test token decoding without verification."""

    @pytest.fixture
    def jwt_service(self):
        """Create a JWT service instance."""
        return JWTService(secret="test-secret")

    def test_decode_token_without_verification(self, jwt_service):
        """Test decoding token without verification."""
        token = jwt_service.issue_access_token(
            subject="user123",
            permissions=["read", "write"],
            custom_claims={"tenant": "abc"}
        )

        decoded = jwt_service.decode_token(token)
        assert decoded["sub"] == "user123"
        assert decoded["permissions"] == ["read", "write"]
        assert decoded["tenant"] == "abc"

    def test_decode_expired_token(self, jwt_service):
        """Test decoding expired token without verification."""
        expired_token = jwt_service.issue_access_token(
            subject="user123",
            expire_minutes=-1
        )

        # Should decode without error even if expired
        decoded = jwt_service.decode_token(expired_token)
        assert decoded["sub"] == "user123"

    def test_decode_malformed_token(self, jwt_service):
        """Test decoding malformed token."""
        with pytest.raises(InvalidToken):
            jwt_service.decode_token("not.a.token")


class TestAlgorithmSupport:
    """Test support for different algorithms."""

    def test_hmac_algorithms(self):
        """Test HMAC algorithms."""
        for algo in ["HS256", "HS384", "HS512"]:
            service = JWTService(algorithm=algo, secret="secret-key")
            token = service.issue_access_token(subject="user123")
            decoded = service.verify_token(token)
            assert decoded["sub"] == "user123"

    def test_rsa_algorithms(self):
        """Test RSA algorithms."""
        # Generate test keys (in real scenario, use proper keys)
        private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA0Z3VS6JJcds6DCu4U5XpGgX6g7FwYVRkSZcxaRBrDRxIhCCe
1Ip7DrNMkrpJvtsM2wS7G8y+VTLoqd/tMehj3eOzqCl7fCYPV6gZoiHPfwRB1bDX
3xaBf/7PZsPiuNJZHu4ci8mIJiyY9DeZdd4y5W9yLfTg4ExSbe8f2IDh3sxBqF5e
o6bkMvAYbP6W6kWfqLJqdLGPPGVN0aSvCf5TAhDWFJkGrFwPJXmZotWvj7gIFOxy
Gs6ByXkGT7h8JCYq2Dq6jELDLjoINCdLlE7x6yazrbtUUK6DGaXBkpmrviiGKhnE
9mhVJtQ4cH9NaHvW7NJ3l4OOSxWMTBnKlKPxewIDAQABAoIBAQCxj2j1hZEnyxLp
8upLXEJwMUJnRqXC9HTGeAzUiWzCHpqaWKHGxOZH5rMkIfuPcxIA7j+bDzglm7r4
F+sPy6LHDmGVMlnfJ7cIV0LHoQszV5o8wIcoSfHKJ8ReNaJNaV8LwV9GLBkNcUDO
F/hEG0mnqGhKU8jLIbhJAy9gg7BzFjU3fZDPW0iA9bnBuCqeVQCLdcQsYXJx0xEs
NTbf6rRHdNCmnwFOH6YOM6Y5SGLBMs3rmpO7k+PGLhqiiYoPG5S4KHqr7YvPInLr
q9qbS9hOdVnoe8TaVkQeNx8WJGqYpE3JGmTXOJmZ3EJHLtGOXXv9nHqOcv1nLaTO
a1PHrtgRAoGBAPRBW5Jof4VfhDWobJBrO6cOXYD5HhzP3T7bWPLxNF2b7wDfdT5h
1BdYKeZCPJtreLMCj3PuV+s3Qzf1cTtWgJDGUJcLoNDGlZkT7M8T2lDIV0lX6eVp
o9xGiSYIdkYv0mpR5M+pOpOzZ4JbvLRvtH/GlIoD7JQMs2VrYOJvO/fJAoGBANvL
dPJETiTkxWOM5zj1F72KyOlVEhQTQmvfh8OIAJaU2lT1z+1+BgvF+SJmQnPeRFdE
OorNsYS3CXHupP8GBgFqccOKCPdCCpLBiVMgPWXN/N5w7kfQoMza9IdCrA9PHoO4
JYo65xT8rRz+Gb4/tE39p0cQlM16FEzLe5YjgjgjAoGAaU8bIsKOI9YGr/7j8j3k
YV1ZNOGtqNZxz2m5pBb6JJ4ymMNWKPWKEfyp6F4UB7vMUZwiUz+siVIY+in6Ld8y
7nmbpOuF8c4YLRQLcTqrXs6n7JaIlNQcJmSqy1jiOiBHT8MLtQQOOtQLmU3sq7Bq
5L7wGj4GYYLJQZQelMoPigkCgYBZ4kwyEVuLfhf9NhYYOlb5qfMgx0yEiowDovQB
1hVpu8lIfVQMUa7x0uS6KdSLNlKeqCs8sFtR34mwxjksLKZG0gWiHNQlHbzVWCsh
R8+5N8OqIxDmCCF+6S+CItFda3X36JMIlKb7QLXZMDhIWZdMh+3UkLCz9Mrju/9a
7RR08QKBgB2kWni0x8aJei4fd48xGkFpfKVqX8YLLz1UkbDcLTS3lMUQJRYuFRuC
AKU3hyy0ixr1neqe4bnOlHoGPKHqiUtSLxaQ1wF0gXGyH6kh+ue/3yMqf/v8oDHr
aFYIKCfXWVhpOD38Q4vRnjLp1fhKWNLNqqVYK0eJHoqEBQfrsLth
-----END RSA PRIVATE KEY-----"""

        public_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0Z3VS6JJcds6DCu4U5Xp
GgX6g7FwYVRkSZcxaRBrDRxIhCCe1Ip7DrNMkrpJvtsM2wS7G8y+VTLoqd/tMehj
3eOzqCl7fCYPV6gZoiHPfwRB1bDX3xaBf/7PZsPiuNJZHu4ci8mIJiyY9DeZdd4y
5W9yLfTg4ExSbe8f2IDh3sxBqF5eo6bkMvAYbP6W6kWfqLJqdLGPPGVN0aSvCf5T
AhDWFJkGrFwPJXmZotWvj7gIFOxyGs6ByXkGT7h8JCYq2Dq6jELDLjoINCdLlE7x
6yazrbtUUK6DGaXBkpmrviiGKhnE9mhVJtQ4cH9NaHvW7NJ3l4OOSxWMTBnKlKPx
ewIDAQAB
-----END PUBLIC KEY-----"""

        for algo in ["RS256", "RS384", "RS512"]:
            service = JWTService(
                algorithm=algo,
                private_key=private_key,
                public_key=public_key
            )
            token = service.issue_access_token(subject="user123")
            decoded = service.verify_token(token)
            assert decoded["sub"] == "user123"


class TestTokenClaims:
    """Test token claims handling."""

    @pytest.fixture
    def jwt_service(self):
        """Create a JWT service instance."""
        return JWTService(
            secret="test-secret",
            issuer="test-issuer",
            default_audience="test-api"
        )

    def test_standard_claims(self, jwt_service):
        """Test standard JWT claims."""
        token = jwt_service.issue_access_token(subject="user123")
        decoded = jwt_service.verify_token(token)

        # Check standard claims
        assert "sub" in decoded  # Subject
        assert "exp" in decoded  # Expiration
        assert "iat" in decoded  # Issued at
        assert "jti" in decoded  # JWT ID
        assert "iss" in decoded  # Issuer
        assert "aud" in decoded  # Audience
        assert "type" in decoded  # Token type

    def test_custom_claims_override(self, jwt_service):
        """Test that custom claims can override defaults."""
        custom_claims = {
            "type": "custom_type",
            "custom_field": "custom_value"
        }
        token = jwt_service.issue_access_token(
            subject="user123",
            custom_claims=custom_claims
        )

        decoded = jwt_service.verify_token(token, verify_exp=False)
        assert decoded["type"] == "custom_type"
        assert decoded["custom_field"] == "custom_value"

    def test_permissions_in_claims(self, jwt_service):
        """Test permissions are properly included in claims."""
        permissions = [
            "users:read",
            "users:write",
            "admin:all"
        ]
        token = jwt_service.issue_access_token(
            subject="user123",
            permissions=permissions
        )

        decoded = jwt_service.verify_token(token)
        assert decoded["permissions"] == permissions


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.fixture
    def jwt_service(self):
        """Create a JWT service instance."""
        return JWTService(secret="test-secret")

    def test_verify_none_token(self, jwt_service):
        """Test verification with None token."""
        with pytest.raises(InvalidToken):
            jwt_service.verify_token(None)

    def test_verify_empty_token(self, jwt_service):
        """Test verification with empty token."""
        with pytest.raises(InvalidToken):
            jwt_service.verify_token("")

    def test_decode_none_token(self, jwt_service):
        """Test decoding with None token."""
        with pytest.raises(InvalidToken):
            jwt_service.decode_token(None)

    def test_refresh_with_none_token(self, jwt_service):
        """Test refresh with None token."""
        with pytest.raises(InvalidToken):
            jwt_service.refresh_access_token(None)

    def test_issue_token_with_none_subject(self, jwt_service):
        """Test issuing token with None subject."""
        # Should handle gracefully or use default
        token = jwt_service.issue_access_token(subject=None)
        decoded = jwt_service.verify_token(token)
        assert decoded["sub"] is None or decoded["sub"] == ""
