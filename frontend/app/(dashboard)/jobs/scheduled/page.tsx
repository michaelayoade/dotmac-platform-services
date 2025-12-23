"use client";

import { useState } from "react";
import {
  Calendar,
  Plus,
  Play,
  Pause,
  Trash2,
  Settings,
  Clock,
  RefreshCcw,
} from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";
import { Button, Card, Modal, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useScheduledJobs,
  usePauseScheduledJob,
  useResumeScheduledJob,
  useDeleteScheduledJob,
  useTriggerScheduledJob,
  type ScheduledJob,
} from "@/lib/hooks/api/use-jobs";

export default function ScheduledJobsPage() {
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  const [showCreateModal, setShowCreateModal] = useState(false);

  const { data: jobsData, isLoading, refetch } = useScheduledJobs();
  const jobs: ScheduledJob[] = jobsData ?? [];

  const pauseJob = usePauseScheduledJob();
  const resumeJob = useResumeScheduledJob();
  const deleteJob = useDeleteScheduledJob();
  const triggerJob = useTriggerScheduledJob();

  const handlePause = async (id: string) => {
    try {
      await pauseJob.mutateAsync(id);
      toast({ title: "Job paused" });
    } catch {
      toast({ title: "Failed to pause job", variant: "error" });
    }
  };

  const handleResume = async (id: string) => {
    try {
      await resumeJob.mutateAsync(id);
      toast({ title: "Job resumed" });
    } catch {
      toast({ title: "Failed to resume job", variant: "error" });
    }
  };

  const handleDelete = async (id: string, name: string) => {
    const confirmed = await confirm({
      title: "Delete Scheduled Job",
      description: `Are you sure you want to delete "${name}"? This action cannot be undone.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deleteJob.mutateAsync(id);
        toast({ title: "Job deleted" });
      } catch {
        toast({ title: "Failed to delete job", variant: "error" });
      }
    }
  };

  const handleTrigger = async (id: string) => {
    try {
      await triggerJob.mutateAsync(id);
      toast({ title: "Job triggered", description: "Check the Jobs page for status." });
    } catch {
      toast({ title: "Failed to trigger job", variant: "error" });
    }
  };

  if (isLoading) {
    return <ScheduledJobsSkeleton />;
  }

  return (
    <div className="space-y-8 animate-fade-up">
      {dialog}

      <PageHeader
        title="Scheduled Jobs"
        description="Manage recurring and scheduled background tasks"
        breadcrumbs={[
          { label: "Jobs", href: "/jobs" },
          { label: "Scheduled" },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={() => refetch()}>
              <RefreshCcw className="w-4 h-4" />
            </Button>
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Create Schedule
            </Button>
          </div>
        }
      />

      {/* Jobs List */}
      {jobs.length === 0 ? (
        <Card className="p-12 text-center">
          <Calendar className="w-12 h-12 text-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">No scheduled jobs</h3>
          <p className="text-text-muted mb-6">Create a scheduled job to automate recurring tasks</p>
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Create Schedule
          </Button>
        </Card>
      ) : (
        <div className="space-y-4">
          {jobs.map((job) => {
            const isPaused = !job.isActive;
            const scheduleLabel = job.cronExpression
              ? job.cronExpression
              : job.intervalSeconds
                ? `Every ${Math.round(job.intervalSeconds / 60)} min`
                : "N/A";

            return (
            <Card key={job.id} className="p-6">
              <div className="flex items-start gap-6">
                {/* Icon */}
                <div
                  className={cn(
                    "w-12 h-12 rounded-lg flex items-center justify-center",
                    isPaused ? "bg-status-warning/15" : "bg-status-success/15"
                  )}
                >
                  <Calendar
                    className={cn(
                      "w-6 h-6",
                      isPaused ? "text-status-warning" : "text-status-success"
                    )}
                  />
                </div>

                {/* Content */}
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <h4 className="font-semibold text-text-primary">{job.name}</h4>
                    <span
                      className={cn(
                        "px-2 py-0.5 rounded-full text-xs font-medium",
                        isPaused
                          ? "bg-status-warning/15 text-status-warning"
                          : "bg-status-success/15 text-status-success"
                      )}
                    >
                      {isPaused ? "Paused" : "Active"}
                    </span>
                  </div>

                  {job.description && (
                    <p className="text-sm text-text-muted mb-3">{job.description}</p>
                  )}

                  <div className="flex items-center gap-6 text-sm">
                    <div className="flex items-center gap-2 text-text-muted">
                      <Clock className="w-4 h-4" />
                      <code className="bg-surface-overlay px-2 py-0.5 rounded">{scheduleLabel}</code>
                    </div>
                    <div className="text-text-muted">
                      Next run: {job.nextRunAt ? format(new Date(job.nextRunAt), "MMM d, HH:mm") : "N/A"}
                    </div>
                    <div className="text-text-muted">
                      Last run: {job.lastRunAt ? formatDistanceToNow(new Date(job.lastRunAt), { addSuffix: true }) : "Never"}
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={() => handleTrigger(job.id)}>
                    <Play className="w-4 h-4 mr-1" />
                    Run Now
                  </Button>
                  {isPaused ? (
                    <Button variant="outline" size="sm" onClick={() => handleResume(job.id)}>
                      <Play className="w-4 h-4" />
                    </Button>
                  ) : (
                    <Button variant="outline" size="sm" onClick={() => handlePause(job.id)}>
                      <Pause className="w-4 h-4" />
                    </Button>
                  )}
                  <Button variant="ghost" size="sm">
                    <Settings className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(job.id, job.name)}
                    className="text-status-error hover:text-status-error"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </Card>
          );
          })}
        </div>
      )}

      {/* Create Modal */}
      <Modal open={showCreateModal} onOpenChange={setShowCreateModal}>
        <div className="p-6 max-w-lg">
          <h2 className="text-xl font-semibold text-text-primary mb-6">Create Scheduled Job</h2>
          <form className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Name</label>
              <Input placeholder="daily-cleanup" />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Description</label>
              <Input placeholder="Clean up old temporary files" />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Job Type</label>
              <select className="w-full px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm">
                <option>cleanup</option>
                <option>sync</option>
                <option>report</option>
                <option>backup</option>
                <option>custom</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Cron Expression</label>
              <Input placeholder="0 0 * * *" className="font-mono" />
              <p className="text-xs text-text-muted mt-1">
                Example: &quot;0 0 * * *&quot; runs daily at midnight
              </p>
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="ghost" onClick={() => setShowCreateModal(false)}>
                Cancel
              </Button>
              <Button>Create Schedule</Button>
            </div>
          </form>
        </div>
      </Modal>
    </div>
  );
}

function ScheduledJobsSkeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      <div className="h-8 w-48 bg-surface-overlay rounded" />
      <div className="space-y-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card p-6 h-32" />
        ))}
      </div>
    </div>
  );
}
