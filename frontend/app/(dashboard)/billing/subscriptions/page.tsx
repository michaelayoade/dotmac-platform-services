"use client";

import { useState } from "react";
import Link from "next/link";
import {
  CreditCard,
  Play,
  Pause,
  XCircle,
  CheckCircle,
  Clock,
  AlertCircle,
  MoreHorizontal,
  Calendar,
  RefreshCw,
} from "lucide-react";
import { Button, useToast } from "@/lib/dotmac/core";
import { cn } from "@/lib/utils";
import { useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useSubscriptions,
  usePauseSubscription,
  useResumeSubscription,
  useCancelSubscription,
} from "@/lib/hooks/api/use-billing";
import type { Subscription, SubscriptionStatus } from "@/types/models";

export default function SubscriptionsPage() {
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();
  const [statusFilter, setStatusFilter] = useState<SubscriptionStatus | undefined>();
  const { data, isLoading } = useSubscriptions({ status: statusFilter });

  const pauseSubscription = usePauseSubscription();
  const resumeSubscription = useResumeSubscription();
  const cancelSubscription = useCancelSubscription();

  const [actioningId, setActioningId] = useState<string | null>(null);

  const subscriptions = data?.items || [];

  const handlePause = async (id: string) => {
    const subscription = subscriptions.find((s: Subscription) => s.id === id);
    const confirmed = await confirm({
      title: "Pause Subscription",
      description: `Are you sure you want to pause ${subscription?.customer?.name || "this"} subscription? Billing will be suspended until resumed for the tenant.`,
      variant: "warning",
    });

    if (!confirmed) return;

    setActioningId(id);
    try {
      await pauseSubscription.mutateAsync(id);
      toast({
        title: "Subscription paused",
        description: "The subscription has been paused.",
        variant: "success",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to pause subscription.",
        variant: "error",
      });
    } finally {
      setActioningId(null);
    }
  };

  const handleResume = async (id: string) => {
    const subscription = subscriptions.find((s: Subscription) => s.id === id);
    const confirmed = await confirm({
      title: "Resume Subscription",
      description: `Are you sure you want to resume ${subscription?.customer?.name || "this"} subscription? Billing will resume immediately.`,
      variant: "info",
    });

    if (!confirmed) return;

    setActioningId(id);
    try {
      await resumeSubscription.mutateAsync(id);
      toast({
        title: "Subscription resumed",
        description: "The subscription has been resumed.",
        variant: "success",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to resume subscription.",
        variant: "error",
      });
    } finally {
      setActioningId(null);
    }
  };

  const handleCancel = async (id: string) => {
    const subscription = subscriptions.find((s: Subscription) => s.id === id);
    const confirmed = await confirm({
      title: "Cancel Subscription",
      description: `Are you sure you want to cancel ${subscription?.customer?.name || "this"} subscription? The tenant will lose access at the end of the current billing period.`,
      variant: "warning",
    });

    if (!confirmed) return;

    setActioningId(id);
    try {
      await cancelSubscription.mutateAsync(id);
      toast({
        title: "Subscription cancelled",
        description: "The subscription has been cancelled.",
        variant: "success",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to cancel subscription.",
        variant: "error",
      });
    } finally {
      setActioningId(null);
    }
  };

  const statusConfig: Record<SubscriptionStatus, { icon: React.ElementType; class: string; label: string }> = {
    active: { icon: CheckCircle, class: "status-badge--success", label: "Active" },
    trialing: { icon: Clock, class: "status-badge--info", label: "Trial" },
    past_due: { icon: AlertCircle, class: "status-badge--warning", label: "Past Due" },
    canceled: { icon: XCircle, class: "bg-surface-overlay text-text-muted", label: "Cancelled" },
    paused: { icon: Pause, class: "status-badge--warning", label: "Paused" },
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount / 100);
  };

  return (
    <div className="space-y-6">
      {/* Confirm dialog */}
      {dialog}

      {/* Page Header with Breadcrumbs */}
      <div>
        <div className="flex items-center gap-2 text-sm text-text-muted mb-4">
          <Link href="/billing" className="hover:text-text-secondary">
            Billing
          </Link>
          <span>/</span>
          <span className="text-text-primary">Subscriptions</span>
        </div>

        <div className="page-header">
          <div>
            <h1 className="page-title">Subscriptions</h1>
            <p className="page-description">
              Manage tenant subscriptions and billing cycles
            </p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex items-center gap-2">
          <span className="text-sm text-text-muted">Status:</span>
          {[
            { value: undefined, label: "All" },
            { value: "active" as SubscriptionStatus, label: "Active" },
            { value: "trialing" as SubscriptionStatus, label: "Trial" },
            { value: "past_due" as SubscriptionStatus, label: "Past Due" },
            { value: "paused" as SubscriptionStatus, label: "Paused" },
            { value: "canceled" as SubscriptionStatus, label: "Cancelled" },
          ].map((option) => (
            <Button
              key={option.label}
              variant={statusFilter === option.value ? "default" : "outline"}
              size="sm"
              onClick={() => setStatusFilter(option.value)}
              className={cn(statusFilter === option.value && "shadow-glow-sm")}
            >
              {option.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Subscriptions Table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-text-muted">
            Loading subscriptions...
          </div>
        ) : subscriptions.length === 0 ? (
          <div className="p-12 text-center">
            <CreditCard className="w-12 h-12 mx-auto text-text-muted mb-4" />
            <h3 className="text-lg font-semibold text-text-primary mb-2">
              No subscriptions found
            </h3>
            <p className="text-text-muted">
              {statusFilter
                ? `No ${statusFilter} subscriptions`
                : "No subscriptions to display"}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Tenant</th>
                  <th>Plan</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Current Period</th>
                  <th>Created</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {subscriptions.map((subscription: Subscription) => {
                  const config = statusConfig[subscription.status];
                  const StatusIcon = config.icon;
                  const isActioning = actioningId === subscription.id;

                  return (
                    <tr key={subscription.id} className="group">
                      <td>
                        <Link
                          href={`/billing/subscriptions/${subscription.id}`}
                          className="hover:text-accent"
                        >
                          <p className="text-sm font-medium text-text-primary">
                            {subscription.customer?.name || "Unknown"}
                          </p>
                          <p className="text-xs text-text-muted">
                            {subscription.customer?.email || "—"}
                          </p>
                        </Link>
                      </td>
                      <td>
                        <p className="text-sm font-medium text-text-primary">
                          {subscription.plan?.name || "Unknown Plan"}
                        </p>
                        <p className="text-xs text-text-muted">
                          {subscription.plan?.interval === "month"
                            ? "Monthly"
                            : "Yearly"}
                        </p>
                      </td>
                      <td>
                        <span className="text-sm font-semibold tabular-nums">
                          {formatCurrency(subscription.plan?.price || 0)}
                        </span>
                        <span className="text-xs text-text-muted">
                          /{subscription.plan?.interval === "month" ? "mo" : "yr"}
                        </span>
                      </td>
                      <td>
                        <span className={cn("status-badge", config.class)}>
                          <StatusIcon className="w-3 h-3" />
                          {config.label}
                        </span>
                        {subscription.cancelAtPeriodEnd && (
                          <p className="text-xs text-status-warning mt-1">
                            Cancels at period end
                          </p>
                        )}
                      </td>
                      <td>
                        <div className="flex items-center gap-1 text-sm text-text-secondary">
                          <Calendar className="w-3 h-3" />
                          <span className="tabular-nums">
                            {formatDate(subscription.currentPeriodStart)} -{" "}
                            {formatDate(subscription.currentPeriodEnd)}
                          </span>
                        </div>
                      </td>
                      <td>
                        <span className="text-sm text-text-muted tabular-nums">
                          {formatDate(subscription.createdAt)}
                        </span>
                      </td>
                      <td>
                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          {isActioning ? (
                            <RefreshCw className="w-4 h-4 animate-spin text-text-muted" />
                          ) : (
                            <>
                              {subscription.status === "active" && (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handlePause(subscription.id)}
                                  aria-label={`Pause subscription for ${subscription.customer?.name || "this tenant"}`}
                                >
                                  <Pause className="w-3 h-3" aria-hidden="true" />
                                </Button>
                              )}
                              {subscription.status === "paused" && (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleResume(subscription.id)}
                                  aria-label={`Resume subscription for ${subscription.customer?.name || "this tenant"}`}
                                >
                                  <Play className="w-3 h-3" aria-hidden="true" />
                                </Button>
                              )}
                              {["active", "paused", "trialing"].includes(
                                subscription.status
                              ) && (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleCancel(subscription.id)}
                                  aria-label={`Cancel subscription for ${subscription.customer?.name || "this tenant"}`}
                                  className="text-status-error hover:text-status-error"
                                >
                                  <XCircle className="w-3 h-3" aria-hidden="true" />
                                </Button>
                              )}
                              <Link href={`/billing/subscriptions/${subscription.id}`}>
                                <Button variant="outline" size="sm">
                                  View
                                </Button>
                              </Link>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
