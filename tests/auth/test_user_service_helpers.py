"""Tests for auth-layer user service helpers."""

from uuid import UUID
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from dotmac.platform.auth.user_service import BaseUserService
from dotmac.platform.domain import (
    AuthorizationError,
    EntityNotFoundError,
    ValidationError,
)

TENANT_ID = str(UUID("11111111-1111-1111-1111-111111111111"))


class DummyUserService(BaseUserService):
    """Concrete subclass exposing helper methods for testing."""

    pass


@pytest.fixture
def db_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def service(db_session):
    return DummyUserService(db_session=db_session, tenant_id=TENANT_ID)


def test_sanitize_user_data_normalizes_and_trims(service):
    payload = {
        "username": "  MixedCase  ",
        "email": " Person@Example.COM ",
        "first_name": "  Alice  ",
        "last_name": None,
        "notes": None,
    }

    sanitized = service._sanitize_user_data(payload)

    assert sanitized == {
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


def test_validate_tenant_access_blocks_mismatch(service):
    with pytest.raises(AuthorizationError):
        service._validate_tenant_access(str(UUID("22222222-2222-2222-2222-222222222222")), "view")


def test_validate_entity_exists_raises_for_missing(service):
    with pytest.raises(EntityNotFoundError):
        service._validate_entity_exists(None, "User", UUID("33333333-3333-3333-3333-333333333333"))


def test_validate_required_fields_flags_missing(service):
    with pytest.raises(ValidationError) as exc:
        service._validate_required_fields({"first_name": "Alice"}, ["first_name", "last_name"])

    assert "last_name" in str(exc.value)


def test_handle_database_error_maps_uniques(service):
    with pytest.raises(ValidationError):
        service._handle_database_error(Exception("UNIQUE constraint failed: users.email"), "create")

    with pytest.raises(ValidationError):
        service._handle_database_error(SQLAlchemyError("db is down"), "update")

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
