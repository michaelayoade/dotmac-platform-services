"use client";

import { useState } from "react";
import {
  Shield,
  AlertTriangle,
  Activity,
  Download,
  Search,
  Clock,
  User,
  Globe,
  ChevronRight,
} from "lucide-react";

import { PageHeader } from "@/components/shared/page-header";
import { Card, Button, Input, Select } from "@dotmac/core";
import { Skeleton } from "@/components/shared/loading-skeleton";
import { cn } from "@/lib/utils";
import {
  useAuditActivities,
  useAuditStats,
  useExportAuditActivities,
  type AuditActivity,
} from "@/lib/hooks/api/use-audit";

type SeverityFilter = "all" | "low" | "medium" | "high" | "critical";
type ActivityTypeFilter = "all" | "auth" | "api" | "system" | "secret" | "user" | "tenant" | "billing" | "admin";

const severityConfig: Record<string, { label: string; color: string; bgColor: string }> = {
  low: { label: "Low", color: "text-text-muted", bgColor: "bg-surface-overlay" },
  medium: { label: "Medium", color: "text-status-info", bgColor: "bg-status-info/15" },
  high: { label: "High", color: "text-status-warning", bgColor: "bg-status-warning/15" },
  critical: { label: "Critical", color: "text-status-error", bgColor: "bg-status-error/15" },
};

const activityTypeLabels: Record<string, string> = {
  auth: "Authentication",
  api: "API Access",
  system: "System",
  secret: "Secrets",
  user: "User Management",
  tenant: "Tenant",
  billing: "Billing",
  admin: "Admin",
  file: "File Operations",
  other: "Other",
};

