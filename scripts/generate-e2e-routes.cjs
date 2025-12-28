const fs = require("fs");
const path = require("path");

const rootDir = path.resolve(__dirname, "..");
const appDir = path.join(rootDir, "frontend", "app");
const outputPath = path.join(rootDir, "frontend", "e2e", "utils", "route-generator.ts");

function walk(dir, files = []) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(fullPath, files);
    } else if (entry.isFile() && entry.name === "page.tsx") {
      files.push(fullPath);
    }
  }
  return files;
}

function filePathToRoute(filePath) {
  let route = filePath
    .replace(/.*\/app\//, "/")
    .replace(/\/page\.tsx$/, "")
    .replace(/\/\([^)]+\)/g, "");
  if (!route) {
    route = "/";
  }
  return route;
}

function getDynamicSegments(route) {
  const matches = route.match(/\[([^\]]+)\]/g) || [];
  return matches.map((m) => m.slice(1, -1));
}

function getRouteGroup(filePath) {
  if (filePath.includes("/(auth)/")) return "auth";
  if (filePath.includes("/partner/")) return "partner";
  if (filePath.includes("/portal/")) return "portal";
  return "dashboard";
}

function routeToName(route) {
  if (route === "/") return "Dashboard Home";
  return route
    .split("/")
    .filter(Boolean)
    .filter((s) => !s.startsWith("["))
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1).replace(/-/g, " "))
    .join(" > ");
}

function requiresAuth(filePath, route) {
  if (filePath.includes("/(auth)/")) return false;
  if (route.endsWith("/login") || route.endsWith("/apply")) return false;
  return true;
}

function formatRoute(route) {
  const segments = route.dynamicSegments.length
    ? `[${route.dynamicSegments.map((s) => `"${s}"`).join(", ")}]`
    : "[]";
  return `  { path: "${route.path}", name: "${route.name}", group: "${route.group}", requiresAuth: ${route.requiresAuth}, isDynamic: ${route.isDynamic}, dynamicSegments: ${segments} },`;
}

const filePaths = walk(appDir).sort();
const routes = [];

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

const staticRoutes = routes.filter((r) => !r.isDynamic);
const dynamicRoutes = routes.filter((r) => r.isDynamic);

const counts = {
  auth: staticRoutes.filter((r) => r.group === "auth").length,
  dashboard: staticRoutes.filter((r) => r.group === "dashboard").length,
  partner: staticRoutes.filter((r) => r.group === "partner").length,
  portal: staticRoutes.filter((r) => r.group === "portal").length,
};

const header = `/**
 * Auto-generated route list from frontend/app directory
 * Run \`pnpm test:e2e:gen-routes\` to regenerate
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
    .replace(/.*\\/app\\//, "/")
    .replace(/\\/page\\.tsx$/, "")
    // Remove route groups (parentheses)
    .replace(/\\/\\([^)]+\\)/g, "")
    // Handle root page
    || "/";

  return route;
}

/**
 * Extract dynamic segments from a route
 */
function getDynamicSegments(route: string): string[] {
  const matches = route.match(/\\[([^\\]]+)\\]/g) || [];
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
  const result = execSync(\`find "\${appDir}" -name "page.tsx" | sort\`, {
    encoding: "utf-8",
  });

  const filePaths = result.trim().split("\\n").filter(Boolean);
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
`;

const staticBlock = [
  `export const ALL_ROUTES: RouteInfo[] = [`,
  `  // Auth routes (${counts.auth})`,
  staticRoutes.filter((r) => r.group === "auth").map(formatRoute).join("\n"),
  "",
  `  // Dashboard routes - static (${counts.dashboard})`,
  staticRoutes.filter((r) => r.group === "dashboard").map(formatRoute).join("\n"),
  "",
  `  // Partner routes - static (${counts.partner})`,
  staticRoutes.filter((r) => r.group === "partner").map(formatRoute).join("\n"),
  "",
  `  // Portal routes - static (${counts.portal})`,
  staticRoutes.filter((r) => r.group === "portal").map(formatRoute).join("\n"),
  `];`,
  "",
].join("\n");

const dynamicBlock = [
  `// Dynamic routes that need fixtures (${dynamicRoutes.length})`,
  `export const DYNAMIC_ROUTES: RouteInfo[] = [`,
  `  // Dashboard dynamic routes`,
  dynamicRoutes.map(formatRoute).join("\n"),
  `];`,
  "",
].join("\n");

const tail = `// Convenience exports
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

// Total: ${staticRoutes.length} static + ${dynamicRoutes.length} dynamic = ${
  staticRoutes.length + dynamicRoutes.length
} routes
`;

const out = header + staticBlock + dynamicBlock + tail;
fs.writeFileSync(outputPath, out);
console.log(
  `Updated ${outputPath} with ${staticRoutes.length} static and ${dynamicRoutes.length} dynamic routes.`
);
