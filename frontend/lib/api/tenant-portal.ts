/**
 * Tenant Portal API
 *
 * API client functions for tenant self-service portal
 */

import { api } from "./client";
import type {
  TenantDashboard,
  TeamMembersResponse,
  InvitationsResponse,
  Invitation,
  InviteMemberRequest,
  UpdateMemberRoleRequest,
  TeamMember,
  BillingInfo,
  InvoicesResponse,
  UsageMetrics,
  UsageBreakdown,
  TenantSettings,
  UpdateTenantSettingsRequest,
  ApiKey,
  CreateApiKeyRequest,
  CreateApiKeyResponse,
} from "@/types/tenant-portal";

// Dashboard
export async function getTenantDashboard(): Promise<TenantDashboard> {
  return api.get<TenantDashboard>("/api/v1/tenants/portal/dashboard");
}

// Team Members
export interface GetMembersParams {
  page?: number;
  pageSize?: number;
  search?: string;
  role?: string;
}

export async function getTenantMembers(
  params?: GetMembersParams
): Promise<TeamMembersResponse> {
  const query: Record<string, string | number | boolean | undefined> | undefined = params
    ? {
        page: params.page,
        pageSize: params.pageSize,
        search: params.search,
        role: params.role,
      }
    : undefined;

  return api.get<TeamMembersResponse>("/api/v1/tenants/portal/members", {
    params: query,
  });
}

export async function getMemberById(id: string): Promise<TeamMember> {
  return api.get<TeamMember>(`/api/v1/tenants/portal/members/${id}`);
}

export async function updateMemberRole(
  id: string,
  data: UpdateMemberRoleRequest
): Promise<TeamMember> {
  return api.patch<TeamMember>(`/api/v1/tenants/portal/members/${id}/role`, data);
}

export async function removeMember(id: string): Promise<void> {
  return api.delete<void>(`/api/v1/tenants/portal/members/${id}`);
}

// Invitations
export async function getInvitations(): Promise<InvitationsResponse> {
  return api.get<InvitationsResponse>("/api/v1/tenants/portal/invitations");
}

export async function inviteMember(
  data: InviteMemberRequest
): Promise<Invitation> {
  return api.post<Invitation>("/api/v1/tenants/portal/invitations", data);
}

export async function cancelInvitation(id: string): Promise<void> {
  return api.delete<void>(`/api/v1/tenants/portal/invitations/${id}`);
}

export async function resendInvitation(id: string): Promise<Invitation> {
  return api.post<Invitation>(
    `/api/v1/tenants/portal/invitations/${id}/resend`
  );
}

// Billing
export async function getTenantBilling(): Promise<BillingInfo> {
  return api.get<BillingInfo>("/api/v1/tenants/portal/billing");
}

export interface GetInvoicesParams {
  page?: number;
  pageSize?: number;
  status?: string;
}

export async function getTenantInvoices(
  params?: GetInvoicesParams
): Promise<InvoicesResponse> {
  const query: Record<string, string | number | boolean | undefined> | undefined = params
    ? {
        page: params.page,
        pageSize: params.pageSize,
        status: params.status,
      }
    : undefined;

  return api.get<InvoicesResponse>("/api/v1/tenants/portal/invoices", {
    params: query,
  });
}

export async function downloadInvoice(id: string): Promise<Blob> {
  return api.getBlob(`/api/v1/tenants/portal/invoices/${id}/download`);
}

// Usage
export interface GetUsageParams {
  period?: "7d" | "30d" | "90d" | "1y";
}

export async function getTenantUsage(
  params?: GetUsageParams
): Promise<UsageMetrics> {
  const query: Record<string, string | number | boolean | undefined> | undefined = params
    ? {
        period: params.period,
      }
    : undefined;

  return api.get<UsageMetrics>("/api/v1/tenants/portal/usage", { params: query });
}

export async function getTenantUsageBreakdown(
  params?: GetUsageParams
): Promise<UsageBreakdown> {
  const query: Record<string, string | number | boolean | undefined> | undefined = params
    ? {
        period: params.period,
      }
    : undefined;

  return api.get<UsageBreakdown>("/api/v1/tenants/portal/usage/breakdown", {
    params: query,
  });
}

// Settings
export async function getTenantSettings(): Promise<TenantSettings> {
  return api.get<TenantSettings>("/api/v1/tenants/portal/settings");
}

export async function updateTenantSettings(
  data: UpdateTenantSettingsRequest
): Promise<TenantSettings> {
  return api.patch<TenantSettings>("/api/v1/tenants/portal/settings", data);
}

// API Keys
export async function getApiKeys(): Promise<ApiKey[]> {
  return api.get<ApiKey[]>("/api/v1/tenants/portal/api-keys");
}

export async function createApiKey(
  data: CreateApiKeyRequest
): Promise<CreateApiKeyResponse> {
  return api.post<CreateApiKeyResponse>("/api/v1/tenants/portal/api-keys", data);
}

export async function deleteApiKey(id: string): Promise<void> {
  return api.delete<void>(`/api/v1/tenants/portal/api-keys/${id}`);
}
