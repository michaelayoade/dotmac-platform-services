"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  ArrowLeft,
  Server,
  Cpu,
  HardDrive,
  Box,
  Plus,
  X,
  Loader2,
} from "lucide-react";
import { Button, Card, Input, Select } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  updateDeploymentSchema,
  type UpdateDeploymentData,
  CPU_OPTIONS,
  MEMORY_OPTIONS,
  STORAGE_OPTIONS,
} from "@/lib/schemas";
import { useDeployment, useUpdateDeployment } from "@/lib/hooks/api/use-deployments";

interface EditDeploymentPageProps {
  params: Promise<{ id: string }>;
}

const environments = [
  { value: "development", label: "Development", color: "bg-status-info/15 text-status-info" },
  { value: "staging", label: "Staging", color: "bg-status-warning/15 text-status-warning" },
  { value: "production", label: "Production", color: "bg-status-error/15 text-status-error" },
];

export default function EditDeploymentPage({ params }: EditDeploymentPageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();

  const { data: deployment, isLoading } = useDeployment(id);
  const updateDeployment = useUpdateDeployment();

  const [envVars, setEnvVars] = useState<Array<{ key: string; value: string }>>([]);
  const [newEnvKey, setNewEnvKey] = useState("");
  const [newEnvValue, setNewEnvValue] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting, isDirty },
    setValue,
    watch,
    reset,
  } = useForm<UpdateDeploymentData>({
    resolver: zodResolver(updateDeploymentSchema),
  });

  const selectedEnvironment = watch("environment");
  const resourcesCpu = watch("resources.cpu");
  const resourcesMemory = watch("resources.memory");
  const resourcesStorage = watch("resources.storage");

  // Populate form when deployment loads
  useEffect(() => {
    if (deployment) {
      reset({
        name: deployment.name || "",
        environment: deployment.environment || "development",
        version: deployment.version || "latest",
        replicas: deployment.replicas || 1,
        resources: {
          cpu: deployment.resources?.cpu || "1",
          memory: deployment.resources?.memory || "1GB",
          storage: deployment.resources?.storage || "10GB",
        },
      });
      // Convert env vars object to array
      if (deployment.envVars) {
        const vars = Object.entries(deployment.envVars).map(([key, value]) => ({
          key,
          value: String(value),
        }));
        setEnvVars(vars);
      }
    }
  }, [deployment, reset]);

  const handleAddEnvVar = () => {
    if (!newEnvKey.trim()) return;
    setEnvVars([...envVars, { key: newEnvKey.trim(), value: newEnvValue }]);
    setNewEnvKey("");
    setNewEnvValue("");
  };

  const handleRemoveEnvVar = (index: number) => {
    setEnvVars(envVars.filter((_, i) => i !== index));
  };

  const onSubmit = async (data: UpdateDeploymentData) => {
    try {
      const envVarsRecord = envVars.reduce(
        (acc, { key, value }) => {
          acc[key] = value;
          return acc;
        },
        {} as Record<string, string>
      );

      await updateDeployment.mutateAsync({
        id,
        data: {
          name: data.name,
          environment: data.environment,
          version: data.version,
          replicas: data.replicas,
          resources: data.resources ? {
            cpu: data.resources.cpu,
            memory: data.resources.memory,
            storage: data.resources.storage,
          } : undefined,
          envVars: Object.keys(envVarsRecord).length > 0 ? envVarsRecord : undefined,
        },
      });

      toast({
        title: "Deployment updated",
        description: "Changes have been saved successfully.",
      });

      router.push(`/deployments/${id}`);
    } catch {
      toast({
        title: "Error",
        description: "Failed to update deployment. Please try again.",
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

  if (!deployment) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <h2 className="text-xl font-semibold text-text-primary mb-2">Deployment not found</h2>
        <p className="text-text-muted mb-6">
          The deployment you&apos;re looking for doesn&apos;t exist.
        </p>
        <Button onClick={() => router.push("/deployments")}>Back to Deployments</Button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title={`Edit ${deployment.name}`}
        breadcrumbs={[
          { label: "Deployments", href: "/deployments" },
          { label: deployment.name, href: `/deployments/${id}` },
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
              <Server className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Basic Information</h3>
              <p className="text-sm text-text-muted">Update deployment details</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Name <span className="text-status-error">*</span>
              </label>
              <Input
                {...register("name")}
                placeholder="my-deployment"
                className={cn(errors.name && "border-status-error")}
              />
              {errors.name && (
                <p className="text-xs text-status-error mt-1">{errors.name.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Version
              </label>
              <Input
                {...register("version")}
                placeholder="latest"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Environment
              </label>
              <Select
                value={selectedEnvironment}
                onValueChange={(value) =>
                  setValue("environment", value as UpdateDeploymentData["environment"], { shouldDirty: true })
                }
                options={environments.map((e) => ({ value: e.value, label: e.label }))}
                placeholder="Select environment"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Replicas
              </label>
              <Input
                {...register("replicas", { valueAsNumber: true })}
                type="number"
                min={1}
                max={10}
              />
            </div>
          </div>
        </Card>

        {/* Resources */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
              <Cpu className="w-5 h-5 text-highlight" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Resources</h3>
              <p className="text-sm text-text-muted">Configure compute resources</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                <Cpu className="w-4 h-4 inline mr-1" />
                CPU
              </label>
              <Select
                value={resourcesCpu}
                onValueChange={(value) => setValue("resources.cpu", value, { shouldDirty: true })}
                options={CPU_OPTIONS.map((o) => ({ value: o.value, label: o.label }))}
                placeholder="Select CPU"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                <HardDrive className="w-4 h-4 inline mr-1" />
                Memory
              </label>
              <Select
                value={resourcesMemory}
                onValueChange={(value) => setValue("resources.memory", value, { shouldDirty: true })}
                options={MEMORY_OPTIONS.map((o) => ({ value: o.value, label: o.label }))}
                placeholder="Select Memory"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                <Box className="w-4 h-4 inline mr-1" />
                Storage
              </label>
              <Select
                value={resourcesStorage}
                onValueChange={(value) => setValue("resources.storage", value, { shouldDirty: true })}
                options={STORAGE_OPTIONS.map((o) => ({ value: o.value, label: o.label }))}
                placeholder="Select Storage"
              />
            </div>
          </div>
        </Card>

        {/* Environment Variables */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
              <Box className="w-5 h-5 text-status-info" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Environment Variables</h3>
              <p className="text-sm text-text-muted">Configure environment variables</p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Input
                value={newEnvKey}
                onChange={(e) => setNewEnvKey(e.target.value)}
                placeholder="KEY"
                className="flex-1"
              />
              <Input
                value={newEnvValue}
                onChange={(e) => setNewEnvValue(e.target.value)}
                placeholder="value"
                className="flex-1"
              />
              <Button type="button" variant="outline" onClick={handleAddEnvVar}>
                <Plus className="w-4 h-4" />
              </Button>
            </div>

            {envVars.length > 0 && (
              <div className="space-y-2">
                {envVars.map((env, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-2 p-3 bg-surface-overlay rounded-lg"
                  >
                    <code className="text-sm font-mono text-accent flex-1">{env.key}</code>
                    <code className="text-sm font-mono text-text-secondary flex-1 truncate">
                      {env.value || "(empty)"}
                    </code>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveEnvVar(index)}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
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
              disabled={!isDirty || isSubmitting || updateDeployment.isPending}
            >
              {isSubmitting || updateDeployment.isPending ? "Saving..." : "Save Changes"}
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
