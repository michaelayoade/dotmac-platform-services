import { type ElementType } from "react";
import Link from "next/link";
import {
  Plus,
  Download,
  CheckCircle,
  Clock,
  AlertCircle,
  XCircle,
  Receipt,
} from "lucide-react";
import { Button } from "@/lib/dotmac/core";

import { getInvoices, type Invoice } from "@/lib/api/billing";
import { fetchOrNull } from "@/lib/api/fetch-or-null";
import { cn } from "@/lib/utils";
import { InvoiceFilters } from "./invoice-filters";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Invoices",
  description: "Manage tenant invoices",
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
  const search = searchParams.search;

  const response = await fetchOrNull(() => getInvoices({ page, pageSize: 20, status, search }));
  const invoices = response?.invoices ?? [];
  const totalCount = response?.totalCount ?? null;
  const pageCount = response?.pageCount ?? 1;

  const stats = response
    ? {
        total: totalCount,
        paid: invoices.filter((i) => i.status === "paid").length,
        pending: invoices.filter((i) => i.status === "pending").length,
        overdue: invoices.filter((i) => i.status === "overdue").length,
      }
    : {
        total: null,
        paid: null,
        pending: null,
        overdue: null,
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
              Create and manage tenant invoices
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
          <p className="metric-value text-2xl">{stats.total ?? "—"}</p>
        </div>
        <div className="quick-stat">
          <p className="metric-label">Paid</p>
          <p className="metric-value text-2xl text-status-success">{stats.paid ?? "—"}</p>
        </div>
        <div className="quick-stat">
          <p className="metric-label">Pending</p>
          <p className="metric-value text-2xl text-status-warning">{stats.pending ?? "—"}</p>
        </div>
        <div className="quick-stat">
          <p className="metric-label">Overdue</p>
          <p className="metric-value text-2xl text-status-error">{stats.overdue ?? "—"}</p>
        </div>
      </div>

      {/* Filter Bar */}
      <InvoiceFilters currentStatus={status} />

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
                <Link href={`/billing/invoices?page=${page - 1}${status ? `&status=${status}` : ""}${search ? `&search=${encodeURIComponent(search)}` : ""}`}>
                  <Button variant="outline" size="sm">
                    Previous
                  </Button>
                </Link>
              )}
              <span className="text-sm text-text-secondary">
                Page {page} of {pageCount}
              </span>
              {page < pageCount && (
                <Link href={`/billing/invoices?page=${page + 1}${status ? `&status=${status}` : ""}${search ? `&search=${encodeURIComponent(search)}` : ""}`}>
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
    <table className="data-table" aria-label="Invoices list"><caption className="sr-only">Invoices list</caption>
      <thead>
        <tr>
          <th>Invoice</th>
          <th>Tenant</th>
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
