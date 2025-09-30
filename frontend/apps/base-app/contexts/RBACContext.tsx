/**
 * RBAC Context Provider
 * Manages roles, permissions, and access control throughout the application
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { logger } from '@/lib/utils/logger';
import { handleError } from '@/lib/utils/error-handler';
import { useToast } from '@/components/ui/use-toast';

// Migrated from sonner to useToast hook
// Note: toast options have changed:
// - sonner: toast.success('msg') -> useToast: toast({ title: 'Success', description: 'msg' })
// - sonner: toast.error('msg') -> useToast: toast({ title: 'Error', description: 'msg', variant: 'destructive' })
// - For complex options, refer to useToast documentation

/**
 * Permission categories matching backend
 */
export enum PermissionCategory {
  USERS = 'users',
  BILLING = 'billing',
  ANALYTICS = 'analytics',
  COMMUNICATIONS = 'communications',
  INFRASTRUCTURE = 'infrastructure',
  SECRETS = 'secrets',
  CUSTOMERS = 'customers',
  SETTINGS = 'settings',
  SYSTEM = 'system'
}

/**
 * Permission actions
 */
export enum PermissionAction {
  CREATE = 'create',
  READ = 'read',
  UPDATE = 'update',
  DELETE = 'delete',
  EXECUTE = 'execute',
  MANAGE = 'manage'
}

/**
 * Types
 */
export interface Permission {
  name: string;
  display_name: string;
  description?: string;
  category: PermissionCategory;
  resource?: string;
  action?: string;
  is_system: boolean;
}

export interface Role {
  name: string;
  display_name: string;
  description?: string;
  parent_role?: string;
  is_system: boolean;
  is_active: boolean;
  permissions: Permission[];
  created_at: string;
  updated_at: string;
}

export interface UserPermissions {
  user_id: string;
  roles: Role[];
  direct_permissions: Permission[];
  effective_permissions: Permission[];
  is_superuser: boolean;
}

export interface RoleCreateRequest {
  name: string;
  display_name: string;
  description?: string;
  parent_role?: string;
  permissions: string[];
}

export interface RoleUpdateRequest {
  display_name?: string;
  description?: string;
  parent_role?: string;
  permissions?: string[];
  is_active?: boolean;
}

export interface UserRoleAssignment {
  user_id: string;
  role_name: string;
  granted_by?: string;
  expires_at?: string;
}

export interface UserPermissionGrant {
  user_id: string;
  permission_name: string;
  granted_by?: string;
  expires_at?: string;
}

/**
 * API functions
 */
const rbacApi = {
  // Permissions
  fetchPermissions: async (category?: PermissionCategory): Promise<Permission[]> => {
    const params = category ? `?category=${category}` : '';
    const response = await apiClient.get(`/api/v1/auth/rbac/permissions${params}`);
    return response.data;
  },

  fetchPermission: async (name: string): Promise<Permission> => {
    const response = await apiClient.get(`/api/v1/auth/rbac/permissions/${name}`);
    return response.data;
  },

  // Roles
  fetchRoles: async (activeOnly = true): Promise<Role[]> => {
    const response = await apiClient.get(`/api/v1/auth/rbac/roles?active_only=${activeOnly}`);
    return response.data;
  },

  createRole: async (data: RoleCreateRequest): Promise<Role> => {
    const response = await apiClient.post('/api/v1/auth/rbac/roles', data);
    return response.data;
  },

  updateRole: async (name: string, data: RoleUpdateRequest): Promise<Role> => {
    const response = await apiClient.patch(`/api/v1/auth/rbac/roles/${name}`, data);
    return response.data;
  },

  deleteRole: async (name: string): Promise<void> => {
    await apiClient.delete(`/api/v1/auth/rbac/roles/${name}`);
  },

  // User permissions
  fetchMyPermissions: async (): Promise<UserPermissions> => {
    const response = await apiClient.get('/api/v1/auth/rbac/my-permissions');
    return response.data;
  },

  fetchUserPermissions: async (userId: string): Promise<UserPermissions> => {
    const response = await apiClient.get(`/api/v1/auth/rbac/users/${userId}/permissions`);
    return response.data;
  },

  assignRoleToUser: async (data: UserRoleAssignment): Promise<void> => {
    await apiClient.post('/api/v1/auth/rbac/users/assign-role', data);
  },

  revokeRoleFromUser: async (data: UserRoleAssignment): Promise<void> => {
    await apiClient.post('/api/v1/auth/rbac/users/revoke-role', data);
  },

  grantPermissionToUser: async (data: UserPermissionGrant): Promise<void> => {
    await apiClient.post('/api/v1/auth/rbac/users/grant-permission', data);
  },
};

