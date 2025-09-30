"""
API endpoints for RBAC management
"""
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.db import get_session
from dotmac.platform.auth.core import get_current_user, UserInfo
from dotmac.platform.auth.rbac_service import RBACService, get_rbac_service
from dotmac.platform.auth.rbac_dependencies import (
    require_permission,
    require_role,
    require_admin
)
from dotmac.platform.auth.models import PermissionCategory

router = APIRouter(tags=["rbac"])


# ==================== Pydantic Models ====================

class PermissionResponse(BaseModel):
    """Permission response model"""
    id: UUID
    name: str
    display_name: str
    description: Optional[str]
    category: PermissionCategory
    is_active: bool
    is_system: bool


class RoleResponse(BaseModel):
    """Role response model"""
    id: UUID
    name: str
    display_name: str
    description: Optional[str]
    priority: int
    is_active: bool
    is_system: bool
    is_default: bool
    permissions: List[PermissionResponse] = []
    user_count: Optional[int] = None


class RoleCreateRequest(BaseModel):
    """Request to create a role"""
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    parent_role: Optional[str] = None
    is_default: bool = False


class RoleUpdateRequest(BaseModel):
    """Request to update a role"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class UserRoleAssignment(BaseModel):
    """User role assignment request"""
    user_id: UUID
    role_name: str
    expires_at: Optional[datetime] = None
    metadata: Optional[dict] = None


class UserPermissionGrant(BaseModel):
    """Direct permission grant request"""
    user_id: UUID
    permission_name: str
    granted: bool = True  # True to grant, False to revoke
    expires_at: Optional[datetime] = None
    reason: Optional[str] = None


class UserPermissionsResponse(BaseModel):
    """User permissions response"""
    user_id: UUID
    permissions: List[str]
    roles: List[RoleResponse]
    direct_grants: List[PermissionResponse]
    effective_permissions: List[str]  # All permissions after inheritance


# ==================== Permission Endpoints ====================

@router.get("/permissions", response_model=List[PermissionResponse])
async def list_permissions(
    category: Optional[PermissionCategory] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_session),
    current_user: UserInfo = Depends(require_permission("admin.role.manage"))
):
    """List all available permissions"""
    from dotmac.platform.auth.models import Permission

    query = db.query(Permission)

    if category:
        query = query.filter(Permission.category == category)

    if active_only:
        query = query.filter(Permission.is_active == True)

    permissions = query.order_by(Permission.category, Permission.name).all()

    return [
        PermissionResponse(
            id=p.id,
            name=p.name,
            display_name=p.display_name,
            description=p.description,
            category=p.category,
            is_active=p.is_active,
            is_system=p.is_system
        )
        for p in permissions
    ]


@router.get("/permissions/{permission_name}", response_model=PermissionResponse)
async def get_permission(
    permission_name: str,
    db: AsyncSession = Depends(get_session),
    current_user: UserInfo = Depends(require_permission("admin.role.manage"))
):
    """Get details of a specific permission"""
    from dotmac.platform.auth.models import Permission

    permission = db.query(Permission).filter_by(name=permission_name).first()

    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission '{permission_name}' not found"
        )

    return PermissionResponse(
        id=permission.id,
        name=permission.name,
        display_name=permission.display_name,
        description=permission.description,
        category=permission.category,
        is_active=permission.is_active,
        is_system=permission.is_system
    )


# ==================== Role Endpoints ====================

@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    active_only: bool = True,
    include_permissions: bool = False,
    include_user_count: bool = False,
    db: AsyncSession = Depends(get_session),
    current_user: UserInfo = Depends(require_permission("admin.role.manage"))
):
    """List all available roles"""
    from dotmac.platform.auth.models import Role, user_roles
    from sqlalchemy import select, func
    from sqlalchemy.orm import selectinload

    query = db.query(Role)

    if active_only:
        query = query.filter(Role.is_active == True)

    if include_permissions:
        query = query.options(selectinload(Role.permissions))

    roles = query.order_by(Role.priority.desc(), Role.name).all()

    response = []
    for role in roles:
        role_resp = RoleResponse(
            id=role.id,
            name=role.name,
            display_name=role.display_name,
            description=role.description,
            priority=role.priority,
            is_active=role.is_active,
            is_system=role.is_system,
            is_default=role.is_default
        )

        if include_permissions:
            role_resp.permissions = [
                PermissionResponse(
                    id=p.id,
                    name=p.name,
                    display_name=p.display_name,
                    description=p.description,
                    category=p.category,
                    is_active=p.is_active,
                    is_system=p.is_system
                )
                for p in role.permissions
            ]

        if include_user_count:
            count = db.query(func.count(user_roles.c.user_id)).filter(
                user_roles.c.role_id == role.id
            ).scalar()
            role_resp.user_count = count

        response.append(role_resp)

    return response


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    request: RoleCreateRequest,
    db: AsyncSession = Depends(get_session),
    rbac_service: RBACService = Depends(get_rbac_service),
    current_user: UserInfo = Depends(require_admin)
):
    """Create a new role"""
    try:
        role = await rbac_service.create_role(
            name=request.name,
            display_name=request.display_name,
            description=request.description,
            permissions=request.permissions,
            parent_role=request.parent_role,
            is_default=request.is_default
        )

        return RoleResponse(
            id=role.id,
            name=role.name,
            display_name=role.display_name,
            description=role.description,
            priority=role.priority,
            is_active=role.is_active,
            is_system=role.is_system,
            is_default=role.is_default
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/roles/{role_name}", response_model=RoleResponse)
async def update_role(
    role_name: str,
    request: RoleUpdateRequest,
    db: AsyncSession = Depends(get_session),
    current_user: UserInfo = Depends(require_admin)
):
    """Update an existing role"""
    from dotmac.platform.auth.models import Role, Permission

    role = db.query(Role).filter_by(name=role_name).first()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{role_name}' not found"
        )

    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System roles cannot be modified"
        )

    # Update fields
    if request.display_name is not None:
        role.display_name = request.display_name

    if request.description is not None:
        role.description = request.description

    if request.is_active is not None:
        role.is_active = request.is_active

    if request.is_default is not None:
        # Only one role can be default
        if request.is_default:
            db.query(Role).filter(Role.id != role.id).update({"is_default": False})
        role.is_default = request.is_default

    if request.permissions is not None:
        # Update permissions
        role.permissions.clear()
        for perm_name in request.permissions:
            permission = db.query(Permission).filter_by(name=perm_name).first()
            if permission:
                role.permissions.append(permission)

    db.commit()

    return RoleResponse(
        id=role.id,
        name=role.name,
        display_name=role.display_name,
        description=role.description,
        priority=role.priority,
        is_active=role.is_active,
        is_system=role.is_system,
        is_default=role.is_default
    )


@router.delete("/roles/{role_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_name: str,
    db: AsyncSession = Depends(get_session),
    current_user: UserInfo = Depends(require_admin)
):
    """Delete a role"""
    from dotmac.platform.auth.models import Role

    role = db.query(Role).filter_by(name=role_name).first()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{role_name}' not found"
        )

    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System roles cannot be deleted"
        )

    db.delete(role)
    db.commit()


# ==================== User Permission Management ====================

@router.get("/users/{user_id}/permissions", response_model=UserPermissionsResponse)
async def get_user_permissions(
    user_id: UUID,
    db: AsyncSession = Depends(get_session),
    rbac_service: RBACService = Depends(get_rbac_service),
    current_user: UserInfo = Depends(require_permission("admin.user.read"))
):
    """Get all permissions for a user"""
    # Get effective permissions
    permissions = await rbac_service.get_user_permissions(user_id)

    # Get roles
    roles = await rbac_service.get_user_roles(user_id)

    # Get direct permission grants
    from dotmac.platform.auth.models import Permission, user_permissions

    direct_perms = db.query(Permission).join(user_permissions).filter(
        user_permissions.c.user_id == user_id,
        user_permissions.c.granted == True
    ).all()

    return UserPermissionsResponse(
        user_id=user_id,
        permissions=list(permissions),
        roles=[
            RoleResponse(
                id=r.id,
                name=r.name,
                display_name=r.display_name,
                description=r.description,
                priority=r.priority,
                is_active=r.is_active,
                is_system=r.is_system,
                is_default=r.is_default
            )
            for r in roles
        ],
        direct_grants=[
            PermissionResponse(
                id=p.id,
                name=p.name,
                display_name=p.display_name,
                description=p.description,
                category=p.category,
                is_active=p.is_active,
                is_system=p.is_system
            )
            for p in direct_perms
        ],
        effective_permissions=list(permissions)
    )


@router.post("/users/assign-role", status_code=status.HTTP_204_NO_CONTENT)
async def assign_role_to_user(
    request: UserInfoRoleAssignment,
    db: AsyncSession = Depends(get_session),
    rbac_service: RBACService = Depends(get_rbac_service),
    current_user: UserInfo = Depends(require_admin)
):
    """Assign a role to a user"""
    await rbac_service.assign_role_to_user(
        user_id=request.user_id,
        role_name=request.role_name,
        granted_by=current_user.id,
        expires_at=request.expires_at,
        metadata=request.metadata
    )


@router.post("/users/revoke-role", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_role_from_user(
    request: UserInfoRoleAssignment,
    db: AsyncSession = Depends(get_session),
    rbac_service: RBACService = Depends(get_rbac_service),
    current_user: UserInfo = Depends(require_admin)
):
    """Revoke a role from a user"""
    await rbac_service.revoke_role_from_user(
        user_id=request.user_id,
        role_name=request.role_name,
        revoked_by=current_user.id,
        reason=request.metadata.get("reason") if request.metadata else None
    )


@router.post("/users/grant-permission", status_code=status.HTTP_204_NO_CONTENT)
async def grant_permission_to_user(
    request: UserInfoPermissionGrant,
    db: AsyncSession = Depends(get_session),
    rbac_service: RBACService = Depends(get_rbac_service),
    current_user: UserInfo = Depends(require_admin)
):
    """Grant or revoke a specific permission directly to/from a user"""
    if request.granted:
        await rbac_service.grant_permission_to_user(
            user_id=request.user_id,
            permission_name=request.permission_name,
            granted_by=current_user.id,
            expires_at=request.expires_at,
            reason=request.reason
        )
    else:
        # Revoke by setting granted=False in user_permissions
        from dotmac.platform.auth.models import Permission, user_permissions

        permission = db.query(Permission).filter_by(name=request.permission_name).first()
        if permission:
            db.execute(
                user_permissions.update()
                .where(
                    user_permissions.c.user_id == request.user_id,
                    user_permissions.c.permission_id == permission.id
                )
                .values(granted=False, reason=request.reason)
            )
            db.commit()


@router.get("/my-permissions", response_model=UserPermissionsResponse)
async def get_my_permissions(
    db: AsyncSession = Depends(get_session),
    rbac_service: RBACService = Depends(get_rbac_service),
    current_user: UserInfo = Depends(get_current_user)
):
    """Get current user's permissions"""
    return await get_user_permissions(current_user.id, db, rbac_service, current_user)