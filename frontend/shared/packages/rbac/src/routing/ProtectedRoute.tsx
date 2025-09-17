import React from 'react';
import { useAuth } from '@dotmac/auth';
import { useAccessControl } from '../hooks/useAccessControl';
import type { RouteGuardProps } from '../types';

/**
 * Route component that protects access based on permissions/roles
 * Can be used with React Router or any routing system
 *
 * @example
 * <ProtectedRoute
 *   permissions="admin:users"
 *   component={AdminUsersPage}
 *   redirect="/unauthorized"
 * />
 */
export function ProtectedRoute({
  children,
  component: Component,
  element,
  permissions,
  roles,
  requireAll = false,
  redirect = '/login',
  fallback,
  onAccessDenied,
}: RouteGuardProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const { checkAccess } = useAccessControl();

  // Show loading state while auth is being determined
  if (isLoading) {
    return (
      <div className='flex items-center justify-center min-h-screen'>
        <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600'></div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    if (typeof window !== 'undefined') {
      window.location.href = redirect;
    }
    return null;
  }

  // Check permissions/roles
  const hasAccess = checkAccess(permissions, roles, requireAll);

  if (!hasAccess) {
    onAccessDenied?.();

    if (fallback) {
      return <>{fallback}</>;
    }

    // Default unauthorized component
    return (
      <div className='flex items-center justify-center min-h-screen'>
        <div className='text-center'>
          <h1 className='text-4xl font-bold text-gray-800 mb-4'>403</h1>
          <h2 className='text-xl text-gray-600 mb-4'>Access Denied</h2>
          <p className='text-gray-500 mb-6'>You don't have permission to access this page.</p>
          <button
            onClick={() => window.history.back()}
            className='bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded'
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  // Render the protected content
  if (Component) {
    return <Component />;
  }

  if (element) {
    return element;
  }

  return <>{children}</>;
}

/**
 * Higher-order component for protecting routes
 */
export function withRouteProtection({
  permissions,
  roles,
  requireAll = false,
  redirect = '/login',
  fallback,
}: Omit<RouteGuardProps, 'children' | 'component' | 'element'>) {
  return function ProtectedRouteWrapper<P extends object>(Component: React.ComponentType<P>) {
    return function ProtectedComponent(props: P) {
      return (
        <ProtectedRoute
          permissions={permissions}
          roles={roles}
          requireAll={requireAll}
          redirect={redirect}
          fallback={fallback}
        >
          <Component {...props} />
        </ProtectedRoute>
      );
    };
  };
}

/**
 * Convenience components for common route protection patterns
 */
export const AdminRoute = ({ children, ...props }: Omit<RouteGuardProps, 'roles'>) => (
  <ProtectedRoute roles='admin' {...props}>
    {children}
  </ProtectedRoute>
);

export const ManagerRoute = ({ children, ...props }: Omit<RouteGuardProps, 'roles'>) => (
  <ProtectedRoute roles={['admin', 'manager']} {...props}>
    {children}
  </ProtectedRoute>
);

export const AuthenticatedRoute = ({
  children,
  ...props
}: Omit<RouteGuardProps, 'permissions' | 'roles'>) => (
  <ProtectedRoute {...props}>{children}</ProtectedRoute>
);
