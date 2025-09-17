/**
 * Comprehensive example showing all RBAC features in action
 * This demonstrates how to use the RBAC system in a real application
 */

import React from 'react';
import {
  // Core components
  ProtectedComponent,
  AdminOnly,
  ManagerOnly,
  AuthenticatedOnly,
  ConditionalRender,
  ShowIfAny,
  ShowIfAll,
  HideIf,

  // Permission-aware UI
  PermissionAwareButton,
  CreateButton,
  EditButton,
  DeleteButton,
  AdminButton,
  PermissionAwareForm,
  PermissionAwareInput,

  // Routing
  ProtectedRoute,
  AdminRoute,
  ManagerRoute,

  // Hooks
  usePermissions,
  useAccessControl,

  // Decorators
  withAccessControl,
  createProtected,
  commonDecorators,
} from '@dotmac/providers';

// Example 1: Dashboard with role-based sections
function AdminDashboard() {
  const { hasPermission, hasRole, getUserPermissions } = usePermissions();

  return (
    <div className='dashboard'>
      <h1>Admin Dashboard</h1>

      {/* Everyone authenticated sees this */}
      <AuthenticatedOnly>
        <section className='overview'>
          <h2>System Overview</h2>
          <MetricsCards />
        </section>
      </AuthenticatedOnly>

      {/* Only managers and admins see this */}
      <ManagerOnly>
        <section className='management'>
          <h2>Management Tools</h2>
          <TeamMetrics />
          <UserActivityLog />
        </section>
      </ManagerOnly>

      {/* Admin-only section */}
      <AdminOnly fallback={<div>Admin access required</div>}>
        <section className='admin'>
          <h2>System Administration</h2>
          <SystemSettings />
          <AuditLogs />
        </section>
      </AdminOnly>

      {/* Conditional sections based on specific permissions */}
      <ShowIfAny permissions={['billing:read', 'billing:admin']}>
        <section className='billing'>
          <h2>Billing Overview</h2>
          <BillingMetrics />
        </section>
      </ShowIfAny>

      <ShowIfAll permissions={['users:admin', 'system:config']}>
        <section className='advanced'>
          <h2>Advanced Configuration</h2>
          <AdvancedSettings />
        </section>
      </ShowIfAll>

      {/* Hide sensitive info from certain roles */}
      <HideIf roles='readonly'>
        <section className='sensitive'>
          <h2>Sensitive Operations</h2>
          <DatabaseMaintenance />
        </section>
      </HideIf>

      {/* Debug info for development */}
      {process.env.NODE_ENV === 'development' && (
        <details className='debug'>
          <summary>Debug Info</summary>
          <pre>
            Has admin role: {hasRole('admin').toString()}
            Has user:create permission: {hasPermission('users:create').toString()}
            All permissions: {JSON.stringify(getUserPermissions(), null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}

// Example 2: User management with comprehensive RBAC
function UserManagement() {
  const { checkAccess } = useAccessControl();
  const [users, setUsers] = React.useState([]);

  const canCreateUser = checkAccess('users:create');
  const canDeleteUser = checkAccess('users:delete');
  const canUpdateUserRole = checkAccess('users:admin');

  return (
    <div className='user-management'>
      <div className='header'>
        <h1>User Management</h1>

        {/* Create button - only shown if user has permission */}
        <CreateButton resource='users' onClick={() => openCreateUserModal()} hideIfNoAccess={true}>
          Create User
        </CreateButton>
      </div>

      {/* User list - protected by read permission */}
      <ProtectedComponent
        permissions='users:read'
        fallback={<div>You don't have permission to view users</div>}
      >
        <UserList users={users} />
      </ProtectedComponent>

      {/* Bulk actions - only for admins */}
      <AdminOnly>
        <div className='bulk-actions'>
          <AdminButton onClick={() => bulkDeleteUsers()}>Bulk Delete</AdminButton>
          <AdminButton onClick={() => exportUsers()}>Export Users</AdminButton>
        </div>
      </AdminOnly>
    </div>
  );
}

// Example 3: Complex form with field-level permissions
function UserEditForm({ user, onSave, onDelete }) {
  const [formData, setFormData] = React.useState(user);

  return (
    <PermissionAwareForm
      permissions='users:update'
      readOnlyIfNoAccess={true}
      onSubmit={(e) => {
        e.preventDefault();
        onSave(formData);
      }}
      className='user-form'
    >
      <div className='form-group'>
        <label>Email</label>
        <PermissionAwareInput
          type='email'
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          permissions='users:update'
          placeholder='user@example.com'
        />
      </div>

      <div className='form-group'>
        <label>Name</label>
        <PermissionAwareInput
          type='text'
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          permissions='users:update'
          placeholder='Full name'
        />
      </div>

      <div className='form-group'>
        <label>Role (Admin only)</label>
        <PermissionAwareInput
          type='text'
          value={formData.role}
          onChange={(e) => setFormData({ ...formData, role: e.target.value })}
          permissions='users:admin' // Only admins can change roles
          placeholder='User role'
        />
      </div>

      <div className='form-actions'>
        <EditButton resource='users' type='submit' disableIfNoAccess={true}>
          Save Changes
        </EditButton>

        <DeleteButton resource='users' onClick={() => onDelete(user.id)} hideIfNoAccess={true}>
          Delete User
        </DeleteButton>
      </div>
    </PermissionAwareForm>
  );
}

// Example 4: Using HOCs and decorators
const ProtectedUserList = withAccessControl(UserList, {
  permissions: 'users:read',
  fallback: () => <div>Access denied to user list</div>,
  onAccessDenied: () => console.log('User tried to access user list without permission'),
});

// Using resource-based decorators
const UserComponents = commonDecorators.users;
const ReadOnlyUserList = UserComponents.read(UserList);
const AdminUserList = UserComponents.admin(UserList);

// Custom protected components using createProtected
const CustomProtectedComponents = createProtected(UserList);
const ManagerUserList = CustomProtectedComponents.withRoles(['admin', 'manager']);

// Example 5: Advanced routing with route guards
function AppRoutes() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path='/' element={<HomePage />} />
      <Route path='/login' element={<LoginPage />} />

      {/* Protected routes */}
      <Route path='/dashboard' element={<ProtectedRoute component={Dashboard} />} />

      {/* Admin-only routes */}
      <Route
        path='/admin/*'
        element={
          <AdminRoute>
            <AdminRoutes />
          </AdminRoute>
        }
      />

      {/* Permission-based routes */}
      <Route
        path='/users'
        element={
          <ProtectedRoute
            permissions='users:read'
            component={UserManagement}
            redirect='/unauthorized'
            fallback={<AccessDeniedPage />}
          />
        }
      />

      <Route
        path='/billing'
        element={
          <ProtectedRoute
            permissions={['billing:read', 'billing:admin']}
            requireAll={false} // User needs ANY of these permissions
            component={BillingDashboard}
          />
        }
      />

      {/* Manager-level routes */}
      <Route path='/reports' element={<ManagerRoute component={ReportsPage} />} />

      {/* Complex permission requirements */}
      <Route
        path='/system'
        element={
          <ProtectedRoute
            permissions='system:admin'
            roles='admin'
            requireAll={true} // Must have BOTH permission AND role
            component={SystemAdministration}
          />
        }
      />
    </Routes>
  );
}

// Example 6: Custom access control logic
function CustomAccessControlExample() {
  const { evaluateRule } = useAccessControl();

  // Complex access rule
  const complexRule = {
    checks: [
      { type: 'permission', value: ['billing:read', 'billing:admin'], operator: 'OR' },
      { type: 'role', value: 'manager', operator: 'AND' },
    ],
    operator: 'AND', // Must satisfy both permission check AND role check
  };

  const hasComplexAccess = evaluateRule(complexRule);

  return (
    <ConditionalRender show={hasComplexAccess}>
      <div>
        <h3>Complex Access Control</h3>
        <p>This content is shown only if user has billing permissions AND is a manager</p>
      </div>
    </ConditionalRender>
  );
}

// Example 7: Portal-specific components
function PortalSpecificExample() {
  return (
    <div>
      {/* Different content for different portals */}
      <ProtectedComponent permissions='admin:dashboard'>
        <AdminDashboardWidget />
      </ProtectedComponent>

      <ProtectedComponent permissions='customer:profile'>
        <CustomerProfileWidget />
      </ProtectedComponent>

      <ProtectedComponent permissions='reseller:customers'>
        <ResellerCustomersWidget />
      </ProtectedComponent>

      <ProtectedComponent permissions='technician:field_ops'>
        <TechnicianToolsWidget />
      </ProtectedComponent>
    </div>
  );
}

// Mock components for the examples
const MetricsCards = () => <div>Metrics Cards</div>;
const TeamMetrics = () => <div>Team Metrics</div>;
const UserActivityLog = () => <div>User Activity Log</div>;
const SystemSettings = () => <div>System Settings</div>;
const AuditLogs = () => <div>Audit Logs</div>;
const BillingMetrics = () => <div>Billing Metrics</div>;
const AdvancedSettings = () => <div>Advanced Settings</div>;
const DatabaseMaintenance = () => <div>Database Maintenance</div>;
const UserList = ({ users }) => <div>User List: {users?.length || 0} users</div>;
const HomePage = () => <div>Home Page</div>;
const LoginPage = () => <div>Login Page</div>;
const Dashboard = () => <div>Dashboard</div>;
const AdminRoutes = () => <div>Admin Routes</div>;
const AccessDeniedPage = () => <div>Access Denied</div>;
const BillingDashboard = () => <div>Billing Dashboard</div>;
const ReportsPage = () => <div>Reports</div>;
const SystemAdministration = () => <div>System Administration</div>;
const AdminDashboardWidget = () => <div>Admin Dashboard Widget</div>;
const CustomerProfileWidget = () => <div>Customer Profile Widget</div>;
const ResellerCustomersWidget = () => <div>Reseller Customers Widget</div>;
const TechnicianToolsWidget = () => <div>Technician Tools Widget</div>;

// Mock functions
const openCreateUserModal = () => console.log('Opening create user modal');
const bulkDeleteUsers = () => console.log('Bulk deleting users');
const exportUsers = () => console.log('Exporting users');
