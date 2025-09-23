"""Tests for database module."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String

from dotmac.platform.db import (
    Base,
    BaseModel,
    TimestampMixin,
    SoftDeleteMixin,
    get_sync_engine,
    get_async_engine,
)


class TestDatabaseModels:
    """Test database models and mixins."""

    def test_base_model(self):
        """Test BaseModel abstract class."""

        # Create a test model
        class TestModel(BaseModel, Base):
            __tablename__ = "test_model"
            name = Column(String)

        model = TestModel(id=1, name="test")
        assert model.id == 1
        assert model.name == "test"

    def test_timestamp_mixin(self):
        """Test TimestampMixin."""

        class TestTimestamp(TimestampMixin, Base):
            __tablename__ = "test_timestamp"
            id = Column(Integer, primary_key=True)

        model = TestTimestamp()
        assert model.created_at is None  # Will be set by database
        assert model.updated_at is None  # Will be set by database

    def test_soft_delete_mixin(self):
        """Test SoftDeleteMixin."""

        class TestSoftDelete(SoftDeleteMixin, Base):
            __tablename__ = "test_soft_delete"
            id = Column(Integer, primary_key=True)

        model = TestSoftDelete()
        assert model.deleted_at is None
        assert model.is_deleted is False

        # Test soft delete
        now = datetime.now(timezone.utc)
        model.deleted_at = now
        assert model.is_deleted is True

    def test_soft_delete_soft_delete_method(self):
        """Test soft_delete method."""

        class TestModel(SoftDeleteMixin, Base):
            __tablename__ = "test_delete_method"
            id = Column(Integer, primary_key=True)

        model = TestModel()
        assert model.deleted_at is None

        model.soft_delete()
        assert model.deleted_at is not None
        assert model.is_deleted is True

    def test_soft_delete_restore_method(self):
        """Test restore method."""

        class TestModel(SoftDeleteMixin, Base):
            __tablename__ = "test_restore"
            id = Column(Integer, primary_key=True)

        model = TestModel()
        model.soft_delete()
        assert model.is_deleted is True

        model.restore()
        assert model.deleted_at is None
        assert model.is_deleted is False


class TestDatabaseConnection:
    """Test database connection functions."""

    @patch("dotmac.platform.db.settings")
    @patch("dotmac.platform.db.create_engine")
    def test_get_sync_engine(self, mock_create_engine, mock_settings):
        """Test get_sync_engine creates engine correctly."""
        # Reset engine state
        import dotmac.platform.db as db_module
        db_module._sync_engine = None

        mock_settings.database.url = "postgresql://user:pass@localhost/db"
        mock_settings.database.pool_size = 5
        mock_settings.database.max_overflow = 10
        mock_settings.database.pool_timeout = 30
        mock_settings.database.pool_recycle = 300
        mock_settings.database.pool_pre_ping = True
        mock_settings.database.echo = False

        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        # First call creates engine
        engine1 = get_sync_engine()
        assert engine1 == mock_engine
        mock_create_engine.assert_called_once_with(
            "postgresql://user:pass@localhost/db",
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=300,
            pool_pre_ping=True,
        )

        # Second call returns cached engine
        engine2 = get_sync_engine()
        assert engine2 == engine1
        assert mock_create_engine.call_count == 1  # Not called again

    @patch("dotmac.platform.db.settings")
    @patch("dotmac.platform.db.create_async_engine")
    def test_get_async_engine(self, mock_create_async_engine, mock_settings):
        """Test get_async_engine creates async engine correctly."""
        # Reset engine state
        import dotmac.platform.db as db_module
        db_module._async_engine = None

        mock_settings.database.url = "postgresql://user:pass@localhost/db"
        mock_settings.database.async_url = "postgresql+asyncpg://user:pass@localhost/db"
        mock_settings.database.pool_size = 10
        mock_settings.database.max_overflow = 20
        mock_settings.database.pool_timeout = 30
        mock_settings.database.pool_recycle = 600
        mock_settings.database.pool_pre_ping = True
        mock_settings.database.echo = True

        mock_engine = MagicMock()
        mock_create_async_engine.return_value = mock_engine

        engine = get_async_engine()
        assert engine == mock_engine
        mock_create_async_engine.assert_called_once_with(
            "postgresql+asyncpg://user:pass@localhost/db",
            echo=True,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=600,
            pool_pre_ping=True,
        )