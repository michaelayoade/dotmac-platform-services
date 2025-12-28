"use client";

import { useState } from "react";
import {
  CreditCard,
  Download,
  Calendar,
  CheckCircle,
  AlertCircle,
  Zap,
  ArrowUpRight,
} from "lucide-react";
import { useToast } from "@dotmac/core";

import { PageHeader, StatusBadge, EmptyState } from "@/components/shared";
import {
  useTenantBilling,
  useTenantInvoices,
  useDownloadInvoice,
} from "@/lib/hooks/api/use-tenant-portal";
import { cn } from "@/lib/utils";
import type { CurrentSubscription } from "@/types/tenant-portal";

const statusColors: Record<CurrentSubscription["status"], "success" | "error" | "info"> = {
  ACTIVE: "success",
  CANCELLED: "error",
  PAST_DUE: "error",
  TRIALING: "info",
};

const invoiceStatusColors = {
  DRAFT: "pending",
  OPEN: "warning",
  PAID: "success",
  VOID: "error",
  UNCOLLECTIBLE: "error",
} as const;


const planFeatures: Record<CurrentSubscription["planType"], string[]> = {
  PROFESSIONAL: [
    "Up to 10 team members",
    "100,000 API calls/month",
    "5 GB storage",
    "Priority support",
    "Advanced analytics",
    "Custom integrations",
  ],
  STARTER: [
    "Up to 3 team members",
    "25,000 API calls/month",
    "1 GB storage",
    "Email support",
    "Basic analytics",
  ],
  FREE: [
    "1 team member",
    "5,000 API calls/month",
    "500 MB storage",
    "Community support",
  ],
  ENTERPRISE: [
    "Unlimited team members",
    "Custom API limits",
    "Dedicated infrastructure",
    "Enterprise support",
    "Custom analytics",
    "SLA-backed uptime",
  ],
};

function BillingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="bg-surface-elevated rounded-lg border border-border p-6 h-40" />
      <div className="bg-surface-elevated rounded-lg border border-border p-6 h-64" />
    </div>
  );
}

