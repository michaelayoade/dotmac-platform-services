"""
Integration test against a live OpenBao/Vault instance.

Requires the following environment variables to be set:
- DOTMAC_VAULT_URL (e.g., http://localhost:8200)
- DOTMAC_VAULT_TOKEN
Optional:
- DOTMAC_VAULT_MOUNT_POINT (default: "secret")
"""

import os
import uuid

import pytest

from dotmac.platform.secrets import OpenBaoProvider

pytestmark = pytest.mark.integration


def _vault_env() -> tuple[str, str, str]:
    url = os.getenv("DOTMAC_VAULT_URL")
    token = os.getenv("DOTMAC_VAULT_TOKEN")
    mount = os.getenv("DOTMAC_VAULT_MOUNT_POINT", "secret")
    return url, token, mount


@pytest.mark.asyncio
async def test_openbao_roundtrip() -> None:
    url, token, mount = _vault_env()
    if not url or not token:
        pytest.skip("DOTMAC_VAULT_URL and DOTMAC_VAULT_TOKEN must be set for live OpenBao test")

    provider = OpenBaoProvider(url=url, token=token, mount_point=mount, kv_version=2)

    # Unique path per run
    secret_path = f"integration/{uuid.uuid4()}"
    payload = {"api_key": "s3cr3t", "note": "integration-test"}

    try:
        # Store secret
        ok = await provider.set_secret(secret_path, payload)
        assert ok is True

        # Retrieve secret
        data = await provider.get_secret(secret_path)
        assert data["api_key"] == payload["api_key"]
        assert data["note"] == payload["note"]
    finally:
        # Cleanup (best-effort)
        try:
            await provider.delete_secret(secret_path)
        except Exception:
            pass
        await provider.close()
