"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Search,
  Filter,
  Clock,
  CheckCircle,
  AlertCircle,
  XCircle,
  Loader2,
  Ban,
  User,
  FileText,
  Mail,
} from "lucide-react";
import { format } from "date-fns";
import { Button, Card, Input, Select } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  useDunningExecutions,
  useDunningCampaigns,
  useCancelDunningExecution,
  type DunningExecution,
  type DunningExecutionStatus,
  type ListDunningExecutionsParams,
} from "@/lib/hooks/api/use-billing";

const statusConfig: Record<
  DunningExecutionStatus,
  { icon: typeof Clock; label: string; class: string }
> = {
  pending: { icon: Clock, label: "Pending", class: "bg-surface-overlay text-text-muted" },
  in_progress: { icon: Loader2, label: "In Progress", class: "bg-status-info/15 text-status-info" },
  completed: { icon: CheckCircle, label: "Completed", class: "bg-status-success/15 text-status-success" },
  failed: { icon: AlertCircle, label: "Failed", class: "bg-status-error/15 text-status-error" },
  cancelled: { icon: Ban, label: "Cancelled", class: "bg-surface-overlay text-text-muted" },
};

export default function DunningExecutionsPage() {
  const { toast } = useToast();
  const [filters, setFilters] = useState<ListDunningExecutionsParams>({
    page: 1,
    pageSize: 20,
  });
  const [showFilters, setShowFilters] = useState(false);

  const { data: executionsData, isLoading } = useDunningExecutions(filters);
  const { data: campaignsData } = useDunningCampaigns({ pageSize: 100 });
  const cancelExecution = useCancelDunningExecution();

  const executions = executionsData?.items ?? [];
  const totalPages = executionsData?.totalPages ?? 1;
  const total = executionsData?.total ?? 0;
  const campaigns = campaignsData?.items ?? [];

  const handleCancel = async (execution: DunningExecution) => {
    if (!confirm(`Cancel dunning for ${execution.customerName}?`)) return;

    try {
      await cancelExecution.mutateAsync(execution.id);
      toast({
        title: "Execution cancelled",
        description: `Dunning for ${execution.customerName} has been cancelled.`,
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to cancel execution.",
        variant: "error",
      });
    }
  };

  const handleFilterChange = (key: keyof ListDunningExecutionsParams, value: string | undefined) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value || undefined,
      page: 1,
    }));
  };

  if (isLoading) {
    return <ExecutionsPageSkeleton />;
  }

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="Dunning Executions"
        breadcrumbs={[
          { label: "Billing", href: "/billing" },
          { label: "Dunning", href: "/billing/dunning" },
          { label: "Executions" },
        ]}
      />

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {Object.entries(statusConfig).map(([status, config]) => {
          const count = executions.filter((e) => e.status === status).length;
          const StatusIcon = config.icon;
          return (
            <Card
              key={status}
              className={cn(
                "p-4 cursor-pointer transition-all",
                filters.status === status && "ring-2 ring-accent"
              )}
              onClick={() =>
                handleFilterChange("status", filters.status === status ? undefined : (status as DunningExecutionStatus))
              }
            >
              <div className="flex items-center gap-3">
                <StatusIcon
                  className={cn(
                    "w-5 h-5",
                    status === "in_progress" && "animate-spin",
                    config.class.includes("success")
                      ? "text-status-success"
                      : config.class.includes("error")
                      ? "text-status-error"
                      : config.class.includes("info")
                      ? "text-status-info"
                      : "text-text-muted"
                  )}
                />
                <div>
                  <p className="text-xs text-text-muted">{config.label}</p>
                  <p className="text-lg font-bold text-text-primary">{count}</p>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Filter Bar */}
      <Card className="p-4">
        <div className="flex flex-col gap-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
              <Input
                type="text"
                placeholder="Search by customer..."
                className="pl-10"
              />
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant={showFilters ? "default" : "outline"}
                onClick={() => setShowFilters(!showFilters)}
              >
                <Filter className="w-4 h-4 mr-2" />
                Filters
              </Button>
            </div>
          </div>

          {showFilters && (
            <div className="pt-4 border-t border-border grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">
                  Campaign
                </label>
                <Select
                  value={filters.campaignId || ""}
                  onChange={(e) => handleFilterChange("campaignId", e.target.value)}
                >
                  <option value="">All Campaigns</option>
                  {campaigns.map((campaign) => (
                    <option key={campaign.id} value={campaign.id}>
                      {campaign.name}
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">
                  Status
                </label>
                <Select
                  value={filters.status || ""}
                  onChange={(e) => handleFilterChange("status", e.target.value)}
                >
                  <option value="">All Statuses</option>
                  {Object.entries(statusConfig).map(([status, config]) => (
                    <option key={status} value={status}>
                      {config.label}
                    </option>
                  ))}
                </Select>
              </div>
              <div className="flex items-end">
                <Button
                  variant="ghost"
                  onClick={() =>
                    setFilters({ page: 1, pageSize: 20 })
                  }
                >
                  Clear Filters
                </Button>
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Executions Table */}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          {executions.length > 0 ? (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Customer</th>
                  <th>Invoice</th>
                  <th>Amount</th>
                  <th>Campaign</th>
                  <th>Progress</th>
                  <th>Status</th>
                  <th>Next Action</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {executions.map((execution) => (
                  <ExecutionRow
                    key={execution.id}
                    execution={execution}
                    onCancel={() => handleCancel(execution)}
                    isCancelling={cancelExecution.isPending}
                  />
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-12 text-center">
              <Mail className="w-12 h-12 mx-auto text-text-muted mb-4" />
              <h3 className="text-lg font-semibold text-text-primary mb-2">No executions found</h3>
              <p className="text-text-muted">
                {filters.status || filters.campaignId
                  ? "Try adjusting your filters"
                  : "Dunning executions will appear here when campaigns are triggered"}
              </p>
            </div>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between p-4 border-t border-border">
            <p className="text-sm text-text-muted">
              Showing {executions.length} of {total} executions
            </p>
            <div className="flex items-center gap-2">
              {(filters.page ?? 1) > 1 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setFilters((prev) => ({ ...prev, page: (prev.page ?? 1) - 1 }))
                  }
                >
                  Previous
                </Button>
              )}
              <span className="text-sm text-text-secondary">
                Page {filters.page ?? 1} of {totalPages}
              </span>
              {(filters.page ?? 1) < totalPages && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setFilters((prev) => ({ ...prev, page: (prev.page ?? 1) + 1 }))
                  }
                >
                  Next
                </Button>
              )}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

function ExecutionRow({
  execution,
  onCancel,
  isCancelling,
}: {
  execution: DunningExecution;
  onCancel: () => void;
  isCancelling: boolean;
}) {
  const config = statusConfig[execution.status];
  const StatusIcon = config.icon;
  const canCancel = execution.status === "pending" || execution.status === "in_progress";

  return (
    <tr className="group">
      <td>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-accent-subtle flex items-center justify-center">
            <User className="w-4 h-4 text-accent" />
          </div>
          <div>
            <p className="text-sm font-medium text-text-primary">{execution.customerName}</p>
            <p className="text-xs text-text-muted">{execution.customerEmail}</p>
          </div>
        </div>
      </td>
      <td>
        <Link
          href={`/billing/invoices/${execution.invoiceId}`}
          className="font-mono text-sm text-accent hover:text-accent-hover"
        >
          {execution.invoiceNumber}
        </Link>
      </td>
      <td>
        <span className="font-semibold text-status-warning tabular-nums">
          ${(execution.amount / 100).toLocaleString()}
        </span>
        <span className="text-xs text-text-muted ml-1">{execution.currency}</span>
      </td>
      <td>
        <Link
          href={`/billing/dunning/campaigns/${execution.campaignId}`}
          className="text-sm text-accent hover:text-accent-hover"
        >
          {execution.campaignName}
        </Link>
      </td>
      <td>
        <div className="flex items-center gap-2">
          <div className="flex-1 h-2 bg-surface-overlay rounded-full overflow-hidden">
            <div
              className="h-full bg-accent rounded-full transition-all"
              style={{ width: `${(execution.currentStep / execution.totalSteps) * 100}%` }}
            />
          </div>
          <span className="text-xs text-text-muted tabular-nums">
            {execution.currentStep}/{execution.totalSteps}
          </span>
        </div>
      </td>
      <td>
        <span className={cn("status-badge", config.class)}>
          <StatusIcon
            className={cn("w-3 h-3", execution.status === "in_progress" && "animate-spin")}
          />
          {config.label}
        </span>
      </td>
      <td>
        {execution.nextActionAt ? (
          <span className="text-sm text-text-muted tabular-nums">
            {format(new Date(execution.nextActionAt), "MMM d, h:mm a")}
          </span>
        ) : execution.completedAt ? (
          <span className="text-sm text-text-muted tabular-nums">
            {format(new Date(execution.completedAt), "MMM d")}
          </span>
        ) : (
          <span className="text-sm text-text-muted">—</span>
        )}
      </td>
      <td>
        {canCancel && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onCancel}
            disabled={isCancelling}
            className="opacity-0 group-hover:opacity-100 transition-opacity text-status-error hover:text-status-error"
          >
            <XCircle className="w-4 h-4 mr-1" />
            Cancel
          </Button>
        )}
      </td>
    </tr>
  );
}

function ExecutionsPageSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center justify-between">
        <div>
          <div className="h-4 w-32 bg-surface-overlay rounded mb-2" />
          <div className="h-8 w-48 bg-surface-overlay rounded" />
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="card p-4">
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 bg-surface-overlay rounded" />
              <div>
                <div className="h-3 w-16 bg-surface-overlay rounded mb-2" />
                <div className="h-5 w-8 bg-surface-overlay rounded" />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="card p-4">
        <div className="flex gap-4">
          <div className="flex-1 h-10 bg-surface-overlay rounded" />
          <div className="h-10 w-24 bg-surface-overlay rounded" />
        </div>
      </div>

      <div className="card overflow-hidden">
        <div className="p-4 space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-16 bg-surface-overlay rounded" />
          ))}
        </div>
      </div>
    </div>
  );
}
