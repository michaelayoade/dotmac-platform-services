"use client";

import { useState } from "react";
import {
  User,
  Mail,
  Lock,
  Building2,
  Users,
  Globe,
  ArrowRight,
  ArrowLeft,
  Loader2,
} from "lucide-react";
import { Form, FormField, FormSubmitButton, useForm } from "@dotmac/forms";
import { Input, Button } from "@dotmac/core";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { cn } from "@/lib/utils";
import { StepIndicator, type Step } from "@/components/shared/step-indicator";
import { PlanSelector, type PlanType } from "./plan-selector";

// Step 1: Account Schema
const accountSchema = z.object({
  fullName: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Please enter a valid email address"),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
    .regex(/[a-z]/, "Password must contain at least one lowercase letter")
    .regex(/[0-9]/, "Password must contain at least one number"),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});

// Step 2: Organization Schema
const organizationSchema = z.object({
  companyName: z.string().min(2, "Company name must be at least 2 characters"),
  companySlug: z
    .string()
    .min(3, "Slug must be at least 3 characters")
    .max(50, "Slug must be at most 50 characters")
    .regex(/^[a-z0-9-]+$/, "Slug can only contain lowercase letters, numbers, and hyphens"),
  industry: z.string().optional(),
  companySize: z.string().optional(),
  country: z.string().optional(),
});

type AccountFormData = z.infer<typeof accountSchema>;
type OrganizationFormData = z.infer<typeof organizationSchema>;

export interface SignupData {
  account: AccountFormData;
  organization: OrganizationFormData;
  plan: PlanType;
}

interface SignupWizardProps {
  onComplete: (data: SignupData) => Promise<void>;
  className?: string;
}

const steps: Step[] = [
  { id: "account", title: "Account", description: "Create your account" },
  { id: "organization", title: "Organization", description: "Tell us about your company" },
  { id: "plan", title: "Plan", description: "Choose your plan" },
];

const industries = [
  { value: "", label: "Select industry" },
  { value: "technology", label: "Technology" },
  { value: "healthcare", label: "Healthcare" },
  { value: "finance", label: "Finance" },
  { value: "education", label: "Education" },
  { value: "retail", label: "Retail" },
  { value: "manufacturing", label: "Manufacturing" },
  { value: "services", label: "Professional Services" },
  { value: "other", label: "Other" },
];

const companySizes = [
  { value: "", label: "Select company size" },
  { value: "1-10", label: "1-10 employees" },
  { value: "11-50", label: "11-50 employees" },
  { value: "51-200", label: "51-200 employees" },
  { value: "201-500", label: "201-500 employees" },
  { value: "501-1000", label: "501-1000 employees" },
  { value: "1000+", label: "1000+ employees" },
];

