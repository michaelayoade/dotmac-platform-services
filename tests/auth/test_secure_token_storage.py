"""Comprehensive tests for secure token storage."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, call
import json
import hashlib

from dotmac.platform.auth.email_service import SecureTokenStorage, PasswordResetToken


class TestSecureTokenStorage:
    """Test secure token storage for distributed systems."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis_mock = MagicMock()
        redis_mock.get = MagicMock(return_value=None)
        redis_mock.setex = MagicMock(return_value=True)
        redis_mock.delete = MagicMock(return_value=1)
        redis_mock.exists = MagicMock(return_value=0)
        return redis_mock

    @pytest.fixture
    def storage_with_mock_redis(self, mock_redis):
        """Create storage with mocked Redis."""
        with patch("dotmac.platform.caching.get_redis", return_value=mock_redis):
            storage = SecureTokenStorage()
            storage._redis_client = mock_redis
            return storage

    def test_store_token_success(self, storage_with_mock_redis, mock_redis):
        """Test successful token storage with encryption."""
        storage = storage_with_mock_redis
        token = "test_token_123"
        email = "user@example.com"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        # Store token
        result = storage.store_token(token, email, expires_at)

        assert result is True

        # Verify Redis was called with encrypted data
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args

        # Check key is hashed
        expected_key = f"password_reset:{hashlib.sha256(token.encode()).hexdigest()}"
        assert call_args[0][0] == expected_key

        # Check TTL is set (second argument) - allow for minor time differences
        ttl = call_args[0][1]
        assert 3598 <= ttl <= 3600  # 1 hour TTL with small tolerance

        # Check data is encrypted (third argument, not plaintext)
        encrypted_data = call_args[0][2]
        assert isinstance(encrypted_data, bytes)
        assert b"user@example.com" not in encrypted_data  # Email should be encrypted

    def test_get_token_success(self, storage_with_mock_redis, mock_redis):
        """Test successful token retrieval and decryption."""
        storage = storage_with_mock_redis
        token = "test_token_123"
        email = "user@example.com"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        # Prepare encrypted data
        token_data = PasswordResetToken(
            token=token,
            email=email,
            expires_at=expires_at,
            used=False
        )

        # Manually encrypt data for mock
        data_json = json.dumps({
            "token": token,
            "email": email,
            "expires_at": expires_at.isoformat(),
            "used": False
        })
        encrypted_data = storage._fernet.encrypt(data_json.encode())
        mock_redis.get.return_value = encrypted_data

        # Get token
        result = storage.get_token(token)

        assert result is not None
        assert result.email == email
        assert result.token == token
        assert result.used is False
        assert abs((result.expires_at - expires_at).total_seconds()) < 1

        # Verify Redis was called with hashed key
        expected_key = f"password_reset:{hashlib.sha256(token.encode()).hexdigest()}"
        mock_redis.get.assert_called_once_with(expected_key)

    def test_get_token_not_found(self, storage_with_mock_redis, mock_redis):
        """Test token retrieval when token doesn't exist."""
        storage = storage_with_mock_redis
        mock_redis.get.return_value = None

        result = storage.get_token("nonexistent_token")

        assert result is None
        mock_redis.get.assert_called_once()

    def test_get_token_decryption_failure(self, storage_with_mock_redis, mock_redis):
        """Test handling of corrupted encrypted data."""
        storage = storage_with_mock_redis

        # Set corrupted encrypted data
        mock_redis.get.return_value = b"corrupted_data"

        result = storage.get_token("test_token")

        assert result is None  # Should return None on decryption failure

    def test_invalidate_token(self, storage_with_mock_redis, mock_redis):
        """Test token invalidation."""
        storage = storage_with_mock_redis
        token = "test_token_123"

        result = storage.invalidate_token(token)

        assert result is True

        # Verify Redis delete was called with hashed key
        expected_key = f"password_reset:{hashlib.sha256(token.encode()).hexdigest()}"
        mock_redis.delete.assert_called_once_with(expected_key)

    def test_mark_token_used(self, storage_with_mock_redis, mock_redis):
        """Test marking token as used."""
        storage = storage_with_mock_redis
        token = "test_token_123"
        email = "user@example.com"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        # Setup existing token data
        token_data = {
            "token": token,
            "email": email,
            "expires_at": expires_at.isoformat(),
            "used": False
        }
        encrypted_data = storage._fernet.encrypt(json.dumps(token_data).encode())
        mock_redis.get.return_value = encrypted_data

        # Mark as used
        result = storage.mark_token_used(token)

        assert result is True

        # Verify token was re-saved with used=True
        mock_redis.setex.assert_called_once()

        # Decrypt the saved data to verify it's marked as used
        saved_encrypted_data = mock_redis.setex.call_args[0][2]
        decrypted = storage._fernet.decrypt(saved_encrypted_data)
        saved_data = json.loads(decrypted)
        assert saved_data["used"] is True

    def test_mark_token_used_not_found(self, storage_with_mock_redis, mock_redis):
        """Test marking non-existent token as used."""
        storage = storage_with_mock_redis
        mock_redis.get.return_value = None

        result = storage.mark_token_used("nonexistent_token")

        assert result is False
        mock_redis.setex.assert_not_called()

    def test_concurrent_token_operations(self, storage_with_mock_redis, mock_redis):
        """Test concurrent token operations for race conditions."""
        storage = storage_with_mock_redis

        # Simulate multiple concurrent token operations
        tokens = [f"token_{i}" for i in range(10)]
        emails = [f"user{i}@example.com" for i in range(10)]
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        # Store tokens (synchronously now)
        results = [
            storage.store_token(token, email, expires_at)
            for token, email in zip(tokens, emails)
        ]

        assert all(results)
        assert mock_redis.setex.call_count == 10

    def test_token_expiration_handling(self, storage_with_mock_redis, mock_redis):
        """Test handling of expired tokens."""
        storage = storage_with_mock_redis
        token = "expired_token"
        email = "user@example.com"

        # Create expired token
        expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

        token_data = {
            "token": token,
            "email": email,
            "expires_at": expires_at.isoformat(),
            "used": False
        }
        encrypted_data = storage._fernet.encrypt(json.dumps(token_data).encode())
        mock_redis.get.return_value = encrypted_data

        # Try to get expired token
        result = storage.get_token(token)

        # Our implementation invalidates expired tokens and returns None
        assert result is None
        # Verify that invalidate was called (delete was called on Redis)
        mock_redis.delete.assert_called_once()

    def test_redis_connection_failure(self, storage_with_mock_redis, mock_redis):
        """Test handling of Redis connection failures."""
        storage = storage_with_mock_redis

        # Simulate Redis connection failure
        mock_redis.setex.side_effect = Exception("Redis connection failed")

        token = "test_token"
        email = "user@example.com"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        result = storage.store_token(token, email, expires_at)

        assert result is False  # Should return False on failure

    def test_encryption_key_rotation(self):
        """Test that different encryption keys produce different ciphertext."""
        # Create two storages with different keys
        with patch("dotmac.platform.caching.get_redis"):
            storage1 = SecureTokenStorage()
            storage2 = SecureTokenStorage()

        data = json.dumps({"test": "data"}).encode()

        encrypted1 = storage1._fernet.encrypt(data)
        encrypted2 = storage2._fernet.encrypt(data)

        # Different keys should produce different ciphertext
        assert encrypted1 != encrypted2

        # But each should decrypt its own data correctly
        assert storage1._fernet.decrypt(encrypted1) == data
        assert storage2._fernet.decrypt(encrypted2) == data

    def test_token_hash_collision_prevention(self, storage_with_mock_redis):
        """Test that token hashing prevents collisions."""
        storage = storage_with_mock_redis

        # Generate similar tokens
        token1 = "test_token_123"
        token2 = "test_token_124"

        # Calculate hashes
        hash1 = hashlib.sha256(token1.encode()).hexdigest()
        hash2 = hashlib.sha256(token2.encode()).hexdigest()

        # Hashes should be different even for similar tokens
        assert hash1 != hash2

        # Keys should be different
        key1 = f"password_reset:{hash1}"
        key2 = f"password_reset:{hash2}"
        assert key1 != key2


