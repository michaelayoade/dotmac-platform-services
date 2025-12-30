"use client";

import { useState, useEffect, useRef } from "react";
import { useSearchParams } from "next/navigation";
import {
  Plus,
  Building2,
  Mail,
  Phone,
  Calendar,
  DollarSign,
  MoreVertical,
  Pencil,
  Trash2,
  Link2,
  Copy,
  Check,
  RefreshCw,
} from "lucide-react";

import { PageHeader, StatusBadge, EmptyState, SearchInput } from "@/components/shared";
import { ReferralForm } from "@/components/features/partner/referral-form";
import {
  usePartnerReferrals,
  useDeleteReferral,
  useReferralLink,
  useGenerateReferralLink,
} from "@/lib/hooks/api/use-partner-portal";
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


function ReferralCard({
  referral,
  onEdit,
  onDelete,
}: {
  referral: Referral;
  onEdit: (referral: Referral) => void;
  onDelete: (referral: Referral) => void;
}) {
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowMenu(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

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

        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-2 rounded-md text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors"
          >
            <MoreVertical className="w-4 h-4" />
          </button>

          {showMenu && (
            <div className="absolute right-0 top-full mt-1 z-10 w-36 bg-surface-elevated border border-border rounded-lg shadow-lg overflow-hidden">
              <button
                onClick={() => {
                  setShowMenu(false);
                  onEdit(referral);
                }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-text-primary hover:bg-surface-overlay transition-colors"
              >
                <Pencil className="w-4 h-4" />
                Edit
              </button>
              <button
                onClick={() => {
                  setShowMenu(false);
                  onDelete(referral);
                }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-status-error hover:bg-status-error/10 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </div>
          )}
        </div>
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

function ReferralLinkCard() {
  const { data: linkData, isLoading } = useReferralLink();
  const generateLink = useGenerateReferralLink();
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (linkData?.url) {
      await navigator.clipboard.writeText(linkData.url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleGenerate = async () => {
    try {
      await generateLink.mutateAsync();
    } catch (error) {
      console.error("Failed to generate referral link:", error);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-surface-elevated rounded-lg border border-border p-5 animate-pulse">
        <div className="h-5 w-32 bg-surface-overlay rounded mb-3" />
        <div className="h-10 w-full bg-surface-overlay rounded" />
      </div>
    );
  }

  return (
    <div className="bg-accent-subtle/30 rounded-lg border border-accent/20 p-5">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
          <Link2 className="w-5 h-5 text-accent" />
        </div>
        <div>
          <h3 className="font-semibold text-text-primary">Your Referral Link</h3>
          <p className="text-xs text-text-muted">Share this link to earn commissions</p>
        </div>
      </div>

      {linkData?.url ? (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <div className="flex-1 px-3 py-2 bg-surface rounded-lg border border-border text-sm text-text-secondary font-mono truncate">
              {linkData.url}
            </div>
            <button
              onClick={handleCopy}
              className={cn(
                "p-2 rounded-lg transition-colors",
                copied
                  ? "bg-status-success/15 text-status-success"
                  : "bg-surface-overlay text-text-muted hover:text-text-primary"
              )}
            >
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            </button>
            <button
              onClick={handleGenerate}
              disabled={generateLink.isPending}
              className="p-2 rounded-lg bg-surface-overlay text-text-muted hover:text-text-primary transition-colors disabled:opacity-50"
              title="Generate new link"
            >
              <RefreshCw className={cn("w-4 h-4", generateLink.isPending && "animate-spin")} />
            </button>
          </div>
          <p className="text-xs text-text-muted">
            {linkData.usageCount} click{linkData.usageCount !== 1 ? "s" : ""} so far
          </p>
        </div>
      ) : (
        <button
          onClick={handleGenerate}
          disabled={generateLink.isPending}
          className="w-full px-4 py-2 rounded-lg bg-accent text-text-inverse hover:bg-accent-hover transition-colors disabled:opacity-50"
        >
          {generateLink.isPending ? "Generating..." : "Generate Referral Link"}
        </button>
      )}
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
  const [editingReferral, setEditingReferral] = useState<Referral | null>(null);
  const [statusFilter, setStatusFilter] = useState<ReferralStatus | "ALL">("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  const { data, isLoading, error, refetch } = usePartnerReferrals({
    status: statusFilter !== "ALL" ? statusFilter : undefined,
    search: searchQuery || undefined,
  });
  const deleteReferral = useDeleteReferral();

  const errorMessage =
    error instanceof Error ? error.message : error ? "Failed to load referrals." : null;

  // Open form if action=new in URL
  useEffect(() => {
    if (searchParams.get("action") === "new") {
      setIsFormOpen(true);
    }
  }, [searchParams]);

  const handleEdit = (referral: Referral) => {
    setEditingReferral(referral);
    setIsFormOpen(true);
  };

  const handleDelete = async (referral: Referral) => {
    if (confirm(`Are you sure you want to delete the referral for ${referral.companyName}?`)) {
      try {
        await deleteReferral.mutateAsync(referral.id);
      } catch (error) {
        console.error("Failed to delete referral:", error);
      }
    }
  };

  const handleFormClose = () => {
    setIsFormOpen(false);
    setEditingReferral(null);
  };

  const handleFormSuccess = () => {
    refetch();
    handleFormClose();
  };

  const referrals = data?.referrals ?? [];
  const totalReferrals = data ? referrals.length : null;
  const filteredReferrals =
    statusFilter === "ALL"
      ? referrals
      : referrals.filter((r) => r.status === statusFilter);

  const statusCounts = data
    ? referrals.reduce(
        (acc, r) => {
          acc[r.status] = (acc[r.status] || 0) + 1;
          return acc;
        },
        {} as Record<string, number>
      )
    : null;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Referrals"
        description="Track and manage your tenant referrals"
        actions={
          <button
            onClick={() => setIsFormOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-accent text-text-inverse hover:bg-accent-hover transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Referral
          </button>
        }
      />

      {/* Referral Link Generator */}
      <ReferralLinkCard />

      {errorMessage && (
        <div className="p-3 rounded-md bg-status-error/10 text-status-error text-sm">
          {errorMessage}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Search */}
        <SearchInput
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder="Search referrals..."
          className="flex-1 max-w-md"
        />

        {/* Status Filter */}
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
            All ({totalReferrals ?? "—"})
          </button>
          {(["NEW", "CONTACTED", "QUALIFIED", "CONVERTED", "LOST"] as ReferralStatus[]).map(
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
                {statusLabels[status]} ({statusCounts ? statusCounts[status] || 0 : "—"})
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
            <ReferralCard
              key={referral.id}
              referral={referral}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {/* Referral Form Modal */}
      <ReferralForm
        isOpen={isFormOpen}
        onClose={handleFormClose}
        onSuccess={handleFormSuccess}
        editReferral={editingReferral}
      />
    </div>
  );
}
