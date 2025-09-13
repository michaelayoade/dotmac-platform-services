"""
Lightweight tests for auth.dependencies re-exports and aliases.
"""

import pytest


@pytest.mark.unit
def test_dependencies_exports_and_aliases():
    from dotmac.platform.auth import dependencies as deps

    # Ensure key callables/aliases exist
    for name in [
        "RequireAuthenticated",
        "RequireAdmin",
        "RequireReadAccess",
        "RequireWriteAccess",
        "get_current_user",
        "get_optional_user",
        "require_scopes",
        "require_roles",
        "require_permissions",  # alias
        "get_current_active_user",  # alias
    ]:
        assert hasattr(deps, name)
