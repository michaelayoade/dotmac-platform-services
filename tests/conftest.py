"""
Global pytest configuration and fixtures for DotMac Platform Services tests.
Minimal version with graceful handling of missing dependencies.
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Optional dependency imports with fallbacks
# Optional fakeredis import with graceful fallback when unavailable
try:
    import fakeredis as _fakeredis

    fakeredis = _fakeredis
    HAS_FAKEREDIS = True
except Exception:  # pragma: no cover - fallback for environments without fakeredis
    from types import SimpleNamespace

    class _DummySyncRedis:
        def __init__(self, *_, **__):
            self._data: dict[str, str] = {}

        # minimal subset used in tests/fixtures
        def flushdb(self):
            self._data.clear()

        def set(self, key, value, ex=None):  # noqa: ARG002
            self._data[str(key)] = value
            return True

        def get(self, key):
            return self._data.get(str(key))

        def delete(self, key):
            return 1 if self._data.pop(str(key), None) is not None else 0

        def close(self):
            return None

    class _DummyAsyncRedis:
        def __init__(self, *_, **__):
            self._data: dict[str, str] = {}

        async def flushdb(self):
            self._data.clear()

        async def set(self, key, value, ex=None):  # noqa: ARG002
            self._data[str(key)] = value
            return True

        async def get(self, key):
            return self._data.get(str(key))

        async def delete(self, key):
            return 1 if self._data.pop(str(key), None) is not None else 0

        async def close(self):
            return None

    fakeredis = SimpleNamespace(
        FakeRedis=_DummySyncRedis,
        aioredis=SimpleNamespace(FakeRedis=_DummyAsyncRedis),
    )
    HAS_FAKEREDIS = False

try:
    import freezegun

    HAS_FREEZEGUN = True
except ImportError:
    HAS_FREEZEGUN = False

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

try:
    from sqlalchemy import create_engine
    from sqlalchemy.engine import make_url
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from sqlalchemy.orm import Session, sessionmaker

    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

# Graceful imports from dotmac platform
try:
    from dotmac.platform.auth.core import JWTService

    HAS_JWT_SERVICE = True
except ImportError:
    HAS_JWT_SERVICE = False

try:
    from dotmac.platform.db import Base

    HAS_DATABASE_BASE = True
except ImportError:
    HAS_DATABASE_BASE = False


# Basic fixtures that don't require external dependencies
@pytest.fixture
def mock_session():
    """Mock database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_sync_session():
    """Mock synchronous database session."""
    session = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.close = Mock()
    return session


@pytest.fixture
def mock_provider():
    """Mock provider for testing."""
    provider = AsyncMock()
    return provider


@pytest.fixture
def mock_config():
    """Mock configuration."""
    config = Mock()
    config.environment = "test"
    config.debug = True
    return config


@pytest.fixture
def mock_api_key_service():
    """Mock API key service."""
    service = AsyncMock()
    service.create_api_key = AsyncMock()
    service.validate_api_key = AsyncMock()
    service.revoke_api_key = AsyncMock()
    return service


@pytest.fixture
def mock_secrets_manager():
    """Mock secrets manager."""
    manager = AsyncMock()
    manager.get_jwt_keypair = AsyncMock()
    manager.get_symmetric_secret = AsyncMock()
    manager.get_database_credentials = AsyncMock()
    return manager


# Conditional fixtures that require external dependencies
if HAS_FAKEREDIS:

    @pytest.fixture
    def redis_client():
        """Redis client using fakeredis."""
        client = fakeredis.FakeRedis(decode_responses=True)
        client.flushall()
        yield client
        client.flushall()

else:

    @pytest.fixture
    def redis_client():
        """Mock Redis client when fakeredis not available."""
        return Mock()


if HAS_SQLALCHEMY:

    @pytest.fixture
    def db_engine():
        """Test database engine."""
        db_url = os.environ.get("DOTMAC_DATABASE_URL", "sqlite:///:memory:")
        connect_args: dict[str, object] = {}

        try:
            url = make_url(db_url)
        except Exception:
            url = None

        if url is not None and url.get_backend_name() == "sqlite":
            connect_args["check_same_thread"] = False
            database = url.database
            if database and database != ":memory":
                candidate = Path(database)
                if not candidate.is_absolute():
                    candidate = Path.cwd() / candidate
                candidate.parent.mkdir(parents=True, exist_ok=True)

        engine = create_engine(db_url, connect_args=connect_args)
        if HAS_DATABASE_BASE:
            Base.metadata.create_all(engine)
        yield engine
        if HAS_DATABASE_BASE:
            Base.metadata.drop_all(engine)
        engine.dispose()

    @pytest.fixture
    def db_session(db_engine):
        """Test database session."""
        SessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
        session = SessionLocal()
        try:
            yield session
        finally:
            try:
                session.rollback()
            except Exception:
                pass
            session.close()

    @pytest.fixture
    async def async_db_engine():
        """Async database engine for tests."""
        db_url = os.environ.get("DOTMAC_DATABASE_URL_ASYNC", "sqlite+aiosqlite:///:memory:")
        connect_args: dict[str, object] = {}

        try:
            url = make_url(db_url)
        except Exception:
            url = None

        if url is not None and url.get_backend_name().startswith("sqlite"):
            database = url.database
            if database and database != ":memory":
                candidate = Path(database)
                if not candidate.is_absolute():
                    candidate = Path.cwd() / candidate
                candidate.parent.mkdir(parents=True, exist_ok=True)

        engine = create_async_engine(db_url, connect_args=connect_args)
        if HAS_DATABASE_BASE:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        try:
            yield engine
        finally:
            if HAS_DATABASE_BASE:
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
            await engine.dispose()

    @pytest.fixture
    async def async_db_session(async_db_engine):
        """Async database session."""
        SessionMaker = async_sessionmaker(async_db_engine, expire_on_commit=False)
        async with SessionMaker() as session:
            try:
                yield session
            finally:
                try:
                    await session.rollback()
                except Exception:
                    pass