/**
 * RBAC Context
 */
interface RBACContextValue {
  // Current user permissions
  permissions: UserPermissions | null;
  loading: boolean;
  error: Error | null;

  // Permission checks
  hasPermission: (permission: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
  hasAllPermissions: (permissions: string[]) => boolean;
  hasRole: (role: string) => boolean;
  canAccess: (category: PermissionCategory, action?: PermissionAction) => boolean;

  // Role management
  roles: Role[];
  createRole: (data: RoleCreateRequest) => Promise<void>;
  updateRole: (name: string, data: RoleUpdateRequest) => Promise<void>;
  deleteRole: (name: string) => Promise<void>;

  // User role/permission management
  assignRole: (userId: string, roleName: string) => Promise<void>;
  revokeRole: (userId: string, roleName: string) => Promise<void>;
  grantPermission: (userId: string, permissionName: string) => Promise<void>;

  // Utilities
  refreshPermissions: () => void;
  getAllPermissions: () => Promise<Permission[]>;
}

const RBACContext = createContext<RBACContextValue | undefined>(undefined);

/**
 * RBAC Provider Component
 */
export function RBACProvider({ children }: { children: React.ReactNode }) {
  const { toast } = useToast();

  const queryClient = useQueryClient();

  // Fetch current user permissions
  const {
    data: permissions,
    isLoading: loading,
    error,
    refetch: refreshPermissions
  } = useQuery({
    queryKey: ['rbac', 'my-permissions'],
    queryFn: rbacApi.fetchMyPermissions,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });

  // Fetch all roles
  const { data: roles = [] } = useQuery({
    queryKey: ['rbac', 'roles'],
    queryFn: () => rbacApi.fetchRoles(true),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });

  // Permission check functions
  const effectivePermissions = permissions?.effective_permissions ?? [];
  const assignedRoles = permissions?.roles ?? [];
  const isSuperuser = permissions?.is_superuser ?? false;

  const hasPermission = useCallback((permission: string): boolean => {
    if (!permissions) return false;
    if (isSuperuser) return true;

    return effectivePermissions.some(p =>
      p.name === permission || p.name === '*' || p.name.endsWith('.*')
    );
  }, [permissions, effectivePermissions, isSuperuser]);

  const hasAnyPermission = useCallback((perms: string[]): boolean => {
    if (!permissions) return false;
    if (isSuperuser) return true;

    return perms.some(perm => hasPermission(perm));
  }, [permissions, hasPermission, isSuperuser]);

  const hasAllPermissions = useCallback((perms: string[]): boolean => {
    if (!permissions) return false;
    if (isSuperuser) return true;

    return perms.every(perm => hasPermission(perm));
  }, [permissions, hasPermission, isSuperuser]);

  const hasRole = useCallback((role: string): boolean => {
    if (!permissions) return false;
    if (isSuperuser) return true;

    return assignedRoles.some(r => r.name === role);
  }, [permissions, assignedRoles, isSuperuser]);

  const canAccess = useCallback((category: PermissionCategory, action?: PermissionAction): boolean => {
    if (!permissions) return false;
    if (isSuperuser) return true;

    const permissionName = action ? `${category}.${action}` : `${category}.*`;

    return effectivePermissions.some(p => {
      // Exact match
      if (p.name === permissionName) return true;

      // Wildcard match (e.g., users.* matches users.read)
      if (p.name === `${category}.*`) return true;

      // System wildcard
      if (p.name === '*') return true;

      // Category and action match
      if (p.category === category && (!action || p.action === action)) return true;

      return false;
    });
  }, [permissions, isSuperuser, effectivePermissions]);

  // Role management mutations
  const createRoleMutation = useMutation({
    mutationFn: rbacApi.createRole,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rbac', 'roles'] });
      toast({ title: 'Success', description: 'Role created successfully' });
    },
    onError: (error) => {
      handleError(error, { showToast: true, toastMessage: 'Failed to create role' });
    },
  });

