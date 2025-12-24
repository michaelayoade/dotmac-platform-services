/**
 * Dashboard Layout
 *
 * Main layout component for dashboards with:
 * - Header with title and actions
 * - Filter bar
 * - Content area
 * - Responsive grid
 */

"use client";

import { type ReactNode } from "react";

import { cn } from "../utils/cn";

// ============================================================================
// Types
// ============================================================================

export interface DashboardLayoutProps {
  /** Dashboard title */
  title?: string;
  /** Dashboard subtitle/description */
  subtitle?: string;
  /** Header actions (buttons, dropdowns) */
  actions?: ReactNode;
  /** Filter components */
  filters?: ReactNode;
  /** Show filter bar */
  showFilters?: boolean;
  /** Main content */
  children: ReactNode;
  /** Sidebar content */
  sidebar?: ReactNode;
  /** Sidebar position */
  sidebarPosition?: "left" | "right";
  /** Sidebar width */
  sidebarWidth?: string;
  /** CSS class name */
  className?: string;
  /** Content class name */
  contentClassName?: string;
}

// ============================================================================
// Component
// ============================================================================

export function DashboardLayout({
  title,
  subtitle,
  actions,
  filters,
  showFilters = true,
  children,
  sidebar,
  sidebarPosition = "right",
  sidebarWidth = "320px",
  className,
  contentClassName,
}: DashboardLayoutProps) {
  return (
    <div className={cn("min-h-screen bg-gray-50", className)}>
      {/* Header */}
      {(title || actions) && (
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              {title && (
                <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
              )}
              {subtitle && (
                <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
              )}
            </div>
            {actions && <div className="flex items-center gap-3">{actions}</div>}
          </div>
        </header>
      )}

      {/* Filters */}
      {showFilters && filters && (
        <div className="bg-white border-b border-gray-200 px-6 py-3">
          <div className="flex flex-wrap items-center gap-3">{filters}</div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex">
        {/* Left Sidebar */}
        {sidebar && sidebarPosition === "left" && (
          <aside
            className="hidden lg:block bg-white border-r border-gray-200 p-6 overflow-y-auto"
            style={{ width: sidebarWidth, minWidth: sidebarWidth }}
          >
            {sidebar}
          </aside>
        )}

        {/* Content */}
        <main
          className={cn(
            "flex-1 p-6 overflow-y-auto",
            contentClassName
          )}
        >
          {children}
        </main>

        {/* Right Sidebar */}
        {sidebar && sidebarPosition === "right" && (
          <aside
            className="hidden lg:block bg-white border-l border-gray-200 p-6 overflow-y-auto"
            style={{ width: sidebarWidth, minWidth: sidebarWidth }}
          >
            {sidebar}
          </aside>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Dashboard Section
// ============================================================================

export interface DashboardSectionProps {
  /** Section title */
  title?: string;
  /** Section description */
  description?: string;
  /** Section actions */
  actions?: ReactNode;
  /** Section content */
  children: ReactNode;
  /** Collapsible */
  collapsible?: boolean;
  /** Default collapsed state */
  defaultCollapsed?: boolean;
  /** CSS class name */
  className?: string;
}

export function DashboardSection({
  title,
  description,
  actions,
  children,
  className,
}: DashboardSectionProps) {
  return (
    <section className={cn("mb-8", className)}>
      {(title || actions) && (
        <div className="flex items-center justify-between mb-4">
          <div>
            {title && (
              <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
            )}
            {description && (
              <p className="text-sm text-gray-500">{description}</p>
            )}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}
      {children}
    </section>
  );
}

export default DashboardLayout;
