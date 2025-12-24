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
  PartnerCustomersResponse,
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

// Customers
export interface GetCustomersParams {
  page?: number;
  pageSize?: number;
  status?: string;
  search?: string;
}

export async function getPartnerCustomers(
  params?: GetCustomersParams
): Promise<PartnerCustomersResponse> {
  const query: Record<string, string | number | boolean | undefined> | undefined = params
    ? {
        page: params.page,
        pageSize: params.pageSize,
        status: params.status,
        search: params.search,
      }
    : undefined;

  return api.get<PartnerCustomersResponse>("/api/v1/partners/portal/customers", {
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
