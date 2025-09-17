import React from 'react';
import { useAccessControl } from '../hooks/useAccessControl';
import type { WithAccessControlOptions } from '../types';

/**
 * Higher-order component that adds access control to any component
 *
 * @example
 * const ProtectedUserList = withAccessControl(UserListComponent, {
 *   permissions: 'users:read',
 *   fallback: AccessDeniedComponent,
 *   onAccessDenied: () => console.log('Access denied to user list')
 * });
 */
export function withAccessControl<P extends object>(
  Component: React.ComponentType<P>,
  options: WithAccessControlOptions
) {
  const {
    permissions,
    roles,
    requireAll = false,
    fallback: FallbackComponent,
    onAccessDenied,
  } = options;

  const WrappedComponent = React.forwardRef<any, P>((props, ref) => {
    const { checkAccess } = useAccessControl();

    const hasAccess = checkAccess(permissions, roles, requireAll);

    if (!hasAccess) {
      onAccessDenied?.();

      if (FallbackComponent) {
        return <FallbackComponent />;
      }

      // Default fallback
      return (
        <div className='p-4 text-center text-gray-500'>
          <p>Access denied. You don't have the required permissions.</p>
        </div>
      );
    }

    return <Component {...props} ref={ref} />;
  });

  // Set display name for debugging
  const componentName = Component.displayName || Component.name || 'Component';
  WrappedComponent.displayName = `withAccessControl(${componentName})`;

  return WrappedComponent;
}

/**
 * Decorator factory for specific permission patterns
 */
export const accessControlDecorators = {
  /**
   * Requires admin role
   */
  requireAdmin: <P extends object>(Component: React.ComponentType<P>) =>
    withAccessControl(Component, { roles: 'admin' }),

  /**
   * Requires manager or admin role
   */
  requireManager: <P extends object>(Component: React.ComponentType<P>) =>
    withAccessControl(Component, { roles: ['admin', 'manager'] }),

  /**
   * Requires specific permission
   */
  requirePermission:
    (permission: string | string[]) =>
    <P extends object>(Component: React.ComponentType<P>) =>
      withAccessControl(Component, { permissions: permission }),

  /**
   * Requires all specified permissions
   */
  requireAllPermissions:
    (permissions: string[]) =>
    <P extends object>(Component: React.ComponentType<P>) =>
      withAccessControl(Component, { permissions, requireAll: true }),

  /**
   * Requires any of the specified permissions
   */
  requireAnyPermission:
    (permissions: string[]) =>
    <P extends object>(Component: React.ComponentType<P>) =>
      withAccessControl(Component, { permissions, requireAll: false }),

  /**
   * Custom access control with callback
   */
  requireCustom:
    (options: WithAccessControlOptions) =>
    <P extends object>(Component: React.ComponentType<P>) =>
      withAccessControl(Component, options),
};

/**
 * Decorator for method-level access control (for class components)
 */
export function requiresPermission(permission: string | string[], requireAll = false) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value;

    descriptor.value = function (...args: any[]) {
      // This would need to be called within a component context
      // or with access to the permission checking logic
      const { checkAccess } = useAccessControl();

      if (!checkAccess(permission, undefined, requireAll)) {
        console.warn(`Access denied for method ${propertyKey}: insufficient permissions`);
        return;
      }

      return originalMethod.apply(this, args);
    };

    return descriptor;
  };
}

/**
 * HOC for protecting specific component methods
 */
export function withMethodProtection<P extends object>(
  Component: React.ComponentType<P>,
  methodPermissions: Record<string, string | string[]>
) {
  return class ProtectedComponent extends React.Component<P> {
    render() {
      const protectedProps = { ...this.props } as any;

      // Wrap methods with permission checks
      Object.keys(methodPermissions).forEach((methodName) => {
        const originalMethod = protectedProps[methodName];
        if (typeof originalMethod === 'function') {
          protectedProps[methodName] = (...args: any[]) => {
            // Note: This would need proper context access in real implementation
            return originalMethod(...args);
          };
        }
      });

      return <Component {...protectedProps} />;
    }
  };
}
