"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Plus,
  Search,
  Tag,
  Percent,
  DollarSign,
  Layers,
  TrendingUp,
  Play,
  Pause,
  Trash2,
  AlertTriangle,
  CheckCircle,
  Clock,
  Calculator,
} from "lucide-react";
import { format } from "date-fns";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  usePricingRules,
  usePricingConflicts,
  useActivatePricingRule,
  useDeactivatePricingRule,
  useDeletePricingRule,
  type PricingRule,
  type PricingRuleType,
  type PricingRuleStatus,
  type ListPricingRulesParams,
} from "@/lib/hooks/api/use-billing";

const typeConfig: Record<PricingRuleType, { icon: typeof Tag; label: string; color: string }> = {
  discount: { icon: Percent, label: "Discount", color: "text-status-success" },
  markup: { icon: TrendingUp, label: "Markup", color: "text-status-warning" },
  override: { icon: DollarSign, label: "Override", color: "text-accent" },
  bundle: { icon: Layers, label: "Bundle", color: "text-highlight" },
  volume: { icon: TrendingUp, label: "Volume", color: "text-status-info" },
  tiered: { icon: Layers, label: "Tiered", color: "text-accent" },
};

const statusConfig: Record<PricingRuleStatus, { label: string; class: string }> = {
  active: { label: "Active", class: "bg-status-success/15 text-status-success" },
  inactive: { label: "Inactive", class: "bg-surface-overlay text-text-muted" },
  scheduled: { label: "Scheduled", class: "bg-status-info/15 text-status-info" },
  expired: { label: "Expired", class: "bg-status-warning/15 text-status-warning" },
};

