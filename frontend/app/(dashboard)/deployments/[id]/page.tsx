"use client";

import { use, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Play,
  Square,
  RefreshCcw,
  Trash2,
  Settings,
  ArrowUpCircle,
  Activity,
  Cpu,
  HardDrive,
  Server,
  Clock,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Terminal,
  Scale,
  TrendingUp,
  Globe,
} from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";
import { Button, Card } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { ConfirmDialog, useConfirmDialog } from "@/components/shared/confirm-dialog";
import { ActivityTimeline, type ActivityItem } from "@/components/shared/activity-timeline";
import { DeploymentMetricsCharts } from "@/components/features/deployments/deployment-metrics-charts";
import {
  useDeployment,
  useDeploymentStatus,
  useDeploymentMetrics,
  useDeleteDeployment,
  useRestartDeployment,
  useProvisionDeployment,
  useDestroyDeployment,
  useScaleDeployment,
} from "@/lib/hooks/api/use-deployments";

interface DeploymentDetailPageProps {
  params: Promise<{ id: string }>;
}

const statusColors: Record<string, { bg: string; text: string; icon: React.ElementType }> = {
  running: { bg: "bg-status-success/15", text: "text-status-success", icon: CheckCircle2 },
  pending: { bg: "bg-status-warning/15", text: "text-status-warning", icon: Clock },
  stopped: { bg: "bg-surface-overlay", text: "text-text-muted", icon: Square },
  failed: { bg: "bg-status-error/15", text: "text-status-error", icon: XCircle },
  provisioning: { bg: "bg-status-info/15", text: "text-status-info", icon: RefreshCcw },
  destroying: { bg: "bg-status-error/15", text: "text-status-error", icon: Trash2 },
};

const envColors: Record<string, { bg: string; text: string }> = {
  production: { bg: "bg-status-error/15", text: "text-status-error" },
  staging: { bg: "bg-status-warning/15", text: "text-status-warning" },
  development: { bg: "bg-status-info/15", text: "text-status-info" },
};