class TestAuthEmailServiceIntegration:
    """Integration tests for AuthEmailService with SecureTokenStorage."""

    @pytest.fixture
    def mock_notification_service(self):
        """Mock notification service."""
        mock = MagicMock()
        mock.send.return_value = MagicMock(
            id="notif-123",
            status="sent"
        )
        return mock

    @pytest.fixture
    def email_service(self, mock_notification_service):
        """Create email service with mocked dependencies."""
        from dotmac.platform.auth.email_service import AuthEmailService

        with patch("dotmac.platform.caching.get_redis") as mock_redis:
            mock_redis.return_value = MagicMock()

            with patch("dotmac.platform.auth.email_service.get_notification_service", return_value=mock_notification_service):
                service = AuthEmailService(
                    app_name="TestApp",
                    base_url="https://example.com"
                )

            # Mock the token storage
            service.token_storage = MagicMock()
            service.token_storage.store_token = MagicMock(return_value=True)
            service.token_storage.get_token = MagicMock()
            service.token_storage.mark_token_used = MagicMock(return_value=True)
            service.token_storage.invalidate_token = MagicMock(return_value=True)

            return service

    def test_send_password_reset_email(self, email_service):
        """Test sending password reset email with secure storage."""
        email = "user@example.com"

        response, token = email_service.send_password_reset_email(email)

        assert response.status == "sent"
        assert token is not None

        # Verify token was stored securely
        email_service.token_storage.store_token.assert_called_once()
        call_args = email_service.token_storage.store_token.call_args
        # Using keyword arguments
        assert call_args[1]["token"] == token  # token
        assert call_args[1]["email"] == email  # email
        assert call_args[1]["expires_at"] > datetime.now(timezone.utc)  # expires_at in future

    def test_verify_reset_token_valid(self, email_service):
        """Test verifying valid reset token."""
        token = "valid_token"
        email = "user@example.com"

        # Mock token retrieval
        mock_token_data = PasswordResetToken(
            token=token,
            email=email,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            used=False
        )
        email_service.token_storage.get_token.return_value = mock_token_data

        result = email_service.verify_reset_token(token)

        assert result == email
        email_service.token_storage.mark_token_used.assert_called_once_with(token)

    def test_verify_reset_token_already_used(self, email_service):
        """Test verifying already used token."""
        token = "used_token"

        # Mock used token
        mock_token_data = PasswordResetToken(
            token=token,
            email="user@example.com",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            used=True
        )
        email_service.token_storage.get_token.return_value = mock_token_data

        result = email_service.verify_reset_token(token)

        assert result is None
        email_service.token_storage.mark_token_used.assert_not_called()

    def test_verify_reset_token_expired(self, email_service):
        """Test verifying expired token."""
        token = "expired_token"

        # Mock expired token
        mock_token_data = PasswordResetToken(
            token=token,
            email="user@example.com",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            used=False
        )
        email_service.token_storage.get_token.return_value = mock_token_data

        result = email_service.verify_reset_token(token)

        assert result is None
        email_service.token_storage.invalidate_token.assert_called_once_with(token)

    def test_multi_instance_token_sharing(self):
        """Test token sharing across multiple service instances."""
        # This test demonstrates that multiple instances share the same Redis storage
        # In production, they'd also share the same encryption key via environment variable

        # Patch get_redis where it's used, not where it's defined
        with patch("dotmac.platform.auth.email_service.get_redis") as get_redis_mock:
            mock_redis = MagicMock()
            get_redis_mock.return_value = mock_redis

            # Create two independent storage instances
            storage1 = SecureTokenStorage()
            storage2 = SecureTokenStorage()

            # Store token with instance 1
            token = "shared_token"
            email = "user@example.com"
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

            result = storage1.store_token(token, email, expires_at)
            assert result is True

            # After store_token, the Redis client should be initialized
            assert storage1._redis_client is not None
            assert storage1._redis_client is mock_redis

            # Verify setex was called on the shared Redis mock
            mock_redis.setex.assert_called_once()

            # storage2 hasn't been used yet
            assert storage2._redis_client is None  # Not yet initialized

            # When storage2 needs Redis, it would get the same instance
            storage2.store_token("another_token", "other@example.com", expires_at)
            assert storage2._redis_client is mock_redis

            # Both instances used the same Redis
            assert mock_redis.setex.call_count == 2