"""
Secrets API endpoints using Vault/OpenBao.

Provides REST endpoints for secrets management operations.
"""

import logging
from typing import Annotated, Any, Dict, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from dotmac.platform.secrets.vault_client import AsyncVaultClient, VaultError
from dotmac.platform.settings import settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# ========================================
# Dependency Injection
# ========================================


async def get_vault_client() -> AsyncVaultClient:
    """Get Vault client instance."""
    if not settings.vault.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vault/OpenBao is not enabled",
        )

    return AsyncVaultClient(
        url=settings.vault.url,
        token=settings.vault.token,
        namespace=settings.vault.namespace,
        mount_path=settings.vault.mount_path,
        kv_version=settings.vault.kv_version,
    )


# ========================================
# Request/Response Models
# ========================================


class SecretData(BaseModel):
    """Secret data model."""

    data: Dict[str, Any] = Field(..., description="Secret key-value pairs")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")


class SecretResponse(BaseModel):
    """Secret response model."""

    path: str = Field(..., description="Secret path")
    data: Dict[str, Any] = Field(..., description="Secret data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Secret metadata")


class SecretInfo(BaseModel):
    """Secret information with metadata."""

    path: str = Field(..., description="Secret path")
    created_time: Optional[str] = Field(None, description="When the secret was created")
    updated_time: Optional[str] = Field(None, description="When the secret was last updated")
    version: Optional[int] = Field(None, description="Current version (KV v2)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SecretListResponse(BaseModel):
    """List secrets response."""

    secrets: list[SecretInfo] = Field(..., description="List of secrets with metadata")


class HealthResponse(BaseModel):
    """Vault health response."""

    healthy: bool = Field(..., description="Health status")
    vault_url: str = Field(..., description="Vault URL")
    mount_path: str = Field(..., description="Mount path")


# ========================================
# API Endpoints
# ========================================


@router.get("/health", response_model=HealthResponse, tags=["secrets"])
async def check_vault_health(
    vault: Annotated[AsyncVaultClient, Depends(get_vault_client)]
) -> HealthResponse:
    """Check Vault/OpenBao health status."""
    try:
        healthy = await vault.health_check()
        return HealthResponse(
            healthy=healthy,
            vault_url=settings.vault.url,
            mount_path=settings.vault.mount_path,
        )
    except Exception as e:
        logger.error(f"Vault health check failed: {e}")
        return HealthResponse(
            healthy=False,
            vault_url=settings.vault.url,
            mount_path=settings.vault.mount_path,
        )


@router.get("/secrets/{path:path}", response_model=SecretResponse, tags=["secrets"])
async def get_secret(
    path: str,
    vault: Annotated[AsyncVaultClient, Depends(get_vault_client)],
) -> SecretResponse:
    """
    Get a secret from Vault.

    Args:
        path: Secret path (e.g., "app/database/credentials")
    """
    try:
        async with vault:
            data = await vault.get_secret(path)

        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Secret not found at path: {path}",
            )

        return SecretResponse(
            path=path,
            data=data,
            metadata=None,  # Vault doesn't separate metadata in KV v2
        )

    except VaultError as e:
        logger.error(f"Failed to retrieve secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve secret: {str(e)}",
        )


@router.post("/secrets/{path:path}", response_model=SecretResponse, tags=["secrets"])
async def create_or_update_secret(
    path: str,
    secret_data: SecretData,
    vault: Annotated[AsyncVaultClient, Depends(get_vault_client)],
) -> SecretResponse:
    """
    Create or update a secret in Vault.

    Args:
        path: Secret path
        secret_data: Secret data to store
    """
    try:
        async with vault:
            await vault.set_secret(path, secret_data.data)

        return SecretResponse(
            path=path,
            data=secret_data.data,
            metadata=secret_data.metadata,
        )

    except VaultError as e:
        logger.error(f"Failed to store secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store secret: {str(e)}",
        )


@router.delete("/secrets/{path:path}", status_code=status.HTTP_204_NO_CONTENT, tags=["secrets"])
async def delete_secret(
    path: str,
    vault: Annotated[AsyncVaultClient, Depends(get_vault_client)],
) -> None:
    """
    Delete a secret from Vault.

    Note: This marks the secret as deleted in Vault KV v2.
    The secret can be undeleted or permanently destroyed using Vault CLI.

    Args:
        path: Secret path to delete
    """
    try:
        async with vault:
            # For KV v2, delete the latest version
            await vault.delete_secret(path)

            logger.info(f"Deleted secret at path: {path}")
            return None

    except VaultError as e:
        logger.error(f"Failed to delete secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete secret: {str(e)}",
        )


@router.get("/secrets", response_model=SecretListResponse, tags=["secrets"])
async def list_secrets(
    vault: Annotated[AsyncVaultClient, Depends(get_vault_client)],
    prefix: str = Query("", description="Optional path prefix to filter secrets"),
) -> SecretListResponse:
    """
    List secrets in Vault.

    Args:
        prefix: Optional prefix to filter secret paths
    """
    try:
        if not vault:
            logger.error("Vault client not available")
            return SecretListResponse(secrets=[])

        # Use the vault client to list secrets with metadata
        secrets_with_metadata = await vault.list_secrets_with_metadata(prefix)

        # Convert to SecretInfo objects
        secrets = []
        for secret_data in secrets_with_metadata:
            try:
                secret_info = SecretInfo(
                    path=secret_data["path"],
                    created_time=secret_data.get("created_time"),
                    updated_time=secret_data.get("updated_time"),
                    version=secret_data.get("version"),
                    metadata=secret_data.get("metadata", {"source": "vault"})
                )
                secrets.append(secret_info)
            except Exception as e:
                logger.warning(f"Failed to parse secret metadata for {secret_data.get('path', 'unknown')}: {e}")
                # Still include the secret even if parsing fails
                secret_info = SecretInfo(
                    path=secret_data.get("path", "unknown"),
                    metadata={"source": "vault", "parsing_error": str(e)}
                )
                secrets.append(secret_info)

        logger.info(f"Listed {len(secrets)} secrets with prefix '{prefix}'")
        return SecretListResponse(secrets=secrets)

    except VaultError as e:
        logger.error(f"Failed to list secrets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list secrets: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error listing secrets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list secrets"
        )


# ========================================
# Export
# ========================================

__all__ = ["router"]
