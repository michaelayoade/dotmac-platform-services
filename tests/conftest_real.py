"""
Pytest configuration using REAL services (no mocks).
This configuration connects to actual Docker services for integration testing.
"""

import os
from collections.abc import AsyncGenerator, Generator
from uuid import uuid4

import hvac
import pytest
import pytest_asyncio
import redis
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from dotmac.platform.auth.jwt_service import JWTService

# Import our modules
from dotmac.platform.core import TenantContext
from dotmac.platform.database.base import Base
from dotmac.platform.observability import ObservabilityManager
from dotmac.platform.secrets.manager import SecretsManager

# ============================================================================
# Test Configuration - Using REAL Services
# ============================================================================


@pytest.fixture(scope="session")
def test_config() -> dict:
    """Provide test configuration for real services."""
    return {
        "environment": "test",
        "database_url": "postgresql://dotmac:dotmac_password@localhost:5432/dotmac",
        "redis_url": "redis://localhost:6379/0",
        "openbao_url": "http://localhost:8200",
        "openbao_token": "root-token",
        "jwt_secret": "test-secret-key-for-jwt-signing",
        "jwt_algorithm": "HS256",
        "jwt_expiration": 3600,
    }


# ============================================================================
# Real Database Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def database_engine(test_config):
    """Create real PostgreSQL database engine."""
    engine = create_engine(test_config["database_url"], echo=False, pool_size=5, max_overflow=10)

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    yield engine

    # Optional: Clean up test data
    # Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(database_engine) -> Generator[Session, None, None]:
    """Provide real database session."""
    SessionLocal = sessionmaker(bind=database_engine, autocommit=False, autoflush=False)
    session = SessionLocal()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest_asyncio.fixture(scope="function")
async def async_db_session(test_config) -> AsyncGenerator[AsyncSession, None]:
    """Provide real async database session."""
    db_url = test_config["database_url"].replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url, echo=False)
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ============================================================================
# Real Redis Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def redis_client(test_config):
    """Provide real Redis client."""
    client = redis.from_url(test_config["redis_url"], decode_responses=True)

    # Clear test keys
    for key in client.scan_iter("test:*"):
        client.delete(key)

    yield client

    # Cleanup
    for key in client.scan_iter("test:*"):
        client.delete(key)
    client.close()


@pytest_asyncio.fixture(scope="function")
async def async_redis_client(test_config):
    """Provide real async Redis client."""
    import aioredis

    client = await aioredis.from_url(test_config["redis_url"], decode_responses=True)

    # Clear test keys
    async for key in client.scan_iter("test:*"):
        await client.delete(key)

    yield client

    # Cleanup
    async for key in client.scan_iter("test:*"):
        await client.delete(key)
    await client.close()


# ============================================================================
# Real OpenBao Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def openbao_client(test_config):
    """Provide real OpenBao client."""
    client = hvac.Client(url=test_config["openbao_url"], token=test_config["openbao_token"])

    # Verify connection
    assert client.is_authenticated(), "OpenBao authentication failed"

    # Create test mount point if not exists
    try:
        client.sys.enable_secrets_engine(backend_type="kv", path="test", options={"version": "2"})
    except Exception:
        pass  # Mount might already exist

    yield client


# ============================================================================
# Authentication Fixtures with Real JWT
# ============================================================================


@pytest.fixture(scope="function")
def jwt_service(test_config) -> JWTService:
    """Provide real JWT service."""
    os.environ["JWT_SECRET_KEY"] = test_config["jwt_secret"]
    os.environ["JWT_ALGORITHM"] = test_config["jwt_algorithm"]

    service = JWTService()
    return service


@pytest.fixture(scope="function")
def test_user(db_session) -> dict:
    """Get test user from real database."""
    # Use the seeded test user
    result = db_session.execute(
        text("SELECT * FROM auth.users WHERE email = 'user@test.local'")
    ).fetchone()

    if result:
        return {
            "id": str(result.id),
            "email": result.email,
            "username": result.username,
            "is_active": result.is_active,
            "is_admin": result.is_admin,
            "tenant_id": str(result.tenant_id),
            "roles": ["user"],
            "permissions": ["read:profile", "write:profile"],
        }

    # Create if not exists
    user_id = str(uuid4())
    tenant_id = "11111111-1111-1111-1111-111111111111"

    db_session.execute(
        text(
            """
        INSERT INTO auth.users (id, email, username, password_hash, tenant_id)
        VALUES (:id, :email, :username, :password_hash, :tenant_id)
        """
        ),
        {
            "id": user_id,
            "email": "test@example.com",
            "username": "testuser",
            "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY/JF8WqhLxqbXC",
            "tenant_id": tenant_id,
        },
    )
    db_session.commit()

    return {
        "id": user_id,
        "email": "test@example.com",
        "username": "testuser",
        "is_active": True,
        "is_admin": False,
        "tenant_id": tenant_id,
        "roles": ["user"],
        "permissions": ["read:profile", "write:profile"],
    }


