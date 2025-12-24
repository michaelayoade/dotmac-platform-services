import { Suspense, type ElementType } from "react";
import Link from "next/link";
import {
  Plus,
  Server,
  Activity,
  Cpu,
  HardDrive,
  MemoryStick,
  Globe,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  RefreshCw,
  MoreHorizontal,
  ExternalLink,
  Terminal,
  Settings,
  Trash2,
  Pause,
  Play,
} from "lucide-react";
import { Button } from "@/lib/dotmac/core";

import { cn } from "@/lib/utils";
import {
  getDeployments as fetchDeployments,
  type Deployment as APIDeployment,
} from "@/lib/api/deployments";
import { safeApi } from "@/lib/api/safe-api";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Deployments",
  description: "Infrastructure and deployment management",
};

// Display interface for DeploymentCard component
interface DeploymentDisplay {
  id: string;
  name: string;
  tenant: {
    id: string;
    name: string;
  };
  environment: "production" | "staging" | "development";
  status: "running" | "deploying" | "stopped" | "failed" | "pending";
  region: string;
  version: string;
  resources: {
    cpu: number;
    memory: number;
    storage: number;
  };
  metrics: {
    cpuUsage: number;
    memoryUsage: number;
    requestsPerSec: number;
    errorRate: number;
  };
  lastDeployed: string;
  createdAt: string;
}

// Map API deployment to display format
function mapDeploymentToDisplay(deployment: APIDeployment): DeploymentDisplay {
  const statusMap: Record<string, DeploymentDisplay["status"]> = {
    running: "running",
    pending: "pending",
    stopped: "stopped",
    failed: "failed",
    provisioning: "deploying",
    scaling: "deploying",
  };

  // Parse resource strings like "2" or "2 vCPU" to numbers
  const parseResource = (value: string | undefined, defaultVal: number): number => {
    if (!value) return defaultVal;
    const match = value.match(/[\d.]+/);
    return match ? parseFloat(match[0]) : defaultVal;
  };

  return {
    id: deployment.id,
    name: deployment.name,
    tenant: {
      id: deployment.tenantId,
      name: deployment.tenantId, // Would need tenant lookup for actual name
    },
    environment: deployment.environment,
    status: statusMap[deployment.status] || "pending",
    region: deployment.region,
    version: deployment.version,
    resources: {
      cpu: parseResource(deployment.resources.cpu, 2),
      memory: parseResource(deployment.resources.memory, 8),
      storage: parseResource(deployment.resources.storage, 50),
    },
    metrics: {
      // Metrics would need separate API call for real values
      cpuUsage: deployment.health?.status === "healthy" ? 45 : 0,
      memoryUsage: deployment.health?.status === "healthy" ? 55 : 0,
      requestsPerSec: deployment.health?.status === "healthy" ? 100 : 0,
      errorRate: deployment.health?.status === "unhealthy" ? 5 : 0.1,
    },
    lastDeployed: deployment.lastDeployedAt || deployment.updatedAt,
    createdAt: deployment.createdAt,
  };
}

export default async function DeploymentsPage() {
  const { deployments: apiDeployments } = await safeApi(
    () => fetchDeployments({ pageSize: 50 }),
    { deployments: [], totalCount: 0, pageCount: 1 }
  );
  const deployments = apiDeployments.map(mapDeploymentToDisplay);
  const stats = {
    total: deployments.length,
    running: deployments.filter((d) => d.status === "running").length,
    deploying: deployments.filter((d) => d.status === "deploying").length,
    failed: deployments.filter((d) => d.status === "failed").length,
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Deployments</h1>
          <p className="page-description">
            Manage infrastructure, monitor resources, and deploy instances
          </p>
        </div>
        <Link href="/deployments/new">
          <Button className="shadow-glow-sm hover:shadow-glow">
            <Plus className="w-4 h-4 mr-2" />
            New Deployment
          </Button>
        </Link>
      </div>

      {/* Stats */}
      <div className="quick-stats">
        <StatCard
          label="Total Deployments"
          value={stats.total}
          icon={Server}
        />
        <StatCard
          label="Running"
          value={stats.running}
          icon={CheckCircle}
          iconColor="text-status-success"
        />
        <StatCard
          label="Deploying"
          value={stats.deploying}
          icon={RefreshCw}
          iconColor="text-status-info"
          animate
        />
        <StatCard
          label="Failed"
          value={stats.failed}
          icon={XCircle}
          iconColor="text-status-error"
        />
      </div>

      {/* Deployments List */}
      <div className="space-y-4">
        {deployments.map((deployment, index) => (
          <DeploymentCard key={deployment.id} deployment={deployment} index={index} />
        ))}
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  icon: Icon,
  iconColor = "text-text-muted",
  animate = false,
}: {
  label: string;
  value: number;
  icon: ElementType;
  iconColor?: string;
  animate?: boolean;
}) {
  return (
    <div className="quick-stat">
      <div className="flex items-center justify-between mb-2">
        <Icon className={cn("w-5 h-5", iconColor, animate && "animate-spin")} />
      </div>
      <p className="metric-value text-2xl">{value}</p>
      <p className="metric-label">{label}</p>
    </div>
  );
}