export default function DeploymentDetailPage({ params }: DeploymentDetailPageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  const [scaleReplicas, setScaleReplicas] = useState<number | null>(null);

  // Data fetching
  const { data: deployment, isLoading, error, refetch } = useDeployment(id);
  const { data: status } = useDeploymentStatus(id, { refetchInterval: 5000 });
  const { data: metrics } = useDeploymentMetrics(id);

  // Mutations
  const deleteDeployment = useDeleteDeployment();
  const restartDeployment = useRestartDeployment();
  const provisionDeployment = useProvisionDeployment();
  const destroyDeployment = useDestroyDeployment();
  const scaleDeployment = useScaleDeployment();

  const handleDelete = async () => {
    const confirmed = await confirm({
      title: "Delete Deployment",
      description: `Are you sure you want to delete "${deployment?.name}"? This will permanently remove all associated resources.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deleteDeployment.mutateAsync(id);
        toast({
          title: "Deployment deleted",
          description: "The deployment has been removed.",
        });
        router.push("/deployments");
      } catch {
        toast({
          title: "Error",
          description: "Failed to delete deployment.",
          variant: "error",
        });
      }
    }
  };

  const handleRestart = async () => {
    try {
      await restartDeployment.mutateAsync(id);
      toast({ title: "Deployment restarting" });
    } catch {
      toast({ title: "Failed to restart", variant: "error" });
    }
  };

  const handleProvision = async () => {
    try {
      await provisionDeployment.mutateAsync(id);
      toast({ title: "Deployment provisioning" });
    } catch {
      toast({ title: "Failed to provision", variant: "error" });
    }
  };

  const handleDestroy = async () => {
    const confirmed = await confirm({
      title: "Destroy Deployment",
      description: "This will stop and remove all running instances. The deployment configuration will remain.",
      variant: "warning",
    });

    if (confirmed) {
      try {
        await destroyDeployment.mutateAsync(id);
        toast({ title: "Deployment destroying" });
      } catch {
        toast({ title: "Failed to destroy", variant: "error" });
      }
    }
  };

  const handleScale = async () => {
    if (scaleReplicas === null) return;

    try {
      await scaleDeployment.mutateAsync({ id, data: { replicas: scaleReplicas } });
      toast({ title: `Scaled to ${scaleReplicas} replicas` });
      setScaleReplicas(null);
    } catch {
      toast({ title: "Failed to scale", variant: "error" });
    }
  };

  if (isLoading) {
    return <DeploymentDetailSkeleton />;
  }

  if (error || !deployment) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="text-status-error mb-4">
          <Server className="w-12 h-12" />
        </div>
        <h2 className="text-xl font-semibold text-text-primary mb-2">Deployment not found</h2>
        <p className="text-text-muted mb-6">
          The deployment doesn&apos;t exist or you don&apos;t have access.
        </p>
        <Button onClick={() => router.push("/deployments")}>Back to Deployments</Button>
      </div>
    );
  }

  const statusInfo = statusColors[deployment.status] || statusColors.pending;
  const StatusIcon = statusInfo.icon;
  const envInfo = envColors[deployment.environment] || envColors.development;

  const isRunning = deployment.status === "running";
  const isStopped = deployment.status === "stopped" || deployment.status === "failed";

  const events: ActivityItem[] = (status?.events || []).slice(0, 5).map((event, idx) => ({
    id: `event-${idx}`,
    type: event.type,
    title: event.type.charAt(0).toUpperCase() + event.type.slice(1),
    description: event.message,
    timestamp: event.timestamp,
    iconColor: event.type === "error" ? "text-status-error" : "text-text-muted",
    iconBgColor: event.type === "error" ? "bg-status-error/15" : "bg-surface-overlay",
  }));

  return (
    <div className="space-y-8 animate-fade-up">
      {dialog}

      {/* Page Header */}
      <PageHeader
        title={deployment.name}
        breadcrumbs={[
          { label: "Deployments", href: "/deployments" },
          { label: deployment.name },
        ]}
        badge={
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium",
                statusInfo.bg,
                statusInfo.text
              )}
            >
              <StatusIcon className="w-3 h-3" />
              {deployment.status.charAt(0).toUpperCase() + deployment.status.slice(1)}
            </span>
            <span
              className={cn(
                "inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium",
                envInfo.bg,
                envInfo.text
              )}
            >
              {deployment.environment}
            </span>
          </div>
        }
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => refetch()}>
              <RefreshCcw className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              onClick={() => router.push(`/deployments/${id}/logs`)}
            >
              <Terminal className="w-4 h-4 mr-2" />
              Logs
            </Button>
            <Button variant="outline" onClick={() => router.push(`/deployments/${id}/settings`)}>
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </Button>
          </div>
        }
      />

      {/* Quick Actions Bar */}
      <div className="flex items-center gap-3 p-4 bg-surface-overlay rounded-lg">
        {isStopped ? (
          <Button onClick={handleProvision} disabled={provisionDeployment.isPending}>
            <Play className="w-4 h-4 mr-2" />
            {provisionDeployment.isPending ? "Provisioning..." : "Start"}
          </Button>
        ) : (
          <Button variant="outline" onClick={handleDestroy} disabled={destroyDeployment.isPending}>
            <Square className="w-4 h-4 mr-2" />
            {destroyDeployment.isPending ? "Stopping..." : "Stop"}
          </Button>
        )}

        <Button
          variant="outline"
          onClick={handleRestart}
          disabled={!isRunning || restartDeployment.isPending}
        >
          <RefreshCcw className="w-4 h-4 mr-2" />
          {restartDeployment.isPending ? "Restarting..." : "Restart"}
        </Button>

        <Button variant="outline" onClick={() => router.push(`/deployments/${id}/upgrade`)}>
          <ArrowUpCircle className="w-4 h-4 mr-2" />
          Upgrade
        </Button>

        <div className="flex-1" />

        <div className="flex items-center gap-2">
          <span className="text-sm text-text-muted">Replicas:</span>
          <select
            value={scaleReplicas ?? deployment.replicas}
            onChange={(e) => setScaleReplicas(parseInt(e.target.value))}
            className="px-3 py-1.5 bg-surface-primary border border-border-subtle rounded-md text-sm"
          >
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
          {scaleReplicas !== null && scaleReplicas !== deployment.replicas && (
            <Button size="sm" onClick={handleScale} disabled={scaleDeployment.isPending}>
              <Scale className="w-4 h-4 mr-1" />
              Apply
            </Button>
          )}
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Details & Metrics */}
        <div className="lg:col-span-2 space-y-6">
          {/* Deployment Info */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Deployment Information</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <p className="text-xs text-text-muted mb-1">Image</p>
                <code className="text-sm text-accent font-mono">{deployment.image}</code>
              </div>
              <div>
                <p className="text-xs text-text-muted mb-1">Version</p>
                <p className="text-sm text-text-primary font-mono">{deployment.version}</p>
              </div>
              <div>
                <p className="text-xs text-text-muted mb-1">Region</p>
                <div className="flex items-center gap-1.5">
                  <Globe className="w-4 h-4 text-text-muted" />
                  <span className="text-sm text-text-primary">{deployment.region || "us-east-1"}</span>
                </div>
              </div>
              <div>
                <p className="text-xs text-text-muted mb-1">Created</p>
                <p className="text-sm text-text-primary">
                  {format(new Date(deployment.createdAt), "MMM d, yyyy")}
                </p>
              </div>
              <div>
                <p className="text-xs text-text-muted mb-1">Last Updated</p>
                <p className="text-sm text-text-primary">
                  {formatDistanceToNow(new Date(deployment.updatedAt), { addSuffix: true })}
                </p>
              </div>
              <div>
                <p className="text-xs text-text-muted mb-1">Replicas</p>
                <p className="text-sm text-text-primary">
                  {status?.replicas?.ready ?? 0} / {status?.replicas?.desired ?? deployment.replicas} ready
                </p>
              </div>
            </div>
          </Card>

          {/* Resources */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Resource Allocation</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="p-4 rounded-lg bg-surface-overlay">
                <div className="flex items-center gap-2 mb-2">
                  <Cpu className="w-5 h-5 text-accent" />
                  <span className="text-sm font-medium text-text-secondary">CPU</span>
                </div>
                <p className="text-2xl font-semibold text-text-primary">
                  {deployment.resources?.cpu || "1"}
                  <span className="text-sm font-normal text-text-muted ml-1">vCPU</span>
                </p>
                {metrics?.cpu !== undefined && (
                  <div className="mt-2">
                    <div className="h-1.5 bg-surface-primary rounded-full overflow-hidden">
                      <div
                        className="h-full bg-accent rounded-full transition-all"
                        style={{ width: `${Math.min(metrics.cpu, 100)}%` }}
                      />
                    </div>
                    <p className="text-xs text-text-muted mt-1">{metrics.cpu.toFixed(1)}% used</p>
                  </div>
                )}
              </div>

              <div className="p-4 rounded-lg bg-surface-overlay">
                <div className="flex items-center gap-2 mb-2">
                  <Activity className="w-5 h-5 text-status-success" />
                  <span className="text-sm font-medium text-text-secondary">Memory</span>
                </div>
                <p className="text-2xl font-semibold text-text-primary">
                  {deployment.resources?.memory || "1GB"}
                </p>
                {metrics?.memory !== undefined && (
                  <div className="mt-2">
                    <div className="h-1.5 bg-surface-primary rounded-full overflow-hidden">
                      <div
                        className="h-full bg-status-success rounded-full transition-all"
                        style={{ width: `${Math.min(metrics.memory, 100)}%` }}
                      />
                    </div>
                    <p className="text-xs text-text-muted mt-1">{metrics.memory.toFixed(1)}% used</p>
                  </div>
                )}
              </div>

              <div className="p-4 rounded-lg bg-surface-overlay">
                <div className="flex items-center gap-2 mb-2">
                  <HardDrive className="w-5 h-5 text-highlight" />
                  <span className="text-sm font-medium text-text-secondary">Storage</span>
                </div>
                <p className="text-2xl font-semibold text-text-primary">
                  {deployment.resources?.storage || "10GB"}
                </p>
                {metrics?.storage !== undefined && (
                  <div className="mt-2">
                    <div className="h-1.5 bg-surface-primary rounded-full overflow-hidden">
                      <div
                        className="h-full bg-highlight rounded-full transition-all"
                        style={{ width: `${Math.min(metrics.storage, 100)}%` }}
                      />
                    </div>
                    <p className="text-xs text-text-muted mt-1">{metrics.storage.toFixed(1)}% used</p>
                  </div>
                )}
              </div>
            </div>
          </Card>

          {/* Performance Metrics Charts */}
          {isRunning && (
            <DeploymentMetricsCharts
              deploymentId={id}
              isLoading={false}
            />
          )}

          {/* Events */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">Recent Events</h3>
              <Button variant="ghost" size="sm">
                View All
              </Button>
            </div>
            {events.length > 0 ? (
              <ActivityTimeline activities={events} />
            ) : (
              <p className="text-sm text-text-muted py-4 text-center">No recent events</p>
            )}
          </Card>
        </div>

        {/* Right Column - Status & Metrics */}
        <div className="space-y-6">
          {/* Health Status */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Health Status</h3>
            <div className="flex items-center gap-3 mb-4">
              {status?.health === "healthy" ? (
                <CheckCircle2 className="w-8 h-8 text-status-success" />
              ) : status?.health === "degraded" ? (
                <AlertTriangle className="w-8 h-8 text-status-warning" />
              ) : (
                <XCircle className="w-8 h-8 text-status-error" />
              )}
              <div>
                <p className="text-lg font-semibold text-text-primary capitalize">
                  {status?.health || "Unknown"}
                </p>
                <p className="text-sm text-text-muted">
                  Last checked {status?.lastUpdated ? formatDistanceToNow(new Date(status.lastUpdated), { addSuffix: true }) : "never"}
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-text-muted">Desired</span>
                <span className="text-text-primary">{status?.replicas?.desired ?? deployment.replicas}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-text-muted">Ready</span>
                <span className="text-status-success">{status?.replicas?.ready ?? 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-text-muted">Available</span>
                <span className="text-text-primary">{status?.replicas?.available ?? 0}</span>
              </div>
            </div>
          </Card>

          {/* Traffic Metrics */}
          {metrics && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-text-primary mb-4">Traffic</h3>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
                    <TrendingUp className="w-5 h-5 text-accent" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Requests/min</p>
                    <p className="text-lg font-semibold text-text-primary">
                      {metrics.requestsPerMinute?.toLocaleString() ?? 0}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
                    <Clock className="w-5 h-5 text-status-success" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Avg Latency</p>
                    <p className="text-lg font-semibold text-text-primary">
                      {metrics.averageLatency ?? 0}ms
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-status-error/15 flex items-center justify-center">
                    <AlertTriangle className="w-5 h-5 text-status-error" />
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Error Rate</p>
                    <p className="text-lg font-semibold text-text-primary">
                      {(metrics.errorRate ?? 0).toFixed(2)}%
                    </p>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Environment Variables Preview */}
          {deployment.envVars && Object.keys(deployment.envVars).length > 0 && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-text-primary mb-4">Environment</h3>
              <div className="space-y-2">
                {Object.entries(deployment.envVars).slice(0, 5).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-sm">
                    <span className="text-text-muted font-mono">{key}</span>
                    <span className="text-text-secondary truncate max-w-[120px]">
                      {value.includes("SECRET") || value.includes("KEY") ? "••••••" : value}
                    </span>
                  </div>
                ))}
                {Object.keys(deployment.envVars).length > 5 && (
                  <p className="text-xs text-text-muted pt-2">
                    +{Object.keys(deployment.envVars).length - 5} more variables
                  </p>
                )}
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

function DeploymentDetailSkeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      <div className="flex items-center justify-between">
        <div>
          <div className="h-4 w-32 bg-surface-overlay rounded mb-2" />
          <div className="h-8 w-64 bg-surface-overlay rounded" />
        </div>
        <div className="flex gap-2">
          <div className="h-10 w-24 bg-surface-overlay rounded" />
          <div className="h-10 w-24 bg-surface-overlay rounded" />
        </div>
      </div>

      <div className="h-16 bg-surface-overlay rounded-lg" />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6 h-48" />
          <div className="card p-6 h-48" />
        </div>
        <div className="space-y-6">
          <div className="card p-6 h-48" />
          <div className="card p-6 h-48" />
        </div>
      </div>
    </div>
  );
}
