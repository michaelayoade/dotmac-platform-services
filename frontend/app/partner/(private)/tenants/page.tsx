"use client";

import { useState } from "react";
import {
  Building2,
  Mail,
  DollarSign,
  Calendar,
  TrendingUp,
  Users,
  MoreVertical,
  ArrowUpRight,
} from "lucide-react";

import { PageHeader, StatusBadge, EmptyState, SearchInput } from "@/components/shared";
import { usePartnerTenants } from "@/lib/hooks/api/use-partner-portal";
import { cn } from "@/lib/utils";
import type { PartnerTenant } from "@/types/partner-portal";

const statusColors = {
  ACTIVE: "success" as const,
  INACTIVE: "warning" as const,
};


function TenantCard({ tenant }: { tenant: PartnerTenant }) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const statusLabel = tenant.isActive ? "ACTIVE" : "INACTIVE";

  return (
    <div className="bg-surface-elevated rounded-lg border border-border overflow-hidden hover:border-border-hover transition-colors">
      {/* Header */}
      <div className="p-5 border-b border-border">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-1">
              <h3 className="font-semibold text-text-primary truncate">
                {tenant.tenantName}
              </h3>
              <StatusBadge status={statusColors[statusLabel]} label={statusLabel} />
            </div>
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <span className="text-xs px-2 py-0.5 rounded-full bg-surface-overlay">
                {tenant.engagementType}
              </span>
            </div>
          </div>
          <button className="p-2 rounded-md text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors">
            <MoreVertical className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 divide-x divide-border">
        <div className="p-4">
          <p className="text-xs text-text-muted uppercase tracking-wider mb-1">
            Total Commissions
          </p>
          <p className="text-lg font-semibold text-text-primary">
            ${tenant.totalCommissions.toLocaleString()}
          </p>
        </div>
        <div className="p-4">
          <p className="text-xs text-text-muted uppercase tracking-wider mb-1">
            Total Revenue
          </p>
          <p className="text-lg font-semibold text-text-primary">
            ${tenant.totalRevenue.toLocaleString()}
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="px-5 py-3 bg-surface-overlay/50 flex items-center justify-between text-sm">
        <div className="flex items-center gap-4 text-text-muted">
          <span className="flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5" />
            Since {formatDate(tenant.startDate)}
          </span>
        </div>
        {tenant.endDate ? (
          <span className="text-xs text-text-muted">
            Ended {formatDate(tenant.endDate)}
          </span>
        ) : null}
      </div>
    </div>
  );
}

function TenantsSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 animate-pulse">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <div
          key={i}
          className="bg-surface-elevated rounded-lg border border-border h-52"
        >
          <div className="p-5 border-b border-border">
            <div className="h-5 w-32 bg-surface-overlay rounded mb-2" />
            <div className="h-4 w-24 bg-surface-overlay rounded" />
          </div>
          <div className="grid grid-cols-2 divide-x divide-border">
            <div className="p-4">
              <div className="h-3 w-16 bg-surface-overlay rounded mb-2" />
              <div className="h-6 w-20 bg-surface-overlay rounded" />
            </div>
            <div className="p-4">
              <div className="h-3 w-16 bg-surface-overlay rounded mb-2" />
              <div className="h-6 w-20 bg-surface-overlay rounded" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function TenantsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "ACTIVE" | "INACTIVE">("ALL");

  const { data, isLoading, error } = usePartnerTenants({
    status: statusFilter !== "ALL" ? statusFilter : undefined,
    search: searchQuery || undefined,
  });
  const errorMessage =
    error instanceof Error ? error.message : error ? "Failed to load tenants." : null;

  const tenants = data?.tenants ?? [];
  const filteredTenants =
    statusFilter === "ALL"
      ? tenants
      : tenants.filter((t) => (t.isActive ? "ACTIVE" : "INACTIVE") === statusFilter);

  // Summary stats
  const activeTenants = data ? tenants.filter((t) => t.isActive).length : null;
  const totalCommissions = data
    ? tenants.reduce((sum, t) => sum + t.totalCommissions, 0)
    : null;
  const totalRevenue = data
    ? tenants.reduce((sum, t) => sum + t.totalRevenue, 0)
    : null;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tenants"
        description="Your managed tenants and their revenue"
      />

      {errorMessage && (
        <div className="p-3 rounded-md bg-status-error/10 text-status-error text-sm">
          {errorMessage}
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="bg-surface-elevated rounded-lg border border-border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-accent/15 text-accent">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Active Tenants</p>
              <p className="text-xl font-semibold text-text-primary">
                {activeTenants ?? "—"}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-surface-elevated rounded-lg border border-border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-status-success/15 text-status-success">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Total Commissions</p>
              <p className="text-xl font-semibold text-text-primary">
                {totalCommissions !== null ? `$${totalCommissions.toLocaleString()}` : "—"}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-surface-elevated rounded-lg border border-border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-highlight/15 text-highlight">
              <DollarSign className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Total Revenue</p>
              <p className="text-xl font-semibold text-text-primary">
                {totalRevenue !== null ? `$${totalRevenue.toLocaleString()}` : "—"}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <SearchInput
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder="Search tenants..."
          className="flex-1 max-w-md"
        />

        <div className="flex gap-2">
          {(["ALL", "ACTIVE", "INACTIVE"] as const).map((status) => (
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
              {status === "ALL" ? "All" : status.charAt(0) + status.slice(1).toLowerCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Tenants Grid */}
      {isLoading ? (
        <TenantsSkeleton />
      ) : filteredTenants.length === 0 ? (
        <EmptyState
          icon={Building2}
          title="No tenants found"
          description="Managed tenants will appear here once they are linked"
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredTenants.map((tenant) => (
            <TenantCard key={tenant.id} tenant={tenant} />
          ))}
        </div>
      )}
    </div>
  );
}
