"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import {
  Plus,
  Search,
  Filter,
  ChevronDown,
  Building2,
  Mail,
  Phone,
  Calendar,
  DollarSign,
  MoreVertical,
} from "lucide-react";

import { PageHeader, StatusBadge, EmptyState } from "@/components/shared";
import { ReferralForm } from "@/components/features/partner/referral-form";
import { usePartnerReferrals } from "@/lib/hooks/api/use-partner-portal";
import { cn } from "@/lib/utils";
import type { Referral, ReferralStatus } from "@/types/partner-portal";

const statusColors: Record<ReferralStatus, "pending" | "success" | "warning" | "error" | "info"> = {
  NEW: "info",
  CONTACTED: "pending",
  QUALIFIED: "warning",
  CONVERTED: "success",
  LOST: "error",
};

const statusLabels: Record<ReferralStatus, string> = {
  NEW: "New",
  CONTACTED: "Contacted",
  QUALIFIED: "Qualified",
  CONVERTED: "Converted",
  LOST: "Lost",
};

// Demo data for when API is not available
const demoReferrals: Referral[] = [
  {
    id: "1",
    companyName: "TechStart Inc.",
    contactName: "Sarah Johnson",
    contactEmail: "sarah@techstart.com",
    contactPhone: "+1 (555) 123-4567",
    status: "NEW" as ReferralStatus,
    estimatedValue: 2500,
    createdAt: "2024-12-20T10:30:00Z",
    updatedAt: "2024-12-20T10:30:00Z",
    notes: "Interested in enterprise plan",
  },
  {
    id: "2",
    companyName: "CloudNine Solutions",
    contactName: "Michael Chen",
    contactEmail: "m.chen@cloudnine.io",
    contactPhone: "+1 (555) 234-5678",
    status: "CONTACTED" as ReferralStatus,
    estimatedValue: 1800,
    createdAt: "2024-12-18T14:15:00Z",
    updatedAt: "2024-12-18T14:15:00Z",
    notes: "Follow up scheduled for next week",
  },
  {
    id: "3",
    companyName: "DataFlow Systems",
    contactName: "Emily Rodriguez",
    contactEmail: "emily.r@dataflow.com",
    status: "QUALIFIED" as ReferralStatus,
    estimatedValue: 3200,
    createdAt: "2024-12-15T09:00:00Z",
    updatedAt: "2024-12-15T09:00:00Z",
    notes: "Needs custom integration support",
  },
  {
    id: "4",
    companyName: "Acme Corporation",
    contactName: "James Wilson",
    contactEmail: "jwilson@acme.com",
    contactPhone: "+1 (555) 345-6789",
    status: "CONVERTED" as ReferralStatus,
    estimatedValue: 4500,
    createdAt: "2024-12-10T11:45:00Z",
    updatedAt: "2024-12-10T11:45:00Z",
    convertedAt: "2024-12-18T16:00:00Z",
  },
  {
    id: "5",
    companyName: "StartupXYZ",
    contactName: "Amanda Lee",
    contactEmail: "amanda@startupxyz.co",
    status: "LOST" as ReferralStatus,
    estimatedValue: 1200,
    createdAt: "2024-12-05T08:30:00Z",
    updatedAt: "2024-12-05T08:30:00Z",
    notes: "Went with competitor",
  },
];

