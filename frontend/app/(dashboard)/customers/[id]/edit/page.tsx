"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, User, Building2, Mail, Phone, MapPin, Tag, Plus, X, Shield } from "lucide-react";
import { Button, Card, Input, Select } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { updateCustomerSchema, type UpdateCustomerData } from "@/lib/schemas";
import { useCustomer, useUpdateCustomer } from "@/lib/hooks/api/use-customers";

interface EditCustomerPageProps {
  params: Promise<{ id: string }>;
}

const customerTypes = [
  { value: "individual", label: "Individual" },
  { value: "business", label: "Business" },
  { value: "enterprise", label: "Enterprise" },
];

const customerStatuses = [
  { value: "active", label: "Active" },
  { value: "inactive", label: "Inactive" },
  { value: "prospect", label: "Prospect" },
  { value: "lead", label: "Lead" },
  { value: "churned", label: "Churned" },
];

export default function EditCustomerPage({ params }: EditCustomerPageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();

  const { data: customer, isLoading, error } = useCustomer(id);
  const updateCustomer = useUpdateCustomer();

  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");
  const [showAddressFields, setShowAddressFields] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting, isDirty },
    setValue,
    watch,
    reset,
  } = useForm<UpdateCustomerData>({
    resolver: zodResolver(updateCustomerSchema),
  });

  const selectedType = watch("type");
  const selectedStatus = watch("status");

  // Populate form when customer data loads
  useEffect(() => {
    if (customer) {
      reset({
        name: customer.name,
        email: customer.email,
        phone: customer.phone || "",
        company: customer.company || "",
        type: customer.type,
        status: customer.status,
        billingAddress: customer.billingAddress,
      });
      setTags(customer.tags || []);
      setShowAddressFields(!!customer.billingAddress);
    }
  }, [customer, reset]);

  const handleAddTag = () => {
    if (!tagInput.trim()) return;
    const newTags = [...tags, tagInput.trim()];
    setTags(newTags);
    setValue("tags", newTags, { shouldDirty: true });
    setTagInput("");
  };

  const handleRemoveTag = (tagToRemove: string) => {
    const newTags = tags.filter((t) => t !== tagToRemove);
    setTags(newTags);
    setValue("tags", newTags, { shouldDirty: true });
  };

  const onSubmit = async (data: UpdateCustomerData) => {
    try {
      await updateCustomer.mutateAsync({
        id,
        data: {
          name: data.name,
          email: data.email,
          phone: data.phone,
          company: data.company,
          type: data.type,
          status: data.status,
          tags: tags,
          address: data.billingAddress
            ? {
                line1: data.billingAddress.line1,
                line2: data.billingAddress.line2,
                city: data.billingAddress.city,
                state: data.billingAddress.state,
                postalCode: data.billingAddress.postalCode,
                country: data.billingAddress.country,
              }
            : undefined,
        },
      });

      toast({
        title: "Customer updated",
        description: "Changes have been saved successfully.",
      });

      router.push(`/customers/${id}`);
    } catch {
      toast({
        title: "Error",
        description: "Failed to update customer. Please try again.",
        variant: "error",
      });
    }
  };

  if (isLoading) {
    return <EditCustomerSkeleton />;
  }

  if (error || !customer) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <h2 className="text-xl font-semibold text-text-primary mb-2">Customer not found</h2>
        <p className="text-text-muted mb-6">Unable to load customer data.</p>
        <Button onClick={() => router.push("/customers")}>Back to Customers</Button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title={`Edit ${customer.name}`}
        breadcrumbs={[
          { label: "Customers", href: "/customers" },
          { label: customer.name, href: `/customers/${id}` },
          { label: "Edit" },
        ]}
        actions={
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        }
      />

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Status */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
              <Shield className="w-5 h-5 text-status-info" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Status</h3>
              <p className="text-sm text-text-muted">Customer account status</p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Account Status
            </label>
            <Select
              value={selectedStatus}
              onValueChange={(value) => setValue("status", value as UpdateCustomerData["status"], { shouldDirty: true })}
              options={customerStatuses}
              placeholder="Select status"
            />
          </div>
        </Card>

        {/* Basic Information */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <User className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Basic Information</h3>
              <p className="text-sm text-text-muted">Customer name and contact details</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Full Name <span className="text-status-error">*</span>
              </label>
              <Input
                {...register("name")}
                placeholder="Enter customer name"
                className={cn(errors.name && "border-status-error")}
              />
              {errors.name && (
                <p className="text-xs text-status-error mt-1">{errors.name.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                <Mail className="w-4 h-4 inline mr-1" />
                Email <span className="text-status-error">*</span>
              </label>
              <Input
                {...register("email")}
                type="email"
                placeholder="customer@example.com"
                className={cn(errors.email && "border-status-error")}
              />
              {errors.email && (
                <p className="text-xs text-status-error mt-1">{errors.email.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                <Phone className="w-4 h-4 inline mr-1" />
                Phone
              </label>
              <Input {...register("phone")} type="tel" placeholder="+1 (555) 000-0000" />
            </div>
          </div>
        </Card>

        {/* Business Information */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
              <Building2 className="w-5 h-5 text-highlight" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Business Information</h3>
              <p className="text-sm text-text-muted">Company and customer type</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Customer Type
              </label>
            <Select
              value={selectedType}
              onValueChange={(value) => setValue("type", value as UpdateCustomerData["type"], { shouldDirty: true })}
              options={customerTypes}
              placeholder="Select type"
            />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Company Name
              </label>
              <Input {...register("company")} placeholder="Acme Inc." />
            </div>
          </div>
        </Card>

        {/* Billing Address */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
                <MapPin className="w-5 h-5 text-status-info" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-text-primary">Billing Address</h3>
                <p className="text-sm text-text-muted">Address for invoices</p>
              </div>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setShowAddressFields(!showAddressFields)}
            >
              {showAddressFields ? "Hide" : "Show Address"}
            </Button>
          </div>

          {showAddressFields && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-text-primary mb-1.5">
                  Address Line 1
                </label>
                <Input {...register("billingAddress.line1")} placeholder="123 Main Street" />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-text-primary mb-1.5">
                  Address Line 2
                </label>
                <Input {...register("billingAddress.line2")} placeholder="Suite 100 (optional)" />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">City</label>
                <Input {...register("billingAddress.city")} placeholder="San Francisco" />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">
                  State / Province
                </label>
                <Input {...register("billingAddress.state")} placeholder="CA" />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">
                  Postal Code
                </label>
                <Input {...register("billingAddress.postalCode")} placeholder="94102" />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">Country</label>
                <Input {...register("billingAddress.country")} placeholder="United States" />
              </div>
            </div>
          )}
        </Card>

        {/* Tags */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
              <Tag className="w-5 h-5 text-status-success" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Tags</h3>
              <p className="text-sm text-text-muted">Organize with custom labels</p>
            </div>
          </div>

          <div className="flex items-center gap-2 mb-4">
            <Input
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              placeholder="Add a tag..."
              onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), handleAddTag())}
            />
            <Button type="button" variant="outline" onClick={handleAddTag}>
              <Plus className="w-4 h-4" />
            </Button>
          </div>

          <div className="flex flex-wrap gap-2">
            {tags.length > 0 ? (
              tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm bg-surface-overlay text-text-secondary"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => handleRemoveTag(tag)}
                    className="hover:text-status-error transition-colors"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))
            ) : (
              <p className="text-sm text-text-muted">No tags</p>
            )}
          </div>
        </Card>

        {/* Actions */}
        <div className="flex items-center justify-between pt-4">
          <p className="text-sm text-text-muted">
            {isDirty ? "You have unsaved changes" : "No changes made"}
          </p>
          <div className="flex items-center gap-3">
            <Button type="button" variant="ghost" onClick={() => router.back()}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting || updateCustomer.isPending || !isDirty}
            >
              {isSubmitting || updateCustomer.isPending ? "Saving..." : "Save Changes"}
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}

function EditCustomerSkeleton() {
  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-pulse">
      <div>
        <div className="h-4 w-32 bg-surface-overlay rounded mb-2" />
        <div className="h-8 w-64 bg-surface-overlay rounded" />
      </div>

      {[1, 2, 3].map((i) => (
        <div key={i} className="card p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-surface-overlay rounded-lg" />
            <div>
              <div className="h-5 w-40 bg-surface-overlay rounded mb-1" />
              <div className="h-3 w-56 bg-surface-overlay rounded" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="h-4 w-20 bg-surface-overlay rounded mb-2" />
              <div className="h-10 bg-surface-overlay rounded" />
            </div>
            <div>
              <div className="h-4 w-20 bg-surface-overlay rounded mb-2" />
              <div className="h-10 bg-surface-overlay rounded" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
