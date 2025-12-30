/**
 * Auto-generated route list from frontend/app directory
 * Run `pnpm test:e2e:gen-routes` to regenerate
 */

import { execSync } from "child_process";
import path from "path";

export interface RouteInfo {
  path: string;
  name: string;
  group: "auth" | "dashboard" | "partner" | "portal";
  requiresAuth: boolean;
  isDynamic: boolean;
  dynamicSegments: string[];
}

/**
 * Convert a file path to a URL route
 */
function filePathToRoute(filePath: string): string {
  // Remove base path and page.tsx
  let route = filePath
    .replace(/.*\/app\//, "/")
    .replace(/\/page\.tsx$/, "")
    // Remove route groups (parentheses)
    .replace(/\/\([^)]+\)/g, "")
    // Handle root page
    || "/";

  return route;
}

/**
 * Extract dynamic segments from a route
 */
function getDynamicSegments(route: string): string[] {
  const matches = route.match(/\[([^\]]+)\]/g) || [];
  return matches.map((m) => m.slice(1, -1));
}

/**
 * Determine route group from file path
 */
function getRouteGroup(filePath: string): RouteInfo["group"] {
  if (filePath.includes("/(auth)/")) return "auth";
  if (filePath.includes("/partner/")) return "partner";
  if (filePath.includes("/portal/")) return "portal";
  return "dashboard";
}

/**
 * Generate a human-readable name from route
 */
function routeToName(route: string): string {
  if (route === "/") return "Dashboard Home";

  return route
    .split("/")
    .filter(Boolean)
    .filter((s) => !s.startsWith("["))
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1).replace(/-/g, " "))
    .join(" > ");
}

/**
 * Check if route requires authentication
 */
function requiresAuth(filePath: string, route: string): boolean {
  // Auth pages don't require auth
  if (filePath.includes("/(auth)/")) return false;
  // Login pages don't require auth
  if (route.endsWith("/login") || route.endsWith("/apply")) return false;
  // Everything else requires auth
  return true;
}

/**
 * Scan the app directory and generate route info
 */
export function generateRoutes(appDir: string): RouteInfo[] {
  const result = execSync(`find "${appDir}" -name "page.tsx" | sort`, {
    encoding: "utf-8",
  });

  const filePaths = result.trim().split("\n").filter(Boolean);
  const routes: RouteInfo[] = [];

  for (const filePath of filePaths) {
    const route = filePathToRoute(filePath);
    const dynamicSegments = getDynamicSegments(route);

    routes.push({
      path: route,
      name: routeToName(route),
      group: getRouteGroup(filePath),
      requiresAuth: requiresAuth(filePath, route),
      isDynamic: dynamicSegments.length > 0,
      dynamicSegments,
    });
  }

  return routes;
}

/**
 * Get static routes (no dynamic segments)
 */
export function getStaticRoutes(routes: RouteInfo[]): RouteInfo[] {
  return routes.filter((r) => !r.isDynamic);
}

/**
 * Get dynamic routes (have dynamic segments)
 */
export function getDynamicRoutes(routes: RouteInfo[]): RouteInfo[] {
  return routes.filter((r) => r.isDynamic);
}

/**
 * Group routes by their group
 */
export function groupRoutesByType(routes: RouteInfo[]): Record<RouteInfo["group"], RouteInfo[]> {
  return {
    auth: routes.filter((r) => r.group === "auth"),
    dashboard: routes.filter((r) => r.group === "dashboard"),
    partner: routes.filter((r) => r.group === "partner"),
    portal: routes.filter((r) => r.group === "portal"),
  };
}

