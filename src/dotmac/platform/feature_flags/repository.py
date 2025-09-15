"""
Production-ready feature flag repository using DRY patterns.
Provides database operations with tenant isolation and caching.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import AsyncBaseRepository
from .models import FeatureFlag, FeatureFlagStatus


class FeatureFlagRepository(AsyncBaseRepository[FeatureFlag]):
    """
    Feature flag repository with tenant-aware operations.
    Inherits full CRUD functionality from AsyncBaseRepository.
    """

    def __init__(self, db: AsyncSession, tenant_id: str | None = None):
        super().__init__(FeatureFlag, db, tenant_id)

    async def find_by_key(self, flag_key: str) -> FeatureFlag | None:
        """Find a feature flag by its key."""
        query = select(FeatureFlag).where(FeatureFlag.key == flag_key)

        # Add tenant isolation if available
        if self.tenant_id and hasattr(FeatureFlag, "tenant_id"):
            query = query.where(FeatureFlag.tenant_id == self.tenant_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def find_by_status(self, status: FeatureFlagStatus) -> list[FeatureFlag]:
        """Find feature flags by status."""
        query = select(FeatureFlag).where(FeatureFlag.status == status)

        # Add tenant isolation if available
        if self.tenant_id and hasattr(FeatureFlag, "tenant_id"):
            query = query.where(FeatureFlag.tenant_id == self.tenant_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def find_by_tags(self, tags: list[str]) -> list[FeatureFlag]:
        """Find feature flags that have any of the specified tags."""
        if not tags:
            return await self.list()

        # Build query to match any tag (assuming JSON contains operation)
        conditions = [FeatureFlag.tags.contains([tag]) for tag in tags]
        query = select(FeatureFlag).where(or_(*conditions))

        # Add tenant isolation if available
        if self.tenant_id and hasattr(FeatureFlag, "tenant_id"):
            query = query.where(FeatureFlag.tenant_id == self.tenant_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def find_active_flags(self) -> list[FeatureFlag]:
        """Find all active feature flags for evaluation."""
        return await self.find_by_status(FeatureFlagStatus.ACTIVE)

    async def find_expired_flags(self) -> list[FeatureFlag]:
        """Find feature flags that have expired."""
        from datetime import datetime, timezone

        query = select(FeatureFlag).where(
            and_(
                FeatureFlag.expires_at.isnot(None),
                FeatureFlag.expires_at < datetime.now(timezone.utc),
                FeatureFlag.status == FeatureFlagStatus.ACTIVE,
            )
        )

        # Add tenant isolation if available
        if self.tenant_id and hasattr(FeatureFlag, "tenant_id"):
            query = query.where(FeatureFlag.tenant_id == self.tenant_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_by_status(self) -> dict[str, int]:
        """Get count of flags by status."""
        query = select(FeatureFlag.status, func.count(FeatureFlag.id)).group_by(FeatureFlag.status)

        # Add tenant isolation if available
        if self.tenant_id and hasattr(FeatureFlag, "tenant_id"):
            query = query.where(FeatureFlag.tenant_id == self.tenant_id)

        result = await self.db.execute(query)
        return dict(result.all())

    async def soft_delete_by_key(self, flag_key: str) -> bool:
        """Soft delete a feature flag by setting status to ARCHIVED."""
        flag = await self.find_by_key(flag_key)
        if not flag:
            return False

        flag.status = FeatureFlagStatus.ARCHIVED
        flag.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(flag)

        return True

    async def bulk_update_status(self, flag_keys: list[str], status: FeatureFlagStatus) -> int:
        """Bulk update status for multiple flags."""
        from datetime import datetime, timezone

        from sqlalchemy import update

        query = (
            update(FeatureFlag)
            .where(FeatureFlag.key.in_(flag_keys))
            .values(status=status, updated_at=datetime.now(timezone.utc))
        )

        # Add tenant isolation if available
        if self.tenant_id and hasattr(FeatureFlag, "tenant_id"):
            query = query.where(FeatureFlag.tenant_id == self.tenant_id)

        result = await self.db.execute(query)
        await self.db.commit()

        return result.rowcount
