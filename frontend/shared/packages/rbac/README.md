# @dotmac/rbac - Universal Role-Based Access Control

A comprehensive RBAC system for DotMac Framework that leverages the existing authentication system to provide fine-grained access control across all portals.

## Features

- ✅ **Universal RBAC components** - Protect any UI element with permissions/roles
- ✅ **Permission-aware UI components** - Buttons, forms, and inputs that automatically handle access control
- ✅ **Role-based routing** - Protect routes based on permissions or roles
- ✅ **Access control decorators** - Higher-order components and decorators for component protection
- ✅ **Portal-specific configurations** - Different permission sets for each portal type
- ✅ **Seamless integration** - Works with existing @dotmac/auth and @dotmac/providers

## Quick Start

### Basic Usage

```tsx
import { ProtectedComponent, usePermissions, PermissionAwareButton } from '@dotmac/providers';

function UserManagement() {
  const { hasPermission } = usePermissions();

  return (
    <div>
      <h1>User Management</h1>

      {/* Show content only if user has permission */}
      <ProtectedComponent permissions='users:read'>
        <UserList />
      </ProtectedComponent>

      {/* Button that's disabled without permission */}
      <PermissionAwareButton permissions='users:create' onClick={createUser}>
        Create User
      </PermissionAwareButton>

      {/* Conditional rendering */}
      {hasPermission('users:delete') && <DeleteUsersButton />}
    </div>
  );
}
```

### Route Protection

```tsx
import { ProtectedRoute, AdminRoute } from '@dotmac/providers';

function App() {
  return (
    <Router>
      <Routes>
        {/* Admin-only route */}
        <Route path='/admin' element={<AdminRoute component={AdminDashboard} />} />

        {/* Permission-based route */}
        <Route
          path='/users'
          element={
            <ProtectedRoute
              permissions={['users:read', 'users:create']}
              requireAll={false}
              component={UserManagement}
              redirect='/unauthorized'
            />
          }
        />
      </Routes>
    </Router>
  );
}
```

### Higher-Order Components

```tsx
import { withAccessControl, createProtected } from '@dotmac/providers';

// Using HOC decorator
const ProtectedUserList = withAccessControl(UserList, {
  permissions: 'users:read',
  fallback: () => <div>Access denied</div>,
});

// Using component factory
const UserComponents = createProtected(UserList);
const AdminUserList = UserComponents.adminOnly();
const ManagerUserList = UserComponents.withRoles(['admin', 'manager']);
```

## API Reference

### Components

#### ProtectedComponent

Protects any UI element based on permissions or roles.

```tsx
<ProtectedComponent
  permissions={string | string[]}
  roles={string | string[]}
  requireAll={boolean}
  fallback={ReactNode}
  onAccessDenied={() => void}
>
  {children}
</ProtectedComponent>
```

#### Permission-Aware UI Components

- `PermissionAwareButton` - Button with permission-based disable/hide
- `PermissionAwareForm` - Form with read-only states
- `PermissionAwareInput` - Input with permission-based read-only
- `CreateButton`, `EditButton`, `DeleteButton` - Pre-configured action buttons

#### Routing Components

- `ProtectedRoute` - Route protection with redirects
- `AdminRoute`, `ManagerRoute` - Role-specific route shortcuts
- `RouteGuardProvider` - App-level route guard system

### Hooks

#### usePermissions()

```tsx
const {
  hasPermission,
  hasRole,
  hasAnyPermission,
  hasAllPermissions,
  getUserPermissions,
  getUserRoles,
} = usePermissions();
```

#### useAccessControl()

```tsx
const { checkAccess, checkPermissions, checkRoles, evaluateRule } = useAccessControl();
```

### Decorators

#### withAccessControl()

```tsx
const ProtectedComponent = withAccessControl(Component, {
  permissions: 'users:read',
  roles: 'admin',
  requireAll: false,
  fallback: ErrorComponent,
  onAccessDenied: () => console.log('Access denied'),
});
```

#### Resource-based decorators

```tsx
import { commonDecorators } from '@dotmac/rbac';

const UserComponents = commonDecorators.users;
const ReadOnlyUserList = UserComponents.read(UserList);
const AdminUserList = UserComponents.admin(UserList);
```

## Permission System

### Portal-Specific Permissions

Each portal has its own permission structure:

**Admin Portal:**

- `users:*` - Full user management
- `billing:*` - Full billing access
- `network:*` - Network management
- `system:*` - System administration

**Customer Portal:**

- `profile:*` - Profile management
- `billing:read` - View billing info
- `tickets:*` - Support tickets

**Reseller Portal:**

- `customers:*` - Customer management
- `commissions:read` - View commissions
- `reports:*` - Generate reports

**Technician Portal:**

- `network:read,update` - Network operations
- `tickets:*` - Field support tickets
- `field_ops:*` - Field operations

**Management Portal:**

- `*` - Full system access (admin)
- `tenants:*` - Tenant management
- `analytics:*` - System analytics

### Role Hierarchy

1. **Admin** - Full access to portal resources
2. **Manager** - Management-level access with some restrictions
3. **User** - Standard user access
4. **Readonly** - View-only access

### Permission Format

Permissions follow the pattern: `resource:action`

- `users:read` - Read user data
- `users:create` - Create new users
- `users:update` - Update user information
- `users:delete` - Delete users
- `users:*` - All user operations

## Integration with Existing System

The RBAC system seamlessly integrates with your existing auth setup:

```tsx
// In your app root
import { UniversalProviders } from '@dotmac/providers';

function App() {
  return (
    <UniversalProviders
      portal='admin'
      authVariant='secure'
      features={{
        notifications: true,
        rbac: true, // RBAC is automatically available
      }}
    >
      <YourApp />
    </UniversalProviders>
  );
}
```

## Examples

### Dashboard with Role-Based Sections

```tsx
import { ProtectedComponent, AdminOnly, ManagerOnly, ShowIfAny } from '@dotmac/providers';

function Dashboard() {
  return (
    <div>
      <h1>Dashboard</h1>

      {/* Everyone sees this */}
      <MetricsOverview />

      {/* Managers and admins see this */}
      <ManagerOnly>
        <TeamMetrics />
      </ManagerOnly>

      {/* Only admins see this */}
      <AdminOnly>
        <SystemMetrics />
      </AdminOnly>

      {/* Show if user has any billing permission */}
      <ShowIfAny permissions={['billing:read', 'billing:create']}>
        <BillingSection />
      </ShowIfAny>
    </div>
  );
}
```

### Complex Form with Field-Level Permissions

```tsx
import {
  PermissionAwareForm,
  PermissionAwareInput,
  PermissionAwareButton,
} from '@dotmac/providers';

function UserEditForm({ user }) {
  return (
    <PermissionAwareForm permissions='users:update'>
      <PermissionAwareInput
        name='email'
        value={user.email}
        permissions='users:update'
        placeholder='Email address'
      />

      <PermissionAwareInput
        name='role'
        value={user.role}
        permissions='users:admin' // Only admins can change roles
        placeholder='User role'
      />

      <PermissionAwareButton type='submit' permissions='users:update'>
        Save Changes
      </PermissionAwareButton>

      <PermissionAwareButton permissions='users:delete' onClick={deleteUser} className='danger'>
        Delete User
      </PermissionAwareButton>
    </PermissionAwareForm>
  );
}
```

This RBAC system provides comprehensive, type-safe access control that integrates seamlessly with your existing DotMac Framework setup.
