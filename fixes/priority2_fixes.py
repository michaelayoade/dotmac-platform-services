"""
Priority 2 Fixes for DotMac Platform Services

This file contains the fixes for the three priority 2 issues:
1. Update Pydantic models with missing required fields
2. Fix Vault client mock configurations in secrets tests
3. Resolve bulk service async session handling
"""

# ==============================================================================
# FIX 1: Update Pydantic models with missing required fields
# ==============================================================================
# Issue: FileMetadata model requires created_at field but tests don't provide it
# Location: tests/file_storage/test_router_simple.py


# Fix for test fixture:
def fixed_mock_file_metadata():
    """Fixed mock file metadata for testing."""
    from datetime import UTC, datetime

    from dotmac.platform.file_storage.service import FileMetadata

    return FileMetadata(
        file_id="test-file-123",
        file_name="test.txt",
        file_size=1024,
        content_type="text/plain",
        created_at=datetime.now(UTC),  # ADD THIS REQUIRED FIELD
        upload_timestamp=datetime.now(UTC),  # If this field exists
        user_id="test-user-123",
        checksum="abc123def456",
        tags=["test", "document"],
    )


# ==============================================================================
# FIX 2: Fix Vault client mock configurations in secrets tests
# ==============================================================================
# Issue: Test expects boolean return but function returns None
# Location: tests/secrets/test_secrets_loader_simple.py

# The load_secrets_from_vault function returns None, not a boolean
# Original function signature:
# async def load_secrets_from_vault(...) -> None:


# Fixed test expectations:
async def fixed_test_load_secrets_from_vault_no_vault_config():
    """Fixed test for async secrets loading when Vault config unavailable."""
    from unittest.mock import Mock, patch

    from dotmac.platform.secrets.secrets_loader import load_secrets_from_vault

    mock_settings = Mock()
    mock_settings.vault.enabled = False  # Ensure vault is disabled

    with patch("dotmac.platform.secrets.secrets_loader.HAS_VAULT_CONFIG", False):
        result = await load_secrets_from_vault(mock_settings)
        # Function returns None, not False
        assert result is None  # FIX: Check for None instead of False


async def fixed_test_load_secrets_from_vault_success():
    """Fixed test for successful async secrets loading."""
    from unittest.mock import AsyncMock, Mock, patch

    from dotmac.platform.secrets.secrets_loader import load_secrets_from_vault

    mock_settings = Mock()
    mock_settings.vault.enabled = True  # Ensure vault is enabled
    mock_client = AsyncMock()

    # Mock successful secret retrieval
    mock_client.get_secret.return_value = {"value": "secret_value"}

    with patch("dotmac.platform.secrets.secrets_loader.HAS_VAULT_CONFIG", True):
        with patch(
            "dotmac.platform.secrets.secrets_loader.get_async_vault_client",
            return_value=mock_client,
        ):
            with patch("dotmac.platform.secrets.secrets_loader.set_nested_attr") as mock_set:
                result = await load_secrets_from_vault(mock_settings)

                # Function returns None on success
                assert result is None  # FIX: Check for None instead of True
                # Verify that secrets were loaded by checking side effects
                assert mock_client.get_secret.call_count > 0
                assert mock_set.call_count > 0


# ==============================================================================
# FIX 3: Resolve bulk service async session handling
# ==============================================================================
# Issue: get_async_session() is a generator but used as context manager
# Location: src/dotmac/platform/communications/bulk_service.py

# The get_async_session is an async generator (uses yield) for FastAPI dependency injection
# It should not be used directly with 'async with'

# Option 1: Create a proper context manager wrapper
from contextlib import asynccontextmanager


@asynccontextmanager
async def get_session_context():
    """Proper context manager for getting async session."""
    from dotmac.platform.db import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Option 2: Fix the bulk_service.py usage
# Replace lines 83-86 in bulk_service.py:
async def fixed_create_bulk_job(self, job_data, session=None):
    """Fixed create bulk job with proper session handling."""
    if session is None:
        # Use the AsyncSessionLocal directly instead of get_async_session
        from dotmac.platform.db import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            return await self._create_bulk_job(job_data, session)
    return await self._create_bulk_job(job_data, session)


# Option 3: Alternative fix using proper session creation
async def fixed_create_bulk_job_alt(self, job_data, session=None):
    """Alternative fix using manual session creation."""
    if session is None:
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy.orm import sessionmaker

        from dotmac.platform.db import async_engine

        AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

        async with AsyncSessionLocal() as session:
            async with session.begin():
                return await self._create_bulk_job(job_data, session)
    return await self._create_bulk_job(job_data, session)


# ==============================================================================
# IMPLEMENTATION INSTRUCTIONS
# ==============================================================================
"""
To apply these fixes:

1. For FileMetadata model (Fix 1):
   - Update test fixtures in tests/file_storage/test_router_simple.py
   - Add created_at=datetime.now(UTC) to all FileMetadata instantiations in tests

2. For Vault client tests (Fix 2):
   - Update tests/secrets/test_secrets_loader_simple.py
   - Change assertions from checking boolean returns to None returns
   - Add proper mock settings with vault.enabled attribute

3. For bulk service async sessions (Fix 3):
   - Update src/dotmac/platform/communications/bulk_service.py
   - Replace get_async_session() usage with AsyncSessionLocal() directly
   - Apply this pattern to all methods that create sessions (lines 83-86, 155-158, etc.)

Example patch for bulk_service.py:
"""

BULK_SERVICE_PATCH = """
# In bulk_service.py, replace all occurrences of:
if session is None:
    async with get_async_session() as session:
        return await self._method_name(data, session)

# With:
if session is None:
    from dotmac.platform.db import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        return await self._method_name(data, session)
"""