export default function SecurityPage() {
  const [page, setPage] = useState(1);
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>("all");
  const [typeFilter, setTypeFilter] = useState<ActivityTypeFilter>("all");
  const [searchQuery, setSearchQuery] = useState("");

  const { data: statsData, isLoading: statsLoading } = useAuditStats({ periodDays: 7 });
  const { data: activitiesData, isLoading: activitiesLoading } = useAuditActivities({
    page,
    pageSize: 20,
    severity: severityFilter === "all" ? undefined : severityFilter,
    activityType: typeFilter === "all" ? undefined : typeFilter,
  });
  const exportMutation = useExportAuditActivities();

  const activities = activitiesData?.activities ?? [];
  const totalCount = activitiesData?.totalCount ?? 0;
  const pageCount = activitiesData?.pageCount ?? 1;

  const handleExport = () => {
    exportMutation.mutate({ format: "csv" });
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const getRelativeTime = (timestamp: string) => {
    const now = new Date();
    const date = new Date(timestamp);
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return "Just now";
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Security"
        description="Monitor security events and audit trail"
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={handleExport}
            disabled={exportMutation.isPending}
          >
            <Download className="w-4 h-4 mr-2" />
            Export Logs
          </Button>
        }
      />

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {statsLoading ? (
          <>
            {[1, 2, 3, 4].map((i) => (
              <Card key={i} className="p-4">
                <Skeleton className="h-4 w-24 mb-2" />
                <Skeleton className="h-8 w-16" />
              </Card>
            ))}
          </>
        ) : (
          <>
            <Card className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-accent/15">
                  <Activity className="w-5 h-5 text-accent" />
                </div>
                <div>
                  <p className="text-sm text-text-muted">Total Events (7d)</p>
                  <p className="text-2xl font-semibold text-text-primary">
                    {statsData?.totalActivities?.toLocaleString() ?? 0}
                  </p>
                </div>
              </div>
            </Card>

            <Card className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-status-error/15">
                  <AlertTriangle className="w-5 h-5 text-status-error" />
                </div>
                <div>
                  <p className="text-sm text-text-muted">Critical Events</p>
                  <p className="text-2xl font-semibold text-text-primary">
                    {statsData?.bySeverity?.critical ?? 0}
                  </p>
                </div>
              </div>
            </Card>

            <Card className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-status-warning/15">
                  <Shield className="w-5 h-5 text-status-warning" />
                </div>
                <div>
                  <p className="text-sm text-text-muted">Auth Events</p>
                  <p className="text-2xl font-semibold text-text-primary">
                    {statsData?.byType?.auth ?? 0}
                  </p>
                </div>
              </div>
            </Card>

            <Card className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-status-info/15">
                  <Globe className="w-5 h-5 text-status-info" />
                </div>
                <div>
                  <p className="text-sm text-text-muted">API Events</p>
                  <p className="text-2xl font-semibold text-text-primary">
                    {statsData?.byType?.api ?? 0}
                  </p>
                </div>
              </div>
            </Card>
          </>
        )}
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
              <Input
                placeholder="Search audit logs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Select
              value={severityFilter}
              onValueChange={(val) => setSeverityFilter(val as SeverityFilter)}
              options={[
                { value: "all", label: "All Severity" },
                { value: "low", label: "Low" },
                { value: "medium", label: "Medium" },
                { value: "high", label: "High" },
                { value: "critical", label: "Critical" },
              ]}
              placeholder="Severity"
              className="w-[140px]"
            />

            <Select
              value={typeFilter}
              onValueChange={(val) => setTypeFilter(val as ActivityTypeFilter)}
              options={[
                { value: "all", label: "All Types" },
                { value: "auth", label: "Authentication" },
                { value: "api", label: "API Access" },
                { value: "system", label: "System" },
                { value: "secret", label: "Secrets" },
                { value: "user", label: "User Management" },
                { value: "tenant", label: "Tenant" },
                { value: "billing", label: "Billing" },
                { value: "admin", label: "Admin" },
              ]}
              placeholder="Activity Type"
              className="w-[160px]"
            />
          </div>
        </div>
      </Card>

      {/* Activity List */}
      <Card>
        <div className="divide-y divide-border">
          {activitiesLoading ? (
            <>
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="p-4">
                  <div className="flex items-start gap-4">
                    <Skeleton className="w-10 h-10 rounded-lg" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-48" />
                      <Skeleton className="h-3 w-64" />
                    </div>
                    <Skeleton className="h-6 w-16 rounded-full" />
                  </div>
                </div>
              ))}
            </>
          ) : activities.length === 0 ? (
            <div className="p-8 text-center text-text-muted">
              <Shield className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No audit events found</p>
            </div>
          ) : (
            activities.map((activity) => (
              <ActivityRow
                key={activity.id}
                activity={activity}
                formatTimestamp={formatTimestamp}
                getRelativeTime={getRelativeTime}
              />
            ))
          )}
        </div>

        {/* Pagination */}
        {pageCount > 1 && (
          <div className="flex items-center justify-between p-4 border-t border-border">
            <p className="text-sm text-text-muted">
              Page {page} of {pageCount} ({totalCount} total events)
            </p>
            <div className="flex gap-2">
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
                onClick={() => setPage((p) => Math.min(pageCount, p + 1))}
                disabled={page === pageCount}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

function ActivityRow({
  activity,
  formatTimestamp,
  getRelativeTime,
}: {
  activity: AuditActivity;
  formatTimestamp: (ts: string) => string;
  getRelativeTime: (ts: string) => string;
}) {
  const severity = severityConfig[activity.severity] ?? severityConfig.low;

  return (
    <div className="p-4 hover:bg-surface-overlay/50 transition-colors">
      <div className="flex items-start gap-4">
        <div
          className={cn(
            "p-2 rounded-lg",
            activity.severity === "critical"
              ? "bg-status-error/15"
              : activity.severity === "high"
              ? "bg-status-warning/15"
              : "bg-surface-overlay"
          )}
        >
          <Shield
            className={cn(
              "w-5 h-5",
              activity.severity === "critical"
                ? "text-status-error"
                : activity.severity === "high"
                ? "text-status-warning"
                : "text-text-muted"
            )}
          />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <p className="text-sm font-medium text-text-primary">{activity.action}</p>
            <span
              className={cn(
                "text-2xs font-medium px-2 py-0.5 rounded-full",
                severity.bgColor,
                severity.color
              )}
            >
              {severity.label}
            </span>
          </div>
          <p className="text-sm text-text-secondary mb-2">{activity.description}</p>
          <div className="flex flex-wrap items-center gap-4 text-xs text-text-muted">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {getRelativeTime(activity.timestamp)}
            </span>
            {activity.userId && (
              <span className="flex items-center gap-1">
                <User className="w-3 h-3" />
                {activity.userId}
              </span>
            )}
            {activity.ipAddress && (
              <span className="flex items-center gap-1">
                <Globe className="w-3 h-3" />
                {activity.ipAddress}
              </span>
            )}
            <span className="px-2 py-0.5 rounded bg-surface-overlay text-text-muted">
              {activityTypeLabels[activity.activityType] ?? activity.activityType}
            </span>
          </div>
        </div>

        <ChevronRight className="w-5 h-5 text-text-muted flex-shrink-0" />
      </div>
    </div>
  );
}
