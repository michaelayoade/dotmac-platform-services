"use client";

import { use, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Mail,
  Phone,
  Building2,
  Briefcase,
  Calendar,
  Edit3,
  Trash2,
  Tag,
  Plus,
  X,
  RefreshCcw,
  FileText,
  MessageSquare,
  Clock,
  User,
  CheckCircle2,
} from "lucide-react";
import { format } from "date-fns";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { ConfirmDialog, useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  ActivityTimeline,
  getActivityIcon,
  type ActivityItem,
} from "@/components/shared/activity-timeline";
import {
  useContact,
  useDeleteContact,
  useContactActivities,
  useAddContactTag,
  useRemoveContactTag,
} from "@/lib/hooks/api/use-contacts";

interface ContactDetailPageProps {
  params: Promise<{ id: string }>;
}

const statusColors: Record<string, { bg: string; text: string; dot: string }> = {
  active: { bg: "bg-status-success/15", text: "text-status-success", dot: "bg-status-success" },
  inactive: { bg: "bg-surface-overlay", text: "text-text-muted", dot: "bg-text-muted" },
  archived: { bg: "bg-status-warning/15", text: "text-status-warning", dot: "bg-status-warning" },
  blocked: { bg: "bg-status-error/15", text: "text-status-error", dot: "bg-status-error" },
  pending: { bg: "bg-status-info/15", text: "text-status-info", dot: "bg-status-info" },
};

const stageLabels: Record<string, string> = {
  prospect: "Prospect",
  lead: "Lead",
  opportunity: "Opportunity",
  account: "Account",
  partner: "Partner",
  vendor: "Vendor",
  other: "Other",
};