export default function BillingPage() {
  const { data: billingData, isLoading } = useTenantBilling();
  const downloadInvoice = useDownloadInvoice();
  const { toast } = useToast();
  const billing = billingData ?? null;

  const handleChangePlan = () => {
    toast({
      title: "Change Plan",
      description: "Please contact support to change your subscription plan.",
      variant: "info",
    });
  };

  const handleUpgrade = () => {
    toast({
      title: "Upgrade Plan",
      description: "Please contact support to upgrade your subscription.",
      variant: "info",
    });
  };

  const handleAddPaymentMethod = () => {
    toast({
      title: "Coming Soon",
      description: "Payment method management will be available in a future update.",
      variant: "info",
    });
  };

  const handleEditPaymentMethod = (methodId: string) => {
    toast({
      title: "Coming Soon",
      description: "Payment method editing will be available in a future update.",
      variant: "info",
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const formatCurrency = (amount: number) => {
    return `$${(amount / 100).toFixed(2)}`;
  };

  const handleDownloadInvoice = async (id: string) => {
    try {
      const blob = await downloadInvoice.mutateAsync(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `invoice-${id}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Failed to download invoice:", error);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Billing"
          description="Manage your subscription and payment methods"
        />
        <BillingSkeleton />
      </div>
    );
  }

  if (!billing) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Billing"
          description="Manage your subscription and payment methods"
        />
        <EmptyState
          icon={CreditCard}
          title="No billing data available"
          description="Connect a payment method to view subscription details and invoices."
        />
      </div>
    );
  }

  const { subscription, invoices, paymentMethods, upcomingInvoice } = billing;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Billing"
        description="Manage your subscription and payment methods"
      />

      {/* Current Plan */}
      <div className="bg-gradient-to-r from-accent/10 to-highlight/10 rounded-lg border border-accent/20 p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-lg bg-accent/20 text-accent">
              <Zap className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-3 mb-1">
                <h2 className="text-xl font-semibold text-text-primary">
                  {subscription.planName} Plan
                </h2>
                <StatusBadge status={statusColors[subscription.status]} label={subscription.status} />
              </div>
              <p className="text-text-muted">
                ${subscription.monthlyPrice}/month •{" "}
                {subscription.billingInterval === "monthly" ? "Monthly" : "Yearly"} billing
              </p>
              <p className="text-sm text-text-muted mt-1">
                Current period: {formatDate(subscription.currentPeriodStart)} -{" "}
                {formatDate(subscription.currentPeriodEnd)}
              </p>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleChangePlan}
              className="px-4 py-2 rounded-md border border-border text-text-secondary hover:text-text-primary hover:bg-surface-overlay transition-colors"
            >
              Change Plan
            </button>
            <button
              onClick={handleUpgrade}
              className="px-4 py-2 rounded-md bg-accent text-text-inverse hover:bg-accent-hover transition-colors"
            >
              Upgrade
            </button>
          </div>
        </div>

        {/* Plan Features */}
        <div className="mt-6 pt-6 border-t border-accent/20">
          <h3 className="text-sm font-semibold text-text-primary mb-3">
            Plan Features
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {planFeatures[subscription.planType].map((feature, i) => (
              <div
                key={i}
                className="flex items-center gap-2 text-sm text-text-secondary"
              >
                <CheckCircle className="w-4 h-4 text-status-success flex-shrink-0" />
                <span>{feature}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Upcoming Invoice */}
      {upcomingInvoice && (
        <div className="bg-surface-elevated rounded-lg border border-border p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-2 rounded-lg bg-status-warning/15 text-status-warning">
                <Calendar className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-text-primary">
                  Next Invoice
                </h3>
                <p className="text-sm text-text-muted">
                  Due {formatDate(upcomingInvoice.dueDate)}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xl font-semibold text-text-primary">
                {formatCurrency(upcomingInvoice.amountDue)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Payment Methods */}
      <div className="bg-surface-elevated rounded-lg border border-border">
        <div className="p-6 border-b border-border flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-text-primary">Payment Methods</h3>
            <p className="text-sm text-text-muted">
              Manage your payment options
            </p>
          </div>
          <button
            onClick={handleAddPaymentMethod}
            className="text-sm text-accent hover:text-accent-hover"
          >
            Add Payment Method
          </button>
        </div>

        <div className="divide-y divide-border">
          {paymentMethods.map((method) => (
            <div
              key={method.id}
              className="p-6 flex items-center justify-between"
            >
              <div className="flex items-center gap-4">
                <div className="p-2 rounded-lg bg-surface-overlay">
                  <CreditCard className="w-5 h-5 text-text-muted" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-text-primary">
                      {method.card?.brand} •••• {method.card?.last4}
                    </p>
                    {method.isDefault && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-accent/15 text-accent">
                        Default
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-text-muted">
                    Expires {method.card?.expMonth}/{method.card?.expYear}
                  </p>
                </div>
              </div>
              <button
                onClick={() => handleEditPaymentMethod(method.id)}
                className="text-sm text-text-muted hover:text-text-secondary"
              >
                Edit
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Invoice History */}
      <div className="bg-surface-elevated rounded-lg border border-border">
        <div className="p-6 border-b border-border">
          <h3 className="font-semibold text-text-primary">Invoice History</h3>
          <p className="text-sm text-text-muted">View and download past invoices</p>
        </div>

        {invoices.length === 0 ? (
          <div className="p-12">
            <EmptyState
              icon={CreditCard}
              title="No invoices yet"
              description="Your invoices will appear here"
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table" aria-label="Invoice history"><caption className="sr-only">Invoice history</caption>
              <thead>
                <tr className="border-b border-border bg-surface-overlay/50">
                  <th className="px-6 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Invoice
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((invoice) => (
                  <tr
                    key={invoice.id}
                    className="border-b border-border hover:bg-surface-overlay/50 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <span className="font-medium text-text-primary">
                        {invoice.number}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-text-secondary">
                      {formatDate(invoice.createdAt)}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={invoiceStatusColors[invoice.status]} label={invoice.status} />
                    </td>
                    <td className="px-6 py-4 text-right font-medium text-text-primary">
                      {formatCurrency(invoice.amountDue)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => handleDownloadInvoice(invoice.id)}
                        disabled={downloadInvoice.isPending}
                        className="inline-flex items-center gap-1 text-sm text-accent hover:text-accent-hover disabled:opacity-50"
                      >
                        <Download className="w-4 h-4" />
                        Download
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
