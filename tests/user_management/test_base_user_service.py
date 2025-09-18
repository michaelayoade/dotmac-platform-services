"""Unit tests for shared user management base service helpers."""

from uuid import UUID
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from dotmac.platform.core import AuthorizationError
from dotmac.platform.core.enhanced.exceptions import EntityNotFoundError, ValidationError
from dotmac.platform.user_management.services.base_service import BaseUserService


TENANT_ID = UUID("11111111-1111-1111-1111-111111111111")


class DummyUserService(BaseUserService):
    """Minimal concrete subclass for exercising base helpers."""

    pass


@pytest.fixture
def db_session():
    """Provide an async session double."""
    session = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def service(db_session):
    """Instantiate dummy service with a fixed tenant."""
    return DummyUserService(db_session=db_session, tenant_id=TENANT_ID)


def test_sanitize_user_data_normalizes_and_strips(service):
    payload = {
        "username": "  MixedCase  ",
        "email": " Person@Example.COM ",
        "first_name": "  Alice  ",
        "last_name": None,
        "notes": None,
    }

    result = service._sanitize_user_data(payload)

    assert result == {
        "username": "mixedcase",
        "email": "person@example.com",
        "first_name": "Alice",
    }


def test_mask_sensitive_data_hides_known_fields(service):
    payload = {
        "token": "secret-token",
        "email": "visible@example.com",
        "password_hash": "hash",
        "custom": "value",
    }

    masked = service._mask_sensitive_data(payload)

    assert masked["token"] == "***MASKED***"
    assert masked["password_hash"] == "***MASKED***"
    assert masked["email"] == "visible@example.com"
    assert masked["custom"] == "value"


def test_validate_tenant_access_blocks_cross_tenant(service):
    with pytest.raises(AuthorizationError):
        service._validate_tenant_access(UUID("22222222-2222-2222-2222-222222222222"), "view")


def test_validate_entity_exists_raises_for_missing(service):
    with pytest.raises(EntityNotFoundError):
        service._validate_entity_exists(None, "User", UUID("33333333-3333-3333-3333-333333333333"))


def test_validate_required_fields_reports_missing(service):
    with pytest.raises(ValidationError) as exc:
        service._validate_required_fields({"first_name": "Alice"}, ["first_name", "last_name"])

    assert "last_name" in str(exc.value)


def test_handle_database_error_maps_common_messages(service):
    with pytest.raises(ValidationError) as exc:
        service._handle_database_error(Exception("UNIQUE constraint failed: users.email"), "create")

    assert "Email address is already in use" in str(exc.value)

    with pytest.raises(RuntimeError):
        service._handle_database_error(Exception("unexpected"), "update")


@pytest.mark.asyncio
async def test_health_check_reports_status(service, db_session):
    db_session.execute.return_value = 1

    healthy = await service.health_check()
    assert healthy["status"] == "healthy"
    assert healthy["checks"]["database"] == "connected"

    db_session.execute.side_effect = SQLAlchemyError("db down")
    unhealthy = await service.health_check()
    assert unhealthy["status"] == "unhealthy"
    assert unhealthy["checks"]["database"] == "disconnected"
