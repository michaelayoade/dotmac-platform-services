import React from 'react';
import { useAuth } from '@dotmac/auth';
import { useAccessControl } from '../hooks/useAccessControl';

interface RouteGuardConfig {
  permissions?: string | string[];
  roles?: string | string[];
  requireAll?: boolean;
  redirectTo?: string;
  fallback?: React.ComponentType<any>;
}

/**
 * Route guard system for protecting multiple routes with configuration
 */
export class RouteGuardManager {
  private guards: Map<string, RouteGuardConfig> = new Map();

  /**
   * Register a route guard configuration
   */
  registerGuard(routePath: string, config: RouteGuardConfig) {
    this.guards.set(routePath, config);
  }

  /**
   * Get guard configuration for a route
   */
  getGuard(routePath: string): RouteGuardConfig | undefined {
    return this.guards.get(routePath);
  }

  /**
   * Check if a route path matches any registered guards
   */
  findMatchingGuard(currentPath: string): RouteGuardConfig | undefined {
    for (const [guardPath, config] of this.guards.entries()) {
      if (this.matchesPath(currentPath, guardPath)) {
        return config;
      }
    }
    return undefined;
  }

  private matchesPath(currentPath: string, guardPath: string): boolean {
    // Simple path matching - could be enhanced with wildcards
    if (guardPath.includes('*')) {
      const pattern = guardPath.replace('*', '.*');
      const regex = new RegExp(`^${pattern}$`);
      return regex.test(currentPath);
    }
    return currentPath === guardPath || currentPath.startsWith(guardPath);
  }
}

// Global instance
export const routeGuardManager = new RouteGuardManager();

/**
 * Hook to register route guards declaratively
 */
export function useRouteGuard(routePath: string, config: RouteGuardConfig) {
  React.useEffect(() => {
    routeGuardManager.registerGuard(routePath, config);
  }, [routePath, config]);
}

/**
 * Component that applies route guards based on current location
 * Should be placed at the app root level
 */
export function RouteGuardProvider({
  children,
  getCurrentPath,
}: {
  children: React.ReactNode;
  getCurrentPath: () => string;
}) {
  const { isAuthenticated, isLoading } = useAuth();
  const { checkAccess } = useAccessControl();

  const currentPath = getCurrentPath();
  const guard = routeGuardManager.findMatchingGuard(currentPath);

  if (isLoading) {
    return (
      <div className='flex items-center justify-center min-h-screen'>
        <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600'></div>
      </div>
    );
  }

  // No guard found, allow access
  if (!guard) {
    return <>{children}</>;
  }

  // Check authentication
  if (!isAuthenticated) {
    if (typeof window !== 'undefined' && guard.redirectTo) {
      window.location.href = guard.redirectTo;
    }
    return null;
  }

  // Check permissions/roles
  const hasAccess = checkAccess(guard.permissions, guard.roles, guard.requireAll);

  if (!hasAccess) {
    if (guard.fallback) {
      const FallbackComponent = guard.fallback;
      return <FallbackComponent />;
    }

    return (
      <div className='flex items-center justify-center min-h-screen'>
        <div className='text-center'>
          <h1 className='text-4xl font-bold text-gray-800 mb-4'>403</h1>
          <h2 className='text-xl text-gray-600 mb-4'>Access Denied</h2>
          <p className='text-gray-500'>You don't have permission to access this page.</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

/**
 * Utility functions for common route guard configurations
 */
export const routeGuards = {
  admin: (redirectTo = '/login'): RouteGuardConfig => ({
    roles: 'admin',
    redirectTo,
  }),

  manager: (redirectTo = '/login'): RouteGuardConfig => ({
    roles: ['admin', 'manager'],
    redirectTo,
  }),

  authenticated: (redirectTo = '/login'): RouteGuardConfig => ({
    redirectTo,
  }),

  permission: (permission: string | string[], redirectTo = '/login'): RouteGuardConfig => ({
    permissions: permission,
    redirectTo,
  }),

  role: (role: string | string[], redirectTo = '/login'): RouteGuardConfig => ({
    roles: role,
    redirectTo,
  }),
};
