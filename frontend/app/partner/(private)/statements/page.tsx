"use client";

import { useState } from "react";
import {
  FileText,
  Download,
  Calendar,
  DollarSign,
  CheckCircle,
  Clock,
} from "lucide-react";

import { PageHeader, StatusBadge, EmptyState } from "@/components/shared";
import {
  usePartnerStatements,
  useDownloadStatement,
} from "@/lib/hooks/api/use-partner-portal";
import { cn } from "@/lib/utils";
import type { Statement } from "@/types/partner-portal";

const statusColors: Record<Statement["status"], "pending" | "info" | "success"> = {
  DRAFT: "pending",
  FINAL: "info",
  PAID: "success",
};

// Demo data
const demoStatements: Statement[] = [
  {
    id: "1",
    period: "December 2024",
    startDate: "2024-12-01T00:00:00Z",
    endDate: "2024-12-31T23:59:59Z",
    totalRevenue: 7300,
    totalCommissions: 1235,
    status: "DRAFT" as const,
    createdAt: "2024-12-01T00:00:00Z",
  },
  {
    id: "2",
    period: "November 2024",
    startDate: "2024-11-01T00:00:00Z",
    endDate: "2024-11-30T23:59:59Z",
    totalRevenue: 10500,
    totalCommissions: 1575,
    status: "FINAL" as const,
    createdAt: "2024-11-01T00:00:00Z",
  },
  {
    id: "3",
    period: "October 2024",
    startDate: "2024-10-01T00:00:00Z",
    endDate: "2024-10-31T23:59:59Z",
    totalRevenue: 9800,
    totalCommissions: 1470,
    status: "PAID" as const,
    paidAt: "2024-11-15T14:00:00Z",
    createdAt: "2024-10-01T00:00:00Z",
  },
  {
    id: "4",
    period: "September 2024",
    startDate: "2024-09-01T00:00:00Z",
    endDate: "2024-09-30T23:59:59Z",
    totalRevenue: 8500,
    totalCommissions: 1275,
    status: "PAID" as const,
    paidAt: "2024-10-15T14:00:00Z",
    createdAt: "2024-09-01T00:00:00Z",
  },
  {
    id: "5",
    period: "August 2024",
    startDate: "2024-08-01T00:00:00Z",
    endDate: "2024-08-31T23:59:59Z",
    totalRevenue: 11200,
    totalCommissions: 1680,
    status: "PAID" as const,
    paidAt: "2024-09-15T14:00:00Z",
    createdAt: "2024-08-01T00:00:00Z",
  },
];

function StatementCard({
  statement,
  onDownload,
  isDownloading,
}: {
  statement: Statement;
  onDownload: (id: string) => void;
  isDownloading: boolean;
}) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <div className="bg-surface-elevated rounded-lg border border-border overflow-hidden hover:border-border-hover transition-colors">
      {/* Header */}
      <div className="p-5 border-b border-border">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h3 className="font-semibold text-text-primary">
                {statement.period}
              </h3>
              <StatusBadge status={statusColors[statement.status]} label={statement.status} />
            </div>
            <p className="text-sm text-text-muted">
              {formatDate(statement.startDate)} - {formatDate(statement.endDate)}
            </p>
          </div>
          {statement.status !== "DRAFT" && (
            <button
              onClick={() => onDownload(statement.id)}
              disabled={isDownloading}
              className="p-2 rounded-md text-text-muted hover:text-accent hover:bg-accent/10 transition-colors disabled:opacity-50"
              title="Download PDF"
            >
              <Download className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 divide-x divide-border">
        <div className="p-4">
          <p className="text-xs text-text-muted uppercase tracking-wider mb-1">
            Total Revenue
          </p>
          <p className="text-lg font-semibold text-text-primary">
            ${statement.totalRevenue.toLocaleString()}
          </p>
        </div>
        <div className="p-4">
          <p className="text-xs text-text-muted uppercase tracking-wider mb-1">
            Commissions
          </p>
          <p className="text-lg font-semibold text-status-success">
            ${statement.totalCommissions.toLocaleString()}
          </p>
        </div>
      </div>

      {/* Footer */}
      {statement.status === "PAID" && statement.paidAt && (
        <div className="px-5 py-3 bg-surface-overlay/50 flex items-center gap-2 text-sm text-status-success">
          <CheckCircle className="w-4 h-4" />
          <span>Paid on {formatDate(statement.paidAt)}</span>
        </div>
      )}
      {statement.status === "FINAL" && (
        <div className="px-5 py-3 bg-surface-overlay/50 flex items-center gap-2 text-sm text-text-muted">
          <Clock className="w-4 h-4" />
          <span>Payment processing</span>
        </div>
      )}
      {statement.status === "DRAFT" && (
        <div className="px-5 py-3 bg-surface-overlay/50 flex items-center gap-2 text-sm text-text-muted">
          <FileText className="w-4 h-4" />
          <span>Period in progress</span>
        </div>
      )}
    </div>
  );
}

function StatementsSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 animate-pulse">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <div
          key={i}
          className="bg-surface-elevated rounded-lg border border-border h-48"
        >
          <div className="p-5 border-b border-border">
            <div className="h-5 w-32 bg-surface-overlay rounded mb-2" />
            <div className="h-4 w-40 bg-surface-overlay rounded" />
          </div>
          <div className="grid grid-cols-2 divide-x divide-border">
            <div className="p-4">
              <div className="h-3 w-20 bg-surface-overlay rounded mb-2" />
              <div className="h-6 w-24 bg-surface-overlay rounded" />
            </div>
            <div className="p-4">
              <div className="h-3 w-20 bg-surface-overlay rounded mb-2" />
              <div className="h-6 w-24 bg-surface-overlay rounded" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function StatementsPage() {
  const [yearFilter, setYearFilter] = useState<number>(new Date().getFullYear());

  const { data, isLoading, error } = usePartnerStatements({
    year: yearFilter,
  });

  const downloadStatement = useDownloadStatement();

  const statements = data?.statements || demoStatements;

  const handleDownload = async (id: string) => {
    try {
      const blob = await downloadStatement.mutateAsync(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `statement-${id}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Failed to download statement:", error);
    }
  };

  // Calculate totals
  const totals = statements.reduce(
    (acc, s) => ({
      revenue: acc.revenue + s.totalRevenue,
      commissions: acc.commissions + s.totalCommissions,
      paid: acc.paid + (s.status === "PAID" ? s.totalCommissions : 0),
    }),
    { revenue: 0, commissions: 0, paid: 0 }
  );

  const years = [2024, 2023, 2022];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Statements"
        description="Monthly commission statements and payout history"
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="bg-surface-elevated rounded-lg border border-border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-accent/10 text-accent">
              <DollarSign className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Total Revenue ({yearFilter})</p>
              <p className="text-xl font-semibold text-text-primary">
                ${totals.revenue.toLocaleString()}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-surface-elevated rounded-lg border border-border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-highlight/10 text-highlight">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Total Commissions</p>
              <p className="text-xl font-semibold text-text-primary">
                ${totals.commissions.toLocaleString()}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-surface-elevated rounded-lg border border-border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-status-success/10 text-status-success">
              <CheckCircle className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Paid Out</p>
              <p className="text-xl font-semibold text-text-primary">
                ${totals.paid.toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Year Filter */}
      <div className="flex gap-2">
        {years.map((year) => (
          <button
            key={year}
            onClick={() => setYearFilter(year)}
            className={cn(
              "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
              yearFilter === year
                ? "bg-accent text-white"
                : "bg-surface-overlay text-text-secondary hover:text-text-primary"
            )}
          >
            {year}
          </button>
        ))}
      </div>

      {/* Statements Grid */}
      {isLoading ? (
        <StatementsSkeleton />
      ) : statements.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No statements found"
          description="Monthly statements will be generated as you earn commissions"
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {statements.map((statement) => (
            <StatementCard
              key={statement.id}
              statement={statement}
              onDownload={handleDownload}
              isDownloading={downloadStatement.isPending}
            />
          ))}
        </div>
      )}
    </div>
  );
}
