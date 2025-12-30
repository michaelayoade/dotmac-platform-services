/**
 * Permission Hook
 *
 * Check user permissions for RBAC
 */

"use client";

import { useMemo, type ReactNode } from "react";
import { useCurrentUser } from "@/lib/hooks/api/use-auth";

interface UsePermissionReturn {
  hasPermission: (permission: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
  hasAllPermissions: (permissions: string[]) => boolean;
  permissions: string[];
  role: string | null;
  isLoading: boolean;
}

export function usePermission(): UsePermissionReturn {
  const { data: user, isLoading } = useCurrentUser();

  const permissions = useMemo(() => {
    if (!user?.permissions) return [];
    return user.permissions as string[];
  }, [user?.permissions]);

  const role = (user?.roles?.[0] ?? null) as string | null;

  const hasPermission = (permission: string): boolean => {
    // Admins have all permissions
    if (role === "admin" || role === "platform_admin" || role === "super_admin") {
      return true;
    }

    // Check explicit permission
    if (permissions.includes(permission) || permissions.includes("*") || permissions.includes("*:*")) {
      return true;
    }

    // Check wildcard permissions
    const [resource, action] = permission.split(":");
    if (permissions.includes(`${resource}:*`)) return true;
    if (permissions.includes("*:*")) return true;

    return false;
  };

  const hasAnyPermission = (perms: string[]): boolean => {
    return perms.some((p) => hasPermission(p));
  };

  const hasAllPermissions = (perms: string[]): boolean => {
    return perms.every((p) => hasPermission(p));
  };

  return {
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    permissions,
    role,
    isLoading,
  };
}

/**
 * Permission Gate Component
 *
 * Conditionally render children based on permissions
 */
interface PermissionGateProps {
  permission?: string;
  permissions?: string[];
  requireAll?: boolean;
  fallback?: ReactNode;
  children: ReactNode;
}

export function PermissionGate({
  permission,
  permissions,
  requireAll = false,
  fallback = null,
  children,
}: PermissionGateProps) {
  const { hasPermission, hasAnyPermission, hasAllPermissions, isLoading } =
    usePermission();

  // While loading, avoid rendering gated content until permissions resolve
  if (isLoading) return <>{fallback ?? null}</>;

  let hasAccess = true;

  if (permission) {
    hasAccess = hasPermission(permission);
  } else if (permissions) {
    hasAccess = requireAll
      ? hasAllPermissions(permissions)
      : hasAnyPermission(permissions);
  }

  return hasAccess ? <>{children}</> : <>{fallback}</>;
}
