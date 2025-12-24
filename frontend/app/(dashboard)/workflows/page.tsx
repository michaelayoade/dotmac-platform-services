"use client";

import { useState } from "react";
import Link from "next/link";
import {
  GitBranch,
  Play,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Search,
  Filter,
  RefreshCcw,
  Plus,
  Copy,
  Trash2,
  MoreHorizontal,
  Zap,
  TrendingUp,
  Activity,
} from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";
import { Button, Card, Input, Modal } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { ConfirmDialog, useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useWorkflows,
  useWorkflowStats,
  useDeleteWorkflow,
  usePublishWorkflow,
  useUnpublishWorkflow,
  useCloneWorkflow,
  useExecuteWorkflow,
} from "@/lib/hooks/api/use-workflows";

export default function WorkflowsPage() {
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [page, setPage] = useState(1);
  const [showCloneModal, setShowCloneModal] = useState(false);
  const [cloneTarget, setCloneTarget] = useState<{ id: string; name: string } | null>(null);
  const [cloneName, setCloneName] = useState("");

  const { data, isLoading, refetch } = useWorkflows({
    page,
    pageSize: 20,
    search: searchQuery || undefined,
    isActive: statusFilter === "all" ? undefined : statusFilter === "active",
  });
  const { data: stats } = useWorkflowStats();

  const deleteWorkflow = useDeleteWorkflow();
  const publishWorkflow = usePublishWorkflow();
  const unpublishWorkflow = useUnpublishWorkflow();
  const cloneWorkflow = useCloneWorkflow();
  const executeWorkflow = useExecuteWorkflow();

  const workflows = data?.workflows || [];
  const totalPages = data?.pageCount || 1;

  const handleDelete = async (id: string, name: string) => {
    const confirmed = await confirm({
      title: "Delete Workflow",
      description: `Are you sure you want to delete "${name}"? This will remove all versions and execution history.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deleteWorkflow.mutateAsync(id);
        toast({ title: "Workflow deleted" });
      } catch {
        toast({ title: "Failed to delete workflow", variant: "error" });
      }
    }
  };

  const handleToggleActive = async (id: string, isActive: boolean) => {
    try {
      if (isActive) {
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

  const handleClone = async () => {
    if (!cloneTarget || !cloneName.trim()) return;

    try {
      await cloneWorkflow.mutateAsync({ id: cloneTarget.id, newName: cloneName });
      toast({ title: "Workflow cloned" });
      setShowCloneModal(false);
      setCloneTarget(null);
      setCloneName("");
    } catch {
      toast({ title: "Failed to clone workflow", variant: "error" });
    }
  };

  const handleExecute = async (id: string) => {
    try {
      await executeWorkflow.mutateAsync({ workflowId: id });
      toast({ title: "Workflow executed", description: "Check executions for status." });
    } catch {
      toast({ title: "Failed to execute workflow", variant: "error" });
    }
  };

  const openCloneModal = (id: string, name: string) => {
    setCloneTarget({ id, name });
    setCloneName(`${name} (Copy)`);
    setShowCloneModal(true);
  };

  if (isLoading) {
    return <WorkflowsSkeleton />;
  }

  return (
    <div className="space-y-8 animate-fade-up">
      {dialog}

      <PageHeader
        title="Workflows"
        description="Orchestrate and automate complex business processes"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={() => refetch()}>
              <RefreshCcw className="w-4 h-4" />
            </Button>
            <Link href="/workflows/new">
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                New Workflow
              </Button>
            </Link>
          </div>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <GitBranch className="w-5 h-5 text-accent" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Active Workflows</p>
              <p className="text-2xl font-semibold text-text-primary">
                {workflows.filter((w) => w.isActive).length}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5 text-status-success" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Success Rate</p>
              <p className="text-2xl font-semibold text-status-success">
                {stats?.successRate ? `${(stats.successRate * 100).toFixed(1)}%` : "N/A"}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
              <Activity className="w-5 h-5 text-status-info" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Total Executions</p>
              <p className="text-2xl font-semibold text-text-primary">
                {stats?.totalExecutions?.toLocaleString() || 0}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
              <Clock className="w-5 h-5 text-highlight" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Avg Duration</p>
              <p className="text-2xl font-semibold text-text-primary">
                {stats?.avgDuration ? `${(stats.avgDuration / 1000).toFixed(1)}s` : "N/A"}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search workflows..."
            className="pl-10"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-text-muted" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
          >
            <option value="all">All Workflows</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>

      {/* Workflows Grid */}
      {workflows.length === 0 ? (
        <Card className="p-12 text-center">
          <GitBranch className="w-12 h-12 text-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">No workflows found</h3>
          <p className="text-text-muted mb-6">
            {searchQuery || statusFilter !== "all"
              ? "Try adjusting your filters"
              : "Create your first workflow to automate processes"}
          </p>
          <Link href="/workflows/new">
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Create Workflow
            </Button>
          </Link>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {workflows.map((workflow) => (
            <Card key={workflow.id} className="p-6 hover:border-border-strong transition-colors">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      "w-10 h-10 rounded-lg flex items-center justify-center",
                      workflow.isActive ? "bg-status-success/15" : "bg-surface-overlay"
                    )}
                  >
                    <GitBranch
                      className={cn(
                        "w-5 h-5",
                        workflow.isActive ? "text-status-success" : "text-text-muted"
                      )}
                    />
                  </div>
                  <div>
                    <Link
                      href={`/workflows/${workflow.id}`}
                      className="font-semibold text-text-primary hover:text-accent transition-colors"
                    >
                      {workflow.name}
                    </Link>
                    <p className="text-xs text-text-muted">v{workflow.version}</p>
                  </div>
                </div>
                <span
                  className={cn(
                    "px-2 py-0.5 rounded-full text-xs font-medium",
                    workflow.isActive
                      ? "bg-status-success/15 text-status-success"
                      : "bg-surface-overlay text-text-muted"
                  )}
                >
                  {workflow.isActive ? "Active" : "Inactive"}
                </span>
              </div>

              {workflow.description && (
                <p className="text-sm text-text-muted mb-4 line-clamp-2">{workflow.description}</p>
              )}

              <div className="flex items-center gap-4 text-sm text-text-muted mb-4">
                <div className="flex items-center gap-1">
                  <Zap className="w-3.5 h-3.5" />
                  {workflow.steps?.length || 0} steps
                </div>
                {workflow.triggers && workflow.triggers.length > 0 && (
                  <div className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    {workflow.triggers.length} trigger{workflow.triggers.length > 1 ? "s" : ""}
                  </div>
                )}
              </div>

              {workflow.tags && workflow.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-4">
                  {workflow.tags.slice(0, 3).map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-0.5 rounded text-xs bg-surface-overlay text-text-secondary"
                    >
                      {tag}
                    </span>
                  ))}
                  {workflow.tags.length > 3 && (
                    <span className="px-2 py-0.5 rounded text-xs bg-surface-overlay text-text-muted">
                      +{workflow.tags.length - 3}
                    </span>
                  )}
                </div>
              )}

              <div className="flex items-center justify-between pt-4 border-t border-border-subtle">
                <p className="text-xs text-text-muted">
                  Updated {formatDistanceToNow(new Date(workflow.updatedAt), { addSuffix: true })}
                </p>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleExecute(workflow.id)}
                    disabled={!workflow.isActive}
                  >
                    <Play className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => openCloneModal(workflow.id, workflow.name)}
                  >
                    <Copy className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(workflow.id, workflow.name)}
                    className="text-status-error hover:text-status-error"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
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

      {/* Clone Modal */}
      <Modal open={showCloneModal} onOpenChange={setShowCloneModal}>
        <div className="p-6 max-w-md">
          <h2 className="text-xl font-semibold text-text-primary mb-2">Clone Workflow</h2>
          <p className="text-text-muted mb-6">
            Create a copy of &quot;{cloneTarget?.name}&quot;
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

function WorkflowsSkeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      <div className="h-8 w-48 bg-surface-overlay rounded" />
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card p-4 h-20" />
        ))}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="card p-6 h-56" />
        ))}
      </div>
    </div>
  );
}
