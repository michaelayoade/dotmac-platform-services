import type { Meta, StoryObj } from '@storybook/react';
import { ProtectedRoute } from './ProtectedRoute';
import { AccessControlProvider } from '../providers/AccessControlProvider';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';

const meta: Meta<typeof ProtectedRoute> = {
  title: 'RBAC/ProtectedRoute',
  component: ProtectedRoute,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component:
          'Route component that enforces access control at the routing level. Redirects unauthorized users or shows fallback content.',
      },
    },
  },
};

export default meta;
type Story = StoryObj<typeof ProtectedRoute>;

// Demo components
const PublicPage = () => (
  <div className='p-6 bg-blue-50'>
    <h2 className='text-2xl font-bold text-blue-800 mb-4'>Public Page</h2>
    <p className='text-blue-700'>This page is accessible to everyone.</p>
  </div>
);

const AdminPage = () => (
  <div className='p-6 bg-green-50'>
    <h2 className='text-2xl font-bold text-green-800 mb-4'>Admin Dashboard</h2>
    <p className='text-green-700'>This page requires admin role or users:manage permission.</p>
  </div>
);

const BillingPage = () => (
  <div className='p-6 bg-purple-50'>
    <h2 className='text-2xl font-bold text-purple-800 mb-4'>Billing Management</h2>
    <p className='text-purple-700'>This page requires billing:read permission.</p>
  </div>
);

const UnauthorizedPage = () => (
  <div className='p-6 bg-red-50'>
    <h2 className='text-2xl font-bold text-red-800 mb-4'>Access Denied</h2>
    <p className='text-red-700'>You don't have permission to access the requested page.</p>
    <Link to='/' className='text-blue-600 hover:underline mt-4 inline-block'>
      ← Back to Home
    </Link>
  </div>
);

const Navigation = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Home' },
    { path: '/admin', label: 'Admin Dashboard' },
    { path: '/billing', label: 'Billing' },
  ];

  return (
    <nav className='bg-gray-800 text-white p-4'>
      <div className='flex space-x-4'>
        {navItems.map(({ path, label }) => (
          <Link
            key={path}
            to={path}
            className={`px-3 py-2 rounded ${
              location.pathname === path ? 'bg-gray-700' : 'hover:bg-gray-700'
            }`}
          >
            {label}
          </Link>
        ))}
      </div>
    </nav>
  );
};

const RouteDemo = ({
  userPermissions,
  userRoles,
}: {
  userPermissions: string[];
  userRoles: string[];
}) => (
  <Router>
    <AccessControlProvider userPermissions={userPermissions} userRoles={userRoles}>
      <div className='min-h-screen'>
        <div className='bg-blue-100 p-4 border-b'>
          <strong>Current User Context:</strong>
          <br />
          Permissions: {userPermissions.join(', ') || 'None'}
          <br />
          Roles: {userRoles.join(', ') || 'None'}
        </div>

        <Navigation />

        <Routes>
          <Route path='/' element={<PublicPage />} />

          <Route
            path='/admin'
            element={
              <ProtectedRoute
                permissions={['users:manage']}
                roles={['admin']}
                requireAll={false}
                fallback={<UnauthorizedPage />}
              >
                <AdminPage />
              </ProtectedRoute>
            }
          />

          <Route
            path='/billing'
            element={
              <ProtectedRoute permissions={['billing:read']} fallback={<UnauthorizedPage />}>
                <BillingPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </div>
    </AccessControlProvider>
  </Router>
);

export const AdminUser: Story = {
  render: () => (
    <RouteDemo
      userPermissions={['users:manage', 'billing:read', 'users:read']}
      userRoles={['admin']}
    />
  ),
  parameters: {
    docs: {
      description: {
        story: 'Admin user can access all routes. Navigate between pages to test access control.',
      },
    },
  },
};

export const BillingUser: Story = {
  render: () => <RouteDemo userPermissions={['billing:read']} userRoles={['user']} />,
  parameters: {
    docs: {
      description: {
        story: 'User with billing permissions can access billing page but not admin dashboard.',
      },
    },
  },
};

export const RegularUser: Story = {
  render: () => <RouteDemo userPermissions={['profile:read']} userRoles={['user']} />,
  parameters: {
    docs: {
      description: {
        story: 'Regular user can only access public pages. Protected routes show fallback content.',
      },
    },
  },
};

export const NoPermissions: Story = {
  render: () => <RouteDemo userPermissions={[]} userRoles={[]} />,
  parameters: {
    docs: {
      description: {
        story: 'User with no permissions can only access public content.',
      },
    },
  },
};
