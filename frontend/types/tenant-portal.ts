// Tenant Portal Types

export interface TenantDashboardStats {
  activeUsers: number;
  maxUsers: number;
  apiCallsThisMonth: number;
  apiCallsLimit: number;
  storageUsedMb: number;
  storageLimitMb: number;
  daysUntilRenewal: number;
  planName: string;
  planType: "FREE" | "STARTER" | "PROFESSIONAL" | "ENTERPRISE";
}

export interface TenantDashboard {
  stats: TenantDashboardStats;
  recentActivity: TenantActivity[];
}

export interface TenantActivity {
  id: string;
  type: "user_joined" | "user_removed" | "role_changed" | "settings_updated" | "plan_upgraded";
  description: string;
  userId?: string;
  userName?: string;
  createdAt: string;
}

// Team Members
export type MemberRole = "tenant_admin" | "member" | "viewer";
export type MemberStatus = "ACTIVE" | "PENDING" | "SUSPENDED";

export interface TeamMember {
  id: string;
  userId: string;
  email: string;
  fullName: string;
  role: MemberRole;
  status: MemberStatus;
  avatarUrl?: string;
  lastActiveAt?: string;
  joinedAt: string;
}

export interface TeamMembersResponse {
  members: TeamMember[];
  total: number;
  page: number;
  pageSize: number;
}

export interface Invitation {
  id: string;
  email: string;
  role: MemberRole;
  status: "PENDING" | "ACCEPTED" | "EXPIRED" | "CANCELLED";
  invitedBy: string;
  invitedByName: string;
  expiresAt: string;
  createdAt: string;
}

export interface InvitationsResponse {
  invitations: Invitation[];
  total: number;
}

export interface InviteMemberRequest {
  email: string;
  role: MemberRole;
  sendEmail?: boolean;
}

export interface UpdateMemberRoleRequest {
  role: MemberRole;
}

// Billing
export interface CurrentSubscription {
  id: string;
  planName: string;
  planType: "FREE" | "STARTER" | "PROFESSIONAL" | "ENTERPRISE";
  status: "ACTIVE" | "CANCELLED" | "PAST_DUE" | "TRIALING";
  currentPeriodStart: string;
  currentPeriodEnd: string;
  cancelAtPeriodEnd: boolean;
  monthlyPrice: number;
  billingInterval: "monthly" | "yearly";
  trialEndsAt?: string;
}

export interface Invoice {
  id: string;
  number: string;
  status: "DRAFT" | "OPEN" | "PAID" | "VOID" | "UNCOLLECTIBLE";
  amountDue: number;
  amountPaid: number;
  currency: string;
  periodStart: string;
  periodEnd: string;
  dueDate?: string;
  paidAt?: string;
  downloadUrl?: string;
  createdAt: string;
}

export interface InvoicesResponse {
  invoices: Invoice[];
  total: number;
  page: number;
  pageSize: number;
}

export interface PaymentMethod {
  id: string;
  type: "card" | "bank_account";
  isDefault: boolean;
  card?: {
    brand: string;
    last4: string;
    expMonth: number;
    expYear: number;
  };
  bankAccount?: {
    bankName: string;
    last4: string;
  };
  createdAt: string;
}

export interface BillingInfo {
  subscription: CurrentSubscription;
  invoices: Invoice[];
  paymentMethods: PaymentMethod[];
  upcomingInvoice?: {
    amountDue: number;
    dueDate: string;
  };
}

// Usage
export interface UsageMetrics {
  apiCalls: UsageMetric;
  storage: UsageMetric;
  users: UsageMetric;
  bandwidth: UsageMetric;
}

export interface UsageMetric {
  current: number;
  limit: number;
  unit: string;
  percentUsed: number;
  history: UsageDataPoint[];
}

export interface UsageDataPoint {
  date: string;
  value: number;
}

export interface UsageBreakdown {
  byFeature: FeatureUsage[];
  byUser: UserUsage[];
}

export interface FeatureUsage {
  feature: string;
  calls: number;
  percentage: number;
}

export interface UserUsage {
  userId: string;
  userName: string;
  apiCalls: number;
  storageUsed: number;
}

// Settings
export interface TenantSettings {
  general: {
    name: string;
    slug: string;
    industry?: string;
    timezone: string;
    dateFormat: string;
    language: string;
  };
  branding: {
    logoUrl?: string;
    primaryColor?: string;
    accentColor?: string;
  };
  security: {
    mfaRequired: boolean;
    sessionTimeout: number;
    ipWhitelist: string[];
    allowedDomains: string[];
  };
  features: {
    [key: string]: boolean;
  };
}

export interface UpdateTenantSettingsRequest {
  general?: Partial<TenantSettings["general"]>;
  branding?: Partial<TenantSettings["branding"]>;
  security?: Partial<TenantSettings["security"]>;
  features?: Partial<TenantSettings["features"]>;
}

// API Keys
export interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  lastUsedAt?: string;
  expiresAt?: string;
  createdAt: string;
  createdBy: string;
}

export interface CreateApiKeyRequest {
  name: string;
  expiresInDays?: number;
}

export interface CreateApiKeyResponse {
  apiKey: ApiKey;
  secretKey: string; // Only returned once on creation
}
