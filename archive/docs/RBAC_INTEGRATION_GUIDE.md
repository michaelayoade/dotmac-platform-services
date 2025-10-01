# RBAC Integration Guide

## Overview

This guide documents the complete Role-Based Access Control (RBAC) integration between the backend and frontend of the DotMac Platform Services application.

## Backend RBAC Implementation

### Database Schema
- **Tables**: `roles`, `permissions`, `role_permissions`, `user_roles`, `user_permissions`
- **Migration**: `alembic/versions/2025_01_27_add_rbac_tables.py`
- **Models**: `src/dotmac/platform/auth/models.py`

### Core Components

#### 1. RBAC Service (`auth/rbac_service.py`)
- Role hierarchy management
- Permission inheritance
- Caching for performance
- User permission calculation

#### 2. RBAC Router (`auth/rbac_router.py`)
**Endpoints:**
- `GET /auth/rbac/permissions` - List all permissions
- `GET /auth/rbac/permissions/{name}` - Get specific permission
- `GET /auth/rbac/roles` - List all roles
- `POST /auth/rbac/roles` - Create new role
- `PATCH /auth/rbac/roles/{name}` - Update role
- `DELETE /auth/rbac/roles/{name}` - Delete role
- `GET /auth/rbac/my-permissions` - Get current user permissions
- `GET /auth/rbac/users/{id}/permissions` - Get user permissions
- `POST /auth/rbac/users/assign-role` - Assign role to user
- `POST /auth/rbac/users/revoke-role` - Revoke role from user
- `POST /auth/rbac/users/grant-permission` - Grant direct permission

#### 3. RBAC Dependencies (`auth/rbac_dependencies.py`)
- `require_permission()` - Decorator for permission checks
- `require_any_permission()` - Check for any of multiple permissions
- `require_all_permissions()` - Check for all specified permissions

### Permission Categories
```python
class PermissionCategory(str, Enum):
    USERS = "users"
    BILLING = "billing"
    ANALYTICS = "analytics"
    COMMUNICATIONS = "communications"
    INFRASTRUCTURE = "infrastructure"
    SECRETS = "secrets"
    CUSTOMERS = "customers"
    SETTINGS = "settings"
    SYSTEM = "system"
```

## Frontend RBAC Integration

### Core Components

#### 1. RBAC Context (`contexts/RBACContext.tsx`)
Provides centralized permission management:
```typescript
const {
  permissions,     // Current user permissions
  hasPermission,   // Check single permission
  hasRole,         // Check if user has role
  canAccess,       // Check category access
  roles,           // All available roles
  createRole,      // Create new role
  assignRole,      // Assign role to user
} = useRBAC();
```

#### 2. Permission Guards (`components/auth/PermissionGuard.tsx`)

**Components:**
- `<PermissionGuard>` - Hide/show content based on permissions
- `<RouteGuard>` - Protect entire pages/routes
- `<Can>` / `<Cannot>` - Simple permission checks
- `<PermissionButton>` - Button with permission check
- `<PermissionMenuItem>` - Menu item with permission check

**Usage Examples:**
```tsx
// Guard a component
<PermissionGuard permission="users.create">
  <CreateUserButton />
</PermissionGuard>

// Guard a route
<RouteGuard category={PermissionCategory.BILLING}>
  <BillingPage />
</RouteGuard>

// Simple permission check
<Can I="settings.update">
  <EditSettingsButton />
</Can>

// Permission button
<PermissionButton
  permission="customers.delete"
  onClick={handleDelete}
>
  Delete Customer
</PermissionButton>
```

#### 3. Hooks
- `useRBAC()` - Access RBAC context
- `usePermission(permission)` - Check permission(s)
- `useRole(role)` - Check role
- `useCategoryAccess(category, action)` - Check category access
- `usePermissionVisibility(permission)` - Get visibility props

### Integration Steps

#### Step 1: Update Authentication Flow
```typescript
// In useAuth hook or auth provider
const login = async (credentials) => {
  const response = await apiClient.post('/auth/login', credentials);
  const { token, user } = response.data;

  // Store token
  localStorage.setItem('token', token);

  // Fetch user permissions
  const permissions = await apiClient.get('/auth/rbac/my-permissions');

  // Update context with user and permissions
  setUser({ ...user, permissions });
};
```

#### Step 2: Wrap App with RBAC Provider
```tsx
// In _app.tsx or root layout
import { RBACProvider } from '@/contexts/RBACContext';

function MyApp({ Component, pageProps }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RBACProvider>
          <Component {...pageProps} />
        </RBACProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
```

#### Step 3: Replace Mock Data
Replace mock role/permission data in pages with real API calls:

