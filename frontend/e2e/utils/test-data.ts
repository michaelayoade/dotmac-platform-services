/**
 * Test data constants for E2E tests
 */

// Re-export auto-generated routes
export {
  ALL_ROUTES,
  DYNAMIC_ROUTES,
  STATIC_ROUTES,
  STATIC_AUTH_ROUTES,
  STATIC_DASHBOARD_ROUTES,
  STATIC_PARTNER_ROUTES,
  STATIC_PORTAL_ROUTES,
  ROUTE_COUNTS,
  type RouteInfo,
} from "./route-generator";

// Test user credentials
export const TEST_USERS = {
  admin: {
    email: process.env.TEST_ADMIN_EMAIL || "admin@test.local",
    password: process.env.TEST_ADMIN_PASSWORD || "TestPassword123!",
    name: "Test Admin",
    role: "admin",
  },
  partner: {
    email: process.env.TEST_PARTNER_EMAIL || "partner@test.local",
    password: process.env.TEST_PARTNER_PASSWORD || "TestPassword123!",
    name: "Test Partner",
    role: "partner_admin",
  },
  tenant: {
    email: process.env.TEST_TENANT_EMAIL || "tenant@test.local",
    password: process.env.TEST_TENANT_PASSWORD || "TestPassword123!",
    name: "Test Tenant User",
    role: "tenant_admin",
  },
  viewer: {
    email: process.env.TEST_VIEWER_EMAIL || "viewer@test.local",
    password: process.env.TEST_VIEWER_PASSWORD || "TestPassword123!",
    name: "Test Viewer",
    role: "viewer",
  },
} as const;

// Test tenants
export const TEST_TENANTS = {
  primary: {
    id: "tenant-001",
    name: "Acme Corporation",
    domain: "acme.local",
  },
  secondary: {
    id: "tenant-002",
    name: "Tech Industries",
    domain: "tech.local",
  },
} as const;

// Test invoices
export const TEST_INVOICES = {
  paid: {
    id: "inv-001",
    number: "INV-2024-001",
    amount: 125000,
    status: "paid",
  },
  pending: {
    id: "inv-002",
    number: "INV-2024-002",
    amount: 250000,
    status: "pending",
  },
  overdue: {
    id: "inv-003",
    number: "INV-2024-003",
    amount: 75000,
    status: "overdue",
  },
} as const;

// Test fixtures for dynamic routes
export const TEST_FIXTURES = {
  // IDs for dynamic route testing
  userId: "user-001",
  tenantId: "tenant-001",
  invoiceId: "inv-001",
  subscriptionId: "sub-001",
  partnerId: "partner-001",
  ticketId: "ticket-001",
  jobId: "job-001",
  workflowId: "workflow-001",
  deploymentId: "deploy-001",
  contactId: "contact-001",
  catalogId: "catalog-001",
  webhookId: "webhook-001",
  executionId: "exec-001",
} as const;

/**
 * Generate a testable URL for a dynamic route
 */
export function resolveDynamicRoute(
  route: string,
  fixtures: Partial<typeof TEST_FIXTURES> = TEST_FIXTURES
): string {
  return route
    .replace("[id]", fixtures.userId || "test-id")
    .replace("[userId]", fixtures.userId || "test-id")
    .replace("[tenantId]", fixtures.tenantId || "test-id")
    .replace("[invoiceId]", fixtures.invoiceId || "test-id")
    .replace("[subscriptionId]", fixtures.subscriptionId || "test-id")
    .replace("[partnerId]", fixtures.partnerId || "test-id")
    .replace("[ticketId]", fixtures.ticketId || "test-id")
    .replace("[jobId]", fixtures.jobId || "test-id")
    .replace("[workflowId]", fixtures.workflowId || "test-id")
    .replace("[deploymentId]", fixtures.deploymentId || "test-id")
    .replace("[contactId]", fixtures.contactId || "test-id")
    .replace("[catalogId]", fixtures.catalogId || "test-id")
    .replace("[webhookId]", fixtures.webhookId || "test-id")
    .replace("[executionId]", fixtures.executionId || "test-id")
    .replace("[name]", "test-feature")
    .replace("[category]", "general")
    .replace("[...path]", "test/path");
}

// URL patterns for quick access
export const PORTAL_URLS = {
  auth: {
    login: "/login",
    signup: "/signup",
    forgotPassword: "/forgot-password",
    resetPassword: "/reset-password",
    verifyEmail: "/verify-email",
  },
  dashboard: {
    home: "/",
    analytics: "/analytics",
    users: "/users",
    usersNew: "/users/new",
    tenants: "/tenants",
    tenantsNew: "/tenants/new",
    billing: "/billing",
    billingInvoices: "/billing/invoices",
    billingInvoicesNew: "/billing/invoices/new",
    billingSubscriptions: "/billing/subscriptions",
    billingPayments: "/billing/payments",
    settings: "/settings",
  },
  partner: {
    login: "/partner/login",
    apply: "/partner/apply",
    home: "/partner",
    commissions: "/partner/commissions",
    referrals: "/partner/referrals",
    statements: "/partner/statements",
    team: "/partner/team",
    settings: "/partner/settings",
  },
  portal: {
    login: "/portal/login",
    home: "/portal",
    billing: "/portal/billing",
    settings: "/portal/settings",
    team: "/portal/team",
    usage: "/portal/usage",
  },
} as const;
