"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  ArrowLeft,
  User,
  Building2,
  Mail,
  Phone,
  Briefcase,
  Tag,
  Plus,
  X,
  Settings2,
} from "lucide-react";
import { Button, Card, Input, Select } from "@dotmac/core";
import { useToast } from "@dotmac/core";
import { useState } from "react";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  createContactSchema,
  contactStatuses,
  contactStages,
  type CreateContactData,
} from "@/lib/schemas/contacts";
import { useCreateContact } from "@/lib/hooks/api/use-contacts";

export default function NewContactPage() {
  const router = useRouter();
  const { toast } = useToast();
  const createContact = useCreateContact();

  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setValue,
    watch,
  } = useForm<CreateContactData>({
    resolver: zodResolver(createContactSchema),
    defaultValues: {
      firstName: "",
      lastName: "",
      email: "",
      phone: "",
      company: "",
      jobTitle: "",
      department: "",
      status: "active",
      stage: "prospect",
      notes: "",
      tags: [],
      isPrimary: false,
      isDecisionMaker: false,
      isBillingContact: false,
      isTechnicalContact: false,
    },
  });

  const selectedStatus = watch("status");
  const selectedStage = watch("stage");

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

  const onSubmit = async (data: CreateContactData) => {
    try {
      const result = await createContact.mutateAsync({
        firstName: data.firstName,
        lastName: data.lastName,
        displayName: data.displayName || `${data.firstName} ${data.lastName || ""}`.trim(),
        email: data.email || undefined,
        phone: data.phone || undefined,
        company: data.company || undefined,
        jobTitle: data.jobTitle || undefined,
        department: data.department || undefined,
        status: data.status,
        stage: data.stage,
        notes: data.notes || undefined,
        tags: tags,
        isPrimary: data.isPrimary,
        isDecisionMaker: data.isDecisionMaker,
        isBillingContact: data.isBillingContact,
        isTechnicalContact: data.isTechnicalContact,
        preferredLanguage: data.preferredLanguage || undefined,
        timezone: data.timezone || undefined,
      });

      toast({
        title: "Contact created",
        description: `${data.firstName} ${data.lastName || ""} has been added successfully.`,
      });

      router.push(`/contacts/${result.id}`);
    } catch {
      toast({
        title: "Error",
        description: "Failed to create contact. Please try again.",
        variant: "error",
      });
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="New Contact"
        breadcrumbs={[{ label: "Contacts", href: "/contacts" }, { label: "New Contact" }]}
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
              <p className="text-sm text-text-muted">Contact name and identity</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                First Name <span className="text-status-error">*</span>
              </label>
              <Input
                {...register("firstName")}
                placeholder="John"
                className={cn(errors.firstName && "border-status-error")}
              />
              {errors.firstName && (
                <p className="text-xs text-status-error mt-1">{errors.firstName.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Last Name
              </label>
              <Input {...register("lastName")} placeholder="Doe" />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                <Mail className="w-4 h-4 inline mr-1" />
                Email
              </label>
              <Input
                {...register("email")}
                type="email"
                placeholder="john@example.com"
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
              <p className="text-sm text-text-muted">Company and role details</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Company</label>
              <Input {...register("company")} placeholder="Acme Inc." />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                <Briefcase className="w-4 h-4 inline mr-1" />
                Job Title
              </label>
              <Input {...register("jobTitle")} placeholder="Product Manager" />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Department
              </label>
              <Input {...register("department")} placeholder="Engineering" />
            </div>
          </div>
        </Card>

        {/* Status & Classification */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
              <Settings2 className="w-5 h-5 text-status-info" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Status & Classification</h3>
              <p className="text-sm text-text-muted">Contact status and pipeline stage</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Status</label>
              <Select
                value={selectedStatus}
                onValueChange={(value) => setValue("status", value as CreateContactData["status"])}
                options={contactStatuses.map((s) => ({ value: s.value, label: s.label }))}
                placeholder="Select status"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Stage</label>
              <Select
                value={selectedStage}
                onValueChange={(value) => setValue("stage", value as CreateContactData["stage"])}
                options={contactStages.map((s) => ({ value: s.value, label: s.label }))}
                placeholder="Select stage"
              />
            </div>
          </div>

          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
            <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
              <input type="checkbox" {...register("isPrimary")} className="rounded" />
              Primary Contact
            </label>
            <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
              <input type="checkbox" {...register("isDecisionMaker")} className="rounded" />
              Decision Maker
            </label>
            <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
              <input type="checkbox" {...register("isBillingContact")} className="rounded" />
              Billing Contact
            </label>
            <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
              <input type="checkbox" {...register("isTechnicalContact")} className="rounded" />
              Technical Contact
            </label>
          </div>
        </Card>

        {/* Notes */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-surface-overlay flex items-center justify-center">
              <Briefcase className="w-5 h-5 text-text-muted" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Notes</h3>
              <p className="text-sm text-text-muted">Additional information</p>
            </div>
          </div>

          <textarea
            {...register("notes")}
            rows={4}
            placeholder="Add any notes about this contact..."
            className="w-full px-3 py-2 rounded-lg border border-border-default bg-surface-primary text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent resize-none"
          />
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
          <Button type="submit" disabled={isSubmitting || createContact.isPending}>
            {isSubmitting || createContact.isPending ? "Creating..." : "Create Contact"}
          </Button>
        </div>
      </form>
    </div>
  );
}
