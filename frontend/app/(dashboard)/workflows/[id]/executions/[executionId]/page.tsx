"use client";

import { use } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  GitBranch,
  Play,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCcw,
  Terminal,
  Zap,
  Webhook,
  Calendar,
  MousePointer,
  ChevronRight,
  ArrowLeft,
  StopCircle,
  Info,
} from "lucide-react";
import { format, formatDuration, intervalToDuration, formatDistanceToNow } from "date-fns";
import { Button, Card } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  useWorkflowExecution,
  useExecutionLogs,
  useCancelExecution,
  useRetryExecution,
} from "@/lib/hooks/api/use-workflows";
import type { ExecutionLog } from "@/lib/api/workflows";

interface ExecutionDetailPageProps {
  params: Promise<{ id: string; executionId: string }>;
}

const statusConfig = {
  pending: { label: "Pending", color: "bg-status-info/15 text-status-info", icon: Clock },
  running: { label: "Running", color: "bg-accent-subtle text-accent", icon: Play },
  completed: { label: "Completed", color: "bg-status-success/15 text-status-success", icon: CheckCircle2 },
  failed: { label: "Failed", color: "bg-status-error/15 text-status-error", icon: XCircle },
  cancelled: { label: "Cancelled", color: "bg-surface-overlay text-text-muted", icon: AlertCircle },
};

const triggerConfig = {
  manual: { label: "Manual", icon: MousePointer },
  scheduled: { label: "Scheduled", icon: Calendar },
  webhook: { label: "Webhook", icon: Webhook },
  event: { label: "Event", icon: Zap },
};

