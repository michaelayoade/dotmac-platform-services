"""API Key management endpoints."""

from datetime import datetime, UTC
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .core import UserInfo, get_current_user, api_key_service

router = APIRouter(prefix="/api/v1/auth/api-keys", tags=["API Keys"])


# ============================================
# Pydantic Models
# ============================================


class APIKeyCreateRequest(BaseModel):
    """Request to create API key."""
    name: str = Field(min_length=1, max_length=255, description="Human-readable name for the API key")
    scopes: List[str] = Field(default_factory=list, description="List of permissions/scopes for the key")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")


class APIKeyResponse(BaseModel):
    """API key information."""
    id: str = Field(description="API key identifier")
    name: str = Field(description="Human-readable name")
    scopes: List[str] = Field(description="Assigned permissions/scopes")
    created_at: datetime = Field(description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    description: Optional[str] = Field(None, description="Optional description")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")
    is_active: bool = Field(description="Whether the key is active")

    # Don't expose the actual key value in list responses
    key_preview: str = Field(description="Masked key preview (sk_****)")


class APIKeyCreateResponse(APIKeyResponse):
    """Response when creating API key - includes full key value."""
    api_key: str = Field(description="Full API key value (only shown once)")


class APIKeyListResponse(BaseModel):
    """List of API keys."""
    api_keys: List[APIKeyResponse]
    total: int
    page: int
    limit: int


class APIKeyUpdateRequest(BaseModel):
    """Request to update API key."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    scopes: Optional[List[str]] = Field(None)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = Field(None)


# ============================================
# Enhanced API Key Service Functions
# ============================================


async def _enhanced_create_api_key(
    user_id: str,
    name: str,
    scopes: List[str] | None = None,
    expires_at: Optional[datetime] = None,
    description: Optional[str] = None,
) -> tuple[str, str]:
    """Create API key with enhanced metadata."""
    key_id = str(uuid4())
    api_key = await api_key_service.create_api_key(user_id, name, scopes)

    # Store enhanced metadata
    client = await api_key_service._get_redis()
    enhanced_data = {
        "id": key_id,
        "user_id": user_id,
        "name": name,
        "scopes": scopes or [],
        "created_at": datetime.now(UTC).isoformat(),
        "expires_at": expires_at.isoformat() if expires_at else None,
        "description": description,
        "last_used_at": None,
        "is_active": True,
    }

    if client:
        await client.set(f"api_key_meta:{key_id}", api_key_service._serialize(enhanced_data))
        await client.set(f"api_key_lookup:{api_key}", key_id)
    else:
        # Fallback to memory
        if not hasattr(api_key_service, "_memory_meta"):
            api_key_service._memory_meta = {}
            api_key_service._memory_lookup = {}
        api_key_service._memory_meta[key_id] = enhanced_data
        api_key_service._memory_lookup[api_key] = key_id

    return api_key, key_id


async def _list_user_api_keys(user_id: str) -> List[dict]:
    """List all API keys for a user."""
    client = await api_key_service._get_redis()
    keys = []

    if client:
        # Scan for user's API key metadata
        async for key in client.scan_iter(match=f"api_key_meta:*"):
            data_str = await client.get(key)
            if data_str:
                data = api_key_service._deserialize(data_str)
                if data.get("user_id") == user_id:
                    keys.append(data)
    else:
        # Fallback to memory
        memory_meta = getattr(api_key_service, "_memory_meta", {})
        for data in memory_meta.values():
            if data.get("user_id") == user_id:
                keys.append(data)

    return keys


async def _get_api_key_by_id(key_id: str) -> Optional[dict]:
    """Get API key metadata by ID."""
    client = await api_key_service._get_redis()

    if client:
        data_str = await client.get(f"api_key_meta:{key_id}")
        return api_key_service._deserialize(data_str) if data_str else None
    else:
        # Fallback to memory
        memory_meta = getattr(api_key_service, "_memory_meta", {})
        return memory_meta.get(key_id)


async def _update_api_key_metadata(key_id: str, updates: dict) -> bool:
    """Update API key metadata."""
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
        # Fallback to memory
        memory_meta = getattr(api_key_service, "_memory_meta", {})
        if key_id in memory_meta:
            memory_meta[key_id].update(updates)
            return True
        return False


async def _revoke_api_key_by_id(key_id: str) -> bool:
    """Revoke API key by ID."""
    # First get the actual API key
    client = await api_key_service._get_redis()
    api_key = None

    if client:
        # Find the API key from lookup
        async for lookup_key in client.scan_iter(match=f"api_key_lookup:*"):
            stored_key_id = await client.get(lookup_key)
            if stored_key_id == key_id:
                api_key = lookup_key.replace("api_key_lookup:", "")
                break
    else:
        # Fallback to memory
        memory_lookup = getattr(api_key_service, "_memory_lookup", {})
        for key, stored_key_id in memory_lookup.items():
            if stored_key_id == key_id:
                api_key = key
                break

    if not api_key:
        return False

    # Revoke the actual key and clean up metadata
    success = await api_key_service.revoke_api_key(api_key)

    if success:
        if client:
            await client.delete(f"api_key_meta:{key_id}")
            await client.delete(f"api_key_lookup:{api_key}")
        else:
            # Fallback to memory
            memory_meta = getattr(api_key_service, "_memory_meta", {})
            memory_lookup = getattr(api_key_service, "_memory_lookup", {})
            memory_meta.pop(key_id, None)
            memory_lookup.pop(api_key, None)

    return success


def _mask_api_key(api_key: str) -> str:
    """Create masked preview of API key."""
    if len(api_key) > 10:
        return f"{api_key[:7]}...{api_key[-4:]}"
    return api_key[:4] + "****"


# Monkey patch serialization methods to APIKeyService if not present
if not hasattr(api_key_service, '_serialize'):
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
) -> APIKeyCreateResponse:
    """Create a new API key."""
    try:
        api_key, key_id = await _enhanced_create_api_key(
            user_id=current_user.user_id,
            name=request.name,
            scopes=request.scopes,
            expires_at=request.expires_at,
            description=request.description,
        )

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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.get("", response_model=APIKeyListResponse)
async def list_api_keys(
    page: int = 1,
    limit: int = 50,
    current_user: UserInfo = Depends(get_current_user),
) -> APIKeyListResponse:
    """List user's API keys."""
    try:
        keys_data = await _list_user_api_keys(current_user.user_id)

        # Sort by creation date (newest first)
        keys_data.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_keys = keys_data[start_idx:end_idx]

        api_keys = []
        for key_data in paginated_keys:
            api_keys.append(APIKeyResponse(
                id=key_data["id"],
                name=key_data["name"],
                scopes=key_data["scopes"],
                created_at=datetime.fromisoformat(key_data["created_at"]),
                expires_at=datetime.fromisoformat(key_data["expires_at"]) if key_data.get("expires_at") else None,
                description=key_data.get("description"),
                last_used_at=datetime.fromisoformat(key_data["last_used_at"]) if key_data.get("last_used_at") else None,
                is_active=key_data.get("is_active", True),
                key_preview=f"sk_****{key_data['id'][-4:]}"
            ))

        return APIKeyListResponse(
            api_keys=api_keys,
            total=len(keys_data),
            page=page,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list API keys: {str(e)}"
        )


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: str,
    current_user: UserInfo = Depends(get_current_user),
) -> APIKeyResponse:
    """Get API key details."""
    try:
        key_data = await _get_api_key_by_id(key_id)

        if not key_data or key_data.get("user_id") != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )

        return APIKeyResponse(
            id=key_data["id"],
            name=key_data["name"],
            scopes=key_data["scopes"],
            created_at=datetime.fromisoformat(key_data["created_at"]),
            expires_at=datetime.fromisoformat(key_data["expires_at"]) if key_data.get("expires_at") else None,
            description=key_data.get("description"),
            last_used_at=datetime.fromisoformat(key_data["last_used_at"]) if key_data.get("last_used_at") else None,
            is_active=key_data.get("is_active", True),
            key_preview=f"sk_****{key_data['id'][-4:]}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get API key: {str(e)}"
        )


