"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Save,
  Percent,
  DollarSign,
  Plus,
  Trash2,
  Tag,
} from "lucide-react";
import { Button, Card, Input, Select } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { PageHeader } from "@/components/shared/page-header";
import {
  useCreatePricingRule,
  type PricingRuleType,
  type PricingConditionType,
  type CreatePricingRuleData,
} from "@/lib/hooks/api/use-billing";

interface ConditionFormData {
  id: string;
  type: PricingConditionType;
  operator: "equals" | "not_equals" | "greater_than" | "less_than" | "in" | "not_in" | "between";
  value: string;
}

export default function NewPricingRulePage() {
  const router = useRouter();
  const { toast } = useToast();
  const createRule = useCreatePricingRule();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [type, setType] = useState<PricingRuleType>("discount");
  const [priority, setPriority] = useState(100);
  const [discountType, setDiscountType] = useState<"percentage" | "fixed_amount">("percentage");
  const [discountValue, setDiscountValue] = useState<number | undefined>();
  const [conditions, setConditions] = useState<ConditionFormData[]>([]);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [usageLimit, setUsageLimit] = useState<number | undefined>();

  const addCondition = () => {
    const newCondition: ConditionFormData = {
      id: Date.now().toString(),
      type: "customer_segment",
      operator: "equals",
      value: "",
    };
    setConditions([...conditions, newCondition]);
  };

  const removeCondition = (id: string) => {
    setConditions(conditions.filter((c) => c.id !== id));
  };

  const updateCondition = (id: string, updates: Partial<ConditionFormData>) => {
    setConditions(conditions.map((c) => (c.id === id ? { ...c, ...updates } : c)));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      toast({
        title: "Validation Error",
        description: "Rule name is required.",
        variant: "error",
      });
      return;
    }

    const data: CreatePricingRuleData = {
      name: name.trim(),
      description: description.trim() || undefined,
      type,
      priority,
      conditions: conditions.map((c) => ({
        type: c.type,
        operator: c.operator,
        value: c.value,
      })),
      discountType: type === "discount" ? discountType : undefined,
      discountValue: type === "discount" && discountValue ?
        (discountType === "percentage" ? discountValue : discountValue * 100) : undefined,
      startDate: startDate || undefined,
      endDate: endDate || undefined,
      usageLimit,
    };

    try {
      const rule = await createRule.mutateAsync(data);
      toast({
        title: "Rule created",
        description: `"${rule.name}" has been created successfully.`,
      });
      router.push(`/billing/pricing/${rule.id}`);
    } catch {
      toast({
        title: "Error",
        description: "Failed to create rule. Please try again.",
        variant: "error",
      });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-3xl mx-auto space-y-8 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="New Pricing Rule"
        breadcrumbs={[
          { label: "Billing", href: "/billing" },
          { label: "Pricing", href: "/billing/pricing" },
          { label: "New" },
        ]}
        actions={
          <Button variant="ghost" type="button" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        }
      />

      {/* Basic Info */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-text-primary mb-6">Rule Details</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Rule Name <span className="text-status-error">*</span>
            </label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Summer Sale 20% Off"
              required
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Description
            </label>
            <Input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of this rule"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Rule Type <span className="text-status-error">*</span>
            </label>
            <Select value={type} onChange={(e) => setType(e.target.value as PricingRuleType)}>
              <option value="discount">Discount</option>
              <option value="markup">Markup</option>
              <option value="override">Price Override</option>
              <option value="volume">Volume Discount</option>
              <option value="bundle">Bundle Pricing</option>
              <option value="tiered">Tiered Pricing</option>
            </Select>
          </div>
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Priority
            </label>
            <Input
              type="number"
              min={1}
              value={priority}
              onChange={(e) => setPriority(parseInt(e.target.value) || 100)}
            />
            <p className="text-xs text-text-muted mt-1">Higher priority rules are applied first</p>
          </div>
        </div>
      </Card>

      {/* Discount Configuration */}
      {type === "discount" && (
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
              <Percent className="w-5 h-5 text-status-success" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Discount</h3>
              <p className="text-sm text-text-muted">Configure the discount amount</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Discount Type
              </label>
              <Select
                value={discountType}
                onChange={(e) => setDiscountType(e.target.value as "percentage" | "fixed_amount")}
              >
                <option value="percentage">Percentage</option>
                <option value="fixed_amount">Fixed Amount</option>
              </Select>
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Value
              </label>
              <div className="relative">
                {discountType === "percentage" ? (
                  <Percent className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                ) : (
                  <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                )}
                <Input
                  type="number"
                  min={0}
                  step={discountType === "percentage" ? 1 : 0.01}
                  value={discountValue || ""}
                  onChange={(e) => setDiscountValue(parseFloat(e.target.value) || undefined)}
                  placeholder={discountType === "percentage" ? "10" : "5.00"}
                  className={discountType === "fixed_amount" ? "pl-10" : ""}
                />
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Conditions */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <Tag className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Conditions</h3>
              <p className="text-sm text-text-muted">When should this rule apply?</p>
            </div>
          </div>
          <Button type="button" variant="outline" onClick={addCondition}>
            <Plus className="w-4 h-4 mr-2" />
            Add Condition
          </Button>
        </div>

        {conditions.length > 0 ? (
          <div className="space-y-4">
            {conditions.map((condition) => (
              <div
                key={condition.id}
                className="flex items-center gap-4 p-4 bg-surface-overlay rounded-lg"
              >
                <Select
                  value={condition.type}
                  onChange={(e) =>
                    updateCondition(condition.id, { type: e.target.value as PricingConditionType })
                  }
                  className="w-40"
                >
                  <option value="customer_segment">Customer Segment</option>
                  <option value="product_category">Product Category</option>
                  <option value="quantity">Quantity</option>
                  <option value="coupon_code">Coupon Code</option>
                  <option value="subscription_tier">Subscription Tier</option>
                </Select>
                <Select
                  value={condition.operator}
                  onChange={(e) =>
                    updateCondition(condition.id, {
                      operator: e.target.value as ConditionFormData["operator"],
                    })
                  }
                  className="w-32"
                >
                  <option value="equals">Equals</option>
                  <option value="not_equals">Not Equals</option>
                  <option value="greater_than">Greater Than</option>
                  <option value="less_than">Less Than</option>
                  <option value="in">In List</option>
                </Select>
                <Input
                  value={condition.value}
                  onChange={(e) => updateCondition(condition.id, { value: e.target.value })}
                  placeholder="Value"
                  className="flex-1"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeCondition(condition.id)}
                  className="text-status-error hover:text-status-error"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-text-muted">
            <p>No conditions added. This rule will apply to all purchases.</p>
          </div>
        )}
      </Card>

      {/* Schedule & Limits */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-text-primary mb-6">Schedule & Limits</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Start Date
            </label>
            <Input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              End Date
            </label>
            <Input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Usage Limit
            </label>
            <Input
              type="number"
              min={1}
              value={usageLimit || ""}
              onChange={(e) => setUsageLimit(parseInt(e.target.value) || undefined)}
              placeholder="Unlimited"
            />
          </div>
        </div>
      </Card>

      {/* Actions */}
      <Card className="p-6">
        <div className="flex items-center justify-end gap-3">
          <Button type="button" variant="ghost" onClick={() => router.back()}>
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={createRule.isPending}
            className="shadow-glow-sm hover:shadow-glow"
          >
            {createRule.isPending ? (
              "Creating..."
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Create Rule
              </>
            )}
          </Button>
        </div>
      </Card>
    </form>
  );
}
