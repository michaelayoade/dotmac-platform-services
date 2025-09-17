import React from 'react';
import { useAccessControl } from '../hooks/useAccessControl';

interface ConditionalRenderProps {
  children: React.ReactNode;
  show?: boolean;
  permissions?: string | string[];
  roles?: string | string[];
  requireAll?: boolean;
  fallback?: React.ReactNode;
}

/**
 * Component that conditionally renders based on permissions, roles, or custom logic
 * More flexible than ProtectedComponent for complex conditional rendering
 */
export function ConditionalRender({
  children,
  show = true,
  permissions,
  roles,
  requireAll = false,
  fallback = null,
}: ConditionalRenderProps) {
  const { checkAccess } = useAccessControl();

  // Custom show/hide logic
  if (!show) {
    return <>{fallback}</>;
  }

  // Permission-based logic
  const hasAccess = checkAccess(permissions, roles, requireAll);

  if (!hasAccess) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

/**
 * Show content only if user has ANY of the specified permissions
 */
export const ShowIfAny = ({
  permissions,
  roles,
  children,
  fallback = null,
}: {
  permissions?: string[];
  roles?: string[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) => (
  <ConditionalRender permissions={permissions} roles={roles} requireAll={false} fallback={fallback}>
    {children}
  </ConditionalRender>
);

/**
 * Show content only if user has ALL of the specified permissions
 */
export const ShowIfAll = ({
  permissions,
  roles,
  children,
  fallback = null,
}: {
  permissions?: string[];
  roles?: string[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) => (
  <ConditionalRender permissions={permissions} roles={roles} requireAll={true} fallback={fallback}>
    {children}
  </ConditionalRender>
);

/**
 * Hide content if user has specified permissions/roles
 */
export const HideIf = ({
  permissions,
  roles,
  children,
  requireAll = false,
}: {
  permissions?: string | string[];
  roles?: string | string[];
  children: React.ReactNode;
  requireAll?: boolean;
}) => {
  const { checkAccess } = useAccessControl();
  const hasAccess = checkAccess(permissions, roles, requireAll);

  if (hasAccess) {
    return null;
  }

  return <>{children}</>;
};