export default function ContactDetailPage({ params }: ContactDetailPageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  const [newTag, setNewTag] = useState("");
  const [showTagInput, setShowTagInput] = useState(false);

  // Data fetching
  const { data: contact, isLoading, error, refetch } = useContact(id);
  const { data: activities } = useContactActivities(id);

  // Mutations
  const deleteContact = useDeleteContact();
  const addTag = useAddContactTag();
  const removeTag = useRemoveContactTag();

  const handleDelete = async () => {
    const displayName =
      contact?.displayName || `${contact?.firstName} ${contact?.lastName || ""}`.trim();
    const confirmed = await confirm({
      title: "Delete Contact",
      description: `Are you sure you want to delete "${displayName}"? This action cannot be undone.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deleteContact.mutateAsync(id);
        toast({
          title: "Contact deleted",
          description: "The contact has been successfully deleted.",
        });
        router.push("/contacts");
      } catch {
        toast({
          title: "Error",
          description: "Failed to delete contact. Please try again.",
          variant: "error",
        });
      }
    }
  };

  const handleAddTag = async () => {
    if (!newTag.trim()) return;

    try {
      await addTag.mutateAsync({ contactId: id, tag: newTag.trim() });
      setNewTag("");
      setShowTagInput(false);
      toast({ title: "Tag added" });
    } catch {
      toast({ title: "Failed to add tag", variant: "error" });
    }
  };

  const handleRemoveTag = async (tag: string) => {
    try {
      await removeTag.mutateAsync({ contactId: id, tag });
      toast({ title: "Tag removed" });
    } catch {
      toast({ title: "Failed to remove tag", variant: "error" });
    }
  };

  // Loading state
  if (isLoading) {
    return <ContactDetailSkeleton />;
  }

  // Error state
  if (error || !contact) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="text-status-error mb-4">
          <FileText className="w-12 h-12" />
        </div>
        <h2 className="text-xl font-semibold text-text-primary mb-2">Contact not found</h2>
        <p className="text-text-muted mb-6">
          The contact you&apos;re looking for doesn&apos;t exist or you don&apos;t have access.
        </p>
        <Button onClick={() => router.push("/contacts")}>Back to Contacts</Button>
      </div>
    );
  }

  const displayName =
    contact.displayName || `${contact.firstName} ${contact.lastName || ""}`.trim();
  const status = statusColors[contact.status || "active"] || statusColors.active;

  // Map activities to ActivityItem format
  const activityItems: ActivityItem[] =
    activities?.map((activity) => ({
      id: activity.id,
      type: activity.activityType,
      title: activity.subject,
      description: activity.description || undefined,
      timestamp: activity.activityDate || activity.createdAt,
      ...getActivityIcon(activity.activityType),
    })) || [];


  return (
    <div className="space-y-8 animate-fade-up">
      {dialog}

      {/* Page Header */}
      <PageHeader
        title={displayName}
        breadcrumbs={[{ label: "Contacts", href: "/contacts" }, { label: displayName }]}
        badge={
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium",
                status.bg,
                status.text
              )}
            >
              <span className={cn("w-1.5 h-1.5 rounded-full", status.dot)} />
              {(contact.status || "active").charAt(0).toUpperCase() +
                (contact.status || "active").slice(1)}
            </span>
            {contact.stage && (
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-surface-overlay text-text-secondary">
                {stageLabels[contact.stage] || contact.stage}
              </span>
            )}
          </div>
        }
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => refetch()}>
              <RefreshCcw className="w-4 h-4" />
            </Button>
            <Button variant="outline" onClick={() => router.push(`/contacts/${id}/edit`)}>
              <Edit3 className="w-4 h-4 mr-2" />
              Edit
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </Button>
          </div>
        }
      />

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Contact Information */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Contact Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {(contact.email || contact.contactMethods?.find((m) => m.type === "email")) && (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
                    <Mail className="w-5 h-5 text-accent" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Email</p>
                    <a
                      href={`mailto:${contact.email || contact.contactMethods?.find((m) => m.type === "email")?.value}`}
                      className="text-sm text-accent hover:underline"
                    >
                      {contact.email ||
                        contact.contactMethods?.find((m) => m.type === "email")?.value}
                    </a>
                  </div>
                </div>
              )}

              {(contact.phone || contact.contactMethods?.find((m) => m.type === "phone")) && (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
                    <Phone className="w-5 h-5 text-status-success" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Phone</p>
                    <a
                      href={`tel:${contact.phone || contact.contactMethods?.find((m) => m.type === "phone")?.value}`}
                      className="text-sm text-text-primary hover:text-accent"
                    >
                      {contact.phone ||
                        contact.contactMethods?.find((m) => m.type === "phone")?.value}
                    </a>
                  </div>
                </div>
              )}

              {contact.company && (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
                    <Building2 className="w-5 h-5 text-highlight" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Company</p>
                    <p className="text-sm text-text-primary">{contact.company}</p>
                  </div>
                </div>
              )}

              {contact.jobTitle && (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
                    <Briefcase className="w-5 h-5 text-status-info" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Job Title</p>
                    <p className="text-sm text-text-primary">{contact.jobTitle}</p>
                  </div>
                </div>
              )}

              {contact.department && (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-surface-overlay flex items-center justify-center">
                    <User className="w-5 h-5 text-text-muted" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Department</p>
                    <p className="text-sm text-text-primary">{contact.department}</p>
                  </div>
                </div>
              )}

              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-surface-overlay flex items-center justify-center">
                  <Calendar className="w-5 h-5 text-text-muted" />
                </div>
                <div>
                  <p className="text-xs text-text-muted">Created</p>
                  <p className="text-sm text-text-primary">
                    {format(new Date(contact.createdAt), "MMM d, yyyy")}
                  </p>
                </div>
              </div>
            </div>
          </Card>

          {/* Contact Roles */}
          {(contact.isPrimary ||
            contact.isDecisionMaker ||
            contact.isBillingContact ||
            contact.isTechnicalContact) && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-text-primary mb-4">Contact Roles</h3>
              <div className="flex flex-wrap gap-2">
                {contact.isPrimary && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm bg-accent-subtle text-accent">
                    <CheckCircle2 className="w-3 h-3" />
                    Primary Contact
                  </span>
                )}
                {contact.isDecisionMaker && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm bg-highlight-subtle text-highlight">
                    <CheckCircle2 className="w-3 h-3" />
                    Decision Maker
                  </span>
                )}
                {contact.isBillingContact && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm bg-status-success/15 text-status-success">
                    <CheckCircle2 className="w-3 h-3" />
                    Billing Contact
                  </span>
                )}
                {contact.isTechnicalContact && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm bg-status-info/15 text-status-info">
                    <CheckCircle2 className="w-3 h-3" />
                    Technical Contact
                  </span>
                )}
              </div>
            </Card>
          )}

          {/* Notes */}
          {contact.notes && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-text-primary mb-4">Notes</h3>
              <p className="text-sm text-text-secondary whitespace-pre-wrap">{contact.notes}</p>
            </Card>
          )}

          {/* Tags */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">Tags</h3>
              {!showTagInput && (
                <Button variant="ghost" size="sm" onClick={() => setShowTagInput(true)}>
                  <Plus className="w-4 h-4 mr-1" />
                  Add Tag
                </Button>
              )}
            </div>

            {showTagInput && (
              <div className="flex items-center gap-2 mb-4">
                <Input
                  placeholder="Enter tag name..."
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAddTag()}
                  className="flex-1"
                />
                <Button size="sm" onClick={handleAddTag} disabled={!newTag.trim() || addTag.isPending}>
                  Add
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setShowTagInput(false)}>
                  <X className="w-4 h-4" />
                </Button>
              </div>
            )}

            <div className="flex flex-wrap gap-2">
              {contact.tags && contact.tags.length > 0 ? (
                contact.tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm bg-surface-overlay text-text-secondary group"
                  >
                    <Tag className="w-3 h-3" />
                    {tag}
                    <button
                      onClick={() => handleRemoveTag(tag)}
                      className="ml-1 opacity-0 group-hover:opacity-100 transition-opacity hover:text-status-error"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))
              ) : (
                <p className="text-sm text-text-muted">No tags assigned</p>
              )}
            </div>
          </Card>

          {/* Activity Timeline */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">Recent Activity</h3>
              <Button variant="ghost" size="sm">
                View All
              </Button>
            </div>
            <ActivityTimeline activities={activityItems} maxItems={5} />
          </Card>
        </div>

        {/* Right Column - Quick Info & Actions */}
        <div className="space-y-6">
          {/* Quick Info */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Quick Info</h3>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
                  <User className="w-5 h-5 text-accent" />
                </div>
                <div>
                  <p className="text-xs text-text-muted">Stage</p>
                  <p className="text-sm font-medium text-text-primary">
                    {stageLabels[contact.stage || "other"] || "Other"}
                  </p>
                </div>
              </div>

              {contact.lastContactedAt && (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
                    <Clock className="w-5 h-5 text-status-info" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Last Contacted</p>
                    <p className="text-sm font-medium text-text-primary">
                      {format(new Date(contact.lastContactedAt), "MMM d, yyyy")}
                    </p>
                  </div>
                </div>
              )}

              {contact.preferredLanguage && (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-surface-overlay flex items-center justify-center">
                    <MessageSquare className="w-5 h-5 text-text-muted" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Preferred Language</p>
                    <p className="text-sm font-medium text-text-primary">
                      {contact.preferredLanguage}
                    </p>
                  </div>
                </div>
              )}

              {contact.timezone && (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-surface-overlay flex items-center justify-center">
                    <Clock className="w-5 h-5 text-text-muted" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Timezone</p>
                    <p className="text-sm font-medium text-text-primary">{contact.timezone}</p>
                  </div>
                </div>
              )}
            </div>
          </Card>

          {/* Quick Actions */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Quick Actions</h3>
            <div className="space-y-2">
              {contact.email && (
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => window.open(`mailto:${contact.email}`, "_blank")}
                >
                  <Mail className="w-4 h-4 mr-2" />
                  Send Email
                </Button>
              )}
              {contact.phone && (
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => window.open(`tel:${contact.phone}`, "_blank")}
                >
                  <Phone className="w-4 h-4 mr-2" />
                  Call
                </Button>
              )}
              <Button variant="outline" className="w-full justify-start">
                <MessageSquare className="w-4 h-4 mr-2" />
                Log Activity
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <FileText className="w-4 h-4 mr-2" />
                Add Note
              </Button>
            </div>
          </Card>

          {/* Custom Fields */}
          {contact.customFields && Object.keys(contact.customFields).length > 0 && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-text-primary mb-4">Custom Fields</h3>
              <div className="space-y-2">
                {Object.entries(contact.customFields).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-sm">
                    <span className="text-text-muted">{key}</span>
                    <span className="text-text-primary font-mono">{String(value)}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

// Loading skeleton
function ContactDetailSkeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div>
          <div className="h-4 w-32 bg-surface-overlay rounded mb-2" />
          <div className="h-8 w-64 bg-surface-overlay rounded" />
        </div>
        <div className="flex gap-2">
          <div className="h-10 w-24 bg-surface-overlay rounded" />
          <div className="h-10 w-24 bg-surface-overlay rounded" />
        </div>
      </div>

      {/* Content skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <div className="h-6 w-40 bg-surface-overlay rounded mb-4" />
            <div className="grid grid-cols-2 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-surface-overlay rounded-lg" />
                  <div>
                    <div className="h-3 w-16 bg-surface-overlay rounded mb-1" />
                    <div className="h-4 w-32 bg-surface-overlay rounded" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="card p-6">
            <div className="h-6 w-32 bg-surface-overlay rounded mb-4" />
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-surface-overlay rounded-lg" />
                  <div>
                    <div className="h-3 w-20 bg-surface-overlay rounded mb-1" />
                    <div className="h-5 w-24 bg-surface-overlay rounded" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