function DeploymentCard({ deployment, index }: { deployment: DeploymentDisplay; index: number }) {
  const statusConfig: Record<
    DeploymentDisplay["status"],
    { class: string; label: string; icon: ElementType; animate: boolean }
  > = {
    running: { class: "status-badge--success", label: "Running", icon: CheckCircle, animate: false },
    deploying: { class: "status-badge--info", label: "Deploying", icon: RefreshCw, animate: true },
    stopped: { class: "bg-surface-overlay text-text-muted", label: "Stopped", icon: Pause, animate: false },
    failed: { class: "status-badge--error", label: "Failed", icon: XCircle, animate: false },
    pending: { class: "status-badge--warning", label: "Pending", icon: Clock, animate: false },
  };

  const envConfig = {
    production: { class: "bg-status-error/15 text-status-error", label: "Production" },
    staging: { class: "bg-status-warning/15 text-status-warning", label: "Staging" },
    development: { class: "bg-status-info/15 text-status-info", label: "Development" },
  };

  const status = statusConfig[deployment.status];
  const env = envConfig[deployment.environment];
  const StatusIcon = status.icon;

  return (
    <div
      className="card p-6 animate-fade-up"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className="flex flex-col lg:flex-row lg:items-center gap-6">
        {/* Main Info */}
        <div className="flex-1">
          <div className="flex items-start gap-4">
            {/* Icon */}
            <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-accent/20 to-highlight/20 flex items-center justify-center">
              <Server className="w-6 h-6 text-accent" />
            </div>

            {/* Details */}
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-1">
                <Link
                  href={`/deployments/${deployment.id}`}
                  className="text-lg font-semibold text-text-primary hover:text-accent transition-colors"
                >
                  {deployment.name}
                </Link>
                <span className={cn("status-badge", status.class)}>
                  <StatusIcon
                    className={cn("w-3 h-3", status.animate && "animate-spin")}
                  />
                  {status.label}
                </span>
                <span className={cn("text-2xs font-semibold px-2 py-0.5 rounded", env.class)}>
                  {env.label}
                </span>
              </div>

              <div className="flex items-center gap-4 text-sm text-text-muted">
                <span className="flex items-center gap-1">
                  <Globe className="w-4 h-4" />
                  {deployment.region}
                </span>
                <span>v{deployment.version}</span>
                <span>{deployment.tenant.name}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Resource Usage */}
        <div className="grid grid-cols-4 gap-4 lg:gap-6">
          <ResourceMetric
            label="CPU"
            value={deployment.metrics.cpuUsage}
            max={100}
            unit="%"
            icon={Cpu}
          />
          <ResourceMetric
            label="Memory"
            value={deployment.metrics.memoryUsage}
            max={100}
            unit="%"
            icon={MemoryStick}
          />
          <ResourceMetric
            label="Requests"
            value={deployment.metrics.requestsPerSec}
            unit="/s"
            icon={Activity}
            noProgress
          />
          <ResourceMetric
            label="Errors"
            value={deployment.metrics.errorRate}
            unit="%"
            icon={AlertTriangle}
            noProgress
            alert={deployment.metrics.errorRate > 1}
          />
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 lg:ml-4">
          <button className="p-2 rounded-md text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors">
            <Terminal className="w-4 h-4" />
          </button>
          <button className="p-2 rounded-md text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors">
            <Settings className="w-4 h-4" />
          </button>
          <button className="p-2 rounded-md text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors">
            <MoreHorizontal className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-border-subtle text-xs text-text-muted">
        <div className="flex items-center gap-4">
          <span>
            Resources: {deployment.resources.cpu} vCPU • {deployment.resources.memory}GB RAM •{" "}
            {deployment.resources.storage}GB Storage
          </span>
        </div>
        <span>
          Last deployed: {new Date(deployment.lastDeployed).toLocaleString()}
        </span>
      </div>
    </div>
  );
}

function ResourceMetric({
  label,
  value,
  max,
  unit,
  icon: Icon,
  noProgress = false,
  alert = false,
}: {
  label: string;
  value: number;
  max?: number;
  unit: string;
  icon: ElementType;
  noProgress?: boolean;
  alert?: boolean;
}) {
  const percentage = max ? (value / max) * 100 : 0;
  const isHigh = percentage > 80;

  return (
    <div className="text-center">
      <div className="flex items-center justify-center gap-1 mb-1">
        <Icon
          className={cn(
            "w-4 h-4",
            alert
              ? "text-status-error"
              : isHigh
              ? "text-status-warning"
              : "text-text-muted"
          )}
        />
        <span
          className={cn(
            "text-lg font-semibold tabular-nums",
            alert
              ? "text-status-error"
              : isHigh
              ? "text-status-warning"
              : "text-text-primary"
          )}
        >
          {value.toFixed(value < 10 ? 1 : 0)}
          <span className="text-xs text-text-muted">{unit}</span>
        </span>
      </div>
      {!noProgress && max && (
        <div className="h-1 bg-surface-overlay rounded-full overflow-hidden">
          <div
            className={cn(
              "h-full rounded-full transition-all",
              isHigh ? "bg-status-warning" : "bg-accent"
            )}
            style={{ width: `${Math.min(percentage, 100)}%` }}
          />
        </div>
      )}
      <p className="text-2xs text-text-muted mt-1 uppercase tracking-wider">{label}</p>
    </div>
  );
}