@pytest.fixture(scope="function")
def admin_user(db_session) -> dict:
    """Get admin user from real database."""
    # Use the seeded admin user
    result = db_session.execute(
        text("SELECT * FROM auth.users WHERE email = 'admin@test.local'")
    ).fetchone()

    if result:
        return {
            "id": str(result.id),
            "email": result.email,
            "username": result.username,
            "is_active": result.is_active,
            "is_admin": result.is_admin,
            "tenant_id": str(result.tenant_id),
            "roles": ["admin"],
            "permissions": ["*"],
        }

    raise ValueError("Admin user not found in database")


@pytest.fixture(scope="function")
def access_token(jwt_service, test_user) -> str:
    """Create real JWT access token."""
    return jwt_service.create_access_token(
        subject=test_user["id"],
        claims={
            "email": test_user["email"],
            "username": test_user["username"],
            "tenant_id": test_user["tenant_id"],
            "roles": test_user["roles"],
        },
    )


# ============================================================================
# Tenant Fixtures with Real Database
# ============================================================================


@pytest.fixture(scope="function")
def tenant_context(db_session) -> TenantContext:
    """Get tenant context from real database."""
    # Use the seeded test tenant
    result = db_session.execute(
        text("SELECT * FROM tenant.tenants WHERE name = 'Test Tenant'")
    ).fetchone()

    if result:
        return TenantContext(
            tenant_id=str(result.id),
            tenant_name=result.name,
            domain=result.domain,
            is_active=result.is_active,
            metadata={"tier": result.tier, "max_users": result.max_users},
        )

    raise ValueError("Test tenant not found in database")


# ============================================================================
# FastAPI Fixtures with Real Middleware
# ============================================================================


@pytest.fixture(scope="function")
def fastapi_app(jwt_service, redis_client) -> FastAPI:
    """Create FastAPI app with real services."""
    app = FastAPI(title="Test App", version="1.0.0")

    # Apply real observability
    obs_mgr = ObservabilityManager(
        service_name="test-service", environment="test", enable_tracing=True, enable_metrics=True
    )
    obs_mgr.initialize()
    obs_mgr.apply_middleware(app)

    # Add test routes
    @app.get("/health")
    async def health():
        return {"status": "healthy", "redis": redis_client.ping()}

    @app.get("/protected")
    async def protected():
        return {"message": "This is protected"}

    @app.get("/db-test")
    async def db_test(session: Session = Depends(get_db)):
        result = session.execute(text("SELECT 1")).scalar()
        return {"db_status": "connected", "result": result}

    return app


@pytest.fixture(scope="function")
def test_client(fastapi_app) -> TestClient:
    """Provide test client for FastAPI app."""
    return TestClient(fastapi_app)


# ============================================================================
# Observability with Real Services
# ============================================================================


@pytest.fixture(scope="function")
def observability_manager(test_config) -> ObservabilityManager:
    """Provide real ObservabilityManager."""
    manager = ObservabilityManager(
        service_name="test-service",
        environment="test",
        otlp_endpoint="http://localhost:4317",  # Real OTLP endpoint
        enable_tracing=True,
        enable_metrics=True,
        enable_logging=True,
    )
    manager.initialize()
    yield manager
    manager.shutdown()


# ============================================================================
# Secrets Manager with Real Vault
# ============================================================================


@pytest.fixture(scope="function")
def secrets_manager(openbao_client, redis_client) -> SecretsManager:
    """Provide real SecretsManager with OpenBao and Redis."""
    manager = SecretsManager(
        vault_url="http://localhost:8200",
        vault_token="root-token",
        mount_point="test",
        cache_client=redis_client,
        cache_ttl=60,
    )
    yield manager


# ============================================================================
# Database Session Helper
# ============================================================================


def get_db():
    """Dependency for getting database session in FastAPI."""
    engine = create_engine("postgresql://dotmac:dotmac_password@localhost:5432/dotmac")
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Test Data Management
# ============================================================================


@pytest.fixture(scope="function")
def clean_test_data(db_session):
    """Clean up test data after tests."""
    yield

    # Clean up test data created during tests
    db_session.execute(
        text(
            """
        DELETE FROM auth.sessions WHERE user_id IN (
            SELECT id FROM auth.users WHERE email LIKE '%test%'
        )
    """
        )
    )
    db_session.execute(
        text(
            """
        DELETE FROM auth.api_keys WHERE user_id IN (
            SELECT id FROM auth.users WHERE email LIKE '%test%'
        )
    """
        )
    )
    db_session.execute(
        text(
            """
        DELETE FROM auth.users WHERE email LIKE '%pytest%'
    """
        )
    )
    db_session.commit()


# Import for dependency injection
from fastapi import Depends
