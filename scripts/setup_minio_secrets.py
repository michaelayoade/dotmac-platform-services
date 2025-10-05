#!/usr/bin/env python3
"""
Setup MinIO credentials in Vault/OpenBao.

This script stores MinIO access and secret keys in Vault so they can be
securely loaded at runtime instead of being hardcoded or in environment variables.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotmac.platform.secrets import VaultClient
from dotmac.platform.settings import settings


def setup_minio_secrets(
    access_key: str = "minioadmin",
    secret_key: str = "minioadmin123",
    vault_url: str = None,
    vault_token: str = None,
):
    """Store MinIO credentials in Vault.

    The secrets are stored at:
    - storage/access_key
    - storage/secret_key

    These paths are mapped in secrets_loader.py to:
    - settings.storage.access_key
    - settings.storage.secret_key
    """
    # Use provided values or defaults from settings
    vault_url = vault_url or settings.vault.url
    vault_token = vault_token or settings.vault.token

    if not vault_url or not vault_token:
        print("❌ Vault URL and token are required")
        print("Set VAULT__URL and VAULT__TOKEN environment variables")
        return False

    print(f"🔐 Connecting to Vault at {vault_url}")

    try:
        client = VaultClient(
            url=vault_url,
            token=vault_token,
            mount_path=settings.vault.mount_path,
            kv_version=settings.vault.kv_version,
        )

        # Store access key
        client.set_secret(
            path="storage/access_key",
            secret={"value": access_key},
        )
        print("✅ Stored MinIO access key in Vault at storage/access_key")

        # Store secret key
        client.set_secret(
            path="storage/secret_key",
            secret={"value": secret_key},
        )
        print("✅ Stored MinIO secret key in Vault at storage/secret_key")

        # Verify the secrets can be read
        stored_access = client.get_secret("storage/access_key")
        stored_secret = client.get_secret("storage/secret_key")

        if stored_access.get("value") == access_key and stored_secret.get("value") == secret_key:
            print("✅ Verified: MinIO credentials successfully stored in Vault")
            print("\nTo use these credentials:")
            print("1. Set VAULT__ENABLED=true in your environment")
            print("2. The secrets will be loaded automatically at startup")
            print("3. Access via settings.storage.access_key and settings.storage.secret_key")
            return True
        else:
            print("❌ Verification failed: stored credentials don't match")
            return False

    except Exception as e:
        print(f"❌ Error storing MinIO credentials: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Store MinIO credentials in Vault")
    parser.add_argument(
        "--access-key",
        default="minioadmin",
        help="MinIO access key (default: minioadmin)",
    )
    parser.add_argument(
        "--secret-key",
        default="minioadmin123",
        help="MinIO secret key (default: minioadmin123)",
    )
    parser.add_argument(
        "--vault-url",
        help="Vault URL (default: from VAULT__URL env var)",
    )
    parser.add_argument(
        "--vault-token",
        help="Vault token (default: from VAULT__TOKEN env var)",
    )

    args = parser.parse_args()

    success = setup_minio_secrets(
        access_key=args.access_key,
        secret_key=args.secret_key,
        vault_url=args.vault_url,
        vault_token=args.vault_token,
    )

    sys.exit(0 if success else 1)
