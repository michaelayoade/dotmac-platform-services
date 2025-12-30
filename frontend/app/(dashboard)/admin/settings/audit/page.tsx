"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ChevronLeft,
  History,
  Download,
  Filter,
  RefreshCw,
  AlertCircle,
  Clock,
  Edit,
  RotateCcw,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useSettingsAuditLogs, useSettingsHealth } from "@/lib/hooks/api/use-admin-settings";
import { categoryOrder, getCategoryConfig } from "@/lib/config/admin-settings";
import { AuditLogTable } from "@/components/features/admin-settings/audit-log-table";
import type { SettingsCategory } from "@/lib/api/admin-settings";

export default function AuditPage() {
  const [categoryFilter, setCategoryFilter] = useState<SettingsCategory | "">("");
  const [limitFilter, setLimitFilter] = useState<number>(100);

  const { data: logs, isLoading, error, refetch } = useSettingsAuditLogs({
    category: categoryFilter || undefined,
    limit: limitFilter,
  });

  const { data: health } = useSettingsHealth();

  // Calculate stats from logs
  const stats = logs ? {
    total: logs.length,
    updates: logs.filter(l => l.action === "update").length,
    restores: logs.filter(l => l.action === "restore").length,
    imports: logs.filter(l => l.action === "import").length,
    uniqueUsers: new Set(logs.map(l => l.userId)).size,
    uniqueCategories: new Set(logs.map(l => l.category)).size,
  } : null;

  const handleExportCSV = () => {
    if (!logs || logs.length === 0) return;

    const headers = ["Timestamp", "User", "Category", "Action", "Changes", "Reason", "IP Address"];
    const rows = logs.map(log => [
      new Date(log.timestamp).toISOString(),
      log.userEmail,
      log.category,
      log.action,
      Object.keys(log.changes).join("; "),
      log.reason || "",
      log.ipAddress || "",
    ]);

    const csv = [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `settings-audit-log-${new Date().toISOString().split("T")[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
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
            <span className="text-sm text-text-primary">Audit Logs</span>
          </div>

          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-accent-subtle">
              <History className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h1 className="page-title">Settings Audit Log</h1>
              <p className="page-description">
                Track all configuration changes and modifications
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            disabled={isLoading}
            className="btn btn--secondary btn--sm"
          >
            <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
            Refresh
          </button>
          <button
            onClick={handleExportCSV}
            disabled={!logs || logs.length === 0}
            className={cn(
              "btn btn--secondary btn--sm",
              (!logs || logs.length === 0) && "opacity-50 cursor-not-allowed"
            )}
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <div className="card p-4">
            <div className="flex items-center gap-3">
              <Clock className="w-5 h-5 text-text-muted" />
              <div>
                <p className="text-sm text-text-muted">Total Entries</p>
                <p className="text-xl font-semibold text-text-primary">{stats.total}</p>
              </div>
            </div>
          </div>
          <div className="card p-4">
            <div className="flex items-center gap-3">
              <Edit className="w-5 h-5 text-accent" />
              <div>
                <p className="text-sm text-text-muted">Updates</p>
                <p className="text-xl font-semibold text-text-primary">{stats.updates}</p>
              </div>
            </div>
          </div>
          <div className="card p-4">
            <div className="flex items-center gap-3">
              <RotateCcw className="w-5 h-5 text-warning" />
              <div>
                <p className="text-sm text-text-muted">Restores</p>
                <p className="text-xl font-semibold text-text-primary">{stats.restores}</p>
              </div>
            </div>
          </div>
          <div className="card p-4">
            <div className="flex items-center gap-3">
              <Download className="w-5 h-5 text-success" />
              <div>
                <p className="text-sm text-text-muted">Imports</p>
                <p className="text-xl font-semibold text-text-primary">{stats.imports}</p>
              </div>
            </div>
          </div>
          <div className="card p-4">
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 flex items-center justify-center">
                <span className="text-lg">👤</span>
              </div>
              <div>
                <p className="text-sm text-text-muted">Unique Users</p>
                <p className="text-xl font-semibold text-text-primary">{stats.uniqueUsers}</p>
              </div>
            </div>
          </div>
          <div className="card p-4">
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 flex items-center justify-center">
                <span className="text-lg">📁</span>
              </div>
              <div>
                <p className="text-sm text-text-muted">Categories</p>
                <p className="text-xl font-semibold text-text-primary">{stats.uniqueCategories}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-text-muted" />
            <span className="text-sm font-medium text-text-primary">Filters:</span>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-sm text-text-muted">Category:</label>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value as SettingsCategory | "")}
              className="input py-1 px-2 text-sm"
            >
              <option value="">All categories</option>
              {categoryOrder.map((cat) => {
                const config = getCategoryConfig(cat);
                return (
                  <option key={cat} value={cat}>
                    {config.label}
                  </option>
                );
              })}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-sm text-text-muted">Limit:</label>
            <select
              value={limitFilter}
              onChange={(e) => setLimitFilter(Number(e.target.value))}
              className="input py-1 px-2 text-sm"
            >
              <option value={50}>50</option>
              <option value={100}>100</option>
              <option value={250}>250</option>
              <option value={500}>500</option>
            </select>
          </div>

          {(categoryFilter || limitFilter !== 100) && (
            <button
              onClick={() => {
                setCategoryFilter("");
                setLimitFilter(100);
              }}
              className="text-sm text-accent hover:underline"
            >
              Clear filters
            </button>
          )}
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="card p-6">
          <div className="animate-pulse space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center gap-4">
                <div className="w-4 h-4 bg-surface-overlay rounded" />
                <div className="h-4 bg-surface-overlay rounded w-32" />
                <div className="h-4 bg-surface-overlay rounded w-40" />
                <div className="h-4 bg-surface-overlay rounded w-24" />
                <div className="h-4 bg-surface-overlay rounded w-16" />
                <div className="h-4 bg-surface-overlay rounded w-20" />
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
                Failed to load audit logs
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

      {/* Audit Log Table */}
      {logs && <AuditLogTable logs={logs} />}
    </div>
  );
}
