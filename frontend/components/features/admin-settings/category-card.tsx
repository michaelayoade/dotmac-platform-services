"use client";

import Link from "next/link";
import { ChevronRight, AlertTriangle, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";
import { getCategoryConfig } from "@/lib/config/admin-settings";
import type { SettingsCategoryInfo } from "@/lib/api/admin-settings";

interface CategoryCardProps {
  category: SettingsCategoryInfo;
  index: number;
}

export function CategoryCard({ category, index }: CategoryCardProps) {
  const config = getCategoryConfig(category.category);
  const Icon = config.icon;

  return (
    <Link
      href={`/admin/settings/${category.category}`}
      className={cn(
        "card card--interactive p-6 group animate-fade-up"
      )}
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div
          className={cn(
            "p-3 rounded-lg bg-accent-subtle group-hover:bg-accent/20 transition-colors",
            config.color
          )}
        >
          <Icon className="w-5 h-5" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <h3 className="font-semibold text-text-primary group-hover:text-accent transition-colors truncate">
              {config.label}
            </h3>
            <ChevronRight className="w-4 h-4 text-text-muted group-hover:text-accent group-hover:translate-x-0.5 transition-all flex-shrink-0" />
          </div>
          <p className="text-sm text-text-muted mb-3 line-clamp-2">
            {config.description}
          </p>

          {/* Badges */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-2xs px-2 py-0.5 rounded-full bg-surface-overlay text-text-muted">
              {category.fieldsCount} fields
            </span>

            {category.hasSensitiveFields && (
              <span className="text-2xs px-2 py-0.5 rounded-full bg-warning-subtle text-warning flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" />
                Sensitive
              </span>
            )}

            {category.restartRequired && (
              <span className="text-2xs px-2 py-0.5 rounded-full bg-danger-subtle text-danger flex items-center gap-1">
                <RefreshCw className="w-3 h-3" />
                Restart required
              </span>
            )}

            {category.lastUpdated && (
              <span className="text-2xs text-text-muted">
                Updated {formatRelativeTime(category.lastUpdated)}
              </span>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}

function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString();
}
