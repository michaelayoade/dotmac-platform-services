"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Key,
  Plus,
  Copy,
  Trash2,
  Clock,
  AlertTriangle,
  Check,
  X,
  RefreshCw,
  Eye,
  EyeOff,
} from "lucide-react";
import { Button, useToast } from "@/lib/dotmac/core";
import { cn } from "@/lib/utils";
import { useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useApiKeys,
  useCreateApiKey,
  useDeleteApiKey,
} from "@/lib/hooks/api/use-tenant-portal";
import type { ApiKey } from "@/types/tenant-portal";

export default function ApiKeysSettingsPage() {
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();
  const { data: apiKeys = [], isLoading } = useApiKeys();
  const createApiKey = useCreateApiKey();
  const deleteApiKey = useDeleteApiKey();

  const [isCreating, setIsCreating] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [expiresInDays, setExpiresInDays] = useState<number | undefined>();
  const [newSecretKey, setNewSecretKey] = useState<string | null>(null);
  const [showSecret, setShowSecret] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!newKeyName.trim()) {
      toast({
        title: "Error",
        description: "Please enter a name for the API key",
        variant: "error",
      });
      return;
    }

    try {
      const result = await createApiKey.mutateAsync({
        name: newKeyName.trim(),
        expiresInDays,
      });

      setNewSecretKey(result.secretKey);
      setNewKeyName("");
      setExpiresInDays(undefined);

      toast({
        title: "API key created",
        description: "Make sure to copy your secret key now. You won't be able to see it again.",
        variant: "success",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to create API key",
        variant: "error",
      });
    }
  };

  const handleDelete = async (id: string) => {
    const key = apiKeys.find((k: ApiKey) => k.id === id);
    const confirmed = await confirm({
      title: "Revoke API Key",
      description: `Are you sure you want to revoke "${key?.name || "this key"}"? Any applications using this key will immediately lose access. This action cannot be undone.`,
      variant: "danger",
    });

    if (!confirmed) return;

    setDeletingId(id);
    try {
      await deleteApiKey.mutateAsync(id);
      toast({
        title: "API key revoked",
        description: "The API key has been permanently revoked.",
        variant: "success",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to revoke API key",
        variant: "error",
      });
    } finally {
      setDeletingId(null);
    }
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied",
      description: `${label} copied to clipboard`,
    });
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const isExpired = (expiresAt?: string) => {
    if (!expiresAt) return false;
    return new Date(expiresAt) < new Date();
  };

  return (
    <div className="max-w-3xl space-y-6">
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary">API Keys</h1>
          <p className="text-text-muted mt-1">
            Manage API keys for programmatic access
          </p>
        </div>
        {!isCreating && !newSecretKey && (
          <Button
            onClick={() => setIsCreating(true)}
            className="shadow-glow-sm hover:shadow-glow"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create API Key
          </Button>
        )}
      </div>

      {/* Security Warning */}
      <div className="flex items-start gap-3 p-4 bg-status-warning/15 border border-status-warning/30 rounded-lg">
        <AlertTriangle className="w-5 h-5 text-status-warning flex-shrink-0 mt-0.5" />
        <div className="text-sm">
          <p className="font-medium text-text-primary">Keep your API keys secure</p>
          <p className="text-text-muted mt-1">
            API keys provide full access to your account. Never share them publicly or commit them to version control.
          </p>
        </div>
      </div>

      {/* New Key Created - Show Secret */}
      {newSecretKey && (
        <div className="card p-6 border-status-success/30 bg-status-success/5">
          <div className="flex items-start gap-3 mb-4">
            <Check className="w-5 h-5 text-status-success flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-text-primary">
                API Key Created Successfully
              </h3>
              <p className="text-sm text-text-muted mt-1">
                Copy your secret key now. You won&apos;t be able to see it again.
              </p>
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-text-muted mb-1">
                Secret Key
              </label>
              <div className="flex items-center gap-2">
                <code className="flex-1 px-3 py-2 bg-surface-overlay rounded text-sm font-mono text-text-primary overflow-x-auto">
                  {showSecret ? newSecretKey : "••••••••••••••••••••••••••••••••"}
                </code>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowSecret(!showSecret)}
                  aria-label={showSecret ? "Hide secret key" : "Show secret key"}
                >
                  {showSecret ? (
                    <EyeOff className="w-4 h-4" aria-hidden="true" />
                  ) : (
                    <Eye className="w-4 h-4" aria-hidden="true" />
                  )}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => copyToClipboard(newSecretKey, "Secret key")}
                  aria-label="Copy secret key to clipboard"
                >
                  <Copy className="w-4 h-4" aria-hidden="true" />
                </Button>
              </div>
            </div>

            <Button
              variant="outline"
              onClick={() => {
                setNewSecretKey(null);
                setIsCreating(false);
              }}
            >
              Done
            </Button>
          </div>
        </div>
      )}

      {/* Create New Key Form */}
      {isCreating && !newSecretKey && (
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <Key className="w-5 h-5 text-accent" />
            </div>
            <h2 className="text-sm font-semibold text-text-primary">
              Create New API Key
            </h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Key Name
              </label>
              <input
                type="text"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="e.g., Production Server, CI/CD Pipeline"
                className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent"
                autoFocus
              />
              <p className="text-xs text-text-muted mt-1">
                A descriptive name to help you identify this key
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Expiration (optional)
              </label>
              <select
                value={expiresInDays || ""}
                onChange={(e) =>
                  setExpiresInDays(
                    e.target.value ? Number(e.target.value) : undefined
                  )
                }
                className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
              >
                <option value="">Never expires</option>
                <option value="30">30 days</option>
                <option value="60">60 days</option>
                <option value="90">90 days</option>
                <option value="180">180 days</option>
                <option value="365">1 year</option>
              </select>
            </div>

            <div className="flex items-center gap-3 pt-2">
              <Button
                variant="outline"
                onClick={() => {
                  setIsCreating(false);
                  setNewKeyName("");
                  setExpiresInDays(undefined);
                }}
              >
                Cancel
              </Button>
              <Button
                onClick={handleCreate}
                disabled={createApiKey.isPending}
                className="shadow-glow-sm"
              >
                {createApiKey.isPending ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Key className="w-4 h-4 mr-2" />
                    Create Key
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* API Keys List */}
      <div className="card">
        <div className="p-4 border-b border-border">
          <h2 className="text-sm font-semibold text-text-primary">
            Active API Keys
          </h2>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-text-muted">
            Loading API keys...
          </div>
        ) : apiKeys.length === 0 ? (
          <div className="p-8 text-center">
            <Key className="w-12 h-12 mx-auto text-text-muted mb-4" />
            <h3 className="text-lg font-semibold text-text-primary mb-2">
              No API keys yet
            </h3>
            <p className="text-text-muted mb-6">
              Create an API key to start using the API programmatically
            </p>
            {!isCreating && (
              <Button onClick={() => setIsCreating(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Create API Key
              </Button>
            )}
          </div>
        ) : (
          <div className="divide-y divide-border">
            {apiKeys.map((key: ApiKey) => {
              const expired = isExpired(key.expiresAt);

              return (
                <div
                  key={key.id}
                  className={cn(
                    "p-4 flex items-center justify-between",
                    expired && "opacity-60"
                  )}
                >
                  <div className="flex items-center gap-4">
                    <div
                      className={cn(
                        "w-10 h-10 rounded-lg flex items-center justify-center",
                        expired
                          ? "bg-status-error/15"
                          : "bg-accent-subtle"
                      )}
                    >
                      <Key
                        className={cn(
                          "w-5 h-5",
                          expired ? "text-status-error" : "text-accent"
                        )}
                      />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-text-primary">
                          {key.name}
                        </p>
                        {expired && (
                          <span className="text-xs px-1.5 py-0.5 rounded bg-status-error/15 text-status-error">
                            Expired
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-xs text-text-muted">
                        <span className="font-mono">{key.prefix}...</span>
                        <span>Created {formatDate(key.createdAt)}</span>
                        {key.lastUsedAt && (
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            Last used {formatDate(key.lastUsedAt)}
                          </span>
                        )}
                        {key.expiresAt && (
                          <span>
                            {expired ? "Expired" : "Expires"}{" "}
                            {formatDate(key.expiresAt)}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(key.prefix, "Key prefix")}
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDelete(key.id)}
                      disabled={deletingId === key.id}
                    >
                      {deletingId === key.id ? (
                        <RefreshCw className="w-4 h-4 animate-spin" />
                      ) : (
                        <Trash2 className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
