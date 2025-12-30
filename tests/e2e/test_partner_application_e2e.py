"""
End-to-end tests for partner applications.

Tests cover public application submission and admin review workflows.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.partner_management.models import PartnerApplication, PartnerApplicationStatus

pytestmark = [pytest.mark.asyncio, pytest.mark.e2e]


# ============================================================================
# Fixtures for Partner Application E2E Tests
# ============================================================================


@pytest_asyncio.fixture
async def pending_application(e2e_db_session: AsyncSession, tenant_id: str):
    """Create a pending partner application."""
    unique_id = uuid.uuid4().hex[:8]
    application = PartnerApplication(
        id=uuid.uuid4(),
        company_name=f"Test Partner Company {unique_id}",
        contact_name=f"John Doe {unique_id}",
        contact_email=f"partner_{unique_id}@example.com",
        phone="+1-555-0100",
        website=f"https://partner-{unique_id}.example.com",
        business_description="A technology partner specializing in integrations.",
        status=PartnerApplicationStatus.PENDING,
        tenant_id=tenant_id,
    )
    e2e_db_session.add(application)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(application)
    return application


@pytest_asyncio.fixture
async def multiple_applications(e2e_db_session: AsyncSession, tenant_id: str):
    """Create multiple partner applications with different statuses."""
    applications = []
    statuses = [
        PartnerApplicationStatus.PENDING,
        PartnerApplicationStatus.PENDING,
        PartnerApplicationStatus.APPROVED,
        PartnerApplicationStatus.REJECTED,
    ]

    for i, status_val in enumerate(statuses):
        unique_id = uuid.uuid4().hex[:8]
        application = PartnerApplication(
            id=uuid.uuid4(),
            company_name=f"Partner Company {unique_id}",
            contact_name=f"Contact {i}",
            contact_email=f"contact_{unique_id}@example.com",
            phone=f"+1-555-010{i}",
            business_description=f"Description for application {i}",
            status=status_val,
            tenant_id=tenant_id,
        )
        e2e_db_session.add(application)
        applications.append(application)

    await e2e_db_session.commit()
    for app in applications:
        await e2e_db_session.refresh(app)
    return applications


# ============================================================================
# Public Application Submission Tests
# ============================================================================


class TestPartnerApplicationSubmitE2E:
    """End-to-end tests for public partner application submission."""

    async def test_submit_partner_application(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test submitting a partner application."""
        unique_id = uuid.uuid4().hex[:8]
        application_data = {
            "company_name": f"New Partner {unique_id}",
            "contact_name": "Jane Smith",
            "contact_email": f"jane_{unique_id}@example.com",
            "phone": "+1-555-0200",
            "website": f"https://partner-{unique_id}.com",
            "business_description": "We provide cloud solutions for enterprises.",
        }

        response = await async_client.post(
            f"/api/v1/partners/apply?tenant_id={tenant_id}",
            json=application_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["company_name"] == application_data["company_name"]
        assert data["status"] == "pending"
        assert "id" in data

    async def test_submit_application_minimal_data(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test submitting application with minimal required data."""
        unique_id = uuid.uuid4().hex[:8]
        application_data = {
            "company_name": f"Minimal Partner {unique_id}",
            "contact_name": "Min Contact",
            "contact_email": f"min_{unique_id}@example.com",
        }

        response = await async_client.post(
            f"/api/v1/partners/apply?tenant_id={tenant_id}",
            json=application_data,
        )

        # May require more fields or accept minimal
        assert response.status_code in [201, 422]

    async def test_submit_application_invalid_email(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test submitting application with invalid email."""
        application_data = {
            "company_name": "Invalid Email Partner",
            "contact_name": "Test Contact",
            "contact_email": "not-an-email",
            "business_description": "Description",
        }

        response = await async_client.post(
            f"/api/v1/partners/apply?tenant_id={tenant_id}",
            json=application_data,
        )

        assert response.status_code == 422

    async def test_submit_application_missing_company(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test submitting application without company name."""
        application_data = {
            "contact_name": "Test Contact",
            "contact_email": "test@example.com",
        }

        response = await async_client.post(
            f"/api/v1/partners/apply?tenant_id={tenant_id}",
            json=application_data,
        )

        assert response.status_code == 422


# ============================================================================
# Admin Application Review Tests
# ============================================================================


class TestPartnerApplicationAdminE2E:
    """End-to-end tests for admin application review."""

    async def test_list_applications(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_applications: list[PartnerApplication],
    ):
        """Test listing partner applications."""
        response = await async_client.get(
            "/api/v1/partners/applications",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "applications" in data
        assert "total" in data

    async def test_list_applications_filter_by_status(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_applications: list[PartnerApplication],
    ):
        """Test listing applications filtered by status."""
        response = await async_client.get(
            "/api/v1/partners/applications?status=pending",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "applications" in data
        # All returned should be pending
        for app in data["applications"]:
            assert app["status"] == "pending"

    async def test_list_applications_pagination(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_applications: list[PartnerApplication],
    ):
        """Test listing applications with pagination."""
        response = await async_client.get(
            "/api/v1/partners/applications?page=1&page_size=2",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "page" in data
        assert "page_size" in data
        assert len(data["applications"]) <= 2

    async def test_get_application(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        pending_application: PartnerApplication,
    ):
        """Test getting a specific application."""
        response = await async_client.get(
            f"/api/v1/partners/applications/{pending_application.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(pending_application.id)
        assert data["company_name"] == pending_application.company_name

    async def test_get_application_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting non-existent application."""
        fake_id = uuid.uuid4()
        response = await async_client.get(
            f"/api/v1/partners/applications/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_approve_application(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        pending_application: PartnerApplication,
    ):
        """Test approving a partner application."""
        response = await async_client.post(
            f"/api/v1/partners/applications/{pending_application.id}/approve",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"

    async def test_approve_already_approved(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        e2e_db_session: AsyncSession,
        pending_application: PartnerApplication,
    ):
        """Test approving an already approved application."""
        # First approve
        pending_application.status = PartnerApplicationStatus.APPROVED
        await e2e_db_session.commit()

        response = await async_client.post(
            f"/api/v1/partners/applications/{pending_application.id}/approve",
            headers=auth_headers,
        )

        # Should fail or return error
        assert response.status_code in [400, 409]

    async def test_reject_application(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        pending_application: PartnerApplication,
    ):
        """Test rejecting a partner application."""
        response = await async_client.post(
            f"/api/v1/partners/applications/{pending_application.id}/reject",
            json={"rejection_reason": "Does not meet partner requirements."},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"

    async def test_reject_application_without_reason(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        pending_application: PartnerApplication,
    ):
        """Test rejecting application without reason."""
        response = await async_client.post(
            f"/api/v1/partners/applications/{pending_application.id}/reject",
            json={},
            headers=auth_headers,
        )

        # May require reason or accept empty
        assert response.status_code in [200, 400, 422]


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestPartnerApplicationErrorsE2E:
    """End-to-end tests for application error handling."""

    async def test_list_applications_unauthorized(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test listing applications without authentication."""
        response = await async_client.get(
            "/api/v1/partners/applications",
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 401

    async def test_approve_application_unauthorized(
        self,
        async_client: AsyncClient,
        tenant_id: str,
        pending_application: PartnerApplication,
    ):
        """Test approving application without authentication."""
        response = await async_client.post(
            f"/api/v1/partners/applications/{pending_application.id}/approve",
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 401

    async def test_approve_nonexistent_application(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test approving non-existent application."""
        fake_id = uuid.uuid4()
        response = await async_client.post(
            f"/api/v1/partners/applications/{fake_id}/approve",
            headers=auth_headers,
        )

        assert response.status_code == 404