export default function ExecutionDetailPage({ params }: ExecutionDetailPageProps) {
  const { id: workflowId, executionId } = use(params);
  const router = useRouter();
  const { toast } = useToast();

  const { data: execution, isLoading, error, refetch } = useWorkflowExecution(workflowId, executionId);
  const { data: logs } = useExecutionLogs(workflowId, executionId);
  const logEntries: ExecutionLog[] = logs ?? [];

  const cancelExecution = useCancelExecution();
  const retryExecution = useRetryExecution();

  const handleCancel = async () => {
    try {
      await cancelExecution.mutateAsync({ workflowId, executionId });
      toast({ title: "Execution cancelled" });
    } catch {
      toast({ title: "Failed to cancel execution", variant: "error" });
    }
  };

  const handleRetry = async () => {
    try {
      await retryExecution.mutateAsync({ workflowId, executionId });
      toast({ title: "Execution retrying" });
    } catch {
      toast({ title: "Failed to retry execution", variant: "error" });
    }
  };

  if (isLoading) {
    return <ExecutionDetailSkeleton />;
  }

  if (error || !execution) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <GitBranch className="w-12 h-12 text-text-muted mb-4" />
        <h2 className="text-xl font-semibold text-text-primary mb-2">Execution not found</h2>
        <p className="text-text-muted mb-6">This execution doesn&apos;t exist or has been deleted.</p>
        <Button onClick={() => router.push(`/workflows/${workflowId}`)}>Back to Workflow</Button>
      </div>
    );
  }

  const status = statusConfig[execution.status as keyof typeof statusConfig] || statusConfig.pending;
  const StatusIcon = status.icon;
  const trigger = triggerConfig[execution.triggerType as keyof typeof triggerConfig] || triggerConfig.manual;
  const TriggerIcon = trigger.icon;

  const duration = execution.startedAt && execution.completedAt
    ? intervalToDuration({
        start: new Date(execution.startedAt),
        end: new Date(execution.completedAt),
      })
    : null;

  return (
    <div className="space-y-6 animate-fade-up">
      <PageHeader
        title={`Execution ${executionId.slice(0, 8)}`}
        breadcrumbs={[
          { label: "Workflows", href: "/workflows" },
          { label: execution.workflowName, href: `/workflows/${workflowId}` },
          { label: `Execution ${executionId.slice(0, 8)}` },
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
            {(execution.status === "pending" || execution.status === "running") && (
              <Button variant="destructive" onClick={handleCancel}>
                <StopCircle className="w-4 h-4 mr-2" />
                Cancel
              </Button>
            )}
            {execution.status === "failed" && (
              <Button onClick={handleRetry}>
                <RefreshCcw className="w-4 h-4 mr-2" />
                Retry
              </Button>
            )}
          </div>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Progress - for running executions */}
          {execution.status === "running" && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-text-primary mb-4">Progress</h3>
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
                  <Play className="w-5 h-5 text-accent animate-pulse" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-text-primary">Execution in progress</p>
                  <p className="text-sm text-text-muted">
                    Started {formatDistanceToNow(new Date(execution.startedAt), { addSuffix: true })}
                  </p>
                </div>
              </div>
            </Card>
          )}

          {/* Step Results */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-6">Step Results</h3>
            {execution.stepResults && execution.stepResults.length > 0 ? (
              <div className="space-y-3">
                {execution.stepResults.map((step, index) => {
                  const stepStatus = statusConfig[step.status as keyof typeof statusConfig] || statusConfig.pending;
                  const StepStatusIcon = stepStatus.icon;

                  return (
                    <div
                      key={step.stepId}
                      className={cn(
                        "flex items-center gap-4 p-4 rounded-lg border",
                        step.status === "failed"
                          ? "border-status-error/30 bg-status-error/5"
                          : "border-border-subtle bg-surface-overlay"
                      )}
                    >
                      <div
                        className={cn(
                          "w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium",
                          step.status === "completed"
                            ? "bg-status-success/15 text-status-success"
                            : step.status === "failed"
                            ? "bg-status-error/15 text-status-error"
                            : step.status === "running"
                            ? "bg-accent-subtle text-accent"
                            : "bg-surface-overlay text-text-muted"
                        )}
                      >
                        {step.status === "completed" || step.status === "failed" ? (
                          <StepStatusIcon className="w-4 h-4" />
                        ) : (
                          index + 1
                        )}
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-text-primary">{step.stepName}</p>
                        <div className="flex items-center gap-4 text-sm text-text-muted">
                          <span className={stepStatus.color.split(" ")[1]}>{stepStatus.label}</span>
                          {step.startedAt && step.completedAt && (
                            <span>
                              {formatDuration(
                                intervalToDuration({
                                  start: new Date(step.startedAt),
                                  end: new Date(step.completedAt),
                                }),
                                { format: ["minutes", "seconds"] }
                              ) || "< 1s"}
                            </span>
                          )}
                        </div>
                        {step.error && (
                          <p className="text-sm text-status-error mt-2">{step.error}</p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-text-muted text-center py-8">No step results available</p>
            )}
          </Card>

          {/* Logs */}
          <Card className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <Terminal className="w-5 h-5 text-text-muted" />
              <h3 className="text-lg font-semibold text-text-primary">Logs</h3>
            </div>
            <div className="bg-surface-primary border border-border-subtle rounded-lg p-4 max-h-[400px] overflow-auto font-mono text-sm">
              {logEntries.length > 0 ? (
                logEntries.map((log, i) => (
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
                    <span
                      className={cn(
                        "w-12 shrink-0",
                        log.level === "error" && "text-status-error",
                        log.level === "warn" && "text-status-warning",
                        log.level === "info" && "text-status-info"
                      )}
                    >
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
          {execution.status === "failed" && execution.error && (
            <Card className="p-6 border-status-error/50">
              <div className="flex items-center gap-3 mb-4">
                <AlertCircle className="w-5 h-5 text-status-error" />
                <h3 className="text-lg font-semibold text-status-error">Error Details</h3>
              </div>
              <pre className="bg-status-error/10 p-4 rounded-lg text-sm text-status-error overflow-auto">
                {execution.error}
              </pre>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Execution Info */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Details</h3>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-text-muted mb-1">Workflow</p>
                <Link
                  href={`/workflows/${workflowId}`}
                  className="text-accent hover:underline"
                >
                  {execution.workflowName}
                </Link>
              </div>
              <div>
                <p className="text-sm text-text-muted mb-1">Trigger</p>
                <div className="flex items-center gap-2">
                  <TriggerIcon className="w-4 h-4 text-text-muted" />
                  <span className="text-text-primary">{trigger.label}</span>
                </div>
              </div>
              <div>
                <p className="text-sm text-text-muted mb-1">Started</p>
                <p className="text-text-primary">
                  {format(new Date(execution.startedAt), "MMM d, yyyy HH:mm:ss")}
                </p>
              </div>
              {execution.completedAt && (
                <div>
                  <p className="text-sm text-text-muted mb-1">Completed</p>
                  <p className="text-text-primary">
                    {format(new Date(execution.completedAt), "MMM d, yyyy HH:mm:ss")}
                  </p>
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
            </div>
          </Card>

          {/* Context */}
          {execution.context && Object.keys(execution.context).length > 0 && (
            <Card className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <Info className="w-5 h-5 text-text-muted" />
                <h3 className="text-lg font-semibold text-text-primary">Context</h3>
              </div>
              <pre className="bg-surface-overlay p-4 rounded-lg text-xs overflow-auto max-h-48 font-mono">
                {JSON.stringify(execution.context, null, 2)}
              </pre>
            </Card>
          )}

          {/* Result */}
          {execution.result && (
            <Card className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <CheckCircle2 className="w-5 h-5 text-status-success" />
                <h3 className="text-lg font-semibold text-text-primary">Result</h3>
              </div>
              <pre className="bg-surface-overlay p-4 rounded-lg text-xs overflow-auto max-h-48 font-mono">
                {JSON.stringify(execution.result, null, 2)}
              </pre>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

function ExecutionDetailSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 w-64 bg-surface-overlay rounded" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6 h-48" />
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
