"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  CreditCard,
  Calendar,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Pause,
  Play,
  RefreshCw,
  ArrowUpRight,
  User,
  Mail,
  Building,
} from "lucide-react";
import { Button, useToast } from "@/lib/dotmac/core";
import { cn } from "@/lib/utils";
import {
  useSubscription,
  usePauseSubscription,
  useResumeSubscription,
  useCancelSubscription,
  useChangePlan,
  useProrationPreview,
} from "@/lib/hooks/api/use-billing";
import type { SubscriptionStatus } from "@/types/models";

interface Plan {
  id: string;
  name: string;
  price: number;
  interval: "month" | "year";
  features: string[];
}

// Mock available plans for plan change
const availablePlans: Plan[] = [
  {
    id: "plan_basic",
    name: "Basic",
    price: 2900,
    interval: "month",
    features: ["5 team members", "10GB storage", "Email support"],
  },
  {
    id: "plan_pro",
    name: "Professional",
    price: 7900,
    interval: "month",
    features: ["25 team members", "100GB storage", "Priority support", "API access"],
  },
  {
    id: "plan_enterprise",
    name: "Enterprise",
    price: 19900,
    interval: "month",
    features: ["Unlimited team members", "Unlimited storage", "24/7 support", "API access", "Custom integrations"],
  },
];

