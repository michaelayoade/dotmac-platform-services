import { Page, Route } from "@playwright/test";

const API_BASE = process.env.PLAYWRIGHT_API_URL || "http://localhost:8000";

/**
 * Mock API responses for testing without backend
 */
export const API_MOCKS: Record<string, unknown> = {
  // Auth - current user
  "api/v1/auth/me": {
    id: "test-user-id",
    email: "admin@test.local",
    name: "Test Admin",
    role: "admin",
    roles: ["admin"],
    permissions: ["*:*"],
    tenantId: "test-tenant-id",
    isPlatformAdmin: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },

  // Billing metrics
  "api/v1/billing/metrics": {
    mrr: 1250000,
    arr: 15000000,
    outstanding: 450000,
    collectionRate: 94.5,
    overdueCount: 3,
    activeSubscriptions: 156,
    churnedThisMonth: 2,
    upgradesThisMonth: 8,
  },
  // Billing payments
  "api/v1/billing/payments": {
    payments: [
      {
        id: "pay-001",
        customerId: "cust-001",
        customerName: "Acme Corp",
        invoiceId: "inv-001",
        invoiceNumber: "INV-2024-001",
        amount: 125000,
        currency: "USD",
        method: "card",
        status: "completed",
        paymentDate: new Date().toISOString(),
        createdAt: new Date().toISOString(),
      },
    ],
    total: 1,
    page: 1,
    pageSize: 20,
    pageCount: 1,
  },

  // Invoices list
  "api/v1/billing/invoices": {
    items: [
      {
        id: "inv-001",
        number: "INV-2024-001",
        customer: { id: "cust-001", name: "Acme Corp", email: "billing@acme.com" },
        amount: 125000,
        status: "paid",
        currency: "USD",
        dueDate: new Date().toISOString(),
        createdAt: new Date().toISOString(),
        lineItems: [
          {
            description: "Pro plan",
            quantity: 1,
            unitPrice: 125000,
            amount: 125000,
          },
        ],
      },
      {
        id: "inv-002",
        number: "INV-2024-002",
        customer: { id: "cust-002", name: "Tech Inc", email: "billing@tech.com" },
        amount: 250000,
        status: "pending",
        currency: "USD",
        dueDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        createdAt: new Date().toISOString(),
        lineItems: [
          {
            description: "Enterprise plan",
            quantity: 1,
            unitPrice: 250000,
            amount: 250000,
          },
        ],
      },
    ],
    total: 2,
    page: 1,
    pageSize: 20,
  },

  // Subscriptions list
  "api/v1/billing/subscriptions": {
    items: [
      {
        id: "sub-001",
        customerId: "cust-001",
        customerName: "Acme Corp",
        planName: "Professional",
        status: "active",
        currentPeriodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        amount: 9900,
      },
    ],
    total: 1,
    page: 1,
    pageSize: 20,
  },

  // Users list
  "api/v1/users": {
    items: [
      {
        id: "user-001",
        email: "admin@test.local",
        name: "Test Admin",
        role: "admin",
        status: "active",
        createdAt: new Date().toISOString(),
      },
      {
        id: "user-002",
        email: "user@test.local",
        name: "Test User",
        role: "user",
        status: "active",
        createdAt: new Date().toISOString(),
      },
    ],
    total: 2,
    page: 1,
    pageSize: 20,
  },

  // Tenants list
  "api/v1/tenants": {
    items: [
      {
        id: "tenant-001",
        name: "Acme Corporation",
        domain: "acme.local",
        status: "active",
        plan: "professional",
        userCount: 15,
        createdAt: new Date().toISOString(),
      },
      {
        id: "tenant-002",
        name: "Tech Industries",
        domain: "tech.local",
        status: "active",
        plan: "enterprise",
        userCount: 45,
        createdAt: new Date().toISOString(),
      },
    ],
    total: 2,
    page: 1,
    pageSize: 20,
  },

  // Partners list
  "api/v1/partners": {
    items: [
      {
        id: "partner-001",
        name: "Partner Solutions",
        email: "contact@partnersolutions.com",
        status: "active",
        commissionRate: 15,
        totalReferrals: 12,
        totalEarnings: 450000,
        createdAt: new Date().toISOString(),
      },
    ],
    total: 1,
    page: 1,
    pageSize: 20,
  },

  // Deployments list
  "api/v1/deployments": {
    items: [
      {
        id: "deploy-001",
        name: "Production",
        status: "running",
        environment: "production",
        version: "1.2.3",
        lastDeployedAt: new Date().toISOString(),
      },
    ],
    total: 1,
    page: 1,
    pageSize: 20,
  },
  // Partner portal dashboard
  "api/v1/partners/portal/dashboard": {
    stats: {
      totalTenants: 4,
      activeTenants: 3,
      totalRevenueGenerated: 125000,
      totalCommissionsEarned: 18500,
      totalCommissionsPaid: 12000,
      pendingCommissions: 6500,
      totalReferrals: 24,
      convertedReferrals: 12,
      pendingReferrals: 8,
      conversionRate: 50,
      currentTier: "Gold",
      commissionModel: "Revenue share",
      defaultCommissionRate: 15,
    },
    revenueHistory: [
      { date: "Jan", revenue: 12000 },
      { date: "Feb", revenue: 13500 },
      { date: "Mar", revenue: 14200 },
      { date: "Apr", revenue: 15100 },
      { date: "May", revenue: 16000 },
      { date: "Jun", revenue: 17200 },
    ],
    commissionHistory: [
      { month: "Jan", amount: 1800 },
      { month: "Feb", amount: 2050 },
      { month: "Mar", amount: 2200 },
      { month: "Apr", amount: 2300 },
      { month: "May", amount: 2500 },
      { month: "Jun", amount: 2650 },
    ],
  },
  "api/v1/partners/portal/referrals": {
    referrals: [
      {
        id: "ref-001",
        companyName: "Acme Corp",
        contactName: "Jane Doe",
        contactEmail: "jane@acme.com",
        status: "QUALIFIED",
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
    ],
    total: 1,
    page: 1,
    pageSize: 20,
  },
  "api/v1/partners/portal/tenants": {
    tenants: [
      {
        id: "pt-001",
        tenantId: "tenant-001",
        tenantName: "Acme Corp",
        engagementType: "Referral",
        totalRevenue: 45000,
        totalCommissions: 6750,
        commissionRate: 15,
        startDate: new Date().toISOString(),
        isActive: true,
      },
    ],
    total: 1,
    page: 1,
    pageSize: 20,
  },
  "api/v1/partners/portal/commissions": {
    commissions: [
      {
        id: "com-001",
        tenantId: "tenant-001",
        tenantName: "Acme Corp",
        period: "2024-06",
        baseAmount: 12000,
        commissionRate: 15,
        commissionAmount: 1800,
        status: "PAID",
        paidAt: new Date().toISOString(),
        createdAt: new Date().toISOString(),
      },
    ],
    total: 1,
    page: 1,
    pageSize: 20,
    summary: {
      totalPending: 0,
      totalApproved: 0,
      totalPaid: 1800,
    },
  },
  "api/v1/partners/portal/statements": {
    statements: [
      {
        id: "stmt-001",
        period: "2024-06",
        startDate: new Date().toISOString(),
        endDate: new Date().toISOString(),
        totalRevenue: 12000,
        totalCommissions: 1800,
        status: "PAID",
        paidAt: new Date().toISOString(),
        createdAt: new Date().toISOString(),
      },
    ],
    total: 1,
    page: 1,
    pageSize: 20,
  },
  "api/v1/partners/portal/profile": {
    id: "partner-001",
    companyName: "Partner Solutions",
    contactName: "Jane Doe",
    contactEmail: "jane@partner.com",
    commissionRate: 15,
    tier: "GOLD",
    joinedAt: new Date().toISOString(),
    payoutPreferences: { method: "BANK_TRANSFER" },
    notificationSettings: {
      emailNewReferral: true,
      emailCommissionApproved: true,
      emailPayoutProcessed: true,
      emailMonthlyStatement: true,
    },
  },
  "api/v1/partners/portal/users": {
    users: [
      {
        id: "partner-user-1",
        partnerId: "partner-001",
        userId: "user-1",
        firstName: "Partner",
        lastName: "Admin",
        fullName: "Partner Admin",
        email: "partner@dotmac.com",
        role: "partner_admin",
        isPrimaryContact: true,
        isActive: true,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
    ],
  },
  "api/v1/partners/portal/invitations": {
    invitations: [
      {
        id: "partner-invite-1",
        partnerId: "partner-001",
        email: "invitee@partner.com",
        role: "partner_admin",
        status: "pending",
        invitedBy: "Partner Admin",
        createdAt: new Date().toISOString(),
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      },
    ],
  },
  // Tenant portal
  "api/v1/tenants/portal/dashboard": {
    stats: {
      activeUsers: 12,
      maxUsers: 25,
      apiCallsThisMonth: 45000,
      apiCallsLimit: 100000,
      storageUsedMb: 1200,
      storageLimitMb: 5000,
      daysUntilRenewal: 18,
      planName: "Professional",
      planType: "PROFESSIONAL",
    },
    recentActivity: [
      {
        id: "act-1",
        type: "user_joined",
        description: "Alex Johnson joined your workspace",
        createdAt: new Date().toISOString(),
      },
    ],
  },
  "api/v1/tenants/portal/billing": {
    subscription: {
      id: "sub-001",
      planName: "Professional",
      planType: "PROFESSIONAL",
      status: "ACTIVE",
      currentPeriodStart: new Date().toISOString(),
      currentPeriodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      cancelAtPeriodEnd: false,
      monthlyPrice: 9900,
      billingInterval: "monthly",
    },
    invoices: [
      {
        id: "tp-inv-1",
        number: "INV-2024-001",
        status: "PAID",
        amountDue: 0,
        amountPaid: 9900,
        currency: "USD",
        periodStart: new Date().toISOString(),
        periodEnd: new Date().toISOString(),
        paidAt: new Date().toISOString(),
        createdAt: new Date().toISOString(),
      },
    ],
    paymentMethods: [],
  },
  "api/v1/tenants/portal/invoices": {
    invoices: [
      {
        id: "tp-inv-1",
        number: "INV-2024-001",
        status: "PAID",
        amountDue: 0,
        amountPaid: 9900,
        currency: "USD",
        periodStart: new Date().toISOString(),
        periodEnd: new Date().toISOString(),
        paidAt: new Date().toISOString(),
        createdAt: new Date().toISOString(),
      },
    ],
    total: 1,
    page: 1,
    pageSize: 20,
  },
  "api/v1/tenants/portal/usage": {
    apiCalls: {
      current: 45000,
      limit: 100000,
      unit: "calls",
      percentUsed: 45,
      history: [{ date: "2024-06-01", value: 1500 }],
    },
    storage: {
      current: 1200,
      limit: 5000,
      unit: "MB",
      percentUsed: 24,
      history: [{ date: "2024-06-01", value: 300 }],
    },
    users: {
      current: 12,
      limit: 25,
      unit: "users",
      percentUsed: 48,
      history: [{ date: "2024-06-01", value: 10 }],
    },
    bandwidth: {
      current: 320,
      limit: 1000,
      unit: "GB",
      percentUsed: 32,
      history: [{ date: "2024-06-01", value: 50 }],
    },
  },
  "api/v1/tenants/portal/usage/breakdown": {
    byFeature: [
      { feature: "API", calls: 30000, percentage: 66 },
      { feature: "Webhooks", calls: 15000, percentage: 34 },
    ],
    byUser: [
      { userId: "user-1", userName: "Alex Johnson", apiCalls: 12000, storageUsed: 200 },
    ],
  },
  "api/v1/tenants/portal/settings": {
    general: {
      name: "Acme Corp",
      slug: "acme",
      timezone: "UTC",
      dateFormat: "YYYY-MM-DD",
      language: "en",
    },
    branding: {},
    security: {
      mfaRequired: false,
      sessionTimeout: 30,
      ipWhitelist: [],
      allowedDomains: [],
    },
    features: {
      advancedAnalytics: false,
      customIntegrations: false,
      apiAccess: true,
    },
  },
  "api/v1/tenants/portal/members": {
    members: [
      {
        id: "member-1",
        userId: "user-1",
        email: "alex@acme.com",
        fullName: "Alex Johnson",
        role: "tenant_admin",
        status: "ACTIVE",
        joinedAt: new Date().toISOString(),
      },
    ],
    total: 1,
    page: 1,
    pageSize: 20,
  },
  "api/v1/tenants/portal/invitations": {
    invitations: [
      {
        id: "invite-1",
        email: "invitee@acme.com",
        role: "member",
        status: "PENDING",
        invitedBy: "Alex Johnson",
        invitedByName: "Alex Johnson",
        createdAt: new Date().toISOString(),
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      },
    ],
    total: 1,
  },
  "api/v1/tenants/portal/api-keys": [
    {
      id: "key-1",
      name: "Primary API Key",
      prefix: "dmk",
      createdAt: new Date().toISOString(),
      createdBy: "Alex Johnson",
    },
  ],

  // Tickets list
  "api/v1/tickets": {
    items: [
      {
        id: "ticket-001",
        subject: "Help with integration",
        status: "open",
        priority: "medium",
        createdAt: new Date().toISOString(),
      },
    ],
    total: 1,
    page: 1,
    pageSize: 20,
  },

  // Jobs list
  "api/v1/jobs": {
    items: [
      {
        id: "job-001",
        name: "Daily backup",
        status: "completed",
        lastRunAt: new Date().toISOString(),
        nextRunAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      },
    ],
    total: 1,
    page: 1,
    pageSize: 20,
  },

  // Workflows list
  "api/v1/workflows": {
    items: [
      {
        id: "workflow-001",
        name: "Onboarding",
        status: "active",
        executionCount: 42,
        createdAt: new Date().toISOString(),
      },
    ],
    total: 1,
    page: 1,
    pageSize: 20,
  },

  // Contacts list
  "api/v1/contacts": {
    items: [
      {
        id: "contact-001",
        name: "John Doe",
        email: "john@example.com",
        company: "Acme Corp",
        phone: "+1234567890",
        createdAt: new Date().toISOString(),
      },
    ],
    total: 1,
    page: 1,
    pageSize: 20,
  },

  // Analytics overview
  "api/v1/analytics/overview": {
    totalUsers: 1250,
    activeUsers: 890,
    totalRevenue: 15000000,
    growthRate: 12.5,
    topProducts: [
      { name: "Professional", count: 450 },
      { name: "Enterprise", count: 125 },
    ],
  },

  // Monitoring health
  "api/v1/monitoring/health": {
    status: "healthy",
    services: [
      { name: "API", status: "healthy", latency: 45 },
      { name: "Database", status: "healthy", latency: 12 },
      { name: "Cache", status: "healthy", latency: 3 },
    ],
  },
};

/**
 * Setup API mocks for a page
 */
export async function setupApiMocks(
  page: Page,
  customMocks: Record<string, unknown> = {}
): Promise<void> {
  const allMocks = { ...API_MOCKS, ...customMocks };

  await page.route(`${API_BASE}/api/**`, async (route: Route) => {
    const url = route.request().url();
    const path = new URL(url).pathname;

    // Find matching mock
    for (const [mockPath, mockData] of Object.entries(allMocks)) {
      if (path.includes(mockPath)) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockData),
        });
        return;
      }
    }

    // Pass through if no mock found
    await route.continue();
  });
}

