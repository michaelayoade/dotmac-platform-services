"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Layers,
  Play,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Search,
  Filter,
  RefreshCcw,
  Calendar,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { useJobs, useJobsDashboard, useJobStats, useJobQueues, useRetryJob, useCancelJob } from "@/lib/hooks/api/use-jobs";
import type { JobSummary } from "@/lib/api/jobs";
import { DashboardAlerts, DashboardRecentActivity } from "@/components/features/dashboard";

type JobStatus = "pending" | "running" | "completed" | "failed" | "cancelled";

const statusConfig: Record<JobStatus, { label: string; color: string; icon: React.ElementType }> = {
  pending: { label: "Pending", color: "bg-status-info/15 text-status-info", icon: Clock },
  running: { label: "Running", color: "bg-accent-subtle text-accent", icon: Play },
  completed: { label: "Completed", color: "bg-status-success/15 text-status-success", icon: CheckCircle2 },
  failed: { label: "Failed", color: "bg-status-error/15 text-status-error", icon: XCircle },
  cancelled: { label: "Cancelled", color: "bg-surface-overlay text-text-muted", icon: AlertCircle },
};

export default function JobsPage() {
  const { toast } = useToast();

  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<JobStatus | "all">("all");
  const [page, setPage] = useState(1);

  const { data, isLoading, refetch } = useJobs({
    page,
    pageSize: 20,
    jobStatus: statusFilter !== "all" ? statusFilter : undefined,
  });
  const { data: dashboardData } = useJobsDashboard();
  const { data: stats } = useJobStats();
  const { data: queues } = useJobQueues();

  const retryJob = useRetryJob();
  const cancelJob = useCancelJob();

  const jobsData: JobSummary[] = data?.jobs || [];
  const jobs = jobsData.filter((job) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      job.id.toLowerCase().includes(query) ||
      job.title.toLowerCase().includes(query) ||
      job.jobType.toLowerCase().includes(query)
    );
  });
  const totalPages = data?.pageCount || 1;

  const handleRetry = async (id: string) => {
    try {
      await retryJob.mutateAsync(id);
      toast({ title: "Job retrying" });
    } catch {
      toast({ title: "Failed to retry job", variant: "error" });
    }
  };

  const handleCancel = async (id: string) => {
    try {
      await cancelJob.mutateAsync(id);
      toast({ title: "Job cancelled" });
    } catch {
      toast({ title: "Failed to cancel job", variant: "error" });
    }
  };

  if (isLoading) {
    return <JobsSkeleton />;
  }

  return (
    <div className="space-y-8 animate-fade-up">
      <PageHeader
        title="Jobs"
        description="Monitor and manage background jobs"
        actions={
          <div className="flex items-center gap-2">
            <Link href="/jobs/scheduled">
              <Button variant="outline">
                <Calendar className="w-4 h-4 mr-2" />
                Scheduled Jobs
              </Button>
            </Link>
            <Button variant="ghost" onClick={() => refetch()}>
              <RefreshCcw className="w-4 h-4" />
            </Button>
          </div>
        }
      />

      {/* Dashboard Alerts */}
      {dashboardData?.alerts && dashboardData.alerts.length > 0 && (
        <DashboardAlerts alerts={dashboardData.alerts} />
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Pending</p>
          <p className="text-2xl font-semibold text-status-info">{stats?.pendingJobs || 0}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Running</p>
          <p className="text-2xl font-semibold text-accent">{stats?.runningJobs || 0}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Completed</p>
          <p className="text-2xl font-semibold text-status-success">{stats?.completedJobs || 0}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Failed</p>
          <p className="text-2xl font-semibold text-status-error">{stats?.failedJobs || 0}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Avg Duration</p>
          <p className="text-2xl font-semibold text-text-primary">
            {stats?.avgDurationSeconds ? `${Math.round(stats.avgDurationSeconds)}s` : "N/A"}
          </p>
        </Card>
      </div>

      {/* Queue Overview */}
      {queues && queues.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {queues.slice(0, 4).map((queue) => (
            <Card key={queue.name} className="p-4">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-medium text-text-primary">{queue.name}</p>
                <span
                  className={cn(
                    "px-2 py-0.5 rounded-full text-xs",
                    queue.active > 0
                      ? "bg-status-success/15 text-status-success"
                      : "bg-surface-overlay text-text-muted"
                  )}
                >
                  {queue.active > 0 ? "Active" : "Idle"}
                </span>
              </div>
              <div className="flex items-center gap-4 text-sm text-text-muted">
                <span>{queue.size} total</span>
                <span>{queue.active} active</span>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search jobs..."
            className="pl-10"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-text-muted" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as JobStatus | "all")}
            className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
          >
            <option value="all">All Status</option>
            <option value="pending">Pending</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Jobs List */}
      {jobs.length === 0 ? (
        <Card className="p-12 text-center">
          <Layers className="w-12 h-12 text-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">No jobs found</h3>
          <p className="text-text-muted">
            {searchQuery || statusFilter !== "all" ? "Try adjusting your filters" : "Jobs will appear here when created"}
          </p>
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="data-table" aria-label="Background jobs"><caption className="sr-only">Background jobs</caption>
              <thead>
                <tr className="border-b border-border-subtle">
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Job ID</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Type</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Status</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Progress</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Created</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Duration</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => {
                  const status = statusConfig[job.status as JobStatus] || statusConfig.pending;
                  const StatusIcon = status.icon;

                  return (
                    <tr key={job.id} className="border-b border-border-subtle hover:bg-surface-overlay/50">
                      <td className="px-4 py-3">
                        <Link href={`/jobs/${job.id}`} className="text-sm text-accent hover:underline font-mono">
                          {job.id.slice(0, 8)}
                        </Link>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm text-text-primary">{job.jobType}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={cn(
                            "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium",
                            status.color
                          )}
                        >
                          <StatusIcon className="w-3 h-3" />
                          {status.label}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {job.progressPercent !== undefined ? (
                          <div className="w-24">
                            <div className="h-1.5 bg-surface-overlay rounded-full overflow-hidden">
                              <div
                                className="h-full bg-accent rounded-full transition-all"
                                style={{ width: `${job.progressPercent}%` }}
                              />
                            </div>
                            <span className="text-xs text-text-muted">{job.progressPercent}%</span>
                          </div>
                        ) : (
                          <span className="text-sm text-text-muted">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm text-text-muted">
                          {formatDistanceToNow(new Date(job.createdAt), { addSuffix: true })}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm text-text-muted font-mono">
                          {job.durationSeconds ? `${job.durationSeconds}s` : "-"}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          {job.status === "failed" && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleRetry(job.id)}
                            >
                              <RefreshCcw className="w-4 h-4" />
                            </Button>
                          )}
                          {(job.status === "pending" || job.status === "running") && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleCancel(job.id)}
                              className="text-status-error hover:text-status-error"
                            >
                              <XCircle className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
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
    </div>
  );
}

function JobsSkeleton() {
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
