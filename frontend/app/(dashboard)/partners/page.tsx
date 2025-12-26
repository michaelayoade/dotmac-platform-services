"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Handshake,
  Plus,
  Search,
  Filter,
  RefreshCcw,
  Users,
  Building2,
  DollarSign,
  TrendingUp,
  Play,
  Pause,
  Trash2,
  Edit,
  Eye,
  ChevronRight,
} from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { ConfirmDialog, useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  usePartners,
  useDeletePartner,
  useActivatePartner,
  useDeactivatePartner,
} from "@/lib/hooks/api/use-partners";
import type { PartnerStatus, PartnerTier } from "@/lib/api/partners";

const tierConfig: Record<PartnerTier, { label: string; color: string }> = {
  bronze: { label: "Bronze", color: "bg-surface-overlay text-text-secondary" },
  silver: { label: "Silver", color: "bg-surface-overlay text-text-secondary" },
  gold: { label: "Gold", color: "bg-highlight/15 text-highlight" },
  platinum: { label: "Platinum", color: "bg-status-info/15 text-status-info" },
  direct: { label: "Direct", color: "bg-status-success/15 text-status-success" },
};

const statusConfig: Record<PartnerStatus, { label: string; color: string }> = {
  active: { label: "Active", color: "bg-status-success/15 text-status-success" },
  pending: { label: "Pending", color: "bg-status-warning/15 text-status-warning" },
  suspended: { label: "Suspended", color: "bg-status-error/15 text-status-error" },
  terminated: { label: "Terminated", color: "bg-status-error/15 text-status-error" },
  archived: { label: "Archived", color: "bg-surface-overlay text-text-muted" },
};

