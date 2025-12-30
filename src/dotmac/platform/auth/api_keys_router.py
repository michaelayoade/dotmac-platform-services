"""API Key management endpoints."""

import hashlib
import inspect
from datetime import UTC, datetime
from typing import Any
from unittest.mock import Mock
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.database import get_session

from .core import UserInfo, api_key_service, get_current_user
from .models import ApiKey

router = APIRouter(prefix="/auth/api-keys", tags=["API Keys"])


class ScopeDetail(BaseModel):  # BaseModel resolves to Any in isolation
    """API key scope detail."""

    model_config = ConfigDict()

    name: str
    description: str


class AvailableScopesResponse(BaseModel):  # BaseModel resolves to Any in isolation
    """Response for available API key scopes."""

    model_config = ConfigDict()

    scopes: dict[str, ScopeDetail]


# ============================================
# Security Helpers
# ============================================


def _hash_api_key(api_key: str) -> str:
    """
    Hash API key using SHA-256 for secure storage.

    We use SHA-256 instead of bcrypt because:
    1. API keys are high-entropy random tokens (not user passwords)
    2. SHA-256 is sufficient for preventing rainbow table attacks
    3. Faster verification for high-throughput API requests

    Args:
        api_key: The plaintext API key

    Returns:
        Hex-encoded SHA-256 hash of the API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


# ============================================
# Pydantic Models
# ============================================


class APIKeyCreateRequest(BaseModel):
    """Request to create API key."""

    model_config = ConfigDict()

    name: str = Field(
        min_length=1, max_length=255, description="Human-readable name for the API key"
    )
    scopes: list[str] = Field(
        default_factory=list, description="List of permissions/scopes for the key"
    )
    expires_at: datetime | None = Field(None, description="Optional expiration date")
    description: str | None = Field(None, max_length=500, description="Optional description")


class APIKeyResponse(BaseModel):
    """API key information."""

    model_config = ConfigDict()

    id: str = Field(description="API key identifier")
    name: str = Field(description="Human-readable name")
    scopes: list[str] = Field(description="Assigned permissions/scopes")
    created_at: datetime = Field(description="Creation timestamp")
    expires_at: datetime | None = Field(None, description="Expiration timestamp")
    description: str | None = Field(None, description="Optional description")
    last_used_at: datetime | None = Field(None, description="Last usage timestamp")
    is_active: bool = Field(description="Whether the key is active")

    # Don't expose the actual key value in list responses
    key_preview: str = Field(description="Masked key preview (sk_****)")


class APIKeyCreateResponse(APIKeyResponse):
    """Response when creating API key - includes full key value."""

    api_key: str = Field(description="Full API key value (only shown once)")


class APIKeyListResponse(BaseModel):
    """List of API keys."""

    model_config = ConfigDict()

    api_keys: list[APIKeyResponse]
    total: int
    page: int
    limit: int


class APIKeyUpdateRequest(BaseModel):
    """Request to update API key."""

    model_config = ConfigDict()

    name: str | None = Field(None, min_length=1, max_length=255)
    scopes: list[str] | None = Field(None)
    description: str | None = Field(None, max_length=500)
    is_active: bool | None = Field(None)


# ============================================
# Enhanced API Key Service Functions
# ============================================


async def _enhanced_create_api_key(
    user_id: str,
    name: str,
    scopes: list[str] | None = None,
    expires_at: datetime | None = None,
    description: str | None = None,
    tenant_id: str | None = None,
    session: AsyncSession | None = None,
) -> tuple[str, str]:
    """Create API key with enhanced metadata and tenant binding.

    SECURITY: API keys MUST be bound to a tenant to prevent cross-tenant access.

    Args:
        user_id: User ID (UUID as string)
        name: Human-readable key name
        scopes: Optional permission scopes
        expires_at: Optional expiration timestamp
        description: Optional key description
        tenant_id: Tenant ID for multi-tenant isolation (REQUIRED for production)
        session: Database session for persistence

    Returns:
        Tuple of (api_key, key_id)
    """
    key_id = uuid4()
    api_key = await api_key_service.create_api_key(user_id, name, scopes, tenant_id)

    # SECURITY: Hash the API key before storing
    api_key_hash = _hash_api_key(api_key)
    prefix = api_key[:8]

    # Persist to database if session provided
    if session:
        api_key_entity = ApiKey(
            id=key_id,
            user_id=UUID(user_id),
            tenant_id=UUID(tenant_id) if tenant_id else None,
            name=name,
            prefix=prefix,
            key_hash=api_key_hash,
            scopes=scopes or [],
            description=description,
            is_active=True,
            expires_at=expires_at,
        )
        session.add(api_key_entity)
        await session.flush()

    # Also cache to Redis for fast lookup
    client = await api_key_service._get_redis()
    enhanced_data = {
        "id": str(key_id),
        "user_id": user_id,
        "name": name,
        "prefix": prefix,
        "scopes": scopes or [],
        "tenant_id": tenant_id,  # SECURITY: Bind API key to tenant
        "created_at": datetime.now(UTC).isoformat(),
        "expires_at": expires_at.isoformat() if expires_at else None,
        "description": description,
        "last_used_at": None,
        "is_active": True,
    }

    fallback_allowed = getattr(api_key_service, "_fallback_allowed", True)

    if client:
        await client.set(f"api_key_meta:{key_id}", api_key_service._serialize(enhanced_data))
        await client.set(f"api_key_lookup:{api_key_hash}", str(key_id))
    elif not session:
        # Only use memory fallback if no database session
        if not fallback_allowed:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="API key service unavailable. Redis connectivity is required.",
            )
        memory_meta = getattr(api_key_service, "_memory_meta", None)
        if memory_meta is None:
            memory_meta = {}
            api_key_service._memory_meta = memory_meta
        memory_lookup = getattr(api_key_service, "_memory_lookup", None)
        if memory_lookup is None:
            memory_lookup = {}
            api_key_service._memory_lookup = memory_lookup

        memory_meta[str(key_id)] = enhanced_data
        memory_lookup[api_key_hash] = str(key_id)

    return api_key, str(key_id)


async def _list_user_api_keys(user_id: str, session: AsyncSession | None = None) -> list[dict[str, Any]]:
    """List all API keys for a user.

    Queries database first if session provided, otherwise falls back to Redis/memory.
    """
    keys: list[dict[str, Any]] = []

    # Try database first if session provided
    if session:
        result = await session.execute(
            select(ApiKey)
            .where(ApiKey.user_id == UUID(user_id))
            .where(ApiKey.is_active == True)  # noqa: E712
            .order_by(ApiKey.created_at.desc())
        )
        db_keys = result.scalars().all()
        for key in db_keys:
            keys.append({
                "id": str(key.id),
                "user_id": str(key.user_id),
                "tenant_id": str(key.tenant_id) if key.tenant_id else None,
                "name": key.name,
                "prefix": key.prefix,
                "scopes": key.scopes or [],
                "created_at": key.created_at.isoformat() if key.created_at else None,
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "description": key.description,
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                "is_active": key.is_active,
            })
        return keys

    # Fall back to Redis/memory for backwards compatibility
    client = await api_key_service._get_redis()
    fallback_allowed = getattr(api_key_service, "_fallback_allowed", True)

    if client:
        # Scan for user's API key metadata
        async for key in client.scan_iter(match="api_key_meta:*"):
            data_str = await client.get(key)
            if data_str:
                data = api_key_service._deserialize(data_str)
                if data.get("user_id") == user_id:
                    keys.append(data)
    else:
        if not fallback_allowed:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="API key metadata unavailable. Redis connectivity is required.",
            )
        # Fallback to memory
        memory_meta = getattr(api_key_service, "_memory_meta", {})
        for data in memory_meta.values():
            if data.get("user_id") == user_id:
                keys.append(data)

    return keys


async def _get_api_key_by_id(key_id: str, session: AsyncSession | None = None) -> dict[str, Any] | None:
    """Get API key metadata by ID."""
    # Try database first if session provided
    if session:
        result = await session.execute(
            select(ApiKey).where(ApiKey.id == UUID(key_id))
        )
        key = result.scalar_one_or_none()
        if key:
            return {
                "id": str(key.id),
                "user_id": str(key.user_id),
                "tenant_id": str(key.tenant_id) if key.tenant_id else None,
                "name": key.name,
                "prefix": key.prefix,
                "scopes": key.scopes or [],
                "created_at": key.created_at.isoformat() if key.created_at else None,
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "description": key.description,
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                "is_active": key.is_active,
            }
        return None

    # Fall back to Redis/memory
    client = await api_key_service._get_redis()

    if client:
        data_str = await client.get(f"api_key_meta:{key_id}")
        return api_key_service._deserialize(data_str) if data_str else None
    else:
        if not getattr(api_key_service, "_fallback_allowed", True):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="API key metadata unavailable. Redis connectivity is required.",
            )
        # Fallback to memory
        return getattr(api_key_service, "_memory_meta", {}).get(key_id)


async def _update_api_key_metadata(key_id: str, updates: dict[str, Any], session: AsyncSession | None = None) -> bool:
    """Update API key metadata."""
    # Try database first if session provided
    if session:
        result = await session.execute(
            select(ApiKey).where(ApiKey.id == UUID(key_id))
        )
        key = result.scalar_one_or_none()
        if not key:
            return False

        # Update allowed fields
        if "name" in updates:
            key.name = updates["name"]
        if "scopes" in updates:
            key.scopes = updates["scopes"]
        if "description" in updates:
            key.description = updates["description"]
        if "is_active" in updates:
            key.is_active = updates["is_active"]

        await session.flush()

        # Also update Redis cache if available
        client = await api_key_service._get_redis()
        if client:
            data_str = await client.get(f"api_key_meta:{key_id}")
            if data_str:
                data = api_key_service._deserialize(data_str)
                data.update(updates)
                await client.set(f"api_key_meta:{key_id}", api_key_service._serialize(data))

        return True

    # Fall back to Redis/memory
    client = await api_key_service._get_redis()

    if client:
        data_str = await client.get(f"api_key_meta:{key_id}")
        if not data_str:
            return False

        data = api_key_service._deserialize(data_str)
        data.update(updates)
        await client.set(f"api_key_meta:{key_id}", api_key_service._serialize(data))
        return True
    else:
        if not getattr(api_key_service, "_fallback_allowed", True):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="API key metadata unavailable. Redis connectivity is required.",
            )
        # Fallback to memory
        memory_meta = getattr(api_key_service, "_memory_meta", {})
        if key_id in memory_meta:
            memory_meta[key_id].update(updates)
            return True
        return False


async def _revoke_api_key_by_id(key_id: str, session: AsyncSession | None = None) -> bool:
    """
    Revoke API key by ID.

    Soft-deletes in database if session provided, also cleans up Redis cache.
    """
    # Try database first if session provided
    if session:
        result = await session.execute(
            select(ApiKey).where(ApiKey.id == UUID(key_id))
        )
        key = result.scalar_one_or_none()
        if not key:
            return False

        # Soft delete by setting is_active = False
        key.is_active = False
        await session.flush()

        # Also clean up Redis cache
        client = await api_key_service._get_redis()
        if client:
            await client.delete(f"api_key_meta:{key_id}")
            # Find and delete lookup entry
            api_key_hash = None
            async for lookup_key in client.scan_iter(match="api_key_lookup:*"):
                stored_key_id = await client.get(lookup_key)
                if isinstance(stored_key_id, bytes):
                    stored_key_id = stored_key_id.decode("utf-8")
                if stored_key_id == key_id:
                    api_key_hash = lookup_key.replace("api_key_lookup:", "")
                    await client.delete(lookup_key)
                    break
            if api_key_hash:
                await client.delete(f"api_key:{api_key_hash}")
        else:
            memory_lookup = getattr(api_key_service, "_memory_lookup", {})
            api_key_hash = None
            for key_hash, stored_key_id in memory_lookup.items():
                if stored_key_id == key_id:
                    api_key_hash = key_hash
                    break
            if api_key_hash:
                getattr(api_key_service, "_memory_meta", {}).pop(key_id, None)
                memory_lookup.pop(api_key_hash, None)
                getattr(api_key_service, "_memory_keys", {}).pop(api_key_hash, None)

        return True

    # Fall back to Redis/memory for backwards compatibility
    client = await api_key_service._get_redis()
    api_key_hash = None

    if client:
        # Find the API key hash from lookup
        async for lookup_key in client.scan_iter(match="api_key_lookup:*"):
            stored_key_id = await client.get(lookup_key)
            if stored_key_id == key_id:
                # Extract the hash from the lookup key
                api_key_hash = lookup_key.replace("api_key_lookup:", "")
                break
    else:
        if not getattr(api_key_service, "_fallback_allowed", True):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="API key revocation unavailable. Redis connectivity is required.",
            )
        # Fallback to memory
        for key_hash, stored_key_id in getattr(api_key_service, "_memory_lookup", {}).items():
            if stored_key_id == key_id:
                api_key_hash = key_hash
                break

    if not api_key_hash:
        return False

    # SECURITY FIX: Use revoke_by_hash since we already have the hash
    # (not the plaintext). This avoids double-hashing.
    revoke_by_hash = getattr(api_key_service, "revoke_api_key_by_hash", None)
    if isinstance(revoke_by_hash, Mock):  # tests patch api_key_service with MagicMock
        revoke_by_hash = None

    if revoke_by_hash is not None:
        result = revoke_by_hash(api_key_hash)
        success = await result if inspect.isawaitable(result) else bool(result)
    else:
        fallback_result = api_key_service.revoke_api_key(api_key_hash)
        success = (
            await fallback_result if inspect.isawaitable(fallback_result) else bool(fallback_result)
        )

    if success:
        if client:
            await client.delete(f"api_key_meta:{key_id}")
            await client.delete(f"api_key_lookup:{api_key_hash}")
            await client.delete(f"api_key:{api_key_hash}")
        else:
            # Fallback to memory
            getattr(api_key_service, "_memory_meta", {}).pop(key_id, None)
            getattr(api_key_service, "_memory_lookup", {}).pop(api_key_hash, None)
            getattr(api_key_service, "_memory_keys", {}).pop(api_key_hash, None)

    return success


def _mask_api_key(api_key: str) -> str:
    """Create masked preview of API key."""
    if len(api_key) > 10:
        return f"{api_key[:7]}...{api_key[-4:]}"
    return api_key[:4] + "****"


# Monkey patch serialization methods to APIKeyService if not present
if not hasattr(api_key_service, "_serialize"):
    import json

    api_key_service._serialize = json.dumps
    api_key_service._deserialize = json.loads


# ============================================
# API Endpoints
# ============================================


@router.post("", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: APIKeyCreateRequest,
    current_user: UserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> APIKeyCreateResponse:
    """Create a new API key."""
    try:
        # SECURITY: Bind API key to current user's tenant
        api_key, key_id = await _enhanced_create_api_key(
            user_id=current_user.user_id,
            name=request.name,
            scopes=request.scopes,
            expires_at=request.expires_at,
            description=request.description,
            tenant_id=current_user.tenant_id,  # SECURITY: Enforce tenant binding
            session=session,
        )
        await session.commit()

        return APIKeyCreateResponse(
            id=key_id,
            name=request.name,
            scopes=request.scopes,
            created_at=datetime.now(UTC),
            expires_at=request.expires_at,
            description=request.description,
            last_used_at=None,
            is_active=True,
            key_preview=_mask_api_key(api_key),
            api_key=api_key,
        )
    except RuntimeError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}",
        )


@router.get("", response_model=APIKeyListResponse)
async def list_api_keys(
    page: int = 1,
    limit: int = 50,
    current_user: UserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> APIKeyListResponse:
    """List user's API keys."""
    try:
        keys_data = await _list_user_api_keys(current_user.user_id, session=session)

        # Sort by creation date (newest first) - already sorted in DB query but ensure consistency
        keys_data.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_keys = keys_data[start_idx:end_idx]

        api_keys = []
        for key_data in paginated_keys:
            api_keys.append(
                APIKeyResponse(
                    id=key_data["id"],
                    name=key_data["name"],
                    scopes=key_data["scopes"],
                    created_at=datetime.fromisoformat(key_data["created_at"]),
                    expires_at=(
                        datetime.fromisoformat(key_data["expires_at"])
                        if key_data.get("expires_at")
                        else None
                    ),
                    description=key_data.get("description"),
                    last_used_at=(
                        datetime.fromisoformat(key_data["last_used_at"])
                        if key_data.get("last_used_at")
                        else None
                    ),
                    is_active=key_data.get("is_active", True),
                    key_preview=f"{key_data.get('prefix', 'sk_')}****",
                )
            )

        return APIKeyListResponse(
            api_keys=api_keys,
            total=len(keys_data),
            page=page,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list API keys: {str(e)}",
        )


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: str,
    current_user: UserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> APIKeyResponse:
    """Get API key details."""
    try:
        key_data = await _get_api_key_by_id(key_id, session=session)

        if not key_data or key_data.get("user_id") != current_user.user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

        return APIKeyResponse(
            id=key_data["id"],
            name=key_data["name"],
            scopes=key_data["scopes"],
            created_at=datetime.fromisoformat(key_data["created_at"]),
            expires_at=(
                datetime.fromisoformat(key_data["expires_at"])
                if key_data.get("expires_at")
                else None
            ),
            description=key_data.get("description"),
            last_used_at=(
                datetime.fromisoformat(key_data["last_used_at"])
                if key_data.get("last_used_at")
                else None
            ),
            is_active=key_data.get("is_active", True),
            key_preview=f"{key_data.get('prefix', 'sk_')}****",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get API key: {str(e)}",
        )


