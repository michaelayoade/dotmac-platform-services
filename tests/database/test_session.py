"""
Tests for database session management.
"""

import os
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import Session as SyncSession

from dotmac.platform.database.session import (
    _ensure_async_engine,
    _ensure_sync_engine,
    _get_async_url,
    _get_sync_url,
    check_database_health,
    create_async_database_engine,
    get_async_db,
    get_async_db_session,
    get_database_session,
    get_db_session,
)


class TestDatabaseURLConfiguration:
    """Test database URL configuration from environment variables."""

    def test_sync_url_from_environment(self):
        """Test sync database URL from environment variable."""
        test_url = "postgresql://user:pass@localhost/testdb"
        with patch.dict(os.environ, {"DOTMAC_DATABASE_URL": test_url}):
            assert _get_sync_url() == test_url

    def test_sync_url_fallback_to_sqlite(self):
        """Test sync database URL falls back to SQLite for development."""
        with patch.dict(os.environ, {}, clear=True):
            url = _get_sync_url()
            assert url == "sqlite:///./dotmac_dev.sqlite"

    def test_async_url_from_environment(self):
        """Test async database URL from environment variable."""
        test_url = "postgresql+asyncpg://user:pass@localhost/testdb"
        with patch.dict(os.environ, {"DOTMAC_DATABASE_URL_ASYNC": test_url}):
            assert _get_async_url() == test_url

    def test_async_url_derived_from_sync_postgresql(self):
        """Test async URL derived from sync PostgreSQL URL."""
        sync_url = "postgresql://user:pass@localhost/testdb"
        with patch.dict(os.environ, {"DOTMAC_DATABASE_URL": sync_url}, clear=True):
            async_url = _get_async_url()
            assert async_url == "postgresql+asyncpg://user:pass@localhost/testdb"

    def test_async_url_derived_from_sync_sqlite(self):
        """Test async URL derived from sync SQLite URL."""
        sync_url = "sqlite:///./test.db"
        with patch.dict(os.environ, {"DOTMAC_DATABASE_URL": sync_url}, clear=True):
            async_url = _get_async_url()
            assert async_url == "sqlite+aiosqlite:///./test.db"

    def test_async_url_fallback_keeps_unknown_scheme(self):
        """Test async URL keeps unknown schemes as-is."""
        unknown_url = "mysql://user:pass@localhost/testdb"
        with patch.dict(os.environ, {"DOTMAC_DATABASE_URL": unknown_url}, clear=True):
            async_url = _get_async_url()
            assert async_url == unknown_url


class TestEngineManagement:
    """Test database engine creation and caching."""

    @patch("dotmac.platform.database.session.create_engine")
    def test_sync_engine_creation(self, mock_create_engine):
        """Test sync engine is created and cached."""
        import dotmac.platform.database.session as session_module

        # Reset global state
        session_module._sync_engine = None

        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine

        # First call creates engine
        engine1 = _ensure_sync_engine()
        assert engine1 == mock_engine
        mock_create_engine.assert_called_once()

        # Second call returns cached engine
        engine2 = _ensure_sync_engine()
        assert engine2 == mock_engine
        assert mock_create_engine.call_count == 1  # Still only called once

    @patch("dotmac.platform.database.session.create_async_engine")
    def test_async_engine_creation(self, mock_create_async_engine):
        """Test async engine is created and cached."""
        import dotmac.platform.database.session as session_module

        # Reset global state
        session_module._async_engine = None

        mock_engine = Mock(spec=AsyncEngine)
        mock_create_async_engine.return_value = mock_engine

        # First call creates engine
        engine1 = _ensure_async_engine()
        assert engine1 == mock_engine
        mock_create_async_engine.assert_called_once()

        # Second call returns cached engine
        engine2 = _ensure_async_engine()
        assert engine2 == mock_engine
        assert mock_create_async_engine.call_count == 1


class TestSyncSession:
    """Test synchronous database session management."""

    @patch("dotmac.platform.database.session._ensure_sync_engine")
    def test_get_database_session_success(self, mock_ensure_engine):
        """Test successful sync session creation and cleanup."""
        mock_engine = Mock()
        mock_ensure_engine.return_value = mock_engine

        mock_session = Mock(spec=SyncSession)
        mock_sessionmaker = Mock(return_value=mock_session)

        with patch("dotmac.platform.database.session.sync_sessionmaker", mock_sessionmaker):
            with get_database_session() as session:
                assert session == mock_session
                mock_sessionmaker.assert_called_once_with(
                    bind=mock_engine, autoflush=False, autocommit=False
                )

            # Session should be closed after context
            mock_session.close.assert_called_once()
            mock_session.rollback.assert_not_called()

    @patch("dotmac.platform.database.session._ensure_sync_engine")
    def test_get_database_session_exception_handling(self, mock_ensure_engine):
        """Test sync session rollback on exception."""
        mock_engine = Mock()
        mock_ensure_engine.return_value = mock_engine

        mock_session = Mock(spec=SyncSession)
        mock_sessionmaker = Mock(return_value=mock_session)

        with patch("dotmac.platform.database.session.sync_sessionmaker", mock_sessionmaker):
            with pytest.raises(ValueError):
                with get_database_session():
                    raise ValueError("Test error")

            # Session should be rolled back and closed
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called()


