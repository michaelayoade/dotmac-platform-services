"""
FastAPI routes for feature flag management (clean minimal version).
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from dotmac_shared.core.logging import get_logger

from .client import FeatureFlagClient
from .models import FeatureFlag, FeatureFlagStatus, RolloutStrategy

logger = get_logger(__name__)


class CreateFlagRequest(BaseModel):
    key: str
    name: str
    description: Optional[str] = None
    strategy: RolloutStrategy = RolloutStrategy.ALL_OFF
    percentage: float = Field(0.0, ge=0.0, le=100.0)
    user_list: list[str] = Field(default_factory=list)
    tenant_list: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    environments: list[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None
    payload: Optional[dict[str, Any]] = None


class UpdateFlagRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[FeatureFlagStatus] = None
    strategy: Optional[RolloutStrategy] = None
    percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    user_list: Optional[list[str]] = None
    tenant_list: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    expires_at: Optional[datetime] = None
    payload: Optional[dict[str, Any]] = None


class EvaluationRequest(BaseModel):
    context: dict[str, Any] = Field(default_factory=dict)


class EvaluationResponse(BaseModel):
    enabled: bool
    variant: Optional[str] = None
    payload: Optional[dict[str, Any]] = None


def create_feature_flag_router(client: FeatureFlagClient) -> APIRouter:
    router = APIRouter(prefix="/api/feature-flags", tags=["Feature Flags"])

    @router.get("/")
    async def list_flags(tags: Optional[str] = Query(None, description="Comma-separated tags")) -> list[dict[str, Any]]:
        try:
            tag_list = tags.split(",") if tags else None
            flags_data = await client.list_flags(tag_list)
            return flags_data
        except Exception as e:
            logger.error(f"Error listing flags: {e}")
            raise HTTPException(status_code=500, detail="Failed to list feature flags") from e

    @router.get("/{flag_key}")
    async def get_flag(flag_key: str) -> dict[str, Any]:
        try:
            flag_info = await client.get_flag_info(flag_key)
            if not flag_info:
                raise HTTPException(status_code=404, detail="Feature flag not found")
            return flag_info
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting flag {flag_key}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get feature flag") from e

    @router.post("/", status_code=201)
    async def create_flag(request: CreateFlagRequest) -> dict[str, Any]:
        try:
            data = request.model_dump()
            if not data["environments"]:
                data["environments"] = [client.environment]
            flag = FeatureFlag(**data, status=FeatureFlagStatus.ACTIVE)
            success = await client.manager.create_flag(flag)
            if not success:
                raise HTTPException(status_code=400, detail="Failed to create feature flag")
            return {"message": "Feature flag created", "key": request.key}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating flag {request.key}: {e}")
            raise HTTPException(status_code=500, detail="Failed to create feature flag") from e

    @router.put("/{flag_key}")
    async def update_flag(flag_key: str, request: UpdateFlagRequest) -> dict[str, str]:
        try:
            current_flag = await client.manager.get_flag_details(flag_key)
            if not current_flag:
                raise HTTPException(status_code=404, detail="Feature flag not found")
            for field, value in request.model_dump(exclude_unset=True).items():
                setattr(current_flag, field, value)
            current_flag.updated_at = datetime.utcnow()
            success = await client.manager.update_flag(current_flag)
            if not success:
                raise HTTPException(status_code=400, detail="Failed to update feature flag")
            return {"message": "Feature flag updated"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating flag {flag_key}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update feature flag") from e

    @router.delete("/{flag_key}")
    async def delete_flag(flag_key: str) -> dict[str, str]:
        try:
            success = await client.delete_flag(flag_key)
            if not success:
                raise HTTPException(status_code=404, detail="Feature flag not found")
            return {"message": "Feature flag deleted"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting flag {flag_key}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete feature flag") from e

    @router.post("/{flag_key}/evaluate", response_model=EvaluationResponse)
    async def evaluate_flag(flag_key: str, request: EvaluationRequest) -> EvaluationResponse:
        try:
            enabled = await client.is_enabled(flag_key, request.context)
            variant = await client.get_variant(flag_key, request.context)
            payload = await client.get_payload(flag_key, request.context)
            return EvaluationResponse(enabled=enabled, variant=variant, payload=payload)
        except Exception as e:
            logger.error(f"Error evaluating flag {flag_key}: {e}")
            raise HTTPException(status_code=500, detail="Failed to evaluate feature flag") from e

    return router
