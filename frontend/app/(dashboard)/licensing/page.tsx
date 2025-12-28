"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Key,
  Plus,
  Search,
  Filter,
  RefreshCcw,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  Users,
  Copy,
  Trash2,
  Edit,
  Play,
  Pause,
  Shield,
} from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";
import { Button, Card, Input, Modal } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useLicenses,
  useLicensingDashboard,
  useLicenseTemplates,
  useDeleteLicense,
  useSuspendLicense,
  useReactivateLicense,
  useValidateLicense,
} from "@/lib/hooks/api/use-licensing";
import type { LicenseStatus, LicenseType } from "@/lib/api/licensing";
import { DashboardAlerts } from "@/components/features/dashboard";

const statusConfig: Record<LicenseStatus, { label: string; color: string; icon: React.ElementType }> = {
  active: { label: "Active", color: "bg-status-success/15 text-status-success", icon: CheckCircle2 },
  expired: { label: "Expired", color: "bg-status-error/15 text-status-error", icon: XCircle },
  suspended: { label: "Suspended", color: "bg-status-warning/15 text-status-warning", icon: AlertCircle },
  revoked: { label: "Revoked", color: "bg-status-error/15 text-status-error", icon: XCircle },
  trial: { label: "Trial", color: "bg-surface-overlay text-text-muted", icon: Clock },
};

const typeConfig: Record<LicenseType, { label: string; color: string }> = {
  perpetual: { label: "Perpetual", color: "bg-accent-subtle text-accent" },
  subscription: { label: "Subscription", color: "bg-status-info/15 text-status-info" },
  trial: { label: "Trial", color: "bg-status-warning/15 text-status-warning" },
  enterprise: { label: "Enterprise", color: "bg-highlight-subtle text-highlight" },
};

