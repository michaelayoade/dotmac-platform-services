import type { Meta, StoryObj } from '@storybook/react';
import { useAccessControl } from '../hooks/useAccessControl';
import { AccessControlProvider } from '../providers/AccessControlProvider';
import { useState } from 'react';

const meta: Meta = {
  title: 'RBAC/useAccessControl Hook',
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component:
          'Hook providing access control utilities including permission/role checking and access enforcement.',
      },
    },
  },
};

export default meta;

const AccessControlDemo = () => {
  const { checkAccess, hasPermission, hasRole, userPermissions, userRoles } = useAccessControl();

  const [testPermission, setTestPermission] = useState('users:read');
  const [testRole, setTestRole] = useState('admin');
  const [testPermissions, setTestPermissions] = useState(['users:read', 'billing:write']);
  const [requireAll, setRequireAll] = useState(false);

  const permissionTests = [
    { permission: 'users:read', label: 'Read Users' },
    { permission: 'users:write', label: 'Write Users' },
    { permission: 'billing:read', label: 'Read Billing' },
    { permission: 'billing:write', label: 'Write Billing' },
    { permission: 'admin:access', label: 'Admin Access' },
  ];

  const roleTests = [
    { role: 'admin', label: 'Administrator' },
    { role: 'manager', label: 'Manager' },
    { role: 'user', label: 'Regular User' },
    { role: 'readonly', label: 'Read Only' },
  ];

  return (
    <div className='max-w-4xl mx-auto p-6 space-y-6'>
      <h2 className='text-2xl font-bold'>useAccessControl Hook Demo</h2>

      {/* Current User Context */}
      <div className='bg-gray-50 p-4 rounded-lg'>
        <h3 className='font-semibold mb-2'>Current User Context</h3>
        <div className='grid md:grid-cols-2 gap-4 text-sm'>
          <div>
            <strong>Permissions:</strong>
            <ul className='mt-1 list-disc list-inside'>
              {userPermissions.map((permission) => (
                <li key={permission} className='text-green-700'>
                  {permission}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <strong>Roles:</strong>
            <ul className='mt-1 list-disc list-inside'>
              {userRoles.map((role) => (
                <li key={role} className='text-blue-700'>
                  {role}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Individual Permission Tests */}
      <div className='bg-white border border-gray-200 p-4 rounded-lg'>
        <h3 className='font-semibold mb-3'>Individual Permission Tests</h3>
        <div className='grid md:grid-cols-3 gap-2'>
          {permissionTests.map(({ permission, label }) => {
            const hasAccess = hasPermission(permission);
            return (
              <div
                key={permission}
                className={`p-3 rounded text-sm ${
                  hasAccess
                    ? 'bg-green-100 text-green-800 border border-green-200'
                    : 'bg-red-100 text-red-800 border border-red-200'
                }`}
              >
                <div className='flex items-center justify-between'>
                  <span>{label}</span>
                  <span>{hasAccess ? '✅' : '❌'}</span>
                </div>
                <div className='text-xs opacity-70 mt-1'>{permission}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Role Tests */}
      <div className='bg-white border border-gray-200 p-4 rounded-lg'>
        <h3 className='font-semibold mb-3'>Role Tests</h3>
        <div className='grid md:grid-cols-2 gap-2'>
          {roleTests.map(({ role, label }) => {
            const hasRoleAccess = hasRole(role);
            return (
              <div
                key={role}
                className={`p-3 rounded text-sm ${
                  hasRoleAccess
                    ? 'bg-blue-100 text-blue-800 border border-blue-200'
                    : 'bg-gray-100 text-gray-600 border border-gray-200'
                }`}
              >
                <div className='flex items-center justify-between'>
                  <span>{label}</span>
                  <span>{hasRoleAccess ? '✅' : '❌'}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Interactive Tests */}
      <div className='grid md:grid-cols-2 gap-4'>
        {/* Single Permission Test */}
        <div className='bg-white border border-gray-200 p-4 rounded-lg'>
          <h3 className='font-semibold mb-3'>Test Single Permission</h3>
          <div className='space-y-3'>
            <input
              type='text'
              value={testPermission}
              onChange={(e) => setTestPermission(e.target.value)}
              placeholder='e.g., users:read'
              className='w-full px-3 py-2 border border-gray-300 rounded'
            />
            <div
              className={`p-3 rounded text-sm ${
                hasPermission(testPermission)
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              }`}
            >
              Result: {hasPermission(testPermission) ? 'GRANTED' : 'DENIED'}
            </div>
          </div>
        </div>

        {/* Single Role Test */}
        <div className='bg-white border border-gray-200 p-4 rounded-lg'>
          <h3 className='font-semibold mb-3'>Test Single Role</h3>
          <div className='space-y-3'>
            <input
              type='text'
              value={testRole}
              onChange={(e) => setTestRole(e.target.value)}
              placeholder='e.g., admin'
              className='w-full px-3 py-2 border border-gray-300 rounded'
            />
            <div
              className={`p-3 rounded text-sm ${
                hasRole(testRole) ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-600'
              }`}
            >
              Result: {hasRole(testRole) ? 'HAS ROLE' : 'NO ROLE'}
            </div>
          </div>
        </div>
      </div>

      {/* Combined Access Test */}
      <div className='bg-white border border-gray-200 p-4 rounded-lg'>
        <h3 className='font-semibold mb-3'>Test Combined Access</h3>
        <div className='space-y-3'>
          <div>
            <label className='block text-sm font-medium mb-1'>
              Test Permissions (comma-separated):
            </label>
            <input
              type='text'
              value={testPermissions.join(', ')}
              onChange={(e) =>
                setTestPermissions(
                  e.target.value
                    .split(',')
                    .map((p) => p.trim())
                    .filter(Boolean)
                )
              }
              placeholder='e.g., users:read, billing:write'
              className='w-full px-3 py-2 border border-gray-300 rounded'
            />
          </div>
          <div className='flex items-center space-x-2'>
            <input
              type='checkbox'
              id='requireAll'
              checked={requireAll}
              onChange={(e) => setRequireAll(e.target.checked)}
              className='rounded'
            />
            <label htmlFor='requireAll' className='text-sm'>
              Require all permissions (vs any)
            </label>
          </div>
          <div
            className={`p-3 rounded text-sm ${
              checkAccess(testPermissions, undefined, requireAll)
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            }`}
          >
            <div>
              <strong>Result:</strong>{' '}
              {checkAccess(testPermissions, undefined, requireAll)
                ? 'ACCESS GRANTED'
                : 'ACCESS DENIED'}
            </div>
            <div className='text-xs mt-1 opacity-75'>
              Testing: {testPermissions.join(', ')} (
              {requireAll ? 'ALL required' : 'ANY sufficient'})
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

type Story = StoryObj;

export const AdminUser: Story = {
  render: () => (
    <AccessControlProvider
      userPermissions={[
        'users:read',
        'users:write',
        'billing:read',
        'billing:write',
        'admin:access',
      ]}
      userRoles={['admin', 'manager']}
    >
      <AccessControlDemo />
    </AccessControlProvider>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Administrator with full permissions and roles. Can access most features.',
      },
    },
  },
};

export const BillingManager: Story = {
  render: () => (
    <AccessControlProvider
      userPermissions={['billing:read', 'billing:write', 'users:read']}
      userRoles={['manager', 'user']}
    >
      <AccessControlDemo />
    </AccessControlProvider>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Billing manager with limited permissions focused on billing operations.',
      },
    },
  },
};

export const RegularUser: Story = {
  render: () => (
    <AccessControlProvider userPermissions={['profile:read', 'profile:write']} userRoles={['user']}>
      <AccessControlDemo />
    </AccessControlProvider>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Regular user with minimal permissions, can only manage own profile.',
      },
    },
  },
};

export const ReadOnlyUser: Story = {
  render: () => (
    <AccessControlProvider
      userPermissions={['users:read', 'billing:read']}
      userRoles={['readonly']}
    >
      <AccessControlDemo />
    </AccessControlProvider>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Read-only user who can view but not modify most resources.',
      },
    },
  },
};
