/**
 * RBAC API Client
 *
 * Role-Based Access Control API for managing:
 * - Roles (create, update, delete)
 * - Permissions
 * - User role assignments
 */

import { api, normalizePaginatedResponse } from "./client";

// Types
export interface Permission {
  id: string;
  name: string;
  description: string;
  resource: string;
  action: string;
  createdAt: string;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  isSystem: boolean;
  permissions: Permission[];
  userCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface CreateRoleData {
  name: string;
  description: string;
  permissionIds: string[];
}

export interface UpdateRoleData {
  name?: string;
  description?: string;
  permissionIds?: string[];
}

export interface UserRole {
  userId: string;
  roleId: string;
  roleName: string;
  assignedAt: string;
  assignedBy?: string;
}

// Role API
export async function getRoles(): Promise<Role[]> {
  const response = await api.get<unknown>("/api/v1/auth/roles");
  // Handle both array and paginated response
  if (Array.isArray(response)) {
    return response as Role[];
  }
  const normalized = normalizePaginatedResponse<Role>(response);
  return normalized.items;
}

export async function getRole(id: string): Promise<Role> {
  return api.get<Role>(`/api/v1/auth/roles/${id}`);
}

export async function createRole(data: CreateRoleData): Promise<Role> {
  return api.post<Role>("/api/v1/auth/roles", {
    name: data.name,
    description: data.description,
    permission_ids: data.permissionIds,
  });
}

export async function updateRole(id: string, data: UpdateRoleData): Promise<Role> {
  return api.put<Role>(`/api/v1/auth/roles/${id}`, {
    name: data.name,
    description: data.description,
    permission_ids: data.permissionIds,
  });
}

export async function deleteRole(id: string): Promise<void> {
  return api.delete(`/api/v1/auth/roles/${id}`);
}

// Permissions API
export async function getPermissions(): Promise<Permission[]> {
  const response = await api.get<unknown>("/api/v1/auth/permissions");
  if (Array.isArray(response)) {
    return response as Permission[];
  }
  const normalized = normalizePaginatedResponse<Permission>(response);
  return normalized.items;
}

// User Role Assignment API
export async function getUserRoles(userId: string): Promise<UserRole[]> {
  return api.get<UserRole[]>(`/api/v1/auth/users/${userId}/roles`);
}

export async function assignRoleToUser(userId: string, roleId: string): Promise<void> {
  return api.post(`/api/v1/auth/users/${userId}/roles/${roleId}`);
}

export async function removeRoleFromUser(userId: string, roleId: string): Promise<void> {
  return api.delete(`/api/v1/auth/users/${userId}/roles/${roleId}`);
}

// User Permissions API
export async function getUserPermissions(userId: string): Promise<Permission[]> {
  return api.get<Permission[]>(`/api/v1/auth/users/${userId}/permissions`);
}
