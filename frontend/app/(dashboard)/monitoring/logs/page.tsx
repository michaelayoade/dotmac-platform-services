"use client";

import { useMemo, useState } from "react";
import {
  FileText,
  Search,
  Filter,
  RefreshCcw,
  Download,
  AlertCircle,
  AlertTriangle,
  Info,
  Bug,
  Clock,
  Server,
  ChevronDown,
  ChevronRight,
  X,
} from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";
import { Button, Card, Input, Modal } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  useLogs,
  useLogServices,
  useLogStats,
  useExportLogs,
} from "@/lib/hooks/api/use-monitoring";
import type { LogLevel } from "@/lib/api/monitoring";

const levelConfig: Record<LogLevel, { label: string; color: string; icon: React.ElementType }> = {
  CRITICAL: { label: "Critical", color: "text-status-error bg-status-error/20", icon: AlertCircle },
  ERROR: { label: "Error", color: "text-status-error bg-status-error/15", icon: AlertCircle },
  WARNING: { label: "Warning", color: "text-status-warning bg-status-warning/15", icon: AlertTriangle },
  INFO: { label: "Info", color: "text-status-info bg-status-info/15", icon: Info },
  DEBUG: { label: "Debug", color: "text-text-muted bg-surface-overlay", icon: Bug },
};

