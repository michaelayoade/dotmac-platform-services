"use client";

import { use } from "react";
import { useRouter } from "next/navigation";
import {
  Mail,
  Phone,
  Building2,
  MapPin,
  Calendar,
  DollarSign,
  Receipt,
  TrendingUp,
  Heart,
  Edit3,
  Trash2,
  Tag,
  Plus,
  X,
  MessageSquare,
  CreditCard,
  FileText,
  RefreshCcw,
} from "lucide-react";
import { format } from "date-fns";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { ConfirmDialog, useConfirmDialog } from "@/components/shared/confirm-dialog";
import { ActivityTimeline, getActivityIcon, type ActivityItem } from "@/components/shared/activity-timeline";
import {
  useCustomer,
  useDeleteCustomer,
  useCustomerMetrics,
  useAddCustomerTag,
  useRemoveCustomerTag,
} from "@/lib/hooks/api/use-customers";
import { useState } from "react";

interface CustomerDetailPageProps {
  params: Promise<{ id: string }>;
}

const statusColors: Record<string, { bg: string; text: string; dot: string }> = {
  active: { bg: "bg-status-success/15", text: "text-status-success", dot: "bg-status-success" },
  inactive: { bg: "bg-surface-overlay", text: "text-text-muted", dot: "bg-text-muted" },
  churned: { bg: "bg-status-error/15", text: "text-status-error", dot: "bg-status-error" },
  lead: { bg: "bg-status-info/15", text: "text-status-info", dot: "bg-status-info" },
};

const typeLabels: Record<string, string> = {
  individual: "Individual",
  business: "Business",
  enterprise: "Enterprise",
};