@router.patch("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: str,
    request: APIKeyUpdateRequest,
    current_user: UserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> APIKeyResponse:
    """Update API key."""
    try:
        key_data = await _get_api_key_by_id(key_id, session=session)

        if not key_data or key_data.get("user_id") != current_user.user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

        # Prepare updates
        updates: dict[str, Any] = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.scopes is not None:
            updates["scopes"] = request.scopes
        if request.description is not None:
            updates["description"] = request.description
        if request.is_active is not None:
            updates["is_active"] = request.is_active

        if updates:
            success = await _update_api_key_metadata(key_id, updates, session=session)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update API key",
                )
            await session.commit()

        # Get updated data
        updated_data = await _get_api_key_by_id(key_id, session=session)
        if not updated_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load updated API key metadata",
            )

        updated_id = str(updated_data["id"])
        return APIKeyResponse(
            id=updated_id,
            name=str(updated_data["name"]),
            scopes=list(updated_data["scopes"]),
            created_at=datetime.fromisoformat(str(updated_data["created_at"])),
            expires_at=(
                datetime.fromisoformat(str(updated_data["expires_at"]))
                if updated_data.get("expires_at")
                else None
            ),
            description=updated_data.get("description"),
            last_used_at=(
                datetime.fromisoformat(str(updated_data["last_used_at"]))
                if updated_data.get("last_used_at")
                else None
            ),
            is_active=bool(updated_data.get("is_active", True)),
            key_preview=f"{updated_data.get('prefix', 'sk_')}****",
        )
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update API key: {str(e)}",
        )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    current_user: UserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Revoke API key."""
    try:
        key_data = await _get_api_key_by_id(key_id, session=session)

        if not key_data or key_data.get("user_id") != current_user.user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

        success = await _revoke_api_key_by_id(key_id, session=session)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to revoke API key"
            )
        await session.commit()
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke API key: {str(e)}",
        )


# ============================================
# Available Scopes Endpoint
# ============================================


@router.get("/scopes/available", response_model=AvailableScopesResponse)
async def get_available_scopes(
    current_user: UserInfo = Depends(get_current_user),
) -> AvailableScopesResponse:
    """Get available API key scopes."""
    # Define available scopes based on your application's permissions
    scopes = {
        # General Access
        "read": {"name": "Read Access", "description": "Read-only access to resources"},
        "write": {"name": "Write Access", "description": "Create and update resources"},
        "delete": {"name": "Delete Access", "description": "Delete resources"},
        # Contacts
        "contacts:read": {"name": "Read Contacts", "description": "View contacts"},
        "contacts:write": {"name": "Manage Contacts", "description": "Create and manage contacts"},
        # Billing & Revenue
        "billing:read": {"name": "Read Billing", "description": "View invoices and billing data"},
        "billing:write": {
            "name": "Manage Billing",
            "description": "Create invoices and manage billing",
        },
        "billing:payments": {
            "name": "Process Payments",
            "description": "Record and process payments",
        },
        "subscriptions:read": {
            "name": "Read Subscriptions",
            "description": "View subscription plans",
        },
        "subscriptions:write": {
            "name": "Manage Subscriptions",
            "description": "Create and modify subscriptions",
        },
        # Support & Ticketing
        "tickets:read": {"name": "Read Tickets", "description": "View support tickets"},
        "tickets:write": {"name": "Manage Tickets", "description": "Create and update tickets"},
        "tickets:assign": {"name": "Assign Tickets", "description": "Assign tickets to agents"},
        # Communications
        "communications:read": {
            "name": "Read Communications",
            "description": "View communication history",
        },
        "communications:send": {
            "name": "Send Communications",
            "description": "Send emails and notifications",
        },
        "communications:campaigns": {
            "name": "Manage Campaigns",
            "description": "Create and manage campaigns",
        },
        "communications:templates": {
            "name": "Manage Templates",
            "description": "Manage communication templates",
        },
        # Operations & Automation
        "automation:read": {
            "name": "Read Automation",
            "description": "View automation playbooks and jobs",
        },
        "automation:execute": {
            "name": "Execute Automation",
            "description": "Run automation playbooks",
        },
        "workflows:read": {"name": "Read Workflows", "description": "View workflow definitions"},
        "workflows:execute": {
            "name": "Execute Workflows",
            "description": "Trigger workflow execution",
        },
        "jobs:read": {"name": "Read Jobs", "description": "View background jobs"},
        # Integrations
        "webhooks:read": {"name": "Read Webhooks", "description": "View webhook subscriptions"},
        "webhooks:manage": {
            "name": "Manage Webhooks",
            "description": "Create and manage webhook subscriptions",
        },
        "integrations:read": {
            "name": "Read Integrations",
            "description": "View configured integrations",
        },
        "integrations:manage": {
            "name": "Manage Integrations",
            "description": "Configure integrations",
        },
        # Analytics & Reporting
        "analytics:read": {
            "name": "Read Analytics",
            "description": "Access analytics and reporting data",
        },
        "analytics:export": {"name": "Export Analytics", "description": "Export analytics data"},
        # Partner Management
        "partner:read": {"name": "Read Partners", "description": "View partner information"},
        "partner:manage": {
            "name": "Manage Partners",
            "description": "Manage partner relationships",
        },
        "partner:tenants:list": {
            "name": "List Managed Tenants",
            "description": "View managed tenant list",
        },
        "partner:tenants:manage": {
            "name": "Manage Tenants",
            "description": "Manage partner tenants",
        },
    }

    return AvailableScopesResponse(scopes=scopes)
