"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { format, formatDistanceToNow } from "date-fns";
import {
  ArrowLeft,
  Key,
  FolderKey,
  Plus,
  Trash2,
  Eye,
  EyeOff,
  Copy,
  RefreshCcw,
  History,
  Shield,
  Calendar,
  Loader2,
} from "lucide-react";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useSecret,
  useSecretMetadata,
  useUpdateSecret,
  useDeleteSecret,
  useRotateSecret,
  useRotationPolicies,
  useSetRotationPolicy,
} from "@/lib/hooks/api/use-secrets";

interface SecretDetailPageProps {
  params: Promise<{ path: string[] }>;
}

interface KeyValuePair {
  key: string;
  value: string;
  hidden: boolean;
}

export default function SecretDetailPage({ params }: SecretDetailPageProps) {
  const { path: pathSegments } = use(params);
  const secretPath = pathSegments.map(decodeURIComponent).join("/");

  const router = useRouter();
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  const { data: secret, isLoading } = useSecret(secretPath);
  const { data: metadata } = useSecretMetadata(secretPath);
  const { data: rotationPolicies } = useRotationPolicies();

  const updateSecret = useUpdateSecret();
  const deleteSecret = useDeleteSecret();
  const rotateSecret = useRotateSecret();
  const setRotationPolicy = useSetRotationPolicy();

  const [isEditing, setIsEditing] = useState(false);
  const [keyValues, setKeyValues] = useState<KeyValuePair[]>([]);
  const [isDirty, setIsDirty] = useState(false);

  // Populate form when secret loads
  useEffect(() => {
    if (secret?.data) {
      const pairs = Object.entries(secret.data).map(([key, value]) => ({
        key,
        value: String(value),
        hidden: true,
      }));
      setKeyValues(pairs.length > 0 ? pairs : [{ key: "", value: "", hidden: true }]);
    }
  }, [secret]);

  const rotationPolicy = rotationPolicies?.find((p) => p.path === secretPath);

  const handleAddKeyValue = () => {
    setKeyValues([...keyValues, { key: "", value: "", hidden: true }]);
    setIsDirty(true);
  };

  const handleRemoveKeyValue = (index: number) => {
    if (keyValues.length <= 1) {
      toast({ title: "At least one key-value pair is required", variant: "error" });
      return;
    }
    setKeyValues(keyValues.filter((_, i) => i !== index));
    setIsDirty(true);
  };

  const handleUpdateKeyValue = (
    index: number,
    field: "key" | "value",
    value: string
  ) => {
    const updated = [...keyValues];
    updated[index][field] = value;
    setKeyValues(updated);
    setIsDirty(true);
  };

  const handleToggleHidden = (index: number) => {
    const updated = [...keyValues];
    updated[index].hidden = !updated[index].hidden;
    setKeyValues(updated);
  };

  const handleDelete = async () => {
    const confirmed = await confirm({
      title: "Delete Secret",
      description: `Are you sure you want to delete "${secretPath}"? This will mark all versions as deleted.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deleteSecret.mutateAsync({ path: secretPath });
        toast({ title: "Secret deleted" });
        router.push("/settings/secrets");
      } catch {
        toast({ title: "Failed to delete secret", variant: "error" });
      }
    }
  };

  const handleRotate = async () => {
    const confirmed = await confirm({
      title: "Rotate Secret",
      description: "This will create a new version with the current values. Applications using this secret will get the new version.",
      variant: "warning",
    });

    if (confirmed) {
      const data = keyValues.reduce(
        (acc, { key, value }) => {
          if (key.trim()) acc[key.trim()] = value;
          return acc;
        },
        {} as Record<string, unknown>
      );

      try {
        await rotateSecret.mutateAsync({ path: secretPath, newData: data });
        toast({ title: "Secret rotated successfully" });
      } catch {
        toast({ title: "Failed to rotate secret", variant: "error" });
      }
    }
  };

  const handleSaveChanges = async () => {
    const validPairs = keyValues.filter((kv) => kv.key.trim());
    if (validPairs.length === 0) {
      toast({ title: "At least one key-value pair is required", variant: "error" });
      return;
    }

    const data = validPairs.reduce(
      (acc, { key, value }) => {
        acc[key.trim()] = value;
        return acc;
      },
      {} as Record<string, unknown>
    );

    try {
      await updateSecret.mutateAsync({ path: secretPath, data });
      toast({ title: "Secret updated" });
      setIsEditing(false);
      setIsDirty(false);
    } catch {
      toast({ title: "Failed to update secret", variant: "error" });
    }
  };

  const handleCancelEdit = () => {
    if (secret?.data) {
      const pairs = Object.entries(secret.data).map(([key, value]) => ({
        key,
        value: String(value),
        hidden: true,
      }));
      setKeyValues(pairs.length > 0 ? pairs : [{ key: "", value: "", hidden: true }]);
    }
    setIsEditing(false);
    setIsDirty(false);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({ title: "Copied to clipboard" });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    );
  }

  if (!secret) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <h2 className="text-xl font-semibold text-text-primary mb-2">Secret not found</h2>
        <p className="text-text-muted mb-6">
          The secret at &quot;{secretPath}&quot; doesn&apos;t exist.
        </p>
        <Button onClick={() => router.push("/settings/secrets")}>Back to Secrets</Button>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-up">
      {dialog}

      <PageHeader
        title={secretPath.split("/").pop() || secretPath}
        breadcrumbs={[
          { label: "Settings", href: "/settings" },
          { label: "Secrets", href: "/settings/secrets" },
          { label: secretPath },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={() => router.back()}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            {isEditing ? (
              <>
                <Button variant="ghost" onClick={handleCancelEdit}>
                  Cancel
                </Button>
                <Button
                  onClick={handleSaveChanges}
                  disabled={!isDirty || updateSecret.isPending}
                >
                  {updateSecret.isPending ? "Saving..." : "Save Changes"}
                </Button>
              </>
            ) : (
              <Button variant="outline" onClick={() => setIsEditing(true)}>
                Edit
              </Button>
            )}
          </div>
        }
      />

      {/* Quick Actions */}
      <div className="flex items-center gap-4 flex-wrap">
        <Button variant="outline" size="sm" onClick={() => copyToClipboard(secretPath)}>
          <Copy className="w-4 h-4 mr-1" />
          Copy Path
        </Button>
        <Button variant="outline" size="sm" onClick={handleRotate}>
          <RefreshCcw className="w-4 h-4 mr-1" />
          Rotate
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleDelete}
          className="text-status-error hover:text-status-error"
        >
          <Trash2 className="w-4 h-4 mr-1" />
          Delete
        </Button>
      </div>

      {/* Path & Metadata */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
            <FolderKey className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary">Secret Info</h3>
            <p className="text-sm text-text-muted">Path and version information</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-text-muted mb-1">Full Path</p>
            <code className="text-sm text-accent bg-surface-overlay px-3 py-2 rounded-lg inline-block">
              {secretPath}
            </code>
          </div>
          <div>
            <p className="text-sm text-text-muted mb-1">Current Version</p>
            <p className="text-lg font-semibold font-mono text-text-primary">
              v{secret.version}
            </p>
          </div>
          <div>
            <p className="text-sm text-text-muted mb-1">Created</p>
            <p className="text-sm text-text-primary">
              {format(new Date(secret.createdAt), "MMM d, yyyy HH:mm")}
            </p>
          </div>
          <div>
            <p className="text-sm text-text-muted mb-1">Last Updated</p>
            <p className="text-sm text-text-primary">
              {formatDistanceToNow(new Date(secret.createdAt), { addSuffix: true })}
            </p>
          </div>
        </div>
      </Card>

      {/* Secret Data */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
              <Key className="w-5 h-5 text-highlight" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Secret Data</h3>
              <p className="text-sm text-text-muted">Key-value pairs</p>
            </div>
          </div>
          {isEditing && (
            <Button type="button" variant="outline" size="sm" onClick={handleAddKeyValue}>
              <Plus className="w-4 h-4 mr-1" />
              Add Field
            </Button>
          )}
        </div>

        <div className="space-y-3">
          {keyValues.map((kv, index) => (
            <div key={index} className="flex items-center gap-2">
              {isEditing ? (
                <>
                  <Input
                    value={kv.key}
                    onChange={(e) => handleUpdateKeyValue(index, "key", e.target.value)}
                    placeholder="KEY"
                    className="flex-1 font-mono"
                  />
                  <div className="relative flex-1">
                    <Input
                      type={kv.hidden ? "password" : "text"}
                      value={kv.value}
                      onChange={(e) => handleUpdateKeyValue(index, "value", e.target.value)}
                      placeholder="value"
                      className="font-mono pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => handleToggleHidden(index)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary"
                    >
                      {kv.hidden ? (
                        <Eye className="w-4 h-4" />
                      ) : (
                        <EyeOff className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemoveKeyValue(index)}
                    disabled={keyValues.length <= 1}
                    className="text-status-error hover:text-status-error"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </>
              ) : (
                <div className="flex items-center gap-2 p-3 bg-surface-overlay rounded-lg flex-1">
                  <code className="text-sm font-mono text-accent flex-shrink-0">{kv.key}</code>
                  <span className="text-text-muted">=</span>
                  <code className="text-sm font-mono text-text-secondary flex-1 truncate">
                    {kv.hidden ? "••••••••" : kv.value}
                  </code>
                  <button
                    onClick={() => handleToggleHidden(index)}
                    className="p-1 text-text-muted hover:text-text-primary"
                  >
                    {kv.hidden ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                  </button>
                  <button
                    onClick={() => copyToClipboard(kv.value)}
                    className="p-1 text-text-muted hover:text-text-primary"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* Rotation Policy */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
            <Calendar className="w-5 h-5 text-status-info" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary">Rotation Policy</h3>
            <p className="text-sm text-text-muted">Automatic rotation schedule</p>
          </div>
        </div>

        {rotationPolicy ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-text-muted mb-1">Status</p>
              <span
                className={cn(
                  "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium",
                  rotationPolicy.isEnabled
                    ? "bg-status-success/15 text-status-success"
                    : "bg-surface-overlay text-text-muted"
                )}
              >
                {rotationPolicy.isEnabled ? "Enabled" : "Disabled"}
              </span>
            </div>
            <div>
              <p className="text-sm text-text-muted mb-1">Rotation Period</p>
              <p className="text-sm text-text-primary">
                Every {rotationPolicy.rotationPeriodDays} days
              </p>
            </div>
            <div>
              <p className="text-sm text-text-muted mb-1">Next Rotation</p>
              <p className="text-sm text-text-primary">
                {rotationPolicy.nextRotationAt
                  ? format(new Date(rotationPolicy.nextRotationAt), "MMM d, yyyy")
                  : "Not scheduled"}
              </p>
            </div>
          </div>
        ) : (
          <p className="text-sm text-text-muted">
            No rotation policy configured. Secrets will not be automatically rotated.
          </p>
        )}
      </Card>

      {/* Version History */}
      {metadata && metadata.versions.length > 0 && (
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-status-warning/15 flex items-center justify-center">
              <History className="w-5 h-5 text-status-warning" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Version History</h3>
              <p className="text-sm text-text-muted">Previous versions of this secret</p>
            </div>
          </div>

          <div className="space-y-2">
            {metadata.versions.slice(0, 10).map((version) => (
              <div
                key={version.version}
                className={cn(
                  "flex items-center justify-between p-3 rounded-lg",
                  version.version === secret.version
                    ? "bg-accent-subtle"
                    : "bg-surface-overlay"
                )}
              >
                <div className="flex items-center gap-3">
                  <span className="font-mono text-sm font-medium text-text-primary">
                    v{version.version}
                  </span>
                  {version.version === secret.version && (
                    <span className="text-xs px-2 py-0.5 rounded bg-accent text-text-inverse">
                      Current
                    </span>
                  )}
                  {version.deletedAt && (
                    <span className="text-xs px-2 py-0.5 rounded bg-status-error/15 text-status-error">
                      Deleted
                    </span>
                  )}
                </div>
                <p className="text-sm text-text-muted">
                  {format(new Date(version.createdAt), "MMM d, yyyy HH:mm")}
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