export default function PricingRulesPage() {
  const { toast } = useToast();
  const [filters, setFilters] = useState<ListPricingRulesParams>({
    page: 1,
    pageSize: 20,
  });
  const [searchTerm, setSearchTerm] = useState("");

  const { data: rulesData, isLoading } = usePricingRules(filters);
  const { data: conflicts } = usePricingConflicts();
  const activateRule = useActivatePricingRule();
  const deactivateRule = useDeactivatePricingRule();
  const deleteRule = useDeletePricingRule();

  const rules = rulesData?.items ?? [];
  const totalPages = rulesData?.totalPages ?? 1;
  const total = rulesData?.total ?? 0;
  const conflictCount = conflicts?.length ?? 0;

  const handleActivate = async (rule: PricingRule) => {
    try {
      await activateRule.mutateAsync(rule.id);
      toast({
        title: "Rule activated",
        description: `"${rule.name}" is now active.`,
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to activate rule.",
        variant: "error",
      });
    }
  };

  const handleDeactivate = async (rule: PricingRule) => {
    try {
      await deactivateRule.mutateAsync(rule.id);
      toast({
        title: "Rule deactivated",
        description: `"${rule.name}" has been deactivated.`,
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to deactivate rule.",
        variant: "error",
      });
    }
  };

  const handleDelete = async (rule: PricingRule) => {
    if (!confirm(`Are you sure you want to delete "${rule.name}"?`)) return;

    try {
      await deleteRule.mutateAsync(rule.id);
      toast({
        title: "Rule deleted",
        description: `"${rule.name}" has been deleted.`,
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to delete rule.",
        variant: "error",
      });
    }
  };

  const filteredRules = rules.filter((r) =>
    r.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (isLoading) {
    return <RulesPageSkeleton />;
  }

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="Pricing Rules"
        breadcrumbs={[
          { label: "Billing", href: "/billing" },
          { label: "Pricing" },
        ]}
        actions={
          <div className="flex items-center gap-3">
            <Link href="/billing/pricing/calculator">
              <Button variant="outline">
                <Calculator className="w-4 h-4 mr-2" />
                Price Calculator
              </Button>
            </Link>
            <Link href="/billing/pricing/new">
              <Button className="shadow-glow-sm hover:shadow-glow">
                <Plus className="w-4 h-4 mr-2" />
                New Rule
              </Button>
            </Link>
          </div>
        }
      />

      {/* Conflict Warning */}
      {conflictCount > 0 && (
        <Link href="/billing/pricing/conflicts">
          <Card className="p-4 bg-status-warning/15 border-status-warning/20 hover:bg-status-warning/15 transition-colors cursor-pointer">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-status-warning" />
              <div className="flex-1">
                <p className="text-sm font-medium text-status-warning">
                  {conflictCount} pricing conflict{conflictCount > 1 ? "s" : ""} detected
                </p>
                <p className="text-xs text-text-muted">
                  Click to review and resolve conflicting rules
                </p>
              </div>
            </div>
          </Card>
        </Link>
      )}

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <p className="text-sm text-text-muted">Total Rules</p>
          <p className="text-2xl font-bold text-text-primary">{total}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted">Active</p>
          <p className="text-2xl font-bold text-status-success">
            {rules.filter((r) => r.status === "active").length}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted">Scheduled</p>
          <p className="text-2xl font-bold text-status-info">
            {rules.filter((r) => r.status === "scheduled").length}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted">Conflicts</p>
          <p className={cn("text-2xl font-bold", conflictCount > 0 ? "text-status-warning" : "text-text-muted")}>
            {conflictCount}
          </p>
        </Card>
      </div>

      {/* Filter Bar */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
            <Input
              type="text"
              placeholder="Search rules..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <StatusFilterButton
              status={undefined}
              label="All"
              currentStatus={filters.status}
              onClick={() => setFilters((prev) => ({ ...prev, status: undefined, page: 1 }))}
            />
            <StatusFilterButton
              status="active"
              label="Active"
              currentStatus={filters.status}
              onClick={() => setFilters((prev) => ({ ...prev, status: "active", page: 1 }))}
            />
            <StatusFilterButton
              status="inactive"
              label="Inactive"
              currentStatus={filters.status}
              onClick={() => setFilters((prev) => ({ ...prev, status: "inactive", page: 1 }))}
            />
            <StatusFilterButton
              status="scheduled"
              label="Scheduled"
              currentStatus={filters.status}
              onClick={() => setFilters((prev) => ({ ...prev, status: "scheduled", page: 1 }))}
            />
          </div>
        </div>
      </Card>

      {/* Rules Table */}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          {filteredRules.length > 0 ? (
            <table className="data-table" aria-label="Pricing rules"><caption className="sr-only">Pricing rules</caption>
              <thead>
                <tr>
                  <th>Rule</th>
                  <th>Type</th>
                  <th>Discount/Value</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Usage</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filteredRules.map((rule) => (
                  <RuleRow
                    key={rule.id}
                    rule={rule}
                    onActivate={() => handleActivate(rule)}
                    onDeactivate={() => handleDeactivate(rule)}
                    onDelete={() => handleDelete(rule)}
                    isActivating={activateRule.isPending}
                    isDeactivating={deactivateRule.isPending}
                  />
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-12 text-center">
              <Tag className="w-12 h-12 mx-auto text-text-muted mb-4" />
              <h3 className="text-lg font-semibold text-text-primary mb-2">No pricing rules found</h3>
              <p className="text-text-muted mb-6">
                {filters.status || searchTerm
                  ? "Try adjusting your filters"
                  : "Create your first pricing rule to customize product pricing"}
              </p>
              {!filters.status && !searchTerm && (
                <Link href="/billing/pricing/new">
                  <Button className="shadow-glow-sm hover:shadow-glow">
                    <Plus className="w-4 h-4 mr-2" />
                    Create Rule
                  </Button>
                </Link>
              )}
            </div>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between p-4 border-t border-border">
            <p className="text-sm text-text-muted">
              Showing {rules.length} of {total} rules
            </p>
            <div className="flex items-center gap-2">
              {(filters.page ?? 1) > 1 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setFilters((prev) => ({ ...prev, page: (prev.page ?? 1) - 1 }))
                  }
                >
                  Previous
                </Button>
              )}
              <span className="text-sm text-text-secondary">
                Page {filters.page ?? 1} of {totalPages}
              </span>
              {(filters.page ?? 1) < totalPages && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setFilters((prev) => ({ ...prev, page: (prev.page ?? 1) + 1 }))
                  }
                >
                  Next
                </Button>
              )}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

function StatusFilterButton({
  status,
  label,
  currentStatus,
  onClick,
}: {
  status: PricingRuleStatus | undefined;
  label: string;
  currentStatus: PricingRuleStatus | undefined;
  onClick: () => void;
}) {
  const isActive = status === currentStatus;

  return (
    <Button
      variant={isActive ? "default" : "outline"}
      size="sm"
      onClick={onClick}
      className={cn(isActive && "shadow-glow-sm")}
    >
      {label}
    </Button>
  );
}

function RuleRow({
  rule,
  onActivate,
  onDeactivate,
  onDelete,
  isActivating,
  isDeactivating,
}: {
  rule: PricingRule;
  onActivate: () => void;
  onDeactivate: () => void;
  onDelete: () => void;
  isActivating: boolean;
  isDeactivating: boolean;
}) {
  const typeInfo = typeConfig[rule.type];
  const statusInfo = statusConfig[rule.status];
  const TypeIcon = typeInfo.icon;

  const getDiscountDisplay = () => {
    if (rule.discountType === "percentage" && rule.discountValue) {
      return `${rule.discountValue}%`;
    }
    if (rule.discountType === "fixed_amount" && rule.discountValue) {
      return `$${(rule.discountValue / 100).toFixed(2)}`;
    }
    if (rule.overridePrice !== undefined) {
      return `$${(rule.overridePrice / 100).toFixed(2)}`;
    }
    if (rule.volumeTiers && rule.volumeTiers.length > 0) {
      return `${rule.volumeTiers.length} tiers`;
    }
    return "—";
  };

  return (
    <tr className="group">
      <td>
        <div>
          <Link
            href={`/billing/pricing/${rule.id}`}
            className="font-medium text-text-primary hover:text-accent"
          >
            {rule.name}
          </Link>
          {rule.description && (
            <p className="text-xs text-text-muted truncate max-w-xs">{rule.description}</p>
          )}
        </div>
      </td>
      <td>
        <div className="flex items-center gap-2">
          <TypeIcon className={cn("w-4 h-4", typeInfo.color)} />
          <span className="text-sm text-text-primary">{typeInfo.label}</span>
        </div>
      </td>
      <td>
        <span className="text-sm font-medium text-text-primary">{getDiscountDisplay()}</span>
      </td>
      <td>
        <span className="text-sm text-text-muted">{rule.priority}</span>
      </td>
      <td>
        <span className={cn("status-badge", statusInfo.class)}>{statusInfo.label}</span>
      </td>
      <td>
        <div className="text-sm">
          <span className="text-text-primary">{rule.usageCount}</span>
          {rule.usageLimit && (
            <span className="text-text-muted">/{rule.usageLimit}</span>
          )}
        </div>
      </td>
      <td>
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          {rule.status === "active" ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={onDeactivate}
              disabled={isDeactivating}
              title="Deactivate rule"
            >
              <Pause className="w-4 h-4" />
            </Button>
          ) : rule.status !== "expired" ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={onActivate}
              disabled={isActivating}
              title="Activate rule"
            >
              <Play className="w-4 h-4" />
            </Button>
          ) : null}
          <Button
            variant="ghost"
            size="sm"
            onClick={onDelete}
            title="Delete rule"
            className="text-status-error hover:text-status-error"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </td>
    </tr>
  );
}

function RulesPageSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center justify-between">
        <div>
          <div className="h-4 w-32 bg-surface-overlay rounded mb-2" />
          <div className="h-8 w-48 bg-surface-overlay rounded" />
        </div>
        <div className="flex gap-3">
          <div className="h-10 w-32 bg-surface-overlay rounded" />
          <div className="h-10 w-24 bg-surface-overlay rounded" />
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card p-4">
            <div className="h-4 w-20 bg-surface-overlay rounded mb-2" />
            <div className="h-8 w-16 bg-surface-overlay rounded" />
          </div>
        ))}
      </div>

      <div className="card p-4">
        <div className="flex gap-4">
          <div className="flex-1 h-10 bg-surface-overlay rounded" />
          <div className="h-10 w-48 bg-surface-overlay rounded" />
        </div>
      </div>

      <div className="card overflow-hidden">
        <div className="p-4 space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-16 bg-surface-overlay rounded" />
          ))}
        </div>
      </div>
    </div>
  );
}