export function SignupWizard({ onComplete, className }: SignupWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form data state
  const [accountData, setAccountData] = useState<AccountFormData | null>(null);
  const [organizationData, setOrganizationData] = useState<OrganizationFormData | null>(null);
  const [selectedPlan, setSelectedPlan] = useState<PlanType>("starter");

  // Step 1 Form
  const accountForm = useForm<AccountFormData>({
    resolver: zodResolver(accountSchema),
    defaultValues: {
      fullName: "",
      email: "",
      password: "",
      confirmPassword: "",
    },
  });

  // Step 2 Form
  const organizationForm = useForm<OrganizationFormData>({
    resolver: zodResolver(organizationSchema),
    defaultValues: {
      companyName: "",
      companySlug: "",
      industry: "",
      companySize: "",
      country: "",
    },
  });

  // Generate slug from company name
  const handleCompanyNameChange = (name: string) => {
    const slug = name
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, "")
      .replace(/\s+/g, "-")
      .replace(/-+/g, "-")
      .slice(0, 50);
    organizationForm.setValue("companySlug", slug);
  };

  const handleAccountSubmit = (data: AccountFormData) => {
    setAccountData(data);
    setCurrentStep(1);
  };

  const handleOrganizationSubmit = (data: OrganizationFormData) => {
    setOrganizationData(data);
    setCurrentStep(2);
  };

  const handlePlanSubmit = async () => {
    if (!accountData || !organizationData) return;

    setIsSubmitting(true);
    setError(null);

    try {
      await onComplete({
        account: accountData,
        organization: organizationData,
        plan: selectedPlan,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
      setIsSubmitting(false);
    }
  };

  const goBack = () => {
    setError(null);
    setCurrentStep((prev) => Math.max(0, prev - 1));
  };

  return (
    <div className={cn("w-full max-w-2xl mx-auto", className)}>
      {/* Step Indicator */}
      <StepIndicator steps={steps} currentStep={currentStep} className="mb-8" />

      {/* Error message */}
      {error && (
        <div className="mb-6 flex items-center gap-3 p-4 rounded-lg bg-status-error/15 border border-status-error/20 text-status-error">
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Step 1: Account */}
      {currentStep === 0 && (
        <div className="space-y-6">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-semibold text-text-primary">
              Create your account
            </h2>
            <p className="text-text-secondary mt-2">
              Enter your details to get started
            </p>
          </div>

          <Form form={accountForm} onSubmit={handleAccountSubmit} className="space-y-5">
            <FormField name="fullName" label="Full Name" required>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                <Input
                  {...accountForm.register("fullName")}
                  placeholder="John Doe"
                  className="pl-10"
                  autoFocus
                />
              </div>
            </FormField>

            <FormField name="email" label="Email Address" required>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                <Input
                  {...accountForm.register("email")}
                  type="email"
                  placeholder="you@company.com"
                  className="pl-10"
                />
              </div>
            </FormField>

            <FormField name="password" label="Password" required>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                <Input
                  {...accountForm.register("password")}
                  type="password"
                  placeholder="••••••••"
                  className="pl-10"
                />
              </div>
              <p className="text-xs text-text-muted mt-1">
                Must be at least 8 characters with uppercase, lowercase, and number
              </p>
            </FormField>

            <FormField name="confirmPassword" label="Confirm Password" required>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                <Input
                  {...accountForm.register("confirmPassword")}
                  type="password"
                  placeholder="••••••••"
                  className="pl-10"
                />
              </div>
            </FormField>

            <FormSubmitButton className="w-full" loadingText="Continuing...">
              Continue
              <ArrowRight className="w-4 h-4 ml-2" />
            </FormSubmitButton>
          </Form>
        </div>
      )}

      {/* Step 2: Organization */}
      {currentStep === 1 && (
        <div className="space-y-6">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-semibold text-text-primary">
              Tell us about your organization
            </h2>
            <p className="text-text-secondary mt-2">
              This helps us customize your experience
            </p>
          </div>

          <Form form={organizationForm} onSubmit={handleOrganizationSubmit} className="space-y-5">
            <FormField name="companyName" label="Company Name" required>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                <Input
                  {...organizationForm.register("companyName", {
                    onChange: (e) => handleCompanyNameChange(e.target.value),
                  })}
                  placeholder="Acme Inc."
                  className="pl-10"
                  autoFocus
                />
              </div>
            </FormField>

            <FormField name="companySlug" label="Workspace URL" required>
              <div className="flex items-center">
                <span className="px-3 py-2 bg-surface-overlay border border-r-0 border-border rounded-l-lg text-text-muted text-sm">
                  app.dotmac.com/
                </span>
                <Input
                  {...organizationForm.register("companySlug")}
                  placeholder="acme"
                  className="rounded-l-none"
                />
              </div>
            </FormField>

            <div className="grid grid-cols-2 gap-4">
              <FormField name="industry" label="Industry">
                <select
                  {...organizationForm.register("industry")}
                  className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-inset"
                >
                  {industries.map((industry) => (
                    <option key={industry.value} value={industry.value}>
                      {industry.label}
                    </option>
                  ))}
                </select>
              </FormField>

              <FormField name="companySize" label="Company Size">
                <select
                  {...organizationForm.register("companySize")}
                  className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-inset"
                >
                  {companySizes.map((size) => (
                    <option key={size.value} value={size.value}>
                      {size.label}
                    </option>
                  ))}
                </select>
              </FormField>
            </div>

            <div className="flex gap-4 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={goBack}
                className="flex-1"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <FormSubmitButton className="flex-1" loadingText="Continuing...">
                Continue
                <ArrowRight className="w-4 h-4 ml-2" />
              </FormSubmitButton>
            </div>
          </Form>
        </div>
      )}

      {/* Step 3: Plan Selection */}
      {currentStep === 2 && (
        <div className="space-y-6">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-semibold text-text-primary">
              Choose your plan
            </h2>
            <p className="text-text-secondary mt-2">
              Start free and upgrade anytime
            </p>
          </div>

          <PlanSelector
            selectedPlan={selectedPlan}
            onPlanSelect={setSelectedPlan}
          />

          <div className="flex gap-4 pt-6">
            <Button
              type="button"
              variant="outline"
              onClick={goBack}
              className="flex-1"
              disabled={isSubmitting}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <Button
              onClick={handlePlanSubmit}
              className="flex-1 shadow-glow-sm hover:shadow-glow"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating account...
                </>
              ) : (
                <>
                  Create Account
                  <ArrowRight className="w-4 h-4 ml-2" />
                </>
              )}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
