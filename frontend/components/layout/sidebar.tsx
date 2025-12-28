"use client";

import { memo, useMemo, useCallback, useLayoutEffect, useState } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { ChevronLeft, ChevronRight, ExternalLink, Zap } from "lucide-react";

import { cn } from "@/lib/utils";
import { usePermission } from "@/lib/hooks/use-permission";
import {
  navigationSections,
  footerNavItem,
  filterNavByPermissions,
  isPathActive,
} from "@/lib/config/navigation";
import type { PlatformUser } from "@/types/auth";

// ============================================================================
// Constants
// ============================================================================

const SIDEBAR_COLLAPSED_KEY = "sidebar-collapsed";

// ============================================================================
// Types
// ============================================================================

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  user: PlatformUser;
  isHydrated: boolean;
}

// ============================================================================
// Hooks
// ============================================================================

/**
 * Hook to persist sidebar collapse state to localStorage
 */
export function useSidebarState() {
  const [collapsed, setCollapsed] = useState(false);
  const [isHydrated, setIsHydrated] = useState(false);

  // Load from localStorage on mount
  useLayoutEffect(() => {
    const saved = localStorage.getItem(SIDEBAR_COLLAPSED_KEY);
    if (saved !== null) {
      setCollapsed(saved === "true");
    }
    setIsHydrated(true);
  }, []);

  // Save to localStorage when changed
  const toggleCollapsed = useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(next));
      return next;
    });
  }, []);

  return { collapsed, toggleCollapsed, isHydrated };
}

// ============================================================================
// Components
// ============================================================================

const NavLink = memo(function NavLink({
  href,
  label,
  icon: Icon,
  badge,
  active,
  collapsed,
  external,
}: {
  href: string;
  label: string;
  icon: React.ElementType;
  badge?: string | number;
  active: boolean;
  collapsed: boolean;
  external?: boolean;
}) {
  const className = cn(
    "relative flex items-center gap-3 rounded-md transition-all duration-150",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-inset",
    collapsed ? "justify-center px-2 py-2.5" : "px-3 py-2.5",
    active
      ? "bg-accent-subtle text-accent"
      : "text-text-secondary hover:bg-surface-overlay hover:text-text-primary"
  );

  const content = (
    <>
      {/* Active indicator */}
      {active && (
        <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-accent rounded-r" />
      )}

      <Icon className={cn("w-5 h-5 flex-shrink-0", active && "text-accent")} />

      {!collapsed && (
        <>
          <span className="text-sm font-medium">{label}</span>
          {external && (
            <ExternalLink className="w-3.5 h-3.5 text-text-muted ml-auto" aria-hidden="true" />
          )}
          {badge !== undefined && (
            <span
              className={cn("inline-flex items-center justify-center w-5 h-5 text-2xs font-semibold rounded-full bg-status-error text-text-inverse", !external && "ml-auto")}
              role="status"
              aria-label={`${badge} notifications`}
            >
              {badge}
            </span>
          )}
        </>
      )}

      {collapsed && badge !== undefined && (
        <span
          className="absolute -top-1 -right-1 w-4 h-4 flex items-center justify-center text-2xs font-semibold rounded-full bg-status-error text-text-inverse"
          role="status"
          aria-label={`${badge} notifications`}
        >
          {badge}
        </span>
      )}
    </>
  );

  if (external) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className={className}
        title={collapsed ? `${label} (opens in new tab)` : undefined}
      >
        {content}
      </a>
    );
  }

  return (
    <Link
      href={href}
      prefetch={true}
      className={className}
      title={collapsed ? label : undefined}
      aria-current={active ? "page" : undefined}
    >
      {content}
    </Link>
  );
});

export const Sidebar = memo(function Sidebar({
  collapsed,
  onToggle,
  user,
  isHydrated,
}: SidebarProps) {
  const pathname = usePathname();
  const { hasPermission, isLoading } = usePermission();
  const userInitial = (
    user.fullName?.charAt(0) ||
    user.username?.charAt(0) ||
    user.email?.charAt(0) ||
    "U"
  ).toUpperCase();

  // Filter navigation by permissions - memoized
  const filteredSections = useMemo(
    () => filterNavByPermissions(navigationSections, hasPermission),
    [hasPermission]
  );

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-20 h-screen",
        "bg-surface-elevated border-r border-border",
        "flex flex-col",
        isHydrated ? "transition-all duration-300 ease-in-out" : "transition-none",
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
        <Link href="/" prefetch={true} className="flex items-center gap-3">
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
            className="p-1.5 rounded-md text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
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
          className="flex items-center justify-center h-10 mx-2 mt-2 rounded-md text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          aria-label="Expand sidebar"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      )}

      {/* Navigation */}
      <nav
        className="flex-1 overflow-y-auto py-4 px-2"
        aria-label="Main navigation"
      >
        {isLoading ? (
          <div className="space-y-4 px-2">
            {Array.from({ length: 6 }).map((_, idx) => (
              <div
                key={`sidebar-skeleton-${idx}`}
                className={cn("h-4 rounded bg-surface-overlay/70 animate-pulse")}
                style={{ width: collapsed ? "1.5rem" : `${60 + idx * 5}%` }}
              />
            ))}
          </div>
        ) : (
          filteredSections.map((section, sectionIdx) => (
            <div key={section.id} className={cn(sectionIdx > 0 && "mt-6")}>
              {!collapsed && (
                <h3 className="px-3 mb-2 text-2xs font-semibold uppercase tracking-wider text-text-muted">
                  {section.title}
                </h3>
              )}
              <ul className="space-y-1">
                {section.items.map((item) => (
                  <li key={item.id}>
                    <NavLink
                      href={item.href}
                      label={item.label}
                      icon={item.icon}
                      badge={item.badge}
                      active={!item.external && isPathActive(item.href, pathname)}
                      collapsed={collapsed}
                      external={item.external}
                    />
                  </li>
                ))}
              </ul>
            </div>
          ))
        )}
      </nav>

      {/* Footer actions */}
      <div className="border-t border-border p-2">
        {/* Help */}
        <Link
          href={footerNavItem.href}
          prefetch={true}
          className={cn(
            "flex items-center gap-3 rounded-md px-3 py-2.5",
            "text-text-muted hover:text-text-secondary hover:bg-surface-overlay",
            "transition-colors",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-inset",
            collapsed && "justify-center px-2"
          )}
          title={collapsed ? footerNavItem.label : undefined}
        >
          <footerNavItem.icon className="w-5 h-5" />
          {!collapsed && (
            <span className="text-sm font-medium">{footerNavItem.label}</span>
          )}
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
              {userInitial}
            </div>
            <span
              className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-status-success border-2 border-surface-elevated rounded-full"
              role="status"
              aria-label="Online"
            >
              <span className="sr-only">Status: Online</span>
            </span>
          </div>

          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary truncate">
                {user.fullName || user.username}
              </p>
              <p className="text-2xs text-text-muted truncate">{user.email}</p>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
});

export default Sidebar;
