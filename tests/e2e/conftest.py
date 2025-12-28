"""Fixtures for E2E tests.

Provides database, HTTP client, and authentication fixtures for end-to-end testing.

## Fixture Cleanup Protocol

All fixtures that modify global state MUST:
1. Store original values before modification
2. Use try/finally to guarantee cleanup
3. Log any cleanup failures (not silently ignore)
4. Verify cleanup completed successfully
"""

import logging
import os
from contextlib import contextmanager
from typing import Generator

import pytest
import pytest_asyncio
from fastapi import HTTPException, Request, status
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from dotmac.platform.db import Base
from tests.fixtures.environment import _import_base_and_models

# Configure logging for test fixtures
logger = logging.getLogger(__name__)


class PatchRegistry:
    """Registry to track and cleanup all active patches."""

    def __init__(self):
        self._patches: list = []
        self._started: set = set()

    def register(self, patch) -> None:
        """Register a patch for tracking."""
        self._patches.append(patch)

    def start(self, patch) -> None:
        """Start a patch and track it."""
        patch.start()
        self._started.add(id(patch))

    def stop_all(self) -> list[str]:
        """Stop all registered patches. Returns list of any errors."""
        errors = []
        for patch in reversed(self._patches):
            if id(patch) in self._started:
                try:
                    patch.stop()
                    self._started.discard(id(patch))
                except Exception as e:
                    errors.append(f"Failed to stop patch: {e}")
                    logger.warning(f"Patch cleanup failed: {e}")
        self._patches.clear()
        return errors

    def clear(self) -> None:
        """Clear registry without stopping (for cases where patches already stopped)."""
        self._patches.clear()
        self._started.clear()


@contextmanager
def safe_dependency_overrides(app) -> Generator[dict, None, None]:
    """Context manager that guarantees dependency overrides are cleared."""
    original_overrides = dict(app.dependency_overrides)
    try:
        yield app.dependency_overrides
    finally:
        app.dependency_overrides.clear()
        # Restore any original overrides that existed before test
        app.dependency_overrides.update(original_overrides)

# Ensure all ORM models are registered before creating tables
_import_base_and_models()


@pytest.fixture(autouse=True)
def e2e_test_environment(monkeypatch):
    """Ensure E2E tests run with consistent environment configuration."""
    monkeypatch.setenv("TESTING", "1")
    # Force lightweight, local dependencies for e2e runs
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("STORAGE__PROVIDER", "local")
    monkeypatch.setenv("STORAGE__LOCAL_PATH", "/tmp/dotmac-e2e-storage")
    monkeypatch.setenv("DOTMAC_STORAGE_LOCAL_PATH", "/tmp/dotmac-e2e-storage")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-for-e2e-tests")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/15")


