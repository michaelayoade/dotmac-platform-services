"use client";

import Link from "next/link";
import {
  DollarSign,
  TrendingUp,
  Clock,
  Users,
  FileText,
  ArrowRight,
  Download,
  CheckCircle,
  AlertCircle,
  Building2,
} from "lucide-react";
import { format } from "date-fns";
import { Button, Card } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { usePartnerBillingSummary } from "@/lib/hooks/api/use-partner-portal";

const statusConfig = {
  paid: { icon: CheckCircle, class: "text-status-success", label: "Paid" },
  pending: { icon: Clock, class: "text-status-warning", label: "Pending" },
  overdue: { icon: AlertCircle, class: "text-status-error", label: "Overdue" },
  draft: { icon: FileText, class: "text-text-muted", label: "Draft" },
  cancelled: { icon: FileText, class: "text-text-muted", label: "Cancelled" },
};

export default function PartnerBillingDashboardPage() {
  const { data: summary, isLoading } = usePartnerBillingSummary();

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="space-y-8 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="Partner Billing"
        breadcrumbs={[
          { label: "Partners", href: "/partners" },
          { label: "Billing" },
        ]}
        actions={
          <div className="flex items-center gap-3">
            <Link href="/partners/billing/export">
              <Button variant="outline">
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </Link>
            <Link href="/partners/billing/invoices">
              <Button className="shadow-glow-sm hover:shadow-glow">
                <FileText className="w-4 h-4 mr-2" />
                View All Invoices
              </Button>
            </Link>
          </div>
        }
      />

      {/* KPI Tiles */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-status-success/15 flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-status-success" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Total Revenue</p>
              <p className="text-2xl font-bold text-text-primary">
                ${((summary?.totalRevenue || 0) / 100).toLocaleString()}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-status-warning/15 flex items-center justify-center">
              <Clock className="w-6 h-6 text-status-warning" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Outstanding</p>
              <p className="text-2xl font-bold text-status-warning">
                ${((summary?.totalOutstanding || 0) / 100).toLocaleString()}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-accent-subtle flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-accent" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Paid This Month</p>
              <p className="text-2xl font-bold text-text-primary">
                ${((summary?.totalPaidThisMonth || 0) / 100).toLocaleString()}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-highlight-subtle flex items-center justify-center">
              <Users className="w-6 h-6 text-highlight" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Active Tenants</p>
              <p className="text-2xl font-bold text-text-primary">
                {summary?.activeTenants || 0}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Revenue by Tenant */}
        <Card className="lg:col-span-2 overflow-hidden">
          <div className="p-6 border-b border-border">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-text-primary">Revenue by Tenant</h3>
              <Link
                href="/partners/billing/invoices"
                className="text-sm text-accent hover:text-accent-hover inline-flex items-center gap-1"
              >
                View all
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
          <div className="overflow-x-auto">
            {summary?.revenueByTenant && summary.revenueByTenant.length > 0 ? (
              <table className="data-table" aria-label="Revenue by tenant"><caption className="sr-only">Revenue by tenant</caption>
                <thead>
                  <tr>
                    <th>Tenant</th>
                    <th className="text-right">Revenue</th>
                    <th className="text-right">Outstanding</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.revenueByTenant.map((tenant) => (
                    <tr key={tenant.tenantId}>
                      <td>
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-accent-subtle flex items-center justify-center">
                            <Building2 className="w-4 h-4 text-accent" />
                          </div>
                          <span className="font-medium text-text-primary">
                            {tenant.tenantName}
                          </span>
                        </div>
                      </td>
                      <td className="text-right">
                        <span className="font-semibold text-text-primary tabular-nums">
                          ${(tenant.revenue / 100).toLocaleString()}
                        </span>
                      </td>
                      <td className="text-right">
                        <span
                          className={cn(
                            "font-medium tabular-nums",
                            tenant.outstanding > 0 ? "text-status-warning" : "text-text-muted"
                          )}
                        >
                          ${(tenant.outstanding / 100).toLocaleString()}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-8 text-center">
                <Building2 className="w-12 h-12 mx-auto text-text-muted mb-4" />
                <p className="text-text-muted">No tenant billing data available</p>
              </div>
            )}
          </div>
        </Card>

        {/* Payment Status Breakdown */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-text-primary mb-6">Payment Status</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-status-success/15 rounded-lg">
              <div className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-status-success" />
                <span className="font-medium text-text-primary">Paid</span>
              </div>
              <span className="text-lg font-bold text-status-success">
                {summary?.paymentStatusBreakdown?.paid || 0}
              </span>
            </div>

            <div className="flex items-center justify-between p-4 bg-status-warning/15 rounded-lg">
              <div className="flex items-center gap-3">
                <Clock className="w-5 h-5 text-status-warning" />
                <span className="font-medium text-text-primary">Pending</span>
              </div>
              <span className="text-lg font-bold text-status-warning">
                {summary?.paymentStatusBreakdown?.pending || 0}
              </span>
            </div>

            <div className="flex items-center justify-between p-4 bg-status-error/15 rounded-lg">
              <div className="flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-status-error" />
                <span className="font-medium text-text-primary">Overdue</span>
              </div>
              <span className="text-lg font-bold text-status-error">
                {summary?.paymentStatusBreakdown?.overdue || 0}
              </span>
            </div>
          </div>
        </Card>
      </div>

      {/* Recent Invoices */}
      <Card className="overflow-hidden">
        <div className="p-6 border-b border-border">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-text-primary">Recent Invoices</h3>
            <Link
              href="/partners/billing/invoices"
              className="text-sm text-accent hover:text-accent-hover inline-flex items-center gap-1"
            >
              View all
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
        <div className="overflow-x-auto">
          {summary?.recentInvoices && summary.recentInvoices.length > 0 ? (
            <table className="data-table" aria-label="Recent partner invoices"><caption className="sr-only">Recent partner invoices</caption>
              <thead>
                <tr>
                  <th>Invoice</th>
                  <th>Tenant</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Due Date</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {summary.recentInvoices.map((invoice) => {
                  const status = statusConfig[invoice.status as keyof typeof statusConfig] || statusConfig.draft;
                  const StatusIcon = status.icon;
                  return (
                    <tr key={invoice.id} className="group">
                      <td>
                        <Link
                          href={`/partners/billing/invoices/${invoice.id}`}
                          className="font-mono text-sm text-accent hover:text-accent-hover"
                        >
                          {invoice.number}
                        </Link>
                      </td>
                      <td>
                        <span className="text-text-primary">{invoice.tenantName}</span>
                      </td>
                      <td>
                        <span className="font-semibold tabular-nums">
                          ${(invoice.amount / 100).toLocaleString()}
                        </span>
                      </td>
                      <td>
                        <span className={cn("inline-flex items-center gap-1.5 text-sm font-medium", status.class)}>
                          <StatusIcon className="w-4 h-4" />
                          {status.label}
                        </span>
                      </td>
                      <td>
                        <span className="text-sm text-text-muted tabular-nums">
                          {format(new Date(invoice.dueDate), "MMM d, yyyy")}
                        </span>
                      </td>
                      <td>
                        <Link
                          href={`/partners/billing/invoices/${invoice.id}`}
                          className="text-sm text-text-muted hover:text-text-secondary opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          View →
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <div className="p-8 text-center">
              <FileText className="w-12 h-12 mx-auto text-text-muted mb-4" />
              <p className="text-text-muted">No recent invoices</p>
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
          <div className="h-10 w-24 bg-surface-overlay rounded" />
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
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-12 bg-surface-overlay rounded" />
            ))}
          </div>
        </div>
        <div className="card p-6">
          <div className="h-6 w-32 bg-surface-overlay rounded mb-4" />
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-surface-overlay rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
