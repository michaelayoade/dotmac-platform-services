import type { User, Permission, PortalType } from '@dotmac/auth';
import type { PortalRoleConfig } from '../types';

/**
 * Utility functions for permission and role management
 */

/**
 * Default role configurations for each portal
 */
export const defaultPortalRoles: PortalRoleConfig = {
  admin: {
    admin: ['*'], // Full access
    manager: [
      'users:read',
      'users:create',
      'users:update',
      'billing:read',
      'billing:create',
      'billing:update',
      'network:read',
      'network:update',
      'reports:read',
      'analytics:read',
    ],
    user: ['dashboard:read', 'profile:read', 'profile:update'],
    readonly: ['dashboard:read'],
  },
  customer: {
    admin: ['profile:*', 'billing:read', 'tickets:*'],
    manager: ['profile:read', 'profile:update', 'billing:read', 'tickets:create'],
    user: ['profile:read', 'billing:read', 'tickets:create'],
    readonly: ['profile:read'],
  },
  reseller: {
    admin: ['customers:*', 'billing:*', 'reports:*', 'commissions:read', 'network:read'],
    manager: [
      'customers:read',
      'customers:create',
      'customers:update',
      'billing:read',
      'reports:read',
      'commissions:read',
    ],
    user: ['customers:read', 'billing:read'],
    readonly: ['customers:read'],
  },
  technician: {
    admin: ['network:*', 'tickets:*', 'field_ops:*'],
    manager: ['network:read', 'network:update', 'tickets:*', 'field_ops:*'],
    user: ['network:read', 'tickets:create', 'tickets:update', 'field_ops:read'],
    readonly: ['network:read', 'tickets:read'],
  },
  management: {
    admin: ['*'], // Full system access
    manager: [
      'tenants:*',
      'users:*',
      'system:read',
      'system:config',
      'reports:*',
      'analytics:*',
      'billing:*',
    ],
    user: ['tenants:read', 'users:read', 'reports:read'],
    readonly: ['dashboard:read', 'reports:read'],
  },
};

/**
 * Check if a permission string matches a pattern
 */
export function matchesPermissionPattern(permission: string, pattern: string): boolean {
  if (pattern === '*') return true;
  if (pattern === permission) return true;

  // Handle wildcard patterns like "users:*"
  if (pattern.endsWith('*')) {
    const prefix = pattern.slice(0, -1);
    return permission.startsWith(prefix);
  }

  return false;
}

/**
 * Get effective permissions for a user based on their role and portal
 */
export function getEffectivePermissions(user: User | null, portal: PortalType): string[] {
  if (!user) return [];

  const roleName = user.role?.name?.toLowerCase();
  const portalRoles = defaultPortalRoles[portal];

  if (!roleName || !portalRoles) return [];

  // Get permissions from role configuration
  const rolePermissions = portalRoles[roleName as keyof typeof portalRoles] || [];

  // Get explicit permissions assigned to user
  const userPermissions = user.permissions?.map((p) => p.id) || [];

  // Combine role-based and explicit permissions
  const allPermissions = [...rolePermissions, ...userPermissions];

  // Remove duplicates
  return Array.from(new Set(allPermissions));
}

/**
 * Check if user has a specific permission
 */
export function hasPermission(user: User | null, permission: string, portal: PortalType): boolean {
  if (!user) return false;

  const effectivePermissions = getEffectivePermissions(user, portal);

  return effectivePermissions.some((p) => matchesPermissionPattern(permission, p));
}

/**
 * Check if user has any of the specified permissions
 */
export function hasAnyPermission(
  user: User | null,
  permissions: string[],
  portal: PortalType
): boolean {
  return permissions.some((permission) => hasPermission(user, permission, portal));
}

/**
 * Check if user has all of the specified permissions
 */
export function hasAllPermissions(
  user: User | null,
  permissions: string[],
  portal: PortalType
): boolean {
  return permissions.every((permission) => hasPermission(user, permission, portal));
}

/**
 * Get all permissions available for a specific portal
 */
export function getPortalPermissions(portal: PortalType): string[] {
  const portalRoles = defaultPortalRoles[portal];
  if (!portalRoles) return [];

  const allPermissions = Object.values(portalRoles).flat();
  return Array.from(new Set(allPermissions)).filter((p) => p !== '*');
}

/**
 * Group permissions by resource
 */
export function groupPermissionsByResource(permissions: string[]): Record<string, string[]> {
  const grouped: Record<string, string[]> = {};

  permissions.forEach((permission) => {
    const [resource, action] = permission.split(':');
    if (resource && action) {
      if (!grouped[resource]) {
        grouped[resource] = [];
      }
      grouped[resource].push(action);
    }
  });

  return grouped;
}

/**
 * Check if a role exists in the portal configuration
 */
export function isValidRole(role: string, portal: PortalType): boolean {
  const portalRoles = defaultPortalRoles[portal];
  return portalRoles ? role.toLowerCase() in portalRoles : false;
}

/**
 * Get the highest role level for a user in a portal
 */
export function getUserRoleLevel(user: User | null, portal: PortalType): number {
  if (!user || !user.role) return 0;

  const roleName = user.role.name.toLowerCase();
  const roleHierarchy = ['readonly', 'user', 'manager', 'admin'];

  return roleHierarchy.indexOf(roleName) + 1;
}

/**
 * Compare two users' role levels
 */
export function compareRoleLevels(
  user1: User | null,
  user2: User | null,
  portal: PortalType
): number {
  const level1 = getUserRoleLevel(user1, portal);
  const level2 = getUserRoleLevel(user2, portal);
  return level1 - level2;
}

/**
 * Generate permission suggestions based on portal and role
 */
export function suggestPermissions(portal: PortalType, role: string): string[] {
  const portalRoles = defaultPortalRoles[portal];
  if (!portalRoles) return [];

  const rolePermissions = portalRoles[role.toLowerCase() as keyof typeof portalRoles];
  return rolePermissions ? [...rolePermissions] : [];
}
