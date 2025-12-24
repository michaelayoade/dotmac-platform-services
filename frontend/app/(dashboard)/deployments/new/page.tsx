"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  ArrowLeft,
  Server,
  Globe,
  Cpu,
  HardDrive,
  Box,
  Plus,
  X,
  Activity,
} from "lucide-react";
import { Button, Card, Input, Select } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  createDeploymentSchema,
  type CreateDeploymentData,
  REGIONS,
  CPU_OPTIONS,
  MEMORY_OPTIONS,
  STORAGE_OPTIONS,
} from "@/lib/schemas";
import { useCreateDeployment } from "@/lib/hooks/api/use-deployments";

const environments = [
  { value: "development", label: "Development", color: "bg-status-info/15 text-status-info" },
  { value: "staging", label: "Staging", color: "bg-status-warning/15 text-status-warning" },
  { value: "production", label: "Production", color: "bg-status-error/15 text-status-error" },
];

export default function NewDeploymentPage() {
  const router = useRouter();
  const { toast } = useToast();
  const createDeployment = useCreateDeployment();

  const [envVars, setEnvVars] = useState<Array<{ key: string; value: string }>>([]);
  const [newEnvKey, setNewEnvKey] = useState("");
  const [newEnvValue, setNewEnvValue] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setValue,
    watch,
  } = useForm<CreateDeploymentData>({
    resolver: zodResolver(createDeploymentSchema),
    defaultValues: {
      name: "",
      environment: "development",
      region: "us-east-1",
      version: "latest",
      replicas: 1,
      resources: {
        cpu: "1",
        memory: "1GB",
        storage: "10GB",
      },
    },
  });

  const selectedEnvironment = watch("environment");
  const selectedRegion = watch("region");
  const replicas = watch("replicas");
  const resourcesCpu = watch("resources.cpu");
  const resourcesMemory = watch("resources.memory");
  const resourcesStorage = watch("resources.storage");

  const handleAddEnvVar = () => {
    if (!newEnvKey.trim()) return;
    setEnvVars([...envVars, { key: newEnvKey.trim(), value: newEnvValue }]);
    setNewEnvKey("");
    setNewEnvValue("");
  };

  const handleRemoveEnvVar = (index: number) => {
    setEnvVars(envVars.filter((_, i) => i !== index));
  };

  const onSubmit = async (data: CreateDeploymentData) => {
    try {
      const envVarsRecord = envVars.reduce(
        (acc, { key, value }) => {
          acc[key] = value;
          return acc;
        },
        {} as Record<string, string>
      );

      const result = await createDeployment.mutateAsync({
        name: data.name,
        environment: data.environment,
        image: `${data.name}:${data.version}`, // Construct image from name:version
        version: data.version,
        replicas: data.replicas,
        resources: {
          cpu: data.resources.cpu,
          memory: data.resources.memory,
          storage: data.resources.storage,
        },
        envVars: Object.keys(envVarsRecord).length > 0 ? envVarsRecord : undefined,
      });

      toast({
        title: "Deployment created",
        description: `${data.name} is being provisioned.`,
      });

      router.push(`/deployments/${result.id}`);
    } catch {
      toast({
        title: "Error",
        description: "Failed to create deployment. Please try again.",
        variant: "error",
      });
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="New Deployment"
        breadcrumbs={[
          { label: "Deployments", href: "/deployments" },
          { label: "New Deployment" },
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
              <p className="text-sm text-text-muted">Deployment name and version</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Deployment Name <span className="text-status-error">*</span>
              </label>
              <Input
                {...register("name")}
                placeholder="my-service"
                className={cn(errors.name && "border-status-error")}
              />
              <p className="text-xs text-text-muted mt-1">
                Lowercase letters, numbers, and hyphens only (3-63 characters)
              </p>
              {errors.name && (
                <p className="text-xs text-status-error mt-1">{errors.name.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Version <span className="text-status-error">*</span>
              </label>
              <Input
                {...register("version")}
                placeholder="v1.0.0 or latest"
                className={cn(errors.version && "border-status-error")}
              />
              {errors.version && (
                <p className="text-xs text-status-error mt-1">{errors.version.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Replicas <span className="text-status-error">*</span>
              </label>
              <select
                value={replicas}
                onChange={(e) => setValue("replicas", parseInt(e.target.value))}
                className="w-full px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
              >
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                  <option key={n} value={n}>
                    {n} {n === 1 ? "replica" : "replicas"}
                  </option>
                ))}
              </select>
              {errors.replicas && (
                <p className="text-xs text-status-error mt-1">{errors.replicas.message}</p>
              )}
            </div>
          </div>
        </Card>

        {/* Environment & Region */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
              <Globe className="w-5 h-5 text-status-info" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Environment & Region</h3>
              <p className="text-sm text-text-muted">Where to deploy</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Environment <span className="text-status-error">*</span>
              </label>
              <div className="flex gap-2">
                {environments.map((env) => (
                  <button
                    key={env.value}
                    type="button"
                    onClick={() => setValue("environment", env.value as CreateDeploymentData["environment"])}
                    className={cn(
                      "flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-all border",
                      selectedEnvironment === env.value
                        ? cn(env.color, "border-current")
                        : "bg-surface-overlay text-text-muted border-transparent hover:bg-surface-overlay/70"
                    )}
                  >
                    {env.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Region <span className="text-status-error">*</span>
              </label>
              <select
                value={selectedRegion}
                onChange={(e) => setValue("region", e.target.value)}
                className="w-full px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
              >
                {REGIONS.map((region) => (
                  <option key={region.value} value={region.value}>
                    {region.label}
                  </option>
                ))}
              </select>
              {errors.region && (
                <p className="text-xs text-status-error mt-1">{errors.region.message}</p>
              )}
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
              <p className="text-sm text-text-muted">CPU, memory, and storage allocation</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                <Cpu className="w-4 h-4 inline mr-1" />
                CPU <span className="text-status-error">*</span>
              </label>
              <select
                value={resourcesCpu}
                onChange={(e) => setValue("resources.cpu", e.target.value)}
                className="w-full px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
              >
                {CPU_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                <Activity className="w-4 h-4 inline mr-1" />
                Memory <span className="text-status-error">*</span>
              </label>
              <select
                value={resourcesMemory}
                onChange={(e) => setValue("resources.memory", e.target.value)}
                className="w-full px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
              >
                {MEMORY_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                <HardDrive className="w-4 h-4 inline mr-1" />
                Storage
              </label>
              <select
                value={resourcesStorage}
                onChange={(e) => setValue("resources.storage", e.target.value)}
                className="w-full px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
              >
                {STORAGE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Resource Summary */}
          <div className="mt-4 p-4 bg-surface-overlay rounded-lg">
            <p className="text-sm text-text-muted">
              Estimated resources per replica: <span className="text-text-primary font-medium">{resourcesCpu} vCPU</span>,{" "}
              <span className="text-text-primary font-medium">{resourcesMemory}</span> RAM,{" "}
              <span className="text-text-primary font-medium">{resourcesStorage}</span> storage
            </p>
            <p className="text-sm text-text-muted mt-1">
              Total with {replicas} replicas:{" "}
              <span className="text-accent font-medium">
                {parseFloat(resourcesCpu) * replicas} vCPU, {parseFloat(resourcesMemory)} × {replicas} RAM
              </span>
            </p>
          </div>
        </Card>

        {/* Environment Variables */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
              <Box className="w-5 h-5 text-status-success" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Environment Variables</h3>
              <p className="text-sm text-text-muted">Configuration for your deployment</p>
            </div>
          </div>

          {/* Add new env var */}
          <div className="flex items-center gap-2 mb-4">
            <Input
              value={newEnvKey}
              onChange={(e) => setNewEnvKey(e.target.value.toUpperCase())}
              placeholder="KEY"
              className="flex-1 font-mono"
            />
            <Input
              value={newEnvValue}
              onChange={(e) => setNewEnvValue(e.target.value)}
              placeholder="value"
              className="flex-[2] font-mono"
            />
            <Button type="button" variant="outline" onClick={handleAddEnvVar}>
              <Plus className="w-4 h-4" />
            </Button>
          </div>

          {/* Env vars list */}
          {envVars.length > 0 ? (
            <div className="space-y-2">
              {envVars.map((envVar, index) => (
                <div
                  key={index}
                  className="flex items-center gap-2 p-2 bg-surface-overlay rounded-lg"
                >
                  <code className="flex-1 text-sm text-accent">{envVar.key}</code>
                  <code className="flex-[2] text-sm text-text-secondary truncate">
                    {envVar.key.includes("SECRET") || envVar.key.includes("KEY") || envVar.key.includes("PASSWORD")
                      ? "••••••••"
                      : envVar.value}
                  </code>
                  <button
                    type="button"
                    onClick={() => handleRemoveEnvVar(index)}
                    className="p-1 hover:text-status-error transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-text-muted py-4 text-center">
              No environment variables configured
            </p>
          )}
        </Card>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-4">
          <Button type="button" variant="ghost" onClick={() => router.back()}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting || createDeployment.isPending}>
            {isSubmitting || createDeployment.isPending ? "Creating..." : "Create Deployment"}
          </Button>
        </div>
      </form>
    </div>
  );
}