/**
 * Mock a specific API error
 */
export async function mockApiError(
  page: Page,
  path: string,
  status: number,
  message: string
): Promise<void> {
  await page.route(`**/${path}`, async (route) => {
    await route.fulfill({
      status,
      contentType: "application/json",
      body: JSON.stringify({
        error_code: "TEST_ERROR",
        message,
        status,
      }),
    });
  });
}

/**
 * Mock authentication success
 */
export async function mockAuthSuccess(page: Page): Promise<void> {
  await page.route("**/api/v1/auth/login/cookie", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        access_token: "mock_access_token",
        token_type: "bearer",
        user: API_MOCKS["api/v1/auth/me"],
      }),
      headers: {
        "Set-Cookie": "access_token=mock_access_token; Path=/; HttpOnly",
      },
    });
  });
}

/**
 * Mock authentication failure
 */
export async function mockAuthFailure(page: Page, message: string = "Invalid credentials"): Promise<void> {
  await page.route("**/api/v1/auth/login/cookie", async (route) => {
    await route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({
        detail: message,
      }),
    });
  });
}

/**
 * Mock 2FA required response
 */
export async function mock2FARequired(page: Page, userId: string = "test-user-id"): Promise<void> {
  await page.route("**/api/v1/auth/login/cookie", async (route) => {
    const origin = route.request().headers()["origin"] || "http://localhost:3000";
    await route.fulfill({
      status: 403,
      contentType: "application/json",
      body: JSON.stringify({
        detail: "2FA verification required",
      }),
      headers: {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Expose-Headers": "X-2FA-Required, X-User-ID",
        "X-2FA-Required": "true",
        "X-User-ID": userId,
      },
    });
  });
}

/**
 * Mock 2FA verification success
 */
export async function mock2FAVerifySuccess(page: Page): Promise<void> {
  await page.route("**/api/v1/auth/login/verify-2fa", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        access_token: "mock_access_token",
        token_type: "bearer",
        user: API_MOCKS["api/v1/auth/me"],
      }),
      headers: {
        "Set-Cookie": "access_token=mock_access_token; Path=/; HttpOnly",
      },
    });
  });
}
