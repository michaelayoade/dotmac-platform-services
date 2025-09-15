"""
Feature flag service layer using DRY patterns.
Consolidates business logic with built-in CRUD operations.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import EntityNotFoundError, ValidationError
from ..services import BaseService
from .api import CreateFlagRequest, EvaluationResponse, UpdateFlagRequest
from .client import FeatureFlagClient
from .models import FeatureFlag, FeatureFlagStatus

# Import the repository for database operations
try:
    from ..repositories import AsyncBaseRepository
except ImportError:
    AsyncBaseRepository = None


class FeatureFlagService(BaseService[FeatureFlag, CreateFlagRequest, UpdateFlagRequest, dict]):
    """Feature flag service with built-in CRUD and business logic."""

    def __init__(self, client: FeatureFlagClient, db: AsyncSession, tenant_id: str):
        super().__init__(
            db,
            tenant_id,
            create_schema=CreateFlagRequest,
            update_schema=UpdateFlagRequest,
            response_schema=dict,
        )
        self.client = client
        # Initialize repository for database operations
        from .repository import FeatureFlagRepository

        self.repository = FeatureFlagRepository(db, tenant_id)

    async def _apply_create_business_rules(self, data: CreateFlagRequest) -> CreateFlagRequest:
        """Apply business rules for flag creation."""
        # Ensure environment is set if not provided
        if not data.environments:
            data.environments = [self.client.environment]

        # Validate flag key format
        if not data.key.replace("-", "").replace("_", "").isalnum():
            raise ValidationError("Flag key can only contain alphanumeric characters, hyphens, and underscores")

        return data

    async def _apply_update_business_rules(self, entity_id: UUID, data: UpdateFlagRequest) -> UpdateFlagRequest:
        """Apply business rules for flag updates."""
        # Set updated timestamp
        if hasattr(data, "updated_at"):
            data.updated_at = datetime.utcnow()

        return data

    async def create_flag(self, data: CreateFlagRequest, user_id: str) -> dict[str, Any]:
        """Create a new feature flag with database and client integration."""
        # Apply business rules
        validated_data = await self._apply_create_business_rules(data)

        # Check if flag already exists
        existing_flag = await self.repository.find_by_key(validated_data.key)
        if existing_flag:
            raise ValidationError(f"Feature flag with key '{validated_data.key}' already exists")

        # Create flag object
        flag_dict = validated_data.model_dump()
        flag_dict.update(
            {
                "status": FeatureFlagStatus.ACTIVE,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )

        # Add tenant ID if available
        if self.repository.tenant_id:
            flag_dict["tenant_id"] = self.repository.tenant_id

        flag = FeatureFlag(**flag_dict)

        try:
            # Save to database
            created_flag = await self.repository.create(flag)

            # Also register with client for evaluation
            client_success = await self.client.manager.create_flag(flag)
            if not client_success:
                # Rollback database creation if client fails
                await self.repository.delete(created_flag.id)
                raise ValidationError("Failed to register flag with evaluation engine")

            return {
                "message": "Feature flag created successfully",
                "key": validated_data.key,
                "id": str(created_flag.id),
            }

        except Exception as e:
            await self.db.rollback()
            raise ValidationError(f"Failed to create feature flag: {str(e)}") from e

    async def update_flag(self, flag_key: str, data: UpdateFlagRequest, user_id: str) -> dict[str, str]:
        """Update an existing feature flag with database and client sync."""
        # Get current flag from database
        current_flag = await self.repository.find_by_key(flag_key)
        if not current_flag:
            raise EntityNotFoundError(f"Feature flag '{flag_key}' not found")

        # Apply business rules
        validated_data = await self._apply_update_business_rules(current_flag.id, data)

        try:
            # Update flag attributes
            update_dict = validated_data.model_dump(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow()

            # Update in database
            updated_flag = await self.repository.update(current_flag.id, update_dict)

            # Sync with evaluation client
            client_success = await self.client.manager.update_flag(updated_flag)
            if not client_success:
                # Log warning but don't fail - database is source of truth
                import logging

                logging.warning(f"Failed to sync flag '{flag_key}' with evaluation engine")

            return {
                "message": "Feature flag updated successfully",
                "key": flag_key,
                "updated_at": updated_flag.updated_at.isoformat(),
            }

        except Exception as e:
            await self.db.rollback()
            raise ValidationError(f"Failed to update feature flag: {str(e)}") from e

    async def delete_flag(self, flag_key: str, user_id: str) -> dict[str, str]:
        """Delete a feature flag with database and client cleanup."""
        # Get flag from database
        flag = await self.repository.find_by_key(flag_key)
        if not flag:
            raise EntityNotFoundError(f"Feature flag '{flag_key}' not found")

        try:
            # Soft delete in database (archive status)
            await self.repository.soft_delete_by_key(flag_key)

            # Remove from evaluation client
            client_success = await self.client.delete_flag(flag_key)
            if not client_success:
                import logging

                logging.warning(f"Failed to remove flag '{flag_key}' from evaluation engine")

            return {"message": "Feature flag deleted successfully", "key": flag_key}

        except Exception as e:
            await self.db.rollback()
            raise ValidationError(f"Failed to delete feature flag: {str(e)}") from e

    async def get_flag(self, flag_key: str, user_id: str) -> dict[str, Any]:
        """Get a feature flag by key from database."""
        flag = await self.repository.find_by_key(flag_key)
        if not flag:
            raise EntityNotFoundError(f"Feature flag '{flag_key}' not found")

        # Convert to dict format
        return {
            "key": flag.key,
            "name": flag.name,
            "description": flag.description,
            "status": flag.status.value,
            "strategy": flag.strategy.value,
            "percentage": flag.percentage,
            "user_list": flag.user_list,
            "tenant_list": flag.tenant_list,
            "tags": flag.tags,
            "environments": flag.environments,
            "created_at": flag.created_at.isoformat() if flag.created_at else None,
            "updated_at": flag.updated_at.isoformat() if flag.updated_at else None,
            "expires_at": flag.expires_at.isoformat() if flag.expires_at else None,
            "payload": flag.payload,
        }

    async def list_flags(self, tags: str | None = None, user_id: str | None = None) -> list[dict[str, Any]]:
        """List feature flags with optional tag filtering from database."""
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
            flags = await self.repository.find_by_tags(tag_list)
        else:
            flags = await self.repository.list()

        # Convert to dict format
        return [
            {
                "key": flag.key,
                "name": flag.name,
                "description": flag.description,
                "status": flag.status.value,
                "strategy": flag.strategy.value,
                "tags": flag.tags,
                "created_at": flag.created_at.isoformat() if flag.created_at else None,
                "updated_at": flag.updated_at.isoformat() if flag.updated_at else None,
            }
            for flag in flags
        ]

    async def evaluate_flag(self, flag_key: str, context: dict[str, Any], user_id: str) -> EvaluationResponse:
        """Evaluate a feature flag for given context."""
        enabled = await self.client.is_enabled(flag_key, context)
        variant = await self.client.get_variant(flag_key, context)
        payload = await self.client.get_payload(flag_key, context)

        return EvaluationResponse(enabled=enabled, variant=variant, payload=payload)