export default function LicensingPage() {
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<LicenseStatus | "all">("all");
  const [typeFilter, setTypeFilter] = useState<LicenseType | "all">("all");
  const [page, setPage] = useState(1);
  const [showValidateModal, setShowValidateModal] = useState(false);
  const [validateKey, setValidateKey] = useState("");

  const { data, isLoading, refetch } = useLicenses({
    page,
    pageSize: 20,
    search: searchQuery || undefined,
    status: statusFilter !== "all" ? statusFilter : undefined,
    type: typeFilter !== "all" ? typeFilter : undefined,
  });
  const { data: dashboardData } = useLicensingDashboard();
  const { data: templates } = useLicenseTemplates();

  const deleteLicense = useDeleteLicense();
  const suspendLicense = useSuspendLicense();
  const reactivateLicense = useReactivateLicense();
  const validateLicense = useValidateLicense();

  const licenses = data?.licenses || [];
  const totalPages = data?.pageCount || 1;
  const expiringSoonCount = licenses.filter((license) => {
    if (!license.expiresAt) return false;
    const expiresAt = new Date(license.expiresAt).getTime();
    return expiresAt < Date.now() + 30 * 24 * 60 * 60 * 1000;
  }).length;
  const totalSeats = licenses.reduce((sum, license) => sum + license.seats, 0);

  const handleDelete = async (id: string, key: string) => {
    const confirmed = await confirm({
      title: "Delete License",
      description: `Are you sure you want to delete license "${key}"? This action cannot be undone.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deleteLicense.mutateAsync(id);
        toast({ title: "License deleted" });
      } catch {
        toast({ title: "Failed to delete license", variant: "error" });
      }
    }
  };

  const handleToggleStatus = async (id: string, status: string) => {
    try {
      if (status === "active") {
        await suspendLicense.mutateAsync({ id });
        toast({ title: "License suspended" });
      } else if (status === "suspended") {
        await reactivateLicense.mutateAsync(id);
        toast({ title: "License reactivated" });
      }
    } catch {
      toast({ title: "Failed to update license", variant: "error" });
    }
  };

  const handleValidate = async () => {
    if (!validateKey) return;

    try {
      const result = await validateLicense.mutateAsync(validateKey);
      if (result.valid) {
        toast({ title: "License is valid", description: `Expires: ${result.expiresAt || "Never"}` });
      } else {
        toast({ title: "License is invalid", description: result.message || "Unknown reason", variant: "error" });
      }
      setShowValidateModal(false);
      setValidateKey("");
    } catch {
      toast({ title: "Failed to validate license", variant: "error" });
    }
  };

  const copyLicenseKey = (key: string) => {
    navigator.clipboard.writeText(key);
    toast({ title: "License key copied" });
  };

  if (isLoading) {
    return <LicensingSkeleton />;
  }

  return (
    <div className="space-y-6 animate-fade-up">
      {dialog}

      <PageHeader
        title="Licensing"
        description="Manage software licenses and activations"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={() => refetch()}>
              <RefreshCcw className="w-4 h-4" />
            </Button>
            <Button variant="outline" onClick={() => setShowValidateModal(true)}>
              <Shield className="w-4 h-4 mr-2" />
              Validate
            </Button>
            <Link href="/licensing/new">
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                Create License
              </Button>
            </Link>
          </div>
        }
      />

      {/* Dashboard Alerts */}
      {dashboardData?.alerts && dashboardData.alerts.length > 0 && (
        <DashboardAlerts alerts={dashboardData.alerts} />
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <Key className="w-5 h-5 text-accent" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Total Licenses</p>
              <p className="text-2xl font-semibold text-text-primary">
                {data?.totalCount?.toLocaleString() || 0}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5 text-status-success" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Active</p>
              <p className="text-2xl font-semibold text-status-success">
                {licenses.filter((l) => l.status === "active").length}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-status-warning/15 flex items-center justify-center">
              <Clock className="w-5 h-5 text-status-warning" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Expiring Soon</p>
              <p className="text-2xl font-semibold text-status-warning">
                {expiringSoonCount}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
              <Users className="w-5 h-5 text-status-info" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Total Seats</p>
              <p className="text-2xl font-semibold text-text-primary">
                {totalSeats.toLocaleString()}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <Input
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setPage(1);
            }}
            placeholder="Search by key or tenant..."
            className="pl-10"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-text-muted" />
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value as LicenseStatus | "all");
              setPage(1);
            }}
            className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="expired">Expired</option>
            <option value="suspended">Suspended</option>
            <option value="trial">Trial</option>
          </select>
          <select
            value={typeFilter}
            onChange={(e) => {
              setTypeFilter(e.target.value as LicenseType | "all");
              setPage(1);
            }}
            className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
          >
            <option value="all">All Types</option>
            <option value="perpetual">Perpetual</option>
            <option value="subscription">Subscription</option>
            <option value="trial">Trial</option>
            <option value="enterprise">Enterprise</option>
          </select>
        </div>
      </div>

      {/* Licenses Table */}
      {licenses.length === 0 ? (
        <Card className="p-12 text-center">
          <Key className="w-12 h-12 text-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">No licenses found</h3>
          <p className="text-text-muted mb-6">
            {searchQuery || statusFilter !== "all" || typeFilter !== "all"
              ? "Try adjusting your filters"
              : "Create your first license to get started"}
          </p>
          <Link href="/licensing/new">
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Create License
            </Button>
          </Link>
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="data-table" aria-label="Software licenses"><caption className="sr-only">Software licenses</caption>
              <thead>
                <tr className="border-b border-border-subtle">
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">License Key</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Type</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Status</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Tenant</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Seats</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Expires</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {licenses.map((license) => {
                  const status = statusConfig[license.status as LicenseStatus] || statusConfig.trial;
                  const type = typeConfig[license.type as LicenseType] || typeConfig.subscription;
                  const StatusIcon = status.icon;

                  return (
                    <tr key={license.id} className="border-b border-border-subtle hover:bg-surface-overlay/50">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <code className="text-sm font-mono text-text-primary">
                            {license.licenseKey.slice(0, 12)}...
                          </code>
                          <button
                            onClick={() => copyLicenseKey(license.licenseKey)}
                            className="text-text-muted hover:text-text-secondary transition-colors"
                          >
                            <Copy className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={cn("px-2 py-0.5 rounded-full text-xs font-medium", type.color)}>
                          {type.label}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium", status.color)}>
                          <StatusIcon className="w-3 h-3" />
                          {status.label}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {license.customerName ? (
                          <Link href={`/tenants/${license.customerId}`} className="text-sm text-accent hover:underline">
                            {license.customerName}
                          </Link>
                        ) : (
                          <span className="text-sm text-text-muted">Unassigned</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm text-text-secondary">
                          {license.usedSeats || 0} / {license.seats}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {license.expiresAt ? (
                          <span className={cn(
                            "text-sm",
                            new Date(license.expiresAt) < new Date()
                              ? "text-status-error"
                              : new Date(license.expiresAt) < new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
                              ? "text-status-warning"
                              : "text-text-muted"
                          )}>
                            {format(new Date(license.expiresAt), "MMM d, yyyy")}
                          </span>
                        ) : (
                          <span className="text-sm text-text-muted">Never</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <Link href={`/licensing/${license.id}`}>
                            <Button variant="ghost" size="sm">
                              <Edit className="w-4 h-4" />
                            </Button>
                          </Link>
                          {(license.status === "active" || license.status === "suspended") && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleToggleStatus(license.id, license.status)}
                            >
                              {license.status === "active" ? (
                                <Pause className="w-4 h-4" />
                              ) : (
                                <Play className="w-4 h-4" />
                              )}
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(license.id, license.licenseKey)}
                            className="text-status-error hover:text-status-error"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-border-subtle">
              <p className="text-sm text-text-muted">
                Page {page} of {totalPages}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Validate Modal */}
      <Modal open={showValidateModal} onOpenChange={setShowValidateModal}>
        <div className="p-6 max-w-md">
          <h2 className="text-xl font-semibold text-text-primary mb-2">Validate License</h2>
          <p className="text-text-muted mb-6">
            Enter a license key to check its validity
          </p>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                License Key
              </label>
              <Input
                value={validateKey}
                onChange={(e) => setValidateKey(e.target.value)}
                placeholder="XXXX-XXXX-XXXX-XXXX"
                className="font-mono"
              />
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="ghost" onClick={() => setShowValidateModal(false)}>
                Cancel
              </Button>
              <Button onClick={handleValidate} disabled={!validateKey || validateLicense.isPending}>
                {validateLicense.isPending ? "Validating..." : "Validate"}
              </Button>
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
}

function LicensingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 w-48 bg-surface-overlay rounded" />
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card p-4 h-20" />
        ))}
      </div>
      <div className="card">
        <div className="p-4 space-y-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-12 bg-surface-overlay rounded" />
          ))}
        </div>
      </div>
    </div>
  );
}
