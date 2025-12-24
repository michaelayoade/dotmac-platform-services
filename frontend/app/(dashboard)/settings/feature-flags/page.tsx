"use client";

import { useState } from "react";
import {
  Flag,
  Plus,
  Search,
  ToggleLeft,
  ToggleRight,
  Trash2,
  Settings,
  Users,
  Percent,
  Clock,
  RefreshCcw,
} from "lucide-react";
import { format } from "date-fns";
import { Button, Card, Input, Modal } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { ConfirmDialog, useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useFeatureFlags,
  useFeatureFlagStatus,
  useEnableFeatureFlag,
  useDisableFeatureFlag,
  useDeleteFeatureFlag,
  useClearFeatureFlagCache,
} from "@/lib/hooks/api/use-feature-flags";

export default function FeatureFlagsPage() {
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  const [searchQuery, setSearchQuery] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);

  const { data: flags, isLoading, refetch } = useFeatureFlags();
  const { data: status } = useFeatureFlagStatus();

  const enableFlag = useEnableFeatureFlag();
  const disableFlag = useDisableFeatureFlag();
  const deleteFlag = useDeleteFeatureFlag();
  const clearCache = useClearFeatureFlagCache();

  const filteredFlags = (flags || []).filter(
    (f) =>
      f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );
  const rolloutsActive = (flags || []).filter(
    (flag) =>
      typeof flag.rolloutPercentage === "number" &&
      flag.rolloutPercentage > 0 &&
      flag.rolloutPercentage < 100
  ).length;

  const handleToggle = async (name: string, enabled: boolean) => {
    try {
      if (enabled) {
        await disableFlag.mutateAsync(name);
        toast({ title: `${name} disabled` });
      } else {
        await enableFlag.mutateAsync(name);
        toast({ title: `${name} enabled` });
      }
    } catch {
      toast({ title: "Failed to toggle flag", variant: "error" });
    }
  };

  const handleDelete = async (name: string) => {
    const confirmed = await confirm({
      title: "Delete Feature Flag",
      description: `Are you sure you want to delete "${name}"? This will affect all users immediately.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deleteFlag.mutateAsync(name);
        toast({ title: "Feature flag deleted" });
      } catch {
        toast({ title: "Failed to delete flag", variant: "error" });
      }
    }
  };

  const handleClearCache = async () => {
    try {
      await clearCache.mutateAsync();
      toast({ title: "Cache cleared", description: "Feature flag cache has been refreshed." });
    } catch {
      toast({ title: "Failed to clear cache", variant: "error" });
    }
  };

  if (isLoading) {
    return <FeatureFlagsSkeleton />;
  }

  return (
    <div className="space-y-8 animate-fade-up">
      {dialog}

      <PageHeader
        title="Feature Flags"
        description="Control feature rollouts and experiments"
        breadcrumbs={[
          { label: "Settings", href: "/settings" },
          { label: "Feature Flags" },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={handleClearCache}>
              <RefreshCcw className="w-4 h-4 mr-2" />
              Clear Cache
            </Button>
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Create Flag
            </Button>
          </div>
        }
      />

      {/* Stats */}
      {status && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <p className="text-sm text-text-muted mb-1">Total Flags</p>
            <p className="text-2xl font-semibold text-text-primary">{status.totalFlags}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-text-muted mb-1">Enabled</p>
            <p className="text-2xl font-semibold text-status-success">{status.enabledFlags}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-text-muted mb-1">Disabled</p>
            <p className="text-2xl font-semibold text-text-muted">{status.disabledFlags}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-text-muted mb-1">Rollouts Active</p>
            <p className="text-2xl font-semibold text-accent">{rolloutsActive}</p>
          </Card>
        </div>
      )}

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
        <Input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search flags..."
          className="pl-10"
        />
      </div>

      {/* Flags List */}
      {filteredFlags.length === 0 ? (
        <Card className="p-12 text-center">
          <Flag className="w-12 h-12 text-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">No feature flags</h3>
          <p className="text-text-muted mb-6">
            {searchQuery ? "No flags match your search" : "Create your first feature flag"}
          </p>
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Create Flag
          </Button>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredFlags.map((flag) => (
            <Card key={flag.name} className="p-6">
              <div className="flex items-start gap-6">
                {/* Toggle */}
                <button
                  onClick={() => handleToggle(flag.name, flag.enabled)}
                  className="mt-1"
                >
                  {flag.enabled ? (
                    <ToggleRight className="w-10 h-10 text-status-success" />
                  ) : (
                    <ToggleLeft className="w-10 h-10 text-text-muted" />
                  )}
                </button>

                {/* Content */}
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <h4 className="font-semibold text-text-primary font-mono">{flag.name}</h4>
                    <span
                      className={cn(
                        "px-2 py-0.5 rounded-full text-xs font-medium",
                        flag.enabled
                          ? "bg-status-success/15 text-status-success"
                          : "bg-surface-overlay text-text-muted"
                      )}
                    >
                      {flag.enabled ? "Enabled" : "Disabled"}
                    </span>
                    {flag.rolloutPercentage !== undefined && flag.rolloutPercentage < 100 && (
                      <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-accent-subtle text-accent">
                        <Percent className="w-3 h-3" />
                        {flag.rolloutPercentage}% rollout
                      </span>
                    )}
                  </div>

                  {flag.description && (
                    <p className="text-sm text-text-muted mb-3">{flag.description}</p>
                  )}

                  <div className="flex items-center gap-4 text-sm text-text-muted">
                    {flag.targetingRules && flag.targetingRules.length > 0 && (
                      <span className="flex items-center gap-1">
                        <Users className="w-4 h-4" />
                        {flag.targetingRules.length} targeting rule
                        {flag.targetingRules.length !== 1 ? "s" : ""}
                      </span>
                    )}
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      Updated {format(new Date(flag.updatedAt), "MMM d, yyyy")}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm">
                    <Settings className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(flag.name)}
                    className="text-status-error hover:text-status-error"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Modal open={showCreateModal} onOpenChange={setShowCreateModal}>
        <div className="p-6 max-w-lg">
          <h2 className="text-xl font-semibold text-text-primary mb-6">Create Feature Flag</h2>
          <form className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Flag Name
              </label>
              <Input placeholder="new_checkout_flow" className="font-mono" />
              <p className="text-xs text-text-muted mt-1">
                Use snake_case for flag names
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Description
              </label>
              <Input placeholder="Enable the new checkout experience" />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Initial State
              </label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="radio" name="state" value="disabled" defaultChecked className="accent-accent" />
                  <span className="text-sm">Disabled</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="radio" name="state" value="enabled" className="accent-accent" />
                  <span className="text-sm">Enabled</span>
                </label>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Rollout Percentage
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="0"
                  max="100"
                  defaultValue="100"
                  className="flex-1 accent-accent"
                />
                <span className="text-sm font-mono w-12 text-right">100%</span>
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="ghost" onClick={() => setShowCreateModal(false)}>
                Cancel
              </Button>
              <Button>Create Flag</Button>
            </div>
          </form>
        </div>
      </Modal>
    </div>
  );
}

function FeatureFlagsSkeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      <div className="h-8 w-48 bg-surface-overlay rounded" />
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card p-4 h-20" />
        ))}
      </div>
      <div className="space-y-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card p-6 h-28" />
        ))}
      </div>
    </div>
  );
}
