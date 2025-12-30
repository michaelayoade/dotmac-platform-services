import { type ElementType } from "react";
import Link from "next/link";
import {
  Plus,
  Download,
  CheckCircle,
  Clock,
  AlertCircle,
  XCircle,
  CreditCard,
  Search,
  Banknote,
} from "lucide-react";
import { Button } from "@/lib/dotmac/core";

import { listPayments, type Payment } from "@/lib/api/payments";
import { fetchOrNull } from "@/lib/api/fetch-or-null";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Payments",
  description: "View and record payments",
};

interface PageProps {
  searchParams: {
    page?: string;
    status?: string;
    method?: string;
    search?: string;
  };
}

export default async function PaymentsPage({ searchParams }: PageProps) {
  const page = Number(searchParams.page) || 1;
  const status = searchParams.status as Payment["status"] | undefined;
  const method = searchParams.method as Payment["method"] | undefined;

  const response = await fetchOrNull(() => listPayments({ page, pageSize: 20, status, method }));
  const payments = response?.payments ?? [];
  const totalCount = response?.total ?? null;
  const pageCount = response?.pageCount ?? 1;

  const stats = response
    ? {
        total: totalCount,
        completed: payments.filter((p) => p.status === "completed").length,
        pending: payments.filter((p) => p.status === "pending").length,
        failed: payments.filter((p) => p.status === "failed").length,
      }
    : {
        total: null,
        completed: null,
        pending: null,
        failed: null,
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
          <span className="text-text-primary">Payments</span>
        </div>

        <div className="page-header">
          <div>
            <h1 className="page-title">Payments</h1>
            <p className="page-description">
              View payment history and record offline payments
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
            <Link href="/billing/payments/record">
              <Button className="shadow-glow-sm hover:shadow-glow">
                <Plus className="w-4 h-4 mr-2" />
                Record Payment
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="quick-stats">
        <div className="quick-stat">
          <p className="metric-label">Total Payments</p>
          <p className="metric-value text-2xl">{stats.total ?? "—"}</p>
        </div>
        <div className="quick-stat">
          <p className="metric-label">Completed</p>
          <p className="metric-value text-2xl text-status-success">{stats.completed ?? "—"}</p>
        </div>
        <div className="quick-stat">
          <p className="metric-label">Pending</p>
          <p className="metric-value text-2xl text-status-warning">{stats.pending ?? "—"}</p>
        </div>
        <div className="quick-stat">
          <p className="metric-label">Failed</p>
          <p className="metric-value text-2xl text-status-error">{stats.failed ?? "—"}</p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
            <input
              type="text"
              placeholder="Search payments..."
              className="w-full pl-10 pr-4 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
            />
          </div>
          <div className="flex items-center gap-2">
            <StatusFilterButton status={undefined} label="All" currentStatus={status} />
            <StatusFilterButton status="completed" label="Completed" currentStatus={status} />
            <StatusFilterButton status="pending" label="Pending" currentStatus={status} />
            <StatusFilterButton status="failed" label="Failed" currentStatus={status} />
          </div>
        </div>
      </div>

      {/* Payments Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <PaymentsTable payments={payments} />
        </div>

        {/* Pagination */}
        {pageCount > 1 && (
          <div className="flex items-center justify-between p-4 border-t border-border">
            <p className="text-sm text-text-muted">
              Showing {payments.length} of {totalCount} payments
            </p>
            <div className="flex items-center gap-2">
              {page > 1 && (
                <Link href={`/billing/payments?page=${page - 1}${status ? `&status=${status}` : ""}`}>
                  <Button variant="outline" size="sm">
                    Previous
                  </Button>
                </Link>
              )}
              <span className="text-sm text-text-secondary">
                Page {page} of {pageCount}
              </span>
              {page < pageCount && (
                <Link href={`/billing/payments?page=${page + 1}${status ? `&status=${status}` : ""}`}>
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
  status: Payment["status"] | undefined;
  label: string;
  currentStatus: Payment["status"] | undefined;
}) {
  const isActive = status === currentStatus;
  const href = status ? `/billing/payments?status=${status}` : "/billing/payments";

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

function PaymentsTable({ payments }: { payments: Payment[] }) {
  const statusConfig: Record<
    Payment["status"],
    { icon: ElementType; class: string; label: string }
  > = {
    completed: { icon: CheckCircle, class: "status-badge--success", label: "Completed" },
    pending: { icon: Clock, class: "status-badge--warning", label: "Pending" },
    failed: { icon: AlertCircle, class: "status-badge--error", label: "Failed" },
    refunded: { icon: XCircle, class: "bg-surface-overlay text-text-muted", label: "Refunded" },
  };

  const methodLabels: Record<Payment["method"], string> = {
    cash: "Cash",
    check: "Check",
    bank_transfer: "Bank Transfer",
    wire_transfer: "Wire Transfer",
    card: "Card",
    other: "Other",
  };

  if (payments.length === 0) {
    return (
      <div className="p-12 text-center">
        <CreditCard className="w-12 h-12 mx-auto text-text-muted mb-4" />
        <h3 className="text-lg font-semibold text-text-primary mb-2">No payments found</h3>
        <p className="text-text-muted mb-6">
          Record your first offline payment to get started
        </p>
        <Link href="/billing/payments/record">
          <Button className="shadow-glow-sm hover:shadow-glow">
            <Plus className="w-4 h-4 mr-2" />
            Record Payment
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <table className="data-table" aria-label="Payments list"><caption className="sr-only">Payments list</caption>
      <thead>
        <tr>
          <th>Date</th>
          <th>Customer</th>
          <th>Amount</th>
          <th>Method</th>
          <th>Status</th>
          <th>Reference</th>
          <th>Invoice</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {payments.map((payment) => {
          const config = statusConfig[payment.status];
          const Icon = config.icon;
          const paymentDate = new Date(payment.paymentDate);

          return (
            <tr key={payment.id} className="group">
              <td>
                <span className="text-sm text-text-secondary tabular-nums">
                  {paymentDate.toLocaleDateString()}
                </span>
              </td>
              <td>
                <div>
                  <p className="text-sm font-medium text-text-primary">
                    {payment.customerName || "Unknown"}
                  </p>
                </div>
              </td>
              <td>
                <span className="text-sm font-semibold tabular-nums">
                  ${(payment.amount / 100).toLocaleString()}
                </span>
                <span className="text-xs text-text-muted ml-1">{payment.currency}</span>
              </td>
              <td>
                <span className="inline-flex items-center gap-1.5 text-sm text-text-secondary">
                  <Banknote className="w-3 h-3" />
                  {methodLabels[payment.method]}
                </span>
              </td>
              <td>
                <span className={cn("status-badge", config.class)}>
                  <Icon className="w-3 h-3" />
                  {config.label}
                </span>
              </td>
              <td>
                <span className="text-sm font-mono text-text-muted">
                  {payment.referenceNumber || "—"}
                </span>
              </td>
              <td>
                {payment.invoiceNumber ? (
                  <Link
                    href={`/billing/invoices/${payment.invoiceId}`}
                    className="text-sm text-accent hover:text-accent-hover font-mono"
                  >
                    {payment.invoiceNumber}
                  </Link>
                ) : (
                  <span className="text-sm text-text-muted">—</span>
                )}
              </td>
              <td>
                <Link
                  href={`/billing/payments/${payment.id}`}
                  className="text-sm text-text-muted hover:text-text-secondary opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  View
                </Link>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
