"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Package,
  Search,
  Star,
  Zap,
  ChevronRight,
  Grid3X3,
  List,
} from "lucide-react";
import { Button, Card, Input, Select } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  useAddonsMarketplace,
  type Addon,
} from "@/lib/hooks/api/use-billing";

const categoryOptions = [
  { value: "", label: "All Categories" },
  { value: "analytics", label: "Analytics" },
  { value: "automation", label: "Automation" },
  { value: "integrations", label: "Integrations" },
  { value: "security", label: "Security" },
  { value: "support", label: "Support" },
  { value: "storage", label: "Storage" },
];

export default function AddonsMarketplacePage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useAddonsMarketplace({
    page,
    pageSize: 12,
    category: category || undefined,
  });

  const filteredAddons = data?.items.filter((addon) =>
    addon.name.toLowerCase().includes(search.toLowerCase()) ||
    addon.description.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="Add-ons Marketplace"
        breadcrumbs={[
          { label: "Billing", href: "/billing" },
          { label: "Add-ons" },
        ]}
        actions={
          <Link href="/billing/addons/active">
            <Button variant="outline">
              <Package className="w-4 h-4 mr-2" />
              My Add-ons
            </Button>
          </Link>
        }
      />

      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search add-ons..."
              className="pl-10"
            />
          </div>
          <div className="flex gap-3">
            <Select
              value={category}
              onValueChange={(value) => {
                setCategory(value);
                setPage(1);
              }}
              options={categoryOptions}
              placeholder="All Categories"
              className="w-48"
            />
            <div className="flex border border-border rounded-lg overflow-hidden">
              <button
                onClick={() => setViewMode("grid")}
                className={cn(
                  "p-2 transition-colors",
                  viewMode === "grid"
                    ? "bg-accent text-text-inverse"
                    : "bg-transparent text-text-muted hover:text-text-primary"
                )}
              >
                <Grid3X3 className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode("list")}
                className={cn(
                  "p-2 transition-colors",
                  viewMode === "list"
                    ? "bg-accent text-text-inverse"
                    : "bg-transparent text-text-muted hover:text-text-primary"
                )}
              >
                <List className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </Card>

      {/* Add-ons Grid/List */}
      {isLoading ? (
        <AddonsSkeleton viewMode={viewMode} />
      ) : filteredAddons && filteredAddons.length > 0 ? (
        viewMode === "grid" ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredAddons.map((addon) => (
              <AddonCard key={addon.id} addon={addon} />
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {filteredAddons.map((addon) => (
              <AddonListItem key={addon.id} addon={addon} />
            ))}
          </div>
        )
      ) : (
        <Card className="p-12 text-center">
          <Package className="w-12 h-12 mx-auto text-text-muted mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">No add-ons found</h3>
          <p className="text-text-muted">
            {search ? "Try adjusting your search or filters" : "No add-ons available in this category"}
          </p>
        </Card>
      )}

      {/* Pagination */}
      {data && data.totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </Button>
          <span className="text-sm text-text-muted">
            Page {page} of {data.totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page === data.totalPages}
            onClick={() => setPage(page + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}

function AddonCard({ addon }: { addon: Addon }) {
  return (
    <Link href={`/billing/addons/${addon.id}`}>
      <Card className="p-6 hover:border-accent transition-colors h-full flex flex-col">
        <div className="flex items-start justify-between mb-4">
          <div className="w-12 h-12 rounded-lg bg-accent-subtle flex items-center justify-center">
            {addon.icon ? (
              <span className="text-2xl">{addon.icon}</span>
            ) : (
              <Package className="w-6 h-6 text-accent" />
            )}
          </div>
          <div className="flex gap-1">
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
        </div>

        <h3 className="text-lg font-semibold text-text-primary mb-2">{addon.name}</h3>
        <p className="text-sm text-text-muted mb-4 flex-1 line-clamp-2">{addon.description}</p>

        <div className="flex items-center justify-between pt-4 border-t border-border">
          <div>
            <span className="text-xl font-bold text-text-primary">
              ${(addon.price / 100).toFixed(2)}
            </span>
            <span className="text-sm text-text-muted">
              {addon.billingCycle === "monthly" && "/mo"}
              {addon.billingCycle === "yearly" && "/yr"}
              {addon.billingCycle === "one_time" && " one-time"}
            </span>
          </div>
          <ChevronRight className="w-5 h-5 text-text-muted" />
        </div>
      </Card>
    </Link>
  );
}

function AddonListItem({ addon }: { addon: Addon }) {
  return (
    <Link href={`/billing/addons/${addon.id}`}>
      <Card className="p-4 hover:border-accent transition-colors">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-lg bg-accent-subtle flex items-center justify-center flex-shrink-0">
            {addon.icon ? (
              <span className="text-2xl">{addon.icon}</span>
            ) : (
              <Package className="w-6 h-6 text-accent" />
            )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-semibold text-text-primary">{addon.name}</h3>
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
            <p className="text-sm text-text-muted truncate">{addon.description}</p>
          </div>

          <div className="text-right flex-shrink-0">
            <span className="text-lg font-bold text-text-primary">
              ${(addon.price / 100).toFixed(2)}
            </span>
            <span className="text-sm text-text-muted block">
              {addon.billingCycle === "monthly" && "/month"}
              {addon.billingCycle === "yearly" && "/year"}
              {addon.billingCycle === "one_time" && "one-time"}
            </span>
          </div>

          <ChevronRight className="w-5 h-5 text-text-muted flex-shrink-0" />
        </div>
      </Card>
    </Link>
  );
}

function AddonsSkeleton({ viewMode }: { viewMode: "grid" | "list" }) {
  if (viewMode === "grid") {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="card p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="w-12 h-12 rounded-lg bg-surface-overlay" />
              <div className="h-5 w-16 bg-surface-overlay rounded-full" />
            </div>
            <div className="h-5 w-32 bg-surface-overlay rounded mb-2" />
            <div className="h-4 w-full bg-surface-overlay rounded mb-4" />
            <div className="pt-4 border-t border-border">
              <div className="h-6 w-20 bg-surface-overlay rounded" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4 animate-pulse">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="card p-4 flex items-center gap-4">
          <div className="w-12 h-12 rounded-lg bg-surface-overlay" />
          <div className="flex-1">
            <div className="h-5 w-32 bg-surface-overlay rounded mb-2" />
            <div className="h-4 w-48 bg-surface-overlay rounded" />
          </div>
          <div className="h-6 w-20 bg-surface-overlay rounded" />
        </div>
      ))}
    </div>
  );
}