@router.patch("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: str,
    request: APIKeyUpdateRequest,
    current_user: UserInfo = Depends(get_current_user),
) -> APIKeyResponse:
    """Update API key."""
    try:
        key_data = await _get_api_key_by_id(key_id)

        if not key_data or key_data.get("user_id") != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )

        # Prepare updates
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.scopes is not None:
            updates["scopes"] = request.scopes
        if request.description is not None:
            updates["description"] = request.description
        if request.is_active is not None:
            updates["is_active"] = request.is_active

        if updates:
            success = await _update_api_key_metadata(key_id, updates)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update API key"
                )

        # Get updated data
        updated_data = await _get_api_key_by_id(key_id)

        return APIKeyResponse(
            id=updated_data["id"],
            name=updated_data["name"],
            scopes=updated_data["scopes"],
            created_at=datetime.fromisoformat(updated_data["created_at"]),
            expires_at=datetime.fromisoformat(updated_data["expires_at"]) if updated_data.get("expires_at") else None,
            description=updated_data.get("description"),
            last_used_at=datetime.fromisoformat(updated_data["last_used_at"]) if updated_data.get("last_used_at") else None,
            is_active=updated_data.get("is_active", True),
            key_preview=f"sk_****{updated_data['id'][-4:]}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update API key: {str(e)}"
        )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    current_user: UserInfo = Depends(get_current_user),
):
    """Revoke API key."""
    try:
        key_data = await _get_api_key_by_id(key_id)

        if not key_data or key_data.get("user_id") != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )

        success = await _revoke_api_key_by_id(key_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke API key"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke API key: {str(e)}"
        )


# ============================================
# Available Scopes Endpoint
# ============================================


@router.get("/scopes/available", response_model=dict)
async def get_available_scopes(
    current_user: UserInfo = Depends(get_current_user),
) -> dict:
    """Get available API key scopes."""
    # Define available scopes based on your application's permissions
    scopes = {
        "read": {
            "name": "Read Access",
            "description": "Read-only access to resources"
        },
        "write": {
            "name": "Write Access",
            "description": "Create and update resources"
        },
        "delete": {
            "name": "Delete Access",
            "description": "Delete resources"
        },
        "customers:read": {
            "name": "Read Customers",
            "description": "View customer information"
        },
        "customers:write": {
            "name": "Manage Customers",
            "description": "Create and update customers"
        },
        "webhooks:manage": {
            "name": "Manage Webhooks",
            "description": "Create and manage webhook subscriptions"
        },
        "analytics:read": {
            "name": "Read Analytics",
            "description": "Access analytics and reporting data"
        },
    }

    return {"scopes": scopes}