"use client";

import { use, useState } from "react";
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
  Copy,
  Trash2,
  Settings,
  Activity,
  ChevronRight,
  Zap,
  Webhook,
  Calendar,
  MousePointer,
  ArrowRight,
  Eye,
  Pause,
  StopCircle,
} from "lucide-react";
import { format, formatDistanceToNow, formatDuration, intervalToDuration } from "date-fns";
import { Button, Card, Modal, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { ConfirmDialog, useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useWorkflow,
  useWorkflowExecutions,
  useWorkflowVersions,
  useDeleteWorkflow,
  usePublishWorkflow,
  useUnpublishWorkflow,
  useCloneWorkflow,
  useExecuteWorkflow,
  useCancelExecution,
  useRetryExecution,
} from "@/lib/hooks/api/use-workflows";

interface WorkflowDetailPageProps {
  params: Promise<{ id: string }>;
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

export default function WorkflowDetailPage({ params }: WorkflowDetailPageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  const [showExecuteModal, setShowExecuteModal] = useState(false);
  const [showCloneModal, setShowCloneModal] = useState(false);
  const [executionContext, setExecutionContext] = useState("");
  const [cloneName, setCloneName] = useState("");
  const [executionsPage, setExecutionsPage] = useState(1);

  const { data: workflow, isLoading, error, refetch } = useWorkflow(id);
  const { data: executionsData } = useWorkflowExecutions(id, { page: executionsPage, pageSize: 10 });
  const { data: versions } = useWorkflowVersions(id);

  const deleteWorkflow = useDeleteWorkflow();
  const publishWorkflow = usePublishWorkflow();
  const unpublishWorkflow = useUnpublishWorkflow();
  const cloneWorkflow = useCloneWorkflow();
  const executeWorkflow = useExecuteWorkflow();
  const cancelExecution = useCancelExecution();
  const retryExecution = useRetryExecution();

  const executions = executionsData?.executions || [];
  const executionsTotalPages = executionsData?.pageCount || 1;

  const handleDelete = async () => {
    const confirmed = await confirm({
      title: "Delete Workflow",
      description: `Are you sure you want to delete "${workflow?.name}"? This will remove all versions and execution history.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deleteWorkflow.mutateAsync(id);
        toast({ title: "Workflow deleted" });
        router.push("/workflows");
      } catch {
        toast({ title: "Failed to delete workflow", variant: "error" });
      }
    }
  };

  const handleToggleActive = async () => {
    if (!workflow) return;

    try {
      if (workflow.isActive) {
        await unpublishWorkflow.mutateAsync(id);
        toast({ title: "Workflow unpublished" });
      } else {
        await publishWorkflow.mutateAsync(id);
        toast({ title: "Workflow published" });
      }
    } catch {
      toast({ title: "Failed to update workflow", variant: "error" });
    }
  };

  const handleExecute = async () => {
    try {
      let context;
      if (executionContext.trim()) {
        context = JSON.parse(executionContext);
      }
      await executeWorkflow.mutateAsync({ workflowId: id, context });
      toast({ title: "Workflow executed" });
      setShowExecuteModal(false);
      setExecutionContext("");
    } catch (e) {
      if (e instanceof SyntaxError) {
        toast({ title: "Invalid JSON context", variant: "error" });
      } else {
        toast({ title: "Failed to execute workflow", variant: "error" });
      }
    }
  };

  const handleClone = async () => {
    if (!cloneName.trim()) return;

    try {
      await cloneWorkflow.mutateAsync({ id, newName: cloneName });
      toast({ title: "Workflow cloned" });
      setShowCloneModal(false);
      setCloneName("");
    } catch {
      toast({ title: "Failed to clone workflow", variant: "error" });
    }
  };

  const handleCancelExecution = async (executionId: string) => {
    try {
      await cancelExecution.mutateAsync({ workflowId: id, executionId });
      toast({ title: "Execution cancelled" });
    } catch {
      toast({ title: "Failed to cancel execution", variant: "error" });
    }
  };

  const handleRetryExecution = async (executionId: string) => {
    try {
      await retryExecution.mutateAsync({ workflowId: id, executionId });
      toast({ title: "Execution retrying" });
    } catch {
      toast({ title: "Failed to retry execution", variant: "error" });
    }
  };

  if (isLoading) {
    return <WorkflowDetailSkeleton />;
  }

  if (error || !workflow) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <GitBranch className="w-12 h-12 text-text-muted mb-4" />
        <h2 className="text-xl font-semibold text-text-primary mb-2">Workflow not found</h2>
        <p className="text-text-muted mb-6">This workflow doesn&apos;t exist or has been deleted.</p>
        <Button onClick={() => router.push("/workflows")}>Back to Workflows</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-up">
      {dialog}

      <PageHeader
        title={workflow.name}
        description={workflow.description}
        breadcrumbs={[
          { label: "Workflows", href: "/workflows" },
          { label: workflow.name },
        ]}
        badge={
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium",
                workflow.isActive
                  ? "bg-status-success/15 text-status-success"
                  : "bg-surface-overlay text-text-muted"
              )}
            >
              {workflow.isActive ? "Active" : "Inactive"}
            </span>
            <span className="text-sm text-text-muted">v{workflow.version}</span>
          </div>
        }
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => refetch()}>
              <RefreshCcw className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleToggleActive}
            >
              {workflow.isActive ? (
                <>
                  <Pause className="w-4 h-4 mr-2" />
                  Unpublish
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Publish
                </>
              )}
            </Button>
            <Button
              onClick={() => setShowExecuteModal(true)}
              disabled={!workflow.isActive}
            >
              <Play className="w-4 h-4 mr-2" />
              Execute
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Steps */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-text-primary">Workflow Steps</h3>
              <span className="text-sm text-text-muted">{workflow.steps?.length || 0} steps</span>
            </div>
            {workflow.steps && workflow.steps.length > 0 ? (
              <div className="space-y-3">
                {workflow.steps.map((step, index) => (
                  <div
                    key={step.id}
                    className="flex items-center gap-4 p-4 bg-surface-overlay rounded-lg"
                  >
                    <div className="w-8 h-8 rounded-full bg-accent-subtle flex items-center justify-center text-accent font-medium text-sm">
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-text-primary">{step.name}</p>
                      <div className="flex items-center gap-4 text-sm text-text-muted">
                        <span>Type: {step.type}</span>
                        {step.retryPolicy && (
                          <span>
                            Retry: {step.retryPolicy.maxRetries}x
                          </span>
                        )}
                      </div>
                    </div>
                    {index < (workflow.steps?.length || 0) - 1 && (
                      <ArrowRight className="w-4 h-4 text-text-muted" />
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-text-muted text-center py-8">No steps configured</p>
            )}
          </Card>

          {/* Executions */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-text-primary">Recent Executions</h3>
              <Link href={`/workflows/${id}/executions`}>
                <Button variant="ghost" size="sm">
                  View All
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </Link>
            </div>
            {executions.length > 0 ? (
              <div className="space-y-3">
                {executions.map((execution) => {
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
                    <div
                      key={execution.id}
                      className="flex items-center gap-4 p-4 bg-surface-overlay rounded-lg"
                    >
                      <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center", status.color.split(" ")[0])}>
                        <StatusIcon className={cn("w-5 h-5", status.color.split(" ")[1])} />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Link
                            href={`/workflows/${id}/executions/${execution.id}`}
                            className="font-medium text-text-primary hover:text-accent transition-colors"
                          >
                            {execution.id.slice(0, 8)}
                          </Link>
                          <span className={cn("px-2 py-0.5 rounded-full text-xs font-medium", status.color)}>
                            {status.label}
                          </span>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-text-muted">
                          <div className="flex items-center gap-1">
                            <TriggerIcon className="w-3.5 h-3.5" />
                            {trigger.label}
                          </div>
                          <span>{formatDistanceToNow(new Date(execution.startedAt), { addSuffix: true })}</span>
                          {duration && (
                            <span>
                              {formatDuration(duration, { format: ["minutes", "seconds"] }) || "< 1s"}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        {(execution.status === "pending" || execution.status === "running") && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleCancelExecution(execution.id)}
                          >
                            <StopCircle className="w-4 h-4" />
                          </Button>
                        )}
                        {execution.status === "failed" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRetryExecution(execution.id)}
                          >
                            <RefreshCcw className="w-4 h-4" />
                          </Button>
                        )}
                        <Link href={`/workflows/${id}/executions/${execution.id}`}>
                          <Button variant="ghost" size="sm">
                            <Eye className="w-4 h-4" />
                          </Button>
                        </Link>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-text-muted text-center py-8">No executions yet</p>
            )}

            {executionsTotalPages > 1 && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-border-subtle">
                <p className="text-sm text-text-muted">
                  Page {executionsPage} of {executionsTotalPages}
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setExecutionsPage((p) => Math.max(1, p - 1))}
                    disabled={executionsPage === 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setExecutionsPage((p) => Math.min(executionsTotalPages, p + 1))}
                    disabled={executionsPage === executionsTotalPages}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Actions */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Actions</h3>
            <div className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => {
                  setCloneName(`${workflow.name} (Copy)`);
                  setShowCloneModal(true);
                }}
              >
                <Copy className="w-4 h-4 mr-2" />
                Clone Workflow
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <Settings className="w-4 h-4 mr-2" />
                Edit Workflow
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start text-status-error hover:text-status-error"
                onClick={handleDelete}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete Workflow
              </Button>
            </div>
          </Card>

          {/* Triggers */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Triggers</h3>
            {workflow.triggers && workflow.triggers.length > 0 ? (
              <div className="space-y-3">
                {workflow.triggers.map((trigger, index) => {
                  const triggerInfo = triggerConfig[trigger.type as keyof typeof triggerConfig] || triggerConfig.manual;
                  const TriggerIcon = triggerInfo.icon;

                  return (
                    <div
                      key={index}
                      className="flex items-center gap-3 p-3 bg-surface-overlay rounded-lg"
                    >
                      <TriggerIcon className="w-5 h-5 text-text-muted" />
                      <div>
                        <p className="font-medium text-text-primary">{triggerInfo.label}</p>
                        <p className="text-xs text-text-muted">
                          {trigger.type === "scheduled" && trigger.config?.cron
                            ? `Cron: ${trigger.config.cron}`
                            : trigger.type === "webhook"
                            ? "Webhook endpoint"
                            : "Manual trigger"}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-text-muted text-sm">No triggers configured</p>
            )}
          </Card>

          {/* Details */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Details</h3>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-text-muted mb-1">Created</p>
                <p className="text-text-primary">
                  {format(new Date(workflow.createdAt), "MMM d, yyyy HH:mm")}
                </p>
              </div>
              <div>
                <p className="text-sm text-text-muted mb-1">Last Updated</p>
                <p className="text-text-primary">
                  {formatDistanceToNow(new Date(workflow.updatedAt), { addSuffix: true })}
                </p>
              </div>
              {versions && versions.length > 0 && (
                <div>
                  <p className="text-sm text-text-muted mb-1">Versions</p>
                  <p className="text-text-primary">{versions.length} version(s)</p>
                </div>
              )}
            </div>
          </Card>

          {/* Tags */}
          {workflow.tags && workflow.tags.length > 0 && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-text-primary mb-4">Tags</h3>
              <div className="flex flex-wrap gap-2">
                {workflow.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2.5 py-1 rounded-full text-sm bg-surface-overlay text-text-secondary"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* Execute Modal */}
      <Modal open={showExecuteModal} onOpenChange={setShowExecuteModal}>
        <div className="p-6 max-w-lg">
          <h2 className="text-xl font-semibold text-text-primary mb-2">Execute Workflow</h2>
          <p className="text-text-muted mb-6">
            Run &quot;{workflow.name}&quot; with optional context data
          </p>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Context (JSON, optional)
              </label>
              <textarea
                value={executionContext}
                onChange={(e) => setExecutionContext(e.target.value)}
                placeholder='{"key": "value"}'
                className="w-full p-3 bg-surface-primary border border-border-subtle rounded-lg text-sm font-mono resize-none min-h-[120px]"
              />
              <p className="text-xs text-text-muted mt-1">
                Pass data to the workflow execution as JSON
              </p>
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="ghost" onClick={() => setShowExecuteModal(false)}>
                Cancel
              </Button>
              <Button onClick={handleExecute}>
                <Play className="w-4 h-4 mr-2" />
                Execute
              </Button>
            </div>
          </div>
        </div>
      </Modal>

      {/* Clone Modal */}
      <Modal open={showCloneModal} onOpenChange={setShowCloneModal}>
        <div className="p-6 max-w-md">
          <h2 className="text-xl font-semibold text-text-primary mb-2">Clone Workflow</h2>
          <p className="text-text-muted mb-6">
            Create a copy of &quot;{workflow.name}&quot;
          </p>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                New Workflow Name
              </label>
              <Input
                value={cloneName}
                onChange={(e) => setCloneName(e.target.value)}
                placeholder="Enter name for the cloned workflow"
              />
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="ghost" onClick={() => setShowCloneModal(false)}>
                Cancel
              </Button>
              <Button onClick={handleClone} disabled={!cloneName.trim()}>
                Clone Workflow
              </Button>
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
}

function WorkflowDetailSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 w-64 bg-surface-overlay rounded" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6 h-64" />
          <div className="card p-6 h-96" />
        </div>
        <div className="space-y-6">
          <div className="card p-6 h-40" />
          <div className="card p-6 h-48" />
          <div className="card p-6 h-32" />
        </div>
      </div>
    </div>
  );
}
