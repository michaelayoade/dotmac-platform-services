"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Calculator,
  ArrowLeft,
  DollarSign,
  Tag,
  Percent,
  CheckCircle,
  Package,
  User,
} from "lucide-react";
import { Button, Card, Input, Select } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { useCalculatePrice, type PricingCalculation } from "@/lib/hooks/api/use-billing";

export default function PricingCalculatorPage() {
  const [productId, setProductId] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [customerId, setCustomerId] = useState("");
  const [couponCode, setCouponCode] = useState("");
  const [result, setResult] = useState<PricingCalculation | null>(null);

  const calculatePrice = useCalculatePrice();

  const handleCalculate = async () => {
    if (!productId) return;

    try {
      const calculation = await calculatePrice.mutateAsync({
        productId,
        quantity,
        customerId: customerId || undefined,
        couponCode: couponCode || undefined,
      });
      setResult(calculation);
    } catch {
      // Error handled by mutation
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="Price Calculator"
        breadcrumbs={[
          { label: "Billing", href: "/billing" },
          { label: "Pricing", href: "/billing/pricing" },
          { label: "Calculator" },
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

      {/* Calculator Form */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
            <Calculator className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary">Calculate Price</h3>
            <p className="text-sm text-text-muted">
              See how pricing rules affect the final price
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Product <span className="text-status-error">*</span>
            </label>
            <div className="relative">
              <Package className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
              <Input
                value={productId}
                onChange={(e) => setProductId(e.target.value)}
                placeholder="Enter product ID or SKU"
                className="pl-10"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Quantity <span className="text-status-error">*</span>
            </label>
            <Input
              type="number"
              min={1}
              value={quantity}
              onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Customer ID
              <span className="text-text-muted font-normal ml-2">(optional)</span>
            </label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
              <Input
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
                placeholder="For customer-specific pricing"
                className="pl-10"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Coupon Code
              <span className="text-text-muted font-normal ml-2">(optional)</span>
            </label>
            <div className="relative">
              <Tag className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
              <Input
                value={couponCode}
                onChange={(e) => setCouponCode(e.target.value)}
                placeholder="Apply a coupon code"
                className="pl-10"
              />
            </div>
          </div>
        </div>

        <div className="mt-6 pt-6 border-t border-border flex justify-end">
          <Button
            onClick={handleCalculate}
            disabled={!productId || calculatePrice.isPending}
            className="shadow-glow-sm hover:shadow-glow"
          >
            {calculatePrice.isPending ? (
              "Calculating..."
            ) : (
              <>
                <Calculator className="w-4 h-4 mr-2" />
                Calculate Price
              </>
            )}
          </Button>
        </div>
      </Card>

      {/* Results */}
      {result && (
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-status-success" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Price Calculation</h3>
              <p className="text-sm text-text-muted">
                {result.appliedRules.length} rule{result.appliedRules.length !== 1 ? "s" : ""} applied
              </p>
            </div>
          </div>

          {/* Price Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="p-4 bg-surface-overlay rounded-lg">
              <p className="text-xs text-text-muted mb-1">Original Price</p>
              <p className="text-2xl font-bold text-text-primary">
                ${(result.originalPrice / 100).toFixed(2)}
              </p>
            </div>
            <div className="p-4 bg-status-success/15 rounded-lg">
              <p className="text-xs text-text-muted mb-1">Final Price</p>
              <p className="text-2xl font-bold text-status-success">
                ${(result.finalPrice / 100).toFixed(2)}
              </p>
            </div>
            <div className="p-4 bg-accent-subtle rounded-lg">
              <p className="text-xs text-text-muted mb-1">You Save</p>
              <p className="text-2xl font-bold text-accent">
                ${(result.savings / 100).toFixed(2)}
                <span className="text-sm font-normal ml-1">
                  ({result.savingsPercent.toFixed(1)}%)
                </span>
              </p>
            </div>
          </div>

          {/* Applied Rules */}
          {result.appliedRules.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-text-primary mb-3">Applied Rules</h4>
              <div className="space-y-2">
                {result.appliedRules.map((appliedRule) => (
                  <div
                    key={appliedRule.ruleId}
                    className="flex items-center justify-between p-3 bg-surface-overlay rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <Percent className="w-4 h-4 text-status-success" />
                      <Link
                        href={`/billing/pricing/${appliedRule.ruleId}`}
                        className="text-sm font-medium text-text-primary hover:text-accent"
                      >
                        {appliedRule.ruleName}
                      </Link>
                    </div>
                    <span className="text-sm font-semibold text-status-success">
                      -${(appliedRule.discountAmount / 100).toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.appliedRules.length === 0 && (
            <div className="text-center py-4">
              <Tag className="w-8 h-8 mx-auto text-text-muted mb-2" />
              <p className="text-sm text-text-muted">No pricing rules were applied</p>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