function ReferralCard({ referral }: { referral: Referral }) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <div className="bg-surface-elevated rounded-lg border border-border p-5 hover:border-border-hover transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="font-semibold text-text-primary truncate">
              {referral.companyName}
            </h3>
            <StatusBadge
              status={statusColors[referral.status]}
              label={statusLabels[referral.status]}
            />
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center gap-2 text-sm text-text-secondary">
              <Building2 className="w-4 h-4 text-text-muted" />
              <span>{referral.contactName}</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-text-secondary">
              <Mail className="w-4 h-4 text-text-muted" />
              <a
                href={`mailto:${referral.contactEmail}`}
                className="hover:text-accent"
              >
                {referral.contactEmail}
              </a>
            </div>
            {referral.contactPhone && (
              <div className="flex items-center gap-2 text-sm text-text-secondary">
                <Phone className="w-4 h-4 text-text-muted" />
                <span>{referral.contactPhone}</span>
              </div>
            )}
          </div>
        </div>

        <button className="p-2 rounded-md text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors">
          <MoreVertical className="w-4 h-4" />
        </button>
      </div>

      {referral.notes && (
        <p className="mt-3 text-sm text-text-muted line-clamp-2">
          {referral.notes}
        </p>
      )}

      <div className="flex items-center justify-between mt-4 pt-4 border-t border-border">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-sm text-text-muted">
            <Calendar className="w-4 h-4" />
            <span>{formatDate(referral.createdAt)}</span>
          </div>
          {referral.estimatedValue && (
            <div className="flex items-center gap-1.5 text-sm text-text-muted">
              <DollarSign className="w-4 h-4" />
              <span>${referral.estimatedValue.toLocaleString()}/mo</span>
            </div>
          )}
        </div>

        {referral.status === "CONVERTED" && referral.convertedAt && (
          <span className="text-xs text-status-success">
            Converted {formatDate(referral.convertedAt)}
          </span>
        )}
      </div>
    </div>
  );
}

function ReferralsSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 animate-pulse">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <div
          key={i}
          className="bg-surface-elevated rounded-lg border border-border p-5 h-48"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="h-5 w-32 bg-surface-overlay rounded" />
            <div className="h-5 w-16 bg-surface-overlay rounded-full" />
          </div>
          <div className="space-y-2">
            <div className="h-4 w-24 bg-surface-overlay rounded" />
            <div className="h-4 w-40 bg-surface-overlay rounded" />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function ReferralsPage() {
  const searchParams = useSearchParams();
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState<ReferralStatus | "ALL">("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  const { data, isLoading, error, refetch } = usePartnerReferrals({
    status: statusFilter !== "ALL" ? statusFilter : undefined,
    search: searchQuery || undefined,
  });

  // Open form if action=new in URL
  useEffect(() => {
    if (searchParams.get("action") === "new") {
      setIsFormOpen(true);
    }
  }, [searchParams]);

  const referrals = data?.referrals || demoReferrals;
  const filteredReferrals =
    statusFilter === "ALL"
      ? referrals
      : referrals.filter((r) => r.status === statusFilter);

  const statusCounts = referrals.reduce(
    (acc, r) => {
      acc[r.status] = (acc[r.status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Referrals"
        description="Track and manage your customer referrals"
        actions={
          <button
            onClick={() => setIsFormOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-accent text-white hover:bg-accent-hover transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Referral
          </button>
        }
      />

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            placeholder="Search referrals..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-md border border-border bg-surface text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent"
          />
        </div>

        {/* Status Filter */}
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setStatusFilter("ALL")}
            className={cn(
              "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
              statusFilter === "ALL"
                ? "bg-accent text-white"
                : "bg-surface-overlay text-text-secondary hover:text-text-primary"
            )}
          >
            All ({referrals.length})
          </button>
          {(["NEW", "CONTACTED", "QUALIFIED", "CONVERTED", "LOST"] as ReferralStatus[]).map(
            (status) => (
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
                {statusLabels[status]} ({statusCounts[status] || 0})
              </button>
            )
          )}
        </div>
      </div>

      {/* Referrals Grid */}
      {isLoading ? (
        <ReferralsSkeleton />
      ) : filteredReferrals.length === 0 ? (
        <EmptyState
          icon={Building2}
          title="No referrals found"
          description={
            statusFilter !== "ALL"
              ? `No referrals with status "${statusLabels[statusFilter]}"`
              : "Submit your first referral to start earning commissions"
          }
          action={{
            label: "Submit Referral",
            onClick: () => setIsFormOpen(true),
          }}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredReferrals.map((referral) => (
            <ReferralCard key={referral.id} referral={referral} />
          ))}
        </div>
      )}

      {/* New Referral Form Modal */}
      <ReferralForm
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSuccess={() => refetch()}
      />
    </div>
  );
}