@pytest_asyncio.fixture(scope="function")
async def e2e_db_engine():
    """Per-test async database engine using in-memory SQLite."""
    engine = create_async_engine(
        os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///:memory:"),
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield engine
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def e2e_db_session(e2e_db_engine) -> AsyncSession:
    """Async session bound to the per-test E2E engine."""
    session_maker = async_sessionmaker(
        e2e_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_maker() as session:
        yield session


@pytest.fixture(autouse=True, scope="function")
def e2e_tenant_config(request):
    """Set e2e-specific tenant configuration only for e2e tests."""
    # Use nodeid which works reliably with pytest-xdist parallel execution
    # nodeid format: "tests/e2e/test_file.py::test_function"
    node_id = request.node.nodeid if hasattr(request.node, "nodeid") else ""

    # Check if this is an e2e test by looking at the node ID
    if "tests/e2e/" not in node_id:
        yield
        return

    original_tenant_id = os.environ.get("DEFAULT_TENANT_ID")

    from dotmac.platform.tenant.config import TenantConfiguration, set_tenant_config

    # Set e2e tenant ID
    os.environ["DEFAULT_TENANT_ID"] = "e2e-test-tenant"

    # Reinitialize tenant config with e2e environment variables
    set_tenant_config(TenantConfiguration())

    yield

    # Restore original tenant ID
    if original_tenant_id:
        os.environ["DEFAULT_TENANT_ID"] = original_tenant_id
    else:
        os.environ.pop("DEFAULT_TENANT_ID", None)

    # Reinitialize tenant config to restore original settings
    set_tenant_config(TenantConfiguration())


@pytest.fixture
def tenant_id():
    """Standard tenant ID for E2E tests."""
    return "e2e-test-tenant"


@pytest.fixture
def user_id():
    """Standard user ID for E2E tests."""
    # Use a fixed UUID with hex letters to avoid SQLite numeric affinity
    return "123e4567-e89b-12d3-a456-426614174000"


@pytest_asyncio.fixture
async def async_client(e2e_db_engine, tenant_id, user_id, request):
    """
    Create async HTTP client with dependency overrides for E2E tests.

    This allows tests to make real HTTP requests to the FastAPI app
    while using a test database and controlled dependencies.
    """
    from dotmac.platform.auth.core import UserInfo
    from dotmac.platform.auth.dependencies import get_current_user
    from dotmac.platform.database import get_async_session as get_database_async_session
    from dotmac.platform.db import get_async_session
    from dotmac.platform.tenant import get_current_tenant_id
    from tests.fixtures.app_stubs import (
        create_mock_redis,
        create_sync_redis,
        start_infrastructure_patchers,
    )

    # Create a session maker for the test engine
    test_session_maker = async_sessionmaker(
        e2e_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Ensure helper context managers inside the app use the per-test session maker
    import dotmac.platform._db_legacy as legacy_db
    import dotmac.platform.db as platform_db

    original_session_maker = legacy_db._async_session_maker
    original_session_maker_alias = legacy_db.async_session_maker
    legacy_db._async_session_maker = test_session_maker
    legacy_db.async_session_maker = test_session_maker
    platform_db.async_session_maker = test_session_maker

    # Initialize patch registry for this fixture
    patch_registry = PatchRegistry()

    infra_patchers = start_infrastructure_patchers()
    for patcher in infra_patchers:
        patch_registry.register(patcher)

    mock_redis = create_mock_redis()
    mock_redis_sync = create_sync_redis(getattr(mock_redis, "_store", None))
    try:
        from dotmac.platform.core.caching import set_redis_client

        set_redis_client(mock_redis_sync)
    except ImportError:
        logger.debug("Caching module not available, skipping Redis client setup")

    get_redis_client_dependency = None
    try:
        from dotmac.platform.redis_client import get_redis_client as get_redis_client_dependency
    except ImportError:
        logger.debug("Redis client dependency not available")

    from dotmac.platform.main import app
    try:
        from dotmac.platform.auth import core as auth_core

        auth_core.session_manager._redis = mock_redis
    except Exception:
        pass

    if get_redis_client_dependency is not None:
        async def override_get_redis_client():
            yield mock_redis

        app.dependency_overrides[get_redis_client_dependency] = override_get_redis_client

    app.state._redis_mock = mock_redis

    # Create mock user with tenant admin permissions for e2e tests
    # NOTE: Explicitly NOT granting "platform:*" or "*" to avoid making all users platform admins
    grant_tenant_admin = any(
        marker in getattr(request, "nodeid", "")
        for marker in (
            "tests/e2e/test_tenant_e2e.py",
            "tests/e2e/test_tenant_portal_e2e.py",
        )
    )

    async def mock_get_current_user(
        request: Request | None = None,
        token: str | None = None,
        api_key: str | None = None,
        credentials=None,
    ):
        """Mock get_current_user for E2E tests - matches actual dependency signature."""
        from dotmac.platform.auth.core import JWTService, TokenType

        auth_header = None
        if request is not None:
            auth_header = request.headers.get("Authorization")
        token_value = None
        if token:
            token_value = token
        if credentials and getattr(credentials, "credentials", None):
            token_value = credentials.credentials
        if token_value is None and isinstance(auth_header, str) and auth_header.lower().startswith(
            "bearer "
        ):
            token_value = auth_header[7:].strip() or None
        has_auth = bool(token_value or api_key)
        if isinstance(auth_header, str) and auth_header.lower().startswith("bearer "):
            has_auth = True
        if not has_auth:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
            )
        if token_value:
            jwt_service = JWTService(algorithm="HS256", secret="test-secret-key-for-e2e-tests")
            try:
                jwt_service.verify_token(token_value, expected_type=TokenType.ACCESS)
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
                )
        permissions = [
            "tenant:read",
            "tenant:write",
            "tenant:admin",
            "users:read",
            "users:write",
            "users:admin",
            "customers:read",
            "customers:write",
            "customers:admin",
            "billing:read",
            "billing:write",
            "billing:admin",
            "files:read",
            "files:write",
            "files:admin",
            "webhooks:read",
            "webhooks:write",
            "webhooks:admin",
            "communications:read",
            "communications:write",
            "communications:admin",
            "data:read",
            "data:write",
            "data:admin",
        ]
        if grant_tenant_admin:
            permissions.append("tenants:*")
        return UserInfo(
            user_id=user_id,
            tenant_id=tenant_id,
            email="e2e-test@example.com",
            # Grant tenant-scoped permissions for e2e tests (not platform admin)
            permissions=permissions,
            roles=["admin"],
            is_platform_admin=False,  # Explicitly not a platform admin
        )

    # Create async generator for session override - creates a new session for each request
    async def override_get_async_session():
        async with test_session_maker() as session:
            try:
                yield session
            finally:
                await session.close()

    # Import additional dependencies that need overriding
    # Patch get_current_tenant_id function to always return e2e tenant_id
    # This is necessary because some code calls get_current_tenant_id() as a function
    # rather than using it as a FastAPI dependency
    from unittest.mock import patch

    from dotmac.platform.auth.models import Role
    from dotmac.platform.db import get_session_dependency

    # Mock RBAC service to return admin role for e2e user
    async def mock_get_user_roles(self, user_id):
        # Return mock admin role for e2e tests (self param needed for instance method)
        from uuid import uuid4

        admin_role = Role(
            id=uuid4(),
            name="admin",
            display_name="Administrator",
            description="Administrator role for e2e tests",
        )
        return [admin_role]

    # Mock permission checking methods to always return True for e2e tests
    async def mock_user_has_all_permissions(self, user_id, permissions):
        # Grant all permissions for e2e tests
        return True

    async def mock_user_has_any_permission(self, user_id, permissions):
        # Grant all permissions for e2e tests
        return True

    # Patch RBACService methods using registry for guaranteed cleanup
    from dotmac.platform.auth import rbac_service

    rbac_patch = patch.object(rbac_service.RBACService, "get_user_roles", new=mock_get_user_roles)
    patch_registry.register(rbac_patch)
    patch_registry.start(rbac_patch)

    rbac_permissions_all_patch = patch.object(
        rbac_service.RBACService, "user_has_all_permissions", new=mock_user_has_all_permissions
    )
    patch_registry.register(rbac_permissions_all_patch)
    patch_registry.start(rbac_permissions_all_patch)

    rbac_permissions_any_patch = patch.object(
        rbac_service.RBACService, "user_has_any_permission", new=mock_user_has_any_permission
    )
    patch_registry.register(rbac_permissions_any_patch)
    patch_registry.start(rbac_permissions_any_patch)

    # Import get_async_db for webhooks router
    from dotmac.platform.db import get_async_db

    # Override app dependencies
    app.dependency_overrides[get_async_session] = override_get_async_session
    app.dependency_overrides[get_async_db] = override_get_async_session  # Webhooks router uses this
    app.dependency_overrides[get_session_dependency] = (
        override_get_async_session  # Auth router uses this
    )
    app.dependency_overrides[get_database_async_session] = override_get_async_session
    app.dependency_overrides[get_current_tenant_id] = lambda: tenant_id
    is_auth_e2e = "tests/e2e/test_auth_e2e.py" in getattr(request.node, "nodeid", "")
    if not is_auth_e2e:
        app.dependency_overrides[get_current_user] = mock_get_current_user

    # Patch the function itself for direct calls (file storage router uses this)
    tenant_patch = patch("dotmac.platform.tenant.get_current_tenant_id", return_value=tenant_id)
    patch_registry.register(tenant_patch)
    patch_registry.start(tenant_patch)

    # Also patch where it's imported in file_storage.router
    router_tenant_patch = patch(
        "dotmac.platform.file_storage.router.get_current_tenant_id", return_value=tenant_id
    )
    patch_registry.register(router_tenant_patch)
    patch_registry.start(router_tenant_patch)

    cleanup_errors = []
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
            follow_redirects=True,
        ) as client:
            yield client
    finally:
        # Stop all patches using registry (guaranteed cleanup)
        patch_errors = patch_registry.stop_all()
        if patch_errors:
            cleanup_errors.extend(patch_errors)

        # Clear dependency overrides
        app.dependency_overrides.clear()

        # Restore global session makers
        legacy_db._async_session_maker = original_session_maker
        legacy_db.async_session_maker = original_session_maker_alias
        platform_db.async_session_maker = original_session_maker_alias

        # Log any cleanup errors (don't silently ignore)
        if cleanup_errors:
            logger.warning(f"Fixture cleanup had {len(cleanup_errors)} errors: {cleanup_errors}")


