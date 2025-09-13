"""
Unit tests for SymmetricEncryptionService encryption/decryption.
"""

import base64

from dotmac.platform.secrets.encryption import (
    DataClassification,
    EncryptedField,
    SymmetricEncryptionService,
)


def test_encrypt_decrypt_roundtrip() -> None:
    svc = SymmetricEncryptionService(secret="unit-test-secret")
    plaintext = "sensitive-string"

    enc = svc.encrypt(plaintext, DataClassification.CONFIDENTIAL)
    assert isinstance(enc, EncryptedField)
    assert enc.algorithm in ("fernet", "base64")
    assert isinstance(enc.encrypted_data, str) and len(enc.encrypted_data) > 0

    # Decrypt back to original
    out = svc.decrypt(enc)
    assert out == plaintext


def test_encrypt_returns_base64_string() -> None:
    svc = SymmetricEncryptionService(secret="another-secret")
    enc = svc.encrypt("abc123", DataClassification.INTERNAL)

    # Ensure the encrypted_data is base64-decodable
    _ = base64.b64decode(enc.encrypted_data)
