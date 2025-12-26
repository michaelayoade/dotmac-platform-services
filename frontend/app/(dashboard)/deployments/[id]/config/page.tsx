"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Settings,
  Save,
  Plus,
  Trash2,
  RefreshCw,
  Eye,
  EyeOff,
  Cpu,
  HardDrive,
  Activity,
  Globe,
  Server,
  AlertCircle,
} from "lucide-react";
import { Button, useToast } from "@/lib/dotmac/core";
import { cn } from "@/lib/utils";
import {
  useDeployment,
  useDeploymentConfig,
  useUpdateDeploymentConfig,
  type DeploymentConfig,
  type UpdateConfigData,
} from "@/lib/hooks/api/use-deployments";

export default function DeploymentConfigPage() {
  const params = useParams();
  const { toast } = useToast();
  const deploymentId = params.id as string;

  const { data: deployment, isLoading: deploymentLoading } = useDeployment(deploymentId);
  const { data: config, isLoading: configLoading } = useDeploymentConfig(deploymentId);
  const updateConfig = useUpdateDeploymentConfig();

  const [envVars, setEnvVars] = useState<{ key: string; value: string; hidden: boolean }[]>([]);
  const [resources, setResources] = useState({ cpu: "", memory: "" });
  const [scaling, setScaling] = useState({ minReplicas: 1, maxReplicas: 3, targetCpuUtilization: 80 });
  const [healthCheck, setHealthCheck] = useState({
    enabled: true,
    path: "/health",
    interval: 30,
    timeout: 5,
    healthyThreshold: 2,
    unhealthyThreshold: 3,
  });
  const [network, setNetwork] = useState({
    port: 8080,
    protocol: "http" as "http" | "https" | "grpc",
    publicAccess: true,
    customDomain: "",
  });

  const [hasChanges, setHasChanges] = useState(false);

  // Populate form with config data
  useEffect(() => {
    if (config) {
      setEnvVars(
        Object.entries(config.envVars || {}).map(([key, value]) => ({
          key,
          value,
          hidden: key.toLowerCase().includes("secret") || key.toLowerCase().includes("password"),
        }))
      );
      setResources({
        cpu: config.resources?.cpu || "",
        memory: config.resources?.memory || "",
      });
      setScaling(config.scaling);
      setHealthCheck(config.healthCheck);
      setNetwork({
        ...config.network,
        customDomain: config.network.customDomain ?? "",
      });
      setHasChanges(false);
    }
  }, [config]);

  const handleAddEnvVar = () => {
    setEnvVars([...envVars, { key: "", value: "", hidden: false }]);
    setHasChanges(true);
  };

  const handleRemoveEnvVar = (index: number) => {
    setEnvVars(envVars.filter((_, i) => i !== index));
    setHasChanges(true);
  };

  const handleEnvVarChange = (index: number, field: "key" | "value", value: string) => {
    const updated = [...envVars];
    updated[index][field] = value;
    setEnvVars(updated);
    setHasChanges(true);
  };

  const toggleEnvVarVisibility = (index: number) => {
    const updated = [...envVars];
    updated[index].hidden = !updated[index].hidden;
    setEnvVars(updated);
  };

  const handleSave = async () => {
    const data: UpdateConfigData = {
      envVars: Object.fromEntries(envVars.filter((e) => e.key).map((e) => [e.key, e.value])),
      resources: {
        cpu: resources.cpu,
        memory: resources.memory,
      },
      scaling,
      healthCheck,
      network,
    };

    try {
      await updateConfig.mutateAsync({ id: deploymentId, data });
      toast({
        title: "Configuration saved",
        description: "Your deployment configuration has been updated.",
        variant: "success",
      });
      setHasChanges(false);
    } catch {
      toast({
        title: "Error",
        description: "Failed to save configuration.",
        variant: "error",
      });
    }
  };

  const isLoading = deploymentLoading || configLoading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <RefreshCw className="w-8 h-8 animate-spin text-text-muted" />
      </div>
    );
  }

  if (!deployment) {
    return (
      <div className="text-center py-12">
        <Server className="w-12 h-12 mx-auto text-text-muted mb-4" />
        <h2 className="text-lg font-semibold text-text-primary mb-2">
          Deployment not found
        </h2>
        <Link href="/deployments">
          <Button variant="outline">Back to Deployments</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumbs */}
      <div className="flex items-center gap-2 text-sm text-text-muted">
        <Link href="/deployments" className="hover:text-text-secondary">
          Deployments
        </Link>
        <span>/</span>
        <Link href={`/deployments/${deploymentId}`} className="hover:text-text-secondary">
          {deployment.name}
        </Link>
        <span>/</span>
        <span className="text-text-primary">Configuration</span>
      </div>

      {/* Page Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <Link
            href={`/deployments/${deploymentId}`}
            className="p-2 rounded-lg hover:bg-surface-hover transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-text-muted" />
          </Link>
          <div>
            <h1 className="text-2xl font-semibold text-text-primary">
              Configuration
            </h1>
            <p className="text-text-muted mt-1">
              {deployment.name} • {deployment.environment}
            </p>
          </div>
        </div>

        <Button
          onClick={handleSave}
          disabled={!hasChanges || updateConfig.isPending}
          className={cn(hasChanges && "shadow-glow-sm")}
        >
          {updateConfig.isPending ? (
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Save className="w-4 h-4 mr-2" />
          )}
          Save Changes
        </Button>
      </div>

      {/* Unsaved Changes Warning */}
      {hasChanges && (
        <div className="flex items-center gap-3 p-4 bg-status-warning/15 border border-status-warning/30 rounded-lg">
          <AlertCircle className="w-5 h-5 text-status-warning flex-shrink-0" />
          <p className="text-sm text-text-primary">
            You have unsaved changes. Save your configuration to apply them.
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Environment Variables */}
        <div className="card lg:col-span-2">
          <div className="p-4 border-b border-border flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Settings className="w-5 h-5 text-text-muted" />
              <h2 className="text-sm font-semibold text-text-primary">
                Environment Variables
              </h2>
            </div>
            <Button variant="outline" size="sm" onClick={handleAddEnvVar}>
              <Plus className="w-3 h-3 mr-1" />
              Add Variable
            </Button>
          </div>
          <div className="p-4 space-y-3">
            {envVars.length === 0 ? (
              <p className="text-sm text-text-muted text-center py-4">
                No environment variables configured
              </p>
            ) : (
              envVars.map((envVar, index) => (
                <div key={index} className="flex items-center gap-3">
                  <input
                    type="text"
                    value={envVar.key}
                    onChange={(e) => handleEnvVarChange(index, "key", e.target.value)}
                    placeholder="KEY"
                    className="flex-1 px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent font-mono text-sm"
                  />
                  <span className="text-text-muted">=</span>
                  <div className="flex-1 relative">
                    <input
                      type={envVar.hidden ? "password" : "text"}
                      value={envVar.value}
                      onChange={(e) => handleEnvVarChange(index, "value", e.target.value)}
                      placeholder="value"
                      className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent font-mono text-sm pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => toggleEnvVarVisibility(index)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary"
                    >
                      {envVar.hidden ? (
                        <Eye className="w-4 h-4" />
                      ) : (
                        <EyeOff className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleRemoveEnvVar(index)}
                    className="text-status-error hover:text-status-error"
                  >
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Resource Limits */}
        <div className="card">
          <div className="p-4 border-b border-border">
            <div className="flex items-center gap-3">
              <Cpu className="w-5 h-5 text-text-muted" />
              <h2 className="text-sm font-semibold text-text-primary">
                Resource Limits
              </h2>
            </div>
          </div>
          <div className="p-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                CPU (millicores)
              </label>
              <input
                type="text"
                value={resources.cpu}
                onChange={(e) => {
                  setResources((r) => ({ ...r, cpu: e.target.value }));
                  setHasChanges(true);
                }}
                placeholder="500m"
                className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent"
              />
              <p className="text-xs text-text-muted mt-1">
                e.g., 500m = 0.5 CPU cores
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Memory
              </label>
              <input
                type="text"
                value={resources.memory}
                onChange={(e) => {
                  setResources((r) => ({ ...r, memory: e.target.value }));
                  setHasChanges(true);
                }}
                placeholder="512Mi"
                className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent"
              />
              <p className="text-xs text-text-muted mt-1">
                e.g., 512Mi = 512 MB
              </p>
            </div>
          </div>
        </div>

        {/* Scaling Settings */}
        <div className="card">
          <div className="p-4 border-b border-border">
            <div className="flex items-center gap-3">
              <HardDrive className="w-5 h-5 text-text-muted" />
              <h2 className="text-sm font-semibold text-text-primary">
                Scaling Settings
              </h2>
            </div>
          </div>
          <div className="p-4 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Min Replicas
                </label>
                <input
                  type="number"
                  min="0"
                  value={scaling.minReplicas}
                  onChange={(e) => {
                    setScaling((s) => ({ ...s, minReplicas: parseInt(e.target.value) || 0 }));
                    setHasChanges(true);
                  }}
                  className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Max Replicas
                </label>
                <input
                  type="number"
                  min="1"
                  value={scaling.maxReplicas}
                  onChange={(e) => {
                    setScaling((s) => ({ ...s, maxReplicas: parseInt(e.target.value) || 1 }));
                    setHasChanges(true);
                  }}
                  className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Target CPU Utilization (%)
              </label>
              <input
                type="number"
                min="1"
                max="100"
                value={scaling.targetCpuUtilization}
                onChange={(e) => {
                  setScaling((s) => ({ ...s, targetCpuUtilization: parseInt(e.target.value) || 80 }));
                  setHasChanges(true);
                }}
                className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
              />
            </div>
          </div>
        </div>

        {/* Health Check */}
        <div className="card">
          <div className="p-4 border-b border-border">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Activity className="w-5 h-5 text-text-muted" />
                <h2 className="text-sm font-semibold text-text-primary">
                  Health Check
                </h2>
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={healthCheck.enabled}
                  onChange={(e) => {
                    setHealthCheck((h) => ({ ...h, enabled: e.target.checked }));
                    setHasChanges(true);
                  }}
                  className="w-4 h-4 text-accent border-border rounded focus:ring-accent"
                />
                <span className="text-sm text-text-muted">Enabled</span>
              </label>
            </div>
          </div>
          <div className={cn("p-4 space-y-4", !healthCheck.enabled && "opacity-50 pointer-events-none")}>
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Health Check Path
              </label>
              <input
                type="text"
                value={healthCheck.path}
                onChange={(e) => {
                  setHealthCheck((h) => ({ ...h, path: e.target.value }));
                  setHasChanges(true);
                }}
                placeholder="/health"
                className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent font-mono"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Interval (seconds)
                </label>
                <input
                  type="number"
                  min="5"
                  value={healthCheck.interval}
                  onChange={(e) => {
                    setHealthCheck((h) => ({ ...h, interval: parseInt(e.target.value) || 30 }));
                    setHasChanges(true);
                  }}
                  className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Timeout (seconds)
                </label>
                <input
                  type="number"
                  min="1"
                  value={healthCheck.timeout}
                  onChange={(e) => {
                    setHealthCheck((h) => ({ ...h, timeout: parseInt(e.target.value) || 5 }));
                    setHasChanges(true);
                  }}
                  className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Network Settings */}
        <div className="card">
          <div className="p-4 border-b border-border">
            <div className="flex items-center gap-3">
              <Globe className="w-5 h-5 text-text-muted" />
              <h2 className="text-sm font-semibold text-text-primary">
                Network Settings
              </h2>
            </div>
          </div>
          <div className="p-4 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Port
                </label>
                <input
                  type="number"
                  min="1"
                  max="65535"
                  value={network.port}
                  onChange={(e) => {
                    setNetwork((n) => ({ ...n, port: parseInt(e.target.value) || 8080 }));
                    setHasChanges(true);
                  }}
                  className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Protocol
                </label>
                <select
                  value={network.protocol}
                  onChange={(e) => {
                    setNetwork((n) => ({ ...n, protocol: e.target.value as "http" | "https" | "grpc" }));
                    setHasChanges(true);
                  }}
                  className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                >
                  <option value="http">HTTP</option>
                  <option value="https">HTTPS</option>
                  <option value="grpc">gRPC</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Custom Domain (optional)
              </label>
              <input
                type="text"
                value={network.customDomain || ""}
                onChange={(e) => {
                  setNetwork((n) => ({ ...n, customDomain: e.target.value }));
                  setHasChanges(true);
                }}
                placeholder="api.example.com"
                className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent"
              />
            </div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={network.publicAccess}
                onChange={(e) => {
                  setNetwork((n) => ({ ...n, publicAccess: e.target.checked }));
                  setHasChanges(true);
                }}
                className="w-4 h-4 text-accent border-border rounded focus:ring-accent"
              />
              <span className="text-sm text-text-secondary">
                Enable public access
              </span>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}
