"use client";

import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export type PlanType = "free" | "starter" | "professional" | "enterprise";

interface PlanFeature {
  text: string;
  included: boolean;
}

interface Plan {
  id: PlanType;
  name: string;
  description: string;
  price: number;
  billingPeriod: string;
  features: PlanFeature[];
  popular?: boolean;
  limits: {
    users: number;
    apiCalls: number;
    storage: number;
  };
}

const plans: Plan[] = [
  {
    id: "free",
    name: "Free",
    description: "Perfect for trying out the platform",
    price: 0,
    billingPeriod: "forever",
    limits: {
      users: 3,
      apiCalls: 1000,
      storage: 1,
    },
    features: [
      { text: "Up to 3 team members", included: true },
      { text: "1,000 API calls/month", included: true },
      { text: "1 GB storage", included: true },
      { text: "Community support", included: true },
      { text: "Basic analytics", included: true },
      { text: "Custom domain", included: false },
      { text: "SSO authentication", included: false },
      { text: "Priority support", included: false },
    ],
  },
  {
    id: "starter",
    name: "Starter",
    description: "Great for small teams getting started",
    price: 29,
    billingPeriod: "per month",
    limits: {
      users: 10,
      apiCalls: 10000,
      storage: 10,
    },
    features: [
      { text: "Up to 10 team members", included: true },
      { text: "10,000 API calls/month", included: true },
      { text: "10 GB storage", included: true },
      { text: "Email support", included: true },
      { text: "Advanced analytics", included: true },
      { text: "Custom domain", included: true },
      { text: "SSO authentication", included: false },
      { text: "Priority support", included: false },
    ],
  },
  {
    id: "professional",
    name: "Professional",
    description: "For growing teams with advanced needs",
    price: 99,
    billingPeriod: "per month",
    popular: true,
    limits: {
      users: 50,
      apiCalls: 100000,
      storage: 100,
    },
    features: [
      { text: "Up to 50 team members", included: true },
      { text: "100,000 API calls/month", included: true },
      { text: "100 GB storage", included: true },
      { text: "Priority email support", included: true },
      { text: "Advanced analytics", included: true },
      { text: "Custom domain", included: true },
      { text: "SSO authentication", included: true },
      { text: "API access", included: true },
    ],
  },
  {
    id: "enterprise",
    name: "Enterprise",
    description: "For large organizations with custom requirements",
    price: -1, // Custom pricing
    billingPeriod: "custom",
    limits: {
      users: -1, // Unlimited
      apiCalls: -1,
      storage: -1,
    },
    features: [
      { text: "Unlimited team members", included: true },
      { text: "Unlimited API calls", included: true },
      { text: "Unlimited storage", included: true },
      { text: "Dedicated support", included: true },
      { text: "Custom analytics", included: true },
      { text: "Custom domain", included: true },
      { text: "SSO authentication", included: true },
      { text: "SLA guarantee", included: true },
    ],
  },
];

interface PlanSelectorProps {
  selectedPlan: PlanType;
  onPlanSelect: (plan: PlanType) => void;
  className?: string;
  showEnterprise?: boolean;
}

export function PlanSelector({
  selectedPlan,
  onPlanSelect,
  className,
  showEnterprise = false,
}: PlanSelectorProps) {
  const displayPlans = showEnterprise
    ? plans
    : plans.filter(p => p.id !== "enterprise");

  return (
    <div className={cn("grid gap-6", className)}>
      <div className={cn(
        "grid gap-4",
        displayPlans.length === 3 ? "md:grid-cols-3" : "md:grid-cols-2 lg:grid-cols-4"
      )}>
        {displayPlans.map((plan) => {
          const isSelected = selectedPlan === plan.id;

          return (
            <button
              key={plan.id}
              type="button"
              onClick={() => onPlanSelect(plan.id)}
              className={cn(
                "relative flex flex-col p-6 rounded-xl border-2 text-left transition-all duration-200",
                isSelected
                  ? "border-accent bg-accent/5 shadow-glow-sm"
                  : "border-border bg-surface hover:border-accent/50 hover:bg-surface-elevated",
                plan.popular && !isSelected && "border-accent/30"
              )}
            >
              {/* Popular badge */}
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="px-3 py-1 text-2xs font-semibold uppercase tracking-wider bg-accent text-white rounded-full">
                    Most Popular
                  </span>
                </div>
              )}

              {/* Plan header */}
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-text-primary">
                  {plan.name}
                </h3>
                <p className="text-sm text-text-muted mt-1">
                  {plan.description}
                </p>
              </div>

              {/* Pricing */}
              <div className="mb-6">
                {plan.price === -1 ? (
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-bold text-text-primary">
                      Custom
                    </span>
                  </div>
                ) : plan.price === 0 ? (
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-bold text-text-primary">
                      $0
                    </span>
                    <span className="text-text-muted">/{plan.billingPeriod}</span>
                  </div>
                ) : (
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-bold text-text-primary">
                      ${plan.price}
                    </span>
                    <span className="text-text-muted">/{plan.billingPeriod}</span>
                  </div>
                )}
              </div>

              {/* Features */}
              <ul className="space-y-3 flex-1">
                {plan.features.slice(0, 5).map((feature, index) => (
                  <li
                    key={index}
                    className={cn(
                      "flex items-start gap-2 text-sm",
                      feature.included ? "text-text-secondary" : "text-text-muted"
                    )}
                  >
                    <Check
                      className={cn(
                        "w-4 h-4 mt-0.5 flex-shrink-0",
                        feature.included ? "text-status-success" : "text-border"
                      )}
                    />
                    <span className={!feature.included ? "line-through" : ""}>
                      {feature.text}
                    </span>
                  </li>
                ))}
              </ul>

              {/* Selection indicator */}
              <div
                className={cn(
                  "mt-6 py-2 px-4 rounded-lg text-center text-sm font-medium transition-colors",
                  isSelected
                    ? "bg-accent text-white"
                    : "bg-surface-overlay text-text-secondary"
                )}
              >
                {isSelected ? "Selected" : "Select Plan"}
              </div>
            </button>
          );
        })}
      </div>

      {/* Enterprise CTA */}
      {!showEnterprise && (
        <p className="text-center text-sm text-text-muted">
          Need more?{" "}
          <a href="/contact" className="text-accent hover:text-accent-hover font-medium">
            Contact us
          </a>{" "}
          for Enterprise pricing.
        </p>
      )}
    </div>
  );
}

export { plans };
