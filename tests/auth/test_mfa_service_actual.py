"""
Tests for MFA Service - matching actual implementation.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pyotp
import pytest

from dotmac.platform.auth.exceptions import AuthenticationError
from dotmac.platform.auth.mfa_service import (
    EmailProvider,
    MFADevice,
    MFAEnrollmentRequest,
    MFAMethod,
    MFAService,
    MFAServiceConfig,
    MFAStatus,
    MFAVerificationRequest,
    SMSProvider,
    TOTPSetupResponse,
    extract_mfa_claims,
    is_mfa_required_for_scope,
    is_mfa_token_valid,
)


class TestMFAEnums:
    """Test MFA enumeration types."""

    def test_mfa_method_values(self):
        """Test MFA method enum values."""
        assert MFAMethod.TOTP == "totp"
        assert MFAMethod.SMS == "sms"
        assert MFAMethod.EMAIL == "email"
        assert MFAMethod.BACKUP_CODE == "backup_code"

    def test_mfa_status_values(self):
        """Test MFA status enum values."""
        assert MFAStatus.PENDING == "pending"
        assert MFAStatus.ACTIVE == "active"
        assert MFAStatus.DISABLED == "disabled"


class TestMFAModels:
    """Test MFA data models."""

    def test_mfa_enrollment_request(self):
        """Test MFA enrollment request model."""
        request = MFAEnrollmentRequest(method=MFAMethod.TOTP, device_name="iPhone 15")

        assert request.method == MFAMethod.TOTP
        assert request.device_name == "iPhone 15"

    def test_mfa_verification_request(self):
        """Test MFA verification request model."""
        request = MFAVerificationRequest(challenge_token="challenge-abc", code="123456")

        assert request.challenge_token == "challenge-abc"
        assert request.code == "123456"

    def test_totp_setup_response(self):
        """Test TOTP setup response model."""
        response = TOTPSetupResponse(
            secret="JBSWY3DPEHPK3PXP",
            qr_code="data:image/png;base64,iVBORw0...",
            backup_codes=["ABC123", "DEF456"],
        )

        assert response.secret == "JBSWY3DPEHPK3PXP"
        assert response.qr_code.startswith("data:image/png")
        assert len(response.backup_codes) == 2

    def test_mfa_service_config(self):
        """Test MFA service configuration."""
        config = MFAServiceConfig(
            issuer_name="DotMac Platform",
            totp_digits=6,
            totp_period=30,
            backup_codes_count=10,
            sms_provider="twilio",
            email_provider="sendgrid",
        )

        assert config.issuer_name == "DotMac Platform"
        assert config.totp_digits == 6
        assert config.totp_period == 30
        assert config.backup_codes_count == 10


class TestMFAService:
    """Test MFA service functionality."""

    @pytest.fixture
    def mfa_service(self, mock_db_session):
        """Create MFA service instance."""
        config = MFAServiceConfig(issuer_name="Test Platform", totp_window=1, backup_codes_count=10)
        # Mock JWT service
        mock_jwt_service = Mock()
        return MFAService(
            database_session=mock_db_session, jwt_service=mock_jwt_service, config=config
        )

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = Mock()
        session.query = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        return session

    @pytest.mark.asyncio
    async def test_enroll_totp(self, mfa_service, mock_db_session):
        """Test TOTP enrollment."""
        user_id = str(uuid4())
        enrollment_request = MFAEnrollmentRequest(method=MFAMethod.TOTP, device_name="Test Device")

        # Mock database queries
        mock_db_session.query().filter().first.return_value = None  # No existing device
        mfa_service._get_user_devices = AsyncMock(return_value=[])

        result = await mfa_service.enroll_device(user_id, enrollment_request)

        assert isinstance(result, TOTPSetupResponse)
        assert result.secret is not None
        assert result.qr_code is not None
        assert len(result.backup_codes) > 0

    @pytest.mark.asyncio
    async def test_verify_totp(self, mfa_service, mock_db_session):
        """Test TOTP verification."""
        user_id = str(uuid4())
        secret = pyotp.random_base32()
        challenge_token = "test-challenge-token"

        # Create mock challenge
        mock_challenge = Mock()
        mock_challenge.device_id = "device-123"
        mock_challenge.user_id = user_id
        mock_challenge.verified_at = None
        mock_challenge.attempts = 0

        # Create mock device
        mock_device = Mock(spec=MFADevice)
        mock_device.secret = secret
        mock_device.status = MFAStatus.ACTIVE
        mock_device.method = MFAMethod.TOTP
        mock_device.failure_count = 0

        mfa_service._get_challenge = AsyncMock(return_value=mock_challenge)
        mfa_service._get_device = AsyncMock(return_value=mock_device)

        # Generate valid TOTP code
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()

        verification_request = MFAVerificationRequest(
            challenge_token=challenge_token, code=valid_code
        )

        result = await mfa_service.verify_mfa_challenge(verification_request)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_verify_totp_invalid_code(self, mfa_service, mock_db_session):
        """Test TOTP verification with invalid code."""
        user_id = str(uuid4())
        secret = pyotp.random_base32()
        challenge_token = "test-challenge-token"

        # Create mock challenge
        mock_challenge = Mock()
        mock_challenge.device_id = "device-123"
        mock_challenge.user_id = user_id
        mock_challenge.verified_at = None
        mock_challenge.attempts = 0

        # Create mock device
        mock_device = Mock(spec=MFADevice)
        mock_device.secret = secret
        mock_device.status = MFAStatus.ACTIVE
        mock_device.method = MFAMethod.TOTP
        mock_device.failure_count = 0

        mfa_service._get_challenge = AsyncMock(return_value=mock_challenge)
        mfa_service._get_device = AsyncMock(return_value=mock_device)

        verification_request = MFAVerificationRequest(
            challenge_token=challenge_token, code="000000"
        )

        with pytest.raises(AuthenticationError):
            await mfa_service.verify_mfa_challenge(verification_request)

    @pytest.mark.asyncio
    async def test_send_sms_code(self, mfa_service, mock_db_session):
        """Test SMS code sending."""
        user_id = str(uuid4())
        phone_number = "+1234567890"

        # Mock SMS provider
        mock_sms_provider = Mock(spec=SMSProvider)
        mock_sms_provider.send_code = AsyncMock(return_value=True)

        with patch.object(mfa_service, "sms_provider", mock_sms_provider):
            with patch.object(mfa_service, "db_session", mock_db_session):
                result = await mfa_service.send_sms_code(user_id, phone_number)

                assert result.success is True
                assert result.challenge_id is not None
                mock_sms_provider.send_code.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_code(self, mfa_service, mock_db_session):
        """Test email code sending."""
        user_id = str(uuid4())
        email = "user@example.com"

        # Mock email provider
        mock_email_provider = Mock(spec=EmailProvider)
        mock_email_provider.send_code = AsyncMock(return_value=True)

        with patch.object(mfa_service, "email_provider", mock_email_provider):
            with patch.object(mfa_service, "db_session", mock_db_session):
                result = await mfa_service.send_email_code(user_id, email)

                assert result.success is True
                assert result.challenge_id is not None
                mock_email_provider.send_code.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_backup_code(self, mfa_service, mock_db_session):
        """Test backup code verification."""
        user_id = str(uuid4())

        # Mock backup codes in database
        mock_device = Mock(spec=MFADevice)
        mock_device.backup_codes = ["CODE123", "CODE456", "CODE789"]
        mock_device.used_backup_codes = []

        mock_db_session.query().filter().first.return_value = mock_device

        with patch.object(mfa_service, "db_session", mock_db_session):
            result = await mfa_service.verify_backup_code(user_id, "CODE123")

            assert result is True
            # Code should be marked as used
            assert "CODE123" in mock_device.used_backup_codes

    @pytest.mark.asyncio
    async def test_verify_backup_code_already_used(self, mfa_service, mock_db_session):
        """Test backup code that's already been used."""
        user_id = str(uuid4())

        # Mock backup codes with one already used
        mock_device = Mock(spec=MFADevice)
        mock_device.backup_codes = ["CODE123", "CODE456"]
        mock_device.used_backup_codes = ["CODE123"]

        mock_db_session.query().filter().first.return_value = mock_device

        with patch.object(mfa_service, "db_session", mock_db_session):
            result = await mfa_service.verify_backup_code(user_id, "CODE123")

            assert result is False

    @pytest.mark.asyncio
    async def test_disable_mfa(self, mfa_service, mock_db_session):
        """Test disabling MFA for a user."""
        user_id = str(uuid4())

        # Mock active MFA devices
        mock_devices = [
            Mock(spec=MFADevice, status=MFAStatus.ACTIVE),
            Mock(spec=MFADevice, status=MFAStatus.ACTIVE),
        ]

        mock_db_session.query().filter().all.return_value = mock_devices

        with patch.object(mfa_service, "db_session", mock_db_session):
            result = await mfa_service.disable_mfa(user_id)

            assert result is True
            # All devices should be disabled
            for device in mock_devices:
                assert device.status == MFAStatus.DISABLED

    @pytest.mark.asyncio
    async def test_get_user_mfa_status(self, mfa_service, mock_db_session):
        """Test getting user's MFA status."""
        user_id = str(uuid4())

        # Mock active MFA devices
        mock_devices = [
            Mock(spec=MFADevice, method=MFAMethod.TOTP, status=MFAStatus.ACTIVE),
            Mock(spec=MFADevice, method=MFAMethod.SMS, status=MFAStatus.ACTIVE),
        ]

        mock_db_session.query().filter().all.return_value = mock_devices

        with patch.object(mfa_service, "db_session", mock_db_session):
            status = await mfa_service.get_user_mfa_status(user_id)

            assert status.enabled is True
            assert MFAMethod.TOTP in status.methods
            assert MFAMethod.SMS in status.methods


