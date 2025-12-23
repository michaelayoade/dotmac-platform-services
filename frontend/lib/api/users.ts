/**
 * Users API
 *
 * User management data fetching and mutations
 * Connected to real backend endpoints
 */

import { api, normalizePaginatedResponse } from "./client";

export interface User {
  id: string;
  email: string;
  name: string;
  role: "admin" | "owner" | "member" | "viewer";
  status: "active" | "pending" | "suspended" | "inactive";
  tenant?: {
    id: string;
    name: string;
  };
  lastActive?: string;
  createdAt: string;
  updatedAt: string;
  mfaEnabled?: boolean;
  avatarUrl?: string;
}

export interface GetUsersParams {
  page?: number;
  pageSize?: number;
  search?: string;
  status?: string;
  role?: string;
  tenantId?: string;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}

export interface GetUsersResponse {
  users: User[];
  totalCount: number;
  pageCount: number;
}

export async function getUsers(params: GetUsersParams = {}): Promise<GetUsersResponse> {
  const { page = 1, pageSize = 20, search, status, role, tenantId, sortBy, sortOrder } = params;

  const response = await api.get<unknown>("/api/v1/users", {
    params: {
      page,
      page_size: pageSize,
      search,
      status,
      role,
      tenant_id: tenantId,
      sort_by: sortBy,
      sort_order: sortOrder,
    },
  });
  const normalized = normalizePaginatedResponse<User>(response);

  return {
    users: normalized.items,
    totalCount: normalized.total,
    pageCount: normalized.totalPages,
  };
}

export async function getUser(id: string): Promise<User> {
  return api.get<User>(`/api/v1/users/${id}`);
}

export interface CreateUserData {
  email: string;
  name: string;
  role: User["role"];
  tenantId?: string;
  sendInvite?: boolean;
}

export async function createUser(data: CreateUserData): Promise<User> {
  return api.post<User>("/api/v1/users", {
    email: data.email,
    name: data.name,
    role: data.role,
    tenant_id: data.tenantId,
    send_invite: data.sendInvite,
  });
}

export interface UpdateUserData {
  name?: string;
  role?: User["role"];
  status?: User["status"];
}

export async function updateUser(id: string, data: UpdateUserData): Promise<User> {
  return api.patch<User>(`/api/v1/users/${id}`, data);
}

export async function deleteUser(id: string): Promise<void> {
  return api.delete(`/api/v1/users/${id}`);
}

export async function suspendUser(id: string): Promise<User> {
  return api.post<User>(`/api/v1/users/${id}/suspend`);
}

export async function activateUser(id: string): Promise<User> {
  return api.post<User>(`/api/v1/users/${id}/activate`);
}

export async function resendInvite(id: string): Promise<void> {
  return api.post(`/api/v1/users/${id}/resend-invite`);
}

export async function resetPassword(id: string): Promise<void> {
  return api.post(`/api/v1/users/${id}/reset-password`);
}
