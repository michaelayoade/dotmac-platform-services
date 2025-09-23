#!/usr/bin/env python
"""
Test script for Vault/OpenBao connection and secrets management.

Usage:
    python -m dotmac.platform.secrets.test_vault
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict

import structlog

from .vault_client import AsyncVaultClient, VaultClient, VaultError
from .vault_config import (
    VaultConnectionManager,
    check_vault_health,
    get_vault_config,
    get_vault_client,
)

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(name: str, success: bool, details: str = ""):
    """Print a test result."""
    status = "✓" if success else "✗"
    color = "\033[92m" if success else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset} {name}: {details}")


async def test_vault_connection():
    """Test Vault connection and basic operations."""
    print_header("DotMac Platform - Vault Connection Test")

    # Get configuration
    print("\n1. Configuration")
    try:
        config = get_vault_config()
        print_result("Configuration loaded", True, f"URL: {config.url}")
        print(f"   Mount path: {config.mount_path}")
        print(f"   KV version: {config.kv_version}")
        if config.namespace:
            print(f"   Namespace: {config.namespace}")
    except Exception as e:
        print_result("Configuration loading", False, str(e))
        return

    # Check health
    print("\n2. Health Check")
    try:
        health = check_vault_health()
        if health["healthy"]:
            print_result("Vault is healthy", True, f"Version: {health.get('version', 'unknown')}")
            print(f"   Initialized: {health.get('initialized', 'unknown')}")
            print(f"   Sealed: {health.get('sealed', 'unknown')}")
        else:
            print_result("Vault health check", False, health.get("error", "Unknown error"))
            return
    except Exception as e:
        print_result("Health check", False, str(e))
        return

    # Test synchronous client
    print("\n3. Synchronous Client Test")
    try:
        client = get_vault_client()

        # Write a test secret
        test_path = "test/connection"
        test_data = {
            "timestamp": str(asyncio.get_event_loop().time()),
            "test": "success",
            "platform": "dotmac",
        }

        try:
            client.set_secret(test_path, test_data)
            print_result("Write secret", True, f"Path: {config.mount_path}/{test_path}")
        except Exception as e:
            print_result("Write secret", False, str(e))

        # Read the secret back
        try:
            retrieved = client.get_secret(test_path)
            if retrieved == test_data:
                print_result("Read secret", True, "Data matches")
            else:
                print_result("Read secret", False, "Data mismatch")
        except Exception as e:
            print_result("Read secret", False, str(e))

        # List secrets
        try:
            secrets_list = client.list_secrets("")
            print_result("List secrets", True, f"Found {len(secrets_list)} keys")
        except Exception as e:
            print_result("List secrets", False, str(e))

        # Delete test secret
        try:
            client.delete_secret(test_path)
            print_result("Delete secret", True, f"Cleaned up {test_path}")
        except Exception as e:
            print_result("Delete secret", False, str(e))

    except Exception as e:
        print_result("Synchronous client", False, str(e))

    # Test asynchronous client
    print("\n4. Asynchronous Client Test")
    try:
        manager = VaultConnectionManager(config)
        async_client = manager.get_async_client()

        # Write multiple secrets
        test_secrets = {
            "test/async/secret1": {"key": "value1"},
            "test/async/secret2": {"key": "value2"},
            "test/async/secret3": {"key": "value3"},
        }

        try:
            for path, data in test_secrets.items():
                await async_client.set_secret(path, data)
            print_result("Write multiple secrets", True, f"Wrote {len(test_secrets)} secrets")
        except Exception as e:
            print_result("Write multiple secrets", False, str(e))

        # Read multiple secrets in parallel
        try:
            paths = list(test_secrets.keys())
            results = await async_client.get_secrets(paths)
            if len(results) == len(test_secrets):
                print_result("Read multiple secrets", True, f"Retrieved {len(results)} secrets")
            else:
                print_result("Read multiple secrets", False, f"Expected {len(test_secrets)}, got {len(results)}")
        except Exception as e:
            print_result("Read multiple secrets", False, str(e))

        # Cleanup
        try:
            for path in test_secrets.keys():
                await async_client.delete_secret(path)
            print_result("Cleanup async secrets", True, "All test secrets deleted")
        except Exception as e:
            print_result("Cleanup async secrets", False, str(e))

    except Exception as e:
        print_result("Asynchronous client", False, str(e))

    # Test application secrets
    print("\n5. Application Secrets Test")
    try:
        client = get_vault_client()

        # Check for expected application secrets
        expected_secrets = [
            ("jwt", ["secret_key", "algorithm"]),
            ("database/postgres", ["host", "port", "database", "username", "password"]),
            ("redis", ["host", "port"]),
            ("encryption", ["fernet_key"]),
        ]

        found_count = 0
        missing_count = 0

        for secret_path, expected_keys in expected_secrets:
            try:
                secret_data = client.get_secret(secret_path)
                if secret_data:
                    found_count += 1
                    missing_keys = [k for k in expected_keys if k not in secret_data]
                    if missing_keys:
                        print_result(
                            f"Secret: {secret_path}",
                            False,
                            f"Missing keys: {', '.join(missing_keys)}"
                        )
                    else:
                        print_result(f"Secret: {secret_path}", True, "All keys present")
                else:
                    missing_count += 1
                    print_result(f"Secret: {secret_path}", False, "Not found")
            except VaultError:
                missing_count += 1
                print_result(f"Secret: {secret_path}", False, "Not found")

        print(f"\nSummary: {found_count} found, {missing_count} missing")

        if missing_count > 0:
            print("\nTo set up missing secrets, run:")
            print("  ./scripts/setup_vault.sh")

    except Exception as e:
        print_result("Application secrets check", False, str(e))

    print("\n" + "=" * 60)
    print("  Test Complete")
    print("=" * 60)


def main():
    """Main entry point."""
    try:
        asyncio.run(test_vault_connection())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()