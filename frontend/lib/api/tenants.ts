/**
 * Tenants API
 *
 * Tenant/organization management data fetching
 * Connected to real backend endpoints
 */

import { api, normalizePaginatedResponse } from "./client";
import type { Tenant, TenantStatus, TenantPlanType } from "@/types/models";
import type { TenantDashboardResponse, DashboardQueryParams } from "./types/dashboard";

// ============================================================================
// Dashboard
// ============================================================================

export async function getTenantsDashboard(
  params?: DashboardQueryParams
): Promise<TenantDashboardResponse> {
  return api.get<TenantDashboardResponse>("/api/v1/tenants/dashboard", {
    params: {
      period_months: params?.periodMonths,
    },
  });
}

// Re-export Tenant from models for convenience
export type { Tenant, TenantStatus, TenantPlanType } from "@/types/models";

export interface TenantListStats {
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
  status?: TenantStatus;
  plan?: TenantPlanType;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}

export async function getTenants(params: GetTenantsParams = {}): Promise<{
  tenants: Tenant[];
  stats: TenantListStats;
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
  const responseStats = (response as { stats?: TenantListStats }).stats;
  const derivedStats: TenantListStats = {
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
  plan: TenantPlanType;
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
  fullName: string;
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

// Domain Verification
export type VerificationMethod = "dns_txt" | "dns_cname";
export type DomainStatus = "pending" | "verified" | "failed" | "expired";

export interface DomainVerification {
  domain: string;
  method: VerificationMethod;
  status: DomainStatus;
  verificationRecord: string;
  verificationValue: string;
  instructions: string;
  expiresAt: string;
  verifiedAt?: string;
  createdAt: string;
}

export interface DomainVerificationResult {
  success: boolean;
  domain: string;
  status: DomainStatus;
  message: string;
  verifiedAt?: string;
}

export async function initiateDomainVerification(
  tenantId: string,
  domain: string,
  method: VerificationMethod
): Promise<DomainVerification> {
  return api.post<DomainVerification>(
    `/api/v1/tenants/${tenantId}/domains/verify`,
    { domain, method }
  );
}

export async function checkDomainVerification(
  tenantId: string,
  domain: string
): Promise<DomainVerificationResult> {
  return api.post<DomainVerificationResult>(
    `/api/v1/tenants/${tenantId}/domains/check`,
    { domain }
  );
}

export async function getDomainStatus(tenantId: string): Promise<{
  domain?: string;
  status: DomainStatus | "none";
  verification?: DomainVerification;
}> {
  return api.get(`/api/v1/tenants/${tenantId}/domains/status`);
}

export async function removeDomain(tenantId: string): Promise<void> {
  return api.delete(`/api/v1/tenants/${tenantId}/domains`);
}

// Branding
export interface TenantBranding {
  logoUrl?: string;
  faviconUrl?: string;
  primaryColor: string;
  secondaryColor: string;
  accentColor: string;
  productName: string;
  tagline?: string;
  supportEmail?: string;
  customCss?: string;
  emailTemplateConfig?: {
    headerLogoUrl?: string;
    footerText?: string;
  };
}

export async function getBranding(tenantId: string): Promise<TenantBranding> {
  return api.get<TenantBranding>(`/api/v1/tenants/${tenantId}/branding`);
}

export async function updateBranding(
  tenantId: string,
  data: Partial<TenantBranding>
): Promise<TenantBranding> {
  return api.put<TenantBranding>(`/api/v1/tenants/${tenantId}/branding`, data);
}

export async function uploadBrandingLogo(
  tenantId: string,
  file: File,
  type: "logo" | "favicon"
): Promise<{ url: string }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("type", type);

  return api.post<{ url: string }>(
    `/api/v1/tenants/${tenantId}/branding/upload`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
}
