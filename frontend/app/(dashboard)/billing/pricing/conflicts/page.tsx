"use client";

import Link from "next/link";
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle,
  AlertCircle,
  Info,
  ChevronRight,
  Shield,
} from "lucide-react";
import { Button, Card } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  usePricingConflicts,
  useResolvePricingConflict,
  type PricingConflict,
} from "@/lib/hooks/api/use-billing";

const severityConfig = {
  low: { icon: Info, label: "Low", class: "bg-status-info/15 text-status-info" },
  medium: { icon: AlertCircle, label: "Medium", class: "bg-status-warning/15 text-status-warning" },
  high: { icon: AlertTriangle, label: "High", class: "bg-status-error/15 text-status-error" },
};

const conflictTypeLabels = {
  overlap: "Overlapping Rules",
  contradiction: "Contradicting Rules",
  priority: "Priority Conflict",
};

export default function PricingConflictsPage() {
  const { toast } = useToast();
  const { data: conflicts, isLoading } = usePricingConflicts();
  const resolveConflict = useResolvePricingConflict();

  const handleResolve = async (conflict: PricingConflict) => {
    try {
      await resolveConflict.mutateAsync({
        conflictId: conflict.id,
        resolution: {},
      });
      toast({
        title: "Conflict resolved",
        description: "The pricing conflict has been resolved.",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to resolve conflict.",
        variant: "error",
      });
    }
  };

  if (isLoading) {
    return <ConflictsPageSkeleton />;
  }

  const conflictList = conflicts ?? [];

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="Pricing Conflicts"
        breadcrumbs={[
          { label: "Billing", href: "/billing" },
          { label: "Pricing", href: "/billing/pricing" },
          { label: "Conflicts" },
        ]}
        actions={
          <Link href="/billing/pricing">
            <Button variant="ghost">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Rules
            </Button>
          </Link>
        }
      />

      {/* Conflicts Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <Info className="w-5 h-5 text-status-info" />
            <div>
              <p className="text-sm text-text-muted">Low Severity</p>
              <p className="text-xl font-bold text-text-primary">
                {conflictList.filter((c) => c.severity === "low").length}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-status-warning" />
            <div>
              <p className="text-sm text-text-muted">Medium Severity</p>
              <p className="text-xl font-bold text-status-warning">
                {conflictList.filter((c) => c.severity === "medium").length}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-status-error" />
            <div>
              <p className="text-sm text-text-muted">High Severity</p>
              <p className="text-xl font-bold text-status-error">
                {conflictList.filter((c) => c.severity === "high").length}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Conflicts List */}
      {conflictList.length > 0 ? (
        <div className="space-y-4">
          {conflictList.map((conflict) => (
            <ConflictCard
              key={conflict.id}
              conflict={conflict}
              onResolve={() => handleResolve(conflict)}
              isResolving={resolveConflict.isPending}
            />
          ))}
        </div>
      ) : (
        <Card className="p-12 text-center">
          <CheckCircle className="w-12 h-12 mx-auto text-status-success mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">No conflicts detected</h3>
          <p className="text-text-muted mb-6">
            All your pricing rules are working in harmony
          </p>
          <Link href="/billing/pricing">
            <Button variant="outline">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Pricing Rules
            </Button>
          </Link>
        </Card>
      )}
    </div>
  );
}

function ConflictCard({
  conflict,
  onResolve,
  isResolving,
}: {
  conflict: PricingConflict;
  onResolve: () => void;
  isResolving: boolean;
}) {
  const severityInfo = severityConfig[conflict.severity];
  const SeverityIcon = severityInfo.icon;

  return (
    <Card className="p-6">
      <div className="flex items-start gap-4">
        <div
          className={cn(
            "w-10 h-10 rounded-lg flex items-center justify-center",
            conflict.severity === "high"
              ? "bg-status-error/15"
              : conflict.severity === "medium"
              ? "bg-status-warning/15"
              : "bg-status-info/15"
          )}
        >
          <SeverityIcon
            className={cn(
              "w-5 h-5",
              conflict.severity === "high"
                ? "text-status-error"
                : conflict.severity === "medium"
                ? "text-status-warning"
                : "text-status-info"
            )}
          />
        </div>

        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <span className={cn("status-badge", severityInfo.class)}>{severityInfo.label}</span>
            <span className="text-sm text-text-muted">
              {conflictTypeLabels[conflict.conflictType]}
            </span>
          </div>

          <p className="text-text-primary mb-4">{conflict.description}</p>

          {/* Conflicting Rules */}
          <div className="mb-4">
            <p className="text-xs text-text-muted mb-2">Conflicting Rules:</p>
            <div className="flex flex-wrap gap-2">
              {conflict.ruleNames.map((name, index) => (
                <Link
                  key={conflict.ruleIds[index]}
                  href={`/billing/pricing/${conflict.ruleIds[index]}`}
                  className="inline-flex items-center gap-1 px-3 py-1.5 bg-surface-overlay rounded-lg text-sm text-accent hover:text-accent-hover"
                >
                  {name}
                  <ChevronRight className="w-3 h-3" />
                </Link>
              ))}
            </div>
          </div>

          {/* Suggested Resolution */}
          {conflict.suggestedResolution && (
            <div className="p-3 bg-accent-subtle/30 rounded-lg border border-accent/20 mb-4">
              <div className="flex items-center gap-2 mb-1">
                <Shield className="w-4 h-4 text-accent" />
                <span className="text-sm font-medium text-accent">Suggested Resolution</span>
              </div>
              <p className="text-sm text-text-secondary">{conflict.suggestedResolution}</p>
            </div>
          )}

          <div className="flex items-center gap-3">
            <Button
              onClick={onResolve}
              disabled={isResolving}
              className="shadow-glow-sm hover:shadow-glow"
            >
              {isResolving ? "Resolving..." : "Auto-Resolve"}
            </Button>
            <span className="text-xs text-text-muted">
              or manually edit the rules above
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
}

function ConflictsPageSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center justify-between">
        <div>
          <div className="h-4 w-32 bg-surface-overlay rounded mb-2" />
          <div className="h-8 w-48 bg-surface-overlay rounded" />
        </div>
        <div className="h-10 w-32 bg-surface-overlay rounded" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="card p-4">
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 bg-surface-overlay rounded" />
              <div>
                <div className="h-4 w-20 bg-surface-overlay rounded mb-2" />
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
