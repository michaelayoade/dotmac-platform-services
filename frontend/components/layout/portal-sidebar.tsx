"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import type { ElementType } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Zap,
  HelpCircle,
  LogOut,
} from "lucide-react";
import { useRouter } from "next/navigation";

import { cn } from "@/lib/utils";
import { api } from "@/lib/api/client";
import type { PlatformUser } from "@/types/auth";

export interface PortalNavItem {
  label: string;
  href: string;
  icon: ElementType;
  badge?: string | number;
}

export interface PortalNavSection {
  title?: string;
  items: PortalNavItem[];
}

export interface PortalConfig {
  title: string;
  subtitle?: string;
  logoIcon?: ElementType;
  navigation: PortalNavSection[];
  baseHref: string;
  helpHref?: string;
}

interface PortalSidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  user: PlatformUser;
  config: PortalConfig;
}

export function PortalSidebar({
  collapsed,
  onToggle,
  user,
  config,
}: PortalSidebarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const LogoIcon = config.logoIcon || Zap;

  const isActive = (href: string) => {
    // Handle base href (e.g., /partner or /portal)
    if (href === config.baseHref) {
      return pathname === config.baseHref;
    }
    return pathname.startsWith(href);
  };

  const handleSignOut = async () => {
    try {
      await api.post("/api/v1/auth/logout");
    } finally {
      router.push(`${config.baseHref}/login`);
    }
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
        <Link href={config.baseHref} className="flex items-center gap-3">
          <div className="relative w-8 h-8 flex items-center justify-center">
            <LogoIcon className="w-6 h-6 text-accent" />
            <div className="absolute inset-0 bg-accent/20 rounded-lg blur-sm" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-semibold text-sm tracking-tight text-text-primary">
                {config.title}
              </span>
              {config.subtitle && (
                <span className="text-2xs text-text-muted">
                  {config.subtitle}
                </span>
              )}
            </div>
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
        {config.navigation.map((section, sectionIdx) => (
          <div key={section.title || sectionIdx} className={cn(sectionIdx > 0 && "mt-6")}>
            {!collapsed && section.title && (
              <h3 className="px-3 mb-2 text-2xs font-semibold uppercase tracking-wider text-text-muted">
                {section.title}
              </h3>
            )}
            <ul className="space-y-1">
              {section.items.map((item) => {
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
                            <span className="ml-auto inline-flex items-center justify-center px-2 h-5 text-2xs font-semibold rounded-full bg-accent/10 text-accent">
                              {item.badge}
                            </span>
                          )}
                        </>
                      )}

                      {collapsed && item.badge && (
                        <span className="absolute -top-1 -right-1 w-4 h-4 flex items-center justify-center text-2xs font-semibold rounded-full bg-accent text-white">
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
        {config.helpHref && (
          <Link
            href={config.helpHref}
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
        )}

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
              {user.fullName?.charAt(0).toUpperCase() ||
                user.username?.charAt(0).toUpperCase() ||
                "U"}
            </div>
            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-status-success border-2 border-surface-elevated rounded-full" />
          </div>

          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary truncate">
                {user.fullName || user.username}
              </p>
              <p className="text-2xs text-text-muted truncate">
                {user.email}
              </p>
            </div>
          )}
        </div>

        {/* Sign out */}
        <button
          onClick={handleSignOut}
          className={cn(
            "w-full flex items-center gap-3 rounded-md px-3 py-2.5 mt-1",
            "text-text-muted hover:text-status-error hover:bg-status-error/10",
            "transition-colors",
            collapsed && "justify-center px-2"
          )}
          title={collapsed ? "Sign out" : undefined}
        >
          <LogOut className="w-5 h-5" />
          {!collapsed && <span className="text-sm font-medium">Sign out</span>}
        </button>
      </div>
    </aside>
  );
}
