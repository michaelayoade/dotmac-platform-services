"""
Mock Vault Fixtures for Testing
Provides HashiCorp Vault client mocks and secrets management test utilities.
"""

import base64
import json
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

# Define exceptions locally to avoid import issues
class SecretNotFoundError(Exception):
    """Secret not found error."""
    pass


class SecretAccessDeniedError(Exception):
    """Secret access denied error."""
    pass


class SecretValidationError(Exception):
    """Secret validation error."""
    pass


class VaultConnectionError(Exception):
    """Vault connection error."""
    pass


class MockVaultClient:
    """
    Mock Vault client with common operations.
    Simulates HashiCorp Vault behavior for testing.
    """

    def __init__(self, url: str = "http://localhost:8200", token: Optional[str] = None):
        self.url = url
        self.token = token or "test-vault-token"
        self.is_authenticated = bool(token)
        self.is_initialized = True
        self.is_sealed = False
        self.secrets: Dict[str, Dict[str, Any]] = {}
        self.policies: Dict[str, Dict] = {}
        self.auth_backends: Dict[str, bool] = {"token": True}
        self.audit_backends: Dict[str, Dict] = {}
        self.mounts: Dict[str, Dict] = {
            "secret/": {"type": "kv", "version": "2"},
            "transit/": {"type": "transit"},
            "pki/": {"type": "pki"},
        }
        self.leases: Dict[str, Dict] = {}
        self.call_history: List[Dict[str, Any]] = []
        self.encryption_keys: Dict[str, bytes] = {}

    async def read_secret(self, path: str, mount_point: str = "secret") -> Dict[str, Any]:
        """Read secret from Vault."""
        self.call_history.append({
            "method": "read_secret",
            "args": {"path": path, "mount_point": mount_point}
        })

        if not self.is_authenticated:
            raise VaultConnectionError("Client is not authenticated")

        if self.is_sealed:
            raise VaultConnectionError("Vault is sealed")

        full_path = f"{mount_point}/{path}"
        if full_path not in self.secrets:
            raise SecretNotFoundError(f"Secret not found at path: {full_path}")

        secret_data = self.secrets[full_path]

        # Simulate KV v2 response structure
        if self.mounts.get(f"{mount_point}/", {}).get("version") == "2":
            return {
                "data": {
                    "data": secret_data.get("data", {}),
                    "metadata": secret_data.get("metadata", {
                        "created_time": datetime.now(UTC).isoformat(),
                        "deletion_time": "",
                        "destroyed": False,
                        "version": 1,
                    })
                },
                "lease_duration": 0,
                "renewable": False,
            }
        else:
            # KV v1 response
            return {
                "data": secret_data.get("data", {}),
                "lease_duration": 0,
                "renewable": False,
            }

    async def write_secret(
        self,
        path: str,
        data: Dict[str, Any],
        mount_point: str = "secret"
    ) -> Dict[str, Any]:
        """Write secret to Vault."""
        self.call_history.append({
            "method": "write_secret",
            "args": {"path": path, "data": data, "mount_point": mount_point}
        })

        if not self.is_authenticated:
            raise VaultConnectionError("Client is not authenticated")

        if self.is_sealed:
            raise VaultConnectionError("Vault is sealed")

        full_path = f"{mount_point}/{path}"

        # Store the secret
        if full_path not in self.secrets:
            self.secrets[full_path] = {
                "data": data,
                "metadata": {
                    "created_time": datetime.now(UTC).isoformat(),
                    "version": 1,
                }
            }
        else:
            # Update existing secret (increment version)
            current = self.secrets[full_path]
            version = current.get("metadata", {}).get("version", 0) + 1
            self.secrets[full_path] = {
                "data": data,
                "metadata": {
                    "created_time": current.get("metadata", {}).get("created_time"),
                    "updated_time": datetime.now(UTC).isoformat(),
                    "version": version,
                }
            }

        return {"data": {"created_time": datetime.now(UTC).isoformat(), "version": 1}}

    async def delete_secret(self, path: str, mount_point: str = "secret") -> bool:
        """Delete secret from Vault."""
        self.call_history.append({
            "method": "delete_secret",
            "args": {"path": path, "mount_point": mount_point}
        })

        if not self.is_authenticated:
            raise VaultConnectionError("Client is not authenticated")

        full_path = f"{mount_point}/{path}"
        if full_path in self.secrets:
            del self.secrets[full_path]
            return True
        return False

    async def list_secrets(self, path: str = "", mount_point: str = "secret") -> List[str]:
        """List secrets at path."""
        self.call_history.append({
            "method": "list_secrets",
            "args": {"path": path, "mount_point": mount_point}
        })

        if not self.is_authenticated:
            raise VaultConnectionError("Client is not authenticated")

        prefix = f"{mount_point}/{path}" if path else f"{mount_point}/"
        keys = []

        for secret_path in self.secrets.keys():
            if secret_path.startswith(prefix):
                # Extract relative path
                relative = secret_path[len(prefix):]
                if relative:
                    # Get first component
                    parts = relative.split("/")
                    key = parts[0] + ("/" if len(parts) > 1 else "")
                    if key not in keys:
                        keys.append(key)

        return sorted(keys)

    async def encrypt_data(self, plaintext: str, key_name: str = "default") -> str:
        """Encrypt data using Transit backend."""
        self.call_history.append({
            "method": "encrypt_data",
            "args": {"key_name": key_name}
        })

        if not self.is_authenticated:
            raise VaultConnectionError("Client is not authenticated")

        # Simulate encryption (base64 encode with prefix)
        encrypted = base64.b64encode(plaintext.encode()).decode()
        return f"vault:v1:{encrypted}"

    async def decrypt_data(self, ciphertext: str, key_name: str = "default") -> str:
        """Decrypt data using Transit backend."""
        self.call_history.append({
            "method": "decrypt_data",
            "args": {"key_name": key_name}
        })

        if not self.is_authenticated:
            raise VaultConnectionError("Client is not authenticated")

        # Simulate decryption
        if not ciphertext.startswith("vault:"):
            raise SecretValidationError("Invalid ciphertext format")

        parts = ciphertext.split(":")
        if len(parts) != 3:
            raise SecretValidationError("Invalid ciphertext format")

        try:
            decrypted = base64.b64decode(parts[2]).decode()
            return decrypted
        except Exception as e:
            raise SecretValidationError(f"Decryption failed: {e}")

    async def create_token(
        self,
        policies: Optional[List[str]] = None,
        ttl: str = "1h",
        renewable: bool = True
    ) -> Dict[str, Any]:
        """Create new authentication token."""
        self.call_history.append({
            "method": "create_token",
            "args": {"policies": policies, "ttl": ttl, "renewable": renewable}
        })

        if not self.is_authenticated:
            raise VaultConnectionError("Client is not authenticated")

        token_id = f"s.{uuid4().hex[:24]}"
        accessor = uuid4().hex

        return {
            "auth": {
                "client_token": token_id,
                "accessor": accessor,
                "policies": policies or ["default"],
                "token_policies": policies or ["default"],
                "lease_duration": 3600,
                "renewable": renewable,
            }
        }

    async def renew_token(self, increment: Optional[int] = None) -> Dict[str, Any]:
        """Renew current token."""
        self.call_history.append({
            "method": "renew_token",
            "args": {"increment": increment}
        })

        if not self.is_authenticated:
            raise VaultConnectionError("Client is not authenticated")

        return {
            "auth": {
                "client_token": self.token,
                "lease_duration": increment or 3600,
                "renewable": True,
            }
        }

    async def revoke_token(self, token: Optional[str] = None) -> bool:
        """Revoke token."""
        self.call_history.append({
            "method": "revoke_token",
            "args": {"token": token}
        })

        if not self.is_authenticated:
            raise VaultConnectionError("Client is not authenticated")

        # Simulate revocation
        if token == self.token:
            self.is_authenticated = False

        return True

    async def enable_auth_backend(self, backend_type: str, path: Optional[str] = None) -> bool:
        """Enable auth backend."""
        self.call_history.append({
            "method": "enable_auth_backend",
            "args": {"backend_type": backend_type, "path": path}
        })

        path = path or backend_type
        self.auth_backends[path] = True
        return True

    async def enable_secrets_engine(
        self,
        engine_type: str,
        path: Optional[str] = None,
        config: Optional[Dict] = None
    ) -> bool:
        """Enable secrets engine."""
        self.call_history.append({
            "method": "enable_secrets_engine",
            "args": {"engine_type": engine_type, "path": path, "config": config}
        })

        path = path or engine_type
        self.mounts[f"{path}/"] = {
            "type": engine_type,
            "config": config or {},
        }
        return True

    async def seal(self) -> bool:
        """Seal Vault."""
        self.is_sealed = True
        return True

    async def unseal(self, key: str) -> Dict[str, Any]:
        """Unseal Vault."""
        self.is_sealed = False
        return {
            "sealed": False,
            "t": 3,
            "n": 5,
            "progress": 0,
        }

    async def get_health(self) -> Dict[str, Any]:
        """Get Vault health status."""
        return {
            "initialized": self.is_initialized,
            "sealed": self.is_sealed,
            "standby": False,
            "cluster_name": "vault-cluster-mock",
            "cluster_id": str(uuid4()),
            "version": "1.14.0",
        }

    async def rotate_encryption_key(self, key_name: str = "default") -> bool:
        """Rotate encryption key."""
        self.call_history.append({
            "method": "rotate_encryption_key",
            "args": {"key_name": key_name}
        })
        # Simulate key rotation
        return True

    async def create_policy(self, name: str, policy: str) -> bool:
        """Create or update policy."""
        self.call_history.append({
            "method": "create_policy",
            "args": {"name": name}
        })
        self.policies[name] = {"policy": policy}
        return True

    async def get_policy(self, name: str) -> Optional[str]:
        """Get policy by name."""
        policy_data = self.policies.get(name)
        return policy_data.get("policy") if policy_data else None

    async def delete_policy(self, name: str) -> bool:
        """Delete policy."""
        if name in self.policies:
            del self.policies[name]
            return True
        return False