```tsx
// Before (mock data)
const mockRoles = [
  { name: 'admin', permissions: ['*'] },
  { name: 'user', permissions: ['read'] }
];

// After (real API)
import { useRBAC } from '@/contexts/RBACContext';

function RolesPage() {
  const { roles, createRole, updateRole, deleteRole } = useRBAC();

  // Use real roles from API
  return <RolesList roles={roles} />;
}
```

#### Step 4: Update Navigation Guards
Add permission checks to navigation items:

```tsx
// In sidebar or navigation
const navigationItems = [
  {
    label: 'Dashboard',
    href: '/dashboard',
    permission: null, // No permission required
  },
  {
    label: 'Users',
    href: '/dashboard/security-access/users',
    permission: 'users.read',
  },
  {
    label: 'Billing',
    href: '/dashboard/billing-revenue',
    permission: 'billing.read',
  },
  {
    label: 'Settings',
    href: '/dashboard/settings',
    permission: 'settings.read',
  },
];

// Render with permission check
{navigationItems.map(item => (
  <Can I={item.permission} key={item.href}>
    <NavLink href={item.href}>{item.label}</NavLink>
  </Can>
))}
```

#### Step 5: Update API Endpoints
Replace `require_admin` with granular permissions:

```python
# Before
@router.get("/users")
@require_admin
async def list_users():
    pass

# After
from dotmac.platform.auth.rbac_dependencies import require_permission

@router.get("/users")
async def list_users(
    user: User = Depends(require_permission("users.read"))
):
    pass
```

## Migration Checklist

### Backend Tasks
- [x] RBAC database schema and models
- [x] RBAC service implementation
- [x] RBAC API endpoints
- [x] Permission-based decorators
- [ ] Replace all `require_admin` with `require_permission`
- [ ] Seed initial roles and permissions
- [ ] Add permission checks to all endpoints

### Frontend Tasks
- [x] RBAC context provider
- [x] Permission guard components
- [x] Permission hooks
- [ ] Update authentication flow
- [ ] Replace mock data in role/permission pages
- [ ] Add permission guards to all routes
- [ ] Update navigation with permission checks
- [ ] Test all user flows with different roles

### Testing Tasks
- [ ] Unit tests for RBAC service
- [ ] Integration tests for RBAC endpoints
- [ ] Frontend permission guard tests
- [ ] End-to-end tests for different roles
- [ ] Permission inheritance tests
- [ ] Cache invalidation tests

## Default Roles and Permissions

### System Roles
```python
roles = [
    {
        "name": "superuser",
        "display_name": "Super Administrator",
        "permissions": ["*"],  # All permissions
    },
    {
        "name": "admin",
        "display_name": "Administrator",
        "permissions": [
            "users.*",
            "billing.*",
            "settings.*",
            "customers.*",
            "communications.*",
        ],
    },
    {
        "name": "manager",
        "display_name": "Manager",
        "permissions": [
            "users.read",
            "billing.read",
            "customers.*",
            "communications.*",
            "analytics.read",
        ],
    },
    {
        "name": "user",
        "display_name": "Regular User",
        "permissions": [
            "customers.read",
            "analytics.read",
            "communications.read",
        ],
    },
]
```

## Security Considerations

1. **Permission Caching**: Permissions are cached for performance but must be invalidated on changes
2. **Token Claims**: Include essential permissions in JWT for stateless validation
3. **Frontend Guards**: Always validate permissions on backend; frontend is for UX only
4. **Audit Logging**: Log all permission changes and role assignments
5. **Expiration**: Support time-limited role assignments
6. **Principle of Least Privilege**: Grant minimum necessary permissions

## Example Implementation

### Protected Page Component
```tsx
// pages/dashboard/admin/users.tsx
import { RouteGuard } from '@/components/auth/PermissionGuard';
import { PermissionCategory } from '@/contexts/RBACContext';

export default function UsersManagementPage() {
  return (
    <RouteGuard
      category={PermissionCategory.USERS}
      action={PermissionAction.MANAGE}
    >
      <div className="p-6">
        <h1>User Management</h1>
        {/* Page content */}
      </div>
    </RouteGuard>
  );
}
```

### Protected API Call
```typescript
// hooks/useUsers.ts
import { useRBAC } from '@/contexts/RBACContext';

export function useUsers() {
  const { hasPermission } = useRBAC();

  const deleteUser = async (userId: string) => {
    if (!hasPermission('users.delete')) {
      throw new Error('Permission denied');
    }

    return apiClient.delete(`/users/${userId}`);
  };

  return { deleteUser };
}
```

## Next Steps

1. **Complete Backend Migration**: Replace all `require_admin` decorators
2. **Seed Permissions**: Run `scripts/seed_rbac.py` to create initial roles
3. **Update Frontend Pages**: Replace mock data with real API calls
4. **Test Coverage**: Write comprehensive tests for all permission scenarios
5. **Documentation**: Update API docs with permission requirements
6. **Monitoring**: Add metrics for permission denials and usage patterns