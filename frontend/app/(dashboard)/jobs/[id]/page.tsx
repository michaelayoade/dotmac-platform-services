"use client";

import { use } from "react";
import { useRouter } from "next/navigation";
import {
  Layers,
  Play,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCcw,
  Terminal,
  Info,
} from "lucide-react";
import { format, formatDuration, intervalToDuration } from "date-fns";
import { Button, Card } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { useJob, useJobLogs, useJobProgress, useRetryJob, useCancelJob } from "@/lib/hooks/api/use-jobs";

interface JobDetailPageProps {
  params: Promise<{ id: string }>;
}

const statusConfig = {
  pending: { label: "Pending", color: "bg-status-info/15 text-status-info", icon: Clock },
  running: { label: "Running", color: "bg-accent-subtle text-accent", icon: Play },
  completed: { label: "Completed", color: "bg-status-success/15 text-status-success", icon: CheckCircle2 },
  failed: { label: "Failed", color: "bg-status-error/15 text-status-error", icon: XCircle },
  cancelled: { label: "Cancelled", color: "bg-surface-overlay text-text-muted", icon: AlertCircle },
};

export default function JobDetailPage({ params }: JobDetailPageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();

  const { data: job, isLoading, error, refetch } = useJob(id);
  const { data: progress } = useJobProgress(id);
  const { data: logs } = useJobLogs(id);

  const retryJob = useRetryJob();
  const cancelJob = useCancelJob();

  const handleRetry = async () => {
    try {
      await retryJob.mutateAsync(id);
      toast({ title: "Job retrying" });
    } catch {
      toast({ title: "Failed to retry job", variant: "error" });
    }
  };

  const handleCancel = async () => {
    try {
      await cancelJob.mutateAsync(id);
      toast({ title: "Job cancelled" });
    } catch {
      toast({ title: "Failed to cancel job", variant: "error" });
    }
  };

  if (isLoading) {
    return <JobDetailSkeleton />;
  }

  if (error || !job) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <Layers className="w-12 h-12 text-text-muted mb-4" />
        <h2 className="text-xl font-semibold text-text-primary mb-2">Job not found</h2>
        <p className="text-text-muted mb-6">This job doesn&apos;t exist or has been deleted.</p>
        <Button onClick={() => router.push("/jobs")}>Back to Jobs</Button>
      </div>
    );
  }

  const status = statusConfig[job.status as keyof typeof statusConfig] || statusConfig.pending;
  const StatusIcon = status.icon;

  const duration = job.startedAt && job.completedAt
    ? intervalToDuration({ start: new Date(job.startedAt), end: new Date(job.completedAt) })
    : null;
  const queueName = typeof job.parameters?.queue === "string" ? job.parameters?.queue : "default";
  const errorDetails =
    job.errorMessage ??
    job.errorTraceback ??
    (job.errorDetails ? JSON.stringify(job.errorDetails, null, 2) : null);

  return (
    <div className="space-y-6 animate-fade-up">
      <PageHeader
        title={`Job ${job.id.slice(0, 8)}`}
        breadcrumbs={[
          { label: "Jobs", href: "/jobs" },
          { label: job.id.slice(0, 8) },
        ]}
        badge={
          <span className={cn("inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium", status.color)}>
            <StatusIcon className="w-3 h-3" />
            {status.label}
          </span>
        }
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => refetch()}>
              <RefreshCcw className="w-4 h-4" />
            </Button>
            {job.status === "failed" && (
              <Button onClick={handleRetry}>
                <RefreshCcw className="w-4 h-4 mr-2" />
                Retry
              </Button>
            )}
            {(job.status === "pending" || job.status === "running") && (
              <Button variant="destructive" onClick={handleCancel}>
                <XCircle className="w-4 h-4 mr-2" />
                Cancel
              </Button>
            )}
          </div>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Progress */}
          {(job.status === "running" || job.status === "pending") && progress && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-text-primary mb-4">Progress</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-text-muted">
                      {progress.currentItem || job.description || "Processing..."}
                    </span>
                    <span className="text-sm font-medium text-text-primary">{progress.progressPercent || 0}%</span>
                  </div>
                  <div className="h-3 bg-surface-overlay rounded-full overflow-hidden">
                    <div
                      className="h-full bg-accent rounded-full transition-all duration-500"
                      style={{ width: `${progress.progressPercent || 0}%` }}
                    />
                  </div>
                </div>
                {job.description && (
                  <p className="text-sm text-text-secondary">{job.description}</p>
                )}
              </div>
            </Card>
          )}

          {/* Logs */}
          <Card className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <Terminal className="w-5 h-5 text-text-muted" />
              <h3 className="text-lg font-semibold text-text-primary">Logs</h3>
            </div>
            <div className="bg-surface-primary border border-border-subtle rounded-lg p-4 max-h-[400px] overflow-auto font-mono text-sm">
              {logs && logs.length > 0 ? (
                logs.map((log, i) => (
                  <div
                    key={i}
                    className={cn(
                      "flex items-start gap-3 py-1",
                      log.level === "error" && "text-status-error",
                      log.level === "warn" && "text-status-warning"
                    )}
                  >
                    <span className="text-text-muted shrink-0">
                      {format(new Date(log.timestamp), "HH:mm:ss.SSS")}
                    </span>
                    <span className={cn(
                      "w-12 shrink-0",
                      log.level === "error" && "text-status-error",
                      log.level === "warn" && "text-status-warning",
                      log.level === "info" && "text-status-info"
                    )}>
                      [{log.level.toUpperCase()}]
                    </span>
                    <span className="flex-1 break-all">{log.message}</span>
                  </div>
                ))
              ) : (
                <p className="text-text-muted text-center py-8">No logs available</p>
              )}
            </div>
          </Card>

          {/* Error Details */}
          {job.status === "failed" && errorDetails && (
            <Card className="p-6 border-status-error/50">
              <div className="flex items-center gap-3 mb-4">
                <AlertCircle className="w-5 h-5 text-status-error" />
                <h3 className="text-lg font-semibold text-status-error">Error Details</h3>
              </div>
              <pre className="bg-status-error/10 p-4 rounded-lg text-sm text-status-error overflow-auto">
                {errorDetails}
              </pre>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Job Info */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Details</h3>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-text-muted mb-1">Type</p>
                <p className="text-text-primary font-medium">{job.jobType}</p>
              </div>
              <div>
                <p className="text-sm text-text-muted mb-1">Queue</p>
                <p className="text-text-primary">{queueName}</p>
              </div>
              <div>
                <p className="text-sm text-text-muted mb-1">Created</p>
                <p className="text-text-primary">{format(new Date(job.createdAt), "MMM d, yyyy HH:mm:ss")}</p>
              </div>
              {job.startedAt && (
                <div>
                  <p className="text-sm text-text-muted mb-1">Started</p>
                  <p className="text-text-primary">{format(new Date(job.startedAt), "MMM d, yyyy HH:mm:ss")}</p>
                </div>
              )}
              {job.completedAt && (
                <div>
                  <p className="text-sm text-text-muted mb-1">Completed</p>
                  <p className="text-text-primary">{format(new Date(job.completedAt), "MMM d, yyyy HH:mm:ss")}</p>
                </div>
              )}
              {duration && (
                <div>
                  <p className="text-sm text-text-muted mb-1">Duration</p>
                  <p className="text-text-primary font-mono">
                    {formatDuration(duration, { format: ["hours", "minutes", "seconds"] })}
                  </p>
                </div>
              )}
              <div>
                <p className="text-sm text-text-muted mb-1">Items</p>
                <p className="text-text-primary">
                  {job.itemsProcessed} / {job.itemsTotal ?? "-"}
                </p>
              </div>
            </div>
          </Card>

          {/* Payload */}
          {job.parameters && (
            <Card className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <Info className="w-5 h-5 text-text-muted" />
                <h3 className="text-lg font-semibold text-text-primary">Parameters</h3>
              </div>
              <pre className="bg-surface-overlay p-4 rounded-lg text-xs overflow-auto max-h-48 font-mono">
                {JSON.stringify(job.parameters, null, 2)}
              </pre>
            </Card>
          )}

          {/* Result */}
          {job.result && (
            <Card className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <CheckCircle2 className="w-5 h-5 text-status-success" />
                <h3 className="text-lg font-semibold text-text-primary">Result</h3>
              </div>
              <pre className="bg-surface-overlay p-4 rounded-lg text-xs overflow-auto max-h-48 font-mono">
                {JSON.stringify(job.result, null, 2)}
              </pre>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

function JobDetailSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 w-64 bg-surface-overlay rounded" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6 h-32" />
          <div className="card p-6 h-96" />
        </div>
        <div className="space-y-6">
          <div className="card p-6 h-64" />
          <div className="card p-6 h-48" />
        </div>
      </div>
    </div>
  );
}
