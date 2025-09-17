import { usePermissions } from './usePermissions';
import type { AccessRule, PermissionCheck } from '../types';

/**
 * Advanced access control hook for complex permission scenarios
 */
export function useAccessControl() {
  const permissions = usePermissions();

  const checkAccess = (
    requiredPermissions?: string | string[],
    requiredRoles?: string | string[],
    requireAll = false
  ): boolean => {
    const permissionCheck = checkPermissions(requiredPermissions, requireAll);
    const roleCheck = checkRoles(requiredRoles, requireAll);

    // If both permissions and roles are specified, both must pass
    if (requiredPermissions && requiredRoles) {
      return permissionCheck && roleCheck;
    }

    // If only permissions are specified
    if (requiredPermissions) {
      return permissionCheck;
    }

    // If only roles are specified
    if (requiredRoles) {
      return roleCheck;
    }

    // If neither specified, allow access (authenticated user)
    return true;
  };

  const checkPermissions = (
    requiredPermissions?: string | string[],
    requireAll = false
  ): boolean => {
    if (!requiredPermissions) return true;

    if (typeof requiredPermissions === 'string') {
      return permissions.hasPermission(requiredPermissions);
    }

    if (requireAll) {
      return permissions.hasAllPermissions(requiredPermissions);
    } else {
      return permissions.hasAnyPermission(requiredPermissions);
    }
  };

  const checkRoles = (requiredRoles?: string | string[], requireAll = false): boolean => {
    if (!requiredRoles) return true;

    if (typeof requiredRoles === 'string') {
      return permissions.hasRole(requiredRoles);
    }

    if (requireAll) {
      return permissions.hasAllRoles(requiredRoles);
    } else {
      return permissions.hasAnyRole(requiredRoles);
    }
  };

  const evaluateRule = (rule: AccessRule): boolean => {
    const results = rule.checks.map((check: PermissionCheck) => {
      if (check.type === 'permission') {
        if (check.operator === 'AND' && Array.isArray(check.value)) {
          return permissions.hasAllPermissions(check.value);
        } else {
          return permissions.hasPermission(check.value);
        }
      } else if (check.type === 'role') {
        if (check.operator === 'AND' && Array.isArray(check.value)) {
          return permissions.hasAllRoles(check.value);
        } else {
          return permissions.hasRole(check.value);
        }
      }
      return false;
    });

    // Apply rule-level operator
    if (rule.operator === 'AND') {
      return results.every((result) => result);
    } else {
      return results.some((result) => result);
    }
  };

  return {
    checkAccess,
    checkPermissions,
    checkRoles,
    evaluateRule,
    ...permissions,
  };
}