class MockVaultProvider:
    """Mock Vault secrets provider for testing."""

    def __init__(self, client: Optional[MockVaultClient] = None):
        self.client = client or MockVaultClient(token="test-token")
        self.cache: Dict[str, Any] = {}
        self.validators: Dict[str, Any] = {}

    async def get_secret(self, path: str) -> Dict[str, Any]:
        """Get secret from Vault."""
        # Check cache first
        if path in self.cache:
            return self.cache[path]

        # Read from Vault
        result = await self.client.read_secret(path)

        # Extract data based on KV version
        if "data" in result and "data" in result["data"]:
            # KV v2
            secret_data = result["data"]["data"]
        else:
            # KV v1
            secret_data = result.get("data", {})

        # Validate if validator exists
        if path in self.validators:
            validator = self.validators[path]
            if not validator(secret_data):
                raise SecretValidationError(f"Validation failed for secret at {path}")

        # Cache the result
        self.cache[path] = secret_data
        return secret_data

    async def set_secret(self, path: str, data: Dict[str, Any]) -> bool:
        """Set secret in Vault."""
        await self.client.write_secret(path, data)
        # Invalidate cache
        if path in self.cache:
            del self.cache[path]
        return True

    async def delete_secret(self, path: str) -> bool:
        """Delete secret from Vault."""
        result = await self.client.delete_secret(path)
        # Invalidate cache
        if path in self.cache:
            del self.cache[path]
        return result

    def add_validator(self, path: str, validator: Any):
        """Add validator for secret path."""
        self.validators[path] = validator

    async def encrypt(self, plaintext: str, key_name: str = "default") -> str:
        """Encrypt data."""
        return await self.client.encrypt_data(plaintext, key_name)

    async def decrypt(self, ciphertext: str, key_name: str = "default") -> str:
        """Decrypt data."""
        return await self.client.decrypt_data(ciphertext, key_name)


