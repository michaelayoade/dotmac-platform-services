import { useAuth } from '@dotmac/auth';
import type { PermissionContextValue } from '../types';

/**
 * Hook that provides comprehensive permission checking utilities
 * Leverages the existing auth system's hasPermission and hasRole methods
 */
export function usePermissions(): PermissionContextValue {
  const auth = useAuth();

  const hasPermission = (permission: string | string[]): boolean => {
    if (!auth.user || !auth.isAuthenticated) return false;

    if (typeof permission === 'string') {
      return auth.hasPermission(permission);
    }

    return permission.some((p) => auth.hasPermission(p));
  };

  const hasRole = (role: string | string[]): boolean => {
    if (!auth.user || !auth.isAuthenticated) return false;

    if (typeof role === 'string') {
      return auth.hasRole(role);
    }

    return role.some((r) => auth.hasRole(r));
  };

  const hasAnyPermission = (permissions: string[]): boolean => {
    if (!auth.user || !auth.isAuthenticated) return false;
    return permissions.some((permission) => auth.hasPermission(permission));
  };

  const hasAllPermissions = (permissions: string[]): boolean => {
    if (!auth.user || !auth.isAuthenticated) return false;
    return permissions.every((permission) => auth.hasPermission(permission));
  };

  const hasAnyRole = (roles: string[]): boolean => {
    if (!auth.user || !auth.isAuthenticated) return false;
    return roles.some((role) => auth.hasRole(role));
  };

  const hasAllRoles = (roles: string[]): boolean => {
    if (!auth.user || !auth.isAuthenticated) return false;
    return roles.every((role) => auth.hasRole(role));
  };

  const getUserPermissions = (): string[] => {
    if (!auth.user || !auth.isAuthenticated) return [];
    return auth.user.permissions?.map((p) => p.id) || [];
  };

  const getUserRoles = (): string[] => {
    if (!auth.user || !auth.isAuthenticated) return [];
    return auth.user.role ? [auth.user.role.name] : [];
  };

  return {
    hasPermission,
    hasRole,
    hasAnyPermission,
    hasAllPermissions,
    hasAnyRole,
    hasAllRoles,
    getUserPermissions,
    getUserRoles,
  };
}
