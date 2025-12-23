"use client";

import { useState } from "react";
import {
  Search,
  Building2,
  Mail,
  DollarSign,
  Calendar,
  TrendingUp,
  Users,
  MoreVertical,
  ArrowUpRight,
} from "lucide-react";

import { PageHeader, StatusBadge, EmptyState } from "@/components/shared";
import { usePartnerCustomers } from "@/lib/hooks/api/use-partner-portal";
import { cn } from "@/lib/utils";
import type { PartnerCustomer } from "@/types/partner-portal";

const statusColors = {
  ACTIVE: "success" as const,
  CHURNED: "error" as const,
  SUSPENDED: "warning" as const,
};

const engagementLabels = {
  REFERRAL: "Referral",
  MANAGED: "Managed",
  RESELLER: "Reseller",
};

// Demo data
const demoCustomers: PartnerCustomer[] = [
  {
    id: "1",
    tenantId: "t1",
    tenantName: "Acme Corporation",
    contactName: "James Wilson",
    contactEmail: "jwilson@acme.com",
    status: "ACTIVE" as const,
    engagementType: "REFERRAL" as const,
    monthlyRevenue: 4500,
    totalRevenue: 54000,
    commissionRate: 15,
    startDate: "2024-01-15T00:00:00Z",
    lastActivityAt: "2024-12-22T14:30:00Z",
  },
  {
    id: "2",
    tenantId: "t2",
    tenantName: "CloudNine Solutions",
    contactName: "Michael Chen",
    contactEmail: "m.chen@cloudnine.io",
    status: "ACTIVE" as const,
    engagementType: "MANAGED" as const,
    monthlyRevenue: 2800,
    totalRevenue: 33600,
    commissionRate: 20,
    startDate: "2024-03-01T00:00:00Z",
    lastActivityAt: "2024-12-21T09:15:00Z",
  },
  {
    id: "3",
    tenantId: "t3",
    tenantName: "DataFlow Systems",
    contactName: "Emily Rodriguez",
    contactEmail: "emily.r@dataflow.com",
    status: "ACTIVE" as const,
    engagementType: "REFERRAL" as const,
    monthlyRevenue: 3200,
    totalRevenue: 25600,
    commissionRate: 15,
    startDate: "2024-05-10T00:00:00Z",
    lastActivityAt: "2024-12-20T16:45:00Z",
  },
  {
    id: "4",
    tenantId: "t4",
    tenantName: "StartupXYZ",
    contactName: "Amanda Lee",
    contactEmail: "amanda@startupxyz.co",
    status: "CHURNED" as const,
    engagementType: "REFERRAL" as const,
    monthlyRevenue: 0,
    totalRevenue: 4800,
    commissionRate: 15,
    startDate: "2024-06-01T00:00:00Z",
    lastActivityAt: "2024-10-15T11:00:00Z",
  },
];

function CustomerCard({ customer }: { customer: PartnerCustomer }) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const timeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));

    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}d ago`;
    return formatDate(dateString);
  };

  return (
    <div className="bg-surface-elevated rounded-lg border border-border overflow-hidden hover:border-border-hover transition-colors">
      {/* Header */}
      <div className="p-5 border-b border-border">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-1">
              <h3 className="font-semibold text-text-primary truncate">
                {customer.tenantName}
              </h3>
              <StatusBadge status={statusColors[customer.status]} label={customer.status} />
            </div>
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <span>{customer.contactName}</span>
              <span className="text-text-muted/50">•</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-surface-overlay">
                {engagementLabels[customer.engagementType]}
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
            Monthly
          </p>
          <p className="text-lg font-semibold text-text-primary">
            ${customer.monthlyRevenue.toLocaleString()}
          </p>
        </div>
        <div className="p-4">
          <p className="text-xs text-text-muted uppercase tracking-wider mb-1">
            Total Revenue
          </p>
          <p className="text-lg font-semibold text-text-primary">
            ${customer.totalRevenue.toLocaleString()}
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="px-5 py-3 bg-surface-overlay/50 flex items-center justify-between text-sm">
        <div className="flex items-center gap-4 text-text-muted">
          <span className="flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5" />
            Since {formatDate(customer.startDate)}
          </span>
        </div>
        <span className="text-xs text-text-muted">
          Active {timeAgo(customer.lastActivityAt)}
        </span>
      </div>
    </div>
  );
}

function CustomersSkeleton() {
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

export default function CustomersPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "ACTIVE" | "CHURNED" | "SUSPENDED">("ALL");

  const { data, isLoading, error } = usePartnerCustomers({
    status: statusFilter !== "ALL" ? statusFilter : undefined,
    search: searchQuery || undefined,
  });

  const customers = data?.customers || demoCustomers;
  const filteredCustomers =
    statusFilter === "ALL"
      ? customers
      : customers.filter((c) => c.status === statusFilter);

  // Summary stats
  const activeCustomers = customers.filter((c) => c.status === "ACTIVE").length;
  const totalMonthly = customers
    .filter((c) => c.status === "ACTIVE")
    .reduce((sum, c) => sum + c.monthlyRevenue, 0);
  const totalRevenue = customers.reduce((sum, c) => sum + c.totalRevenue, 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Customers"
        description="Your assigned customers and their revenue"
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="bg-surface-elevated rounded-lg border border-border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-accent/10 text-accent">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Active Customers</p>
              <p className="text-xl font-semibold text-text-primary">
                {activeCustomers}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-surface-elevated rounded-lg border border-border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-status-success/10 text-status-success">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Monthly Revenue</p>
              <p className="text-xl font-semibold text-text-primary">
                ${totalMonthly.toLocaleString()}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-surface-elevated rounded-lg border border-border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-highlight/10 text-highlight">
              <DollarSign className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Total Revenue</p>
              <p className="text-xl font-semibold text-text-primary">
                ${totalRevenue.toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            placeholder="Search customers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-md border border-border bg-surface text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent"
          />
        </div>

        <div className="flex gap-2">
          {(["ALL", "ACTIVE", "CHURNED", "SUSPENDED"] as const).map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={cn(
                "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                statusFilter === status
                  ? "bg-accent text-white"
                  : "bg-surface-overlay text-text-secondary hover:text-text-primary"
              )}
            >
              {status === "ALL" ? "All" : status.charAt(0) + status.slice(1).toLowerCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Customers Grid */}
      {isLoading ? (
        <CustomersSkeleton />
      ) : filteredCustomers.length === 0 ? (
        <EmptyState
          icon={Building2}
          title="No customers found"
          description="Your referred customers will appear here once they sign up"
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredCustomers.map((customer) => (
            <CustomerCard key={customer.id} customer={customer} />
          ))}
        </div>
      )}
    </div>
  );
}
