import React from 'react';
import { useAccessControl } from '../hooks/useAccessControl';
import type { AccessControlProps } from '../types';

/**
 * Universal component for protecting UI elements based on permissions/roles
 *
 * @example
 * <ProtectedComponent permissions="users:create">
 *   <CreateUserButton />
 * </ProtectedComponent>
 *
 * @example
 * <ProtectedComponent
 *   permissions={["billing:read", "billing:update"]}
 *   requireAll={false}
 *   fallback={<div>Access denied</div>}
 * >
 *   <BillingSection />
 * </ProtectedComponent>
 */
export function ProtectedComponent({
  children,
  fallback = null,
  permissions,
  roles,
  requireAll = false,
  onAccessDenied,
}: AccessControlProps) {
  const { checkAccess } = useAccessControl();

  const hasAccess = checkAccess(permissions, roles, requireAll);

  if (!hasAccess) {
    onAccessDenied?.();
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

/**
 * Convenience components for common access control patterns
 */
export const AdminOnly = ({ children, fallback = null }: Omit<AccessControlProps, 'roles'>) => (
  <ProtectedComponent roles='admin' fallback={fallback}>
    {children}
  </ProtectedComponent>
);

export const ManagerOnly = ({ children, fallback = null }: Omit<AccessControlProps, 'roles'>) => (
  <ProtectedComponent roles={['admin', 'manager']} fallback={fallback}>
    {children}
  </ProtectedComponent>
);

export const AuthenticatedOnly = ({
  children,
  fallback = null,
}: Omit<AccessControlProps, 'permissions' | 'roles'>) => (
  <ProtectedComponent fallback={fallback}>{children}</ProtectedComponent>
);
