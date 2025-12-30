/**
 * Centralized Navigation Configuration
 * Single source of truth for all navigation items across the application
 */

import type { ElementType } from "react";
import {
  LayoutDashboard,
  Users,
  Building2,
  CreditCard,
  BarChart3,
  Server,
  Settings,
  Shield,
  Bell,
  HelpCircle,
  MessageSquare,
  Layers,
  GitBranch,
  Activity,
  Contact,
  Handshake,
  Mail,
  Key,
  Puzzle,
  Package,
  Plus,
  FileText,
  ExternalLink,
  LineChart,
  Network,
  HardDrive,
  Cog,
} from "lucide-react";

// ============================================================================
// Types
// ============================================================================

export interface NavItem {
  id: string;
  label: string;
  href: string;
  icon: ElementType;
  permission?: string;
  badge?: number | string;
  keywords?: string[]; // For command palette search
  description?: string; // For command palette
  external?: boolean; // Opens in new tab
}

export interface NavSection {
  id: string;
  title: string;
  items: NavItem[];
}

export interface ActionItem {
  id: string;
  label: string;
  href: string;
  icon: ElementType;
  keywords?: string[];
  description?: string;
}

// ============================================================================
// Navigation Sections
// ============================================================================

export const navigationSections: NavSection[] = [
  {
    id: "overview",
    title: "Overview",
    items: [
      {
        id: "dashboard",
        label: "Dashboard",
        href: "/",
        icon: LayoutDashboard,
        keywords: ["home", "overview"],
      },
      {
        id: "analytics",
        label: "Analytics",
        href: "/analytics",
        icon: BarChart3,
        keywords: ["reports", "metrics", "stats"],
      },
    ],
  },
  {
    id: "management",
    title: "Management",
    items: [
      {
        id: "users",
        label: "Users",
        href: "/users",
        icon: Users,
        permission: "users:read",
        keywords: ["members", "team"],
      },
      {
        id: "tenants",
        label: "Tenants",
        href: "/tenants",
        icon: Building2,
        permission: "tenants:read",
        keywords: ["organizations", "orgs"],
      },
    ],
  },
  {
    id: "operations",
    title: "Operations",
    items: [
      {
        id: "billing",
        label: "Billing",
        href: "/billing",
        icon: CreditCard,
        permission: "billing:read",
        keywords: ["invoices", "payments", "subscriptions"],
      },
      {
        id: "catalog",
        label: "Product Catalog",
        href: "/catalog",
        icon: Package,
        permission: "billing:catalog:read",
        keywords: ["products", "plans", "pricing"],
      },
      {
        id: "deployments",
        label: "Deployments",
        href: "/deployments",
        icon: Server,
        permission: "deployments:read",
        keywords: ["infrastructure", "instances"],
      },
      {
        id: "tickets",
        label: "Tickets",
        href: "/tickets",
        icon: MessageSquare,
        permission: "tickets:read",
        keywords: ["support", "issues"],
      },
      {
        id: "jobs",
        label: "Jobs",
        href: "/jobs",
        icon: Layers,
        permission: "jobs:read",
        keywords: ["tasks", "queue"],
      },
      {
        id: "workflows",
        label: "Workflows",
        href: "/workflows",
        icon: GitBranch,
        permission: "workflows:read",
        keywords: ["automation", "pipelines"],
      },
    ],
  },
  {
    id: "monitoring",
    title: "Monitoring",
    items: [
      {
        id: "monitoring-overview",
        label: "Overview",
        href: "/monitoring",
        icon: Activity,
        permission: "monitoring:read",
        keywords: ["health", "status"],
      },
    ],
  },
  {
    id: "crm",
    title: "CRM",
    items: [
      {
        id: "contacts",
        label: "Contacts",
        href: "/contacts",
        icon: Contact,
        permission: "contacts:read",
        keywords: ["people", "customers"],
      },
      {
        id: "partners",
        label: "Partners",
        href: "/partners",
        icon: Handshake,
        permission: "partners:read",
        keywords: ["affiliates", "resellers"],
      },
      {
        id: "communications",
        label: "Communications",
        href: "/communications",
        icon: Mail,
        permission: "communications:read",
        keywords: ["emails", "messages"],
      },
    ],
  },
  {
    id: "system",
    title: "System",
    items: [
      {
        id: "admin-settings",
        label: "System Settings",
        href: "/admin/settings",
        icon: Cog,
        permission: "settings.read",
        keywords: ["config", "smtp", "email", "database", "redis", "admin", "platform"],
        description: "Configure platform settings and integrations",
      },
      {
        id: "licensing",
        label: "Licensing",
        href: "/licensing",
        icon: Key,
        permission: "licensing:read",
        keywords: ["licenses", "keys"],
      },
      {
        id: "plugins",
        label: "Plugins",
        href: "/plugins",
        icon: Puzzle,
        permission: "plugins:read",
        keywords: ["extensions", "addons"],
      },
      {
        id: "security",
        label: "Security",
        href: "/security",
        icon: Shield,
        permission: "security:read",
        keywords: ["audit", "logs"],
      },
      {
        id: "notifications",
        label: "Notifications",
        href: "/notifications",
        icon: Bell,
        keywords: ["alerts", "updates"],
      },
      {
        id: "settings",
        label: "Settings",
        href: "/settings",
        icon: Settings,
        keywords: ["config", "preferences"],
      },
    ],
  },
  {
    id: "external-tools",
    title: "External Tools",
    items: [
      {
        id: "grafana",
        label: "Grafana",
        href: "http://149.102.158.144:3001",
        icon: LineChart,
        external: true,
        keywords: ["dashboards", "metrics", "visualization"],
        description: "Monitoring dashboards and visualizations",
      },
      {
        id: "jaeger",
        label: "Jaeger",
        href: "http://149.102.158.144:16686",
        icon: Activity,
        external: true,
        keywords: ["tracing", "spans", "distributed"],
        description: "Distributed tracing UI",
      },
      {
        id: "netbox",
        label: "NetBox",
        href: "http://149.102.158.144:8080",
        icon: Network,
        external: true,
        keywords: ["ipam", "dcim", "inventory", "network"],
        description: "IP address and network management",
      },
      {
        id: "minio-console",
        label: "MinIO Console",
        href: "http://149.102.158.144:9001",
        icon: HardDrive,
        external: true,
        keywords: ["storage", "s3", "buckets", "objects"],
        description: "Object storage management",
      },
    ],
  },
];

