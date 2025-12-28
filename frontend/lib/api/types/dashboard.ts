/**
 * Shared TypeScript types for dashboard API responses.
 * All dashboard endpoints return a consistent structure with:
 * - summary: Key statistics
 * - charts: Data for visualizations
 * - alerts: Actionable warnings/errors
 * - recentActivity: Latest items
 * - generatedAt: Timestamp
 */

// ============================================================================
// Common Types
// ============================================================================

export interface ChartDataPoint {
  label: string;
  value: number;
  metadata?: Record<string, unknown>;
}

export interface DashboardAlert {
  type: "info" | "warning" | "error";
  title: string;
  message: string;
  count: number;
  actionUrl?: string;
}

export interface RecentActivityItem {
  id: string;
  type: string;
  description: string;
  status: string;
  timestamp: string;
  amount?: number;
  tenantId?: string;
}

export interface BaseDashboardResponse<TSummary, TCharts> {
  summary: TSummary;
  charts: TCharts;
  alerts: DashboardAlert[];
  recentActivity: RecentActivityItem[];
  generatedAt: string;
}

// ============================================================================
// Billing Dashboard
// ============================================================================

export interface BillingSummary {
  totalRevenue: number;
  revenueThisMonth: number;
  revenueLastMonth: number;
  revenueChangePct: number;
  totalInvoices: number;
  openInvoices: number;
  overdueInvoices: number;
  activeSubscriptions: number;
  mrr: number;
  outstandingBalance: number;
}

export interface BillingCharts {
  revenueTrend: ChartDataPoint[];
  invoicesByStatus: ChartDataPoint[];
  subscriptionsByPlan: ChartDataPoint[];
  paymentMethods: ChartDataPoint[];
}

export type BillingDashboardResponse = BaseDashboardResponse<BillingSummary, BillingCharts>;

// ============================================================================
// Tenant Dashboard
// ============================================================================

export interface TenantSummary {
  totalTenants: number;
  activeTenants: number;
  trialTenants: number;
  suspendedTenants: number;
  newThisMonth: number;
  churnedThisMonth: number;
  growthRatePct: number;
}

export interface TenantCharts {
  tenantGrowth: ChartDataPoint[];
  tenantsByStatus: ChartDataPoint[];
  tenantsByPlan: ChartDataPoint[];
  activityTrend: ChartDataPoint[];
}

export type TenantDashboardResponse = BaseDashboardResponse<TenantSummary, TenantCharts>;

// ============================================================================
// User Dashboard
// ============================================================================

export interface UserSummary {
  totalUsers: number;
  activeUsers: number;
  inactiveUsers: number;
  verifiedUsers: number;
  unverifiedUsers: number;
  newThisMonth: number;
  activeToday: number;
  growthRatePct: number;
}

export interface UserCharts {
  userGrowth: ChartDataPoint[];
  usersByStatus: ChartDataPoint[];
  usersByRole: ChartDataPoint[];
  activityTrend: ChartDataPoint[];
}

export type UserDashboardResponse = BaseDashboardResponse<UserSummary, UserCharts>;

// ============================================================================
// Partner Dashboard
// ============================================================================

export interface PartnerSummary {
  totalPartners: number;
  activePartners: number;
  pendingPartners: number;
  suspendedPartners: number;
  newThisMonth: number;
  pendingApplications: number;
  totalReferrals: number;
  convertedReferrals: number;
  conversionRatePct: number;
  totalCommissions: number;
}

export interface PartnerCharts {
  partnerGrowth: ChartDataPoint[];
  partnersByStatus: ChartDataPoint[];
  referralsTrend: ChartDataPoint[];
  commissionsTrend: ChartDataPoint[];
}

export type PartnerDashboardResponse = BaseDashboardResponse<PartnerSummary, PartnerCharts>;

// ============================================================================
// Licensing Dashboard
// ============================================================================

export interface LicensingSummary {
  totalModules: number;
  activeModules: number;
  totalPlans: number;
  activePlans: number;
  publicPlans: number;
  totalQuotas: number;
  totalSubscriptions: number;
  activeSubscriptions: number;
  trialSubscriptions: number;
}

export interface LicensingCharts {
  subscriptionsByStatus: ChartDataPoint[];
  subscriptionsByPlan: ChartDataPoint[];
  modulesByCategory: ChartDataPoint[];
  subscriptionTrend: ChartDataPoint[];
}

export type LicensingDashboardResponse = BaseDashboardResponse<LicensingSummary, LicensingCharts>;