// Pre-generated routes (updated by build script)
export const ALL_ROUTES: RouteInfo[] = [
  // Auth routes (5)
  { path: "/forgot-password", name: "Forgot password", group: "auth", requiresAuth: false, isDynamic: false, dynamicSegments: [] },
  { path: "/login", name: "Login", group: "auth", requiresAuth: false, isDynamic: false, dynamicSegments: [] },
  { path: "/reset-password", name: "Reset password", group: "auth", requiresAuth: false, isDynamic: false, dynamicSegments: [] },
  { path: "/signup", name: "Signup", group: "auth", requiresAuth: false, isDynamic: false, dynamicSegments: [] },
  { path: "/verify-email", name: "Verify email", group: "auth", requiresAuth: false, isDynamic: false, dynamicSegments: [] },

  // Dashboard routes - static (82)
  { path: "/admin/settings/audit", name: "Admin > Settings > Audit", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/admin/settings/backup", name: "Admin > Settings > Backup", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/admin/settings", name: "Admin > Settings", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/analytics", name: "Analytics", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/addons/active", name: "Billing > Addons > Active", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/addons", name: "Billing > Addons", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/analytics", name: "Billing > Analytics", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/bank-accounts", name: "Billing > Bank accounts", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/bank-accounts/payments", name: "Billing > Bank accounts > Payments", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/bank-accounts/registers", name: "Billing > Bank accounts > Registers", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/credit-notes/new", name: "Billing > Credit notes > New", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/credit-notes", name: "Billing > Credit notes", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/dunning/campaigns/new", name: "Billing > Dunning > Campaigns > New", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/dunning/campaigns", name: "Billing > Dunning > Campaigns", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/dunning/executions", name: "Billing > Dunning > Executions", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/dunning", name: "Billing > Dunning", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/invoices/new", name: "Billing > Invoices > New", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/invoices", name: "Billing > Invoices", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing", name: "Billing", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/payment-methods", name: "Billing > Payment methods", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/payments", name: "Billing > Payments", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/payments/record", name: "Billing > Payments > Record", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/pricing/calculator", name: "Billing > Pricing > Calculator", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/pricing/conflicts", name: "Billing > Pricing > Conflicts", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/pricing/new", name: "Billing > Pricing > New", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/pricing", name: "Billing > Pricing", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/receipts", name: "Billing > Receipts", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/settings", name: "Billing > Settings", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/subscriptions", name: "Billing > Subscriptions", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/billing/usage", name: "Billing > Usage", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/catalog/new", name: "Catalog > New", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/catalog", name: "Catalog", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/communications", name: "Communications", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/communications/templates/new", name: "Communications > Templates > New", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/contacts/import", name: "Contacts > Import", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/contacts/new", name: "Contacts > New", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/contacts", name: "Contacts", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/deployments/new", name: "Deployments > New", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/deployments", name: "Deployments", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/help", name: "Help", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/jobs", name: "Jobs", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/jobs/scheduled", name: "Jobs > Scheduled", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/licensing", name: "Licensing", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/monitoring/alerts", name: "Monitoring > Alerts", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/monitoring/logs", name: "Monitoring > Logs", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/monitoring", name: "Monitoring", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/monitoring/traces", name: "Monitoring > Traces", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/notifications", name: "Notifications", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/", name: "Dashboard Home", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/partners/applications", name: "Partners > Applications", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/partners/billing/export", name: "Partners > Billing > Export", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/partners/billing/invoices", name: "Partners > Billing > Invoices", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/partners/billing", name: "Partners > Billing", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/partners", name: "Partners", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/partners/profile", name: "Partners > Profile", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/partners/referrals/new", name: "Partners > Referrals > New", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/plugins", name: "Plugins", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/security", name: "Security", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/settings/api-keys", name: "Settings > Api keys", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/settings/audit", name: "Settings > Audit", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/settings/branding", name: "Settings > Branding", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/settings/feature-flags/new", name: "Settings > Feature flags > New", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/settings/feature-flags", name: "Settings > Feature flags", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/settings/integrations", name: "Settings > Integrations", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/settings/notifications", name: "Settings > Notifications", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/settings/organization", name: "Settings > Organization", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/settings", name: "Settings", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/settings/profile", name: "Settings > Profile", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/settings/roles", name: "Settings > Roles", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/settings/secrets/new", name: "Settings > Secrets > New", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/settings/secrets", name: "Settings > Secrets", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/settings/security", name: "Settings > Security", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/settings/webhooks/new", name: "Settings > Webhooks > New", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/settings/webhooks", name: "Settings > Webhooks", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/tenants/new", name: "Tenants > New", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/tenants", name: "Tenants", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/tickets/new", name: "Tickets > New", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/tickets", name: "Tickets", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/users/new", name: "Users > New", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/users", name: "Users", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/workflows/new", name: "Workflows > New", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/workflows", name: "Workflows", group: "dashboard", requiresAuth: true, isDynamic: false, dynamicSegments: [] },

  // Partner routes - static (9)
  { path: "/partner/commissions", name: "Partner > Commissions", group: "partner", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/partner", name: "Partner", group: "partner", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/partner/referrals", name: "Partner > Referrals", group: "partner", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/partner/settings", name: "Partner > Settings", group: "partner", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/partner/statements", name: "Partner > Statements", group: "partner", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/partner/team", name: "Partner > Team", group: "partner", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/partner/tenants", name: "Partner > Tenants", group: "partner", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/partner/apply", name: "Partner > Apply", group: "partner", requiresAuth: false, isDynamic: false, dynamicSegments: [] },
  { path: "/partner/login", name: "Partner > Login", group: "partner", requiresAuth: false, isDynamic: false, dynamicSegments: [] },

  // Portal routes - static (6)
  { path: "/portal/billing", name: "Portal > Billing", group: "portal", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/portal", name: "Portal", group: "portal", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/portal/settings", name: "Portal > Settings", group: "portal", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/portal/team", name: "Portal > Team", group: "portal", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/portal/usage", name: "Portal > Usage", group: "portal", requiresAuth: true, isDynamic: false, dynamicSegments: [] },
  { path: "/portal/login", name: "Portal > Login", group: "portal", requiresAuth: false, isDynamic: false, dynamicSegments: [] },
];
// Dynamic routes that need fixtures (34)
export const DYNAMIC_ROUTES: RouteInfo[] = [
  // Dashboard dynamic routes
  { path: "/admin/settings/[category]", name: "Admin > Settings", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["category"] },
  { path: "/billing/addons/[id]", name: "Billing > Addons", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/billing/bank-accounts/[id]", name: "Billing > Bank accounts", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/billing/credit-notes/[id]/apply", name: "Billing > Credit notes > Apply", group: "dashboard", requiresAuth: false, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/billing/credit-notes/[id]", name: "Billing > Credit notes", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/billing/dunning/campaigns/[id]", name: "Billing > Dunning > Campaigns", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/billing/invoices/[id]", name: "Billing > Invoices", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/billing/payments/[id]", name: "Billing > Payments", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/billing/pricing/[id]", name: "Billing > Pricing", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/billing/receipts/[id]", name: "Billing > Receipts", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/billing/subscriptions/[id]", name: "Billing > Subscriptions", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/catalog/[id]/edit", name: "Catalog > Edit", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/catalog/[id]", name: "Catalog", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/communications/templates/[id]/edit", name: "Communications > Templates > Edit", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/contacts/[id]/edit", name: "Contacts > Edit", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/contacts/[id]", name: "Contacts", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/deployments/[id]/config", name: "Deployments > Config", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/deployments/[id]/edit", name: "Deployments > Edit", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/deployments/[id]/logs", name: "Deployments > Logs", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/deployments/[id]", name: "Deployments", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/jobs/[id]", name: "Jobs", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/partners/[id]/users/[userId]", name: "Partners > Users", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id", "userId"] },
  { path: "/partners/[id]/users", name: "Partners > Users", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/partners/billing/invoices/[id]", name: "Partners > Billing > Invoices", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/settings/feature-flags/[name]", name: "Settings > Feature flags", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["name"] },
  { path: "/settings/secrets/[...path]", name: "Settings > Secrets", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["...path"] },
  { path: "/settings/webhooks/[id]", name: "Settings > Webhooks", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/tenants/[id]", name: "Tenants", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/tickets/[id]/edit", name: "Tickets > Edit", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/tickets/[id]", name: "Tickets", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/users/[id]", name: "Users", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/workflows/[id]/edit", name: "Workflows > Edit", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
  { path: "/workflows/[id]/executions/[executionId]", name: "Workflows > Executions", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id", "executionId"] },
  { path: "/workflows/[id]", name: "Workflows", group: "dashboard", requiresAuth: true, isDynamic: true, dynamicSegments: ["id"] },
];
// Convenience exports
export const STATIC_ROUTES = ALL_ROUTES;
export const STATIC_AUTH_ROUTES = ALL_ROUTES.filter((r) => r.group === "auth");
export const STATIC_DASHBOARD_ROUTES = ALL_ROUTES.filter((r) => r.group === "dashboard");
export const STATIC_PARTNER_ROUTES = ALL_ROUTES.filter((r) => r.group === "partner");
export const STATIC_PORTAL_ROUTES = ALL_ROUTES.filter((r) => r.group === "portal");

// Route counts
export const ROUTE_COUNTS = {
  total: ALL_ROUTES.length + DYNAMIC_ROUTES.length,
  static: ALL_ROUTES.length,
  dynamic: DYNAMIC_ROUTES.length,
  auth: STATIC_AUTH_ROUTES.length,
  dashboard: STATIC_DASHBOARD_ROUTES.length,
  partner: STATIC_PARTNER_ROUTES.length,
  portal: STATIC_PORTAL_ROUTES.length,
};

// Total: 102 static + 34 dynamic = 136 routes
