"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  ArrowLeft,
  Flag,
  Percent,
  Target,
  Plus,
  X,
  Trash2,
} from "lucide-react";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { useCreateFeatureFlag } from "@/lib/hooks/api/use-feature-flags";
import {
  createFeatureFlagSchema,
  targetingOperators,
  type CreateFeatureFlagData,
  type TargetingRule,
} from "@/lib/schemas/feature-flags";

export default function NewFeatureFlagPage() {
  const router = useRouter();
  const { toast } = useToast();

  const createFeatureFlag = useCreateFeatureFlag();

  const [targetingRules, setTargetingRules] = useState<TargetingRule[]>([]);
  const [newRule, setNewRule] = useState<Partial<TargetingRule>>({
    attribute: "",
    operator: "eq",
    value: "",
    enabled: true,
  });

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setValue,
    watch,
  } = useForm<CreateFeatureFlagData>({
    resolver: zodResolver(createFeatureFlagSchema),
    defaultValues: {
      name: "",
      description: "",
      enabled: false,
      rolloutPercentage: 100,
      targetingRules: [],
    },
  });

  const isEnabled = watch("enabled");
  const rolloutPercentage = watch("rolloutPercentage") || 100;

  const handleAddRule = () => {
    if (!newRule.attribute?.trim()) {
      toast({ title: "Attribute is required", variant: "error" });
      return;
    }
    setTargetingRules([
      ...targetingRules,
      {
        attribute: newRule.attribute.trim(),
        operator: newRule.operator || "eq",
        value: newRule.value,
        enabled: true,
      },
    ]);
    setNewRule({ attribute: "", operator: "eq", value: "", enabled: true });
  };

  const handleRemoveRule = (index: number) => {
    setTargetingRules(targetingRules.filter((_, i) => i !== index));
  };

  const onSubmit = async (data: CreateFeatureFlagData) => {
    try {
      await createFeatureFlag.mutateAsync({
        ...data,
        targetingRules: targetingRules.length > 0 ? targetingRules : undefined,
      });

      toast({
        title: "Feature flag created",
        description: `${data.name} has been created successfully.`,
      });

      router.push(`/settings/feature-flags/${encodeURIComponent(data.name)}`);
    } catch {
      toast({
        title: "Failed to create feature flag",
        description: "Please try again.",
        variant: "error",
      });
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-up">
      <PageHeader
        title="New Feature Flag"
        breadcrumbs={[
          { label: "Settings", href: "/settings" },
          { label: "Feature Flags", href: "/settings/feature-flags" },
          { label: "New" },
        ]}
        actions={
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        }
      />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Basic Information */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <Flag className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Flag Details</h3>
              <p className="text-sm text-text-muted">Basic feature flag configuration</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Flag Name <span className="text-status-error">*</span>
              </label>
              <Input
                {...register("name")}
                placeholder="my-feature-flag"
                className={cn(errors.name && "border-status-error")}
              />
              <p className="text-xs text-text-muted mt-1">
                Use lowercase letters, numbers, underscores, and hyphens
              </p>
              {errors.name && (
                <p className="text-xs text-status-error mt-1">{errors.name.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Description
              </label>
              <textarea
                {...register("description")}
                placeholder="Describe what this feature flag controls..."
                className="w-full p-3 bg-surface-primary border border-border-subtle rounded-lg text-sm resize-none min-h-[100px]"
              />
            </div>

            <div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isEnabled}
                  onChange={(e) => setValue("enabled", e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm font-medium text-text-primary">
                  Enable flag immediately
                </span>
              </label>
              <p className="text-xs text-text-muted mt-1 ml-6">
                Disabled flags always return false
              </p>
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
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Rollout Percentage
            </label>
            <div className="flex items-center gap-4">
              <Input
                {...register("rolloutPercentage", { valueAsNumber: true })}
                type="number"
                min={0}
                max={100}
                className="w-24"
              />
              <span className="text-sm text-text-muted">%</span>
              <div className="flex-1 h-2 bg-surface-overlay rounded-full overflow-hidden">
                <div
                  className="h-full bg-accent transition-all"
                  style={{ width: `${rolloutPercentage}%` }}
                />
              </div>
            </div>
            <p className="text-xs text-text-muted mt-2">
              {rolloutPercentage === 100
                ? "All users will see this feature"
                : rolloutPercentage === 0
                  ? "No users will see this feature"
                  : `Approximately ${rolloutPercentage}% of users will see this feature`}
            </p>
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

          <div className="space-y-4">
            {/* Add new rule */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
              <Input
                value={newRule.attribute || ""}
                onChange={(e) => setNewRule({ ...newRule, attribute: e.target.value })}
                placeholder="Attribute (e.g., userId)"
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
                Add Rule
              </Button>
            </div>

            {/* Existing rules */}
            {targetingRules.length > 0 && (
              <div className="space-y-2 mt-4">
                {targetingRules.map((rule, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-3 p-3 bg-surface-overlay rounded-lg"
                  >
                    <code className="text-sm font-mono text-accent">{rule.attribute}</code>
                    <span className="text-xs text-text-muted">
                      {targetingOperators.find((op) => op.value === rule.operator)?.label}
                    </span>
                    <code className="text-sm font-mono text-text-secondary flex-1">
                      {String(rule.value)}
                    </code>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveRule(index)}
                    >
                      <Trash2 className="w-4 h-4 text-status-error" />
                    </Button>
                  </div>
                ))}
              </div>
            )}

            {targetingRules.length === 0 && (
              <p className="text-sm text-text-muted text-center py-4">
                No targeting rules. Flag applies to all users based on rollout percentage.
              </p>
            )}
          </div>
        </Card>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-4">
          <Button type="button" variant="ghost" onClick={() => router.back()}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting || createFeatureFlag.isPending}>
            {isSubmitting || createFeatureFlag.isPending ? "Creating..." : "Create Feature Flag"}
          </Button>
        </div>
      </form>
    </div>
  );
}