@pytest_asyncio.fixture
async def client(async_client):
    """Alias for async_client for compatibility with tests using 'client' parameter."""
    yield async_client


@pytest_asyncio.fixture
async def auth_headers(e2e_db_session, tenant_id, user_id):
    """Auth headers for e2e tests."""
    from sqlalchemy import select

    from dotmac.platform.auth.core import JWTService, hash_password
    from dotmac.platform.user_management.models import User

    import uuid as uuid_module

    user_uuid = uuid_module.UUID(user_id)
    result = await e2e_db_session.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            id=user_uuid,
            username="e2e-test-user",
            email="e2e-test@example.com",
            password_hash=hash_password("TestPassword123!"),
            tenant_id=tenant_id,
            is_active=True,
            is_verified=True,
            roles=["user"],
        )
        e2e_db_session.add(user)
        await e2e_db_session.commit()

    jwt_service = JWTService(algorithm="HS256", secret="test-secret-key-for-e2e-tests")
    test_token = jwt_service.create_access_token(
        subject=user_id,  # Use UUID from user_id fixture
        additional_claims={
            "scopes": ["read", "write", "admin"],
            "tenant_id": tenant_id,
            "email": user.email,
            "username": user.username,
        },
    )

    return {
        "Authorization": f"Bearer {test_token}",
        "X-Tenant-ID": tenant_id,
    }


