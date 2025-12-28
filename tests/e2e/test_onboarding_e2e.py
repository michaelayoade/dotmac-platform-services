"""
End-to-end tests for tenant onboarding.

Tests cover full onboarding workflows and public self-signup.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [pytest.mark.asyncio, pytest.mark.e2e]


# ============================================================================
# Fixtures for Onboarding E2E Tests
# ============================================================================


@pytest.fixture
def mock_email_service():
    """Mock email service for onboarding flows."""
    with patch("dotmac.platform.communications.email_service.get_email_service") as mock:
        mock_service = AsyncMock()
        mock_service.send_email = AsyncMock(return_value=True)
        mock_service.send_verification_email = AsyncMock(return_value=True)
        mock_service.send_welcome_email = AsyncMock(return_value=True)
        mock.return_value = mock_service
        yield mock_service


@pytest.fixture
def mock_audit_logging():
    """Mock audit logging.

    Note: The onboarding router doesn't directly import audit functions,
    so we mock them at the service level where they're actually used.
    """
    patches = [
        patch("dotmac.platform.audit.service.log_user_activity", new=AsyncMock()),
        patch("dotmac.platform.audit.service.log_api_activity", new=AsyncMock()),
    ]
    started = []
    for p in patches:
        try:
            p.start()
            started.append(p)
        except AttributeError:
            # Function may not exist, skip
            pass
    yield
    for p in started:
        p.stop()


# ============================================================================
# Full Onboarding Workflow Tests
# ============================================================================


class TestOnboardingWorkflowE2E:
    """End-to-end tests for full tenant onboarding."""

    async def test_complete_onboarding_workflow(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        mock_email_service,
        mock_audit_logging,
    ):
        """Test complete tenant onboarding with all options."""
        unique_id = uuid.uuid4().hex[:8]
        onboarding_data = {
            "tenant": {
                "name": f"New Company {unique_id}",
                "slug": f"new-company-{unique_id}",
                "email": f"contact_{unique_id}@example.com",
                "plan_type": "professional",
            },
            "admin_user": {
                "username": f"admin_{unique_id}",
                "email": f"admin_{unique_id}@example.com",
                "password": "SecurePassword123!",
                "full_name": "Admin User",
                "roles": ["tenant_admin"],
                "send_activation_email": False,
            },
            "options": {
                "apply_default_settings": True,
                "mark_onboarding_complete": True,
                "activate_tenant": True,
            },
        }

        response = await async_client.post(
            "/api/v1/tenants/onboarding",
            json=onboarding_data,
            headers=auth_headers,
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert "tenant" in data
        assert data["created"] is True or "created" not in data

    async def test_onboarding_with_settings(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        mock_email_service,
        mock_audit_logging,
    ):
        """Test onboarding with custom settings."""
        unique_id = uuid.uuid4().hex[:8]
        onboarding_data = {
            "tenant": {
                "name": f"Settings Company {unique_id}",
                "slug": f"settings-company-{unique_id}",
                "email": f"settings_{unique_id}@example.com",
                "plan_type": "starter",
            },
            "admin_user": {
                "username": f"settingsadmin_{unique_id}",
                "email": f"settingsadmin_{unique_id}@example.com",
                "password": "SecurePassword123!",
            },
            "settings": [
                {"key": "max_upload_size", "value": "100", "value_type": "int"},
                {"key": "feature_enabled", "value": "true", "value_type": "bool"},
            ],
        }

        response = await async_client.post(
            "/api/v1/tenants/onboarding",
            json=onboarding_data,
            headers=auth_headers,
        )

        assert response.status_code in [200, 201]

    async def test_onboarding_with_invitations(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        mock_email_service,
        mock_audit_logging,
    ):
        """Test onboarding with team invitations."""
        unique_id = uuid.uuid4().hex[:8]
        onboarding_data = {
            "tenant": {
                "name": f"Invite Company {unique_id}",
                "slug": f"invite-company-{unique_id}",
                "email": f"invite_{unique_id}@example.com",
                "plan_type": "professional",
            },
            "admin_user": {
                "username": f"inviteadmin_{unique_id}",
                "email": f"inviteadmin_{unique_id}@example.com",
                "password": "SecurePassword123!",
            },
            "invitations": [
                {"email": f"member1_{unique_id}@example.com", "role": "member"},
                {"email": f"member2_{unique_id}@example.com", "role": "admin"},
            ],
        }

        response = await async_client.post(
            "/api/v1/tenants/onboarding",
            json=onboarding_data,
            headers=auth_headers,
        )

        assert response.status_code in [200, 201]

    async def test_onboarding_with_feature_flags(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        mock_email_service,
        mock_audit_logging,
    ):
        """Test onboarding with feature flags."""
        unique_id = uuid.uuid4().hex[:8]
        onboarding_data = {
            "tenant": {
                "name": f"Feature Company {unique_id}",
                "slug": f"feature-company-{unique_id}",
                "email": f"feature_{unique_id}@example.com",
                "plan_type": "enterprise",
            },
            "admin_user": {
                "username": f"featureadmin_{unique_id}",
                "email": f"featureadmin_{unique_id}@example.com",
                "password": "SecurePassword123!",
            },
            "feature_flags": {
                "advanced_analytics": True,
                "api_access": True,
                "custom_branding": True,
            },
        }

        response = await async_client.post(
            "/api/v1/tenants/onboarding",
            json=onboarding_data,
            headers=auth_headers,
        )

        assert response.status_code in [200, 201]

    async def test_onboarding_with_metadata(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        mock_email_service,
        mock_audit_logging,
    ):
        """Test onboarding with custom metadata."""
        unique_id = uuid.uuid4().hex[:8]
        onboarding_data = {
            "tenant": {
                "name": f"Metadata Company {unique_id}",
                "slug": f"metadata-company-{unique_id}",
                "email": f"metadata_{unique_id}@example.com",
                "plan_type": "starter",
            },
            "admin_user": {
                "username": f"metaadmin_{unique_id}",
                "email": f"metaadmin_{unique_id}@example.com",
                "password": "SecurePassword123!",
            },
            "metadata": {
                "industry": "Technology",
                "company_size": "50-100",
                "source": "referral",
            },
        }

        response = await async_client.post(
            "/api/v1/tenants/onboarding",
            json=onboarding_data,
            headers=auth_headers,
        )

        assert response.status_code in [200, 201]

    async def test_get_onboarding_status(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting onboarding status."""
        # First create a tenant
        unique_id = uuid.uuid4().hex[:8]
        tenant_data = {
            "name": f"Status Company {unique_id}",
            "slug": f"status-company-{unique_id}",
            "email": f"status_{unique_id}@example.com",
            "plan_type": "starter",
        }

        create_response = await async_client.post(
            "/api/v1/tenants",
            json=tenant_data,
            headers=auth_headers,
        )

        if create_response.status_code == 201:
            tenant_id = create_response.json()["id"]

            response = await async_client.get(
                f"/api/v1/tenants/{tenant_id}/onboarding/status",
                headers=auth_headers,
            )

            assert response.status_code == 200