else:

    @pytest.fixture
    def db_engine():
        """Mock database engine."""
        return Mock()

    @pytest.fixture
    def db_session():
        """Mock database session."""
        return Mock()


if HAS_FASTAPI:

    @pytest.fixture
    def test_app():
        """Test FastAPI application."""
        app = FastAPI(title="Test App")
        return app

    @pytest.fixture
    def test_client(test_app):
        """Test client for FastAPI app."""
        return TestClient(test_app)

else:

    @pytest.fixture
    def test_app():
        """Mock FastAPI application."""
        return Mock()

    @pytest.fixture
    def test_client():
        """Mock test client."""
        return Mock()


# Async cleanup fixture
@pytest.fixture
async def async_cleanup():
    """Fixture to track and cleanup async tasks."""
    tasks = []

    def track_task(task):
        tasks.append(task)

    yield track_task

    # Cleanup all tracked tasks
    for task in tasks:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


# Test environment setup
@pytest.fixture(autouse=True)
def test_environment():
    """Set up test environment variables."""
    original_env = os.environ.copy()

    tmp_dir = Path(os.getcwd()) / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    db_path = tmp_dir / "test_db.sqlite"
    if db_path.exists():
        db_path.unlink()

    # Set test environment
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DOTMAC_ENV"] = "test"
    os.environ["TESTING"] = "true"
    os.environ["DOTMAC_TEST_DB_PATH"] = str(db_path)
    os.environ["DOTMAC_DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    os.environ["DOTMAC_DATABASE_URL_ASYNC"] = f"sqlite+aiosqlite:///{db_path.as_posix()}"

    try:
        yield
    finally:
        # Clean up temporary database file if it exists
        try:
            if db_path.exists():
                db_path.unlink()
        except OSError:
            pass

        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    # Add custom markers
    config.addinivalue_line("markers", "unit: Unit test")
    config.addinivalue_line("markers", "integration: Integration test")
    config.addinivalue_line("markers", "asyncio: Async test")
    config.addinivalue_line("markers", "slow: Slow test")


# Communications config fixture for notification tests
@pytest.fixture
def communications_config():
    """Mock communications configuration for testing."""
    return {
        "notifications": {
            "email": {
                "enabled": True,
                "smtp_host": "localhost",
                "smtp_port": 1025,
                "from_address": "test@example.com",
            },
            "sms": {
                "enabled": False,
            },
            "push": {
                "enabled": False,
            },
        },
        "webhooks": {
            "enabled": True,
            "timeout": 30,
            "retry_attempts": 3,
        },
        "rate_limits": {
            "email": 100,  # per minute
            "sms": 10,
            "push": 1000,
        },
    }


# Event loop fixture for asyncio tests
@pytest.fixture(scope="function")
def event_loop():
    """Create a fresh event loop per test for isolation."""
    loop = asyncio.new_event_loop()
    previous_loop = None
    try:
        try:
            previous_loop = asyncio.get_running_loop()
        except RuntimeError:
            previous_loop = None

        asyncio.set_event_loop(loop)
        yield loop
    finally:
        try:
            # Allow pending callbacks a chance to finalize.
            loop.run_until_complete(asyncio.sleep(0))
            loop.run_until_complete(loop.shutdown_asyncgens())
            if hasattr(loop, "shutdown_default_executor"):
                loop.run_until_complete(loop.shutdown_default_executor())
        except Exception:
            pass
        finally:
            asyncio.set_event_loop(previous_loop)
            loop.close()


# Skip tests that require unavailable dependencies
def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip tests with missing dependencies."""
    skip_no_redis = pytest.mark.skip(reason="fakeredis not available")
    skip_no_db = pytest.mark.skip(reason="sqlalchemy not available")
    skip_no_fastapi = pytest.mark.skip(reason="fastapi not available")

    for item in items:
        # Skip Redis tests if fakeredis not available
        if "redis" in item.keywords and not HAS_FAKEREDIS:
            item.add_marker(skip_no_redis)

        # Skip database tests if SQLAlchemy not available
        if "database" in item.keywords and not HAS_SQLALCHEMY:
            item.add_marker(skip_no_db)

        # Skip FastAPI tests if FastAPI not available
        if "fastapi" in item.keywords and not HAS_FASTAPI:
            item.add_marker(skip_no_fastapi)
