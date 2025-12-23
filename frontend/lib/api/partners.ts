/**
 * Partners API
 *
 * Partner management, accounts, commissions, referrals, and portal metrics
 */

import { api, ApiClientError, normalizePaginatedResponse } from "./client";

// ============================================================================
// Partner Types
// ============================================================================

export type PartnerStatus = "pending" | "active" | "suspended" | "terminated" | "archived";
export type PartnerTier = "bronze" | "silver" | "gold" | "platinum" | "direct";
export type CommissionModel = "revenue_share" | "flat_fee" | "tiered" | "hybrid";

export interface Partner {
  id: string;
  partnerNumber: string;
  status: PartnerStatus;
  companyName: string;
  legalName?: string | null;
  website?: string | null;
  description?: string | null;
  tier: PartnerTier;
  commissionModel: CommissionModel;
  defaultCommissionRate?: number | string | null;
  primaryEmail: string;
  billingEmail?: string | null;
  supportEmail?: string | null;
  phone?: string | null;
  addressLine1?: string | null;
  addressLine2?: string | null;
  city?: string | null;
  stateProvince?: string | null;
  postalCode?: string | null;
  country?: string | null;
  taxId?: string | null;
  vatNumber?: string | null;
  businessRegistration?: string | null;
  slaResponseHours?: number | null;
  slaUptimePercentage?: number | string | null;
  partnershipStartDate?: string | null;
  partnershipEndDate?: string | null;
  lastReviewDate?: string | null;
  nextReviewDate?: string | null;
  totalCustomers: number;
  totalRevenueGenerated: number | string;
  totalCommissionsEarned: number | string;
  totalCommissionsPaid: number | string;
  totalReferrals: number;
  convertedReferrals: number;
  metadata?: Record<string, unknown>;
  customFields?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

// ============================================================================
// Partner CRUD
// ============================================================================

export interface GetPartnersParams {
  page?: number;
  pageSize?: number;
  status?: PartnerStatus;
  tier?: PartnerTier;
  search?: string;
}

export async function getPartners(params: GetPartnersParams = {}): Promise<{
  partners: Partner[];
  totalCount: number;
  pageCount: number;
}> {
  const { page = 1, pageSize = 50, status, tier, search } = params;

  const response = await api.get<unknown>("/api/v1/partners", {
    params: {
      page,
      pageSize,
      status,
      tier,
      search,
    },
  });

  const normalized = normalizePaginatedResponse<Partner>(response);
  return {
    partners: normalized.items,
    totalCount: normalized.total,
    pageCount: normalized.totalPages,
  };
}

export async function getPartner(id: string): Promise<Partner> {
  return api.get<Partner>(`/api/v1/partners/${id}`);
}

export async function getPartnerByNumber(partnerNumber: string): Promise<Partner> {
  return api.get<Partner>(`/api/v1/partners/by-number/${partnerNumber}`);
}

export interface CreatePartnerData {
  companyName: string;
  legalName?: string;
  website?: string;
  description?: string;
  tier?: PartnerTier;
  commissionModel?: CommissionModel;
  defaultCommissionRate?: number;
  primaryEmail: string;
  billingEmail?: string;
  supportEmail?: string;
  phone?: string;
  addressLine1?: string;
  addressLine2?: string;
  city?: string;
  stateProvince?: string;
  postalCode?: string;
  country?: string;
  taxId?: string;
  vatNumber?: string;
  businessRegistration?: string;
  slaResponseHours?: number;
  slaUptimePercentage?: number;
  externalId?: string;
  metadata?: Record<string, unknown>;
  customFields?: Record<string, unknown>;
}

export async function createPartner(data: CreatePartnerData): Promise<Partner> {
  return api.post<Partner>("/api/v1/partners", data);
}

export async function updatePartner(
  id: string,
  data: Partial<CreatePartnerData> & { status?: PartnerStatus }
): Promise<Partner> {
  return api.patch<Partner>(`/api/v1/partners/${id}`, data);
}

export async function deletePartner(id: string): Promise<void> {
  return api.delete(`/api/v1/partners/${id}`);
}

export async function activatePartner(partnerId: string): Promise<Partner> {
  return updatePartner(partnerId, { status: "active" });
}

export async function deactivatePartner(partnerId: string): Promise<Partner> {
  return updatePartner(partnerId, { status: "suspended" });
}

// ============================================================================
// Partner Users
// ============================================================================

export interface PartnerUser {
  id: string;
  partnerId: string;
  userId?: string | null;
  firstName: string;
  lastName: string;
  email: string;
  phone?: string | null;
  role: string;
  isPrimaryContact?: boolean;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export async function getPartnerUsers(partnerId: string): Promise<PartnerUser[]> {
  return api.get<PartnerUser[]>(`/api/v1/partners/${partnerId}/users`);
}

export async function addPartnerUser(
  partnerId: string,
  data: {
    firstName: string;
    lastName: string;
    email: string;
    role: string;
    phone?: string;
    userId?: string;
    isPrimaryContact?: boolean;
  }
): Promise<PartnerUser> {
  return api.post<PartnerUser>(`/api/v1/partners/${partnerId}/users`, {
    ...data,
    partnerId,
  });
}

export async function removePartnerUser(_partnerId: string, _userId: string): Promise<void> {
  throw new ApiClientError("Removing partner users is not supported", 501, "NOT_IMPLEMENTED");
}

// ============================================================================
// Partner Accounts (Customer Assignments)
// ============================================================================

export interface PartnerAccount {
  id: string;
  partnerId: string;
  customerId: string;
  engagementType: string;
  customCommissionRate?: number | string | null;
  totalRevenue: number | string;
  totalCommissions: number | string;
  startDate: string;
  endDate?: string | null;
  isActive: boolean;
  notes?: string | null;
  metadata?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export async function getPartnerAccounts(partnerId: string): Promise<PartnerAccount[]> {
  return api.get<PartnerAccount[]>(`/api/v1/partners/${partnerId}/accounts`);
}

export async function addPartnerAccount(
  partnerId: string,
  customerId: string,
  data?: { engagementType?: string; customCommissionRate?: number; notes?: string }
): Promise<PartnerAccount> {
  return api.post<PartnerAccount>("/api/v1/partners/accounts", {
    partnerId,
    customerId,
    engagementType: data?.engagementType ?? "managed",
    customCommissionRate: data?.customCommissionRate,
    notes: data?.notes,
  });
}

export async function removePartnerAccount(
  _partnerId: string,
  _customerId: string
): Promise<void> {
  throw new ApiClientError("Removing partner accounts is not supported", 501, "NOT_IMPLEMENTED");
}

// ============================================================================
// Commissions
// ============================================================================

export type CommissionStatus = "pending" | "approved" | "paid" | "clawback" | "cancelled";

export interface CommissionEvent {
  id: string;
  partnerId: string;
  commissionAmount: number | string;
  currency: string;
  eventType: string;
  invoiceId?: string | null;
  customerId?: string | null;
  baseAmount?: number | string | null;
  commissionRate?: number | string | null;
  status: CommissionStatus;
  eventDate: string;
  payoutId?: string | null;
  paidAt?: string | null;
  notes?: string | null;
  metadata?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export async function getPartnerCommissions(
  partnerId: string,
  params?: {
    page?: number;
    pageSize?: number;
    status?: CommissionStatus;
  }
): Promise<{
  commissions: CommissionEvent[];
  totalCount: number;
  pageCount: number;
}> {
  const { page = 1, pageSize = 50 } = params ?? {};
  const response = await api.get<{
    events: CommissionEvent[];
    total: number;
    page: number;
    pageSize: number;
  }>(`/api/v1/partners/${partnerId}/commissions`, {
    params: {
      page,
      pageSize,
    },
  });

  return {
    commissions: response.events,
    totalCount: response.total,
    pageCount: pageSize ? Math.ceil(response.total / pageSize) : 0,
  };
}

export async function createCommissionEvent(data: {
  partnerId: string;
  commissionAmount: number;
  currency?: string;
  eventType: string;
  invoiceId?: string;
  customerId?: string;
  baseAmount?: number;
  commissionRate?: number;
  notes?: string;
  metadata?: Record<string, unknown>;
}): Promise<CommissionEvent> {
  return api.post<CommissionEvent>("/api/v1/partners/commissions", data);
}

export async function processCommissionPayout(
  _partnerId: string,
  _commissionIds: string[],
  _paymentMethod: string
): Promise<void> {
  throw new ApiClientError("Commission payouts are not supported", 501, "NOT_IMPLEMENTED");
}

// ============================================================================
// Payouts
// ============================================================================

export type PayoutStatus = "pending" | "ready" | "processing" | "completed" | "failed" | "cancelled";

export interface PartnerPayout {
  id: string;
  partnerId: string;
  totalAmount: number | string;
  currency: string;
  commissionCount: number;
  paymentReference?: string | null;
  paymentMethod: string;
  status: PayoutStatus;
  payoutDate: string;
  completedAt?: string | null;
  periodStart: string;
  periodEnd: string;
  notes?: string | null;
  failureReason?: string | null;
  createdAt: string;
  updatedAt: string;
}

export async function getPartnerPayouts(
  partnerId: string,
  params?: { status?: PayoutStatus; page?: number; pageSize?: number }
): Promise<PartnerPayout[]> {
  void partnerId;
  const { status } = params ?? {};
  return api.get<PartnerPayout[]>("/api/v1/partners/revenue/payouts", {
    params: {
      status,
    },
  });
}

// ============================================================================
// Referrals
// ============================================================================

export type ReferralStatus = "new" | "contacted" | "qualified" | "converted" | "lost" | "invalid";

export interface ReferralLead {
  id: string;
  partnerId: string;
  companyName: string;
  contactName: string;
  contactEmail: string;
  contactPhone?: string | null;
  status: ReferralStatus;
  notes?: string | null;
  metadata?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export async function getReferrals(
  partnerId: string,
  params?: { page?: number; pageSize?: number; status?: ReferralStatus }
): Promise<{
  referrals: ReferralLead[];
  totalCount: number;
  pageCount: number;
}> {
  const { page = 1, pageSize = 50 } = params ?? {};
  const response = await api.get<{
    referrals: ReferralLead[];
    total: number;
    page: number;
    pageSize: number;
  }>(`/api/v1/partners/${partnerId}/referrals`, {
    params: {
      page,
      pageSize,
    },
  });

  return {
    referrals: response.referrals,
    totalCount: response.total,
    pageCount: pageSize ? Math.ceil(response.total / pageSize) : 0,
  };
}

export async function createReferral(data: {
  partnerId: string;
  companyName: string;
  contactName: string;
  contactEmail: string;
  contactPhone?: string;
  notes?: string;
  metadata?: Record<string, unknown>;
}): Promise<ReferralLead> {
  return api.post<ReferralLead>("/api/v1/partners/referrals", data);
}

export async function convertReferral(
  partnerId: string,
  referralId: string,
  customerId: string
): Promise<ReferralLead> {
  return api.patch<ReferralLead>(`/api/v1/partners/referrals/${referralId}`, {
    status: "converted",
    customerId,
  });
}

// ============================================================================
// Partner Portal
// ============================================================================

export interface PartnerDashboard {
  totalCustomers: number;
  activeCustomers: number;
  totalRevenueGenerated: number | string;
  totalCommissionsEarned: number | string;
  totalCommissionsPaid: number | string;
  pendingCommissions: number | string;
  totalReferrals: number;
  convertedReferrals: number;
  pendingReferrals: number;
  conversionRate: number;
  currentTier: string;
  commissionModel: string;
  defaultCommissionRate: number | string;
}

export async function getPartnerDashboard(): Promise<PartnerDashboard> {
  return api.get<PartnerDashboard>("/api/v1/partners/portal/dashboard");
}

export interface PartnerStats {
  partnerId: string;
  periodStart: string;
  periodEnd: string;
  totalCommissions: number | string;
  totalCommissionCount: number;
  totalPayouts: number | string;
  pendingAmount: number | string;
  currency: string;
}

export async function getPartnerStats(params?: {
  periodStart?: string;
  periodEnd?: string;
  periodDays?: number;
}): Promise<PartnerStats> {
  const now = new Date();
  const resolvedPeriodStart =
    params?.periodStart ??
    (params?.periodDays
      ? new Date(now.getTime() - params.periodDays * 24 * 60 * 60 * 1000).toISOString()
      : undefined);
  const resolvedPeriodEnd = params?.periodEnd ?? now.toISOString();

  return api.get<PartnerStats>("/api/v1/partners/revenue/metrics", {
    params: {
      periodStart: resolvedPeriodStart,
      periodEnd: resolvedPeriodEnd,
    },
  });
}
