import type { Meta, StoryObj } from '@storybook/react';
import { ProtectedComponent } from './ProtectedComponent';
import { AccessControlProvider } from '../providers/AccessControlProvider';

const meta: Meta<typeof ProtectedComponent> = {
  title: 'RBAC/ProtectedComponent',
  component: ProtectedComponent,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component:
          'Component that conditionally renders children based on user permissions and roles. Supports fine-grained access control with fallback options.',
      },
    },
  },
  argTypes: {
    permissions: {
      control: 'object',
      description: 'Array of required permissions (format: resource:action)',
    },
    roles: {
      control: 'object',
      description: 'Array of required roles',
    },
    requireAll: {
      control: 'boolean',
      description: 'Whether all permissions/roles are required (true) or any (false)',
    },
    fallback: {
      control: 'text',
      description: 'Content to show when access is denied',
    },
  },
  decorators: [
    (Story, context) => (
      <AccessControlProvider
        userPermissions={context.globals.userPermissions || ['users:read', 'billing:read']}
        userRoles={context.globals.userRoles || ['admin']}
      >
        <div className='p-4 space-y-4'>
          <div className='bg-blue-50 p-3 rounded'>
            <strong>Current User Context:</strong>
            <br />
            Permissions:{' '}
            {(context.globals.userPermissions || ['users:read', 'billing:read']).join(', ')}
            <br />
            Roles: {(context.globals.userRoles || ['admin']).join(', ')}
          </div>
          <Story />
        </div>
      </AccessControlProvider>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof ProtectedComponent>;

const ProtectedContent = () => (
  <div className='bg-green-100 border border-green-400 p-4 rounded'>
    <h3 className='text-green-800 font-semibold'>🔓 Protected Content Visible</h3>
    <p className='text-green-700'>This content is only visible when access requirements are met.</p>
  </div>
);

export const WithPermission: Story = {
  args: {
    permissions: ['users:read'],
    children: <ProtectedContent />,
  },
  parameters: {
    docs: {
      description: {
        story:
          'Component protected by a single permission. Content shows when user has "users:read" permission.',
      },
    },
  },
};

export const WithMultiplePermissions: Story = {
  args: {
    permissions: ['users:read', 'users:write'],
    requireAll: false,
    children: <ProtectedContent />,
  },
  parameters: {
    docs: {
      description: {
        story:
          'Component requiring ANY of multiple permissions. Content shows when user has at least one permission.',
      },
    },
  },
};

export const WithAllPermissionsRequired: Story = {
  args: {
    permissions: ['users:read', 'users:write'],
    requireAll: true,
    children: <ProtectedContent />,
  },
  parameters: {
    docs: {
      description: {
        story:
          'Component requiring ALL permissions. Content only shows when user has both permissions.',
      },
    },
  },
};

export const WithRole: Story = {
  args: {
    roles: ['admin'],
    children: <ProtectedContent />,
  },
  parameters: {
    docs: {
      description: {
        story: 'Component protected by role. Content shows for admin users only.',
      },
    },
  },
};

export const WithFallback: Story = {
  args: {
    permissions: ['super-admin:access'],
    fallback: (
      <div className='bg-red-100 border border-red-400 p-4 rounded'>
        <h3 className='text-red-800 font-semibold'>🔒 Access Denied</h3>
        <p className='text-red-700'>You don't have permission to view this content.</p>
      </div>
    ),
    children: <ProtectedContent />,
  },
  parameters: {
    docs: {
      description: {
        story: 'Component with custom fallback content when access is denied.',
      },
    },
  },
};

export const AccessDeniedCallback: Story = {
  args: {
    permissions: ['restricted:access'],
    onAccessDenied: () => alert('Access denied! This action has been logged.'),
    fallback: (
      <div className='bg-yellow-100 border border-yellow-400 p-4 rounded'>
        <h3 className='text-yellow-800 font-semibold'>⚠️ Restricted Area</h3>
        <p className='text-yellow-700'>
          Access attempt will trigger callback (check browser alert).
        </p>
      </div>
    ),
    children: <ProtectedContent />,
  },
  parameters: {
    docs: {
      description: {
        story: 'Component with access denied callback for logging or notifications.',
      },
    },
  },
};
