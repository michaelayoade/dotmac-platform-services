import React from 'react';
import { ProtectedComponent } from '../components/ProtectedComponent';

/**
 * Functional decorator patterns for common permission scenarios
 */

/**
 * Create a permission-protected version of a component
 */
export function createProtected<P extends object>(Component: React.ComponentType<P>) {
  return {
    /**
     * Require specific permissions
     */
    withPermissions: (permissions: string | string[], requireAll = false) =>
      React.forwardRef<any, P>((props, ref) => (
        <ProtectedComponent permissions={permissions} requireAll={requireAll}>
          <Component {...props} ref={ref} />
        </ProtectedComponent>
      )),

    /**
     * Require specific roles
     */
    withRoles: (roles: string | string[], requireAll = false) =>
      React.forwardRef<any, P>((props, ref) => (
        <ProtectedComponent roles={roles} requireAll={requireAll}>
          <Component {...props} ref={ref} />
        </ProtectedComponent>
      )),

    /**
     * Admin only access
     */
    adminOnly: () =>
      React.forwardRef<any, P>((props, ref) => (
        <ProtectedComponent roles='admin'>
          <Component {...props} ref={ref} />
        </ProtectedComponent>
      )),

    /**
     * Manager or admin access
     */
    managerOnly: () =>
      React.forwardRef<any, P>((props, ref) => (
        <ProtectedComponent roles={['admin', 'manager']}>
          <Component {...props} ref={ref} />
        </ProtectedComponent>
      )),

    /**
     * Custom fallback component
     */
    withFallback: (FallbackComponent: React.ComponentType) =>
      React.forwardRef<any, P>((props, ref) => (
        <ProtectedComponent fallback={<FallbackComponent />}>
          <Component {...props} ref={ref} />
        </ProtectedComponent>
      )),
  };
}

/**
 * Resource-based permission decorators
 * Automatically creates CRUD permission checks based on resource name
 */
export function createResourceProtected<P extends object>(
  Component: React.ComponentType<P>,
  resourceName: string
) {
  const basePermission = resourceName.toLowerCase();

  return {
    /**
     * Require read permission for resource
     */
    readOnly: () =>
      React.forwardRef<any, P>((props, ref) => (
        <ProtectedComponent permissions={`${basePermission}:read`}>
          <Component {...props} ref={ref} />
        </ProtectedComponent>
      )),

    /**
     * Require create permission for resource
     */
    createOnly: () =>
      React.forwardRef<any, P>((props, ref) => (
        <ProtectedComponent permissions={`${basePermission}:create`}>
          <Component {...props} ref={ref} />
        </ProtectedComponent>
      )),

    /**
     * Require update permission for resource
     */
    updateOnly: () =>
      React.forwardRef<any, P>((props, ref) => (
        <ProtectedComponent permissions={`${basePermission}:update`}>
          <Component {...props} ref={ref} />
        </ProtectedComponent>
      )),

    /**
     * Require delete permission for resource
     */
    deleteOnly: () =>
      React.forwardRef<any, P>((props, ref) => (
        <ProtectedComponent permissions={`${basePermission}:delete`}>
          <Component {...props} ref={ref} />
        </ProtectedComponent>
      )),

    /**
     * Require all CRUD permissions for resource
     */
    fullAccess: () =>
      React.forwardRef<any, P>((props, ref) => (
        <ProtectedComponent
          permissions={[
            `${basePermission}:read`,
            `${basePermission}:create`,
            `${basePermission}:update`,
            `${basePermission}:delete`,
          ]}
          requireAll={true}
        >
          <Component {...props} ref={ref} />
        </ProtectedComponent>
      )),

    /**
     * Require any CRUD permission for resource
     */
    anyAccess: () =>
      React.forwardRef<any, P>((props, ref) => (
        <ProtectedComponent
          permissions={[
            `${basePermission}:read`,
            `${basePermission}:create`,
            `${basePermission}:update`,
            `${basePermission}:delete`,
          ]}
          requireAll={false}
        >
          <Component {...props} ref={ref} />
        </ProtectedComponent>
      )),
  };
}

/**
 * Utility functions for common decorator patterns
 */
export const decoratorUtils = {
  /**
   * Create a protected component factory for a specific module
   */
  createModuleDecorators: (moduleName: string) => ({
    read: <P extends object>(Component: React.ComponentType<P>) =>
      createProtected(Component).withPermissions(`${moduleName}:read`),

    create: <P extends object>(Component: React.ComponentType<P>) =>
      createProtected(Component).withPermissions(`${moduleName}:create`),

    update: <P extends object>(Component: React.ComponentType<P>) =>
      createProtected(Component).withPermissions(`${moduleName}:update`),

    delete: <P extends object>(Component: React.ComponentType<P>) =>
      createProtected(Component).withPermissions(`${moduleName}:delete`),

    admin: <P extends object>(Component: React.ComponentType<P>) =>
      createProtected(Component).withPermissions(`${moduleName}:admin`),
  }),

  /**
   * Create portal-specific decorators
   */
  createPortalDecorators: (portalName: string) => ({
    access: <P extends object>(Component: React.ComponentType<P>) =>
      createProtected(Component).withPermissions(`${portalName}:access`),

    admin: <P extends object>(Component: React.ComponentType<P>) =>
      createProtected(Component).withPermissions(`${portalName}:admin`),
  }),
};

/**
 * Example usage and factory functions for common business domains
 */
export const commonDecorators = {
  // User management
  users: decoratorUtils.createModuleDecorators('users'),

  // Billing
  billing: decoratorUtils.createModuleDecorators('billing'),

  // Network management
  network: decoratorUtils.createModuleDecorators('network'),

  // Support tickets
  tickets: decoratorUtils.createModuleDecorators('tickets'),

  // Reports and analytics
  reports: decoratorUtils.createModuleDecorators('reports'),
  analytics: decoratorUtils.createModuleDecorators('analytics'),

  // System administration
  system: decoratorUtils.createModuleDecorators('system'),
};
