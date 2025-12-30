"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Package,
  ArrowLeft,
  CheckCircle,
  XCircle,
  Clock,
  BarChart3,
  ChevronRight,
  AlertCircle,
} from "lucide-react";
import { Button, Card } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  useActiveAddons,
  useCancelAddon,
  type ActiveAddon,
} from "@/lib/hooks/api/use-billing";

const statusConfig = {
  active: {
    label: "Active",
    icon: CheckCircle,
    class: "bg-status-success/15 text-status-success",
  },
  cancelled: {
    label: "Cancelled",
    icon: XCircle,
    class: "bg-status-error/15 text-status-error",
  },
  expired: {
    label: "Expired",
    icon: Clock,
    class: "bg-text-muted/15 text-text-muted",
  },
};

export default function ActiveAddonsPage() {
  const { toast } = useToast();
  const { data: addons, isLoading } = useActiveAddons();
  const cancelAddon = useCancelAddon();
  const [cancellingId, setCancellingId] = useState<string | null>(null);

  const handleCancel = async (addon: ActiveAddon) => {
    if (!confirm(`Are you sure you want to cancel "${addon.addon.name}"?`)) {
      return;
    }

    setCancellingId(addon.id);
    try {
      await cancelAddon.mutateAsync(addon.id);
      toast({
        title: "Add-on cancelled",
        description: `${addon.addon.name} has been cancelled.`,
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to cancel add-on.",
        variant: "error",
      });
    } finally {
      setCancellingId(null);
    }
  };

  if (isLoading) {
    return <ActiveAddonsSkeleton />;
  }

  const activeAddons = addons?.filter((a) => a.status === "active") ?? [];
  const otherAddons = addons?.filter((a) => a.status !== "active") ?? [];

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="My Add-ons"
        breadcrumbs={[
          { label: "Billing", href: "/billing" },
          { label: "Add-ons", href: "/billing/addons" },
          { label: "Active" },
        ]}
        actions={
          <Link href="/billing/addons">
            <Button variant="ghost">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Browse Marketplace
            </Button>
          </Link>
        }
      />

      {/* Active Add-ons Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-status-success" />
            <div>
              <p className="text-sm text-text-muted">Active Add-ons</p>
              <p className="text-xl font-bold text-text-primary">{activeAddons.length}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <BarChart3 className="w-5 h-5 text-accent" />
            <div>
              <p className="text-sm text-text-muted">Monthly Cost</p>
              <p className="text-xl font-bold text-text-primary">
                ${(
                  activeAddons
                    .filter((a) => a.addon.billingCycle === "monthly")
                    .reduce((sum, a) => sum + a.addon.price, 0) / 100
                ).toFixed(2)}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <Clock className="w-5 h-5 text-status-warning" />
            <div>
              <p className="text-sm text-text-muted">Renewing Soon</p>
              <p className="text-xl font-bold text-text-primary">
                {activeAddons.filter((a) => {
                  if (!a.nextBillingDate) return false;
                  const days = Math.ceil(
                    (new Date(a.nextBillingDate).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
                  );
                  return days <= 7 && days > 0;
                }).length}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Active Add-ons List */}
      {activeAddons.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-text-primary">Active Add-ons</h2>
          <div className="space-y-4">
            {activeAddons.map((addon) => (
              <ActiveAddonCard
                key={addon.id}
                addon={addon}
                onCancel={() => handleCancel(addon)}
                isCancelling={cancellingId === addon.id}
              />
            ))}
          </div>
        </div>
      )}

      {/* Other Add-ons */}
      {otherAddons.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-text-primary">Previous Add-ons</h2>
          <div className="space-y-4">
            {otherAddons.map((addon) => (
              <ActiveAddonCard
                key={addon.id}
                addon={addon}
                onCancel={() => handleCancel(addon)}
                isCancelling={cancellingId === addon.id}
              />
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {addons?.length === 0 && (
        <Card className="p-12 text-center">
          <Package className="w-12 h-12 mx-auto text-text-muted mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">No add-ons yet</h3>
          <p className="text-text-muted mb-6">
            Explore our marketplace to find add-ons for your needs
          </p>
          <Link href="/billing/addons">
            <Button className="shadow-glow-sm hover:shadow-glow">
              Browse Marketplace
            </Button>
          </Link>
        </Card>
      )}
    </div>
  );
}

function ActiveAddonCard({
  addon,
  onCancel,
  isCancelling,
}: {
  addon: ActiveAddon;
  onCancel: () => void;
  isCancelling: boolean;
}) {
  const statusInfo = statusConfig[addon.status];
  const StatusIcon = statusInfo.icon;

  return (
    <Card className="p-6">
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 rounded-lg bg-accent-subtle flex items-center justify-center flex-shrink-0">
          {addon.addon.icon ? (
            <span className="text-2xl">{addon.addon.icon}</span>
          ) : (
            <Package className="w-6 h-6 text-accent" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-1">
            <Link
              href={`/billing/addons/${addon.addonId}`}
              className="font-semibold text-text-primary hover:text-accent"
            >
              {addon.addon.name}
            </Link>
            <span className={cn("status-badge", statusInfo.class)}>
              <StatusIcon className="w-3 h-3 mr-1" />
              {statusInfo.label}
            </span>
          </div>

          <p className="text-sm text-text-muted mb-3">{addon.addon.description}</p>

          <div className="flex flex-wrap gap-4 text-sm">
            <div>
              <span className="text-text-muted">Price: </span>
              <span className="font-medium text-text-primary">
                ${(addon.addon.price / 100).toFixed(2)}
                {addon.addon.billingCycle === "monthly" && "/mo"}
                {addon.addon.billingCycle === "yearly" && "/yr"}
              </span>
            </div>
            <div>
              <span className="text-text-muted">Purchased: </span>
              <span className="font-medium text-text-primary">
                {new Date(addon.purchasedAt).toLocaleDateString()}
              </span>
            </div>
            {addon.nextBillingDate && addon.status === "active" && (
              <div>
                <span className="text-text-muted">Next billing: </span>
                <span className="font-medium text-text-primary">
                  {new Date(addon.nextBillingDate).toLocaleDateString()}
                </span>
              </div>
            )}
          </div>

          {/* Usage */}
          {addon.usage && (
            <div className="mt-4 p-3 bg-surface-overlay rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-text-muted">Usage</span>
                <span className="text-sm font-medium text-text-primary">
                  {addon.usage.current.toLocaleString()} / {addon.usage.limit.toLocaleString()} {addon.usage.unit}
                </span>
              </div>
              <div className="h-2 bg-surface-overlay rounded-full overflow-hidden">
                <div
                  className={cn(
                    "h-full transition-all",
                    addon.usage.current / addon.usage.limit > 0.9
                      ? "bg-status-error"
                      : addon.usage.current / addon.usage.limit > 0.7
                      ? "bg-status-warning"
                      : "bg-status-success"
                  )}
                  style={{ width: `${Math.min((addon.usage.current / addon.usage.limit) * 100, 100)}%` }}
                />
              </div>
              {addon.usage.current / addon.usage.limit > 0.9 && (
                <div className="flex items-center gap-1 mt-2 text-xs text-status-warning">
                  <AlertCircle className="w-3 h-3" />
                  Approaching limit
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {addon.status === "active" && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onCancel}
              disabled={isCancelling}
              className="text-status-error hover:text-status-error"
            >
              {isCancelling ? "Cancelling..." : "Cancel"}
            </Button>
          )}
          <Link href={`/billing/addons/${addon.addonId}`}>
            <Button variant="outline" size="sm">
              View Details
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </Link>
        </div>
      </div>
    </Card>
  );
}

function ActiveAddonsSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center justify-between">
        <div>
          <div className="h-4 w-32 bg-surface-overlay rounded mb-2" />
          <div className="h-8 w-48 bg-surface-overlay rounded" />
        </div>
        <div className="h-10 w-40 bg-surface-overlay rounded" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="card p-4">
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 bg-surface-overlay rounded" />
              <div>
                <div className="h-4 w-24 bg-surface-overlay rounded mb-2" />
                <div className="h-6 w-8 bg-surface-overlay rounded" />
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="space-y-4">
        {[1, 2].map((i) => (
          <div key={i} className="card p-6">
            <div className="h-24 bg-surface-overlay rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}
