"""
Auth utility slice tests (no mocks): crypto-safe comparisons and helpers.
"""

from dotmac.platform.auth import (
    constant_time_compare,
    generate_salt,
    generate_secure_token,
    hash_password,
    verify_password,
)


def test_token_salt_and_hash_helpers():
    tok1 = generate_secure_token()
    tok2 = generate_secure_token()
    assert tok1 != tok2
    assert constant_time_compare(tok1, tok1) is True
    assert constant_time_compare(tok1, tok2) is False

    s1 = generate_salt(16)
    s2 = generate_salt(16)
    assert s1 != s2

    pw = "s3cr3t!"
    h = hash_password(pw)
    assert verify_password(pw, h) is True
    assert verify_password("bad", h) is False


# Note: base64url functions removed - use base64.urlsafe_b64encode/decode directly
