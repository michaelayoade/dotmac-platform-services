"use client";

import Link from "next/link";
import {
  AlertTriangle,
  TrendingUp,
  Clock,
  CheckCircle,
  DollarSign,
  Plus,
  ArrowRight,
  Mail,
  Users,
  Target,
} from "lucide-react";
import { format } from "date-fns";
import { Button, Card } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  useDunningAnalytics,
  useDunningCampaigns,
  useDunningExecutions,
  type DunningExecutionStatus,
} from "@/lib/hooks/api/use-billing";

const executionStatusConfig: Record<
  DunningExecutionStatus,
  { label: string; class: string }
> = {
  pending: { label: "Pending", class: "bg-surface-overlay text-text-muted" },
  in_progress: { label: "In Progress", class: "bg-status-info/15 text-status-info" },
  completed: { label: "Completed", class: "bg-status-success/15 text-status-success" },
  failed: { label: "Failed", class: "bg-status-error/15 text-status-error" },
  cancelled: { label: "Cancelled", class: "bg-surface-overlay text-text-muted" },
};

export default function DunningDashboardPage() {
  const { data: analytics, isLoading: analyticsLoading } = useDunningAnalytics();
  const { data: campaignsData } = useDunningCampaigns({ pageSize: 5 });
  const { data: executionsData } = useDunningExecutions({ pageSize: 10 });

  const campaigns = campaignsData?.items ?? [];
  const executions = executionsData?.items ?? [];

  if (analyticsLoading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="space-y-8 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="Dunning Management"
        breadcrumbs={[
          { label: "Billing", href: "/billing" },
          { label: "Dunning" },
        ]}
        actions={
          <div className="flex items-center gap-3">
            <Link href="/billing/dunning/executions">
              <Button variant="outline">
                <Clock className="w-4 h-4 mr-2" />
                View Executions
              </Button>
            </Link>
            <Link href="/billing/dunning/campaigns/new">
              <Button className="shadow-glow-sm hover:shadow-glow">
                <Plus className="w-4 h-4 mr-2" />
                New Campaign
              </Button>
            </Link>
          </div>
        }
      />

      {/* KPI Tiles */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-status-warning/15 flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-status-warning" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Active Executions</p>
              <p className="text-2xl font-bold text-text-primary">
                {analytics?.summary.totalActiveExecutions || 0}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-status-success/15 flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-status-success" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Recovered This Month</p>
              <p className="text-2xl font-bold text-status-success">
                ${((analytics?.summary.totalRecoveredThisMonth || 0) / 100).toLocaleString()}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-accent-subtle flex items-center justify-center">
              <Target className="w-6 h-6 text-accent" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Recovery Rate</p>
              <p className="text-2xl font-bold text-text-primary">
                {((analytics?.summary.overallRecoveryRate || 0) * 100).toFixed(1)}%
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-highlight-subtle flex items-center justify-center">
              <Clock className="w-6 h-6 text-highlight" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Avg. Recovery Days</p>
              <p className="text-2xl font-bold text-text-primary">
                {analytics?.summary.averageRecoveryDays?.toFixed(1) || 0}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Campaign Performance */}
        <Card className="lg:col-span-2 overflow-hidden">
          <div className="p-6 border-b border-border">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-text-primary">Campaign Performance</h3>
              <Link
                href="/billing/dunning/campaigns"
                className="text-sm text-accent hover:text-accent-hover inline-flex items-center gap-1"
              >
                View all
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
          <div className="overflow-x-auto">
            {analytics?.byCampaign && analytics.byCampaign.length > 0 ? (
              <table className="data-table" aria-label="Campaign performance"><caption className="sr-only">Campaign performance</caption>
                <thead>
                  <tr>
                    <th>Campaign</th>
                    <th className="text-right">Executions</th>
                    <th className="text-right">Recovered</th>
                    <th className="text-right">Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {analytics.byCampaign.map((campaign) => (
                    <tr key={campaign.campaignId}>
                      <td>
                        <Link
                          href={`/billing/dunning/campaigns/${campaign.campaignId}`}
                          className="font-medium text-accent hover:text-accent-hover"
                        >
                          {campaign.campaignName}
                        </Link>
                      </td>
                      <td className="text-right tabular-nums">
                        {campaign.executions}
                      </td>
                      <td className="text-right">
                        <span className="font-semibold text-status-success tabular-nums">
                          ${(campaign.recovered / 100).toLocaleString()}
                        </span>
                      </td>
                      <td className="text-right">
                        <span
                          className={cn(
                            "text-sm font-medium tabular-nums",
                            campaign.recoveryRate >= 0.5
                              ? "text-status-success"
                              : campaign.recoveryRate >= 0.25
                              ? "text-status-warning"
                              : "text-status-error"
                          )}
                        >
                          {(campaign.recoveryRate * 100).toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-8 text-center">
                <Mail className="w-12 h-12 mx-auto text-text-muted mb-4" />
                <p className="text-text-muted">No campaign data available</p>
              </div>
            )}
          </div>
        </Card>

        {/* Status Breakdown */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-text-primary mb-6">Execution Status</h3>
          <div className="space-y-4">
            {analytics?.byStatus ? (
              Object.entries(analytics.byStatus).map(([status, count]) => {
                const config = executionStatusConfig[status as DunningExecutionStatus];
                return (
                  <div
                    key={status}
                    className="flex items-center justify-between p-3 bg-surface-overlay rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <span className={cn("status-badge", config.class)}>
                        {config.label}
                      </span>
                    </div>
                    <span className="text-lg font-bold text-text-primary tabular-nums">
                      {count}
                    </span>
                  </div>
                );
              })
            ) : (
              <div className="text-center py-4">
                <p className="text-text-muted">No status data available</p>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Recent Recoveries & Active Executions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Recoveries */}
        <Card className="overflow-hidden">
          <div className="p-6 border-b border-border">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
                <CheckCircle className="w-5 h-5 text-status-success" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-text-primary">Recent Recoveries</h3>
                <p className="text-sm text-text-muted">Successfully collected payments</p>
              </div>
            </div>
          </div>
          <div className="overflow-x-auto">
            {analytics?.recentRecoveries && analytics.recentRecoveries.length > 0 ? (
              <table className="data-table" aria-label="Recent recoveries"><caption className="sr-only">Recent recoveries</caption>
                <thead>
                  <tr>
                    <th>Invoice</th>
                    <th>Customer</th>
                    <th className="text-right">Amount</th>
                    <th>Recovered</th>
                  </tr>
                </thead>
                <tbody>
                  {analytics.recentRecoveries.map((recovery) => (
                    <tr key={recovery.invoiceId}>
                      <td>
                        <Link
                          href={`/billing/invoices/${recovery.invoiceId}`}
                          className="font-mono text-sm text-accent hover:text-accent-hover"
                        >
                          {recovery.invoiceNumber}
                        </Link>
                      </td>
                      <td>
                        <span className="text-sm text-text-primary">{recovery.customerName}</span>
                      </td>
                      <td className="text-right">
                        <span className="font-semibold text-status-success tabular-nums">
                          ${(recovery.amount / 100).toLocaleString()}
                        </span>
                      </td>
                      <td>
                        <span className="text-sm text-text-muted tabular-nums">
                          {format(new Date(recovery.recoveredAt), "MMM d")}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-8 text-center">
                <CheckCircle className="w-12 h-12 mx-auto text-text-muted mb-4" />
                <p className="text-text-muted">No recent recoveries</p>
              </div>
            )}
          </div>
        </Card>

        {/* Active Executions */}
        <Card className="overflow-hidden">
          <div className="p-6 border-b border-border">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-status-warning/15 flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5 text-status-warning" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-text-primary">Active Executions</h3>
                  <p className="text-sm text-text-muted">In-progress dunning attempts</p>
                </div>
              </div>
              <Link
                href="/billing/dunning/executions"
                className="text-sm text-accent hover:text-accent-hover"
              >
                View all →
              </Link>
            </div>
          </div>
          <div className="overflow-x-auto">
            {executions.filter((e) => e.status === "in_progress" || e.status === "pending").length >
            0 ? (
              <table className="data-table" aria-label="Active dunning executions"><caption className="sr-only">Active dunning executions</caption>
                <thead>
                  <tr>
                    <th>Customer</th>
                    <th className="text-right">Amount</th>
                    <th>Step</th>
                    <th>Next Action</th>
                  </tr>
                </thead>
                <tbody>
                  {executions
                    .filter((e) => e.status === "in_progress" || e.status === "pending")
                    .slice(0, 5)
                    .map((execution) => (
                      <tr key={execution.id}>
                        <td>
                          <span className="text-sm font-medium text-text-primary">
                            {execution.customerName}
                          </span>
                        </td>
                        <td className="text-right">
                          <span className="font-semibold text-status-warning tabular-nums">
                            ${(execution.amount / 100).toLocaleString()}
                          </span>
                        </td>
                        <td>
                          <span className="text-sm text-text-muted">
                            {execution.currentStep}/{execution.totalSteps}
                          </span>
                        </td>
                        <td>
                          {execution.nextActionAt ? (
                            <span className="text-sm text-text-muted tabular-nums">
                              {format(new Date(execution.nextActionAt), "MMM d")}
                            </span>
                          ) : (
                            <span className="text-sm text-text-muted">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            ) : (
              <div className="p-8 text-center">
                <Users className="w-12 h-12 mx-auto text-text-muted mb-4" />
                <p className="text-text-muted">No active executions</p>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Campaigns List */}
      <Card className="overflow-hidden">
        <div className="p-6 border-b border-border">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-text-primary">Dunning Campaigns</h3>
            <Link
              href="/billing/dunning/campaigns"
              className="text-sm text-accent hover:text-accent-hover inline-flex items-center gap-1"
            >
              Manage campaigns
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
        <div className="overflow-x-auto">
          {campaigns.length > 0 ? (
            <table className="data-table" aria-label="Dunning campaigns overview"><caption className="sr-only">Dunning campaigns overview</caption>
              <thead>
                <tr>
                  <th>Campaign</th>
                  <th>Trigger</th>
                  <th>Steps</th>
                  <th>Status</th>
                  <th>Executions</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {campaigns.map((campaign) => (
                  <tr key={campaign.id} className="group">
                    <td>
                      <div>
                        <Link
                          href={`/billing/dunning/campaigns/${campaign.id}`}
                          className="font-medium text-text-primary hover:text-accent"
                        >
                          {campaign.name}
                        </Link>
                        {campaign.description && (
                          <p className="text-xs text-text-muted truncate max-w-xs">
                            {campaign.description}
                          </p>
                        )}
                      </div>
                    </td>
                    <td>
                      <span className="text-sm text-text-muted">
                        {campaign.triggerDaysAfterDue} days overdue
                      </span>
                    </td>
                    <td>
                      <span className="text-sm text-text-primary">{campaign.steps.length} steps</span>
                    </td>
                    <td>
                      <span
                        className={cn(
                          "status-badge",
                          campaign.status === "active"
                            ? "bg-status-success/15 text-status-success"
                            : campaign.status === "paused"
                            ? "bg-status-warning/15 text-status-warning"
                            : "bg-surface-overlay text-text-muted"
                        )}
                      >
                        {campaign.status.charAt(0).toUpperCase() + campaign.status.slice(1)}
                      </span>
                    </td>
                    <td>
                      <span className="text-sm text-text-muted tabular-nums">
                        {campaign.stats?.totalExecutions || 0}
                      </span>
                    </td>
                    <td>
                      <Link
                        href={`/billing/dunning/campaigns/${campaign.id}`}
                        className="text-sm text-text-muted hover:text-text-secondary opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        Edit →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-12 text-center">
              <Mail className="w-12 h-12 mx-auto text-text-muted mb-4" />
              <h3 className="text-lg font-semibold text-text-primary mb-2">No campaigns yet</h3>
              <p className="text-text-muted mb-6">
                Create your first dunning campaign to automate payment recovery
              </p>
              <Link href="/billing/dunning/campaigns/new">
                <Button className="shadow-glow-sm hover:shadow-glow">
                  <Plus className="w-4 h-4 mr-2" />
                  Create Campaign
                </Button>
              </Link>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      <div className="flex items-center justify-between">
        <div>
          <div className="h-4 w-32 bg-surface-overlay rounded mb-2" />
          <div className="h-8 w-48 bg-surface-overlay rounded" />
        </div>
        <div className="flex gap-3">
          <div className="h-10 w-32 bg-surface-overlay rounded" />
          <div className="h-10 w-32 bg-surface-overlay rounded" />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-surface-overlay rounded-lg" />
              <div>
                <div className="h-4 w-20 bg-surface-overlay rounded mb-2" />
                <div className="h-8 w-24 bg-surface-overlay rounded" />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card p-6">
          <div className="h-6 w-40 bg-surface-overlay rounded mb-4" />
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 bg-surface-overlay rounded" />
            ))}
          </div>
        </div>
        <div className="card p-6">
          <div className="h-6 w-32 bg-surface-overlay rounded mb-4" />
          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-12 bg-surface-overlay rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