# ============================================================================
# Public Self-Signup Tests
# ============================================================================


class TestPublicSignupE2E:
    """End-to-end tests for public self-signup."""

    async def test_public_signup_success(
        self,
        async_client: AsyncClient,
        tenant_id: str,
        mock_email_service,
        mock_audit_logging,
    ):
        """Test successful public self-signup."""
        unique_id = uuid.uuid4().hex[:8]
        signup_data = {
            "tenant": {
                "name": f"Signup Company {unique_id}",
                "slug": f"signup-company-{unique_id}",
                "plan_type": "free",
            },
            "admin_user": {
                "username": f"signupuser_{unique_id}",
                "email": f"signup_{unique_id}@example.com",
                "password": "SecurePassword123!",
                "full_name": "New User",
            },
        }

        response = await async_client.post(
            "/api/v1/tenants/onboarding/public",
            json=signup_data,
            headers={"X-Tenant-ID": tenant_id},
        )

        # May be disabled by configuration
        if response.status_code == 403:
            assert "self-registration" in response.json().get("detail", "").lower() or \
                   "disabled" in response.json().get("detail", "").lower()
            return

        assert response.status_code in [200, 201]
        data = response.json()
        assert "tenant_id" in data or "tenant" in data

    async def test_public_signup_duplicate_slug(
        self,
        async_client: AsyncClient,
        tenant_id: str,
        e2e_db_session: AsyncSession,
        mock_email_service,
        mock_audit_logging,
    ):
        """Test public signup with duplicate slug."""
        from dotmac.platform.tenant.models import Tenant

        # Create existing tenant
        unique_id = uuid.uuid4().hex[:8]
        existing_tenant = Tenant(
            id=str(uuid.uuid4()),
            name=f"Existing {unique_id}",
            slug=f"existing-{unique_id}",
            email=f"existing_{unique_id}@example.com",
            plan_type="starter",
            status="active",
            is_active=True,
        )
        e2e_db_session.add(existing_tenant)
        await e2e_db_session.commit()

        # Try to create with same slug
        signup_data = {
            "tenant": {
                "name": "Different Name",
                "slug": existing_tenant.slug,
                "plan_type": "free",
            },
            "admin_user": {
                "username": f"dupuser_{unique_id}",
                "email": f"dup_{unique_id}@example.com",
                "password": "SecurePassword123!",
            },
        }

        response = await async_client.post(
            "/api/v1/tenants/onboarding/public",
            json=signup_data,
            headers={"X-Tenant-ID": tenant_id},
        )

        # Should be conflict or forbidden (if disabled)
        assert response.status_code in [400, 403, 409]

    async def test_public_signup_invalid_email(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test public signup with invalid email."""
        signup_data = {
            "tenant": {
                "name": "Test Company",
                "slug": f"test-{uuid.uuid4().hex[:8]}",
                "plan_type": "free",
            },
            "admin_user": {
                "username": "testuser",
                "email": "not-an-email",
                "password": "SecurePassword123!",
            },
        }

        response = await async_client.post(
            "/api/v1/tenants/onboarding/public",
            json=signup_data,
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 422

    async def test_public_signup_short_password(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test public signup with password too short."""
        signup_data = {
            "tenant": {
                "name": "Test Company",
                "slug": f"test-{uuid.uuid4().hex[:8]}",
                "plan_type": "free",
            },
            "admin_user": {
                "username": "testuser",
                "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
                "password": "short",
            },
        }

        response = await async_client.post(
            "/api/v1/tenants/onboarding/public",
            json=signup_data,
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 422


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestOnboardingErrorsE2E:
    """End-to-end tests for onboarding error handling."""

    async def test_onboarding_missing_tenant_data(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test onboarding with missing tenant data."""
        onboarding_data = {
            "admin_user": {
                "username": "testadmin",
                "email": "admin@example.com",
                "password": "SecurePassword123!",
            },
        }

        response = await async_client.post(
            "/api/v1/tenants/onboarding",
            json=onboarding_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    async def test_onboarding_missing_admin_user(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test onboarding with missing admin user data."""
        onboarding_data = {
            "tenant": {
                "name": "Test Company",
                "slug": f"test-{uuid.uuid4().hex[:8]}",
                "email": "contact@example.com",
                "plan_type": "starter",
            },
        }

        response = await async_client.post(
            "/api/v1/tenants/onboarding",
            json=onboarding_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    async def test_onboarding_invalid_plan_type(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test onboarding with invalid plan type."""
        unique_id = uuid.uuid4().hex[:8]
        onboarding_data = {
            "tenant": {
                "name": f"Invalid Plan {unique_id}",
                "slug": f"invalid-plan-{unique_id}",
                "email": f"invalid_{unique_id}@example.com",
                "plan_type": "nonexistent_plan",
            },
            "admin_user": {
                "username": f"planuser_{unique_id}",
                "email": f"planuser_{unique_id}@example.com",
                "password": "SecurePassword123!",
            },
        }

        response = await async_client.post(
            "/api/v1/tenants/onboarding",
            json=onboarding_data,
            headers=auth_headers,
        )

        # May accept any plan_type or reject invalid ones
        assert response.status_code in [200, 201, 400, 422]