export default function LogsPage() {
  const { toast } = useToast();
  const logStatsRange = useMemo(() => {
    const endTime = new Date();
    const startTime = new Date(endTime.getTime() - 24 * 60 * 60 * 1000);
    return { startTime: startTime.toISOString(), endTime: endTime.toISOString() };
  }, []);

  const [searchQuery, setSearchQuery] = useState("");
  const [levelFilter, setLevelFilter] = useState<LogLevel | "all">("all");
  const [serviceFilter, setServiceFilter] = useState<string>("all");
  const [page, setPage] = useState(1);
  const [expandedLogs, setExpandedLogs] = useState<Set<string>>(new Set());
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportFormat, setExportFormat] = useState<"json" | "csv">("json");

  const { data, isLoading, refetch } = useLogs({
    page,
    pageSize: 50,
    search: searchQuery || undefined,
    level: levelFilter === "all" ? undefined : levelFilter,
    service: serviceFilter !== "all" ? serviceFilter : undefined,
  });
  const { data: services } = useLogServices();
  const { data: stats } = useLogStats(logStatsRange);

  const exportLogs = useExportLogs();

  const logs = data?.logs || [];
  const totalPages = data?.pageCount || 1;
  const levelCounts = stats?.byLevel ?? ({} as Record<LogLevel, number>);
  const totalCount = stats?.total ?? 0;
  const errorCount = (levelCounts.ERROR ?? 0) + (levelCounts.CRITICAL ?? 0);
  const warningCount = levelCounts.WARNING ?? 0;
  const infoCount = levelCounts.INFO ?? 0;
  const debugCount = levelCounts.DEBUG ?? 0;

  const toggleExpanded = (id: string) => {
    const newExpanded = new Set(expandedLogs);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedLogs(newExpanded);
  };

  const handleExport = async () => {
    try {
      const result = await exportLogs.mutateAsync({
        format: exportFormat,
        level: levelFilter === "all" ? undefined : levelFilter,
        service: serviceFilter !== "all" ? serviceFilter : undefined,
      });

      // Create download link
      const url = URL.createObjectURL(result);
      const a = document.createElement("a");
      a.href = url;
      a.download = `logs-export-${format(new Date(), "yyyy-MM-dd")}.${exportFormat}`;
      a.click();
      URL.revokeObjectURL(url);

      toast({ title: "Logs exported successfully" });
      setShowExportModal(false);
    } catch {
      toast({ title: "Failed to export logs", variant: "error" });
    }
  };

  const clearFilters = () => {
    setSearchQuery("");
    setLevelFilter("all");
    setServiceFilter("all");
    setPage(1);
  };

  const hasActiveFilters = searchQuery || levelFilter !== "all" || serviceFilter !== "all";

  if (isLoading) {
    return <LogsSkeleton />;
  }

  return (
    <div className="space-y-6 animate-fade-up">
      <PageHeader
        title="Logs Explorer"
        description="Search and analyze application logs"
        breadcrumbs={[
          { label: "Monitoring", href: "/monitoring" },
          { label: "Logs" },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={() => refetch()}>
              <RefreshCcw className="w-4 h-4" />
            </Button>
            <Button variant="outline" onClick={() => setShowExportModal(true)}>
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        }
      />

      {/* Stats Summary */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Total (24h)</p>
          <p className="text-2xl font-semibold text-text-primary">
            {totalCount.toLocaleString()}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Errors</p>
          <p className="text-2xl font-semibold text-status-error">
            {errorCount.toLocaleString()}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Warnings</p>
          <p className="text-2xl font-semibold text-status-warning">
            {warningCount.toLocaleString()}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Info</p>
          <p className="text-2xl font-semibold text-status-info">
            {infoCount.toLocaleString()}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Debug</p>
          <p className="text-2xl font-semibold text-text-muted">
            {debugCount.toLocaleString()}
          </p>
        </Card>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="relative flex-1 min-w-[200px] max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
            <Input
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(1);
              }}
              placeholder="Search logs..."
              className="pl-10"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-text-muted" />
            <select
              value={levelFilter}
              onChange={(e) => {
                setLevelFilter(e.target.value as LogLevel | "all");
                setPage(1);
              }}
              className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
            >
              <option value="all">All Levels</option>
              <option value="CRITICAL">Critical</option>
              <option value="ERROR">Error</option>
              <option value="WARNING">Warning</option>
              <option value="INFO">Info</option>
              <option value="DEBUG">Debug</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-text-muted" />
            <select
              value={serviceFilter}
              onChange={(e) => {
                setServiceFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
            >
              <option value="all">All Services</option>
              {services?.map((service) => (
                <option key={service} value={service}>
                  {service}
                </option>
              ))}
            </select>
          </div>

          {hasActiveFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              <X className="w-4 h-4 mr-1" />
              Clear
            </Button>
          )}
        </div>
      </Card>

      {/* Logs List */}
      {logs.length === 0 ? (
        <Card className="p-12 text-center">
          <FileText className="w-12 h-12 text-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">No logs found</h3>
          <p className="text-text-muted">
            {hasActiveFilters
              ? "Try adjusting your filters"
              : "Logs will appear here as they are generated"}
          </p>
        </Card>
      ) : (
        <Card className="overflow-hidden">
          <div className="divide-y divide-border-subtle">
            {logs.map((log) => {
              const level = levelConfig[log.level];
              const LevelIcon = level.icon;
              const isExpanded = expandedLogs.has(log.id);

              return (
                <div
                  key={log.id}
                  className={cn(
                    "p-4 hover:bg-surface-overlay/50 transition-colors",
                    (log.level === "ERROR" || log.level === "CRITICAL") &&
                      "border-l-2 border-l-status-error"
                  )}
                >
                  <div
                    className="flex items-start gap-4 cursor-pointer"
                    onClick={() => toggleExpanded(log.id)}
                  >
                    <button className="mt-1">
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-text-muted" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-text-muted" />
                      )}
                    </button>
                    <span
                      className={cn(
                        "inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium shrink-0",
                        level.color
                      )}
                    >
                      <LevelIcon className="w-3 h-3" />
                      {level.label}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-text-primary font-mono text-sm truncate">
                        {log.message}
                      </p>
                      <div className="flex items-center gap-4 mt-1 text-xs text-text-muted">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {format(new Date(log.timestamp), "MMM d, HH:mm:ss.SSS")}
                        </span>
                        <span className="flex items-center gap-1">
                          <Server className="w-3 h-3" />
                          {log.service}
                        </span>
                        {log.traceId && (
                          <span className="font-mono">trace: {log.traceId.slice(0, 8)}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="mt-4 ml-8 p-4 bg-surface-primary rounded-lg border border-border-subtle">
                      <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                        <div>
                          <p className="text-text-muted mb-1">Service</p>
                          <p className="text-text-primary">{log.service}</p>
                        </div>
                        <div>
                          <p className="text-text-muted mb-1">Timestamp</p>
                          <p className="text-text-primary font-mono">
                            {format(new Date(log.timestamp), "yyyy-MM-dd HH:mm:ss.SSS")}
                          </p>
                        </div>
                        {log.traceId && (
                          <div>
                            <p className="text-text-muted mb-1">Trace ID</p>
                            <p className="text-text-primary font-mono">{log.traceId}</p>
                          </div>
                        )}
                        {log.spanId && (
                          <div>
                            <p className="text-text-muted mb-1">Span ID</p>
                            <p className="text-text-primary font-mono">{log.spanId}</p>
                          </div>
                        )}
                      </div>
                      <div>
                        <p className="text-text-muted mb-1">Full Message</p>
                        <pre className="text-sm text-text-primary bg-surface-overlay p-3 rounded overflow-auto max-h-48 font-mono whitespace-pre-wrap">
                          {log.message}
                        </pre>
                      </div>
                      {log.metadata && Object.keys(log.metadata).length > 0 && (
                        <div className="mt-4">
                          <p className="text-text-muted mb-1">Metadata</p>
                          <pre className="text-xs text-text-secondary bg-surface-overlay p-3 rounded overflow-auto max-h-32 font-mono">
                            {JSON.stringify(log.metadata, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-border-subtle">
              <p className="text-sm text-text-muted">
                Page {page} of {totalPages}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Export Modal */}
      <Modal open={showExportModal} onOpenChange={setShowExportModal}>
        <div className="p-6 max-w-md">
          <h2 className="text-xl font-semibold text-text-primary mb-2">Export Logs</h2>
          <p className="text-text-muted mb-6">
            Download logs with current filters applied
          </p>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Export Format
              </label>
              <select
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value as "json" | "csv")}
                className="w-full px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
              >
                <option value="json">JSON</option>
                <option value="csv">CSV</option>
              </select>
            </div>
            {hasActiveFilters && (
              <div className="p-3 bg-surface-overlay rounded-lg">
                <p className="text-sm text-text-muted">Active filters will be applied:</p>
                <div className="flex flex-wrap gap-2 mt-2">
                  {searchQuery && (
                    <span className="px-2 py-0.5 bg-surface-primary rounded text-xs text-text-secondary">
                      Search: &quot;{searchQuery}&quot;
                    </span>
                  )}
                  {levelFilter !== "all" && (
                    <span className="px-2 py-0.5 bg-surface-primary rounded text-xs text-text-secondary">
                      Level: {levelConfig[levelFilter]?.label ?? levelFilter}
                    </span>
                  )}
                  {serviceFilter !== "all" && (
                    <span className="px-2 py-0.5 bg-surface-primary rounded text-xs text-text-secondary">
                      Service: {serviceFilter}
                    </span>
                  )}
                </div>
              </div>
            )}
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="ghost" onClick={() => setShowExportModal(false)}>
                Cancel
              </Button>
              <Button onClick={handleExport} disabled={exportLogs.isPending}>
                {exportLogs.isPending ? "Exporting..." : "Export"}
              </Button>
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
}

function LogsSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 w-48 bg-surface-overlay rounded" />
      <div className="grid grid-cols-5 gap-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="card p-4 h-20" />
        ))}
      </div>
      <div className="card p-4 h-16" />
      <div className="card">
        <div className="divide-y divide-border-subtle">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
            <div key={i} className="p-4 h-16" />
          ))}
        </div>
      </div>
    </div>
  );
}
