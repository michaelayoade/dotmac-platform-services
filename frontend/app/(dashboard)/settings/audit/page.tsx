"use client";

import { useState } from "react";
import {
  FileText,
  Search,
  Download,
  Filter,
  Calendar,
  User,
  Activity,
  Shield,
  AlertTriangle,
  Info,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { format, subDays } from "date-fns";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  useAuditActivities,
  useAuditDashboard,
  useAuditStats,
  useExportAuditActivities,
} from "@/lib/hooks/api/use-audit";
import type { AuditActivityType, AuditSeverity } from "@/lib/api/audit";
import { DashboardAlerts } from "@/components/features/dashboard";

type AuditType = "auth" | "data" | "config" | "admin" | "security";

const severityColors: Record<AuditSeverity, { bg: string; text: string }> = {
  low: { bg: "bg-surface-overlay", text: "text-text-muted" },
  medium: { bg: "bg-status-info/15", text: "text-status-info" },
  high: { bg: "bg-status-warning/15", text: "text-status-warning" },
  critical: { bg: "bg-status-error/15", text: "text-status-error" },
};

const typeIcons: Record<AuditType, React.ElementType> = {
  auth: Shield,
  data: FileText,
  config: Activity,
  admin: User,
  security: AlertTriangle,
};

export default function AuditPage() {
  const { toast } = useToast();

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedType, setSelectedType] = useState<AuditActivityType | "all">("all");
  const [selectedSeverity, setSelectedSeverity] = useState<AuditSeverity | "all">("all");
  const [dateRange, setDateRange] = useState({ start: subDays(new Date(), 7), end: new Date() });
  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});

  const { data, isLoading } = useAuditActivities({
    page: 1,
    pageSize: 50,
    activityType: selectedType !== "all" ? selectedType : undefined,
    severity: selectedSeverity !== "all" ? selectedSeverity : undefined,
  });
  const { data: dashboardData } = useAuditDashboard();
  const { data: stats } = useAuditStats({ periodDays: 30 });
  const exportAudit = useExportAuditActivities();

  const activities = data?.activities || [];
  const normalizedQuery = searchQuery.trim().toLowerCase();
  const filteredActivities = normalizedQuery
    ? activities.filter((activity) => {
        return [
          activity.action,
          activity.description,
          activity.activityType,
          activity.userId,
          activity.resourceType,
          activity.resourceId,
          activity.ipAddress,
        ]
          .filter(Boolean)
          .some((value) => String(value).toLowerCase().includes(normalizedQuery));
      })
    : activities;

  const handleExport = async (fileFormat: "json" | "csv") => {
    try {
      const result = await exportAudit.mutateAsync({
        format: fileFormat,
        startDate: dateRange.start.toISOString(),
        endDate: dateRange.end.toISOString(),
        activityType: selectedType !== "all" ? selectedType : undefined,
        severity: selectedSeverity !== "all" ? selectedSeverity : undefined,
      });

      if (!result.downloadUrl) {
        toast({ title: "Export failed", variant: "error" });
        return;
      }

      const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "";
      const resolvedUrl = result.downloadUrl.startsWith("http")
        ? result.downloadUrl
        : `${apiBaseUrl}${result.downloadUrl}`;
      const url = new URL(resolvedUrl, window.location.origin);
      const a = document.createElement("a");
      a.href = url.toString();
      a.download = `audit-log-${format(new Date(), "yyyy-MM-dd")}.${fileFormat}`;
      a.rel = "noopener";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);

      toast({ title: "Export complete" });
    } catch {
      toast({ title: "Export failed", variant: "error" });
    }
  };

  const toggleRow = (id: string) => {
    setExpandedRows((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  if (isLoading) {
    return <AuditSkeleton />;
  }

  return (
    <div className="space-y-8 animate-fade-up">
      <PageHeader
        title="Audit Log"
        description="Track all system activities and changes"
        breadcrumbs={[
          { label: "Settings", href: "/settings" },
          { label: "Audit Log" },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => handleExport("csv")}>
              <Download className="w-4 h-4 mr-2" />
              Export CSV
            </Button>
            <Button variant="outline" onClick={() => handleExport("json")}>
              <Download className="w-4 h-4 mr-2" />
              Export JSON
            </Button>
          </div>
        }
      />

      {/* Dashboard Alerts */}
      {dashboardData?.alerts && dashboardData.alerts.length > 0 && (
        <DashboardAlerts alerts={dashboardData.alerts} />
      )}

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Card className="p-4">
            <p className="text-sm text-text-muted mb-1">Total Activities</p>
            <p className="text-2xl font-semibold text-text-primary">{stats.totalActivities}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-text-muted mb-1">Auth Events</p>
            <p className="text-2xl font-semibold text-accent">{stats.byType?.auth || 0}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-text-muted mb-1">Data Changes</p>
            <p className="text-2xl font-semibold text-status-info">{stats.byType?.data || 0}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-text-muted mb-1">Config Changes</p>
            <p className="text-2xl font-semibold text-status-warning">{stats.byType?.config || 0}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-text-muted mb-1">Security Events</p>
            <p className="text-2xl font-semibold text-status-error">{stats.byType?.security || 0}</p>
          </Card>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search audit log..."
            className="pl-10"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-text-muted" />
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value as AuditActivityType | "all")}
            className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
          >
            <option value="all">All Types</option>
            <option value="auth">Authentication</option>
            <option value="data">Data Changes</option>
            <option value="config">Configuration</option>
            <option value="admin">Admin Actions</option>
            <option value="security">Security</option>
          </select>
        </div>

          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value as AuditSeverity | "all")}
            className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
          >
          <option value="all">All Severities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>

        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-text-muted" />
          <span className="text-sm text-text-muted">Last 7 days</span>
        </div>
      </div>

      {/* Audit Log Table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="data-table" aria-label="Audit log"><caption className="sr-only">Audit log</caption>
            <thead>
              <tr className="border-b border-border-subtle">
                <th className="text-left text-sm font-medium text-text-muted px-4 py-3 w-8"></th>
                <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Timestamp</th>
                <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Type</th>
                <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Action</th>
                <th className="text-left text-sm font-medium text-text-muted px-4 py-3">User</th>
                <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Severity</th>
                <th className="text-left text-sm font-medium text-text-muted px-4 py-3">IP Address</th>
              </tr>
            </thead>
            <tbody>
              {filteredActivities.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-text-muted">
                    <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>No audit entries found</p>
                  </td>
                </tr>
              ) : (
                filteredActivities.map((activity) => {
                  const TypeIcon = typeIcons[activity.activityType as AuditType] || Info;
                  const severity = severityColors[activity.severity as AuditSeverity] || severityColors.low;
                  const isExpanded = expandedRows[activity.id];

                  return (
                    <>
                      <tr
                        key={activity.id}
                        className="border-b border-border-subtle hover:bg-surface-overlay/50 cursor-pointer"
                        onClick={() => toggleRow(activity.id)}
                      >
                        <td className="px-4 py-3">
                          {isExpanded ? (
                            <ChevronDown className="w-4 h-4 text-text-muted" />
                          ) : (
                            <ChevronRight className="w-4 h-4 text-text-muted" />
                          )}
                        </td>
                        <td className="px-4 py-3 text-sm text-text-primary whitespace-nowrap">
                          {format(new Date(activity.timestamp), "MMM d, HH:mm:ss")}
                        </td>
                        <td className="px-4 py-3">
                          <span className="flex items-center gap-2 text-sm">
                            <TypeIcon className="w-4 h-4 text-text-muted" />
                            <span className="capitalize">{activity.activityType}</span>
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-text-primary">{activity.action}</td>
                        <td className="px-4 py-3">
                          <span className="flex items-center gap-2 text-sm">
                            <div className="w-6 h-6 rounded-full bg-accent-subtle flex items-center justify-center">
                              <User className="w-3 h-3 text-accent" />
                            </div>
                            {activity.userId || "System"}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={cn(
                              "px-2 py-0.5 rounded-full text-xs font-medium capitalize",
                              severity.bg,
                              severity.text
                            )}
                          >
                            {activity.severity}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-text-muted font-mono">
                          {activity.ipAddress || "-"}
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr key={`${activity.id}-details`} className="bg-surface-overlay/30">
                          <td colSpan={7} className="px-4 py-4">
                            <div className="grid grid-cols-2 gap-4 text-sm">
                              <div>
                                <p className="text-text-muted mb-1">Resource</p>
                                <p className="text-text-primary font-mono">{activity.resourceType || "-"}</p>
                              </div>
                              <div>
                                <p className="text-text-muted mb-1">Resource ID</p>
                                <p className="text-text-primary font-mono">{activity.resourceId || "-"}</p>
                              </div>
                              <div>
                                <p className="text-text-muted mb-1">User Agent</p>
                                <p className="text-text-primary text-xs truncate">{activity.userAgent || "-"}</p>
                              </div>
                              <div>
                                <p className="text-text-muted mb-1">Tenant</p>
                                <p className="text-text-primary">{activity.tenantId || "-"}</p>
                              </div>
                              {activity.details && Object.keys(activity.details).length > 0 && (
                                <div className="col-span-2">
                                  <p className="text-text-muted mb-1">Metadata</p>
                                  <pre className="text-xs bg-surface-primary p-2 rounded overflow-auto max-h-32">
                                    {JSON.stringify(activity.details, null, 2)}
                                  </pre>
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

function AuditSkeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      <div className="h-8 w-48 bg-surface-overlay rounded" />
      <div className="grid grid-cols-5 gap-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="card p-4 h-20" />
        ))}
      </div>
      <div className="card">
        <div className="p-4 space-y-4">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
            <div key={i} className="h-12 bg-surface-overlay rounded" />
          ))}
        </div>
      </div>
    </div>
  );
}