  const updateRoleMutation = useMutation({
    mutationFn: ({ name, data }: { name: string; data: RoleUpdateRequest }) =>
      rbacApi.updateRole(name, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rbac', 'roles'] });
      toast({ title: 'Success', description: 'Role updated successfully' });
    },
    onError: (error) => {
      handleError(error, { showToast: true, toastMessage: 'Failed to update role' });
    },
  });

  const deleteRoleMutation = useMutation({
    mutationFn: rbacApi.deleteRole,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rbac', 'roles'] });
      toast({ title: 'Success', description: 'Role deleted successfully' });
    },
    onError: (error) => {
      handleError(error, { showToast: true, toastMessage: 'Failed to delete role' });
    },
  });

  // User role/permission mutations
  const assignRoleMutation = useMutation({
    mutationFn: rbacApi.assignRoleToUser,
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['rbac', 'users', variables.user_id] });
      toast({ title: 'Success', description: 'Role assigned successfully' });
    },
    onError: (error) => {
      handleError(error, { showToast: true, toastMessage: 'Failed to assign role' });
    },
  });

  const revokeRoleMutation = useMutation({
    mutationFn: rbacApi.revokeRoleFromUser,
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['rbac', 'users', variables.user_id] });
      toast({ title: 'Success', description: 'Role revoked successfully' });
    },
    onError: (error) => {
      handleError(error, { showToast: true, toastMessage: 'Failed to revoke role' });
    },
  });

  const grantPermissionMutation = useMutation({
    mutationFn: rbacApi.grantPermissionToUser,
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['rbac', 'users', variables.user_id] });
      toast({ title: 'Success', description: 'Permission granted successfully' });
    },
    onError: (error) => {
      handleError(error, { showToast: true, toastMessage: 'Failed to grant permission' });
    },
  });

  // Context value
  const contextValue: RBACContextValue = {
    permissions,
    loading,
    error,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    canAccess,
    roles,
    createRole: async (data) => {
      await createRoleMutation.mutateAsync(data);
    },
    updateRole: async (name, data) => {
      await updateRoleMutation.mutateAsync({ name, data });
    },
    deleteRole: async (name) => {
      await deleteRoleMutation.mutateAsync(name);
    },
    assignRole: async (userId, roleName) => {
      await assignRoleMutation.mutateAsync({ user_id: userId, role_name: roleName });
    },
    revokeRole: async (userId, roleName) => {
      await revokeRoleMutation.mutateAsync({ user_id: userId, role_name: roleName });
    },
    grantPermission: async (userId, permissionName) => {
      await grantPermissionMutation.mutateAsync({ user_id: userId, permission_name: permissionName });
    },
    refreshPermissions: () => refreshPermissions(),
    getAllPermissions: () => rbacApi.fetchPermissions(),
  };

  // Log permission changes in development
  useEffect(() => {
    if (permissions && process.env.NODE_ENV === 'development') {
      logger.info('User permissions loaded', {
        userId: permissions.user_id,
        roles: permissions.roles.map(r => r.name),
        permissionCount: permissions.effective_permissions.length,
        isSuperuser: permissions.is_superuser,
      });
    }
  }, [permissions]);

  return (
    <RBACContext.Provider value={contextValue}>
      {children}
    </RBACContext.Provider>
  );
}

/**
 * Hook to use RBAC context
 */
export function useRBAC() {
  const context = useContext(RBACContext);
  if (!context) {
    throw new Error('useRBAC must be used within RBACProvider');
  }
  return context;
}

/**
 * Hook for permission checks
 */
export function usePermission(permission: string | string[]): boolean {
  const { hasPermission, hasAnyPermission } = useRBAC();

  if (Array.isArray(permission)) {
    return hasAnyPermission(permission);
  }

  return hasPermission(permission);
}

/**
 * Hook for role checks
 */
export function useRole(role: string): boolean {
  const { hasRole } = useRBAC();
  return hasRole(role);
}

/**
 * Hook for category access
 */
export function useCategoryAccess(category: PermissionCategory, action?: PermissionAction): boolean {
  const { canAccess } = useRBAC();
  return canAccess(category, action);
}