class TestAsyncSession:
    """Test asynchronous database session management."""

    @pytest.mark.asyncio
    @patch("dotmac.platform.database.session._ensure_async_engine")
    async def test_get_db_session_success(self, mock_ensure_engine):
        """Test successful async session creation and cleanup."""
        mock_engine = Mock(spec=AsyncEngine)
        mock_ensure_engine.return_value = mock_engine

        mock_session = Mock(spec=AsyncSession)
        mock_session.close = AsyncMock()
        mock_sessionmaker = Mock(return_value=mock_session)

        with patch("dotmac.platform.database.session.async_sessionmaker", mock_sessionmaker):
            async with get_db_session() as session:
                assert session == mock_session
                mock_sessionmaker.assert_called_once_with(
                    bind=mock_engine, autoflush=False, autocommit=False, expire_on_commit=False
                )

            # Session should be closed after context
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("dotmac.platform.database.session._ensure_async_engine")
    async def test_get_db_session_exception_handling(self, mock_ensure_engine):
        """Test async session rollback on exception."""
        mock_engine = Mock(spec=AsyncEngine)
        mock_ensure_engine.return_value = mock_engine

        mock_session = Mock(spec=AsyncSession)
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()
        mock_sessionmaker = Mock(return_value=mock_session)

        with patch("dotmac.platform.database.session.async_sessionmaker", mock_sessionmaker):
            with pytest.raises(ValueError):
                async with get_db_session():
                    raise ValueError("Test error")

            # Session should be rolled back and closed
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_session_aliases(self):
        """Test that async session aliases work correctly."""
        # Verify aliases point to the same function
        assert get_async_db == get_db_session
        assert get_async_db_session == get_db_session


class TestAsyncEngineCreation:
    """Test async engine creation utility."""

    @patch("dotmac.platform.database.session.create_async_engine")
    def test_create_async_database_engine(self, mock_create_async_engine):
        """Test creating async engine with custom URL."""
        test_url = "postgresql+asyncpg://user:pass@localhost/testdb"
        mock_engine = Mock(spec=AsyncEngine)
        mock_create_async_engine.return_value = mock_engine

        result = create_async_database_engine(test_url, pool_size=10, echo=True)

        assert result == mock_engine
        mock_create_async_engine.assert_called_once_with(test_url, pool_size=10, echo=True)


class TestDatabaseHealthCheck:
    """Test database health check functionality."""

    @pytest.mark.asyncio
    @patch("dotmac.platform.database.session._ensure_async_engine")
    async def test_check_database_health_success(self, mock_ensure_engine):
        """Test successful database health check."""
        mock_engine = Mock(spec=AsyncEngine)
        mock_ensure_engine.return_value = mock_engine

        mock_conn = AsyncMock()
        mock_engine.connect = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock()
        mock_conn.close = AsyncMock()

        result = await check_database_health()

        assert result is True
        mock_engine.connect.assert_called_once()
        mock_conn.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("dotmac.platform.database.session._ensure_async_engine")
    async def test_check_database_health_failure(self, mock_ensure_engine):
        """Test database health check failure."""
        mock_engine = Mock(spec=AsyncEngine)
        mock_ensure_engine.return_value = mock_engine

        # Simulate connection failure
        mock_engine.connect = AsyncMock(side_effect=SQLAlchemyError("Connection failed"))

        result = await check_database_health()

        assert result is False
        mock_engine.connect.assert_called_once()


@pytest.mark.integration
class TestDatabaseSessionIntegration:
    """Integration tests with real database."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires real PostgreSQL database connection")
    async def test_real_postgres_session(self):
        """Test real PostgreSQL session operations."""
        # Set up test database URL
        test_url = "postgresql://dotmac:dotmac_password@localhost:5432/dotmac"
        with patch.dict(os.environ, {"DOTMAC_DATABASE_URL": test_url}):
            with get_database_session() as session:
                # Test basic query
                result = session.execute(text("SELECT 1"))
                assert result.scalar() == 1

                # Test transaction
                session.execute(text("CREATE TEMP TABLE test_table (id INT)"))
                session.execute(text("INSERT INTO test_table VALUES (1), (2), (3)"))
                result = session.execute(text("SELECT COUNT(*) FROM test_table"))
                assert result.scalar() == 3

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires real PostgreSQL database connection")
    async def test_real_async_postgres_session(self):
        """Test real async PostgreSQL session operations."""
        test_url = "postgresql+asyncpg://dotmac:dotmac_password@localhost:5432/dotmac"
        with patch.dict(os.environ, {"DOTMAC_DATABASE_URL_ASYNC": test_url}):
            async with get_db_session() as session:
                # Test basic query
                result = await session.execute(text("SELECT 1"))
                assert result.scalar() == 1

                # Test async health check
                health = await check_database_health()
                assert health is True
