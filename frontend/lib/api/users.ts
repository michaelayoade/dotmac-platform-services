/**
 * Users API
 *
 * User management data fetching and mutations
 * Connected to real backend endpoints
 */

import { api, normalizePaginatedResponse } from "./client";

type BackendUser = {
  id?: string;
  userId?: string;
  username?: string;
  email?: string;
  name?: string;
  fullName?: string;
  role?: User["role"];
  roles?: string[];
  status?: User["status"];
  isActive?: boolean;
  isVerified?: boolean;
  createdAt?: string;
  updatedAt?: string;
  lastLogin?: string;
  mfaEnabled?: boolean;
  avatarUrl?: string;
  tenantId?: string;
  tenant?: User["tenant"];
};

function resolveStatus(user: BackendUser): User["status"] {
  if (user.status) {
    return user.status;
  }
  if (user.isActive === false) {
    return "inactive";
  }
  if (user.isVerified === false) {
    return "pending";
  }
  return "active";
}

function mapUser(user: BackendUser): User {
  const resolvedName =
    user.name || user.fullName || user.username || user.email || "Unknown User";
  const role =
    (user.role as User["role"]) ||
    (user.roles?.[0] as User["role"] | undefined) ||
    "member";

  return {
    id: user.id || user.userId || "",
    email: user.email || "",
    name: resolvedName,
    role,
    status: resolveStatus(user),
    tenant: user.tenant,
    lastActive: user.lastLogin,
    createdAt: user.createdAt || "",
    updatedAt: user.updatedAt || "",
    mfaEnabled: user.mfaEnabled,
    avatarUrl: user.avatarUrl,
  };
}

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
  const normalized = normalizePaginatedResponse<BackendUser>(response);
  const users = normalized.items.map(mapUser);

  return {
    users,
    totalCount: normalized.total,
    pageCount: normalized.totalPages,
  };
}

export async function getUser(id: string): Promise<User> {
  const user = await api.get<BackendUser>(`/api/v1/users/${id}`);
  return mapUser(user);
}

export interface CreateUserData {
  email: string;
  name: string;
  role: User["role"];
  tenantId?: string;
  sendInvite?: boolean;
}

export async function createUser(data: CreateUserData): Promise<User> {
  const user = await api.post<BackendUser>("/api/v1/users", {
    email: data.email,
    name: data.name,
    role: data.role,
    tenant_id: data.tenantId,
    send_invite: data.sendInvite,
  });
  return mapUser(user);
}

export interface UpdateUserData {
  name?: string;
  role?: User["role"];
  status?: User["status"];
}

export async function updateUser(id: string, data: UpdateUserData): Promise<User> {
  const user = await api.patch<BackendUser>(`/api/v1/users/${id}`, data);
  return mapUser(user);
}

export async function deleteUser(id: string): Promise<void> {
  return api.delete(`/api/v1/users/${id}`);
}

export async function suspendUser(id: string): Promise<User> {
  const user = await api.post<BackendUser>(`/api/v1/users/${id}/suspend`);
  return mapUser(user);
}

export async function activateUser(id: string): Promise<User> {
  const user = await api.post<BackendUser>(`/api/v1/users/${id}/activate`);
  return mapUser(user);
}

export async function resendInvite(id: string): Promise<void> {
  return api.post(`/api/v1/users/${id}/resend-invite`);
}

export async function resetPassword(id: string): Promise<void> {
  return api.post(`/api/v1/users/${id}/reset-password`);
}
