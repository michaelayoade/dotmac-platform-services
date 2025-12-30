"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Plus,
  Search,
  Mail,
  Play,
  Pause,
  Trash2,
  MoreHorizontal,
  CheckCircle,
  AlertTriangle,
} from "lucide-react";
import { format } from "date-fns";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  useDunningCampaigns,
  useActivateDunningCampaign,
  usePauseDunningCampaign,
  useDeleteDunningCampaign,
  type DunningCampaign,
  type DunningCampaignStatus,
  type ListDunningCampaignsParams,
} from "@/lib/hooks/api/use-billing";

const statusConfig: Record<DunningCampaignStatus, { label: string; class: string }> = {
  active: { label: "Active", class: "bg-status-success/15 text-status-success" },
  paused: { label: "Paused", class: "bg-status-warning/15 text-status-warning" },
  draft: { label: "Draft", class: "bg-surface-overlay text-text-muted" },
  archived: { label: "Archived", class: "bg-surface-overlay text-text-muted" },
};

export default function DunningCampaignsPage() {
  const { toast } = useToast();
  const [filters, setFilters] = useState<ListDunningCampaignsParams>({
    page: 1,
    pageSize: 20,
  });
  const [searchTerm, setSearchTerm] = useState("");

  const { data: campaignsData, isLoading } = useDunningCampaigns(filters);
  const activateCampaign = useActivateDunningCampaign();
  const pauseCampaign = usePauseDunningCampaign();
  const deleteCampaign = useDeleteDunningCampaign();

  const campaigns = campaignsData?.items ?? [];
  const totalPages = campaignsData?.totalPages ?? 1;
  const total = campaignsData?.total ?? 0;

  const handleActivate = async (campaign: DunningCampaign) => {
    try {
      await activateCampaign.mutateAsync(campaign.id);
      toast({
        title: "Campaign activated",
        description: `"${campaign.name}" is now running.`,
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to activate campaign.",
        variant: "error",
      });
    }
  };

  const handlePause = async (campaign: DunningCampaign) => {
    try {
      await pauseCampaign.mutateAsync(campaign.id);
      toast({
        title: "Campaign paused",
        description: `"${campaign.name}" has been paused.`,
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to pause campaign.",
        variant: "error",
      });
    }
  };

  const handleDelete = async (campaign: DunningCampaign) => {
    if (!confirm(`Are you sure you want to delete "${campaign.name}"?`)) return;

    try {
      await deleteCampaign.mutateAsync(campaign.id);
      toast({
        title: "Campaign deleted",
        description: `"${campaign.name}" has been deleted.`,
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to delete campaign.",
        variant: "error",
      });
    }
  };

  const filteredCampaigns = campaigns.filter((c) =>
    c.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (isLoading) {
    return <CampaignsPageSkeleton />;
  }

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="Dunning Campaigns"
        breadcrumbs={[
          { label: "Billing", href: "/billing" },
          { label: "Dunning", href: "/billing/dunning" },
          { label: "Campaigns" },
        ]}
        actions={
          <Link href="/billing/dunning/campaigns/new">
            <Button className="shadow-glow-sm hover:shadow-glow">
              <Plus className="w-4 h-4 mr-2" />
              New Campaign
            </Button>
          </Link>
        }
      />

      {/* Filter Bar */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
            <Input
              type="text"
              placeholder="Search campaigns..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <div className="flex items-center gap-2">
            <StatusFilterButton
              status={undefined}
              label="All"
              currentStatus={filters.status}
              onClick={() => setFilters((prev) => ({ ...prev, status: undefined, page: 1 }))}
            />
            <StatusFilterButton
              status="active"
              label="Active"
              currentStatus={filters.status}
              onClick={() => setFilters((prev) => ({ ...prev, status: "active", page: 1 }))}
            />
            <StatusFilterButton
              status="paused"
              label="Paused"
              currentStatus={filters.status}
              onClick={() => setFilters((prev) => ({ ...prev, status: "paused", page: 1 }))}
            />
            <StatusFilterButton
              status="draft"
              label="Draft"
              currentStatus={filters.status}
              onClick={() => setFilters((prev) => ({ ...prev, status: "draft", page: 1 }))}
            />
          </div>
        </div>
      </Card>

      {/* Campaigns Table */}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          {filteredCampaigns.length > 0 ? (
            <table className="data-table" aria-label="Dunning campaigns"><caption className="sr-only">Dunning campaigns</caption>
              <thead>
                <tr>
                  <th>Campaign</th>
                  <th>Trigger</th>
                  <th>Steps</th>
                  <th>Status</th>
                  <th>Stats</th>
                  <th>Created</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filteredCampaigns.map((campaign) => (
                  <CampaignRow
                    key={campaign.id}
                    campaign={campaign}
                    onActivate={() => handleActivate(campaign)}
                    onPause={() => handlePause(campaign)}
                    onDelete={() => handleDelete(campaign)}
                    isActivating={activateCampaign.isPending}
                    isPausing={pauseCampaign.isPending}
                  />
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-12 text-center">
              <Mail className="w-12 h-12 mx-auto text-text-muted mb-4" />
              <h3 className="text-lg font-semibold text-text-primary mb-2">No campaigns found</h3>
              <p className="text-text-muted mb-6">
                {filters.status || searchTerm
                  ? "Try adjusting your filters"
                  : "Create your first dunning campaign to automate payment recovery"}
              </p>
              {!filters.status && !searchTerm && (
                <Link href="/billing/dunning/campaigns/new">
                  <Button className="shadow-glow-sm hover:shadow-glow">
                    <Plus className="w-4 h-4 mr-2" />
                    Create Campaign
                  </Button>
                </Link>
              )}
            </div>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between p-4 border-t border-border">
            <p className="text-sm text-text-muted">
              Showing {campaigns.length} of {total} campaigns
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

function StatusFilterButton({
  status,
  label,
  currentStatus,
  onClick,
}: {
  status: DunningCampaignStatus | undefined;
  label: string;
  currentStatus: DunningCampaignStatus | undefined;
  onClick: () => void;
}) {
  const isActive = status === currentStatus;

  return (
    <Button
      variant={isActive ? "default" : "outline"}
      size="sm"
      onClick={onClick}
      className={cn(isActive && "shadow-glow-sm")}
    >
      {label}
    </Button>
  );
}

function CampaignRow({
  campaign,
  onActivate,
  onPause,
  onDelete,
  isActivating,
  isPausing,
}: {
  campaign: DunningCampaign;
  onActivate: () => void;
  onPause: () => void;
  onDelete: () => void;
  isActivating: boolean;
  isPausing: boolean;
}) {
  const config = statusConfig[campaign.status];

  return (
    <tr className="group">
      <td>
        <div>
          <Link
            href={`/billing/dunning/campaigns/${campaign.id}`}
            className="font-medium text-text-primary hover:text-accent"
          >
            {campaign.name}
          </Link>
          {campaign.description && (
            <p className="text-xs text-text-muted truncate max-w-xs">{campaign.description}</p>
          )}
        </div>
      </td>
      <td>
        <span className="text-sm text-text-muted">
          {campaign.triggerDaysAfterDue} days overdue
        </span>
      </td>
      <td>
        <div className="flex items-center gap-2">
          <span className="text-sm text-text-primary">{campaign.steps.length} steps</span>
          {campaign.autoSuspendAfterDays && (
            <span
              className="text-xs text-status-warning"
              title={`Auto-suspend after ${campaign.autoSuspendAfterDays} days`}
            >
              <AlertTriangle className="w-3 h-3" />
            </span>
          )}
        </div>
      </td>
      <td>
        <span className={cn("status-badge", config.class)}>{config.label}</span>
      </td>
      <td>
        {campaign.stats ? (
          <div className="text-sm">
            <div className="flex items-center gap-2">
              <span className="text-text-muted">{campaign.stats.totalExecutions} total</span>
              {campaign.stats.recoveryRate > 0 && (
                <span className="text-status-success">
                  {(campaign.stats.recoveryRate * 100).toFixed(0)}% rate
                </span>
              )}
            </div>
          </div>
        ) : (
          <span className="text-sm text-text-muted">—</span>
        )}
      </td>
      <td>
        <span className="text-sm text-text-muted tabular-nums">
          {format(new Date(campaign.createdAt), "MMM d, yyyy")}
        </span>
      </td>
      <td>
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          {campaign.status === "active" ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={onPause}
              disabled={isPausing}
              title="Pause campaign"
            >
              <Pause className="w-4 h-4" />
            </Button>
          ) : campaign.status !== "archived" ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={onActivate}
              disabled={isActivating}
              title="Activate campaign"
            >
              <Play className="w-4 h-4" />
            </Button>
          ) : null}
          <Button
            variant="ghost"
            size="sm"
            onClick={onDelete}
            title="Delete campaign"
            className="text-status-error hover:text-status-error"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
          <Link href={`/billing/dunning/campaigns/${campaign.id}`}>
            <Button variant="ghost" size="sm" title="Edit campaign">
              <MoreHorizontal className="w-4 h-4" />
            </Button>
          </Link>
        </div>
      </td>
    </tr>
  );
}

function CampaignsPageSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center justify-between">
        <div>
          <div className="h-4 w-32 bg-surface-overlay rounded mb-2" />
          <div className="h-8 w-48 bg-surface-overlay rounded" />
        </div>
        <div className="h-10 w-32 bg-surface-overlay rounded" />
      </div>

      <div className="card p-4">
        <div className="flex gap-4">
          <div className="flex-1 h-10 bg-surface-overlay rounded" />
          <div className="h-10 w-48 bg-surface-overlay rounded" />
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
