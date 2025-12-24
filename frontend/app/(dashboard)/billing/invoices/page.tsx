import { Suspense, type ElementType } from "react";
import Link from "next/link";
import {
  Plus,
  Download,
  ArrowLeft,
  CheckCircle,
  Clock,
  AlertCircle,
  XCircle,
  Receipt,
  Filter,
  Search,
} from "lucide-react";
import { Button } from "@/lib/dotmac/core";

import { getInvoices, type Invoice } from "@/lib/api/billing";
import { safeApi } from "@/lib/api/safe-api";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Invoices",
  description: "Manage customer invoices",
};

interface PageProps {
  searchParams: {
    page?: string;
    status?: string;
    search?: string;
  };
}

export default async function InvoicesPage({ searchParams }: PageProps) {
  const page = Number(searchParams.page) || 1;
  const status = searchParams.status as Invoice["status"] | undefined;

  const { invoices, totalCount, pageCount } = await safeApi(
    () => getInvoices({ page, pageSize: 20, status }),
    { invoices: [], totalCount: 0, pageCount: 1 }
  );

  const stats = {
    total: totalCount,
    paid: invoices.filter((i) => i.status === "paid").length,
    pending: invoices.filter((i) => i.status === "pending").length,
    overdue: invoices.filter((i) => i.status === "overdue").length,
    totalAmount: invoices.reduce((sum, i) => sum + i.amount, 0),
  };

  return (
    <div className="space-y-6">
      {/* Page Header with Breadcrumbs */}
      <div>
        <div className="flex items-center gap-2 text-sm text-text-muted mb-4">
          <Link href="/billing" className="hover:text-text-secondary">
            Billing
          </Link>
          <span>/</span>
          <span className="text-text-primary">Invoices</span>
        </div>

        <div className="page-header">
          <div>
            <h1 className="page-title">Invoices</h1>
            <p className="page-description">
              Create and manage customer invoices
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
            <Link href="/billing/invoices/new">
              <Button className="shadow-glow-sm hover:shadow-glow">
                <Plus className="w-4 h-4 mr-2" />
                Create Invoice
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="quick-stats">
        <div className="quick-stat">
          <p className="metric-label">Total Invoices</p>
          <p className="metric-value text-2xl">{stats.total}</p>
        </div>
        <div className="quick-stat">
          <p className="metric-label">Paid</p>
          <p className="metric-value text-2xl text-status-success">{stats.paid}</p>
        </div>
        <div className="quick-stat">
          <p className="metric-label">Pending</p>
          <p className="metric-value text-2xl text-status-warning">{stats.pending}</p>
        </div>
        <div className="quick-stat">
          <p className="metric-label">Overdue</p>
          <p className="metric-value text-2xl text-status-error">{stats.overdue}</p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
            <input
              type="text"
              placeholder="Search invoices..."
              className="w-full pl-10 pr-4 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
            />
          </div>
          <div className="flex items-center gap-2">
            <StatusFilterButton status={undefined} label="All" currentStatus={status} />
            <StatusFilterButton status="pending" label="Pending" currentStatus={status} />
            <StatusFilterButton status="paid" label="Paid" currentStatus={status} />
            <StatusFilterButton status="overdue" label="Overdue" currentStatus={status} />
          </div>
        </div>
      </div>

      {/* Invoices Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <InvoicesTable invoices={invoices} />
        </div>

        {/* Pagination */}
        {pageCount > 1 && (
          <div className="flex items-center justify-between p-4 border-t border-border">
            <p className="text-sm text-text-muted">
              Showing {invoices.length} of {totalCount} invoices
            </p>
            <div className="flex items-center gap-2">
              {page > 1 && (
                <Link href={`/billing/invoices?page=${page - 1}${status ? `&status=${status}` : ""}`}>
                  <Button variant="outline" size="sm">
                    Previous
                  </Button>
                </Link>
              )}
              <span className="text-sm text-text-secondary">
                Page {page} of {pageCount}
              </span>
              {page < pageCount && (
                <Link href={`/billing/invoices?page=${page + 1}${status ? `&status=${status}` : ""}`}>
                  <Button variant="outline" size="sm">
                    Next
                  </Button>
                </Link>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function StatusFilterButton({
  status,
  label,
  currentStatus,
}: {
  status: Invoice["status"] | undefined;
  label: string;
  currentStatus: Invoice["status"] | undefined;
}) {
  const isActive = status === currentStatus;
  const href = status ? `/billing/invoices?status=${status}` : "/billing/invoices";

  return (
    <Link href={href}>
      <Button
        variant={isActive ? "default" : "outline"}
        size="sm"
        className={cn(
          isActive && "shadow-glow-sm"
        )}
      >
        {label}
      </Button>
    </Link>
  );
}

function InvoicesTable({ invoices }: { invoices: Invoice[] }) {
  const statusConfig: Record<
    Invoice["status"],
    { icon: ElementType; class: string; label: string }
  > = {
    paid: { icon: CheckCircle, class: "status-badge--success", label: "Paid" },
    pending: { icon: Clock, class: "status-badge--warning", label: "Pending" },
    overdue: { icon: AlertCircle, class: "status-badge--error", label: "Overdue" },
    draft: { icon: Receipt, class: "bg-surface-overlay text-text-muted", label: "Draft" },
    cancelled: { icon: XCircle, class: "bg-surface-overlay text-text-muted", label: "Cancelled" },
  };

  if (invoices.length === 0) {
    return (
      <div className="p-12 text-center">
        <Receipt className="w-12 h-12 mx-auto text-text-muted mb-4" />
        <h3 className="text-lg font-semibold text-text-primary mb-2">No invoices found</h3>
        <p className="text-text-muted mb-6">
          Create your first invoice to get started
        </p>
        <Link href="/billing/invoices/new">
          <Button className="shadow-glow-sm hover:shadow-glow">
            <Plus className="w-4 h-4 mr-2" />
            Create Invoice
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Invoice</th>
          <th>Customer</th>
          <th>Amount</th>
          <th>Status</th>
          <th>Due Date</th>
          <th>Created</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {invoices.map((invoice) => {
          const config = statusConfig[invoice.status];
          const Icon = config.icon;
          const isOverdue = invoice.status === "overdue";
          const dueDate = new Date(invoice.dueDate);
          const createdDate = new Date(invoice.createdAt);

          return (
            <tr key={invoice.id} className="group">
              <td>
                <Link
                  href={`/billing/invoices/${invoice.id}`}
                  className="font-mono text-sm text-accent hover:text-accent-hover"
                >
                  {invoice.number}
                </Link>
              </td>
              <td>
                <div>
                  <p className="text-sm font-medium text-text-primary">
                    {invoice.customer.name}
                  </p>
                  <p className="text-xs text-text-muted">{invoice.customer.email}</p>
                </div>
              </td>
              <td>
                <span className="text-sm font-semibold tabular-nums">
                  ${(invoice.amount / 100).toLocaleString()}
                </span>
                <span className="text-xs text-text-muted ml-1">{invoice.currency}</span>
              </td>
              <td>
                <span className={cn("status-badge", config.class)}>
                  <Icon className="w-3 h-3" />
                  {config.label}
                </span>
              </td>
              <td>
                <span
                  className={cn(
                    "text-sm tabular-nums",
                    isOverdue ? "text-status-error font-medium" : "text-text-secondary"
                  )}
                >
                  {dueDate.toLocaleDateString()}
                </span>
              </td>
              <td>
                <span className="text-sm text-text-muted tabular-nums">
                  {createdDate.toLocaleDateString()}
                </span>
              </td>
              <td>
                <Link
                  href={`/billing/invoices/${invoice.id}`}
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
  );
}
