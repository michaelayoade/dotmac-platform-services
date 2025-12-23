"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, normalizePaginatedResponse } from "@/lib/api/client";
import { queryKeys } from "@/lib/api/query-keys";
import type { User, UserStatus, UserRole } from "@/types/models";
import type { PaginatedResponse, ListQueryParams } from "@/types/api";

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

export interface UpdateUserData {
  name?: string;
  role?: UserRole;
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
  return api.post<User>(`/api/v1/users/${id}/suspend`);
}

async function activateUser(id: string): Promise<User> {
  return api.post<User>(`/api/v1/users/${id}/activate`);
}

async function resendInvite(id: string): Promise<void> {
  return api.post<void>(`/api/v1/users/${id}/resend-invite`);
}

async function resetPassword(id: string): Promise<void> {
  return api.post<void>(`/api/v1/users/${id}/reset-password`);
}

// Hooks
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
