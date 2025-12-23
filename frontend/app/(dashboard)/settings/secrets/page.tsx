"use client";

import { useState } from "react";
import {
  Key,
  Plus,
  Search,
  Eye,
  EyeOff,
  Copy,
  RefreshCcw,
  Trash2,
  Lock,
  Calendar,
  Shield,
  AlertTriangle,
} from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";
import { Button, Card, Input, Modal } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { ConfirmDialog, useConfirmDialog } from "@/components/shared/confirm-dialog";
import { getSecret } from "@/lib/api/secrets";
import {
  useSecrets,
  useSecretsHealth,
  useSecretsMetrics,
  useCreateSecret,
  useDeleteSecret,
  useRotateSecret,
} from "@/lib/hooks/api/use-secrets";

export default function SecretsPage() {
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  const [searchQuery, setSearchQuery] = useState("");
  const [currentPath, setCurrentPath] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [revealedSecrets, setRevealedSecrets] = useState<Record<string, boolean>>({});
  const [revealingSecrets, setRevealingSecrets] = useState<Record<string, boolean>>({});
  const [secretValues, setSecretValues] = useState<Record<string, Record<string, unknown>>>({});

  const { data: secrets, isLoading } = useSecrets(currentPath);
  const { data: health } = useSecretsHealth();
  const { data: metrics } = useSecretsMetrics();

  const createSecret = useCreateSecret();
  const deleteSecret = useDeleteSecret();
  const rotateSecret = useRotateSecret();

  const filteredSecrets = (secrets || []).filter(
    (s) => s.path.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleDelete = async (path: string) => {
    const confirmed = await confirm({
      title: "Delete Secret",
      description: `Are you sure you want to delete "${path}"? This action can be undone by restoring from version history.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deleteSecret.mutateAsync({ path });
        toast({ title: "Secret deleted" });
      } catch {
        toast({ title: "Failed to delete secret", variant: "error" });
      }
    }
  };

  const handleRotate = async (path: string) => {
    const confirmed = await confirm({
      title: "Rotate Secret",
      description: "This will create a new version of the secret. You'll need to update any applications using this secret.",
      variant: "warning",
    });

    if (confirmed) {
      try {
        // In a real app, this would prompt for new value
        await rotateSecret.mutateAsync({ path, newData: {} });
        toast({ title: "Secret rotated" });
      } catch {
        toast({ title: "Failed to rotate secret", variant: "error" });
      }
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({ title: "Copied to clipboard" });
  };

  const handleToggleReveal = async (path: string) => {
    if (revealedSecrets[path]) {
      setRevealedSecrets((prev) => ({ ...prev, [path]: false }));
      return;
    }

    if (!secretValues[path]) {
      setRevealingSecrets((prev) => ({ ...prev, [path]: true }));
      try {
        const value = await getSecret(path);
        setSecretValues((prev) => ({ ...prev, [path]: value.data }));
      } catch {
        toast({ title: "Failed to fetch secret value", variant: "error" });
        return;
      } finally {
        setRevealingSecrets((prev) => ({ ...prev, [path]: false }));
      }
    }

    setRevealedSecrets((prev) => ({ ...prev, [path]: true }));
  };

  if (isLoading) {
    return <SecretsSkeleton />;
  }

  return (
    <div className="space-y-8 animate-fade-up">
      {dialog}

      <PageHeader
        title="Secrets Management"
        description="Securely store and manage sensitive configuration"
        breadcrumbs={[
          { label: "Settings", href: "/settings" },
          { label: "Secrets" },
        ]}
        actions={
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Create Secret
          </Button>
        }
      />

      {/* Health & Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div
              className={cn(
                "w-10 h-10 rounded-lg flex items-center justify-center",
                health?.status === "healthy" ? "bg-status-success/15" : "bg-status-error/15"
              )}
            >
              <Shield
                className={cn(
                  "w-5 h-5",
                  health?.status === "healthy" ? "text-status-success" : "text-status-error"
                )}
              />
            </div>
            <div>
              <p className="text-sm text-text-muted">Vault Status</p>
              <p className="font-semibold text-text-primary capitalize">{health?.status || "Unknown"}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Total Accesses</p>
          <p className="text-2xl font-semibold text-text-primary">
            {metrics?.totalSecretsAccessed || 0}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Unique Secrets</p>
          <p className="text-2xl font-semibold text-text-primary">
            {metrics?.uniqueSecrets || 0}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Failed Accesses</p>
          <p className="text-2xl font-semibold text-accent">
            {metrics?.failedAccesses || 0}
          </p>
        </Card>
      </div>

      {/* Path breadcrumb */}
      {currentPath && (
        <div className="flex items-center gap-2 text-sm">
          <button
            onClick={() => setCurrentPath("")}
            className="text-accent hover:underline"
          >
            Root
          </button>
          {currentPath.split("/").map((segment, i, arr) => (
            <span key={i} className="flex items-center gap-2">
              <span className="text-text-muted">/</span>
              <button
                onClick={() => setCurrentPath(arr.slice(0, i + 1).join("/"))}
                className="text-accent hover:underline"
              >
                {segment}
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
        <Input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search secrets..."
          className="pl-10"
        />
      </div>

      {/* Secrets List */}
      {filteredSecrets.length === 0 ? (
        <Card className="p-12 text-center">
          <Key className="w-12 h-12 text-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">No secrets</h3>
          <p className="text-text-muted mb-6">
            {searchQuery ? "No secrets match your search" : "Create your first secret to get started"}
          </p>
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Create Secret
          </Button>
        </Card>
      ) : (
        <div className="space-y-2">
          {filteredSecrets.map((secret) => (
            <Card key={secret.path} className="p-4">
              <div className="flex items-center gap-4">
                {/* Icon */}
                <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
                  <Key className="w-5 h-5 text-accent" />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-text-primary">{secret.path.split("/").pop()}</p>
                  <p className="text-sm text-text-muted">{secret.path}</p>
                </div>

                {/* Version & Metadata */}
                <div className="text-right">
                  <p className="text-sm text-text-muted">Version</p>
                  <p className="font-mono text-sm text-text-primary">v{secret.version}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-text-muted">Updated</p>
                  <p className="text-sm text-text-primary">
                    {formatDistanceToNow(new Date(secret.updatedAt), { addSuffix: true })}
                  </p>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleToggleReveal(secret.path)}
                  >
                    {revealedSecrets[secret.path] ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copyToClipboard(secret.path)}
                  >
                    <Copy className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRotate(secret.path)}
                  >
                    <RefreshCcw className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(secret.path)}
                    className="text-status-error hover:text-status-error"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Revealed value */}
              {revealedSecrets[secret.path] && (
                <div className="mt-4 p-3 bg-surface-overlay rounded-lg">
                  <code className="text-sm text-text-primary">
                    {revealingSecrets[secret.path]
                      ? "Loading..."
                      : JSON.stringify(secretValues[secret.path] ?? {}, null, 2)}
                  </code>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Modal open={showCreateModal} onOpenChange={setShowCreateModal}>
        <div className="p-6 max-w-lg">
          <h2 className="text-xl font-semibold text-text-primary mb-6">Create Secret</h2>
          <form className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Path</label>
              <Input placeholder="secret/myapp/api-key" />
              <p className="text-xs text-text-muted mt-1">Use / to organize secrets into folders</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Key</label>
              <Input placeholder="API_KEY" />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">Value</label>
              <Input type="password" placeholder="Enter secret value" />
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="ghost" onClick={() => setShowCreateModal(false)}>
                Cancel
              </Button>
              <Button>Create Secret</Button>
            </div>
          </form>
        </div>
      </Modal>
    </div>
  );
}

function SecretsSkeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      <div className="h-8 w-48 bg-surface-overlay rounded" />
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card p-4 h-20" />
        ))}
      </div>
      <div className="space-y-2">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="card p-4 h-16" />
        ))}
      </div>
    </div>
  );
}
