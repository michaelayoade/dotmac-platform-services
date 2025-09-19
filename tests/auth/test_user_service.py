"""Tests for the consolidated auth user service."""

from unittest.mock import AsyncMock

import pytest

from dotmac.platform.auth.user_service import UserCreateSchema, UserService, UserType
from dotmac.platform.core.enhanced.exceptions import ValidationError


@pytest.fixture
def user_service():
    return UserService(db_session=AsyncMock(), tenant_id=None, user_repo=None)


@pytest.mark.asyncio
async def test_register_user_requires_acceptances(user_service: UserService):
    user_data = UserCreateSchema.model_construct(
        username="user",
        email="user@example.com",
        first_name="Alice",
        user_type=UserType.TENANT_USER,
        password="Password1!",
        terms_accepted=False,
        privacy_accepted=True,
    )

    with pytest.raises(ValidationError):
        await user_service.register_user(user_data)


@pytest.mark.asyncio
async def test_register_user_normalises_admin_user_type(user_service: UserService):
    user_data = UserCreateSchema.model_construct(
        username="user",
        email="user@example.com",
        first_name="Alice",
        user_type=UserType.PLATFORM_ADMIN,
        password="Password1!",
        terms_accepted=True,
        privacy_accepted=True,
    )

    user_service.create_user = AsyncMock(return_value={"id": "user-id"})  # type: ignore[assignment]

    response = await user_service.register_user(user_data)

    assert user_data.user_type == UserType.CUSTOMER
    user_service.create_user.assert_awaited_once_with(user_data, auto_activate=False)
    assert response == {"id": "user-id"}


@pytest.mark.asyncio
async def test_create_user_rejects_duplicate_username(user_service: UserService):
    repo = AsyncMock()
    repo.check_username_available.return_value = False
    repo.check_email_available.return_value = True
    user_service.user_repo = repo

    user_data = UserCreateSchema.model_construct(
        username="user",
        email="user@example.com",
        first_name="Alice",
        user_type=UserType.TENANT_USER,
        password="Password1!",
        terms_accepted=True,
        privacy_accepted=True,
    )

    with pytest.raises(ValidationError):
        await user_service.create_user(user_data)

    repo.check_username_available.assert_awaited_once_with("user")


@pytest.mark.asyncio
async def test_create_user_rejects_duplicate_email(user_service: UserService):
    repo = AsyncMock()
    repo.check_username_available.return_value = True
    repo.check_email_available.return_value = False
    user_service.user_repo = repo

    user_data = UserCreateSchema.model_construct(
        username="user",
        email="user@example.com",
        first_name="Alice",
        user_type=UserType.TENANT_USER,
        password="Password1!",
        terms_accepted=True,
        privacy_accepted=True,
    )

    with pytest.raises(ValidationError):
        await user_service.create_user(user_data)

    repo.check_email_available.assert_awaited_once_with("user@example.com")


@pytest.mark.asyncio
async def test_create_user_invokes_repository(user_service: UserService):
    repo = AsyncMock()
    repo.check_username_available.return_value = True
    repo.check_email_available.return_value = True
    repo.create_user = AsyncMock(return_value={"id": "created"})
    user_service.user_repo = repo

    user_data = UserCreateSchema.model_construct(
        username="user",
        email="user@example.com",
        first_name="Alice",
        user_type=UserType.TENANT_USER,
        password="Password1!",
        terms_accepted=True,
        privacy_accepted=True,
    )

    result = await user_service.create_user(user_data, auto_activate=True)

    repo.create_user.assert_awaited_once()
    assert result == {"id": "created"}
