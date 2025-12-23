// Query Keys Factory
// Centralized query key management for React Query
// Hierarchical structure enables granular cache invalidation

import type { ListQueryParams } from "@/types/api";

export const queryKeys = {
  // Auth module
  auth: {
    all: ["auth"] as const,
    me: () => [...queryKeys.auth.all, "me"] as const,
    sessions: () => [...queryKeys.auth.all, "sessions"] as const,
  },

  // Users module
  users: {
    all: ["users"] as const,
    lists: () => [...queryKeys.users.all, "list"] as const,
    list: (params?: ListQueryParams) =>
      [...queryKeys.users.lists(), params] as const,
    details: () => [...queryKeys.users.all, "detail"] as const,
    detail: (id: string) => [...queryKeys.users.details(), id] as const,
  },

  // Tenants module
  tenants: {
    all: ["tenants"] as const,
    lists: () => [...queryKeys.tenants.all, "list"] as const,
    list: (params?: ListQueryParams) =>
      [...queryKeys.tenants.lists(), params] as const,
    details: () => [...queryKeys.tenants.all, "detail"] as const,
    detail: (id: string) => [...queryKeys.tenants.details(), id] as const,
    current: () => [...queryKeys.tenants.all, "current"] as const,
    stats: (id: string) => [...queryKeys.tenants.detail(id), "stats"] as const,
    settings: (id: string) =>
      [...queryKeys.tenants.detail(id), "settings"] as const,
  },

  // Billing module
  billing: {
    all: ["billing"] as const,
    metrics: () => [...queryKeys.billing.all, "metrics"] as const,
    invoices: {
      all: () => [...queryKeys.billing.all, "invoices"] as const,
      list: (params?: ListQueryParams) =>
        [...queryKeys.billing.invoices.all(), "list", params] as const,
      detail: (id: string) =>
        [...queryKeys.billing.invoices.all(), "detail", id] as const,
    },
    subscriptions: {
      all: () => [...queryKeys.billing.all, "subscriptions"] as const,
      list: (params?: ListQueryParams) =>
        [...queryKeys.billing.subscriptions.all(), "list", params] as const,
      detail: (id: string) =>
        [...queryKeys.billing.subscriptions.all(), "detail", id] as const,
    },
    payments: {
      all: () => [...queryKeys.billing.all, "payments"] as const,
      list: (params?: ListQueryParams) =>
        [...queryKeys.billing.payments.all(), "list", params] as const,
      detail: (id: string) =>
        [...queryKeys.billing.payments.all(), "detail", id] as const,
    },
  },

  // Customers module
  customers: {
    all: ["customers"] as const,
    lists: () => [...queryKeys.customers.all, "list"] as const,
    list: (params?: ListQueryParams) =>
      [...queryKeys.customers.lists(), params] as const,
    details: () => [...queryKeys.customers.all, "detail"] as const,
    detail: (id: string) => [...queryKeys.customers.details(), id] as const,
    metrics: (id: string) =>
      [...queryKeys.customers.detail(id), "metrics"] as const,
  },

  // Deployments module
  deployments: {
    all: ["deployments"] as const,
    lists: () => [...queryKeys.deployments.all, "list"] as const,
    list: (params?: ListQueryParams) =>
      [...queryKeys.deployments.lists(), params] as const,
    details: () => [...queryKeys.deployments.all, "detail"] as const,
    detail: (id: string) => [...queryKeys.deployments.details(), id] as const,
    status: (id: string) =>
      [...queryKeys.deployments.detail(id), "status"] as const,
    logs: (id: string) =>
      [...queryKeys.deployments.detail(id), "logs"] as const,
  },

  // Analytics module
  analytics: {
    all: ["analytics"] as const,
    dashboard: () => [...queryKeys.analytics.all, "dashboard"] as const,
    revenue: (range?: { start: string; end: string }) =>
      [...queryKeys.analytics.all, "revenue", range] as const,
    activity: () => [...queryKeys.analytics.all, "activity"] as const,
    metrics: (type: string) =>
      [...queryKeys.analytics.all, "metrics", type] as const,
  },

  // System health
  health: {
    all: ["health"] as const,
    status: () => [...queryKeys.health.all, "status"] as const,
    services: () => [...queryKeys.health.all, "services"] as const,
  },

  // Notifications module
  notifications: {
    all: ["notifications"] as const,
    list: (params?: { unreadOnly?: boolean; page?: number; pageSize?: number }) =>
      [...queryKeys.notifications.all, "list", params] as const,
    detail: (id: string) => [...queryKeys.notifications.all, "detail", id] as const,
    count: () => [...queryKeys.notifications.all, "count"] as const,
    preferences: () => [...queryKeys.notifications.all, "preferences"] as const,
  },

  // API Keys
  apiKeys: {
    all: ["api-keys"] as const,
    list: () => [...queryKeys.apiKeys.all, "list"] as const,
    detail: (id: string) => [...queryKeys.apiKeys.all, "detail", id] as const,
  },

  // ============================================================================
  // New Modules
  // ============================================================================

  // Consolidated Dashboard module
  consolidated: {
    all: ["consolidated"] as const,
    security: (timeRange?: string) =>
      [...queryKeys.consolidated.all, "security", timeRange] as const,
    operations: (timeRange?: string) =>
      [...queryKeys.consolidated.all, "operations", timeRange] as const,
    billingDashboard: (timeRange?: string) =>
      [...queryKeys.consolidated.all, "billing-dashboard", timeRange] as const,
    infrastructure: () =>
      [...queryKeys.consolidated.all, "infrastructure"] as const,
    monitoring: (periodDays?: number) =>
      [...queryKeys.consolidated.all, "monitoring", periodDays] as const,
    logStats: (periodDays?: number) =>
      [...queryKeys.consolidated.all, "log-stats", periodDays] as const,
  },

  // Monitoring module
  monitoring: {
    all: ["monitoring"] as const,
    logs: {
      all: () => [...queryKeys.monitoring.all, "logs"] as const,
      list: (params?: unknown) =>
        [...queryKeys.monitoring.logs.all(), "list", params] as const,
      detail: (id: string) =>
        [...queryKeys.monitoring.logs.all(), "detail", id] as const,
      stats: (params?: unknown) =>
        [...queryKeys.monitoring.logs.all(), "stats", params] as const,
      services: () => [...queryKeys.monitoring.logs.all(), "services"] as const,
    },
  },

  // Alerts module
  alerts: {
    all: ["alerts"] as const,
    channels: {
      all: () => [...queryKeys.alerts.all, "channels"] as const,
      detail: (id: string) =>
        [...queryKeys.alerts.channels.all(), "detail", id] as const,
    },
    rules: {
      all: () => [...queryKeys.alerts.all, "rules"] as const,
      detail: (id: string) =>
        [...queryKeys.alerts.rules.all(), "detail", id] as const,
    },
    history: {
      all: () => [...queryKeys.alerts.all, "history"] as const,
      list: (params?: unknown) =>
        [...queryKeys.alerts.history.all(), "list", params] as const,
    },
    stats: (params?: unknown) =>
      [...queryKeys.alerts.all, "stats", params] as const,
  },

  // Observability module
  observability: {
    all: ["observability"] as const,
    traces: {
      all: () => [...queryKeys.observability.all, "traces"] as const,
      list: (params?: unknown) =>
        [...queryKeys.observability.traces.all(), "list", params] as const,
      detail: (traceId: string) =>
        [...queryKeys.observability.traces.all(), "detail", traceId] as const,
      spans: (traceId: string) =>
        [...queryKeys.observability.traces.all(), "spans", traceId] as const,
    },
    metrics: {
      all: () => [...queryKeys.observability.all, "metrics"] as const,
      list: (params?: unknown) =>
        [...queryKeys.observability.metrics.all(), "list", params] as const,
      series: (metricName: string, params?: unknown) =>
        [...queryKeys.observability.metrics.all(), "series", metricName, params] as const,
    },
    serviceMap: (params?: unknown) =>
      [...queryKeys.observability.all, "service-map", params] as const,
    serviceDependencies: (serviceName: string) =>
      [...queryKeys.observability.all, "dependencies", serviceName] as const,
    performance: {
      all: () => [...queryKeys.observability.all, "performance"] as const,
      analytics: (params?: unknown) =>
        [...queryKeys.observability.performance.all(), "analytics", params] as const,
      endpoint: (endpoint: string, params?: unknown) =>
        [...queryKeys.observability.performance.all(), "endpoint", endpoint, params] as const,
      slow: (params?: unknown) =>
        [...queryKeys.observability.performance.all(), "slow", params] as const,
    },
  },

  // Ticketing module
  ticketing: {
    all: ["ticketing"] as const,
    tickets: {
      all: () => [...queryKeys.ticketing.all, "tickets"] as const,
      list: (params?: unknown) =>
        [...queryKeys.ticketing.tickets.all(), "list", params] as const,
      detail: (id: string) =>
        [...queryKeys.ticketing.tickets.all(), "detail", id] as const,
      messages: (ticketId: string) =>
        [...queryKeys.ticketing.tickets.all(), "messages", ticketId] as const,
    },
    stats: (params?: unknown) =>
      [...queryKeys.ticketing.all, "stats", params] as const,
    agentPerformance: (params?: unknown) =>
      [...queryKeys.ticketing.all, "agent-performance", params] as const,
  },

  // Workflows module
  workflows: {
    all: ["workflows"] as const,
    list: (params?: unknown) =>
      [...queryKeys.workflows.all, "list", params] as const,
    detail: (id: string) =>
      [...queryKeys.workflows.all, "detail", id] as const,
    versions: (workflowId: string) =>
      [...queryKeys.workflows.all, "versions", workflowId] as const,
    version: (workflowId: string, version: number) =>
      [...queryKeys.workflows.all, "version", workflowId, version] as const,
    executions: {
      all: (workflowId: string) =>
        [...queryKeys.workflows.all, "executions", workflowId] as const,
      list: (workflowId: string, params?: unknown) =>
        [...queryKeys.workflows.executions.all(workflowId), "list", params] as const,
      detail: (workflowId: string, executionId: string) =>
        [...queryKeys.workflows.executions.all(workflowId), "detail", executionId] as const,
      logs: (workflowId: string, executionId: string) =>
        [...queryKeys.workflows.executions.all(workflowId), "logs", executionId] as const,
    },
    stats: (params?: unknown) =>
      [...queryKeys.workflows.all, "stats", params] as const,
  },

  // Jobs module
  jobs: {
    all: ["jobs"] as const,
    list: (params?: unknown) =>
      [...queryKeys.jobs.all, "list", params] as const,
    detail: (id: string) =>
      [...queryKeys.jobs.all, "detail", id] as const,
    progress: (id: string) =>
      [...queryKeys.jobs.all, "progress", id] as const,
    logs: (id: string) =>
      [...queryKeys.jobs.all, "logs", id] as const,
    scheduled: {
      all: () => [...queryKeys.jobs.all, "scheduled"] as const,
      detail: (id: string) =>
        [...queryKeys.jobs.scheduled.all(), "detail", id] as const,
    },
    stats: (params?: unknown) =>
      [...queryKeys.jobs.all, "stats", params] as const,
    queues: () => [...queryKeys.jobs.all, "queues"] as const,
  },

  // Communications module
  communications: {
    all: ["communications"] as const,
    templates: {
      all: () => [...queryKeys.communications.all, "templates"] as const,
      list: (params?: unknown) =>
        [...queryKeys.communications.templates.all(), "list", params] as const,
      detail: (id: string) =>
        [...queryKeys.communications.templates.all(), "detail", id] as const,
    },
    bulkJobs: {
      all: () => [...queryKeys.communications.all, "bulk-jobs"] as const,
      detail: (id: string) =>
        [...queryKeys.communications.bulkJobs.all(), "detail", id] as const,
    },
    logs: {
      all: () => [...queryKeys.communications.all, "logs"] as const,
      list: (params?: unknown) =>
        [...queryKeys.communications.logs.all(), "list", params] as const,
      detail: (id: string) =>
        [...queryKeys.communications.logs.all(), "detail", id] as const,
    },
    stats: (params?: unknown) =>
      [...queryKeys.communications.all, "stats", params] as const,
  },

  // Partners module
  partners: {
    all: ["partners"] as const,
    list: (params?: unknown) =>
      [...queryKeys.partners.all, "list", params] as const,
    detail: (id: string) =>
      [...queryKeys.partners.all, "detail", id] as const,
    users: (partnerId: string) =>
      [...queryKeys.partners.all, "users", partnerId] as const,
    accounts: (partnerId: string) =>
      [...queryKeys.partners.all, "accounts", partnerId] as const,
    commissions: {
      all: (partnerId: string) =>
        [...queryKeys.partners.all, "commissions", partnerId] as const,
      list: (partnerId: string, params?: unknown) =>
        [...queryKeys.partners.commissions.all(partnerId), "list", params] as const,
    },
    payouts: (partnerId: string, params?: unknown) =>
      [...queryKeys.partners.all, "payouts", partnerId, params] as const,
    referrals: {
      all: (partnerId: string) =>
        [...queryKeys.partners.all, "referrals", partnerId] as const,
      list: (partnerId: string, params?: unknown) =>
        [...queryKeys.partners.referrals.all(partnerId), "list", params] as const,
    },
    dashboard: () => [...queryKeys.partners.all, "dashboard"] as const,
    stats: (params?: unknown) =>
      [...queryKeys.partners.all, "stats", params] as const,
  },

  // Contacts module
  contacts: {
    all: ["contacts"] as const,
    list: (params?: unknown) =>
      [...queryKeys.contacts.all, "list", params] as const,
    detail: (id: string) =>
      [...queryKeys.contacts.all, "detail", id] as const,
    methods: (contactId: string) =>
      [...queryKeys.contacts.all, "methods", contactId] as const,
    activities: (contactId: string) =>
      [...queryKeys.contacts.all, "activities", contactId] as const,
    tags: (contactId: string) =>
      [...queryKeys.contacts.all, "tags", contactId] as const,
    stats: (params?: unknown) =>
      [...queryKeys.contacts.all, "stats", params] as const,
  },

  // Webhooks module
  webhooks: {
    all: () => ["webhooks"] as const,
    detail: (id: string) =>
      [...queryKeys.webhooks.all(), "detail", id] as const,
    deliveries: {
      all: (webhookId: string) =>
        [...queryKeys.webhooks.all(), "deliveries", webhookId] as const,
      list: (webhookId: string, params?: unknown) =>
        [...queryKeys.webhooks.deliveries.all(webhookId), "list", params] as const,
      detail: (webhookId: string, deliveryId: string) =>
        [...queryKeys.webhooks.deliveries.all(webhookId), "detail", deliveryId] as const,
    },
    events: () => [...queryKeys.webhooks.all(), "events"] as const,
    stats: (params?: unknown) =>
      [...queryKeys.webhooks.all(), "stats", params] as const,
  },

  // Integrations module
  integrations: {
    all: () => ["integrations"] as const,
    detail: (id: string) =>
      [...queryKeys.integrations.all(), "detail", id] as const,
    logs: (integrationId: string, params?: unknown) =>
      [...queryKeys.integrations.all(), "logs", integrationId, params] as const,
    available: () => [...queryKeys.integrations.all(), "available"] as const,
  },

  // Secrets module
  secrets: {
    all: ["secrets"] as const,
    list: (path?: string) =>
      [...queryKeys.secrets.all, "list", path] as const,
    detail: (path: string, version?: number) =>
      [...queryKeys.secrets.all, "detail", path, version] as const,
    metadata: (path: string) =>
      [...queryKeys.secrets.all, "metadata", path] as const,
    health: () => [...queryKeys.secrets.all, "health"] as const,
    metrics: (params?: unknown) =>
      [...queryKeys.secrets.all, "metrics", params] as const,
    rotationPolicies: () =>
      [...queryKeys.secrets.all, "rotation-policies"] as const,
  },

  // Feature Flags module
  featureFlags: {
    all: () => ["feature-flags"] as const,
    detail: (name: string) =>
      [...queryKeys.featureFlags.all(), "detail", name] as const,
    check: (name: string, context?: unknown) =>
      [...queryKeys.featureFlags.all(), "check", name, context] as const,
    checkBulk: (names: string[], context?: unknown) =>
      [...queryKeys.featureFlags.all(), "check-bulk", names, context] as const,
    status: () => [...queryKeys.featureFlags.all(), "status"] as const,
  },

  // Licensing module
  licensing: {
    all: ["licensing"] as const,
    licenses: {
      all: () => [...queryKeys.licensing.all, "licenses"] as const,
      list: (params?: unknown) =>
        [...queryKeys.licensing.licenses.all(), "list", params] as const,
      detail: (id: string) =>
        [...queryKeys.licensing.licenses.all(), "detail", id] as const,
      byKey: (licenseKey: string) =>
        [...queryKeys.licensing.licenses.all(), "by-key", licenseKey] as const,
    },
    activations: {
      all: () => [...queryKeys.licensing.all, "activations"] as const,
      list: (licenseId: string) =>
        [...queryKeys.licensing.activations.all(), "list", licenseId] as const,
    },
    templates: {
      all: () => [...queryKeys.licensing.all, "templates"] as const,
    },
  },

  // Audit module
  audit: {
    all: ["audit"] as const,
    activities: {
      all: () => [...queryKeys.audit.all, "activities"] as const,
      list: (params?: unknown) =>
        [...queryKeys.audit.activities.all(), "list", params] as const,
      detail: (id: string) =>
        [...queryKeys.audit.activities.all(), "detail", id] as const,
    },
    stats: (params?: unknown) =>
      [...queryKeys.audit.all, "stats", params] as const,
    userSummary: (userId: string, params?: unknown) =>
      [...queryKeys.audit.all, "user-summary", userId, params] as const,
  },

  // Plugins module
  plugins: {
    all: () => ["plugins"] as const,
    detail: (pluginName: string) =>
      [...queryKeys.plugins.all(), "detail", pluginName] as const,
    schema: (pluginName: string) =>
      [...queryKeys.plugins.all(), "schema", pluginName] as const,
    available: () => [...queryKeys.plugins.all(), "available"] as const,
    categories: () => [...queryKeys.plugins.all(), "categories"] as const,
    byCategory: (category: string) =>
      [...queryKeys.plugins.all(), "by-category", category] as const,
    instances: {
      all: (pluginName: string) =>
        [...queryKeys.plugins.all(), "instances", pluginName] as const,
      list: (pluginName: string) =>
        [...queryKeys.plugins.instances.all(pluginName), "list"] as const,
      detail: (pluginName: string, instanceId: string) =>
        [...queryKeys.plugins.instances.all(pluginName), "detail", instanceId] as const,
      configuration: (instanceId: string) =>
        [...queryKeys.plugins.all(), "instance-config", instanceId] as const,
      health: (instanceId: string) =>
        [...queryKeys.plugins.all(), "instance-health", instanceId] as const,
    },
  },

  // Partner Portal module (self-service)
  partnerPortal: {
    all: ["partner-portal"] as const,
    dashboard: () => [...queryKeys.partnerPortal.all, "dashboard"] as const,
    referrals: {
      all: () => [...queryKeys.partnerPortal.all, "referrals"] as const,
      list: (params?: unknown) =>
        [...queryKeys.partnerPortal.referrals.all(), "list", params] as const,
      detail: (id: string) =>
        [...queryKeys.partnerPortal.referrals.all(), "detail", id] as const,
    },
    customers: {
      all: () => [...queryKeys.partnerPortal.all, "customers"] as const,
      list: (params?: unknown) =>
        [...queryKeys.partnerPortal.customers.all(), "list", params] as const,
    },
    commissions: {
      all: () => [...queryKeys.partnerPortal.all, "commissions"] as const,
      list: (params?: unknown) =>
        [...queryKeys.partnerPortal.commissions.all(), "list", params] as const,
    },
    statements: {
      all: () => [...queryKeys.partnerPortal.all, "statements"] as const,
      list: (params?: unknown) =>
        [...queryKeys.partnerPortal.statements.all(), "list", params] as const,
      detail: (id: string) =>
        [...queryKeys.partnerPortal.statements.all(), "detail", id] as const,
    },
    payouts: () => [...queryKeys.partnerPortal.all, "payouts"] as const,
    profile: () => [...queryKeys.partnerPortal.all, "profile"] as const,
  },

  // Tenant Portal module (self-service)
  tenantPortal: {
    all: ["tenant-portal"] as const,
    dashboard: () => [...queryKeys.tenantPortal.all, "dashboard"] as const,
    members: {
      all: () => [...queryKeys.tenantPortal.all, "members"] as const,
      list: (params?: unknown) =>
        [...queryKeys.tenantPortal.members.all(), "list", params] as const,
    },
    invitations: {
      all: () => [...queryKeys.tenantPortal.all, "invitations"] as const,
      list: () => [...queryKeys.tenantPortal.invitations.all(), "list"] as const,
    },
    usage: (params?: unknown) =>
      [...queryKeys.tenantPortal.all, "usage", params] as const,
    billing: () => [...queryKeys.tenantPortal.all, "billing"] as const,
    settings: () => [...queryKeys.tenantPortal.all, "settings"] as const,
  },

  // Product Catalog module
  catalog: {
    all: ["catalog"] as const,
    products: {
      all: () => [...queryKeys.catalog.all, "products"] as const,
      list: (params?: unknown) =>
        [...queryKeys.catalog.products.all(), "list", params] as const,
      detail: (id: string) =>
        [...queryKeys.catalog.products.all(), "detail", id] as const,
    },
    categories: {
      all: () => [...queryKeys.catalog.all, "categories"] as const,
      list: () => [...queryKeys.catalog.categories.all(), "list"] as const,
      detail: (id: string) =>
        [...queryKeys.catalog.categories.all(), "detail", id] as const,
    },
  },
} as const;

// Type helper for query key arrays
type QueryKeyValue<T> = T extends (...args: any[]) => infer R
  ? R
  : T extends readonly unknown[]
    ? T
    : never;

type QueryKeyGroup<T> = QueryKeyValue<T[keyof T]>;

export type QueryKey =
  | QueryKeyGroup<typeof queryKeys.auth>
  | QueryKeyGroup<typeof queryKeys.users>
  | QueryKeyGroup<typeof queryKeys.tenants>;
