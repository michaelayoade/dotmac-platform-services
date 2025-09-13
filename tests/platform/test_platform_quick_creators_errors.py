"""
Tests for quick creator error paths in dotmac.platform when modules unavailable.
"""

import sys

import pytest


@pytest.mark.unit
def test_create_jwt_service_import_error(monkeypatch):
    import dotmac.platform as platform_mod

    # Temporarily remove the auth module to simulate missing optional extra
    saved = sys.modules.pop("dotmac.platform.auth", None)
    try:
        with pytest.raises(ImportError):
            platform_mod.create_jwt_service()
    finally:
        if saved is not None:
            sys.modules["dotmac.platform.auth"] = saved