# ============================================================================
# Shared E2E Test Fixtures
# ============================================================================


@pytest.fixture
def mock_email_service():
    """Mock email service for tests that send emails."""
    from unittest.mock import AsyncMock, patch

    with patch("dotmac.platform.communications.email_service.get_email_service") as mock:
        mock_service = AsyncMock()
        mock_service.send_email = AsyncMock(return_value=True)
        mock_service.send_verification_email = AsyncMock(return_value=True)
        mock_service.send_welcome_email = AsyncMock(return_value=True)
        mock_service.send_password_reset_email = AsyncMock(return_value=True)
        mock.return_value = mock_service
        yield mock_service


@pytest.fixture
def mock_audit_logging():
    """Mock audit logging for tests."""
    from unittest.mock import AsyncMock, patch

    patches = [
        patch("dotmac.platform.audit.router.log_user_activity", new=AsyncMock()),
        patch("dotmac.platform.audit.router.log_api_activity", new=AsyncMock()),
    ]
    for p in patches:
        p.start()
    yield
    for p in patches:
        p.stop()


@pytest_asyncio.fixture
async def platform_admin_client(e2e_db_engine, tenant_id, user_id):
    """
    Create async HTTP client with platform admin permissions.

    Use this fixture when tests need platform admin access.
    """
    from unittest.mock import patch

    from dotmac.platform.auth.core import UserInfo
    from dotmac.platform.auth.dependencies import get_current_user
    from dotmac.platform.auth.models import Role
    from dotmac.platform.database import get_async_session as get_database_async_session
    from dotmac.platform.db import get_async_db, get_async_session, get_session_dependency
    from dotmac.platform.main import app
    from dotmac.platform.tenant import get_current_tenant_id

    test_session_maker = async_sessionmaker(
        e2e_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    import dotmac.platform._db_legacy as legacy_db
    import dotmac.platform.db as platform_db

    original_session_maker = legacy_db._async_session_maker
    original_session_maker_alias = legacy_db.async_session_maker
    legacy_db._async_session_maker = test_session_maker
    legacy_db.async_session_maker = test_session_maker
    platform_db.async_session_maker = test_session_maker

    async def mock_get_current_user_platform_admin(request=None, token=None, api_key=None):
        """Mock get_current_user with platform admin privileges."""
        return UserInfo(
            user_id=user_id,
            tenant_id=tenant_id,
            email="platform-admin@example.com",
            permissions=["platform:*", "*"],  # Full platform admin permissions
            roles=["platform_admin"],
            is_platform_admin=True,
        )

    async def override_get_async_session():
        async with test_session_maker() as session:
            try:
                yield session
            finally:
                await session.close()

    # Mock RBAC service
    from dotmac.platform.auth import rbac_service

    async def mock_get_user_roles(self, user_id):
        from uuid import uuid4

        return [
            Role(
                id=uuid4(),
                name="platform_admin",
                display_name="Platform Administrator",
                description="Platform admin role",
            )
        ]

    async def mock_user_has_all_permissions(self, user_id, permissions):
        return True

    async def mock_user_has_any_permission(self, user_id, permissions):
        return True

    rbac_patch = patch.object(rbac_service.RBACService, "get_user_roles", new=mock_get_user_roles)
    rbac_patch.start()
    rbac_permissions_all_patch = patch.object(
        rbac_service.RBACService, "user_has_all_permissions", new=mock_user_has_all_permissions
    )
    rbac_permissions_all_patch.start()
    rbac_permissions_any_patch = patch.object(
        rbac_service.RBACService, "user_has_any_permission", new=mock_user_has_any_permission
    )
    rbac_permissions_any_patch.start()

    app.dependency_overrides[get_async_session] = override_get_async_session
    app.dependency_overrides[get_async_db] = override_get_async_session
    app.dependency_overrides[get_session_dependency] = override_get_async_session
    app.dependency_overrides[get_database_async_session] = override_get_async_session
    app.dependency_overrides[get_current_tenant_id] = lambda: tenant_id
    app.dependency_overrides[get_current_user] = mock_get_current_user_platform_admin

    tenant_patch = patch("dotmac.platform.tenant.get_current_tenant_id", return_value=tenant_id)
    router_tenant_patch = patch(
        "dotmac.platform.file_storage.router.get_current_tenant_id", return_value=tenant_id
    )
    tenant_patch.start()
    router_tenant_patch.start()

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
            follow_redirects=True,
        ) as client:
            yield client
    finally:
        rbac_patch.stop()
        rbac_permissions_all_patch.stop()
        rbac_permissions_any_patch.stop()
        tenant_patch.stop()
        router_tenant_patch.stop()
        app.dependency_overrides.clear()
        legacy_db._async_session_maker = original_session_maker
        legacy_db.async_session_maker = original_session_maker_alias
        platform_db.async_session_maker = original_session_maker_alias


@pytest.fixture
def platform_admin_headers(tenant_id, user_id):
    """Auth headers with platform admin privileges."""
    from dotmac.platform.auth.core import JWTService

    jwt_service = JWTService(algorithm="HS256", secret="test-secret-key-for-e2e-tests")
    test_token = jwt_service.create_access_token(
        subject=user_id,
        additional_claims={
            "scopes": ["platform:admin", "read", "write", "admin"],
            "tenant_id": tenant_id,
            "email": "platform-admin@example.com",
            "is_platform_admin": True,
        },
    )

    return {
        "Authorization": f"Bearer {test_token}",
        "X-Tenant-ID": tenant_id,
    }
