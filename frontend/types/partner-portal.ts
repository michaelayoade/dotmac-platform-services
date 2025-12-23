// Partner Portal Types

export interface PartnerDashboardStats {
  totalRevenue: number;
  revenueChange: number;
  pendingCommissions: number;
  paidCommissions: number;
  activeCustomers: number;
  customerChange: number;
  conversionRate: number;
  totalReferrals: number;
  convertedReferrals: number;
}

export interface PartnerRevenueDataPoint {
  date: string;
  revenue: number;
}

export interface PartnerCommissionDataPoint {
  month: string;
  amount: number;
}

export interface PartnerDashboard {
  stats: PartnerDashboardStats;
  revenueHistory: PartnerRevenueDataPoint[];
  commissionHistory: PartnerCommissionDataPoint[];
}

// Referrals
export type ReferralStatus =
  | "NEW"
  | "CONTACTED"
  | "QUALIFIED"
  | "CONVERTED"
  | "LOST";

export interface Referral {
  id: string;
  companyName: string;
  contactName: string;
  contactEmail: string;
  contactPhone?: string;
  status: ReferralStatus;
  notes?: string;
  estimatedValue?: number;
  createdAt: string;
  updatedAt: string;
  convertedAt?: string;
  customerId?: string;
}

export interface CreateReferralRequest {
  companyName: string;
  contactName: string;
  contactEmail: string;
  contactPhone?: string;
  notes?: string;
  estimatedValue?: number;
}

export interface ReferralsResponse {
  referrals: Referral[];
  total: number;
  page: number;
  pageSize: number;
}

// Customers
export interface PartnerCustomer {
  id: string;
  tenantId: string;
  tenantName: string;
  contactName: string;
  contactEmail: string;
  status: "ACTIVE" | "CHURNED" | "SUSPENDED";
  engagementType: "REFERRAL" | "MANAGED" | "RESELLER";
  monthlyRevenue: number;
  totalRevenue: number;
  commissionRate: number;
  startDate: string;
  lastActivityAt: string;
}

export interface PartnerCustomersResponse {
  customers: PartnerCustomer[];
  total: number;
  page: number;
  pageSize: number;
}

// Commissions
export type CommissionStatus = "PENDING" | "APPROVED" | "PAID" | "CANCELLED";

export interface Commission {
  id: string;
  customerId: string;
  customerName: string;
  period: string;
  baseAmount: number;
  commissionRate: number;
  commissionAmount: number;
  status: CommissionStatus;
  approvedAt?: string;
  paidAt?: string;
  createdAt: string;
}

export interface CommissionsResponse {
  commissions: Commission[];
  total: number;
  page: number;
  pageSize: number;
  summary: {
    totalPending: number;
    totalApproved: number;
    totalPaid: number;
  };
}

// Statements
export interface Statement {
  id: string;
  period: string;
  startDate: string;
  endDate: string;
  totalRevenue: number;
  totalCommissions: number;
  status: "DRAFT" | "FINAL" | "PAID";
  paidAt?: string;
  downloadUrl?: string;
  createdAt: string;
}

export interface Payout {
  id: string;
  statementId: string;
  amount: number;
  method: "BANK_TRANSFER" | "CHECK" | "PAYPAL";
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
  reference?: string;
  processedAt?: string;
  createdAt: string;
}

export interface StatementsResponse {
  statements: Statement[];
  total: number;
  page: number;
  pageSize: number;
}

export interface PayoutsResponse {
  payouts: Payout[];
  total: number;
}

// Partner Profile
export interface PartnerProfile {
  id: string;
  companyName: string;
  contactName: string;
  contactEmail: string;
  contactPhone?: string;
  address?: {
    street?: string;
    city?: string;
    state?: string;
    postalCode?: string;
    country?: string;
  };
  payoutPreferences: {
    method: "BANK_TRANSFER" | "CHECK" | "PAYPAL";
    bankAccountNumber?: string;
    bankRoutingNumber?: string;
    paypalEmail?: string;
  };
  notificationSettings: {
    emailNewReferral: boolean;
    emailCommissionApproved: boolean;
    emailPayoutProcessed: boolean;
    emailMonthlyStatement: boolean;
  };
  commissionRate: number;
  tier: "BRONZE" | "SILVER" | "GOLD" | "PLATINUM";
  joinedAt: string;
}

export interface UpdatePartnerProfileRequest {
  companyName?: string;
  contactName?: string;
  contactPhone?: string;
  address?: PartnerProfile["address"];
  payoutPreferences?: PartnerProfile["payoutPreferences"];
  notificationSettings?: PartnerProfile["notificationSettings"];
}