export default function CustomerDetailPage({ params }: CustomerDetailPageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  const [newTag, setNewTag] = useState("");
  const [showTagInput, setShowTagInput] = useState(false);

  // Data fetching
  const { data: customer, isLoading, error, refetch } = useCustomer(id);
  const { data: metrics, isLoading: metricsLoading } = useCustomerMetrics(id);

  // Mutations
  const deleteCustomer = useDeleteCustomer();
  const addTag = useAddCustomerTag();
  const removeTag = useRemoveCustomerTag();

  const handleDelete = async () => {
    const confirmed = await confirm({
      title: "Delete Customer",
      description: `Are you sure you want to delete "${customer?.name}"? This action cannot be undone and will remove all associated data.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deleteCustomer.mutateAsync(id);
        toast({
          title: "Customer deleted",
          description: "The customer has been successfully deleted.",
        });
        router.push("/customers");
      } catch {
        toast({
          title: "Error",
          description: "Failed to delete customer. Please try again.",
          variant: "error",
        });
      }
    }
  };

  const handleAddTag = async () => {
    if (!newTag.trim()) return;

    try {
      await addTag.mutateAsync({ id, tag: newTag.trim() });
      setNewTag("");
      setShowTagInput(false);
      toast({ title: "Tag added" });
    } catch {
      toast({ title: "Failed to add tag", variant: "error" });
    }
  };

  const handleRemoveTag = async (tag: string) => {
    try {
      await removeTag.mutateAsync({ id, tag });
      toast({ title: "Tag removed" });
    } catch {
      toast({ title: "Failed to remove tag", variant: "error" });
    }
  };

  // Loading state
  if (isLoading) {
    return <CustomerDetailSkeleton />;
  }

  // Error state
  if (error || !customer) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="text-status-error mb-4">
          <FileText className="w-12 h-12" />
        </div>
        <h2 className="text-xl font-semibold text-text-primary mb-2">Customer not found</h2>
        <p className="text-text-muted mb-6">
          The customer you&apos;re looking for doesn&apos;t exist or you don&apos;t have access.
        </p>
        <Button onClick={() => router.push("/customers")}>Back to Customers</Button>
      </div>
    );
  }

  const status = statusColors[customer.status] || statusColors.inactive;

  // Mock activity data (would come from useCustomerActivity hook)
  const activities: ActivityItem[] = [
    {
      id: "1",
      type: "payment",
      title: "Payment received",
      description: "$1,250.00 for Invoice #INV-2024-001",
      timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      ...getActivityIcon("payment"),
    },
    {
      id: "2",
      type: "invoice",
      title: "Invoice created",
      description: "Invoice #INV-2024-002 for $890.00",
      timestamp: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      ...getActivityIcon("invoice"),
    },
    {
      id: "3",
      type: "support",
      title: "Support ticket opened",
      description: "Billing inquiry - Ticket #TKT-789",
      timestamp: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      ...getActivityIcon("support"),
    },
    {
      id: "4",
      type: "update",
      title: "Customer updated",
      description: "Status changed to Active",
      timestamp: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
      ...getActivityIcon("update"),
    },
  ];

  return (
    <div className="space-y-8 animate-fade-up">
      {dialog}

      {/* Page Header */}
      <PageHeader
        title={customer.name}
        breadcrumbs={[
          { label: "Customers", href: "/customers" },
          { label: customer.name },
        ]}
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
              {customer.status.charAt(0).toUpperCase() + customer.status.slice(1)}
            </span>
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-surface-overlay text-text-secondary">
              {typeLabels[customer.type]}
            </span>
          </div>
        }
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => refetch()}>
              <RefreshCcw className="w-4 h-4" />
            </Button>
            <Button variant="outline" onClick={() => router.push(`/customers/${id}/edit`)}>
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
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
                  <Mail className="w-5 h-5 text-accent" />
                </div>
                <div>
                  <p className="text-xs text-text-muted">Email</p>
                  <a href={`mailto:${customer.email}`} className="text-sm text-accent hover:underline">
                    {customer.email}
                  </a>
                </div>
              </div>

              {customer.phone && (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
                    <Phone className="w-5 h-5 text-status-success" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Phone</p>
                    <a href={`tel:${customer.phone}`} className="text-sm text-text-primary hover:text-accent">
                      {customer.phone}
                    </a>
                  </div>
                </div>
              )}

              {customer.company && (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
                    <Building2 className="w-5 h-5 text-highlight" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Company</p>
                    <p className="text-sm text-text-primary">{customer.company}</p>
                  </div>
                </div>
              )}

              {customer.billingAddress && (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
                    <MapPin className="w-5 h-5 text-status-info" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Address</p>
                    <p className="text-sm text-text-primary">
                      {customer.billingAddress.city}, {customer.billingAddress.country}
                    </p>
                  </div>
                </div>
              )}

              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-surface-overlay flex items-center justify-center">
                  <Calendar className="w-5 h-5 text-text-muted" />
                </div>
                <div>
                  <p className="text-xs text-text-muted">Customer Since</p>
                  <p className="text-sm text-text-primary">
                    {format(new Date(customer.createdAt), "MMM d, yyyy")}
                  </p>
                </div>
              </div>
            </div>
          </Card>

          {/* Billing Address (Full) */}
          {customer.billingAddress && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-text-primary mb-4">Billing Address</h3>
              <div className="text-sm text-text-secondary space-y-1">
                <p>{customer.billingAddress.line1}</p>
                {customer.billingAddress.line2 && <p>{customer.billingAddress.line2}</p>}
                <p>
                  {customer.billingAddress.city}, {customer.billingAddress.state} {customer.billingAddress.postalCode}
                </p>
                <p>{customer.billingAddress.country}</p>
              </div>
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
              {customer.tags && customer.tags.length > 0 ? (
                customer.tags.map((tag) => (
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
            <ActivityTimeline activities={activities} maxItems={5} />
          </Card>
        </div>

        {/* Right Column - Metrics & Quick Actions */}
        <div className="space-y-6">
          {/* Billing Metrics */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Billing Overview</h3>
            {metricsLoading ? (
              <div className="space-y-4">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-4 w-24 bg-surface-overlay rounded mb-1" />
                    <div className="h-6 w-32 bg-surface-overlay rounded" />
                  </div>
                ))}
              </div>
            ) : metrics ? (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
                    <DollarSign className="w-5 h-5 text-status-success" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Total Revenue</p>
                    <p className="text-lg font-semibold text-text-primary">
                      ${metrics.totalRevenue?.toLocaleString() ?? 0}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
                    <Receipt className="w-5 h-5 text-accent" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Purchases</p>
                    <p className="text-lg font-semibold text-text-primary">{metrics.purchaseCount ?? 0}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
                    <TrendingUp className="w-5 h-5 text-highlight" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Avg Order Value</p>
                    <p className="text-lg font-semibold text-text-primary">
                      ${metrics.averageOrderValue?.toLocaleString() ?? 0}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
                    <Heart className="w-5 h-5 text-status-info" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Lifetime Value</p>
                    <p className="text-lg font-semibold text-text-primary">
                      ${metrics.lifetimeValue?.toLocaleString() ?? 0}
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-text-muted">No billing data available</p>
            )}
          </Card>

          {/* Quick Actions */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Quick Actions</h3>
            <div className="space-y-2">
              <Button variant="outline" className="w-full justify-start">
                <CreditCard className="w-4 h-4 mr-2" />
                Create Invoice
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <MessageSquare className="w-4 h-4 mr-2" />
                Send Message
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <FileText className="w-4 h-4 mr-2" />
                Add Note
              </Button>
            </div>
          </Card>

          {/* Metadata */}
          {customer.metadata && Object.keys(customer.metadata).length > 0 && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-text-primary mb-4">Metadata</h3>
              <div className="space-y-2">
                {Object.entries(customer.metadata).map(([key, value]) => (
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
function CustomerDetailSkeleton() {
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
              {[1, 2, 3, 4].map((i) => (
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
