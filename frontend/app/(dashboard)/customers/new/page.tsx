"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, User, Building2, Mail, Phone, MapPin, Tag, Plus, X } from "lucide-react";
import { Button, Card, Input, Select } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { createCustomerSchema, type CreateCustomerData } from "@/lib/schemas";
import { useCreateCustomer } from "@/lib/hooks/api/use-customers";
import { useState } from "react";

const customerTypes = [
  { value: "individual", label: "Individual" },
  { value: "business", label: "Business" },
  { value: "enterprise", label: "Enterprise" },
];

export default function NewCustomerPage() {
  const router = useRouter();
  const { toast } = useToast();
  const createCustomer = useCreateCustomer();

  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");
  const [showAddressFields, setShowAddressFields] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setValue,
    watch,
  } = useForm<CreateCustomerData>({
    resolver: zodResolver(createCustomerSchema),
    defaultValues: {
      name: "",
      email: "",
      phone: "",
      company: "",
      type: "individual",
      tags: [],
    },
  });

  const selectedType = watch("type");

  const handleAddTag = () => {
    if (!tagInput.trim()) return;
    const newTags = [...tags, tagInput.trim()];
    setTags(newTags);
    setValue("tags", newTags);
    setTagInput("");
  };

  const handleRemoveTag = (tagToRemove: string) => {
    const newTags = tags.filter((t) => t !== tagToRemove);
    setTags(newTags);
    setValue("tags", newTags);
  };

  const onSubmit = async (data: CreateCustomerData) => {
    try {
      const result = await createCustomer.mutateAsync({
        name: data.name,
        email: data.email,
        phone: data.phone,
        company: data.company,
        type: data.type,
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
      });

      toast({
        title: "Customer created",
        description: `${data.name} has been added successfully.`,
      });

      router.push(`/customers/${result.id}`);
    } catch {
      toast({
        title: "Error",
        description: "Failed to create customer. Please try again.",
        variant: "error",
      });
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="New Customer"
        breadcrumbs={[
          { label: "Customers", href: "/customers" },
          { label: "New Customer" },
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
                Customer Type <span className="text-status-error">*</span>
              </label>
              <Select
                value={selectedType}
                onValueChange={(value) => setValue("type", value as CreateCustomerData["type"])}
                options={customerTypes}
                placeholder="Select type"
              />
              {errors.type && (
                <p className="text-xs text-status-error mt-1">{errors.type.message}</p>
              )}
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
                <p className="text-sm text-text-muted">Optional address for invoices</p>
              </div>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setShowAddressFields(!showAddressFields)}
            >
              {showAddressFields ? "Hide" : "Add Address"}
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
              <p className="text-sm text-text-muted">No tags added yet</p>
            )}
          </div>
        </Card>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-4">
          <Button type="button" variant="ghost" onClick={() => router.back()}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting || createCustomer.isPending}>
            {isSubmitting || createCustomer.isPending ? "Creating..." : "Create Customer"}
          </Button>
        </div>
      </form>
    </div>
  );
}
