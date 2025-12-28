"use client";

import { use } from "react";
import Link from "next/link";
import { ChevronLeft, AlertCircle, RefreshCw } from "lucide-react";
import { useSettingsCategory } from "@/lib/hooks/api/use-admin-settings";
import { getCategoryConfig, categoryOrder } from "@/lib/config/admin-settings";
import { SettingsFormRenderer } from "@/components/features/admin-settings";
import type { SettingsCategory } from "@/lib/api/admin-settings";

interface CategoryDetailPageProps {
  params: Promise<{ category: string }>;
}

export default function CategoryDetailPage({ params }: CategoryDetailPageProps) {
  const { category } = use(params);
  const settingsCategory = category as SettingsCategory;

  // Validate category
  const isValidCategory = categoryOrder.includes(settingsCategory);

  const { data: settings, isLoading, error, refetch } = useSettingsCategory(
    settingsCategory,
    false // Don't include sensitive values by default
  );

  const config = getCategoryConfig(settingsCategory);
  const Icon = config.icon;

  // Invalid category
  if (!isValidCategory) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link
            href="/admin/settings"
            className="btn btn--ghost btn--sm"
          >
            <ChevronLeft className="w-4 h-4" />
            Back
          </Link>
        </div>
        <div className="card p-8 text-center">
          <AlertCircle className="w-12 h-12 text-danger mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-text-primary mb-2">
            Invalid Category
          </h2>
          <p className="text-text-muted mb-4">
            The category &quot;{category}&quot; does not exist.
          </p>
          <Link href="/admin/settings" className="btn btn--primary">
            Go to Settings
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb and Header */}
      <div className="page-header border-0 pb-0 mb-0">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-4">
            <Link
              href="/admin/settings"
              className="text-sm text-text-muted hover:text-accent transition-colors flex items-center gap-1"
            >
              <ChevronLeft className="w-4 h-4" />
              System Settings
            </Link>
            <span className="text-text-muted">/</span>
            <span className="text-sm text-text-primary">{config.label}</span>
          </div>

          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg bg-accent-subtle ${config.color}`}>
              <Icon className="w-5 h-5" />
            </div>
            <div>
              <h1 className="page-title">{config.label}</h1>
              <p className="page-description">{config.description}</p>
            </div>
          </div>
        </div>

        {/* Refresh Button */}
        <button
          onClick={() => refetch()}
          disabled={isLoading}
          className="btn btn--secondary btn--sm"
          title="Refresh settings"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="card p-6">
          <div className="animate-pulse space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="py-4 border-b border-border last:border-b-0">
                <div className="flex items-center justify-between mb-2">
                  <div className="h-4 bg-surface-overlay rounded w-1/4" />
                  <div className="h-4 bg-surface-overlay rounded w-16" />
                </div>
                <div className="h-4 bg-surface-overlay rounded w-3/4 mb-3" />
                <div className="h-10 bg-surface-overlay rounded w-full max-w-xl" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="card p-6 border-danger/50 bg-danger-subtle">
          <div className="flex items-start gap-4">
            <AlertCircle className="w-5 h-5 text-danger flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-medium text-danger mb-1">
                Failed to load settings
              </h3>
              <p className="text-sm text-danger/80 mb-4">
                {error instanceof Error ? error.message : "An unexpected error occurred"}
              </p>
              <button onClick={() => refetch()} className="btn btn--danger btn--sm">
                Try Again
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Settings Form */}
      {settings && (
        <SettingsFormRenderer
          settings={settings}
          onSaveSuccess={() => refetch()}
        />
      )}
    </div>
  );
}
