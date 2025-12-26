"use client";

import { use } from "react";
import Link from "next/link";
import {
  Package,
  ArrowLeft,
  Check,
  Star,
  Zap,
  Clock,
  CreditCard,
  ChevronRight,
} from "lucide-react";
import { Button, Card } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  useAddon,
  useActiveAddons,
  usePurchaseAddon,
} from "@/lib/hooks/api/use-billing";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function AddonDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const { toast } = useToast();
  const { data: addon, isLoading } = useAddon(id);
  const { data: activeAddons } = useActiveAddons();
  const purchaseAddon = usePurchaseAddon();

  const isOwned = activeAddons?.some(
    (a) => a.addonId === id && a.status === "active"
  );

  const handlePurchase = async () => {
    if (!addon) return;

    try {
      await purchaseAddon.mutateAsync(addon.id);
      toast({
        title: "Add-on purchased",
        description: `${addon.name} has been added to your account.`,
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to purchase add-on.",
        variant: "error",
      });
    }
  };

  if (isLoading) {
    return <AddonDetailSkeleton />;
  }

  if (!addon) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Add-on Not Found"
          breadcrumbs={[
            { label: "Billing", href: "/billing" },
            { label: "Add-ons", href: "/billing/addons" },
            { label: "Not Found" },
          ]}
        />
        <Card className="p-12 text-center">
          <Package className="w-12 h-12 mx-auto text-text-muted mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">Add-on not found</h3>
          <p className="text-text-muted mb-6">The add-on you&apos;re looking for doesn&apos;t exist</p>
          <Link href="/billing/addons">
            <Button>Back to Marketplace</Button>
          </Link>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title={addon.name}
        breadcrumbs={[
          { label: "Billing", href: "/billing" },
          { label: "Add-ons", href: "/billing/addons" },
          { label: addon.name },
        ]}
        actions={
          <Link href="/billing/addons">
            <Button variant="ghost">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Marketplace
            </Button>
          </Link>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Hero Section */}
          <Card className="p-6">
            <div className="flex items-start gap-4 mb-6">
              <div className="w-16 h-16 rounded-xl bg-accent-subtle flex items-center justify-center flex-shrink-0">
                {addon.icon ? (
                  <span className="text-4xl">{addon.icon}</span>
                ) : (
                  <Package className="w-8 h-8 text-accent" />
                )}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h1 className="text-2xl font-bold text-text-primary">{addon.name}</h1>
                  {addon.isFeatured && (
                    <span className="px-2 py-0.5 bg-status-warning/15 text-status-warning text-xs rounded-full flex items-center gap-1">
                      <Star className="w-3 h-3" />
                      Featured
                    </span>
                  )}
                  {addon.isPopular && (
                    <span className="px-2 py-0.5 bg-status-success/15 text-status-success text-xs rounded-full flex items-center gap-1">
                      <Zap className="w-3 h-3" />
                      Popular
                    </span>
                  )}
                </div>
                <p className="text-text-muted">{addon.description}</p>
              </div>
            </div>

            <div className="flex items-center gap-4 py-4 border-t border-border">
              <span className="text-sm text-text-muted">Category:</span>
              <span className="px-2 py-1 bg-surface-overlay text-text-primary text-sm rounded capitalize">
                {addon.category}
              </span>
            </div>
          </Card>

          {/* Features */}
          <Card className="p-6">
            <h2 className="text-lg font-semibold text-text-primary mb-4">Features</h2>
            <ul className="space-y-3">
              {addon.features.map((feature, index) => (
                <li key={index} className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-status-success flex-shrink-0 mt-0.5" />
                  <span className="text-text-primary">{feature}</span>
                </li>
              ))}
            </ul>
          </Card>

          {/* Limits */}
          {addon.limits && Object.keys(addon.limits).length > 0 && (
            <Card className="p-6">
              <h2 className="text-lg font-semibold text-text-primary mb-4">Usage Limits</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(addon.limits).map(([key, value]) => (
                  <div
                    key={key}
                    className="flex items-center justify-between p-3 bg-surface-overlay rounded-lg"
                  >
                    <span className="text-text-muted capitalize">{key.replace(/_/g, " ")}</span>
                    <span className="font-semibold text-text-primary">
                      {value.toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Pricing Card */}
          <Card className="p-6 sticky top-6">
            <div className="text-center mb-6">
              <div className="text-3xl font-bold text-text-primary">
                ${(addon.price / 100).toFixed(2)}
              </div>
              <div className="text-text-muted">
                {addon.billingCycle === "monthly" && "per month"}
                {addon.billingCycle === "yearly" && "per year"}
                {addon.billingCycle === "one_time" && "one-time payment"}
              </div>
            </div>

            {isOwned ? (
              <div className="space-y-3">
                <div className="p-3 bg-status-success/15 rounded-lg text-center">
                  <Check className="w-5 h-5 text-status-success mx-auto mb-1" />
                  <span className="text-sm font-medium text-status-success">
                    You own this add-on
                  </span>
                </div>
                <Link href="/billing/addons/active">
                  <Button variant="outline" className="w-full">
                    View My Add-ons
                    <ChevronRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
              </div>
            ) : (
              <Button
                onClick={handlePurchase}
                disabled={purchaseAddon.isPending}
                className="w-full shadow-glow-sm hover:shadow-glow"
              >
                {purchaseAddon.isPending ? (
                  "Processing..."
                ) : (
                  <>
                    <CreditCard className="w-4 h-4 mr-2" />
                    Purchase Now
                  </>
                )}
              </Button>
            )}

            <div className="mt-6 pt-6 border-t border-border space-y-3">
              <div className="flex items-center gap-2 text-sm text-text-muted">
                <Clock className="w-4 h-4" />
                <span>Instant activation</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-text-muted">
                <Check className="w-4 h-4" />
                <span>Cancel anytime</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-text-muted">
                <CreditCard className="w-4 h-4" />
                <span>Secure payment</span>
              </div>
            </div>
          </Card>

          {/* Related Add-ons */}
          <Card className="p-6">
            <h3 className="text-sm font-semibold text-text-primary mb-4">
              More in {addon.category}
            </h3>
            <div className="space-y-3">
              {/* Placeholder for related add-ons */}
              <p className="text-sm text-text-muted text-center py-4">
                Explore more add-ons in the marketplace
              </p>
              <Link href={`/billing/addons?category=${addon.category}`}>
                <Button variant="outline" size="sm" className="w-full">
                  Browse {addon.category}
                </Button>
              </Link>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

function AddonDetailSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center justify-between">
        <div>
          <div className="h-4 w-32 bg-surface-overlay rounded mb-2" />
          <div className="h-8 w-48 bg-surface-overlay rounded" />
        </div>
        <div className="h-10 w-40 bg-surface-overlay rounded" />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <div className="flex gap-4 mb-6">
              <div className="w-16 h-16 rounded-xl bg-surface-overlay" />
              <div className="flex-1">
                <div className="h-6 w-48 bg-surface-overlay rounded mb-2" />
                <div className="h-4 w-full bg-surface-overlay rounded" />
              </div>
            </div>
          </div>
          <div className="card p-6">
            <div className="h-48 bg-surface-overlay rounded" />
          </div>
        </div>
        <div className="card p-6">
          <div className="h-64 bg-surface-overlay rounded" />
        </div>
      </div>
    </div>
  );
}
