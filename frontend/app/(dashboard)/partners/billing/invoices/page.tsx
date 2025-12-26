"use client";

import { useState } from "react";
import Link from "next/link";
import {
  FileText,
  Download,
  Search,
  Filter,
  CheckCircle,
  Clock,
  AlertCircle,
  Ban,
  Building2,
  Calendar,
  ArrowRight,
} from "lucide-react";
import { format } from "date-fns";
import { Button, Card, Input, Select } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  usePartnerInvoices,
  usePartnerBillingSummary,
  useExportPartnerInvoices,
} from "@/lib/hooks/api/use-partner-portal";
import type { PartnerInvoice, GetPartnerInvoicesParams } from "@/lib/api/partner-portal";

const statusConfig = {
  draft: { icon: FileText, class: "bg-surface-overlay text-text-muted", label: "Draft" },
  pending: { icon: Clock, class: "bg-status-warning/15 text-status-warning", label: "Pending" },
  paid: { icon: CheckCircle, class: "bg-status-success/15 text-status-success", label: "Paid" },
  overdue: { icon: AlertCircle, class: "bg-status-error/15 text-status-error", label: "Overdue" },
  cancelled: { icon: Ban, class: "bg-surface-overlay text-text-muted", label: "Cancelled" },
};

export default function PartnerInvoicesPage() {
  const [filters, setFilters] = useState<GetPartnerInvoicesParams>({
    page: 1,
    pageSize: 20,
  });
  const [searchTerm, setSearchTerm] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  const { data: invoicesData, isLoading } = usePartnerInvoices(filters);
  const { data: summary } = usePartnerBillingSummary();
  const exportInvoices = useExportPartnerInvoices();

  const invoices = invoicesData?.items ?? [];
  const totalPages = invoicesData?.totalPages ?? 1;
  const total = invoicesData?.total ?? 0;

  // Get unique tenants from summary for filter dropdown
  const tenants = summary?.revenueByTenant ?? [];

  const handleFilterChange = (key: keyof GetPartnerInvoicesParams, value: string | undefined) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value || undefined,
      page: 1, // Reset to first page on filter change
    }));
  };

  const handleExport = async () => {
    const today = new Date();
    const thirtyDaysAgo = new Date(today);
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

    try {
      await exportInvoices.mutateAsync({
        startDate: thirtyDaysAgo.toISOString().split("T")[0],
        endDate: today.toISOString().split("T")[0],
        format: "csv",
      });
    } catch {
      // Error handled by mutation
    }
  };

  if (isLoading) {
    return <InvoicesPageSkeleton />;
  }

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="Partner Invoices"
        breadcrumbs={[
          { label: "Partners", href: "/partners" },
          { label: "Billing", href: "/partners/billing" },
          { label: "Invoices" },
        ]}
        actions={
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              onClick={handleExport}
              disabled={exportInvoices.isPending}
            >
              <Download className="w-4 h-4 mr-2" />
              {exportInvoices.isPending ? "Exporting..." : "Export"}
            </Button>
            <Link href="/partners/billing/export">
              <Button variant="outline">
                <Calendar className="w-4 h-4 mr-2" />
                Export History
              </Button>
            </Link>
          </div>
        }
      />

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <p className="text-sm text-text-muted">Total Invoices</p>
          <p className="text-2xl font-bold text-text-primary">{total}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted">Outstanding</p>
          <p className="text-2xl font-bold text-status-warning">
            ${((summary?.totalOutstanding || 0) / 100).toLocaleString()}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted">Paid This Month</p>
          <p className="text-2xl font-bold text-status-success">
            ${((summary?.totalPaidThisMonth || 0) / 100).toLocaleString()}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted">Active Tenants</p>
          <p className="text-2xl font-bold text-text-primary">
            {summary?.activeTenants || 0}
          </p>
        </Card>
      </div>

      {/* Filter Bar */}
      <Card className="p-4">
        <div className="flex flex-col gap-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
              <Input
                type="text"
                placeholder="Search invoices..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
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
              <StatusFilterButtons
                currentStatus={filters.status}
                onStatusChange={(status) => handleFilterChange("status", status)}
              />
            </div>
          </div>

          {/* Expanded Filters */}
          {showFilters && (
            <div className="pt-4 border-t border-border grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">
                  Tenant
                </label>
                <Select
                  value={filters.tenantId || ""}
                  onChange={(e) => handleFilterChange("tenantId", e.target.value)}
                >
                  <option value="">All Tenants</option>
                  {tenants.map((tenant) => (
                    <option key={tenant.tenantId} value={tenant.tenantId}>
                      {tenant.tenantName}
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">
                  Start Date
                </label>
                <Input
                  type="date"
                  value={filters.startDate || ""}
                  onChange={(e) => handleFilterChange("startDate", e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">
                  End Date
                </label>
                <Input
                  type="date"
                  value={filters.endDate || ""}
                  onChange={(e) => handleFilterChange("endDate", e.target.value)}
                />
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

      {/* Invoices Table */}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          {invoices.length > 0 ? (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Invoice</th>
                  <th>Tenant</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Due Date</th>
                  <th>Paid At</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((invoice) => (
                  <InvoiceRow key={invoice.id} invoice={invoice} />
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-12 text-center">
              <FileText className="w-12 h-12 mx-auto text-text-muted mb-4" />
              <h3 className="text-lg font-semibold text-text-primary mb-2">
                No invoices found
              </h3>
              <p className="text-text-muted">
                {filters.status || filters.tenantId
                  ? "Try adjusting your filters"
                  : "No invoices have been created yet"}
              </p>
            </div>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between p-4 border-t border-border">
            <p className="text-sm text-text-muted">
              Showing {invoices.length} of {total} invoices
            </p>
            <div className="flex items-center gap-2">
              {filters.page && filters.page > 1 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setFilters((prev) => ({ ...prev, page: (prev.page || 1) - 1 }))
                  }
                >
                  Previous
                </Button>
              )}
              <span className="text-sm text-text-secondary">
                Page {filters.page || 1} of {totalPages}
              </span>
              {(filters.page || 1) < totalPages && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setFilters((prev) => ({ ...prev, page: (prev.page || 1) + 1 }))
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

function StatusFilterButtons({
  currentStatus,
  onStatusChange,
}: {
  currentStatus?: string;
  onStatusChange: (status: string | undefined) => void;
}) {
  const statuses = [
    { value: undefined, label: "All" },
    { value: "pending", label: "Pending" },
    { value: "paid", label: "Paid" },
    { value: "overdue", label: "Overdue" },
  ];

  return (
    <div className="flex items-center gap-1">
      {statuses.map((status) => (
        <Button
          key={status.value ?? "all"}
          variant={currentStatus === status.value ? "default" : "ghost"}
          size="sm"
          onClick={() => onStatusChange(status.value)}
          className={cn(currentStatus === status.value && "shadow-glow-sm")}
        >
          {status.label}
        </Button>
      ))}
    </div>
  );
}

function InvoiceRow({ invoice }: { invoice: PartnerInvoice }) {
  const config = statusConfig[invoice.status] || statusConfig.pending;
  const StatusIcon = config.icon;

  return (
    <tr className="group">
      <td>
        <Link
          href={`/billing/invoices/${invoice.id}`}
          className="font-mono text-sm text-accent hover:text-accent-hover"
        >
          {invoice.number}
        </Link>
      </td>
      <td>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-accent-subtle flex items-center justify-center">
            <Building2 className="w-4 h-4 text-accent" />
          </div>
          <span className="font-medium text-text-primary">{invoice.tenantName}</span>
        </div>
      </td>
      <td>
        <span className="font-semibold tabular-nums">
          ${(invoice.amount / 100).toLocaleString()}
        </span>
        <span className="text-xs text-text-muted ml-1">{invoice.currency}</span>
      </td>
      <td>
        <span className={cn("status-badge", config.class)}>
          <StatusIcon className="w-3 h-3" />
          {config.label}
        </span>
      </td>
      <td>
        <span className="text-sm text-text-muted tabular-nums">
          {format(new Date(invoice.dueDate), "MMM d, yyyy")}
        </span>
      </td>
      <td>
        {invoice.paidAt ? (
          <span className="text-sm text-status-success tabular-nums">
            {format(new Date(invoice.paidAt), "MMM d, yyyy")}
          </span>
        ) : (
          <span className="text-sm text-text-muted">—</span>
        )}
      </td>
      <td>
        <Link
          href={`/billing/invoices/${invoice.id}`}
          className="text-sm text-text-muted hover:text-text-secondary opacity-0 group-hover:opacity-100 transition-opacity inline-flex items-center gap-1"
        >
          View
          <ArrowRight className="w-3 h-3" />
        </Link>
      </td>
    </tr>
  );
}

function InvoicesPageSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
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

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card p-4">
            <div className="h-4 w-20 bg-surface-overlay rounded mb-2" />
            <div className="h-8 w-24 bg-surface-overlay rounded" />
          </div>
        ))}
      </div>

      <div className="card p-4">
        <div className="flex gap-4">
          <div className="flex-1 h-10 bg-surface-overlay rounded" />
          <div className="h-10 w-24 bg-surface-overlay rounded" />
          <div className="h-10 w-32 bg-surface-overlay rounded" />
        </div>
      </div>

      <div className="card overflow-hidden">
        <div className="p-4 space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-12 bg-surface-overlay rounded" />
          ))}
        </div>
      </div>
    </div>
  );
}
