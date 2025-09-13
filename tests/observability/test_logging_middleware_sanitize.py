"""
Unit test for LoggingMiddleware header sanitization.
"""

import pytest

from dotmac.platform.observability.middleware import LoggingMiddleware


@pytest.mark.unit
def test_sanitize_headers_redacts_sensitive_values():
    # Create instance without calling __init__ to avoid ASGI app dependency
    lm = object.__new__(LoggingMiddleware)
    headers = {
        "Authorization": "Bearer secret",
        "X-Api-Key": "apikey",
        "Cookie": "session=abc",
        "X-Auth-Token": "tok",
        "X-Vault-Token": "vault",
        "X-Secret-Key": "sekrit",
        "X-Access-Token": "accesstok",
        "Other": "keep",
    }

    redacted = lm._sanitize_headers(headers)
    for k in [
        "Authorization",
        "X-Api-Key",
        "Cookie",
        "X-Auth-Token",
        "X-Vault-Token",
        "X-Secret-Key",
        "X-Access-Token",
    ]:
        assert redacted[k] == "***REDACTED***"

    assert redacted["Other"] == "keep"