export default function SubscriptionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const subscriptionId = params.id as string;

  const { data: subscription, isLoading } = useSubscription(subscriptionId);
  const pauseSubscription = usePauseSubscription();
  const resumeSubscription = useResumeSubscription();
  const cancelSubscription = useCancelSubscription();
  const changePlan = useChangePlan();
  const prorationPreview = useProrationPreview();

  const [showChangePlanModal, setShowChangePlanModal] = useState(false);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);
  const [cancelAtPeriodEnd, setCancelAtPeriodEnd] = useState(true);
  const [isActioning, setIsActioning] = useState(false);

  // Get proration preview when plan is selected
  useEffect(() => {
    if (selectedPlanId && subscriptionId) {
      prorationPreview.mutate({ id: subscriptionId, newPlanId: selectedPlanId });
    }
  }, [prorationPreview, selectedPlanId, subscriptionId]);

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
      month: "long",
      day: "numeric",
    });
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount / 100);
  };

  const handlePause = async () => {
    setIsActioning(true);
    try {
      await pauseSubscription.mutateAsync(subscriptionId);
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
      setIsActioning(false);
    }
  };

  const handleResume = async () => {
    setIsActioning(true);
    try {
      await resumeSubscription.mutateAsync(subscriptionId);
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
      setIsActioning(false);
    }
  };

  const handleCancel = async () => {
    setIsActioning(true);
    try {
      await cancelSubscription.mutateAsync(subscriptionId);
      toast({
        title: "Subscription cancelled",
        description: cancelAtPeriodEnd
          ? "The subscription will be cancelled at the end of the current period."
          : "The subscription has been cancelled immediately.",
        variant: "success",
      });
      setShowCancelModal(false);
    } catch {
      toast({
        title: "Error",
        description: "Failed to cancel subscription.",
        variant: "error",
      });
    } finally {
      setIsActioning(false);
    }
  };

  const handleChangePlan = async () => {
    if (!selectedPlanId) return;

    setIsActioning(true);
    try {
      await changePlan.mutateAsync({ id: subscriptionId, newPlanId: selectedPlanId });
      toast({
        title: "Plan changed",
        description: "The subscription plan has been updated.",
        variant: "success",
      });
      setShowChangePlanModal(false);
      setSelectedPlanId(null);
    } catch {
      toast({
        title: "Error",
        description: "Failed to change plan.",
        variant: "error",
      });
    } finally {
      setIsActioning(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <RefreshCw className="w-8 h-8 animate-spin text-text-muted" />
      </div>
    );
  }

  if (!subscription) {
    return (
      <div className="text-center py-12">
        <CreditCard className="w-12 h-12 mx-auto text-text-muted mb-4" />
        <h2 className="text-lg font-semibold text-text-primary mb-2">
          Subscription not found
        </h2>
        <p className="text-text-muted mb-4">
          The subscription you&apos;re looking for doesn&apos;t exist.
        </p>
        <Link href="/billing/subscriptions">
          <Button variant="outline">Back to Subscriptions</Button>
        </Link>
      </div>
    );
  }

  const config = statusConfig[subscription.status];
  const StatusIcon = config.icon;
  const currentPlan = subscription.plan;

  return (
    <div className="space-y-6">
      {/* Breadcrumbs */}
      <div className="flex items-center gap-2 text-sm text-text-muted">
        <Link href="/billing" className="hover:text-text-secondary">
          Billing
        </Link>
        <span>/</span>
        <Link href="/billing/subscriptions" className="hover:text-text-secondary">
          Subscriptions
        </Link>
        <span>/</span>
        <span className="text-text-primary">{subscription.id.slice(0, 8)}...</span>
      </div>

      {/* Page Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <Link
            href="/billing/subscriptions"
            className="p-2 rounded-lg hover:bg-surface-hover transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-text-muted" />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-semibold text-text-primary">
                {currentPlan?.name || "Subscription"}
              </h1>
              <span className={cn("status-badge", config.class)}>
                <StatusIcon className="w-3 h-3" />
                {config.label}
              </span>
            </div>
            <p className="text-text-muted mt-1">
              {subscription.customer?.name || "Customer"} • {formatCurrency(currentPlan?.price || 0)}/
              {currentPlan?.interval === "month" ? "month" : "year"}
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {subscription.status === "active" && (
            <>
              <Button
                variant="outline"
                onClick={() => setShowChangePlanModal(true)}
              >
                <ArrowUpRight className="w-4 h-4 mr-2" />
                Change Plan
              </Button>
              <Button
                variant="outline"
                onClick={handlePause}
                disabled={isActioning}
              >
                <Pause className="w-4 h-4 mr-2" />
                Pause
              </Button>
            </>
          )}
          {subscription.status === "paused" && (
            <Button
              variant="outline"
              onClick={handleResume}
              disabled={isActioning}
            >
              <Play className="w-4 h-4 mr-2" />
              Resume
            </Button>
          )}
          {["active", "paused", "trialing"].includes(subscription.status) && (
            <Button
              variant="destructive"
              onClick={() => setShowCancelModal(true)}
              disabled={isActioning}
            >
              <XCircle className="w-4 h-4 mr-2" />
              Cancel
            </Button>
          )}
        </div>
      </div>

      {/* Alert for cancellation pending */}
      {subscription.cancelAtPeriodEnd && (
        <div className="flex items-start gap-3 p-4 bg-status-warning/10 border border-status-warning/30 rounded-lg">
          <AlertCircle className="w-5 h-5 text-status-warning flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-text-primary">Cancellation scheduled</p>
            <p className="text-sm text-text-muted">
              This subscription will be cancelled at the end of the current billing period on{" "}
              {formatDate(subscription.currentPeriodEnd)}.
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Plan Details */}
          <div className="card">
            <div className="p-4 border-b border-border">
              <h2 className="text-sm font-semibold text-text-primary">
                Plan Details
              </h2>
            </div>
            <div className="p-4 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-text-muted">Plan name</span>
                <span className="font-medium text-text-primary">
                  {currentPlan?.name || "—"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-muted">Price</span>
                <span className="font-semibold text-text-primary tabular-nums">
                  {formatCurrency(currentPlan?.price || 0)}
                  <span className="text-text-muted font-normal">
                    /{currentPlan?.interval === "month" ? "month" : "year"}
                  </span>
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-muted">Billing cycle</span>
                <span className="text-text-primary">
                  {currentPlan?.interval === "month" ? "Monthly" : "Annual"}
                </span>
              </div>
              {currentPlan?.features && currentPlan.features.length > 0 && (
                <div className="pt-4 border-t border-border">
                  <p className="text-sm font-medium text-text-secondary mb-3">
                    Included features
                  </p>
                  <ul className="space-y-2">
                    {currentPlan.features.map((feature, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-sm text-text-muted">
                        <CheckCircle className="w-4 h-4 text-status-success" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* Billing Period */}
          <div className="card">
            <div className="p-4 border-b border-border">
              <h2 className="text-sm font-semibold text-text-primary">
                Billing Period
              </h2>
            </div>
            <div className="p-4 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-text-muted">Current period</span>
                <span className="text-text-primary flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  {formatDate(subscription.currentPeriodStart)} – {formatDate(subscription.currentPeriodEnd)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-muted">Next billing date</span>
                <span className="text-text-primary">
                  {subscription.cancelAtPeriodEnd
                    ? "—"
                    : formatDate(subscription.currentPeriodEnd)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-muted">Started on</span>
                <span className="text-text-primary">
                  {formatDate(subscription.createdAt)}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Customer Info */}
          <div className="card">
            <div className="p-4 border-b border-border">
              <h2 className="text-sm font-semibold text-text-primary">
                Customer
              </h2>
            </div>
            <div className="p-4 space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-accent-subtle flex items-center justify-center">
                  <User className="w-5 h-5 text-accent" />
                </div>
                <div>
                  <p className="font-medium text-text-primary">
                    {subscription.customer?.name || "Unknown"}
                  </p>
                  <p className="text-xs text-text-muted">Customer</p>
                </div>
              </div>
              {subscription.customer?.email && (
                <div className="flex items-center gap-2 text-sm text-text-muted">
                  <Mail className="w-4 h-4" />
                  {subscription.customer.email}
                </div>
              )}
              {subscription.customer?.company && (
                <div className="flex items-center gap-2 text-sm text-text-muted">
                  <Building className="w-4 h-4" />
                  {subscription.customer.company}
                </div>
              )}
              <Link
                href={`/customers/${subscription.customerId}`}
                className="block text-sm text-accent hover:underline mt-2"
              >
                View customer profile →
              </Link>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="card">
            <div className="p-4 border-b border-border">
              <h2 className="text-sm font-semibold text-text-primary">
                Quick Stats
              </h2>
            </div>
            <div className="p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-text-muted">Total paid</span>
                <span className="text-sm font-semibold text-text-primary tabular-nums">
                  {formatCurrency((currentPlan?.price || 0) * 3)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-text-muted">Invoices</span>
                <Link
                  href={`/billing/invoices?customerId=${subscription.customerId}`}
                  className="text-sm text-accent hover:underline"
                >
                  View all →
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Change Plan Modal */}
      {showChangePlanModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => {
              setShowChangePlanModal(false);
              setSelectedPlanId(null);
            }}
          />
          <div className="relative w-full max-w-2xl mx-4 bg-surface border border-border rounded-xl shadow-2xl">
            <div className="flex items-center justify-between p-4 border-b border-border">
              <h2 className="text-lg font-semibold text-text-primary">
                Change Plan
              </h2>
              <button
                onClick={() => {
                  setShowChangePlanModal(false);
                  setSelectedPlanId(null);
                }}
                className="p-2 rounded-lg hover:bg-surface-hover transition-colors"
              >
                <XCircle className="w-5 h-5 text-text-muted" />
              </button>
            </div>

            <div className="p-4 space-y-4">
              <p className="text-sm text-text-muted">
                Select a new plan for this subscription. Any price difference will be prorated.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {availablePlans.map((plan) => (
                  <button
                    key={plan.id}
                    onClick={() => setSelectedPlanId(plan.id)}
                    className={cn(
                      "p-4 rounded-lg border text-left transition-all",
                      selectedPlanId === plan.id
                        ? "border-accent bg-accent-subtle"
                        : "border-border hover:border-accent/50",
                      currentPlan?.name === plan.name && "opacity-50"
                    )}
                    disabled={currentPlan?.name === plan.name}
                  >
                    <p className="font-semibold text-text-primary">{plan.name}</p>
                    <p className="text-2xl font-bold text-text-primary mt-2">
                      {formatCurrency(plan.price)}
                      <span className="text-sm font-normal text-text-muted">/mo</span>
                    </p>
                    <ul className="mt-3 space-y-1">
                      {plan.features.slice(0, 3).map((feature, idx) => (
                        <li key={idx} className="text-xs text-text-muted flex items-center gap-1">
                          <CheckCircle className="w-3 h-3 text-status-success" />
                          {feature}
                        </li>
                      ))}
                    </ul>
                    {currentPlan?.name === plan.name && (
                      <p className="text-xs text-accent mt-2">Current plan</p>
                    )}
                  </button>
                ))}
              </div>

              {/* Proration Preview */}
              {selectedPlanId && prorationPreview.data && (
                <div className="p-4 bg-surface-overlay rounded-lg">
                  <p className="text-sm font-medium text-text-primary mb-2">
                    Proration Preview
                  </p>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between text-text-muted">
                      <span>Current plan credit</span>
                      <span className="text-status-success">
                        -{formatCurrency(Math.abs(prorationPreview.data.proratedAmount))}
                      </span>
                    </div>
                    <div className="flex justify-between text-text-muted">
                      <span>New plan charge</span>
                      <span>{formatCurrency(prorationPreview.data.newPlan.price)}</span>
                    </div>
                    <div className="flex justify-between font-medium text-text-primary pt-2 border-t border-border">
                      <span>Amount due today</span>
                      <span>
                        {formatCurrency(prorationPreview.data.newPlan.price - Math.abs(prorationPreview.data.proratedAmount))}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="flex items-center justify-end gap-3 p-4 border-t border-border">
              <Button
                variant="outline"
                onClick={() => {
                  setShowChangePlanModal(false);
                  setSelectedPlanId(null);
                }}
              >
                Cancel
              </Button>
              <Button
                onClick={handleChangePlan}
                disabled={!selectedPlanId || isActioning}
                className="shadow-glow-sm"
              >
                {isActioning ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Changing...
                  </>
                ) : (
                  "Confirm Change"
                )}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Cancel Modal */}
      {showCancelModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setShowCancelModal(false)}
          />
          <div className="relative w-full max-w-md mx-4 bg-surface border border-border rounded-xl shadow-2xl">
            <div className="flex items-center justify-between p-4 border-b border-border">
              <h2 className="text-lg font-semibold text-text-primary">
                Cancel Subscription
              </h2>
              <button
                onClick={() => setShowCancelModal(false)}
                className="p-2 rounded-lg hover:bg-surface-hover transition-colors"
              >
                <XCircle className="w-5 h-5 text-text-muted" />
              </button>
            </div>

            <div className="p-4 space-y-4">
              <div className="flex items-start gap-3 p-3 bg-status-error/10 border border-status-error/30 rounded-lg">
                <AlertCircle className="w-5 h-5 text-status-error flex-shrink-0 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-text-primary">
                    Are you sure you want to cancel?
                  </p>
                  <p className="text-text-muted mt-1">
                    The customer will lose access to their subscription benefits.
                  </p>
                </div>
              </div>

              <div className="space-y-3">
                <label className="flex items-start gap-3 p-3 rounded-lg border border-border cursor-pointer hover:border-accent/50">
                  <input
                    type="radio"
                    name="cancelOption"
                    checked={cancelAtPeriodEnd}
                    onChange={() => setCancelAtPeriodEnd(true)}
                    className="mt-1"
                  />
                  <div>
                    <p className="text-sm font-medium text-text-primary">
                      Cancel at end of period
                    </p>
                    <p className="text-xs text-text-muted">
                      Customer keeps access until {formatDate(subscription.currentPeriodEnd)}
                    </p>
                  </div>
                </label>
                <label className="flex items-start gap-3 p-3 rounded-lg border border-border cursor-pointer hover:border-accent/50">
                  <input
                    type="radio"
                    name="cancelOption"
                    checked={!cancelAtPeriodEnd}
                    onChange={() => setCancelAtPeriodEnd(false)}
                    className="mt-1"
                  />
                  <div>
                    <p className="text-sm font-medium text-text-primary">
                      Cancel immediately
                    </p>
                    <p className="text-xs text-text-muted">
                      Access ends immediately, no refund issued
                    </p>
                  </div>
                </label>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 p-4 border-t border-border">
              <Button variant="outline" onClick={() => setShowCancelModal(false)}>
                Keep Subscription
              </Button>
              <Button
                variant="destructive"
                onClick={handleCancel}
                disabled={isActioning}
              >
                {isActioning ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Cancelling...
                  </>
                ) : (
                  "Cancel Subscription"
                )}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
