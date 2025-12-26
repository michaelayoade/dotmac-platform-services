"use client";

import { useState } from "react";
import {
  Search,
  Calendar,
  DollarSign,
  TrendingUp,
  Clock,
  CheckCircle,
  Filter,
} from "lucide-react";

import { PageHeader, StatusBadge, EmptyState } from "@/components/shared";
import { usePartnerCommissions } from "@/lib/hooks/api/use-partner-portal";
import { cn } from "@/lib/utils";
import type { Commission, CommissionStatus } from "@/types/partner-portal";

const statusColors: Record<CommissionStatus, "pending" | "info" | "success" | "error"> = {
  PENDING: "pending",
  APPROVED: "info",
  PAID: "success",
  CANCELLED: "error",
};

const statusLabels: Record<CommissionStatus, string> = {
  PENDING: "Pending",
  APPROVED: "Approved",
  PAID: "Paid",
  CANCELLED: "Cancelled",
};


function CommissionRow({ commission }: { commission: Commission }) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  };

  return (
    <tr className="border-b border-border hover:bg-surface-overlay/50 transition-colors">
      <td className="px-4 py-4">
        <div>
          <p className="font-medium text-text-primary">
            {commission.tenantName}
          </p>
          <p className="text-sm text-text-muted">{commission.period}</p>
        </div>
      </td>
      <td className="px-4 py-4 text-right">
        <span className="text-text-secondary">
          ${commission.baseAmount.toLocaleString()}
        </span>
      </td>
      <td className="px-4 py-4 text-center">
        <span className="text-text-secondary">{commission.commissionRate}%</span>
      </td>
      <td className="px-4 py-4 text-right">
        <span className="font-medium text-text-primary">
          ${commission.commissionAmount.toLocaleString()}
        </span>
      </td>
      <td className="px-4 py-4">
        <StatusBadge
          status={statusColors[commission.status]}
          label={statusLabels[commission.status]}
        />
      </td>
      <td className="px-4 py-4 text-right">
        <span className="text-sm text-text-muted">
          {commission.paidAt
            ? `Paid ${formatDate(commission.paidAt)}`
            : commission.approvedAt
              ? `Approved ${formatDate(commission.approvedAt)}`
              : "Awaiting approval"}
        </span>
      </td>
    </tr>
  );
}

function CommissionsSkeleton() {
  return (
    <div className="bg-surface-elevated rounded-lg border border-border overflow-hidden">
      <div className="overflow-x-auto">
        <table className="data-table">
          <thead>
            <tr className="border-b border-border bg-surface-overlay/50">
              <th className="px-4 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wider">
                Tenant
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-text-muted uppercase tracking-wider">
                Base Amount
              </th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-text-muted uppercase tracking-wider">
                Rate
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-text-muted uppercase tracking-wider">
                Commission
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wider">
                Status
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-text-muted uppercase tracking-wider">
                Date
              </th>
            </tr>
          </thead>
          <tbody className="animate-pulse">
            {[1, 2, 3, 4, 5].map((i) => (
              <tr key={i} className="border-b border-border">
                <td className="px-4 py-4">
                  <div className="h-4 w-32 bg-surface-overlay rounded" />
                </td>
                <td className="px-4 py-4">
                  <div className="h-4 w-16 bg-surface-overlay rounded ml-auto" />
                </td>
                <td className="px-4 py-4">
                  <div className="h-4 w-8 bg-surface-overlay rounded mx-auto" />
                </td>
                <td className="px-4 py-4">
                  <div className="h-4 w-16 bg-surface-overlay rounded ml-auto" />
                </td>
                <td className="px-4 py-4">
                  <div className="h-5 w-20 bg-surface-overlay rounded-full" />
                </td>
                <td className="px-4 py-4">
                  <div className="h-4 w-24 bg-surface-overlay rounded ml-auto" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function CommissionsPage() {
  const [statusFilter, setStatusFilter] = useState<CommissionStatus | "ALL">("ALL");

  const { data, isLoading, error } = usePartnerCommissions({
    status: statusFilter !== "ALL" ? statusFilter : undefined,
  });

  const commissions = data?.commissions ?? [];
  const summary = data?.summary ?? null;

  const filteredCommissions =
    statusFilter === "ALL"
      ? commissions
      : commissions.filter((c) => c.status === statusFilter);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Commissions"
        description="Track your commission history and earnings"
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="bg-surface-elevated rounded-lg border border-border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-status-warning/15 text-status-warning">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Pending</p>
              <p className="text-xl font-semibold text-text-primary">
                {summary ? `$${summary.totalPending.toLocaleString()}` : "—"}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-surface-elevated rounded-lg border border-border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-status-info/15 text-status-info">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Approved</p>
              <p className="text-xl font-semibold text-text-primary">
                {summary ? `$${summary.totalApproved.toLocaleString()}` : "—"}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-surface-elevated rounded-lg border border-border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-status-success/15 text-status-success">
              <CheckCircle className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Paid to Date</p>
              <p className="text-xl font-semibold text-text-primary">
                {summary ? `$${summary.totalPaid.toLocaleString()}` : "—"}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => setStatusFilter("ALL")}
          className={cn(
            "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
            statusFilter === "ALL"
              ? "bg-accent text-text-inverse"
              : "bg-surface-overlay text-text-secondary hover:text-text-primary"
          )}
        >
          All
        </button>
        {(["PENDING", "APPROVED", "PAID", "CANCELLED"] as CommissionStatus[]).map(
          (status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={cn(
                "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                statusFilter === status
                  ? "bg-accent text-text-inverse"
                  : "bg-surface-overlay text-text-secondary hover:text-text-primary"
              )}
            >
              {statusLabels[status]}
            </button>
          )
        )}
      </div>

      {/* Commissions Table */}
      {isLoading ? (
        <CommissionsSkeleton />
      ) : filteredCommissions.length === 0 ? (
        <EmptyState
          icon={DollarSign}
          title="No commissions found"
          description="Commissions from your referred tenants will appear here"
        />
      ) : (
        <div className="bg-surface-elevated rounded-lg border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr className="border-b border-border bg-surface-overlay/50">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Tenant
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Base Amount
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Rate
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Commission
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Date
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredCommissions.map((commission) => (
                  <CommissionRow key={commission.id} commission={commission} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
