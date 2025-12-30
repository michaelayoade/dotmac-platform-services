"use client";

import { use, useEffect, useState } from "react";
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
  Loader2,
} from "lucide-react";
import { Button, Card, Input, Select } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  updateContactSchema,
  contactStatuses,
  contactStages,
  type UpdateContactData,
} from "@/lib/schemas/contacts";
import { useContact, useUpdateContact } from "@/lib/hooks/api/use-contacts";

interface EditContactPageProps {
  params: Promise<{ id: string }>;
}

export default function EditContactPage({ params }: EditContactPageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();

  const { data: contact, isLoading } = useContact(id);
  const updateContact = useUpdateContact();

  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting, isDirty },
    setValue,
    watch,
    reset,
  } = useForm<UpdateContactData>({
    resolver: zodResolver(updateContactSchema),
  });

  const selectedStatus = watch("status");
  const selectedStage = watch("stage");

  // Populate form when contact loads
  useEffect(() => {
    if (contact) {
      reset({
        firstName: contact.firstName || "",
        lastName: contact.lastName || "",
        displayName: contact.displayName || "",
        email: contact.email || "",
        phone: contact.phone || "",
        company: contact.company || "",
        jobTitle: contact.jobTitle || "",
        department: contact.department || "",
        status: contact.status || "active",
        stage: contact.stage || "prospect",
        notes: contact.notes || "",
        isPrimary: contact.isPrimary || false,
        isDecisionMaker: contact.isDecisionMaker || false,
        isBillingContact: contact.isBillingContact || false,
        isTechnicalContact: contact.isTechnicalContact || false,
        preferredLanguage: contact.preferredLanguage || "",
        timezone: contact.timezone || "",
      });
      setTags(contact.tags || []);
    }
  }, [contact, reset]);

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

  const onSubmit = async (data: UpdateContactData) => {
    try {
      await updateContact.mutateAsync({
        id,
        data: {
          firstName: data.firstName,
          lastName: data.lastName || undefined,
          displayName:
            data.displayName || `${data.firstName} ${data.lastName || ""}`.trim() || undefined,
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
        },
      });

      toast({
        title: "Contact updated",
        description: "Changes have been saved successfully.",
      });

      router.push(`/contacts/${id}`);
    } catch {
      toast({
        title: "Error",
        description: "Failed to update contact. Please try again.",
        variant: "error",
      });
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    );
  }

  if (!contact) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <h2 className="text-xl font-semibold text-text-primary mb-2">Contact not found</h2>
        <p className="text-text-muted mb-6">
          The contact you&apos;re looking for doesn&apos;t exist.
        </p>
        <Button onClick={() => router.push("/contacts")}>Back to Contacts</Button>
      </div>
    );
  }

  const displayName =
    contact.displayName || `${contact.firstName} ${contact.lastName || ""}`.trim();

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title={`Edit ${displayName}`}
        breadcrumbs={[
          { label: "Contacts", href: "/contacts" },
          { label: displayName, href: `/contacts/${id}` },
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
                onValueChange={(value) =>
                  setValue("status", value as UpdateContactData["status"], { shouldDirty: true })
                }
                options={contactStatuses.map((s) => ({ value: s.value, label: s.label }))}
                placeholder="Select status"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Stage</label>
              <Select
                value={selectedStage}
                onValueChange={(value) =>
                  setValue("stage", value as UpdateContactData["stage"], { shouldDirty: true })
                }
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
              disabled={!isDirty || isSubmitting || updateContact.isPending}
            >
              {isSubmitting || updateContact.isPending ? "Saving..." : "Save Changes"}
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