// ============================================================================
// Communications Dashboard
// ============================================================================

export interface CommunicationsSummary {
  totalSent: number;
  sentToday: number;
  sentThisWeek: number;
  delivered: number;
  failed: number;
  pending: number;
  deliveryRatePct: number;
  totalTemplates: number;
  activeTemplates: number;
}

export interface CommunicationsCharts {
  byStatus: ChartDataPoint[];
  byType: ChartDataPoint[];
  dailyTrend: ChartDataPoint[];
  topTemplates: ChartDataPoint[];
}

export interface CommsRecentActivity extends RecentActivityItem {
  recipient: string;
  subject?: string;
}

export interface CommunicationsDashboardResponse {
  summary: CommunicationsSummary;
  charts: CommunicationsCharts;
  alerts: DashboardAlert[];
  recentActivity: CommsRecentActivity[];
  generatedAt: string;
}

// ============================================================================
// Tickets Dashboard
// ============================================================================

export interface TicketsSummary {
  totalTickets: number;
  openTickets: number;
  inProgressTickets: number;
  waitingTickets: number;
  resolvedTickets: number;
  closedTickets: number;
  slaBreached: number;
  avgResolutionTimeHours: number | null;
}

export interface TicketsCharts {
  ticketsByStatus: ChartDataPoint[];
  ticketsByPriority: ChartDataPoint[];
  ticketsTrend: ChartDataPoint[];
  resolutionTrend: ChartDataPoint[];
}

export interface TicketRecentActivity extends RecentActivityItem {
  priority: string;
}

export interface TicketsDashboardResponse {
  summary: TicketsSummary;
  charts: TicketsCharts;
  alerts: DashboardAlert[];
  recentActivity: TicketRecentActivity[];
  generatedAt: string;
}

// ============================================================================
// Jobs Dashboard
// ============================================================================

export interface JobsSummary {
  totalJobs: number;
  pendingJobs: number;
  runningJobs: number;
  completedJobs: number;
  failedJobs: number;
  cancelledJobs: number;
  successRatePct: number;
  avgDurationSeconds: number | null;
}

export interface JobsCharts {
  jobsByStatus: ChartDataPoint[];
  jobsByType: ChartDataPoint[];
  jobsTrend: ChartDataPoint[];
  successTrend: ChartDataPoint[];
}

export interface JobRecentActivity extends RecentActivityItem {
  progress: number;
}

export interface JobsDashboardResponse {
  summary: JobsSummary;
  charts: JobsCharts;
  alerts: DashboardAlert[];
  recentActivity: JobRecentActivity[];
  generatedAt: string;
}

// ============================================================================
// Workflows Dashboard
// ============================================================================

export interface WorkflowsSummary {
  totalWorkflows: number;
  activeWorkflows: number;
  totalExecutions: number;
  pendingExecutions: number;
  runningExecutions: number;
  completedExecutions: number;
  failedExecutions: number;
  successRatePct: number;
}

export interface WorkflowsCharts {
  executionsByStatus: ChartDataPoint[];
  executionsByWorkflow: ChartDataPoint[];
  executionsTrend: ChartDataPoint[];
  successTrend: ChartDataPoint[];
}

export interface WorkflowRecentActivity extends RecentActivityItem {
  workflowId?: number;
}

export interface WorkflowsDashboardResponse {
  summary: WorkflowsSummary;
  charts: WorkflowsCharts;
  alerts: DashboardAlert[];
  recentActivity: WorkflowRecentActivity[];
  generatedAt: string;
}

// ============================================================================
// Audit Dashboard
// ============================================================================

export interface AuditSummary {
  totalActivities: number;
  activitiesToday: number;
  activitiesThisWeek: number;
  criticalEvents: number;
  highEvents: number;
  authFailures: number;
  permissionChanges: number;
  dataExports: number;
}

export interface AuditCharts {
  activitiesByType: ChartDataPoint[];
  activitiesBySeverity: ChartDataPoint[];
  activitiesTrend: ChartDataPoint[];
  topUsers: ChartDataPoint[];
}

export interface AuditRecentActivity extends RecentActivityItem {
  activityType: string;
  action: string;
  severity: string;
  userId?: string;
}

export interface AuditDashboardResponse {
  summary: AuditSummary;
  charts: AuditCharts;
  alerts: DashboardAlert[];
  recentActivity: AuditRecentActivity[];
  generatedAt: string;
}

// ============================================================================
// Dashboard Query Params
// ============================================================================

export interface DashboardQueryParams {
  periodMonths?: number;
  periodDays?: number;
}