class TestMFAHelperFunctions:
    """Test MFA helper functions."""

    def test_extract_mfa_claims(self):
        """Test extracting MFA claims from token payload."""
        payload = {
            "sub": "user123",
            "mfa": {"verified": True, "method": "totp", "timestamp": "2024-01-01T12:00:00Z"},
        }

        claims = extract_mfa_claims(payload)

        assert claims is not None
        assert claims["verified"] is True
        assert claims["method"] == "totp"

    def test_extract_mfa_claims_missing(self):
        """Test extracting MFA claims when not present."""
        payload = {"sub": "user123", "exp": 1234567890}

        claims = extract_mfa_claims(payload)

        assert claims is None

    def test_is_mfa_required_for_scope(self):
        """Test checking if MFA is required for a scope."""
        mfa_required_scopes = ["admin", "sensitive", "financial"]

        assert is_mfa_required_for_scope("admin", mfa_required_scopes) is True
        assert is_mfa_required_for_scope("read", mfa_required_scopes) is False
        assert is_mfa_required_for_scope("financial", mfa_required_scopes) is True

    def test_is_mfa_token_valid(self):
        """Test MFA token validity check."""
        # Valid token (recent timestamp)
        valid_claims = {"verified": True, "timestamp": datetime.utcnow().isoformat()}

        assert is_mfa_token_valid(valid_claims, max_age_seconds=3600) is True

        # Expired token (old timestamp)
        expired_claims = {
            "verified": True,
            "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
        }

        assert is_mfa_token_valid(expired_claims, max_age_seconds=3600) is False

        # Not verified
        unverified_claims = {"verified": False, "timestamp": datetime.utcnow().isoformat()}

        assert is_mfa_token_valid(unverified_claims) is False
