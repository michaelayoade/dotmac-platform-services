"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  ArrowLeft,
  Key,
  FolderKey,
  Plus,
  X,
  Trash2,
  Eye,
  EyeOff,
} from "lucide-react";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { PageHeader } from "@/components/shared/page-header";
import { useCreateSecret } from "@/lib/hooks/api/use-secrets";

interface KeyValuePair {
  key: string;
  value: string;
  hidden: boolean;
}

export default function NewSecretPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();

  const createSecret = useCreateSecret();

  // Get initial path from URL query param
  const initialPath = searchParams.get("path") || "";

  const [path, setPath] = useState(initialPath);
  const [keyValues, setKeyValues] = useState<KeyValuePair[]>([
    { key: "", value: "", hidden: true },
  ]);

  const handleAddKeyValue = () => {
    setKeyValues([...keyValues, { key: "", value: "", hidden: true }]);
  };

  const handleRemoveKeyValue = (index: number) => {
    if (keyValues.length <= 1) {
      toast({ title: "At least one key-value pair is required", variant: "error" });
      return;
    }
    setKeyValues(keyValues.filter((_, i) => i !== index));
  };

  const handleUpdateKeyValue = (
    index: number,
    field: "key" | "value",
    value: string
  ) => {
    const updated = [...keyValues];
    updated[index][field] = value;
    setKeyValues(updated);
  };

  const handleToggleHidden = (index: number) => {
    const updated = [...keyValues];
    updated[index].hidden = !updated[index].hidden;
    setKeyValues(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!path.trim()) {
      toast({ title: "Path is required", variant: "error" });
      return;
    }

    // Filter out empty key-value pairs and validate
    const validPairs = keyValues.filter((kv) => kv.key.trim());
    if (validPairs.length === 0) {
      toast({ title: "At least one key-value pair is required", variant: "error" });
      return;
    }

    // Convert to data object
    const data = validPairs.reduce(
      (acc, { key, value }) => {
        acc[key.trim()] = value;
        return acc;
      },
      {} as Record<string, unknown>
    );

    try {
      await createSecret.mutateAsync({
        path: path.trim(),
        data,
      });

      toast({
        title: "Secret created",
        description: `Secret at ${path} has been created successfully.`,
      });

      router.push(`/settings/secrets/${encodeURIComponent(path.trim())}`);
    } catch {
      toast({
        title: "Failed to create secret",
        description: "Please try again.",
        variant: "error",
      });
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-up">
      <PageHeader
        title="New Secret"
        breadcrumbs={[
          { label: "Settings", href: "/settings" },
          { label: "Secrets", href: "/settings/secrets" },
          { label: "New" },
        ]}
        actions={
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        }
      />

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Path */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <FolderKey className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Secret Path</h3>
              <p className="text-sm text-text-muted">Where to store this secret</p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Path <span className="text-status-error">*</span>
            </label>
            <Input
              value={path}
              onChange={(e) => setPath(e.target.value)}
              placeholder="secret/myapp/database"
            />
            <p className="text-xs text-text-muted mt-1">
              Use forward slashes to organize secrets into folders (e.g., secret/production/api-key)
            </p>
          </div>
        </Card>

        {/* Key-Value Pairs */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
                <Key className="w-5 h-5 text-highlight" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-text-primary">Secret Data</h3>
                <p className="text-sm text-text-muted">Key-value pairs for this secret</p>
              </div>
            </div>
            <Button type="button" variant="outline" size="sm" onClick={handleAddKeyValue}>
              <Plus className="w-4 h-4 mr-1" />
              Add Field
            </Button>
          </div>

          <div className="space-y-3">
            {keyValues.map((kv, index) => (
              <div key={index} className="flex items-center gap-2">
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
              </div>
            ))}
          </div>

          <p className="text-xs text-text-muted mt-4">
            Secret values are encrypted at rest and in transit
          </p>
        </Card>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-4">
          <Button type="button" variant="ghost" onClick={() => router.back()}>
            Cancel
          </Button>
          <Button type="submit" disabled={createSecret.isPending}>
            {createSecret.isPending ? "Creating..." : "Create Secret"}
          </Button>
        </div>
      </form>
    </div>
  );
}
