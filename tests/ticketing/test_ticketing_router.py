"""
Integration tests for the ticketing router.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from dotmac.platform.auth.core import UserInfo, get_current_user
from dotmac.platform.auth.dependencies import get_current_user_optional
from dotmac.platform.customer_management.models import (
    CommunicationChannel,
    Customer,
    CustomerStatus,
    CustomerTier,
    CustomerType,
)
from dotmac.platform.db import get_session_dependency
from dotmac.platform.partner_management.models import (
    CommissionModel,
    Partner,
    PartnerStatus,
    PartnerTier,
    PartnerUser,
)
from dotmac.platform.tenant import get_current_tenant_id
from dotmac.platform.ticketing.dependencies import get_ticket_service
from dotmac.platform.ticketing.models import Ticket, TicketActorType
from dotmac.platform.ticketing.router import router as ticketing_router
from dotmac.platform.user_management.models import User
from dotmac.platform.ticketing.service import (
    TicketAccessDeniedError,
    TicketNotFoundError,
    TicketService,
    TicketValidationError,
)


@pytest.fixture
def ticketing_app(async_db_session):
    """
    Build a dedicated FastAPI app for ticketing tests with dependency overrides.
    """

    app = FastAPI()
    app.include_router(ticketing_router, prefix="/api/v1/ticketing")

    current_user_holder: dict[str, UserInfo | None] = {"value": None}

    async def override_get_current_user():
        user = current_user_holder["value"]
        if user is None:
            raise AssertionError("Test must set current_user before making requests.")
        return user

    async def override_session():
        yield async_db_session

    def override_get_current_tenant_id():
        return "test-tenant"

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_user_optional] = override_get_current_user
    app.dependency_overrides[get_session_dependency] = override_session
    app.dependency_overrides[get_current_tenant_id] = override_get_current_tenant_id

    return app, current_user_holder


class _StubTicketService(TicketService):
    """Minimal stub that can be customised per test via callables."""

    def __init__(self, session, **handlers):
        super().__init__(session)
        self._handlers = handlers

    async def create_ticket(self, *args, **kwargs):
        handler = self._handlers.get("create_ticket")
        if handler:
            return await handler(*args, **kwargs)
        return await super().create_ticket(*args, **kwargs)

    async def list_tickets(self, *args, **kwargs):
        handler = self._handlers.get("list_tickets")
        if handler:
            return await handler(*args, **kwargs)
        return await super().list_tickets(*args, **kwargs)

    async def get_ticket(self, *args, **kwargs):
        handler = self._handlers.get("get_ticket")
        if handler:
            return await handler(*args, **kwargs)
        return await super().get_ticket(*args, **kwargs)

    async def add_message(self, *args, **kwargs):
        handler = self._handlers.get("add_message")
        if handler:
            return await handler(*args, **kwargs)
        return await super().add_message(*args, **kwargs)

    async def update_ticket(self, *args, **kwargs):
        handler = self._handlers.get("update_ticket")
        if handler:
            return await handler(*args, **kwargs)
        return await super().update_ticket(*args, **kwargs)


@pytest.mark.asyncio
@patch("dotmac.platform.ticketing.events.get_event_bus")
@patch("dotmac.platform.ticketing.router.get_current_tenant_id")
async def test_customer_creates_ticket_for_tenant(mock_get_tenant_id, mock_event_bus, async_db_session, ticketing_app):
    """Customers should be able to open tickets targeting their tenant support team."""
    mock_get_tenant_id.return_value = "test-tenant"
    # Mock event bus to avoid event publishing errors in tests
    from unittest.mock import AsyncMock
    mock_bus_instance = AsyncMock()
    mock_event_bus.return_value = mock_bus_instance

    app, current_user_holder = ticketing_app

    customer_user_id = uuid.uuid4()
    user = User(
        id=customer_user_id,
        username="customer-user",
        email="customer@example.com",
        password_hash="hashed",
        tenant_id="test-tenant",
        roles=["customer"],  # Add roles to match the test expectations
    )
    customer = Customer(
        id=uuid.uuid4(),
        customer_number="CUST-0001",
        first_name="Jane",
        last_name="Doe",
        status=CustomerStatus.ACTIVE,
        customer_type=CustomerType.INDIVIDUAL,
        tier=CustomerTier.BASIC,
        email="customer@example.com",
        preferred_channel=CommunicationChannel.EMAIL,
        tenant_id="test-tenant",
        user_id=customer_user_id,
    )
    async_db_session.add_all([user, customer])
    await async_db_session.commit()
    await async_db_session.refresh(customer)

    current_user_holder["value"] = UserInfo(
        user_id=str(customer_user_id),
        email="customer@example.com",
        username="customer-user",
        roles=["customer"],
        permissions=["tickets:create"],
        tenant_id="test-tenant",
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/ticketing/",
            json={
                "subject": "Need assistance",
                "message": "Our onboarding is blocked.",
                "target_type": "tenant",
                "priority": "high",
            },
        )

    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["origin_type"] == TicketActorType.CUSTOMER.value
    assert payload["target_type"] == TicketActorType.TENANT.value
    assert payload["customer_id"] == str(customer.id)
    assert payload["priority"] == "high"
    assert len(payload["messages"]) >= 1, "Should have at least one message"
    assert payload["messages"][0]["body"] == "Our onboarding is blocked."

    # Ensure ticket persisted with correct tenant association
    stored_ticket = await async_db_session.get(Ticket, uuid.UUID(payload["id"]))
    assert stored_ticket is not None
    assert stored_ticket.tenant_id == "test-tenant"
    assert stored_ticket.customer_id == customer.id


@pytest.mark.asyncio
@patch("dotmac.platform.ticketing.events.get_event_bus")
@patch("dotmac.platform.ticketing.router.get_current_tenant_id")
async def test_tenant_escalates_ticket_to_partner(mock_get_tenant_id, mock_event_bus, async_db_session, ticketing_app):
    """Tenant administrators should be able to escalate tickets to an active partner."""
    mock_get_tenant_id.return_value = "test-tenant"
    from unittest.mock import AsyncMock
    mock_bus_instance = AsyncMock()
    mock_event_bus.return_value = mock_bus_instance

    app, current_user_holder = ticketing_app

    partner = Partner(
        id=uuid.uuid4(),
        partner_number="PARTNER-001",
        company_name="Partner Co",
        primary_email="support@partner.co",
        status=PartnerStatus.ACTIVE,
        tier=PartnerTier.BRONZE,
        commission_model=CommissionModel.REVENUE_SHARE,
        tenant_id="test-tenant",
    )
    async_db_session.add(partner)
    await async_db_session.commit()
    await async_db_session.refresh(partner)

    current_user_holder["value"] = UserInfo(
        user_id=str(uuid.uuid4()),
        email="admin@tenant.com",
        username="tenant-admin",
        roles=["admin"],
        permissions=["tickets:create", "tickets:update"],
        tenant_id="test-tenant",
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/ticketing/",
            json={
                "subject": "Partner escalation",
                "message": "We need partner assistance on deployment.",
                "target_type": "partner",
                "partner_id": str(partner.id),
            },
        )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["partner_id"] == str(partner.id)
    assert data["origin_type"] == TicketActorType.TENANT.value
    assert data["target_type"] == TicketActorType.PARTNER.value


@pytest.mark.asyncio
@patch("dotmac.platform.ticketing.events.get_event_bus")
@patch("dotmac.platform.ticketing.router.get_current_tenant_id")
async def test_partner_appends_message_with_status_transition(mock_get_tenant_id, mock_event_bus, async_db_session, ticketing_app):
    """Partners should respond to tickets and transition status."""
    mock_get_tenant_id.return_value = "test-tenant"
    from unittest.mock import AsyncMock
    mock_bus_instance = AsyncMock()
    mock_event_bus.return_value = mock_bus_instance

    app, current_user_holder = ticketing_app

    # Prepare partner and associated user
    partner_id = uuid.uuid4()
    partner_user_account_id = uuid.uuid4()
    tenant_admin_id = uuid.uuid4()

    partner = Partner(
        id=partner_id,
        partner_number="PARTNER-9000",
        company_name="Reseller Partners",
        primary_email="ops@reseller.io",
        status=PartnerStatus.ACTIVE,
        tier=PartnerTier.SILVER,
        commission_model=CommissionModel.REVENUE_SHARE,
        tenant_id="test-tenant",
    )
    tenant_user = User(
        id=tenant_admin_id,
        username="tenant-user",
        email="tenant@example.com",
        password_hash="hashed",
        tenant_id="test-tenant",
        roles=["admin"],
    )
    partner_portal_user = User(
        id=partner_user_account_id,
        username="partner-portal",
        email="partner.user@example.com",
        password_hash="hashed",
        tenant_id="test-tenant",
    )
    partner_user = PartnerUser(
        id=uuid.uuid4(),
        partner_id=partner_id,
        first_name="Pat",
        last_name="Ner",
        email="partner.user@example.com",
        role="account_manager",
        is_primary_contact=True,
        user_id=partner_user_account_id,
        tenant_id="test-tenant",
    )

    async_db_session.add_all([partner, tenant_user, partner_portal_user, partner_user])
    await async_db_session.commit()
    await async_db_session.refresh(partner)
    await async_db_session.refresh(partner_user)

    # Tenant opens ticket to partner
    current_user_holder["value"] = UserInfo(
        user_id=str(tenant_admin_id),
        email="tenant@example.com",
        username="tenant-user",
        roles=["admin"],
        permissions=["tickets:create"],
        tenant_id="test-tenant",
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        create_resp = await client.post(
            "/api/v1/ticketing/",
            json={
                "subject": "Partner help needed",
                "message": "Please review our integration plan.",
                "target_type": "partner",
                "partner_id": str(partner_id),
            },
        )
        assert create_resp.status_code == 201, create_resp.text
        ticket_payload = create_resp.json()
        ticket_id = ticket_payload["id"]

        # Partner responds and moves ticket in progress
        current_user_holder["value"] = UserInfo(
            user_id=str(partner_user_account_id),
            email="partner.user@example.com",
            username="partner-portal",
            roles=["partner"],
            permissions=["tickets:respond"],
            tenant_id="test-tenant",
        )

        message_resp = await client.post(
            f"/api/v1/ticketing/{ticket_id}/messages",
            json={
                "message": "Review complete, proceeding with implementation.",
                "new_status": "in_progress",
            },
        )

    assert message_resp.status_code == 201, message_resp.text
    updated_ticket = message_resp.json()
    assert updated_ticket["status"] == "in_progress"
    assert len(updated_ticket["messages"]) >= 2, "Should have at least 2 messages"
    assert updated_ticket["messages"][-1]["sender_type"] == TicketActorType.PARTNER.value
    assert (
        updated_ticket["messages"][-1]["body"] == "Review complete, proceeding with implementation."
    )
    assert updated_ticket["partner_id"] == str(partner_id)
    assert updated_ticket["last_response_at"] is not None

    # Reload from database to verify persistence
    stored_ticket = await async_db_session.get(Ticket, uuid.UUID(ticket_id))
    assert stored_ticket.status == "in_progress"
    assert stored_ticket.partner_id == partner_id
    assert stored_ticket.last_response_at is not None
    assert stored_ticket.last_response_at <= datetime.now(UTC)


@pytest.mark.asyncio
async def test_create_ticket_maps_validation_error(async_db_session, ticketing_app):
    """Service validation errors should surface as HTTP 400 responses."""
    app, current_user_holder = ticketing_app

    async def raise_validation(*args, **kwargs):
        raise TicketValidationError("invalid data")

    async def override_service():
        return _StubTicketService(async_db_session, create_ticket=raise_validation)

    app.dependency_overrides[get_ticket_service] = override_service
    current_user_holder["value"] = UserInfo(
        user_id=str(uuid.uuid4()),
        email="user@example.com",
        username="user",
        roles=["customer"],
        permissions=["tickets:create"],
        tenant_id="test-tenant",
    )

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/ticketing/",
                json={
                    "subject": "Invalid",
                    "message": "Trigger validation error",
                    "target_type": "tenant",
                },
            )
    finally:
        app.dependency_overrides.pop(get_ticket_service, None)

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid data"


@pytest.mark.asyncio
async def test_add_message_maps_access_denied(async_db_session, ticketing_app):
    """Access denied should translate to HTTP 403."""
    app, current_user_holder = ticketing_app

    async def raise_forbidden(*args, **kwargs):
        raise TicketAccessDeniedError("not allowed")

    async def override_service():
        return _StubTicketService(async_db_session, add_message=raise_forbidden)

    app.dependency_overrides[get_ticket_service] = override_service
    current_user_holder["value"] = UserInfo(
        user_id=str(uuid.uuid4()),
        email="user@example.com",
        username="user",
        roles=["partner"],
        permissions=["tickets:respond"],
        tenant_id="test-tenant",
    )

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                f"/api/v1/ticketing/{uuid.uuid4()}/messages",
                json={"message": "Attempt response"},
            )
    finally:
        app.dependency_overrides.pop(get_ticket_service, None)

    assert response.status_code == 403
    assert response.json()["detail"] == "not allowed"


@pytest.mark.asyncio
async def test_get_ticket_maps_not_found(async_db_session, ticketing_app):
    """Missing tickets should produce 404."""
    app, current_user_holder = ticketing_app

    async def raise_not_found(*args, **kwargs):
        raise TicketNotFoundError("missing ticket")

    async def override_service():
        return _StubTicketService(async_db_session, get_ticket=raise_not_found)

    app.dependency_overrides[get_ticket_service] = override_service
    current_user_holder["value"] = UserInfo(
        user_id=str(uuid.uuid4()),
        email="user@example.com",
        username="user",
        roles=["admin"],
        permissions=["tickets:read"],
        tenant_id="test-tenant",
    )

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get(f"/api/v1/ticketing/{uuid.uuid4()}")
    finally:
        app.dependency_overrides.pop(get_ticket_service, None)

    assert response.status_code == 404
    assert response.json()["detail"] == "missing ticket"


@pytest.mark.asyncio
async def test_update_ticket_maps_unexpected_error(async_db_session, ticketing_app):
    """Unhandled exceptions are converted to HTTP 500 with generic detail."""
    app, current_user_holder = ticketing_app

    async def raise_generic(*args, **kwargs):
        raise RuntimeError("boom")

    async def override_service():
        return _StubTicketService(async_db_session, update_ticket=raise_generic)

    app.dependency_overrides[get_ticket_service] = override_service
    current_user_holder["value"] = UserInfo(
        user_id=str(uuid.uuid4()),
        email="user@example.com",
        username="user",
        roles=["admin"],
        permissions=["tickets:update"],
        tenant_id="test-tenant",
    )

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.patch(
                f"/api/v1/ticketing/{uuid.uuid4()}",
                json={"status": "resolved"},
            )
    finally:
        app.dependency_overrides.pop(get_ticket_service, None)

    assert response.status_code == 500
    assert response.json()["detail"] == "Ticketing operation failed"
