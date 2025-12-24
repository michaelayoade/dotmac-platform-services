/**
 * Tenants API
 *
 * Tenant/organization management data fetching
 * Connected to real backend endpoints
 */

import { api, normalizePaginatedResponse } from "./client";

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  status: "active" | "trial" | "suspended" | "inactive";
  plan: "Enterprise" | "Professional" | "Starter" | "Free";
  userCount: number;
  mrr: number; // in cents
  deploymentCount: number;
  domain?: string;
  createdAt: string;
  updatedAt: string;
  settings?: {
    features: string[];
    limits: Record<string, number>;
  };
}

export interface TenantStats {
  total: number;
  totalChange: number;
  active: number;
  trial: number;
  suspended: number;
}

export interface GetTenantsParams {
  page?: number;
  pageSize?: number;
  search?: string;
  status?: Tenant["status"];
  plan?: Tenant["plan"];
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}

export async function getTenants(params: GetTenantsParams = {}): Promise<{
  tenants: Tenant[];
  stats: TenantStats;
  totalCount: number;
  pageCount: number;
}> {
  const { page = 1, pageSize = 20, search, status, plan, sortBy, sortOrder } = params;

  const response = await api.get<unknown>("/api/v1/tenants", {
    params: {
      page,
      page_size: pageSize,
      search,
      status,
      plan,
      sort_by: sortBy,
      sort_order: sortOrder,
    },
  });
  const normalized = normalizePaginatedResponse<Tenant>(response);
  const responseStats = (response as { stats?: TenantStats }).stats;
  const derivedStats: TenantStats = {
    total: normalized.total,
    totalChange: 0,
    active: normalized.items.filter((tenant) => tenant.status === "active").length,
    trial: normalized.items.filter((tenant) => tenant.status === "trial").length,
    suspended: normalized.items.filter((tenant) => tenant.status === "suspended").length,
  };

  return {
    tenants: normalized.items,
    stats: responseStats ?? derivedStats,
    totalCount: normalized.total,
    pageCount: normalized.totalPages,
  };
}

export async function getTenant(id: string): Promise<Tenant> {
  return api.get<Tenant>(`/api/v1/tenants/${id}`);
}

export async function getCurrentTenant(): Promise<Tenant> {
  return api.get<Tenant>("/api/v1/tenants/current");
}

export interface TenantDetailedStats {
  userCount: number;
  userChange: number;
  activeUsers: number;
  deploymentCount: number;
  deploymentChange: number;
  storageUsed: number;
  storageLimit: number;
  apiCalls: number;
  apiCallsLimit: number;
}

export async function getTenantStats(id: string): Promise<TenantDetailedStats> {
  return api.get<TenantDetailedStats>(`/api/v1/tenants/${id}/stats`);
}

export interface TenantSettings {
  features: {
    mfa: boolean;
    sso: boolean;
    auditLogs: boolean;
    customDomain: boolean;
    apiAccess: boolean;
    webhooks: boolean;
  };
  limits: {
    maxUsers: number;
    maxDeployments: number;
    maxStorage: number;
    apiRateLimit: number;
  };
  branding?: {
    logoUrl?: string;
    primaryColor?: string;
    customCss?: string;
  };
}

export async function getTenantSettings(id: string): Promise<TenantSettings> {
  return api.get<TenantSettings>(`/api/v1/tenants/${id}/settings`);
}

export async function updateTenantSettings(
  id: string,
  settings: Partial<TenantSettings>
): Promise<TenantSettings> {
  return api.patch<TenantSettings>(`/api/v1/tenants/${id}/settings`, settings);
}

export interface CreateTenantData {
  name: string;
  slug: string;
  plan: Tenant["plan"];
  ownerEmail: string;
  ownerName: string;
}

export async function createTenant(data: CreateTenantData): Promise<Tenant> {
  return api.post<Tenant>("/api/v1/tenants", {
    name: data.name,
    slug: data.slug,
    plan: data.plan,
    owner_email: data.ownerEmail,
    owner_name: data.ownerName,
  });
}

export async function updateTenant(
  id: string,
  data: Partial<Pick<Tenant, "name" | "plan" | "status" | "settings">>
): Promise<Tenant> {
  return api.patch<Tenant>(`/api/v1/tenants/${id}`, data);
}

export async function suspendTenant(id: string, reason?: string): Promise<Tenant> {
  return api.post<Tenant>(`/api/v1/tenants/${id}/suspend`, { reason });
}

export async function activateTenant(id: string): Promise<Tenant> {
  return api.post<Tenant>(`/api/v1/tenants/${id}/activate`);
}

export async function deleteTenant(id: string): Promise<void> {
  return api.delete(`/api/v1/tenants/${id}`);
}

// Tenant member management
export interface TenantMember {
  id: string;
  userId: string;
  email: string;
  name: string;
  role: "owner" | "admin" | "member" | "viewer";
  joinedAt: string;
}

export async function getTenantMembers(tenantId: string): Promise<TenantMember[]> {
  return api.get<TenantMember[]>(`/api/v1/tenants/${tenantId}/members`);
}

export async function inviteTenantMember(
  tenantId: string,
  data: { email: string; role: TenantMember["role"] }
): Promise<TenantMember> {
  return api.post<TenantMember>(`/api/v1/tenants/${tenantId}/members`, data);
}

export async function updateTenantMemberRole(
  tenantId: string,
  memberId: string,
  role: TenantMember["role"]
): Promise<TenantMember> {
  return api.patch<TenantMember>(`/api/v1/tenants/${tenantId}/members/${memberId}`, { role });
}

export async function removeTenantMember(tenantId: string, memberId: string): Promise<void> {
  return api.delete(`/api/v1/tenants/${tenantId}/members/${memberId}`);
}
