"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Globe,
  Building2,
  Check,
  Copy,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Clock,
  X,
} from "lucide-react";
import { Button, useToast } from "@/lib/dotmac/core";
import { cn } from "@/lib/utils";
import { useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useCurrentTenant,
  useDomainStatus,
  useInitiateDomainVerification,
  useCheckDomainVerification,
  useRemoveDomain,
} from "@/lib/hooks/api/use-tenants";
import type { VerificationMethod, DomainStatus } from "@/lib/api/tenants";

export default function OrganizationSettingsPage() {
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();
  const { data: tenant, isLoading: tenantLoading } = useCurrentTenant();
  const { data: domainData, isLoading: domainLoading } = useDomainStatus(
    tenant?.id || ""
  );

  const [domain, setDomain] = useState("");
  const [method, setMethod] = useState<VerificationMethod>("dns_txt");
  const [showInstructions, setShowInstructions] = useState(false);

  const initVerification = useInitiateDomainVerification();
  const checkVerification = useCheckDomainVerification();
  const removeDomain = useRemoveDomain();

  const handleInitiateVerification = async () => {
    if (!tenant?.id || !domain.trim()) return;

    try {
      await initVerification.mutateAsync({
        tenantId: tenant.id,
        domain: domain.trim(),
        method,
      });
      setShowInstructions(true);
      toast({
        title: "Verification initiated",
        description: "Follow the instructions below to verify your domain.",
        variant: "success",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to initiate domain verification",
        variant: "error",
      });
    }
  };

  const handleCheckVerification = async () => {
    if (!tenant?.id || !domainData?.verification?.domain) return;

    try {
      const result = await checkVerification.mutateAsync({
        tenantId: tenant.id,
        domain: domainData.verification.domain,
      });

      if (result.success) {
        toast({
          title: "Domain verified",
          description: `${result.domain} has been verified successfully.`,
          variant: "success",
        });
        setShowInstructions(false);
      } else {
        toast({
          title: "Verification failed",
          description: result.message,
          variant: "error",
        });
      }
    } catch {
      toast({
        title: "Error",
        description: "Failed to check domain verification",
        variant: "error",
      });
    }
  };

  const handleRemoveDomain = async () => {
    if (!tenant?.id) return;

    const confirmed = await confirm({
      title: "Remove Custom Domain",
      description:
        "Are you sure you want to remove this custom domain? Users will need to use the default domain to access the application.",
      variant: "warning",
    });

    if (!confirmed) return;

    try {
      await removeDomain.mutateAsync(tenant.id);
      toast({
        title: "Domain removed",
        description: "Custom domain has been removed.",
        variant: "success",
      });
      setShowInstructions(false);
      setDomain("");
    } catch {
      toast({
        title: "Error",
        description: "Failed to remove domain",
        variant: "error",
      });
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied",
      description: "Value copied to clipboard",
    });
  };

  const statusConfig: Record<
    DomainStatus | "none",
    { icon: React.ElementType; class: string; label: string }
  > = {
    verified: {
      icon: CheckCircle,
      class: "text-status-success bg-status-success/15",
      label: "Verified",
    },
    pending: {
      icon: Clock,
      class: "text-status-warning bg-status-warning/15",
      label: "Pending",
    },
    failed: {
      icon: AlertCircle,
      class: "text-status-error bg-status-error/15",
      label: "Failed",
    },
    expired: {
      icon: X,
      class: "text-text-muted bg-surface-overlay",
      label: "Expired",
    },
    none: {
      icon: Globe,
      class: "text-text-muted bg-surface-overlay",
      label: "Not configured",
    },
  };

  const currentStatus = domainData?.status || "none";
  const StatusIcon = statusConfig[currentStatus].icon;
  const planLabel =
    typeof tenant?.plan === "string" ? tenant.plan : tenant?.plan?.name;

  if (tenantLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent"></div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-6">
      {/* Confirm dialog */}
      {dialog}

      {/* Back link */}
      <Link
        href="/settings"
        className="inline-flex items-center gap-2 text-sm text-text-muted hover:text-text-secondary transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Settings
      </Link>

      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-semibold text-text-primary">
          Organization Settings
        </h1>
        <p className="text-text-muted mt-1">
          Manage your organization&apos;s details and custom domain
        </p>
      </div>

      {/* Organization Info */}
      <div className="card p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
            <Building2 className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-text-primary">
              Organization Details
            </h2>
            <p className="text-xs text-text-muted">
              Basic information about your organization
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">
              Organization Name
            </label>
            <p className="text-text-primary">{tenant?.name || "—"}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">
              Slug
            </label>
            <p className="text-text-muted font-mono text-sm">
              {tenant?.slug || "—"}
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">
              Plan
            </label>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-accent-subtle text-accent">
              {planLabel || "Free"}
            </span>
          </div>
        </div>
      </div>

      {/* Custom Domain */}
      <div className="card p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
            <Globe className="w-5 h-5 text-accent" />
          </div>
          <div className="flex-1">
            <h2 className="text-sm font-semibold text-text-primary">
              Custom Domain
            </h2>
            <p className="text-xs text-text-muted">
              Use your own domain for your organization
            </p>
          </div>
          {currentStatus !== "none" && (
            <span
              className={cn(
                "inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium",
                statusConfig[currentStatus].class
              )}
            >
              <StatusIcon className="w-3 h-3" />
              {statusConfig[currentStatus].label}
            </span>
          )}
        </div>

        {domainLoading ? (
          <div className="text-center text-text-muted py-4">
            Loading domain status...
          </div>
        ) : currentStatus === "verified" ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-status-success/15 rounded-lg border border-status-success/30">
              <div className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-status-success" />
                <div>
                  <p className="text-sm font-medium text-text-primary">
                    {domainData?.domain}
                  </p>
                  <p className="text-xs text-text-muted">
                    Verified on{" "}
                    {domainData?.verification?.verifiedAt
                      ? new Date(
                          domainData.verification.verifiedAt
                        ).toLocaleDateString()
                      : "—"}
                  </p>
                </div>
              </div>
              <Button
                variant="destructive"
                size="sm"
                onClick={handleRemoveDomain}
                disabled={removeDomain.isPending}
              >
                Remove
              </Button>
            </div>
          </div>
        ) : currentStatus === "pending" && showInstructions ? (
          <div className="space-y-4">
            {/* Verification Instructions */}
            <div className="p-4 bg-status-warning/15 rounded-lg border border-status-warning/30">
              <h3 className="text-sm font-semibold text-text-primary mb-3">
                Verification Instructions
              </h3>
              <p className="text-sm text-text-secondary mb-4">
                {domainData?.verification?.instructions}
              </p>

              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">
                    Record Type
                  </label>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 px-3 py-2 bg-surface-overlay rounded text-sm font-mono text-text-primary">
                      {domainData?.verification?.method === "dns_txt"
                        ? "TXT"
                        : "CNAME"}
                    </code>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">
                    Name / Host
                  </label>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 px-3 py-2 bg-surface-overlay rounded text-sm font-mono text-text-primary truncate">
                      {domainData?.verification?.verificationRecord}
                    </code>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        copyToClipboard(
                          domainData?.verification?.verificationRecord || ""
                        )
                      }
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-text-muted mb-1">
                    Value
                  </label>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 px-3 py-2 bg-surface-overlay rounded text-sm font-mono text-text-primary truncate">
                      {domainData?.verification?.verificationValue}
                    </code>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        copyToClipboard(
                          domainData?.verification?.verificationValue || ""
                        )
                      }
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Button
                onClick={handleCheckVerification}
                disabled={checkVerification.isPending}
                className="shadow-glow-sm"
              >
                {checkVerification.isPending ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Checking...
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4 mr-2" />
                    Verify Domain
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                onClick={handleRemoveDomain}
                disabled={removeDomain.isPending}
              >
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Domain Name
              </label>
              <input
                type="text"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                placeholder="app.yourdomain.com"
                className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Verification Method
              </label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="method"
                    value="dns_txt"
                    checked={method === "dns_txt"}
                    onChange={() => setMethod("dns_txt")}
                    className="w-4 h-4 text-accent border-border focus:ring-accent"
                  />
                  <span className="text-sm text-text-primary">
                    DNS TXT Record
                  </span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="method"
                    value="dns_cname"
                    checked={method === "dns_cname"}
                    onChange={() => setMethod("dns_cname")}
                    className="w-4 h-4 text-accent border-border focus:ring-accent"
                  />
                  <span className="text-sm text-text-primary">
                    DNS CNAME Record
                  </span>
                </label>
              </div>
            </div>

            <Button
              onClick={handleInitiateVerification}
              disabled={!domain.trim() || initVerification.isPending}
              className="shadow-glow-sm"
            >
              {initVerification.isPending ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Initiating...
                </>
              ) : (
                <>
                  <Globe className="w-4 h-4 mr-2" />
                  Verify Domain
                </>
              )}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
