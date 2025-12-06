"""
GraphQL schema for DotMac Platform Services.

Provides a minimal GraphQL schema for platform metadata.
"""

import strawberry

from dotmac.platform.version import get_version


@strawberry.type
class Query:
    """Root GraphQL query type with basic platform info."""

    @strawberry.field(description="API version and info")  # type: ignore[misc]
    def version(self) -> str:
        """Get GraphQL API version."""
        return get_version()


@strawberry.type
class Mutation:
    """Root GraphQL mutation type."""

    @strawberry.field(description="Health check mutation")  # type: ignore[misc]
    def ping(self) -> str:
        """Simple ping mutation for testing."""
        return "pong"


@strawberry.type
class RealtimeSubscription:
    """Placeholder for future real-time GraphQL subscriptions."""
    pass


# Create the GraphQL schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=RealtimeSubscription,
)
