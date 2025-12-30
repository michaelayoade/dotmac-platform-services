/**
 * Users API
 *
 * User management data fetching and mutations
 * Connected to real backend endpoints
 */

import { api, normalizePaginatedResponse } from "./client";
import type { UserDashboardResponse, DashboardQueryParams } from "./types/dashboard";

// ============================================================================
// Dashboard
// ============================================================================

export async function getUsersDashboard(
  params?: DashboardQueryParams
): Promise<UserDashboardResponse> {
  return api.get<UserDashboardResponse>("/api/v1/users/dashboard", {
    params: {
      period_months: params?.periodMonths,
    },
  });
}

// ============================================================================
// Types and Helpers
// ============================================================================

type BackendUser = {
  id?: string;
  userId?: string;
  user_id?: string;
  username?: string;
  email?: string;
  name?: string;
  fullName?: string;
  full_name?: string;
  role?: User["role"];
  roles?: string[];
  status?: User["status"];
  isActive?: boolean;
  isVerified?: boolean;
  is_verified?: boolean;
  createdAt?: string;
  updatedAt?: string;
  lastLogin?: string;
  last_login?: string;
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
  if (user.isVerified === false || user.is_verified === false) {
    return "pending";
  }
  return "active";
}

function mapUser(user: BackendUser): User {
  const resolvedName =
    user.name ||
    user.fullName ||
    user.full_name ||
    user.username ||
    user.email ||
    "Unknown User";
  const role =
    (user.role as User["role"]) ||
    (user.roles?.[0] as User["role"] | undefined) ||
    "member";

  return {
    id: user.id || user.userId || user.user_id || "",
    email: user.email || "",
    name: resolvedName,
    role,
    status: resolveStatus(user),
    tenant: user.tenant,
    lastActive: user.lastLogin || user.last_login,
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
  // Backend uses /disable endpoint
  const user = await api.post<BackendUser>(`/api/v1/users/${id}/disable`);
  return mapUser(user);
}

export async function activateUser(id: string): Promise<User> {
  // Backend uses /enable endpoint
  const user = await api.post<BackendUser>(`/api/v1/users/${id}/enable`);
  return mapUser(user);
}

export async function resendInvite(id: string): Promise<void> {
  // Resend verification email for a pending user
  return api.post(`/api/v1/users/${id}/resend-verification`);
}

export async function resetPassword(id: string): Promise<void> {
  // Admin-triggered password reset endpoint
  return api.post(`/api/v1/auth/admin/password-reset/trigger`, { user_id: id });
}

// ========================================
// Bulk Operations
// ========================================

export interface BulkActionResponse {
  success_count: number;
  errors: Array<{ user_id: string; error: string }>;
}

export async function bulkDeleteUsers(
  userIds: string[],
  hardDelete = false
): Promise<BulkActionResponse> {
  return api.post<BulkActionResponse>("/api/v1/users/bulk/delete", {
    user_ids: userIds,
    hard_delete: hardDelete,
  });
}

export async function bulkSuspendUsers(userIds: string[]): Promise<BulkActionResponse> {
  return api.post<BulkActionResponse>("/api/v1/users/bulk/suspend", {
    user_ids: userIds,
  });
}

export async function bulkActivateUsers(userIds: string[]): Promise<BulkActionResponse> {
  return api.post<BulkActionResponse>("/api/v1/users/bulk/activate", {
    user_ids: userIds,
  });
}

export async function bulkResendVerification(userIds: string[]): Promise<BulkActionResponse> {
  return api.post<BulkActionResponse>("/api/v1/users/bulk/resend-verification", {
    user_ids: userIds,
  });
}

export interface ExportUsersParams {
  format?: "csv" | "json";
  isActive?: boolean;
  role?: string;
}

export async function exportUsers(params: ExportUsersParams = {}): Promise<Blob> {
  const { format = "csv", isActive, role } = params;
  const queryParams = new URLSearchParams();
  queryParams.set("format", format);
  if (isActive !== undefined) queryParams.set("is_active", String(isActive));
  if (role) queryParams.set("role", role);

  const response = await fetch(`/api/v1/users/export?${queryParams.toString()}`, {
    method: "POST",
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Failed to export users");
  }

  return response.blob();
}

export function downloadExport(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