export default function PartnersPage() {
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<PartnerStatus | "all">("all");
  const [tierFilter, setTierFilter] = useState<PartnerTier | "all">("all");
  const [page, setPage] = useState(1);

  const { data, isLoading, refetch } = usePartners({
    page,
    pageSize: 20,
    search: searchQuery || undefined,
    status: statusFilter !== "all" ? statusFilter : undefined,
    tier: tierFilter !== "all" ? tierFilter : undefined,
  });
  const deletePartner = useDeletePartner();
  const activatePartner = useActivatePartner();
  const deactivatePartner = useDeactivatePartner();

  const toNumber = (value: number | string | null | undefined) => {
    if (typeof value === "number") {
      return Number.isFinite(value) ? value : 0;
    }
    if (typeof value === "string") {
      const parsed = Number.parseFloat(value);
      return Number.isFinite(parsed) ? parsed : 0;
    }
    return 0;
  };

  const partners = (data?.partners || []).filter((partner) =>
    tierFilter === "all" ? true : partner.tier === tierFilter
  );
  const totalPages = data?.pageCount || 1;
  const totalPartners = data?.totalCount ?? partners.length;
  const activePartners = partners.filter((partner) => partner.status === "active").length;
  const totalReferredAccounts = partners.reduce(
    (sum, partner) => sum + (partner.totalCustomers ?? 0),
    0
  );
  const totalCommissionsPaid = partners.reduce(
    (sum, partner) => sum + toNumber(partner.totalCommissionsPaid),
    0
  );

  const handleDelete = async (id: string, name: string) => {
    const confirmed = await confirm({
      title: "Delete Partner",
      description: `Are you sure you want to delete "${name}"? This will remove all associated data.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deletePartner.mutateAsync(id);
        toast({ title: "Partner deleted" });
      } catch {
        toast({ title: "Failed to delete partner", variant: "error" });
      }
    }
  };

  const handleToggleStatus = async (id: string, isActive: boolean) => {
    try {
      if (isActive) {
        await deactivatePartner.mutateAsync(id);
        toast({ title: "Partner deactivated" });
      } else {
        await activatePartner.mutateAsync(id);
        toast({ title: "Partner activated" });
      }
    } catch {
      toast({ title: "Failed to update partner", variant: "error" });
    }
  };

  if (isLoading) {
    return <PartnersSkeleton />;
  }

  return (
    <div className="space-y-6 animate-fade-up">
      {dialog}

      <PageHeader
        title="Partners"
        description="Manage partner relationships and commissions"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={() => refetch()}>
              <RefreshCcw className="w-4 h-4" />
            </Button>
            <Link href="/partners/new">
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                Add Partner
              </Button>
            </Link>
          </div>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <Handshake className="w-5 h-5 text-accent" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Total Partners</p>
              <p className="text-2xl font-semibold text-text-primary">
                {totalPartners.toLocaleString()}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
              <Building2 className="w-5 h-5 text-status-success" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Active</p>
              <p className="text-2xl font-semibold text-status-success">
                {activePartners.toLocaleString()}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
              <Users className="w-5 h-5 text-status-info" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Referred Accounts</p>
              <p className="text-2xl font-semibold text-text-primary">
                {totalReferredAccounts.toLocaleString()}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
              <DollarSign className="w-5 h-5 text-highlight" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Total Commissions</p>
              <p className="text-2xl font-semibold text-text-primary">
                ${totalCommissionsPaid.toLocaleString()}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <Input
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setPage(1);
            }}
            placeholder="Search partners..."
            className="pl-10"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-text-muted" />
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value as PartnerStatus | "all");
              setPage(1);
            }}
            className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="pending">Pending</option>
            <option value="suspended">Suspended</option>
            <option value="terminated">Terminated</option>
            <option value="archived">Archived</option>
          </select>
          <select
            value={tierFilter}
            onChange={(e) => {
              setTierFilter(e.target.value as PartnerTier | "all");
              setPage(1);
            }}
            className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
          >
            <option value="all">All Tiers</option>
            <option value="platinum">Platinum</option>
            <option value="gold">Gold</option>
            <option value="silver">Silver</option>
            <option value="bronze">Bronze</option>
            <option value="direct">Direct</option>
          </select>
        </div>
      </div>

      {/* Partners Grid */}
      {partners.length === 0 ? (
        <Card className="p-12 text-center">
          <Handshake className="w-12 h-12 text-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">No partners found</h3>
          <p className="text-text-muted mb-6">
            {searchQuery || statusFilter !== "all" || tierFilter !== "all"
              ? "Try adjusting your filters"
              : "Add your first partner to start building relationships"}
          </p>
          <Link href="/partners/new">
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Add Partner
            </Button>
          </Link>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {partners.map((partner) => {
            const status = statusConfig[partner.status as PartnerStatus] || statusConfig.archived;
            const tier = tierConfig[partner.tier as PartnerTier] || tierConfig.bronze;
            const commissionRateRaw = toNumber(partner.defaultCommissionRate);
            const commissionRate =
              commissionRateRaw > 1 ? commissionRateRaw : commissionRateRaw * 100;
            const totalEarned = toNumber(partner.totalCommissionsEarned);
            const totalPaid = toNumber(partner.totalCommissionsPaid);
            const pendingCommissions = Math.max(totalEarned - totalPaid, 0);

            return (
              <Card key={partner.id} className="p-6 hover:border-border-strong transition-colors">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-lg bg-accent-subtle flex items-center justify-center">
                      <Building2 className="w-6 h-6 text-accent" />
                    </div>
                    <div>
                      <Link
                        href={`/partners/${partner.id}`}
                        className="font-semibold text-text-primary hover:text-accent transition-colors"
                      >
                        {partner.companyName}
                      </Link>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={cn("px-2 py-0.5 rounded-full text-xs font-medium", tier.color)}>
                          {tier.label}
                        </span>
                        <span className={cn("px-2 py-0.5 rounded-full text-xs font-medium", status.color)}>
                          {status.label}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {partner.description && (
                  <p className="text-sm text-text-muted mb-4 line-clamp-2">{partner.description}</p>
                )}

                <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                  <div>
                    <p className="text-text-muted">Accounts</p>
                    <p className="font-medium text-text-primary">{partner.totalCustomers || 0}</p>
                  </div>
                  <div>
                    <p className="text-text-muted">Commission Rate</p>
                    <p className="font-medium text-text-primary">{commissionRate.toFixed(2)}%</p>
                  </div>
                  <div>
                    <p className="text-text-muted">Earnings</p>
                    <p className="font-medium text-status-success">
                      ${totalEarned.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-text-muted">Pending</p>
                    <p className="font-medium text-text-primary">
                      ${pendingCommissions.toLocaleString()}
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-border-subtle">
                  <p className="text-xs text-text-muted">
                    Joined {formatDistanceToNow(new Date(partner.createdAt), { addSuffix: true })}
                  </p>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleToggleStatus(partner.id, partner.status === "active")}
                    >
                      {partner.status === "active" ? (
                        <Pause className="w-4 h-4" />
                      ) : (
                        <Play className="w-4 h-4" />
                      )}
                    </Button>
                    <Link href={`/partners/${partner.id}`}>
                      <Button variant="ghost" size="sm">
                        <Eye className="w-4 h-4" />
                      </Button>
                    </Link>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(partner.id, partner.companyName)}
                      className="text-status-error hover:text-status-error"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-text-muted">
            Page {page} of {totalPages}
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

function PartnersSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 w-48 bg-surface-overlay rounded" />
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card p-4 h-20" />
        ))}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="card p-6 h-64" />
        ))}
      </div>
    </div>
  );
}
