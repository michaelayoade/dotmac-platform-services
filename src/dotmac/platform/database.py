"""
Database session dependencies for FastAPI
"""

from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.db import Base, get_async_session as get_db_async_session


async def get_async_session(request: Request = None) -> AsyncIterator[AsyncSession]:  # type: ignore[assignment]
    """Get async database session for dependency injection."""
    async for session in get_db_async_session(request=request):
        yield session


# Legacy alias for compatibility
get_session = get_async_session

# Re-export Base for models
__all__ = ["get_async_session", "get_session", "Base"]
