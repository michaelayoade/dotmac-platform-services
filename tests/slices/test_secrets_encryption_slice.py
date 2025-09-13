"""
Secrets encryption helpers slice tests (no external KMS).
"""

from dotmac.platform.secrets.encryption import (
    decrypt_secret,
    encrypt_secret,
    generate_encryption_key,
)


def test_encrypt_decrypt_roundtrip():
    key = generate_encryption_key()
    secret = "value1"
    enc = encrypt_secret(secret, key)
    dec = decrypt_secret(enc, key)
    assert dec == secret

