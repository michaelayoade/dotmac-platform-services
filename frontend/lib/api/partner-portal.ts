/**
 * Partner Portal API
 *
 * API client functions for partner self-service portal
 */

import { api } from "./client";
import type {
  PartnerDashboard,
  Referral,
  ReferralsResponse,
  CreateReferralRequest,
  PartnerTenantsResponse,
  CommissionsResponse,
  StatementsResponse,
  PayoutsResponse,
  Statement,
  PartnerProfile,
  UpdatePartnerProfileRequest,
} from "@/types/partner-portal";

// Dashboard
export async function getPartnerDashboard(): Promise<PartnerDashboard> {
  return api.get<PartnerDashboard>("/api/v1/partners/portal/dashboard");
}

// Referrals
export interface GetReferralsParams {
  page?: number;
  pageSize?: number;
  status?: string;
  search?: string;
}

export async function getPartnerReferrals(
  params?: GetReferralsParams
): Promise<ReferralsResponse> {
  const query: Record<string, string | number | boolean | undefined> | undefined = params
    ? {
        page: params.page,
        pageSize: params.pageSize,
        status: params.status,
        search: params.search,
      }
    : undefined;

  return api.get<ReferralsResponse>("/api/v1/partners/portal/referrals", {
    params: query,
  });
}

export async function getReferralById(id: string): Promise<Referral> {
  return api.get<Referral>(`/api/v1/partners/portal/referrals/${id}`);
}

export async function createReferral(
  data: CreateReferralRequest
): Promise<Referral> {
  return api.post<Referral>("/api/v1/partners/portal/referrals", data);
}

export async function updateReferral(
  id: string,
  data: Partial<CreateReferralRequest>
): Promise<Referral> {
  return api.patch<Referral>(`/api/v1/partners/portal/referrals/${id}`, data);
}

// Tenants
export interface GetTenantsParams {
  page?: number;
  pageSize?: number;
  status?: string;
  search?: string;
}

export async function getPartnerTenants(
  params?: GetTenantsParams
): Promise<PartnerTenantsResponse> {
  const query: Record<string, string | number | boolean | undefined> | undefined = params
    ? {
        page: params.page,
        pageSize: params.pageSize,
        status: params.status,
        search: params.search,
      }
    : undefined;

  return api.get<PartnerTenantsResponse>("/api/v1/partners/portal/tenants", {
    params: query,
  });
}

// Commissions
export interface GetCommissionsParams {
  page?: number;
  pageSize?: number;
  status?: string;
  startDate?: string;
  endDate?: string;
}

export async function getPartnerCommissions(
  params?: GetCommissionsParams
): Promise<CommissionsResponse> {
  const query: Record<string, string | number | boolean | undefined> | undefined = params
    ? {
        page: params.page,
        pageSize: params.pageSize,
        status: params.status,
        startDate: params.startDate,
        endDate: params.endDate,
      }
    : undefined;

  return api.get<CommissionsResponse>("/api/v1/partners/portal/commissions", {
    params: query,
  });
}

// Statements & Payouts
export interface GetStatementsParams {
  page?: number;
  pageSize?: number;
  status?: string;
  year?: number;
}

export async function getPartnerStatements(
  params?: GetStatementsParams
): Promise<StatementsResponse> {
  const query: Record<string, string | number | boolean | undefined> | undefined = params
    ? {
        page: params.page,
        pageSize: params.pageSize,
        status: params.status,
        year: params.year,
      }
    : undefined;

  return api.get<StatementsResponse>("/api/v1/partners/portal/statements", {
    params: query,
  });
}

export async function getStatementById(id: string): Promise<Statement> {
  return api.get<Statement>(`/api/v1/partners/portal/statements/${id}`);
}

export async function downloadStatement(id: string): Promise<Blob> {
  return api.getBlob(`/api/v1/partners/portal/statements/${id}/download`);
}

