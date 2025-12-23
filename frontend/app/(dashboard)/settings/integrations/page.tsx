"use client";

import { useState } from "react";
import Image from "next/image";
import {
  Globe,
  Plus,
  Search,
  Power,
  PowerOff,
  RefreshCcw,
  Trash2,
  CheckCircle2,
  XCircle,
  ExternalLink,
} from "lucide-react";
import { format } from "date-fns";
import { Button, Card, Input, Modal } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useIntegrations,
  useAvailableIntegrations,
  useEnableIntegration,
  useDisableIntegration,
  useDeleteIntegration,
  useTestIntegration,
  useSyncIntegration,
} from "@/lib/hooks/api/use-integrations";

export default function IntegrationsPage() {
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  const [searchQuery, setSearchQuery] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);

  const { data: integrationsResponse, isLoading } = useIntegrations();
  const { data: availableIntegrations } = useAvailableIntegrations();
  const integrations = integrationsResponse?.integrations ?? [];

  const enableIntegration = useEnableIntegration();
  const disableIntegration = useDisableIntegration();
  const deleteIntegration = useDeleteIntegration();
  const testIntegration = useTestIntegration();
  const syncIntegration = useSyncIntegration();

  const filteredIntegrations = (integrations || []).filter(
    (i) =>
      i.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      i.type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleToggle = async (id: string, enabled: boolean) => {
    try {
      if (enabled) {
        await disableIntegration.mutateAsync(id);
        toast({ title: "Integration disabled" });
      } else {
        await enableIntegration.mutateAsync(id);
        toast({ title: "Integration enabled" });
      }
    } catch {
      toast({ title: "Failed to update integration", variant: "error" });
    }
  };

  const handleDelete = async (id: string, name: string) => {
    const confirmed = await confirm({
      title: "Delete Integration",
      description: `Are you sure you want to delete the "${name}" integration? This will remove all configuration and logs.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deleteIntegration.mutateAsync(id);
        toast({ title: "Integration deleted" });
      } catch {
        toast({ title: "Failed to delete integration", variant: "error" });
      }
    }
  };

  const handleTest = async (id: string) => {
    try {
      const result = await testIntegration.mutateAsync(id);
      const isHealthy = ["connected", "ready"].includes(result.status);
      toast({
        title: isHealthy ? "Connection successful" : "Connection failed",
        description: result.message || `Status: ${result.status}`,
        variant: isHealthy ? "default" : "error",
      });
    } catch {
      toast({ title: "Test failed", variant: "error" });
    }
  };

  const handleSync = async (id: string) => {
    try {
      await syncIntegration.mutateAsync(id);
      toast({ title: "Sync started" });
    } catch {
      toast({ title: "Failed to sync", variant: "error" });
    }
  };
  const iconLoader = ({ src }: { src: string }) => src;

  if (isLoading) {
    return <IntegrationsSkeleton />;
  }

  return (
    <div className="space-y-8 animate-fade-up">
      {dialog}

      <PageHeader
        title="Integrations"
        description="Connect with external services and tools"
        breadcrumbs={[
          { label: "Settings", href: "/settings" },
          { label: "Integrations" },
        ]}
        actions={
          <Button onClick={() => setShowAddModal(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Add Integration
          </Button>
        }
      />

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
        <Input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search integrations..."
          className="pl-10"
        />
      </div>

      {/* Integrations Grid */}
      {filteredIntegrations.length === 0 ? (
        <Card className="p-12 text-center">
          <Globe className="w-12 h-12 text-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">No integrations</h3>
          <p className="text-text-muted mb-6">
            {searchQuery
              ? "No integrations match your search"
              : "Connect your first integration to get started"}
          </p>
          <Button onClick={() => setShowAddModal(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Add Integration
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredIntegrations.map((integration) => {
            const iconUrl =
              typeof integration.metadata?.iconUrl === "string"
                ? integration.metadata.iconUrl
                : undefined;

            return (
              <Card key={integration.name} className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-lg bg-surface-overlay flex items-center justify-center">
                    {iconUrl ? (
                      <Image
                        src={iconUrl}
                        alt={`${integration.name} logo`}
                        width={32}
                        height={32}
                        className="w-8 h-8"
                        loader={iconLoader}
                        unoptimized
                      />
                    ) : (
                      <Globe className="w-6 h-6 text-text-muted" />
                    )}
                  </div>
                  <div>
                    <h4 className="font-semibold text-text-primary">{integration.name}</h4>
                    <p className="text-sm text-text-muted">{integration.provider}</p>
                  </div>
                </div>
                <span
                  className={cn(
                    "inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium",
                    integration.enabled
                      ? "bg-status-success/15 text-status-success"
                      : "bg-surface-overlay text-text-muted"
                  )}
                >
                  {integration.enabled ? (
                    <>
                      <CheckCircle2 className="w-3 h-3" />
                      Active
                    </>
                  ) : (
                    <>
                      <XCircle className="w-3 h-3" />
                      Disabled
                    </>
                  )}
                </span>
              </div>

              {integration.message && (
                <p className="text-sm text-text-muted mb-4">{integration.message}</p>
              )}

              <div className="text-xs text-text-muted mb-4">
                Last check: {integration.lastCheck ? format(new Date(integration.lastCheck), "MMM d, HH:mm") : "Never"}
              </div>

              <div className="flex items-center gap-2 pt-4 border-t border-border-subtle">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleToggle(integration.name, integration.enabled)}
                >
                  {integration.enabled ? (
                    <>
                      <PowerOff className="w-4 h-4 mr-1" />
                      Disable
                    </>
                  ) : (
                    <>
                      <Power className="w-4 h-4 mr-1" />
                      Enable
                    </>
                  )}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleTest(integration.name)}
                  disabled={!integration.enabled}
                >
                  Test
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleSync(integration.name)}
                  disabled={!integration.enabled}
                >
                  <RefreshCcw className="w-4 h-4" />
                </Button>
                <div className="flex-1" />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDelete(integration.name, integration.name)}
                  className="text-status-error hover:text-status-error"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Add Integration Modal */}
      <Modal open={showAddModal} onOpenChange={setShowAddModal}>
        <div className="p-6 max-w-2xl">
          <h2 className="text-xl font-semibold text-text-primary mb-2">Add Integration</h2>
          <p className="text-sm text-text-muted mb-6">
            Choose an integration to connect with your platform
          </p>

          <div className="grid grid-cols-2 gap-4 max-h-[400px] overflow-auto">
            {(availableIntegrations || []).map((integration) => (
              <button
                key={`${integration.type}-${integration.provider}`}
                className="flex items-center gap-4 p-4 rounded-lg border border-border-subtle hover:border-accent transition-all text-left"
                onClick={() => {
                  setShowAddModal(false);
                  // Navigate to integration setup
                  window.location.href = `/settings/integrations/new?type=${integration.type}`;
                }}
              >
                <div className="w-12 h-12 rounded-lg bg-surface-overlay flex items-center justify-center">
                  {integration.iconUrl ? (
                    <Image
                      src={integration.iconUrl}
                      alt={`${integration.name} logo`}
                      width={32}
                      height={32}
                      className="w-8 h-8"
                      loader={iconLoader}
                      unoptimized
                    />
                  ) : (
                    <Globe className="w-6 h-6 text-text-muted" />
                  )}
                </div>
                <div className="flex-1">
                  <p className="font-medium text-text-primary">{integration.name}</p>
                  <p className="text-sm text-text-muted">{integration.description}</p>
                </div>
                <ExternalLink className="w-4 h-4 text-text-muted" />
              </button>
            ))}
          </div>
        </div>
      </Modal>
    </div>
  );
}

function IntegrationsSkeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      <div className="h-8 w-48 bg-surface-overlay rounded" />
      <div className="h-10 w-64 bg-surface-overlay rounded" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="card p-6 h-48" />
        ))}
      </div>
    </div>
  );
}
