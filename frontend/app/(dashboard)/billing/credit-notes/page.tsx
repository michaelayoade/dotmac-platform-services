import { type ElementType } from "react";
import Link from "next/link";
import {
  Plus,
  Download,
  CheckCircle,
  Clock,
  Ban,
  Receipt,
  Search,
  FileText,
} from "lucide-react";
import { Button } from "@/lib/dotmac/core";

import { getCreditNotes, type CreditNote, type CreditNoteStatus } from "@/lib/api/billing";
import { fetchOrNull } from "@/lib/api/fetch-or-null";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Credit Notes",
  description: "Manage credit notes and refunds",
};

interface PageProps {
  searchParams: Promise<{
    page?: string;
    status?: string;
    search?: string;
  }>;
}

export default async function CreditNotesPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const page = Number(params.page) || 1;
  const status = params.status as CreditNoteStatus | undefined;

  const response = await fetchOrNull(() => getCreditNotes({ page, pageSize: 20, status }));
  const creditNotes = response?.creditNotes ?? [];
  const totalCount = response?.totalCount ?? null;
  const pageCount = response?.pageCount ?? 1;

  const stats = response
    ? {
        total: totalCount,
        draft: creditNotes.filter((c) => c.status === "draft").length,
        issued: creditNotes.filter((c) => c.status === "issued").length,
        applied: creditNotes.filter((c) => c.status === "applied").length,
      }
    : {
        total: null,
        draft: null,
        issued: null,
        applied: null,
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
          <span className="text-text-primary">Credit Notes</span>
        </div>

        <div className="page-header">
          <div>
            <h1 className="page-title">Credit Notes</h1>
            <p className="page-description">
              Create and manage credit notes for refunds and adjustments
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
            <Link href="/billing/credit-notes/new">
              <Button className="shadow-glow-sm hover:shadow-glow">
                <Plus className="w-4 h-4 mr-2" />
                Create Credit Note
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="quick-stats">
        <div className="quick-stat">
          <p className="metric-label">Total Credit Notes</p>
          <p className="metric-value text-2xl">{stats.total ?? "—"}</p>
        </div>
        <div className="quick-stat">
          <p className="metric-label">Draft</p>
          <p className="metric-value text-2xl text-text-muted">{stats.draft ?? "—"}</p>
        </div>
        <div className="quick-stat">
          <p className="metric-label">Issued</p>
          <p className="metric-value text-2xl text-status-info">{stats.issued ?? "—"}</p>
        </div>
        <div className="quick-stat">
          <p className="metric-label">Applied</p>
          <p className="metric-value text-2xl text-status-success">{stats.applied ?? "—"}</p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
            <input
              type="text"
              placeholder="Search credit notes..."
              className="w-full pl-10 pr-4 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
            />
          </div>
          <div className="flex items-center gap-2">
            <StatusFilterButton status={undefined} label="All" currentStatus={status} />
            <StatusFilterButton status="draft" label="Draft" currentStatus={status} />
            <StatusFilterButton status="issued" label="Issued" currentStatus={status} />
            <StatusFilterButton status="applied" label="Applied" currentStatus={status} />
            <StatusFilterButton status="voided" label="Voided" currentStatus={status} />
          </div>
        </div>
      </div>

      {/* Credit Notes Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <CreditNotesTable creditNotes={creditNotes} />
        </div>

        {/* Pagination */}
        {pageCount > 1 && (
          <div className="flex items-center justify-between p-4 border-t border-border">
            <p className="text-sm text-text-muted">
              Showing {creditNotes.length} of {totalCount} credit notes
            </p>
            <div className="flex items-center gap-2">
              {page > 1 && (
                <Link href={`/billing/credit-notes?page=${page - 1}${status ? `&status=${status}` : ""}`}>
                  <Button variant="outline" size="sm">
                    Previous
                  </Button>
                </Link>
              )}
              <span className="text-sm text-text-secondary">
                Page {page} of {pageCount}
              </span>
              {page < pageCount && (
                <Link href={`/billing/credit-notes?page=${page + 1}${status ? `&status=${status}` : ""}`}>
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
  status: CreditNoteStatus | undefined;
  label: string;
  currentStatus: CreditNoteStatus | undefined;
}) {
  const isActive = status === currentStatus;
  const href = status ? `/billing/credit-notes?status=${status}` : "/billing/credit-notes";

  return (
    <Link href={href}>
      <Button
        variant={isActive ? "default" : "outline"}
        size="sm"
        className={cn(isActive && "shadow-glow-sm")}
      >
        {label}
      </Button>
    </Link>
  );
}

function CreditNotesTable({ creditNotes }: { creditNotes: CreditNote[] }) {
  const statusConfig: Record<
    CreditNoteStatus,
    { icon: ElementType; class: string; label: string }
  > = {
    draft: { icon: FileText, class: "bg-surface-overlay text-text-muted", label: "Draft" },
    issued: { icon: Receipt, class: "status-badge--info", label: "Issued" },
    applied: { icon: CheckCircle, class: "status-badge--success", label: "Applied" },
    voided: { icon: Ban, class: "bg-surface-overlay text-text-muted", label: "Voided" },
  };

  if (creditNotes.length === 0) {
    return (
      <div className="p-12 text-center">
        <Receipt className="w-12 h-12 mx-auto text-text-muted mb-4" />
        <h3 className="text-lg font-semibold text-text-primary mb-2">No credit notes found</h3>
        <p className="text-text-muted mb-6">
          Create your first credit note to issue refunds or adjustments
        </p>
        <Link href="/billing/credit-notes/new">
          <Button className="shadow-glow-sm hover:shadow-glow">
            <Plus className="w-4 h-4 mr-2" />
            Create Credit Note
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <table className="data-table" aria-label="Credit notes list"><caption className="sr-only">Credit notes list</caption>
      <thead>
        <tr>
          <th>Credit Note</th>
          <th>Customer</th>
          <th>Amount</th>
          <th>Remaining</th>
          <th>Status</th>
          <th>Related Invoice</th>
          <th>Created</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {creditNotes.map((creditNote) => {
          const config = statusConfig[creditNote.status];
          const Icon = config.icon;
          const createdDate = new Date(creditNote.createdAt);

          return (
            <tr key={creditNote.id} className="group">
              <td>
                <Link
                  href={`/billing/credit-notes/${creditNote.id}`}
                  className="font-mono text-sm text-accent hover:text-accent-hover"
                >
                  {creditNote.number}
                </Link>
              </td>
              <td>
                <div>
                  <p className="text-sm font-medium text-text-primary">
                    {creditNote.customerName}
                  </p>
                </div>
              </td>
              <td>
                <span className="text-sm font-semibold tabular-nums">
                  ${(creditNote.amount / 100).toLocaleString()}
                </span>
                <span className="text-xs text-text-muted ml-1">{creditNote.currency}</span>
              </td>
              <td>
                <span className={cn(
                  "text-sm tabular-nums",
                  creditNote.remainingAmount > 0 ? "text-status-warning" : "text-text-muted"
                )}>
                  ${(creditNote.remainingAmount / 100).toLocaleString()}
                </span>
              </td>
              <td>
                <span className={cn("status-badge", config.class)}>
                  <Icon className="w-3 h-3" />
                  {config.label}
                </span>
              </td>
              <td>
                {creditNote.invoiceNumber ? (
                  <Link
                    href={`/billing/invoices/${creditNote.invoiceId}`}
                    className="text-sm text-accent hover:text-accent-hover font-mono"
                  >
                    {creditNote.invoiceNumber}
                  </Link>
                ) : (
                  <span className="text-sm text-text-muted">-</span>
                )}
              </td>
              <td>
                <span className="text-sm text-text-muted tabular-nums">
                  {createdDate.toLocaleDateString()}
                </span>
              </td>
              <td>
                <Link
                  href={`/billing/credit-notes/${creditNote.id}`}
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
