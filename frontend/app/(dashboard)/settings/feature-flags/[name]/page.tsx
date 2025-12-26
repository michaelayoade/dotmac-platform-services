"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { format } from "date-fns";
import {
  ArrowLeft,
  Flag,
  Percent,
  Target,
  Plus,
  Power,
  PowerOff,
  Trash2,
  CheckCircle2,
  XCircle,
  Loader2,
  History,
} from "lucide-react";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useFeatureFlag,
  useUpdateFeatureFlag,
  useDeleteFeatureFlag,
  useEnableFeatureFlag,
  useDisableFeatureFlag,
  useFeatureFlagStatus,
} from "@/lib/hooks/api/use-feature-flags";
import { targetingOperators, type TargetingRule } from "@/lib/schemas/feature-flags";

type EditableRule = TargetingRule;

interface FeatureFlagDetailPageProps {
  params: Promise<{ name: string }>;
}

export default function FeatureFlagDetailPage({ params }: FeatureFlagDetailPageProps) {
  const { name } = use(params);
  const decodedName = decodeURIComponent(name);
  const router = useRouter();
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  const { data: flag, isLoading } = useFeatureFlag(decodedName);
  const { data: statusData } = useFeatureFlagStatus();

  const updateFeatureFlag = useUpdateFeatureFlag();
  const deleteFeatureFlag = useDeleteFeatureFlag();
  const enableFeatureFlag = useEnableFeatureFlag();
  const disableFeatureFlag = useDisableFeatureFlag();

  const [isEditing, setIsEditing] = useState(false);
  const [editedDescription, setEditedDescription] = useState("");
  const [editedRollout, setEditedRollout] = useState(100);
  const [editedRules, setEditedRules] = useState<EditableRule[]>([]);
  const [newRule, setNewRule] = useState<Partial<EditableRule>>({
    attribute: "",
    operator: "eq",
    value: "",
    enabled: true,
  });
  const [isDirty, setIsDirty] = useState(false);

  // Populate edit form when flag loads
  useEffect(() => {
    if (flag) {
      setEditedDescription(flag.description || "");
      setEditedRollout(flag.rolloutPercentage ?? 100);
      setEditedRules(
        (flag.targetingRules || []).map((r) => ({
          attribute: r.attribute,
          operator: r.operator,
          value: r.value,
          enabled: r.enabled,
        }))
      );
    }
  }, [flag]);

  const handleToggle = async () => {
    if (!flag) return;
    try {
      if (flag.enabled) {
        await disableFeatureFlag.mutateAsync(decodedName);
        toast({ title: "Feature flag disabled" });
      } else {
        await enableFeatureFlag.mutateAsync(decodedName);
        toast({ title: "Feature flag enabled" });
      }
    } catch {
      toast({ title: "Failed to update flag", variant: "error" });
    }
  };

  const handleDelete = async () => {
    const confirmed = await confirm({
      title: "Delete Feature Flag",
      description: `Are you sure you want to delete "${decodedName}"? This action cannot be undone.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deleteFeatureFlag.mutateAsync(decodedName);
        toast({ title: "Feature flag deleted" });
        router.push("/settings/feature-flags");
      } catch {
        toast({ title: "Failed to delete flag", variant: "error" });
      }
    }
  };

  const handleAddRule = () => {
    if (!newRule.attribute?.trim()) {
      toast({ title: "Attribute is required", variant: "error" });
      return;
    }
    setEditedRules([
      ...editedRules,
      {
        attribute: newRule.attribute.trim(),
        operator: newRule.operator || "eq",
        value: newRule.value,
        enabled: true,
      },
    ]);
    setNewRule({ attribute: "", operator: "eq", value: "", enabled: true });
    setIsDirty(true);
  };

  const handleRemoveRule = (index: number) => {
    setEditedRules(editedRules.filter((_, i) => i !== index));
    setIsDirty(true);
  };

  const handleSaveChanges = async () => {
    try {
      await updateFeatureFlag.mutateAsync({
        name: decodedName,
        data: {
          description: editedDescription || undefined,
          rolloutPercentage: editedRollout,
          targetingRules: editedRules.length > 0 ? editedRules : undefined,
        },
      });
      toast({ title: "Feature flag updated" });
      setIsEditing(false);
      setIsDirty(false);
    } catch {
      toast({ title: "Failed to update flag", variant: "error" });
    }
  };

  const handleCancelEdit = () => {
    if (flag) {
      setEditedDescription(flag.description || "");
      setEditedRollout(flag.rolloutPercentage ?? 100);
      setEditedRules(
        (flag.targetingRules || []).map((r) => ({
          attribute: r.attribute,
          operator: r.operator,
          value: r.value,
          enabled: r.enabled,
        }))
      );
    }
    setIsEditing(false);
    setIsDirty(false);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    );
  }

  if (!flag) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <h2 className="text-xl font-semibold text-text-primary mb-2">Feature flag not found</h2>
        <p className="text-text-muted mb-6">
          The feature flag &quot;{decodedName}&quot; doesn&apos;t exist.
        </p>
        <Button onClick={() => router.push("/settings/feature-flags")}>Back to Feature Flags</Button>
      </div>
    );
  }

  // Get recent changes for this flag
  const recentChanges =
    statusData?.recentChanges?.filter((c) => c.flagName === decodedName).slice(0, 5) || [];

  return (
    <div className="space-y-8 animate-fade-up">
      {dialog}

      <PageHeader
        title={flag.name}
        breadcrumbs={[
          { label: "Settings", href: "/settings" },
          { label: "Feature Flags", href: "/settings/feature-flags" },
          { label: flag.name },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={() => router.back()}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            {isEditing ? (
              <>
                <Button variant="ghost" onClick={handleCancelEdit}>
                  Cancel
                </Button>
                <Button
                  onClick={handleSaveChanges}
                  disabled={!isDirty || updateFeatureFlag.isPending}
                >
                  {updateFeatureFlag.isPending ? "Saving..." : "Save Changes"}
                </Button>
              </>
            ) : (
              <Button variant="outline" onClick={() => setIsEditing(true)}>
                Edit
              </Button>
            )}
          </div>
        }
      />

      {/* Status & Quick Actions */}
      <div className="flex items-center gap-4 flex-wrap">
        <span
          className={cn(
            "inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium",
            flag.enabled
              ? "bg-status-success/15 text-status-success"
              : "bg-surface-overlay text-text-muted"
          )}
        >
          {flag.enabled ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
          {flag.enabled ? "Enabled" : "Disabled"}
        </span>
        <Button variant="outline" size="sm" onClick={handleToggle}>
          {flag.enabled ? (
            <PowerOff className="w-4 h-4 mr-1" />
          ) : (
            <Power className="w-4 h-4 mr-1" />
          )}
          {flag.enabled ? "Disable" : "Enable"}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleDelete}
          className="text-status-error hover:text-status-error"
        >
          <Trash2 className="w-4 h-4 mr-1" />
          Delete
        </Button>
      </div>

      {/* Flag Details */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
            <Flag className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary">Details</h3>
            <p className="text-sm text-text-muted">Feature flag configuration</p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text-muted mb-1.5">Name</label>
            <code className="text-sm text-accent bg-surface-overlay px-3 py-2 rounded-lg inline-block">
              {flag.name}
            </code>
          </div>

          <div>
            <label className="block text-sm font-medium text-text-muted mb-1.5">Description</label>
            {isEditing ? (
              <textarea
                value={editedDescription}
                onChange={(e) => {
                  setEditedDescription(e.target.value);
                  setIsDirty(true);
                }}
                placeholder="Add a description..."
                className="w-full p-3 bg-surface-primary border border-border-subtle rounded-lg text-sm resize-none min-h-[80px]"
              />
            ) : (
              <p className="text-sm text-text-primary">
                {flag.description || "No description"}
              </p>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-text-muted mb-1">Created</p>
              <p className="text-sm text-text-primary">
                {format(new Date(flag.createdAt), "MMM d, yyyy HH:mm")}
              </p>
            </div>
            <div>
              <p className="text-sm text-text-muted mb-1">Last Updated</p>
              <p className="text-sm text-text-primary">
                {format(new Date(flag.updatedAt), "MMM d, yyyy HH:mm")}
              </p>
            </div>
          </div>
        </div>
      </Card>

      {/* Rollout Configuration */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
            <Percent className="w-5 h-5 text-highlight" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary">Rollout</h3>
            <p className="text-sm text-text-muted">Gradual rollout configuration</p>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-text-muted mb-1.5">
            Rollout Percentage
          </label>
          {isEditing ? (
            <div className="flex items-center gap-4">
              <Input
                type="number"
                value={editedRollout}
                onChange={(e) => {
                  setEditedRollout(parseInt(e.target.value) || 0);
                  setIsDirty(true);
                }}
                min={0}
                max={100}
                className="w-24"
              />
              <span className="text-sm text-text-muted">%</span>
              <div className="flex-1 h-2 bg-surface-overlay rounded-full overflow-hidden">
                <div
                  className="h-full bg-accent transition-all"
                  style={{ width: `${editedRollout}%` }}
                />
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-4">
              <span className="text-2xl font-semibold text-text-primary">
                {flag.rolloutPercentage ?? 100}%
              </span>
              <div className="flex-1 h-2 bg-surface-overlay rounded-full overflow-hidden">
                <div
                  className="h-full bg-accent transition-all"
                  style={{ width: `${flag.rolloutPercentage ?? 100}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Targeting Rules */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
            <Target className="w-5 h-5 text-status-info" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary">Targeting Rules</h3>
            <p className="text-sm text-text-muted">Target specific users or contexts</p>
          </div>
        </div>

        {isEditing && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-2 mb-4">
            <Input
              value={newRule.attribute || ""}
              onChange={(e) => setNewRule({ ...newRule, attribute: e.target.value })}
              placeholder="Attribute"
            />
            <select
              value={newRule.operator || "eq"}
              onChange={(e) =>
                setNewRule({ ...newRule, operator: e.target.value as TargetingRule["operator"] })
              }
              className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
            >
              {targetingOperators.map((op) => (
                <option key={op.value} value={op.value}>
                  {op.label}
                </option>
              ))}
            </select>
            <Input
              value={String(newRule.value || "")}
              onChange={(e) => setNewRule({ ...newRule, value: e.target.value })}
              placeholder="Value"
            />
            <Button type="button" variant="outline" onClick={handleAddRule}>
              <Plus className="w-4 h-4 mr-1" />
              Add
            </Button>
          </div>
        )}

        {(isEditing ? editedRules : flag.targetingRules || []).length > 0 ? (
          <div className="space-y-2">
            {(isEditing ? editedRules : flag.targetingRules || []).map((rule, index) => (
              <div
                key={index}
                className="flex items-center gap-3 p-3 bg-surface-overlay rounded-lg"
              >
                <code className="text-sm font-mono text-accent">{rule.attribute}</code>
                <span className="text-xs text-text-muted px-2 py-0.5 bg-surface-primary rounded">
                  {targetingOperators.find((op) => op.value === rule.operator)?.label}
                </span>
                <code className="text-sm font-mono text-text-secondary flex-1">
                  {String(rule.value)}
                </code>
                {isEditing && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemoveRule(index)}
                  >
                    <Trash2 className="w-4 h-4 text-status-error" />
                  </Button>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-text-muted text-center py-4">
            No targeting rules. Flag applies to all users based on rollout percentage.
          </p>
        )}
      </Card>

      {/* Recent Changes */}
      {recentChanges.length > 0 && (
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-status-warning/15 flex items-center justify-center">
              <History className="w-5 h-5 text-status-warning" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Recent Changes</h3>
              <p className="text-sm text-text-muted">Activity history for this flag</p>
            </div>
          </div>

          <div className="space-y-2">
            {recentChanges.map((change, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-surface-overlay rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <span
                    className={cn(
                      "text-xs font-medium px-2 py-0.5 rounded",
                      change.action === "enabled" && "bg-status-success/15 text-status-success",
                      change.action === "disabled" && "bg-status-error/15 text-status-error",
                      change.action === "updated" && "bg-status-info/15 text-status-info",
                      change.action === "created" && "bg-accent-subtle text-accent"
                    )}
                  >
                    {change.action}
                  </span>
                </div>
                <p className="text-xs text-text-muted">
                  {format(new Date(change.timestamp), "MMM d, HH:mm")}
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
