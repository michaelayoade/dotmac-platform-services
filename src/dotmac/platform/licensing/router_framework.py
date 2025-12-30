"""
API router for composable licensing framework.

Provides REST endpoints for:
- Module and capability management
- Quota definition management
- Dynamic plan builder
- Subscription management
- Feature entitlement enforcement
- Quota tracking and enforcement
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = structlog.get_logger(__name__)

from dotmac.platform.auth.core import UserInfo
from dotmac.platform.auth.dependencies import get_current_user
from dotmac.platform.auth.platform_admin import require_platform_admin
from dotmac.platform.auth.rbac_dependencies import require_any_role
from dotmac.platform.db import get_async_session
from dotmac.platform.licensing.framework import (
    FeatureModule,
    PlanModule,
    PlanQuotaAllocation,
    QuotaDefinition,
    ServicePlan,
    SubscriptionModule,
    SubscriptionQuotaUsage,
    TenantSubscription,
)
from dotmac.platform.licensing.schemas_framework import (
    AddAddonRequest,
    EntitledCapabilitiesResponse,
    # Entitlement schemas
    FeatureEntitlementCheck,
    FeatureEntitlementResponse,
    # Module schemas
    FeatureModuleCreate,
    FeatureModuleResponse,
    FeatureModuleUpdate,
    ModuleCapabilityCreate,
    ModuleCapabilityResponse,
    PlanPricingResponse,
    QuotaCheckRequest,
    QuotaCheckResponse,
    QuotaConsumeRequest,
    QuotaConsumeResponse,
    # Quota schemas
    QuotaDefinitionCreate,
    QuotaDefinitionResponse,
    QuotaDefinitionUpdate,
    QuotaReleaseRequest,
    RemoveAddonRequest,
    # Plan schemas
    ServicePlanCreate,
    ServicePlanDuplicate,
    ServicePlanResponse,
    ServicePlanUpdate,
    # Subscription schemas
    SubscriptionCreate,
    SubscriptionModuleResponse,
    SubscriptionQuotaResponse,
    TenantSubscriptionResponse,
)
from dotmac.platform.licensing.service_framework import (
    FeatureNotEntitledError,
    LicensingFrameworkService,
    ModuleResolutionError,
    QuotaExceededError,
)
from dotmac.platform.tenant.dependencies import get_current_tenant
from dotmac.platform.tenant.models import Tenant

router = APIRouter(prefix="/licensing", tags=["Licensing Framework"])


def _build_subscription_response(subscription: TenantSubscription) -> TenantSubscriptionResponse:
    plan = subscription.plan
    plan_name = plan.plan_name if plan else ""
    custom_config = getattr(subscription, "custom_config", None)
    if custom_config is None:
        custom_config = getattr(subscription, "extra_metadata", {}) or {}

    modules: list[SubscriptionModuleResponse] = []
    for sub_module in subscription.active_modules or []:
        module = sub_module.module
        modules.append(
            SubscriptionModuleResponse(
                id=sub_module.id,
                module_id=sub_module.module_id,
                module_name=module.module_name if module else "",
                module_code=module.module_code if module else "",
                is_enabled=sub_module.is_enabled,
                source=sub_module.source,
                addon_price=sub_module.addon_price,
                expires_at=sub_module.expires_at,
                config=sub_module.config or {},
            )
        )

    quotas: list[SubscriptionQuotaResponse] = []
    for quota_usage in subscription.quota_usage or []:
        quota = quota_usage.quota
        quotas.append(
            SubscriptionQuotaResponse(
                id=quota_usage.id,
                quota_id=quota_usage.quota_id,
                quota_name=quota.quota_name if quota else "",
                quota_code=quota.quota_code if quota else "",
                unit_name=quota.unit_name if quota else "",
                period_start=quota_usage.period_start,
                period_end=quota_usage.period_end,
                allocated_quantity=quota_usage.allocated_quantity,
                current_usage=quota_usage.current_usage,
                overage_quantity=quota_usage.overage_quantity,
                overage_charges=quota_usage.overage_charges,
            )
        )

    return TenantSubscriptionResponse(
        id=subscription.id,
        tenant_id=subscription.tenant_id,
        plan_id=subscription.plan_id,
        plan_name=plan_name,
        status=subscription.status,
        billing_cycle=subscription.billing_cycle,
        monthly_price=subscription.monthly_price,
        annual_price=subscription.annual_price,
        trial_start=subscription.trial_start,
        trial_end=subscription.trial_end,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        stripe_customer_id=getattr(subscription, "stripe_customer_id", None),
        stripe_subscription_id=getattr(subscription, "stripe_subscription_id", None),
        custom_config=custom_config,
        modules=modules,
        quotas=quotas,
        created_at=subscription.created_at,
        updated_at=subscription.updated_at,
    )


# ========================================================================
# FEATURE MODULE MANAGEMENT (Platform Admin Only)
# ========================================================================


@router.post(
    "/modules",
    response_model=FeatureModuleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_platform_admin)],
)
async def create_feature_module(
    module_data: FeatureModuleCreate,
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Create a new feature module (building block).

    Platform admins can create reusable feature modules that can be
    composed into service plans.
    """
    service = LicensingFrameworkService(db)

    try:
        # Create module
        module = await service.create_feature_module(
            module_code=module_data.module_code,
            module_name=module_data.module_name,
            category=module_data.category,
            description=module_data.description,
            dependencies=module_data.dependencies,
            pricing_model=module_data.pricing_model,
            base_price=module_data.base_price,
            config_schema=module_data.config_schema,
            default_config=module_data.default_config,
        )

        # Add capabilities
        for cap_data in module_data.capabilities:
            await service.add_module_capability(
                module_id=module.id,
                capability_code=cap_data.capability_code,
                capability_name=cap_data.capability_name,
                description=cap_data.description,
                api_endpoints=cap_data.api_endpoints,
                ui_routes=cap_data.ui_routes,
                permissions=cap_data.permissions,
                config=cap_data.config,
            )

        # Reload with capabilities
        result = await db.execute(
            select(FeatureModule)
            .options(selectinload(FeatureModule.capabilities))
            .where(FeatureModule.id == module.id)
        )
        module = result.scalar_one()

        return FeatureModuleResponse.model_validate(module)

    except ModuleResolutionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/modules",
    response_model=list[FeatureModuleResponse],
)
async def list_feature_modules(
    category: str | None = Query(None),
    is_active: bool = Query(True),
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """List all available feature modules."""
    query = select(FeatureModule).options(selectinload(FeatureModule.capabilities))

    if category:
        query = query.where(FeatureModule.category == category)
    if current_user.is_platform_admin:
        if is_active is not None:
            query = query.where(FeatureModule.is_active == is_active)
    else:
        query = query.where(FeatureModule.is_active.is_(True), FeatureModule.is_public.is_(True))

    query = query.order_by(FeatureModule.category, FeatureModule.module_name)

    result = await db.execute(query)
    modules = result.scalars().all()

    return [FeatureModuleResponse.model_validate(m) for m in modules]


@router.get(
    "/modules/{module_id}",
    response_model=FeatureModuleResponse,
)
async def get_feature_module(
    module_id: UUID,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """Get feature module by ID."""
    result = await db.execute(
        select(FeatureModule)
        .options(selectinload(FeatureModule.capabilities))
        .where(FeatureModule.id == module_id)
    )
    module = result.scalar_one_or_none()

    if not module or (
        not current_user.is_platform_admin and (not module.is_public or not module.is_active)
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")

    return FeatureModuleResponse.model_validate(module)


@router.patch(
    "/modules/{module_id}",
    response_model=FeatureModuleResponse,
    dependencies=[Depends(require_platform_admin)],
)
async def update_feature_module(
    module_id: UUID,
    update_data: FeatureModuleUpdate,
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """Update feature module."""
    result = await db.execute(select(FeatureModule).where(FeatureModule.id == module_id))
    module = result.scalar_one_or_none()

    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")

    # Update fields
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(module, field, value)

    await db.commit()
    await db.refresh(module)

    # Reload with capabilities
    result = await db.execute(
        select(FeatureModule)
        .options(selectinload(FeatureModule.capabilities))
        .where(FeatureModule.id == module_id)
    )
    module = result.scalar_one()

    return FeatureModuleResponse.model_validate(module)


@router.post(
    "/modules/{module_id}/capabilities",
    response_model=ModuleCapabilityResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_platform_admin)],
)
async def add_module_capability(
    module_id: UUID,
    capability_data: ModuleCapabilityCreate,
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """Add a capability to a feature module."""
    service = LicensingFrameworkService(db)

    capability = await service.add_module_capability(
        module_id=module_id,
        capability_code=capability_data.capability_code,
        capability_name=capability_data.capability_name,
        description=capability_data.description,
        api_endpoints=capability_data.api_endpoints,
        ui_routes=capability_data.ui_routes,
        permissions=capability_data.permissions,
        config=capability_data.config,
    )

    return ModuleCapabilityResponse.model_validate(capability)


# ========================================================================
# QUOTA DEFINITION MANAGEMENT (Platform Admin Only)
# ========================================================================


@router.post(
    "/quotas",
    response_model=QuotaDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_platform_admin)],
)
async def create_quota_definition(
    quota_data: QuotaDefinitionCreate,
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """Create a new quota definition (building block)."""
    service = LicensingFrameworkService(db)

    quota = await service.create_quota_definition(
        quota_code=quota_data.quota_code,
        quota_name=quota_data.quota_name,
        description=quota_data.description,
        unit_name=quota_data.unit_name,
        pricing_model=quota_data.pricing_model,
        overage_rate=quota_data.overage_rate,
        is_metered=quota_data.is_metered,
        reset_period=quota_data.reset_period,
        config=quota_data.config,
    )

    return QuotaDefinitionResponse.model_validate(quota)


@router.get(
    "/quotas",
    response_model=list[QuotaDefinitionResponse],
    dependencies=[Depends(require_platform_admin)],
)
async def list_quota_definitions(
    is_metered: bool | None = Query(None),
    is_active: bool = Query(True),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """List all available quota definitions."""
    query = select(QuotaDefinition)

    if is_metered is not None:
        query = query.where(QuotaDefinition.is_metered == is_metered)
    if is_active is not None:
        query = query.where(QuotaDefinition.is_active == is_active)

    query = query.order_by(QuotaDefinition.quota_name)

    result = await db.execute(query)
    quotas = result.scalars().all()

    return [QuotaDefinitionResponse.model_validate(q) for q in quotas]


@router.get(
    "/quotas/{quota_id}",
    response_model=QuotaDefinitionResponse,
    dependencies=[Depends(require_platform_admin)],
)
async def get_quota_definition(
    quota_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """Get quota definition by ID."""
    result = await db.execute(select(QuotaDefinition).where(QuotaDefinition.id == quota_id))
    quota = result.scalar_one_or_none()

    if not quota:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quota not found")

    return QuotaDefinitionResponse.model_validate(quota)


@router.patch(
    "/quotas/{quota_id}",
    response_model=QuotaDefinitionResponse,
    dependencies=[Depends(require_platform_admin)],
)
async def update_quota_definition(
    quota_id: UUID,
    update_data: QuotaDefinitionUpdate,
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """Update quota definition."""
    result = await db.execute(select(QuotaDefinition).where(QuotaDefinition.id == quota_id))
    quota = result.scalar_one_or_none()

    if not quota:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quota not found")

    # Update fields
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(quota, field, value)

    await db.commit()
    await db.refresh(quota)

    return QuotaDefinitionResponse.model_validate(quota)


# ========================================================================
# DYNAMIC PLAN BUILDER (Platform Admin Only)
# ========================================================================


@router.post(
    "/plans",
    response_model=ServicePlanResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_platform_admin)],
)
async def create_service_plan(
    plan_data: ServicePlanCreate,
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """
    Create a new service plan by composing modules and quotas.

    This is the core endpoint for creating custom plans dynamically.
    """
    service = LicensingFrameworkService(db)

    try:
        plan = await service.create_service_plan(
            plan_name=plan_data.plan_name,
            plan_code=plan_data.plan_code,
            description=plan_data.description,
            base_price_monthly=plan_data.base_price_monthly,
            annual_discount_percent=plan_data.annual_discount_percent,
            is_template=plan_data.is_template,
            is_public=plan_data.is_public,
            is_custom=plan_data.is_custom,
            trial_days=plan_data.trial_days,
            trial_modules=plan_data.trial_modules,
            module_configs=[m.model_dump() for m in plan_data.modules],
            quota_configs=[q.model_dump() for q in plan_data.quotas],
            metadata=plan_data.metadata,
        )

        # Reload with relationships
        result = await db.execute(
            select(ServicePlan)
            .options(
                selectinload(ServicePlan.included_modules).selectinload(PlanModule.module),
                selectinload(ServicePlan.included_quotas).selectinload(PlanQuotaAllocation.quota),
            )
            .where(ServicePlan.id == plan.id)
        )
        plan = result.scalar_one()

        return ServicePlanResponse.model_validate(plan)

    except ModuleResolutionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/plans",
    response_model=list[ServicePlanResponse],
)
async def list_service_plans(
    is_template: bool | None = Query(None),
    is_public: bool | None = Query(None),
    is_active: bool = Query(True),
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """List all service plans."""
    query = select(ServicePlan).options(
        selectinload(ServicePlan.included_modules).selectinload(PlanModule.module),
        selectinload(ServicePlan.included_quotas).selectinload(PlanQuotaAllocation.quota),
    )

    if current_user.is_platform_admin:
        if is_template is not None:
            query = query.where(ServicePlan.is_template == is_template)
        if is_public is not None:
            query = query.where(ServicePlan.is_public == is_public)
        if is_active is not None:
            query = query.where(ServicePlan.is_active == is_active)
    else:
        query = query.where(ServicePlan.is_public.is_(True), ServicePlan.is_active.is_(True))

    query = query.order_by(ServicePlan.plan_name)

    result = await db.execute(query)
    plans = result.scalars().all()

    return [ServicePlanResponse.model_validate(p) for p in plans]


@router.get(
    "/plans/{plan_id}",
    response_model=ServicePlanResponse,
)
async def get_service_plan(
    plan_id: UUID,
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """Get service plan by ID."""
    result = await db.execute(
        select(ServicePlan)
        .options(
            selectinload(ServicePlan.included_modules).selectinload(PlanModule.module),
            selectinload(ServicePlan.included_quotas).selectinload(PlanQuotaAllocation.quota),
        )
        .where(ServicePlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()

    if not plan or (
        not current_user.is_platform_admin and (not plan.is_public or not plan.is_active)
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    return ServicePlanResponse.model_validate(plan)


@router.patch(
    "/plans/{plan_id}",
    response_model=ServicePlanResponse,
    dependencies=[Depends(require_platform_admin)],
)
async def update_service_plan(
    plan_id: UUID,
    update_data: ServicePlanUpdate,
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """Update service plan."""
    result = await db.execute(select(ServicePlan).where(ServicePlan.id == plan_id))
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    # Update fields
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)

    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(ServicePlan)
        .options(
            selectinload(ServicePlan.included_modules).selectinload(PlanModule.module),
            selectinload(ServicePlan.included_quotas).selectinload(PlanQuotaAllocation.quota),
        )
        .where(ServicePlan.id == plan_id)
    )
    plan = result.scalar_one()

    return ServicePlanResponse.model_validate(plan)


@router.post(
    "/plans/{plan_id}/duplicate",
    response_model=ServicePlanResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_platform_admin)],
)
async def duplicate_service_plan(
    plan_id: UUID,
    duplicate_data: ServicePlanDuplicate,
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """Duplicate an existing plan as a reusable template."""
    service = LicensingFrameworkService(db)

    try:
        new_plan = await service.duplicate_plan_as_template(
            source_plan_id=plan_id,
            new_plan_name=duplicate_data.new_plan_name,
            new_plan_code=duplicate_data.new_plan_code,
        )

        # Reload with relationships
        result = await db.execute(
            select(ServicePlan)
            .options(
                selectinload(ServicePlan.included_modules).selectinload(PlanModule.module),
                selectinload(ServicePlan.included_quotas).selectinload(PlanQuotaAllocation.quota),
            )
            .where(ServicePlan.id == new_plan.id)
        )
        new_plan = result.scalar_one()

        return ServicePlanResponse.model_validate(new_plan)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/plans/{plan_id}/pricing",
    response_model=PlanPricingResponse,
)
async def calculate_plan_pricing(
    plan_id: UUID,
    billing_cycle: str = Query("monthly"),
    addon_modules: str | None = Query(None, description="Comma-separated addon module IDs"),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """Calculate total pricing for a plan including add-ons."""
    from dotmac.platform.licensing.framework import BillingCycle

    service = LicensingFrameworkService(db)

    # Parse add-on modules
    addon_module_ids = []
    if addon_modules:
        try:
            addon_module_ids = [UUID(mid.strip()) for mid in addon_modules.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid addon module IDs",
            )

    try:
        cycle = BillingCycle(billing_cycle.strip().lower())
        pricing = await service.calculate_plan_price(plan_id, cycle, addon_module_ids)
        return PlanPricingResponse(**pricing)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ========================================================================
# SUBSCRIPTION MANAGEMENT
# ========================================================================


@router.post(
    "/subscriptions",
    response_model=TenantSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_platform_admin)],
)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """Create a new subscription for a tenant."""
    service = LicensingFrameworkService(db)

    try:
        subscription = await service.create_subscription(
            tenant_id=subscription_data.tenant_id,
            plan_id=subscription_data.plan_id,
            billing_cycle=subscription_data.billing_cycle,
            start_trial=subscription_data.start_trial,
            addon_module_ids=subscription_data.addon_module_ids,
            custom_config=subscription_data.custom_config,
            stripe_customer_id=subscription_data.stripe_customer_id,
            stripe_subscription_id=subscription_data.stripe_subscription_id,
        )

        # Reload with relationships
        result = await db.execute(
            select(TenantSubscription)
            .options(
                selectinload(TenantSubscription.plan),
                selectinload(TenantSubscription.active_modules).selectinload(
                    SubscriptionModule.module
                ),
                selectinload(TenantSubscription.quota_usage).selectinload(
                    SubscriptionQuotaUsage.quota
                ),
            )
            .where(TenantSubscription.id == subscription.id)
        )
        subscription = result.scalar_one()

        return _build_subscription_response(subscription)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/subscriptions/current",
    response_model=TenantSubscriptionResponse,
)
async def get_current_subscription(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """Get current tenant's active subscription."""
    from dotmac.platform.licensing.framework import SubscriptionStatus

    result = await db.execute(
        select(TenantSubscription)
        .options(
            selectinload(TenantSubscription.plan),
            selectinload(TenantSubscription.active_modules).selectinload(SubscriptionModule.module),
            selectinload(TenantSubscription.quota_usage).selectinload(
                SubscriptionQuotaUsage.quota
            ),
        )
        .where(
            TenantSubscription.tenant_id == tenant.id,
            TenantSubscription.status.in_(
                [
                    SubscriptionStatus.TRIAL.value,
                    SubscriptionStatus.ACTIVE.value,
                    SubscriptionStatus.PAST_DUE.value,
                ]
            ),
        )
        .order_by(TenantSubscription.created_at.desc())
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found",
        )

    return _build_subscription_response(subscription)


@router.post(
    "/subscriptions/current/addons",
    response_model=TenantSubscriptionResponse,
    dependencies=[Depends(require_any_role("owner", "admin"))],
)
async def add_addon_to_current_subscription(
    addon_request: AddAddonRequest,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """Add an add-on module to current subscription."""
    from dotmac.platform.licensing.framework import SubscriptionStatus

    service = LicensingFrameworkService(db)

    # Get current subscription
    result = await db.execute(
        select(TenantSubscription)
        .where(
            TenantSubscription.tenant_id == tenant.id,
            TenantSubscription.status.in_(
                [
                    SubscriptionStatus.TRIAL.value,
                    SubscriptionStatus.ACTIVE.value,
                ]
            ),
        )
        .order_by(TenantSubscription.created_at.desc())
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found",
        )

    try:
        await service.add_addon_to_subscription(
            subscription_id=subscription.id,
            module_id=addon_request.module_id,
            activated_by=current_user.user_id,
        )

        # Reload with relationships
        result = await db.execute(
            select(TenantSubscription)
            .options(
                selectinload(TenantSubscription.plan),
                selectinload(TenantSubscription.active_modules).selectinload(
                    SubscriptionModule.module
                ),
                selectinload(TenantSubscription.quota_usage),
            )
            .where(TenantSubscription.id == subscription.id)
        )
        subscription = result.scalar_one()

        return _build_subscription_response(subscription)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/subscriptions/current/addons",
    response_model=TenantSubscriptionResponse,
    dependencies=[Depends(require_any_role("owner", "admin"))],
)
async def remove_addon_from_current_subscription(
    addon_request: RemoveAddonRequest,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: UserInfo = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """Remove an add-on module from current subscription."""
    from dotmac.platform.licensing.framework import SubscriptionStatus

    service = LicensingFrameworkService(db)

    # Get current subscription
    result = await db.execute(
        select(TenantSubscription)
        .where(
            TenantSubscription.tenant_id == tenant.id,
            TenantSubscription.status.in_(
                [
                    SubscriptionStatus.TRIAL.value,
                    SubscriptionStatus.ACTIVE.value,
                ]
            ),
        )
        .order_by(TenantSubscription.created_at.desc())
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found",
        )

    try:
        await service.remove_addon_from_subscription(
            subscription_id=subscription.id,
            module_id=addon_request.module_id,
            deactivated_by=current_user.user_id,
        )

        # Reload with relationships
        result = await db.execute(
            select(TenantSubscription)
            .options(
                selectinload(TenantSubscription.plan),
                selectinload(TenantSubscription.active_modules).selectinload(
                    SubscriptionModule.module
                ),
                selectinload(TenantSubscription.quota_usage),
            )
            .where(TenantSubscription.id == subscription.id)
        )
        subscription = result.scalar_one()

        return _build_subscription_response(subscription)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========================================================================
# FEATURE ENTITLEMENT ENFORCEMENT
# ========================================================================


@router.post(
    "/entitlements/check",
    response_model=FeatureEntitlementResponse,
)
async def check_feature_entitlement(
    check_request: FeatureEntitlementCheck,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """Check if tenant has access to a feature module/capability."""
    service = LicensingFrameworkService(db)

    entitled = await service.check_feature_entitlement(
        tenant_id=tenant.id,
        module_code=check_request.module_code,
        capability_code=check_request.capability_code,
    )

    return FeatureEntitlementResponse(
        entitled=entitled,
        module_code=check_request.module_code,
        capability_code=check_request.capability_code,
        subscription_id=None,  # Could be populated
        expires_at=None,  # Could be populated
    )


@router.get(
    "/entitlements/capabilities",
    response_model=EntitledCapabilitiesResponse,
)
async def get_entitled_capabilities(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """Get all capabilities tenant has access to."""
    service = LicensingFrameworkService(db)

    capabilities = await service.get_entitled_capabilities(tenant_id=tenant.id)

    return EntitledCapabilitiesResponse(capabilities=capabilities)


# ========================================================================
# QUOTA ENFORCEMENT
# ========================================================================


@router.post(
    "/quotas/check",
    response_model=QuotaCheckResponse,
)
async def check_quota(
    check_request: QuotaCheckRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """Check if tenant has quota available."""
    service = LicensingFrameworkService(db)

    try:
        result = await service.check_quota(
            tenant_id=tenant.id,
            quota_code=check_request.quota_code,
            requested_quantity=check_request.requested_quantity,
        )

        return QuotaCheckResponse(
            allowed=result["allowed"],
            quota_code=check_request.quota_code,
            allocated=result["allocated"],
            current=result["current"],
            available=result["available"],
            overage_allowed=result["overage_allowed"],
            overage_rate=result["overage_rate"],
            soft_limit=result.get("soft_limit"),
        )

    except (ValueError, FeatureNotEntitledError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/quotas/consume",
    response_model=QuotaConsumeResponse,
)
async def consume_quota(
    consume_request: QuotaConsumeRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_session),
) -> Any:
    """Consume quota and track usage."""
    service = LicensingFrameworkService(db)

    try:
        result = await service.consume_quota(
            tenant_id=tenant.id,
            quota_code=consume_request.quota_code,
            quantity=consume_request.quantity,
            metadata=consume_request.metadata,
        )

        return QuotaConsumeResponse(
            success=result["success"],
            quota_code=consume_request.quota_code,
            new_usage=result["new_usage"],
            overage=result["overage"],
            overage_charge=result["overage_charge"],
        )

    except QuotaExceededError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except (ValueError, FeatureNotEntitledError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/quotas/release",
    status_code=status.HTTP_200_OK,
)
async def release_quota(
    release_request: QuotaReleaseRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Release quota (e.g., when user is deleted)."""
    service = LicensingFrameworkService(db)

    await service.release_quota(
        tenant_id=tenant.id,
        quota_code=release_request.quota_code,
        quantity=release_request.quantity,
    )

    return {"status": "released"}


# ========================================================================
# LICENSING DASHBOARD
# ========================================================================


class LicensingSummary(BaseModel):
    """Summary statistics for licensing dashboard."""

    model_config = ConfigDict()

    total_modules: int = Field(description="Total feature modules")
    active_modules: int = Field(description="Active feature modules")
    total_plans: int = Field(description="Total service plans")
    active_plans: int = Field(description="Active service plans")
    public_plans: int = Field(description="Public service plans")
    total_quotas: int = Field(description="Total quota definitions")
    total_subscriptions: int = Field(description="Total tenant subscriptions")
    active_subscriptions: int = Field(description="Active tenant subscriptions")
    trial_subscriptions: int = Field(description="Trial tenant subscriptions")


class LicensingChartDataPoint(BaseModel):
    """Single data point for licensing charts."""

    model_config = ConfigDict()

    label: str
    value: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class LicensingCharts(BaseModel):
    """Chart data for licensing dashboard."""

    model_config = ConfigDict()

    subscriptions_by_status: list[LicensingChartDataPoint] = Field(description="Subscriptions by status")
    subscriptions_by_plan: list[LicensingChartDataPoint] = Field(description="Subscriptions by plan")
    modules_by_category: list[LicensingChartDataPoint] = Field(description="Modules by category")
    subscription_trend: list[LicensingChartDataPoint] = Field(description="Monthly subscription trend")


class LicensingAlert(BaseModel):
    """Alert item for licensing dashboard."""

    model_config = ConfigDict()

    type: str = Field(description="Alert type: warning, error, info")
    title: str
    message: str
    count: int = 0
    action_url: str | None = None


class LicensingRecentActivity(BaseModel):
    """Recent activity item for licensing dashboard."""

    model_config = ConfigDict()

    id: str
    type: str = Field(description="Activity type: subscription, plan, module")
    description: str
    status: str
    timestamp: datetime
    tenant_id: str | None = None


class LicensingDashboardResponse(BaseModel):
    """Consolidated licensing dashboard response."""

    model_config = ConfigDict()

    summary: LicensingSummary
    charts: LicensingCharts
    alerts: list[LicensingAlert]
    recent_activity: list[LicensingRecentActivity]
    generated_at: datetime


@router.get(
    "/dashboard",
    response_model=LicensingDashboardResponse,
    summary="Get licensing dashboard data",
    description="Returns consolidated licensing metrics, charts, and alerts for the dashboard",
    dependencies=[Depends(require_platform_admin)],
)
async def get_licensing_dashboard(
    period_months: int = Query(6, ge=1, le=24, description="Months of trend data"),
    db: AsyncSession = Depends(get_async_session),
) -> LicensingDashboardResponse:
    """
    Get consolidated licensing dashboard data including:
    - Summary statistics (modules, plans, quotas, subscriptions)
    - Chart data (trends, breakdowns)
    - Alerts (expiring trials, etc.)
    - Recent activity
    """
    try:
        from dotmac.platform.licensing.framework import SubscriptionStatus

        now = datetime.now(timezone.utc)

        # ========== SUMMARY STATS ==========
        # Module counts
        module_counts_query = select(
            func.count(FeatureModule.id).label("total"),
            func.sum(case((FeatureModule.is_active.is_(True), 1), else_=0)).label("active"),
        )
        module_counts_result = await db.execute(module_counts_query)
        module_counts = module_counts_result.one()

        # Plan counts
        plan_counts_query = select(
            func.count(ServicePlan.id).label("total"),
            func.sum(case((ServicePlan.is_active.is_(True), 1), else_=0)).label("active"),
            func.sum(case((ServicePlan.is_public.is_(True), 1), else_=0)).label("public"),
        )
        plan_counts_result = await db.execute(plan_counts_query)
        plan_counts = plan_counts_result.one()

        # Quota counts
        quota_counts_query = select(func.count(QuotaDefinition.id))
        quota_counts_result = await db.execute(quota_counts_query)
        total_quotas = quota_counts_result.scalar() or 0

        # Subscription counts
        subscription_counts_query = select(
            func.count(TenantSubscription.id).label("total"),
            func.sum(case((TenantSubscription.status == SubscriptionStatus.ACTIVE.value, 1), else_=0)).label("active"),
            func.sum(case((TenantSubscription.status == SubscriptionStatus.TRIAL.value, 1), else_=0)).label("trial"),
        )
        subscription_counts_result = await db.execute(subscription_counts_query)
        subscription_counts = subscription_counts_result.one()

        summary = LicensingSummary(
            total_modules=module_counts.total or 0,
            active_modules=module_counts.active or 0,
            total_plans=plan_counts.total or 0,
            active_plans=plan_counts.active or 0,
            public_plans=plan_counts.public or 0,
            total_quotas=total_quotas,
            total_subscriptions=subscription_counts.total or 0,
            active_subscriptions=subscription_counts.active or 0,
            trial_subscriptions=subscription_counts.trial or 0,
        )

        # ========== CHART DATA ==========
        # Subscriptions by status
        status_query = select(
            TenantSubscription.status,
            func.count(TenantSubscription.id),
        ).group_by(TenantSubscription.status)
        status_result = await db.execute(status_query)
        subscriptions_by_status = [
            LicensingChartDataPoint(label=row[0] if row[0] else "unknown", value=row[1])
            for row in status_result.all()
        ]

        # Subscriptions by plan
        plan_query = select(
            ServicePlan.plan_name,
            func.count(TenantSubscription.id),
        ).join(ServicePlan, TenantSubscription.plan_id == ServicePlan.id).group_by(ServicePlan.plan_name)
        plan_result = await db.execute(plan_query)
        subscriptions_by_plan = [
            LicensingChartDataPoint(label=row[0] if row[0] else "Unknown Plan", value=row[1])
            for row in plan_result.all()
        ]

        # Modules by category
        category_query = select(
            FeatureModule.category,
            func.count(FeatureModule.id),
        ).where(FeatureModule.is_active.is_(True)).group_by(FeatureModule.category)
        category_result = await db.execute(category_query)
        modules_by_category = [
            LicensingChartDataPoint(label=row[0] if row[0] else "uncategorized", value=row[1])
            for row in category_result.all()
        ]

        # Subscription trend (monthly)
        subscription_trend = []
        for i in range(period_months - 1, -1, -1):
            month_date = (now - timedelta(days=i * 30)).replace(day=1)
            next_month = (month_date + timedelta(days=32)).replace(day=1)

            month_count_query = select(func.count(TenantSubscription.id)).where(
                TenantSubscription.created_at >= month_date,
                TenantSubscription.created_at < next_month,
            )
            month_count_result = await db.execute(month_count_query)
            month_count = month_count_result.scalar() or 0

            subscription_trend.append(LicensingChartDataPoint(
                label=month_date.strftime("%b %Y"),
                value=month_count,
            ))

        charts = LicensingCharts(
            subscriptions_by_status=subscriptions_by_status,
            subscriptions_by_plan=subscriptions_by_plan,
            modules_by_category=modules_by_category,
            subscription_trend=subscription_trend,
        )

        # ========== ALERTS ==========
        alerts = []

        # Expiring trials in next 7 days
        trial_expiring_query = select(func.count(TenantSubscription.id)).where(
            TenantSubscription.status == SubscriptionStatus.TRIAL.value,
            TenantSubscription.trial_end <= now + timedelta(days=7),
            TenantSubscription.trial_end > now,
        )
        trial_expiring_result = await db.execute(trial_expiring_query)
        expiring_trials = trial_expiring_result.scalar() or 0

        if expiring_trials > 0:
            alerts.append(LicensingAlert(
                type="warning",
                title="Expiring Trials",
                message=f"{expiring_trials} trial(s) expiring in the next 7 days",
                count=expiring_trials,
                action_url="/licensing/subscriptions?status=trial",
            ))

        # Past due subscriptions
        past_due_query = select(func.count(TenantSubscription.id)).where(
            TenantSubscription.status == SubscriptionStatus.PAST_DUE.value,
        )
        past_due_result = await db.execute(past_due_query)
        past_due_count = past_due_result.scalar() or 0

        if past_due_count > 0:
            alerts.append(LicensingAlert(
                type="error",
                title="Past Due Subscriptions",
                message=f"{past_due_count} subscription(s) are past due",
                count=past_due_count,
                action_url="/licensing/subscriptions?status=past_due",
            ))

        # ========== RECENT ACTIVITY ==========
        recent_subscriptions_query = (
            select(TenantSubscription)
            .options(selectinload(TenantSubscription.plan))
            .order_by(TenantSubscription.created_at.desc())
            .limit(10)
        )
        recent_subscriptions_result = await db.execute(recent_subscriptions_query)
        recent_subscriptions = recent_subscriptions_result.scalars().all()

        recent_activity = [
            LicensingRecentActivity(
                id=str(sub.id),
                type="subscription",
                description=f"Subscription: {sub.plan.plan_name if sub.plan else 'Unknown Plan'}",
                status=sub.status if sub.status else "unknown",
                timestamp=sub.created_at,
                tenant_id=sub.tenant_id,
            )
            for sub in recent_subscriptions
        ]

        return LicensingDashboardResponse(
            summary=summary,
            charts=charts,
            alerts=alerts,
            recent_activity=recent_activity,
            generated_at=now,
        )

    except Exception as e:
        logger.error("Failed to generate licensing dashboard", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate licensing dashboard: {str(e)}",
        )
