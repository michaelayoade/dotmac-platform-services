"""
GraphQL context with authentication and database session.

Provides request context including current user and database session.
"""

import strawberry
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.fastapi import BaseContext

from dotmac.platform.auth.core import UserInfo, jwt_service
from dotmac.platform.db import get_db


@strawberry.type
class Context(BaseContext):
    """
    GraphQL execution context.

    Provides:
    - request: FastAPI Request object
    - db: SQLAlchemy async session
    - current_user: Authenticated user info (optional for public queries)
    """

    request: Request
    db: AsyncSession
    current_user: UserInfo | None = None

    @staticmethod
    async def get_context(request: Request) -> "Context":
        """
        Create GraphQL context from FastAPI request.

        Extracts authentication token and database session.
        Allows guest access for public queries.

        Args:
            request: FastAPI request object

        Returns:
            Context instance with db session and optional user
        """
        # Get database session
        db = get_db()
        db_session = await anext(db)

        # Extract user from token if present
        current_user = None
        try:
            # Try Authorization header first
            auth_header = request.headers.get("Authorization", "")
            token = auth_header.replace("Bearer ", "").strip()

            # Fall back to cookie if no header
            if not token:
                token = request.cookies.get("access_token", "")

            # Verify token and extract user info
            if token:
                payload = jwt_service.verify_token(token)
                current_user = UserInfo(
                    user_id=payload.get("sub", ""),
                    tenant_id=payload.get("tenant_id"),
                    scopes=payload.get("scopes", []),
                    permissions=payload.get("permissions", []),
                )
        except Exception:
            # Guest access - no user context
            pass

        return Context(
            request=request,
            db=db_session,
            current_user=current_user,
        )
