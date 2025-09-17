// Re-export auth types we need
export type { User, UserRole, Permission, PermissionType, PortalType } from '@dotmac/auth';

// RBAC-specific types
export interface AccessControlProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  permissions?: string | string[];
  roles?: string | string[];
  requireAll?: boolean; // true = require ALL permissions/roles, false = require ANY
  onAccessDenied?: () => void;
}

export interface RouteGuardProps extends AccessControlProps {
  redirect?: string;
  component?: React.ComponentType<any>;
  element?: React.ReactElement;
}

export interface PermissionContextValue {
  hasPermission: (permission: string | string[]) => boolean;
  hasRole: (role: string | string[]) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
  hasAllPermissions: (permissions: string[]) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  hasAllRoles: (roles: string[]) => boolean;
  getUserPermissions: () => string[];
  getUserRoles: () => string[];
}

// Higher-order component types
export interface WithAccessControlOptions {
  permissions?: string | string[];
  roles?: string | string[];
  requireAll?: boolean;
  fallback?: React.ComponentType<any>;
  onAccessDenied?: () => void;
}

// Decorator options
export interface AccessControlDecoratorOptions extends WithAccessControlOptions {
  displayName?: string;
}

// Portal role mappings
export interface PortalRoleConfig {
  [portalType: string]: {
    admin: string[];
    manager: string[];
    user: string[];
    readonly: string[];
  };
}

// Permission checking utilities
export type PermissionCheck = {
  type: 'permission' | 'role';
  value: string | string[];
  operator: 'AND' | 'OR';
};

export interface AccessRule {
  checks: PermissionCheck[];
  operator: 'AND' | 'OR'; // How to combine multiple checks
}
