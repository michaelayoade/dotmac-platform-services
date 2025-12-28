"use client";

import Link from "next/link";
import {
  Settings,
  Download,
  Upload,
  History,
  Shield,
  Database,
  RefreshCw,
  AlertCircle,
} from "lucide-react";
import { useSettingsCategories, useSettingsHealth } from "@/lib/hooks/api/use-admin-settings";
import { CategoryCard } from "@/components/features/admin-settings/category-card";
import { categoryOrder } from "@/lib/config/admin-settings";

export default function AdminSettingsPage() {
  const { data: categories, isLoading, error } = useSettingsCategories();
  const { data: health } = useSettingsHealth();

  // Sort categories according to the defined order
  const sortedCategories = categories?.sort((a, b) => {
    const aIndex = categoryOrder.indexOf(a.category);
    const bIndex = categoryOrder.indexOf(b.category);
    return aIndex - bIndex;
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header border-0 pb-0 mb-0">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-accent-subtle">
              <Settings className="w-5 h-5 text-accent" />
            </div>
            <h1 className="page-title">System Settings</h1>
          </div>
          <p className="page-description">
            Configure platform settings, integrations, and system parameters
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <Link
            href="/admin/settings/backup"
            className="btn btn--secondary btn--sm"
          >
            <Database className="w-4 h-4" />
            Backups
          </Link>
          <Link
            href="/admin/settings/audit"
            className="btn btn--secondary btn--sm"
          >
            <History className="w-4 h-4" />
            Audit Logs
          </Link>
        </div>
      </div>

      {/* Health Status Banner */}
      {health && (
        <div className="card p-4 bg-surface-overlay/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div
                  className={`w-2 h-2 rounded-full ${
                    health.status === "healthy" ? "bg-success" : "bg-warning"
                  }`}
                />
                <span className="text-sm font-medium text-text-primary">
                  Settings Service: {health.status === "healthy" ? "Healthy" : "Degraded"}
                </span>
              </div>
              <div className="h-4 w-px bg-border" />
              <span className="text-sm text-text-muted">
                {health.categoriesAvailable} categories
              </span>
              <span className="text-sm text-text-muted">
                {health.backupsCount} backups
              </span>
              <span className="text-sm text-text-muted">
                {health.auditLogsCount} audit entries
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 9 }).map((_, i) => (
            <div key={i} className="card p-6 animate-pulse">
              <div className="flex items-start gap-4">
                <div className="w-11 h-11 rounded-lg bg-surface-overlay" />
                <div className="flex-1 space-y-3">
                  <div className="h-5 bg-surface-overlay rounded w-3/4" />
                  <div className="h-4 bg-surface-overlay rounded w-full" />
                  <div className="flex gap-2">
                    <div className="h-5 bg-surface-overlay rounded w-16" />
                    <div className="h-5 bg-surface-overlay rounded w-20" />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="card p-6 border-danger/50 bg-danger-subtle">
          <div className="flex items-start gap-4">
            <AlertCircle className="w-5 h-5 text-danger flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-medium text-danger mb-1">
                Failed to load settings
              </h3>
              <p className="text-sm text-danger/80">
                {error instanceof Error ? error.message : "An unexpected error occurred"}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Categories Grid */}
      {sortedCategories && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sortedCategories.map((category, index) => (
            <CategoryCard
              key={category.category}
              category={category}
              index={index}
            />
          ))}
        </div>
      )}

      {/* Quick Actions Footer */}
      <div className="card p-4 bg-surface-overlay/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-text-muted">
            <Shield className="w-4 h-4" />
            <span>All changes are logged and require appropriate permissions</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              className="btn btn--ghost btn--xs text-text-muted hover:text-text-primary"
              title="Import settings"
            >
              <Upload className="w-4 h-4" />
              Import
            </button>
            <button
              className="btn btn--ghost btn--xs text-text-muted hover:text-text-primary"
              title="Export settings"
            >
              <Download className="w-4 h-4" />
              Export
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
