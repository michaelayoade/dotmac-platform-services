"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, Building2, User, CreditCard, Link as LinkIcon } from "lucide-react";
import { Button, Card, Input, Select } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { createTenantSchema, tenantPlans, type CreateTenantData } from "@/lib/schemas/tenants";
import { useCreateTenant } from "@/lib/hooks/api/use-tenants";

export default function NewTenantPage() {
  const router = useRouter();
  const { toast } = useToast();
  const createTenant = useCreateTenant();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setValue,
    watch,
  } = useForm<CreateTenantData>({
    resolver: zodResolver(createTenantSchema),
    defaultValues: {
      name: "",
      slug: "",
      plan: "Starter",
      ownerEmail: "",
      ownerName: "",
    },
  });

  const selectedPlan = watch("plan");
  const name = watch("name");

  // Auto-generate slug from name
  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    const slug = value
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    setValue("slug", slug);
  };

  const onSubmit = async (data: CreateTenantData) => {
    try {
      const result = await createTenant.mutateAsync({
        name: data.name,
        slug: data.slug,
        plan: data.plan,
        ownerEmail: data.ownerEmail,
        ownerName: data.ownerName,
      });

      toast({
        title: "Tenant created",
        description: `${data.name} has been created successfully.`,
      });

      router.push(`/tenants/${result.id}`);
    } catch {
      toast({
        title: "Error",
        description: "Failed to create tenant. Please try again.",
        variant: "error",
      });
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="New Tenant"
        breadcrumbs={[{ label: "Tenants", href: "/tenants" }, { label: "New Tenant" }]}
        actions={
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        }
      />

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Organization Details */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <Building2 className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Organization Details</h3>
              <p className="text-sm text-text-muted">Basic information about the tenant</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Organization Name <span className="text-status-error">*</span>
              </label>
              <Input
                {...register("name", { onChange: handleNameChange })}
                placeholder="Acme Corporation"
                className={cn(errors.name && "border-status-error")}
              />
              {errors.name && (
                <p className="text-xs text-status-error mt-1">{errors.name.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                <LinkIcon className="w-4 h-4 inline mr-1" />
                Slug <span className="text-status-error">*</span>
              </label>
              <div className="flex items-center">
                <span className="text-sm text-text-muted mr-2">app.example.com/</span>
                <Input
                  {...register("slug")}
                  placeholder="acme-corp"
                  className={cn("flex-1", errors.slug && "border-status-error")}
                />
              </div>
              {errors.slug && (
                <p className="text-xs text-status-error mt-1">{errors.slug.message}</p>
              )}
              <p className="text-xs text-text-muted mt-1">
                Only lowercase letters, numbers, and hyphens
              </p>
            </div>
          </div>
        </Card>

        {/* Owner Information */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
              <User className="w-5 h-5 text-highlight" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Owner Account</h3>
              <p className="text-sm text-text-muted">
                The primary owner who will manage this tenant
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Owner Email <span className="text-status-error">*</span>
              </label>
              <Input
                {...register("ownerEmail")}
                type="email"
                placeholder="owner@example.com"
                className={cn(errors.ownerEmail && "border-status-error")}
              />
              {errors.ownerEmail && (
                <p className="text-xs text-status-error mt-1">{errors.ownerEmail.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Owner Name <span className="text-status-error">*</span>
              </label>
              <Input
                {...register("ownerName")}
                placeholder="John Doe"
                className={cn(errors.ownerName && "border-status-error")}
              />
              {errors.ownerName && (
                <p className="text-xs text-status-error mt-1">{errors.ownerName.message}</p>
              )}
            </div>
          </div>

          <p className="text-xs text-text-muted mt-4">
            An invitation will be sent to the owner&apos;s email with instructions to set up their
            account.
          </p>
        </Card>

        {/* Plan Selection */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
              <CreditCard className="w-5 h-5 text-status-success" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Subscription Plan</h3>
              <p className="text-sm text-text-muted">Select the plan for this tenant</p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Plan <span className="text-status-error">*</span>
            </label>
            <Select
              value={selectedPlan}
              onValueChange={(value) => setValue("plan", value as CreateTenantData["plan"])}
              options={tenantPlans.map((p) => ({ value: p.value, label: p.label }))}
              placeholder="Select plan"
            />
            {errors.plan && (
              <p className="text-xs text-status-error mt-1">{errors.plan.message}</p>
            )}

            <div className="mt-4 grid grid-cols-2 gap-4">
              {tenantPlans.map((plan) => (
                <div
                  key={plan.value}
                  className={cn(
                    "p-4 rounded-lg border cursor-pointer transition-colors",
                    selectedPlan === plan.value
                      ? "border-accent bg-accent-subtle"
                      : "border-border-default bg-surface-secondary hover:border-border-hover"
                  )}
                  onClick={() => setValue("plan", plan.value as CreateTenantData["plan"])}
                >
                  <h4 className="text-sm font-medium text-text-primary">{plan.label}</h4>
                  <p className="text-xs text-text-muted mt-1">
                    {plan.value === "Free" && "Basic features, limited users"}
                    {plan.value === "Starter" && "Essential features for small teams"}
                    {plan.value === "Professional" && "Advanced features for growing teams"}
                    {plan.value === "Enterprise" && "Full platform access, custom limits"}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </Card>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-4">
          <Button type="button" variant="ghost" onClick={() => router.back()}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting || createTenant.isPending}>
            {isSubmitting || createTenant.isPending ? "Creating..." : "Create Tenant"}
          </Button>
        </div>
      </form>
    </div>
  );
}
