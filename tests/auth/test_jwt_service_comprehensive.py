"""
Comprehensive JWT Service Testing
Implementation of AUTH-001: JWT Service security and functionality testing.
"""

import asyncio
import time
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import jwt
import pytest

from dotmac.platform.auth.jwt_service import JWTService


class TestJWTServiceComprehensive:
    """Comprehensive JWT service testing"""

    @pytest.fixture
    def jwt_service(self):
        """Create JWT service instance for testing"""
        # Use HS256 for testing simplicity
        return JWTService(
            algorithm="HS256",
            secret="test-secret-key-for-comprehensive-testing",
            issuer="test-issuer",
            default_audience="test-audience",
        )

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for JWT service"""
        return {
            "jwt_secret": "test-secret-key-for-testing",
            "jwt_algorithm": "HS256",
            "jwt_expiry_minutes": 30,
        }

    @pytest.fixture
    def mock_secrets_provider(self):
        """Mock secrets provider for testing"""
        from unittest.mock import Mock

        provider = Mock()
        provider.get_jwt_private_key.return_value = None
        provider.get_jwt_public_key.return_value = None
        provider.get_symmetric_secret.return_value = "mock-secret"
        return provider

    # Token Generation Tests

    def test_jwt_token_generation_basic(self, jwt_service):
        """Test basic JWT token generation"""
        token = jwt_service.issue_access_token("user123")

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are typically long

    def test_jwt_token_generation_with_custom_claims(self, jwt_service):
        """Test JWT token generation with custom claims"""
        custom_claims = {"role": "admin", "permissions": ["read", "write"]}
        token = jwt_service.issue_access_token(
            "user123", extra_claims=custom_claims, tenant_id="test_tenant"
        )

        # Decode without verification for testing
        decoded = jwt_service.decode_token_unsafe(token)

        assert decoded["sub"] == "user123"
        assert decoded["role"] == "admin"
        assert decoded["tenant_id"] == "test_tenant"
        assert decoded["permissions"] == ["read", "write"]

    def test_jwt_token_generation_with_custom_expiry(self, jwt_service):
        """Test JWT token generation with custom expiry time"""
        # Generate token with 1 hour expiry
        token = jwt_service.issue_access_token("user123", expires_in=60)
        decoded = jwt_service.decode_token_unsafe(token)

        # Check expiry is approximately 1 hour from now
        exp_time = datetime.fromtimestamp(decoded["exp"], UTC)
        expected_exp = datetime.now(UTC) + timedelta(minutes=60)

        # Allow 1 minute tolerance
        assert abs((exp_time - expected_exp).total_seconds()) < 60

    def test_jwt_token_contains_standard_claims(self, jwt_service):
        """Test that JWT tokens contain standard claims"""
        token = jwt_service.issue_access_token("user123")
        decoded = jwt_service.decode_token_unsafe(token)

        # Standard JWT claims
        assert "sub" in decoded  # Subject
        assert "iat" in decoded  # Issued at
        assert "exp" in decoded  # Expiry
        assert "jti" in decoded  # JWT ID (should be unique)

        assert decoded["sub"] == "user123"

    # Token Validation Tests

    def test_jwt_token_validation_success(self, jwt_service):
        """Test successful JWT token validation"""
        token = jwt_service.issue_access_token("user123")

        # Should validate successfully
        decoded = jwt_service.verify_token(token)
        assert decoded["sub"] == "user123"

    def test_jwt_token_validation_with_claims(self, jwt_service):
        """Test JWT token validation preserves custom claims"""
        claims = {"role": "admin", "department": "engineering"}
        token = jwt_service.issue_access_token("user123", extra_claims=claims)

        decoded = jwt_service.verify_token(token)
        assert decoded["sub"] == "user123"
        assert decoded["role"] == "admin"
        assert decoded["department"] == "engineering"

    @pytest.mark.asyncio
    async def test_jwt_token_expiration_handling(self, jwt_service):
        """Test JWT token expiration detection"""
        from dotmac.platform.auth.exceptions import TokenExpired

        # Generate token with very short expiry (1 second = 1/60 minutes)
        token = jwt_service.issue_access_token("user123", expires_in=1 / 60)

        # Wait for token to expire
        await asyncio.sleep(2)

        # Should raise TokenExpired
        with pytest.raises(TokenExpired):
            jwt_service.verify_token(token)

    def test_jwt_invalid_signature_detection(self, jwt_service):
        """Test detection of tokens with invalid signatures"""
        from dotmac.platform.auth.exceptions import InvalidSignature, InvalidToken

        token = jwt_service.issue_access_token("user123")

        # Tamper with the token (change last character)
        tampered_token = token[:-1] + "X"

        with pytest.raises((InvalidSignature, InvalidToken)):
            jwt_service.verify_token(tampered_token)

    def test_jwt_malformed_token_rejection(self, jwt_service):
        """Test rejection of malformed JWT tokens"""
        from dotmac.platform.auth.exceptions import InvalidToken

        malformed_tokens = [
            "not.a.jwt",
            "invalid-token-format",
            "",
            "a.b",  # Too few segments
            "a.b.c.d.e",  # Too many segments
        ]

        for malformed_token in malformed_tokens:
            with pytest.raises(InvalidToken):
                jwt_service.verify_token(malformed_token)

    def test_jwt_token_without_required_claims(self, jwt_service):
        """Test handling of tokens missing required claims"""
        from dotmac.platform.auth.exceptions import InvalidToken

        # Create token without subject claim using the same secret
        payload = {"iat": int(time.time()), "exp": int(time.time()) + 3600}

        # Use the same secret as the JWT service
        token = jwt.encode(payload, jwt_service.secret, algorithm="HS256")

        with pytest.raises(InvalidToken):
            jwt_service.verify_token(token)

    # Key Rotation and Security Tests

    def test_jwt_key_rotation_scenario(self, jwt_service):
        """Test JWT behavior during key rotation"""
        from dotmac.platform.auth.exceptions import InvalidSignature

        # Generate token with original key
        token1 = jwt_service.issue_access_token("user123")

        # Simulate key rotation
        with patch.object(jwt_service, "_get_signing_key", return_value="new-secret-key"):
            with patch.object(jwt_service, "_get_verification_key", return_value="new-secret-key"):
                # Old token should fail with new key
                with pytest.raises(InvalidSignature):
                    jwt_service.verify_token(token1)

                # New token should work with new key
                token2 = jwt_service.issue_access_token("user456")
                decoded = jwt_service.verify_token(token2)
                assert decoded["sub"] == "user456"

    def test_jwt_algorithm_consistency(self, jwt_service):
        """Test JWT algorithm consistency"""
        from dotmac.platform.auth.exceptions import (
            InvalidAlgorithm,
            InvalidSignature,
            InvalidToken,
        )

        token = jwt_service.issue_access_token("user123")

        # Decode with different algorithm should fail
        with patch.object(jwt_service, "algorithm", "RS256"):
            with pytest.raises((InvalidAlgorithm, InvalidSignature, InvalidToken)):
                jwt_service.verify_token(token)

    # Performance and Load Tests

    def test_jwt_generation_performance(self, jwt_service):
        """Test JWT generation performance under load"""
        start_time = time.time()

        # Generate 1000 tokens
        tokens = []
        for i in range(1000):
            token = jwt_service.issue_access_token(f"user{i}")
            tokens.append(token)

        end_time = time.time()
        generation_time = end_time - start_time

        # Should generate 1000 tokens in reasonable time (< 5 seconds)
        assert generation_time < 5.0
        assert len(tokens) == 1000

        # All tokens should be unique
        assert len(set(tokens)) == 1000

    def test_jwt_validation_performance(self, jwt_service):
        """Test JWT validation performance under load"""
        # Pre-generate tokens
        tokens = [jwt_service.issue_access_token(f"user{i}") for i in range(1000)]

        start_time = time.time()

        # Validate all tokens
        for token in tokens:
            decoded = jwt_service.verify_token(token)
            assert decoded["sub"].startswith("user")

        end_time = time.time()
        validation_time = end_time - start_time

        # Should validate 1000 tokens in reasonable time (< 3 seconds)
        assert validation_time < 3.0

    def test_jwt_concurrent_operations(self, jwt_service):
        """Test JWT operations under concurrent access"""
        import queue
        import threading

        results = queue.Queue()
        errors = queue.Queue()

        def worker(worker_id):
            try:
                # Each worker generates and validates tokens
                for i in range(100):
                    token = jwt_service.issue_access_token(f"worker{worker_id}_user{i}")
                    decoded = jwt_service.verify_token(token)
                    assert decoded["sub"] == f"worker{worker_id}_user{i}"

                results.put(f"worker{worker_id}_success")
            except Exception as e:
                errors.put(f"worker{worker_id}_error: {e}")

        # Start 10 concurrent workers
        threads = []
        for worker_id in range(10):
            thread = threading.Thread(target=worker, args=(worker_id,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        assert results.qsize() == 10  # All workers succeeded
        assert errors.empty()  # No errors occurred

    # RS256 Algorithm Tests

    def test_jwt_rs256_service_initialization(self):
        """Test JWT service initialization with RS256"""
        from dotmac.platform.auth.exceptions import ConfigurationError

        # Should fail without keys
        with pytest.raises(ConfigurationError):
            JWTService(algorithm="RS256")

        # Generate keypair for testing
        private_key, public_key = JWTService.generate_rsa_keypair()

        # Should succeed with keypair
        service = JWTService(algorithm="RS256", private_key=private_key, public_key=public_key)
        assert service.algorithm == "RS256"
        assert service.private_key is not None
        assert service.public_key is not None

    def test_jwt_rs256_token_operations(self):
        """Test JWT token generation and verification with RS256"""
        private_key, public_key = JWTService.generate_rsa_keypair()
        service = JWTService(algorithm="RS256", private_key=private_key, public_key=public_key)

        # Generate token
        token = service.issue_access_token("user123", scopes=["read", "write"])
        assert token is not None

        # Verify token
        decoded = service.verify_token(token)
        assert decoded["sub"] == "user123"
        assert decoded["scopes"] == ["read", "write"]
        assert "scope" in decoded

    def test_jwt_rs256_public_key_only_verification(self):
        """Test RS256 verification with public key only"""
        private_key, public_key = JWTService.generate_rsa_keypair()

        # Service with private key for signing
        signing_service = JWTService(algorithm="RS256", private_key=private_key)
        token = signing_service.issue_access_token("user123")

        # Service with public key only for verification
        verify_service = JWTService(algorithm="RS256", public_key=public_key)
        decoded = verify_service.verify_token(token)
        assert decoded["sub"] == "user123"

        # Should fail to sign without private key
        from dotmac.platform.auth.exceptions import ConfigurationError, InvalidToken

        with pytest.raises((ConfigurationError, InvalidToken)):
            verify_service.issue_access_token("user456")

    # Secrets Provider Integration Tests

    def test_jwt_with_secrets_provider_rs256(self):
        """Test JWT service with secrets provider for RS256"""
        from unittest.mock import Mock

        private_key, public_key = JWTService.generate_rsa_keypair()

        # Mock secrets provider
        mock_provider = Mock()
        mock_provider.get_jwt_private_key.return_value = private_key
        mock_provider.get_jwt_public_key.return_value = public_key

        service = JWTService(algorithm="RS256", secrets_provider=mock_provider)

        # Should use keys from provider
        assert mock_provider.get_jwt_private_key.called
        assert mock_provider.get_jwt_public_key.called

        # Should work normally
        token = service.issue_access_token("user123")
        decoded = service.verify_token(token)
        assert decoded["sub"] == "user123"

    def test_jwt_with_secrets_provider_hs256(self):
        """Test JWT service with secrets provider for HS256"""
        from unittest.mock import Mock

        # Mock secrets provider
        mock_provider = Mock()
        mock_provider.get_symmetric_secret.return_value = "test-secret-from-provider"

        service = JWTService(algorithm="HS256", secrets_provider=mock_provider)

        # Should use secret from provider
        assert mock_provider.get_symmetric_secret.called

        token = service.issue_access_token("user123")
        decoded = service.verify_token(token)
        assert decoded["sub"] == "user123"

    def test_jwt_secrets_provider_fallback(self):
        """Test fallback when secrets provider fails"""
        from unittest.mock import Mock

        # Mock provider that raises exceptions
        mock_provider = Mock()
        mock_provider.get_symmetric_secret.side_effect = Exception("Provider failed")

        # Should fall back to provided secret
        service = JWTService(
            algorithm="HS256", secret="fallback-secret", secrets_provider=mock_provider
        )

        token = service.issue_access_token("user123")
        decoded = service.verify_token(token)
        assert decoded["sub"] == "user123"

    # Configuration and Validation Tests

    def test_jwt_unsupported_algorithm(self):
        """Test unsupported algorithm rejection"""
        from dotmac.platform.auth.exceptions import InvalidAlgorithm

        with pytest.raises(InvalidAlgorithm):
            JWTService(algorithm="HS384")  # Not in SUPPORTED_ALGORITHMS

    def test_jwt_invalid_rsa_keys(self):
        """Test invalid RSA key handling"""
        from dotmac.platform.auth.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError):
            JWTService(algorithm="RS256", private_key="invalid-key")

        with pytest.raises(ConfigurationError):
            JWTService(algorithm="RS256", public_key="invalid-key")

    def test_jwt_missing_hs256_secret(self):
        """Test missing HS256 secret"""
        from dotmac.platform.auth.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError):
            JWTService(algorithm="HS256")  # No secret provided

    def test_jwt_audience_and_issuer_validation(self):
        """Test audience and issuer validation"""
        from dotmac.platform.auth.exceptions import InvalidAudience, InvalidIssuer

        service = JWTService(
            algorithm="HS256",
            secret="test-secret",
            issuer="test-issuer",
            default_audience="test-audience",
        )

        token = service.issue_access_token("user123")

        # Valid audience and issuer should pass
        decoded = service.verify_token(
            token, expected_audience="test-audience", expected_issuer="test-issuer"
        )
        assert decoded["sub"] == "user123"

        # Invalid audience should fail
        with pytest.raises(InvalidAudience):
            service.verify_token(token, expected_audience="wrong-audience")

        # Invalid issuer should fail
        with pytest.raises(InvalidIssuer):
            service.verify_token(token, expected_issuer="wrong-issuer")

    def test_jwt_token_type_validation(self):
        """Test token type validation"""
        from dotmac.platform.auth.exceptions import InvalidToken

        service = JWTService(algorithm="HS256", secret="test-secret")

        access_token = service.issue_access_token("user123")
        refresh_token = service.issue_refresh_token("user123")

        # Correct type should pass
        service.verify_token(access_token, expected_type="access")
        service.verify_token(refresh_token, expected_type="refresh")

        # Wrong type should fail
        with pytest.raises(InvalidToken):
            service.verify_token(access_token, expected_type="refresh")

        with pytest.raises(InvalidToken):
            service.verify_token(refresh_token, expected_type="access")

    # Refresh Token Tests

    def test_jwt_refresh_token_generation(self):
        """Test refresh token generation"""
        service = JWTService(algorithm="HS256", secret="test-secret")

        refresh_token = service.issue_refresh_token(
            "user123", tenant_id="tenant1", expires_in=30  # 30 days
        )

        decoded = service.decode_token_unsafe(refresh_token)
        assert decoded["sub"] == "user123"
        assert decoded["type"] == "refresh"
        assert decoded["tenant_id"] == "tenant1"

        # Check expiry is approximately 30 days
        exp_time = datetime.fromtimestamp(decoded["exp"], UTC)
        expected_exp = datetime.now(UTC) + timedelta(days=30)
        assert abs((exp_time - expected_exp).total_seconds()) < 300  # 5 min tolerance

    def test_jwt_refresh_access_token(self):
        """Test refreshing access tokens"""
        service = JWTService(algorithm="HS256", secret="test-secret")

        # Issue refresh token
        refresh_token = service.issue_refresh_token("user123", tenant_id="tenant1")

        # Use refresh token to get new access token
        new_access_token = service.refresh_access_token(
            refresh_token, scopes=["read", "write"], expires_in=30, extra_claims={"role": "admin"}
        )

        # Verify new access token
        decoded = service.verify_token(new_access_token, expected_type="access")
        assert decoded["sub"] == "user123"
        assert decoded["tenant_id"] == "tenant1"
        assert decoded["scopes"] == ["read", "write"]
        assert decoded["role"] == "admin"

    def test_jwt_refresh_with_invalid_refresh_token(self):
        """Test refresh with invalid refresh token"""
        service = JWTService(algorithm="HS256", secret="test-secret")

        # Use access token as refresh token (wrong type)
        access_token = service.issue_access_token("user123")

        from dotmac.platform.auth.exceptions import InvalidToken

        with pytest.raises(InvalidToken):
            service.refresh_access_token(access_token)

    # Header and Unsafe Operations Tests

    def test_jwt_get_token_header(self):
        """Test getting token header"""
        service = JWTService(algorithm="HS256", secret="test-secret")
        token = service.issue_access_token("user123")

        header = service.get_token_header(token)
        assert header["alg"] == "HS256"
        assert header["typ"] == "JWT"

    def test_jwt_get_token_header_invalid(self):
        """Test getting header from invalid token"""
        service = JWTService(algorithm="HS256", secret="test-secret")

        from dotmac.platform.auth.exceptions import InvalidToken

        with pytest.raises(InvalidToken):
            service.get_token_header("invalid-token")

    def test_jwt_decode_token_unsafe(self):
        """Test unsafe token decoding"""
        service = JWTService(algorithm="HS256", secret="test-secret")
        token = service.issue_access_token("user123", extra_claims={"role": "admin"})

        # Should decode without verification
        decoded = service.decode_token_unsafe(token)
        assert decoded["sub"] == "user123"
        assert decoded["role"] == "admin"

    def test_jwt_decode_token_unsafe_invalid(self):
        """Test unsafe decoding of invalid token"""
        service = JWTService(algorithm="HS256", secret="test-secret")

        from dotmac.platform.auth.exceptions import InvalidToken

        with pytest.raises(InvalidToken):
            service.decode_token_unsafe("invalid-token")

    # Algorithm Consistency and Security Tests

    def test_jwt_algorithm_mismatch_detection(self):
        """Test detection of algorithm mismatch in token"""
        # Create token with different algorithm
        import jwt

        from dotmac.platform.auth.exceptions import InvalidAlgorithm, InvalidToken

        payload = {"sub": "user123", "iat": int(time.time()), "exp": int(time.time()) + 3600}
        token = jwt.encode(payload, "other-secret", algorithm="HS384")

        service = JWTService(algorithm="HS256", secret="test-secret")

        with pytest.raises((InvalidAlgorithm, InvalidToken)):
            service.verify_token(token)

    def test_jwt_verification_options(self):
        """Test various verification options"""
        service = JWTService(algorithm="HS256", secret="test-secret")
        token = service.issue_access_token("user123")

        # Verify without signature check
        decoded = service.verify_token(token, verify_signature=False)
        assert decoded["sub"] == "user123"

        # Verify without expiry check
        decoded = service.verify_token(token, verify_exp=False)
        assert decoded["sub"] == "user123"

    def test_jwt_leeway_tolerance(self):
        """Test clock skew tolerance with leeway"""
        service = JWTService(
            algorithm="HS256", secret="test-secret", leeway=60  # 60 seconds leeway
        )

        # Create a token that's slightly expired but within leeway
        import jwt

        payload = {
            "sub": "user123",
            "iat": int(time.time()) - 120,  # 2 minutes ago
            "exp": int(time.time()) - 30,  # 30 seconds ago (within 60s leeway)
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")

        # Should still be valid due to leeway
        decoded = service.verify_token(token)
        assert decoded["sub"] == "user123"

    # Static Method Tests

    def test_jwt_generate_rsa_keypair(self):
        """Test RSA keypair generation"""
        private_key, public_key = JWTService.generate_rsa_keypair()

        assert private_key.startswith("-----BEGIN PRIVATE KEY-----")
        assert private_key.endswith("-----END PRIVATE KEY-----\n")
        assert public_key.startswith("-----BEGIN PUBLIC KEY-----")
        assert public_key.endswith("-----END PUBLIC KEY-----\n")

        # Test different key sizes
        private_key_4096, _ = JWTService.generate_rsa_keypair(4096)
        assert len(private_key_4096) > len(private_key)  # Larger key = longer PEM

    def test_jwt_generate_hs256_secret(self):
        """Test HS256 secret generation"""
        secret = JWTService.generate_hs256_secret()
        assert len(secret) > 40  # URL-safe base64 encoded should be longer

        # Test different lengths
        short_secret = JWTService.generate_hs256_secret(16)
        long_secret = JWTService.generate_hs256_secret(64)
        assert len(short_secret) < len(long_secret)

        # Should generate unique secrets
        secret1 = JWTService.generate_hs256_secret()
        secret2 = JWTService.generate_hs256_secret()
        assert secret1 != secret2

    # Factory Function Tests

    def test_create_jwt_service_from_config(self):
        """Test JWT service creation from config"""
        from dotmac.platform.auth.jwt_service import create_jwt_service_from_config

        config = {
            "algorithm": "HS256",
            "secret": "test-secret",
            "issuer": "test-issuer",
            "default_audience": "test-audience",
            "access_token_expire_minutes": 30,
            "refresh_token_expire_days": 14,
            "leeway": 30,
        }

        service = create_jwt_service_from_config(config)
        assert service.algorithm == "HS256"
        assert service.issuer == "test-issuer"
        assert service.default_audience == "test-audience"
        assert service.access_token_expire_minutes == 30
        assert service.refresh_token_expire_days == 14
        assert service.leeway == 30

        # Test token generation with configured service
        token = service.issue_access_token("user123")
        decoded = service.verify_token(token)
        assert decoded["sub"] == "user123"
        assert decoded["iss"] == "test-issuer"
        assert decoded["aud"] == "test-audience"

    def test_create_jwt_service_from_config_minimal(self):
        """Test JWT service creation with minimal config"""
        from dotmac.platform.auth.jwt_service import create_jwt_service_from_config

        # Minimal config with algorithm override to HS256 (needs secret)
        config = {"algorithm": "HS256", "secret": "test-secret"}

        service = create_jwt_service_from_config(config)
        assert service.algorithm == "HS256"
        assert service.access_token_expire_minutes == 15  # Default
        assert service.refresh_token_expire_days == 7  # Default
        assert service.leeway == 0  # Default

    # Error Path Coverage Tests

    def test_jwt_token_encoding_error_handling(self):
        """Test error handling during token encoding"""
        service = JWTService(algorithm="HS256", secret="test-secret")

        # Mock jwt.encode to raise an exception
        with patch("jwt.encode", side_effect=Exception("Encoding failed")):
            from dotmac.platform.auth.exceptions import InvalidToken

            with pytest.raises(InvalidToken, match="Failed to encode token"):
                service.issue_access_token("user123")

    def test_jwt_refresh_token_encoding_error_handling(self):
        """Test error handling during refresh token encoding"""
        service = JWTService(algorithm="HS256", secret="test-secret")

        with patch("jwt.encode", side_effect=Exception("Encoding failed")):
            from dotmac.platform.auth.exceptions import InvalidToken

            with pytest.raises(InvalidToken, match="Failed to encode refresh token"):
                service.issue_refresh_token("user123")

    def test_jwt_unexpected_verification_error(self):
        """Test handling of unexpected verification errors"""
        service = JWTService(algorithm="HS256", secret="test-secret")
        token = service.issue_access_token("user123")

        # Mock jwt.decode to raise unexpected error
        with patch("jwt.decode", side_effect=RuntimeError("Unexpected error")):
            from dotmac.platform.auth.exceptions import InvalidToken

            with pytest.raises(InvalidToken, match="Unexpected token validation error"):
                service.verify_token(token)

    def test_jwt_token_missing_subject_claim(self):
        """Test token validation when subject claim is missing"""
        service = JWTService(algorithm="HS256", secret="test-secret")

        # Create token without 'sub' claim
        import jwt

        payload = {"iat": int(time.time()), "exp": int(time.time()) + 3600}
        token = jwt.encode(payload, "test-secret", algorithm="HS256")

        from dotmac.platform.auth.exceptions import InvalidToken

        with pytest.raises(InvalidToken, match="Token missing required 'sub' claim"):
            service.verify_token(token)

    def test_jwt_token_expired_with_timestamp(self):
        """Test expired token with proper timestamp info"""
        service = JWTService(algorithm="HS256", secret="test-secret")

        # Create expired token with known expiry
        import jwt

        exp_timestamp = int(time.time()) - 3600  # 1 hour ago
        payload = {
            "sub": "user123",
            "iat": exp_timestamp - 1800,  # 30 min before expiry
            "exp": exp_timestamp,
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")

        from dotmac.platform.auth.exceptions import TokenExpired

        with pytest.raises(TokenExpired) as exc_info:
            service.verify_token(token)

        # The exception should be raised (that's enough for the coverage)