class MockVaultTransitBackend:
    """Mock Vault Transit backend for encryption operations."""

    def __init__(self, client: MockVaultClient):
        self.client = client
        self.keys: Dict[str, Dict] = {}

    async def create_key(self, name: str, key_type: str = "aes256-gcm96") -> bool:
        """Create encryption key."""
        self.keys[name] = {
            "type": key_type,
            "derived": False,
            "exportable": False,
            "allow_plaintext_backup": False,
            "version": 1,
        }
        return True

    async def encrypt(self, key_name: str, plaintext: str, context: Optional[str] = None) -> str:
        """Encrypt data with key."""
        return await self.client.encrypt_data(plaintext, key_name)

    async def decrypt(self, key_name: str, ciphertext: str, context: Optional[str] = None) -> str:
        """Decrypt data with key."""
        return await self.client.decrypt_data(ciphertext, key_name)

    async def rotate_key(self, name: str) -> bool:
        """Rotate encryption key."""
        if name in self.keys:
            self.keys[name]["version"] += 1
            return True
        return False


@pytest.fixture
def mock_vault_client():
    """Fixture providing a mock Vault client."""
    return MockVaultClient(token="test-vault-token")


@pytest.fixture
def mock_vault_provider(mock_vault_client):
    """Fixture providing a mock Vault provider."""
    return MockVaultProvider(mock_vault_client)


@pytest.fixture
def mock_vault_with_secrets(mock_vault_client):
    """Fixture providing a mock Vault client with test secrets."""
    # Add test secrets
    mock_vault_client.secrets = {
        "secret/database": {
            "data": {
                "username": "testuser",
                "password": "testpass123",
                "host": "localhost",
                "port": 5432,
            },
            "metadata": {"version": 1}
        },
        "secret/api/keys": {
            "data": {
                "stripe": "sk_test_123456",
                "sendgrid": "SG.test123",
                "aws_access_key": "AKIA123456",
                "aws_secret_key": "secret123",
            },
            "metadata": {"version": 1}
        },
        "secret/jwt": {
            "data": {
                "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIE...",
                "public_key": "-----BEGIN PUBLIC KEY-----\nMIIB...",
                "secret": "super-secret-jwt-key",
            },
            "metadata": {"version": 1}
        }
    }

    # Add test policies
    mock_vault_client.policies = {
        "default": {
            "policy": 'path "secret/*" { capabilities = ["read", "list"] }'
        },
        "admin": {
            "policy": 'path "*" { capabilities = ["create", "read", "update", "delete", "list"] }'
        }
    }

    return mock_vault_client


@pytest.fixture
def mock_vault_transit(mock_vault_client):
    """Fixture providing a mock Vault Transit backend."""
    return MockVaultTransitBackend(mock_vault_client)