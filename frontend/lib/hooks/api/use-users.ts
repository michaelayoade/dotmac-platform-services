"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, normalizePaginatedResponse } from "@/lib/api/client";
import { queryKeys } from "@/lib/api/query-keys";
import { getUsersDashboard } from "@/lib/api/users";
import type { User, UserStatus, UserRole } from "@/types/models";
import type { PaginatedResponse, ListQueryParams } from "@/types/api";
import type { DashboardQueryParams } from "@/lib/api/types/dashboard";

// Types
export interface ListUsersParams extends ListQueryParams {
  role?: UserRole;
  status?: UserStatus;
  teamId?: string;
}

export interface CreateUserData {
  email: string;
  name: string;
  role: UserRole;
  teamIds?: string[];
  sendInvite?: boolean;
}

// Tenant-level roles used in forms
type TenantRole = "owner" | "admin" | "member" | "viewer";

export interface UpdateUserData {
  name?: string;
  role?: UserRole | TenantRole;
  phone?: string;
  timezone?: string;
  teamIds?: string[];
}

type UsersResponse = PaginatedResponse<User>;

// API functions
async function getUsers(params?: ListUsersParams): Promise<UsersResponse> {
  const response = await api.get<unknown>("/api/v1/users", {
    params: {
      page: params?.page ?? 1,
      page_size: params?.pageSize ?? 10,
      sort_by: params?.sort?.[0]?.field,
      sort_order: params?.sort?.[0]?.direction,
      search: params?.search,
      role: params?.role,
      status: params?.status,
      team_id: params?.teamId,
    },
  });
  return normalizePaginatedResponse<User>(response);
}

async function getUser(id: string): Promise<User> {
  return api.get<User>(`/api/v1/users/${id}`);
}

async function createUser(data: CreateUserData): Promise<User> {
  return api.post<User>("/api/v1/users", data);
}

async function updateUser({
  id,
  data,
}: {
  id: string;
  data: UpdateUserData;
}): Promise<User> {
  return api.patch<User>(`/api/v1/users/${id}`, data);
}

async function deleteUser(id: string): Promise<void> {
  return api.delete<void>(`/api/v1/users/${id}`);
}

async function suspendUser(id: string): Promise<User> {
  return api.post<User>(`/api/v1/users/${id}/disable`);
}

async function activateUser(id: string): Promise<User> {
  return api.post<User>(`/api/v1/users/${id}/enable`);
}

async function resendInvite(id: string): Promise<void> {
  return api.post<void>(`/api/v1/users/${id}/resend-verification`);
}

async function resetPassword(id: string): Promise<void> {
  return api.post<void>(`/api/v1/auth/admin/password-reset/trigger`, { userId: id });
}

// Hooks

export function useUsersDashboard(params?: DashboardQueryParams) {
  return useQuery({
    queryKey: queryKeys.users.dashboard(params),
    queryFn: () => getUsersDashboard(params),
    staleTime: 60 * 1000, // 1 minute
  });
}

export function useUsers(params?: ListUsersParams) {
  return useQuery({
    queryKey: queryKeys.users.list(params),
    queryFn: () => getUsers(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useUser(id: string) {
  return useQuery({
    queryKey: queryKeys.users.detail(id),
    queryFn: () => getUser(id),
    enabled: !!id,
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users.all });
    },
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateUser,
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.users.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.users.lists() });
    },
  });
}

export function useDeleteUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users.all });
    },
  });
}

export function useSuspendUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: suspendUser,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.users.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.users.lists() });
    },
  });
}

export function useActivateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: activateUser,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.users.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.users.lists() });
    },
  });
}

export function useResendInvite() {
  return useMutation({
    mutationFn: resendInvite,
  });
}

export function useResetPassword() {
  return useMutation({
    mutationFn: resetPassword,
  });
}

// ========================================
// Bulk Operations
// ========================================

interface BulkActionResponse {
  success_count: number;
  errors: Array<{ user_id: string; error: string }>;
}

async function bulkDeleteUsers(userIds: string[], hardDelete = false): Promise<BulkActionResponse> {
  return api.post<BulkActionResponse>("/api/v1/users/bulk/delete", {
    user_ids: userIds,
    hard_delete: hardDelete,
  });
}

async function bulkSuspendUsers(userIds: string[]): Promise<BulkActionResponse> {
  return api.post<BulkActionResponse>("/api/v1/users/bulk/suspend", {
    user_ids: userIds,
  });
}

async function bulkActivateUsers(userIds: string[]): Promise<BulkActionResponse> {
  return api.post<BulkActionResponse>("/api/v1/users/bulk/activate", {
    user_ids: userIds,
  });
}

async function bulkResendVerification(userIds: string[]): Promise<BulkActionResponse> {
  return api.post<BulkActionResponse>("/api/v1/users/bulk/resend-verification", {
    user_ids: userIds,
  });
}

export function useBulkDeleteUsers() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userIds, hardDelete = false }: { userIds: string[]; hardDelete?: boolean }) =>
      bulkDeleteUsers(userIds, hardDelete),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users.all });
    },
  });
}

export function useBulkSuspendUsers() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userIds: string[]) => bulkSuspendUsers(userIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users.all });
    },
  });
}

export function useBulkActivateUsers() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userIds: string[]) => bulkActivateUsers(userIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users.all });
    },
  });
}

export function useBulkResendVerification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userIds: string[]) => bulkResendVerification(userIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users.all });
    },
  });
}
