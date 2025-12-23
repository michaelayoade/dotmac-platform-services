"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import type { Session } from "next-auth";
import type { ElementType } from "react";
import {
  LayoutDashboard,
  Users,
  Building2,
  CreditCard,
  BarChart3,
  UserCircle,
  Server,
  Settings,
  ChevronLeft,
  ChevronRight,
  Zap,
  Shield,
  Bell,
  HelpCircle,
  LogOut,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { usePermission } from "@/lib/hooks/use-permission";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  session: Session;
}

interface NavItem {
  label: string;
  href: string;
  icon: ElementType;
  permission?: string;
  badge?: string | number;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const navigation: NavSection[] = [
  {
    title: "Overview",
    items: [
      { label: "Dashboard", href: "/", icon: LayoutDashboard },
      { label: "Analytics", href: "/analytics", icon: BarChart3 },
    ],
  },
  {
    title: "Management",
    items: [
      {
        label: "Users",
        href: "/users",
        icon: Users,
        permission: "users:read",
      },
      {
        label: "Tenants",
        href: "/tenants",
        icon: Building2,
        permission: "tenants:read",
      },
      {
        label: "Customers",
        href: "/customers",
        icon: UserCircle,
        permission: "customers:read",
      },
    ],
  },
  {
    title: "Operations",
    items: [
      {
        label: "Billing",
        href: "/billing",
        icon: CreditCard,
        permission: "billing:read",
      },
      {
        label: "Deployments",
        href: "/deployments",
        icon: Server,
        permission: "deployments:read",
      },
    ],
  },
  {
    title: "System",
    items: [
      {
        label: "Security",
        href: "/security",
        icon: Shield,
        permission: "security:read",
      },
      {
        label: "Notifications",
        href: "/notifications",
        icon: Bell,
        badge: 3,
      },
      { label: "Settings", href: "/settings", icon: Settings },
    ],
  },
];

export function Sidebar({ collapsed, onToggle, session }: SidebarProps) {
  const pathname = usePathname();
  const { hasPermission } = usePermission();

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 h-screen",
        "bg-surface-elevated border-r border-border",
        "flex flex-col",
        "transition-all duration-300 ease-in-out",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Logo */}
      <div
        className={cn(
          "flex items-center h-16 px-4 border-b border-border",
          collapsed ? "justify-center" : "justify-between"
        )}
      >
        <Link href="/" className="flex items-center gap-3">
          <div className="relative w-8 h-8 flex items-center justify-center">
            <Zap className="w-6 h-6 text-accent" />
            <div className="absolute inset-0 bg-accent/20 rounded-lg blur-sm" />
          </div>
          {!collapsed && (
            <span className="font-semibold text-lg tracking-tight text-text-primary">
              DotMac
            </span>
          )}
        </Link>
        {!collapsed && (
          <button
            onClick={onToggle}
            className="p-1.5 rounded-md text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors"
            aria-label="Collapse sidebar"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Collapse button (when collapsed) */}
      {collapsed && (
        <button
          onClick={onToggle}
          className="flex items-center justify-center h-10 mx-2 mt-2 rounded-md text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors"
          aria-label="Expand sidebar"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      )}

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-2">
        {navigation.map((section, sectionIdx) => (
          <div key={section.title} className={cn(sectionIdx > 0 && "mt-6")}>
            {!collapsed && (
              <h3 className="px-3 mb-2 text-2xs font-semibold uppercase tracking-wider text-text-muted">
                {section.title}
              </h3>
            )}
            <ul className="space-y-1">
              {section.items.map((item) => {
                // Check permission
                if (item.permission && !hasPermission(item.permission)) {
                  return null;
                }

                const Icon = item.icon;
                const active = isActive(item.href);

                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={cn(
                        "relative flex items-center gap-3 rounded-md transition-all duration-150",
                        collapsed ? "justify-center px-2 py-2.5" : "px-3 py-2.5",
                        active
                          ? "bg-accent-subtle text-accent"
                          : "text-text-secondary hover:bg-surface-overlay hover:text-text-primary"
                      )}
                      title={collapsed ? item.label : undefined}
                    >
                      {/* Active indicator */}
                      {active && (
                        <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-accent rounded-r" />
                      )}

                      <Icon
                        className={cn("w-5 h-5 flex-shrink-0", active && "text-accent")}
                      />

                      {!collapsed && (
                        <>
                          <span className="text-sm font-medium">{item.label}</span>
                          {item.badge && (
                            <span className="ml-auto inline-flex items-center justify-center w-5 h-5 text-2xs font-semibold rounded-full bg-status-error text-white">
                              {item.badge}
                            </span>
                          )}
                        </>
                      )}

                      {collapsed && item.badge && (
                        <span className="absolute -top-1 -right-1 w-4 h-4 flex items-center justify-center text-2xs font-semibold rounded-full bg-status-error text-white">
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Footer actions */}
      <div className="border-t border-border p-2">
        {/* Help */}
        <Link
          href="/help"
          className={cn(
            "flex items-center gap-3 rounded-md px-3 py-2.5",
            "text-text-muted hover:text-text-secondary hover:bg-surface-overlay",
            "transition-colors",
            collapsed && "justify-center px-2"
          )}
          title={collapsed ? "Help & Support" : undefined}
        >
          <HelpCircle className="w-5 h-5" />
          {!collapsed && <span className="text-sm font-medium">Help & Support</span>}
        </Link>

        {/* User profile */}
        <div
          className={cn(
            "flex items-center gap-3 rounded-md px-3 py-2.5 mt-1",
            collapsed && "justify-center px-2"
          )}
        >
          {/* Avatar */}
          <div className="relative flex-shrink-0">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent to-highlight flex items-center justify-center text-sm font-semibold text-text-inverse">
              {session.user?.name?.charAt(0).toUpperCase() || "U"}
            </div>
            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-status-success border-2 border-surface-elevated rounded-full" />
          </div>

          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary truncate">
                {session.user?.name}
              </p>
              <p className="text-2xs text-text-muted truncate">
                {session.user?.email}
              </p>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
