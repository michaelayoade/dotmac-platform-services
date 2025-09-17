"""GraphQL support utilities for the DotMac platform."""

from .schema import schema
from .router import mount_graphql

__all__ = ["schema", "mount_graphql"]
