"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/lib/api/query-keys";
import {
  getRoles,
  getRole,
  createRole,
  updateRole,
  deleteRole,
  getPermissions,
  getUserRoles,
  assignRoleToUser,
  removeRoleFromUser,
  getUserPermissions,
  type Role,
  type CreateRoleData,
  type UpdateRoleData,
} from "@/lib/api/rbac";

// Role Hooks
export function useRoles() {
  return useQuery({
    queryKey: queryKeys.rbac.roles.list(),
    queryFn: getRoles,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useRole(id: string) {
  return useQuery({
    queryKey: queryKeys.rbac.roles.detail(id),
    queryFn: () => getRole(id),
    enabled: !!id,
  });
}

export function useCreateRole() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateRoleData) => createRole(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.rbac.roles.all() });
    },
  });
}

export function useUpdateRole() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateRoleData }) =>
      updateRole(id, data),
    onSuccess: (updatedRole) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.rbac.roles.all() });
      queryClient.setQueryData(
        queryKeys.rbac.roles.detail(updatedRole.id),
        updatedRole
      );
    },
  });
}

export function useDeleteRole() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteRole(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.rbac.roles.all() });
    },
  });
}

// Permission Hooks
export function usePermissions() {
  return useQuery({
    queryKey: queryKeys.rbac.permissions.list(),
    queryFn: getPermissions,
    staleTime: 10 * 60 * 1000, // 10 minutes - permissions change rarely
  });
}

// User Role Assignment Hooks
export function useUserRoles(userId: string) {
  return useQuery({
    queryKey: queryKeys.rbac.userRoles(userId),
    queryFn: () => getUserRoles(userId),
    enabled: !!userId,
  });
}

export function useAssignRole() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, roleId }: { userId: string; roleId: string }) =>
      assignRoleToUser(userId, roleId),
    onSuccess: (_, { userId }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.rbac.userRoles(userId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.rbac.userPermissions(userId),
      });
      // Also invalidate roles list as user count may have changed
      queryClient.invalidateQueries({ queryKey: queryKeys.rbac.roles.all() });
    },
  });
}

export function useRemoveRole() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, roleId }: { userId: string; roleId: string }) =>
      removeRoleFromUser(userId, roleId),
    onSuccess: (_, { userId }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.rbac.userRoles(userId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.rbac.userPermissions(userId),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.rbac.roles.all() });
    },
  });
}

// User Permissions Hook
export function useUserPermissions(userId: string) {
  return useQuery({
    queryKey: queryKeys.rbac.userPermissions(userId),
    queryFn: () => getUserPermissions(userId),
    enabled: !!userId,
  });
}