// ============================================================================
// Quick Actions (for Command Palette)
// ============================================================================

export const quickActions: ActionItem[] = [
  {
    id: "action-new-user",
    label: "Create New User",
    href: "/users/new",
    icon: Plus,
    keywords: ["add user", "invite"],
    description: "Add a new user to the platform",
  },
  {
    id: "action-new-tenant",
    label: "Create New Tenant",
    href: "/tenants/new",
    icon: Plus,
    keywords: ["add org", "organization"],
    description: "Create a new tenant organization",
  },
  {
    id: "action-new-invoice",
    label: "Create New Invoice",
    href: "/billing/invoices/new",
    icon: FileText,
    keywords: ["bill", "charge"],
    description: "Generate a new invoice",
  },
  {
    id: "action-new-ticket",
    label: "Create New Ticket",
    href: "/tickets/new",
    icon: Plus,
    keywords: ["support", "issue"],
    description: "Open a support ticket",
  },
  {
    id: "action-new-workflow",
    label: "Create New Workflow",
    href: "/workflows/new",
    icon: Plus,
    keywords: ["automation", "pipeline"],
    description: "Create a new automation workflow",
  },
];

// ============================================================================
// Footer Navigation
// ============================================================================

export const footerNavItem: NavItem = {
  id: "help",
  label: "Help & Support",
  href: "/help",
  icon: HelpCircle,
  keywords: ["support", "documentation", "faq"],
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get all navigation items as a flat array
 */
export function getAllNavItems(): NavItem[] {
  return navigationSections.flatMap((section) => section.items);
}

/**
 * Filter navigation sections by permissions
 */
export function filterNavByPermissions(
  sections: NavSection[],
  hasPermission: (permission: string) => boolean
): NavSection[] {
  return sections
    .map((section) => ({
      ...section,
      items: section.items.filter(
        (item) => !item.permission || hasPermission(item.permission)
      ),
    }))
    .filter((section) => section.items.length > 0);
}

/**
 * Check if a path is active (matches current pathname)
 */
export function isPathActive(href: string, pathname: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname.startsWith(href);
}

/**
 * Search navigation and actions by query
 */
export function searchNavigation(
  query: string,
  items: NavItem[],
  actions: ActionItem[] = []
): { navItems: NavItem[]; actionItems: ActionItem[] } {
  const normalizedQuery = query.toLowerCase().trim();

  if (!normalizedQuery) {
    return { navItems: items, actionItems: actions };
  }

  const matchItem = (item: NavItem | ActionItem): boolean => {
    const searchStr = [
      item.label,
      item.description,
      ...(item.keywords || []),
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    return searchStr.includes(normalizedQuery);
  };

  return {
    navItems: items.filter(matchItem),
    actionItems: actions.filter(matchItem),
  };
}