export async function getPartnerPayouts(): Promise<PayoutsResponse> {
  return api.get<PayoutsResponse>("/api/v1/partners/portal/payouts");
}

// Profile
export async function getPartnerProfile(): Promise<PartnerProfile> {
  return api.get<PartnerProfile>("/api/v1/partners/portal/profile");
}

export async function updatePartnerProfile(
  data: UpdatePartnerProfileRequest
): Promise<PartnerProfile> {
  return api.patch<PartnerProfile>("/api/v1/partners/portal/profile", data);
}

// ============================================
// Partner Billing (Multi-Tenant)
// ============================================

export interface PartnerBillingSummary {
  totalRevenue: number;
  totalOutstanding: number;
  totalPaidThisMonth: number;
  activeTenants: number;
  revenueByTenant: Array<{
    tenantId: string;
    tenantName: string;
    revenue: number;
    outstanding: number;
  }>;
  paymentStatusBreakdown: {
    paid: number;
    pending: number;
    overdue: number;
  };
  recentInvoices: Array<{
    id: string;
    number: string;
    tenantName: string;
    amount: number;
    status: string;
    dueDate: string;
  }>;
}

export async function getPartnerBillingSummary(): Promise<PartnerBillingSummary> {
  return api.get<PartnerBillingSummary>("/api/v1/partner/billing/summary");
}

export interface PartnerInvoice {
  id: string;
  number: string;
  tenantId: string;
  tenantName: string;
  amount: number;
  currency: string;
  status: "draft" | "pending" | "paid" | "overdue" | "cancelled";
  dueDate: string;
  paidAt?: string;
  createdAt: string;
}

export interface GetPartnerInvoicesParams {
  page?: number;
  pageSize?: number;
  tenantId?: string;
  status?: string;
  startDate?: string;
  endDate?: string;
  minAmount?: number;
  maxAmount?: number;
}

export interface PartnerInvoicesResponse {
  items: PartnerInvoice[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export async function getPartnerInvoices(
  params?: GetPartnerInvoicesParams
): Promise<PartnerInvoicesResponse> {
  const query: Record<string, string | number | boolean | undefined> | undefined = params
    ? {
        page: params.page,
        page_size: params.pageSize,
        tenant_id: params.tenantId,
        status: params.status,
        start_date: params.startDate,
        end_date: params.endDate,
        min_amount: params.minAmount,
        max_amount: params.maxAmount,
      }
    : undefined;

  return api.get<PartnerInvoicesResponse>("/api/v1/partner/billing/invoices", {
    params: query,
  });
}

export interface ExportPartnerInvoicesRequest {
  startDate: string;
  endDate: string;
  tenantIds?: string[];
  format: "csv" | "pdf" | "excel";
}

export interface ExportJob {
  id: string;
  status: "pending" | "processing" | "completed" | "failed";
  format: string;
  createdAt: string;
  completedAt?: string;
  downloadUrl?: string;
  error?: string;
}

export async function exportPartnerInvoices(
  data: ExportPartnerInvoicesRequest
): Promise<ExportJob> {
  return api.post<ExportJob>("/api/v1/partner/billing/invoices/export", {
    start_date: data.startDate,
    end_date: data.endDate,
    tenant_ids: data.tenantIds,
    format: data.format,
  });
}

export interface GetExportHistoryParams {
  page?: number;
  pageSize?: number;
}

export interface ExportHistoryResponse {
  items: ExportJob[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export async function getPartnerExportHistory(
  params?: GetExportHistoryParams
): Promise<ExportHistoryResponse> {
  return api.get<ExportHistoryResponse>("/api/v1/partner/billing/exports", {
    params: {
      page: params?.page,
      page_size: params?.pageSize,
    },
  });
}

export async function downloadExport(exportId: string): Promise<Blob> {
  return api.getBlob(`/api/v1/partner/billing/exports/${exportId}/download`);
}
