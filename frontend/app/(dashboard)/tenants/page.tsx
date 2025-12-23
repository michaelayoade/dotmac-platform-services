import { Suspense, type ElementType } from "react";
import Link from "next/link";
import {
  Plus,
  Building2,
  Users,
  CreditCard,
  Activity,
  MoreHorizontal,
  ExternalLink,
  Settings,
  Pause,
  Trash2,
  CheckCircle,
  Clock,
  AlertTriangle,
  XCircle,
} from "lucide-react";
import { Button } from "@dotmac/core";

import { getTenants, type Tenant } from "@/lib/api/tenants";
import { cn } from "@/lib/utils";

export const metadata = {
  title: "Tenants",
  description: "Manage organizations and their configurations",
};

export default async function TenantsPage({
  searchParams,
}: {
  searchParams: { view?: string; status?: string };
}) {
  const view = searchParams.view || "grid";
  const { tenants, stats } = await getTenants();

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Tenants</h1>
          <p className="page-description">
            Manage organizations, subscriptions, and configurations
          </p>
        </div>
        <Link href="/tenants/new">
          <Button className="shadow-glow-sm hover:shadow-glow">
            <Plus className="w-4 h-4 mr-2" />
            New Tenant
          </Button>
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="quick-stats">
        <StatCard
          label="Total Tenants"
          value={stats.total}
          icon={Building2}
          trend={stats.totalChange}
        />
        <StatCard
          label="Active"
          value={stats.active}
          icon={CheckCircle}
          iconColor="text-status-success"
        />
        <StatCard
          label="Trial"
          value={stats.trial}
          icon={Clock}
          iconColor="text-status-warning"
        />
        <StatCard
          label="Suspended"
          value={stats.suspended}
          icon={AlertTriangle}
          iconColor="text-status-error"
        />
      </div>

      {/* View Toggle */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Link
            href="/tenants?view=grid"
            className={cn(
              "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
              view === "grid"
                ? "bg-accent text-text-inverse"
                : "text-text-muted hover:text-text-secondary hover:bg-surface-overlay"
            )}
          >
            Grid View
          </Link>
          <Link
            href="/tenants?view=list"
            className={cn(
              "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
              view === "list"
                ? "bg-accent text-text-inverse"
                : "text-text-muted hover:text-text-secondary hover:bg-surface-overlay"
            )}
          >
            List View
          </Link>
        </div>

        <div className="flex items-center gap-2">
          <select className="h-9 px-3 rounded-md bg-surface-overlay border border-border text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-accent">
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="trial">Trial</option>
            <option value="suspended">Suspended</option>
          </select>
          <select className="h-9 px-3 rounded-md bg-surface-overlay border border-border text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-accent">
            <option value="">All Plans</option>
            <option value="enterprise">Enterprise</option>
            <option value="professional">Professional</option>
            <option value="starter">Starter</option>
          </select>
        </div>
      </div>

      {/* Tenant Grid */}
      <Suspense fallback={<TenantGridSkeleton />}>
        {view === "grid" ? (
          <TenantGrid tenants={tenants} />
        ) : (
          <TenantList tenants={tenants} />
        )}
      </Suspense>
    </div>
  );
}

function StatCard({
  label,
  value,
  icon: Icon,
  iconColor = "text-text-muted",
  trend,
}: {
  label: string;
  value: number;
  icon: ElementType;
  iconColor?: string;
  trend?: number;
}) {
  return (
    <div className="quick-stat">
      <div className="flex items-center justify-between mb-2">
        <Icon className={cn("w-5 h-5", iconColor)} />
        {trend !== undefined && (
          <span
            className={cn(
              "text-xs font-medium",
              trend >= 0 ? "text-status-success" : "text-status-error"
            )}
          >
            {trend >= 0 ? "+" : ""}
            {trend}%
          </span>
        )}
      </div>
      <p className="metric-value text-2xl">{value}</p>
      <p className="metric-label">{label}</p>
    </div>
  );
}

function TenantGrid({ tenants }: { tenants: Tenant[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {tenants.map((tenant, index) => (
        <TenantCard key={tenant.id} tenant={tenant} index={index} />
      ))}
    </div>
  );
}

function TenantCard({ tenant, index }: { tenant: Tenant; index: number }) {
  const statusConfig = {
    active: { class: "status-badge--success", label: "Active", icon: CheckCircle },
    trial: { class: "status-badge--warning", label: "Trial", icon: Clock },
    suspended: { class: "status-badge--error", label: "Suspended", icon: AlertTriangle },
    inactive: { class: "bg-surface-overlay text-text-muted", label: "Inactive", icon: XCircle },
  };

  const config = statusConfig[tenant.status] || statusConfig.inactive;
  const StatusIcon = config.icon;

  return (
    <div
      className="card card--interactive p-5 animate-fade-up"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent/20 to-highlight/20 flex items-center justify-center">
            <Building2 className="w-5 h-5 text-accent" />
          </div>
          <div>
            <Link
              href={`/tenants/${tenant.id}`}
              className="font-semibold text-text-primary hover:text-accent transition-colors"
            >
              {tenant.name}
            </Link>
            <p className="text-xs text-text-muted">{tenant.slug}</p>
          </div>
        </div>
        <TenantActions tenant={tenant} />
      </div>

      {/* Status & Plan */}
      <div className="flex items-center gap-2 mb-4">
        <span className={cn("status-badge", config.class)}>
          <StatusIcon className="w-3 h-3" />
          {config.label}
        </span>
        <span className="text-xs text-text-muted px-2 py-0.5 rounded-full bg-surface-overlay">
          {tenant.plan}
        </span>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-3 gap-4 pt-4 border-t border-border">
        <div>
          <p className="text-lg font-semibold text-text-primary tabular-nums">
            {tenant.userCount}
          </p>
          <p className="text-2xs text-text-muted uppercase tracking-wider">Users</p>
        </div>
        <div>
          <p className="text-lg font-semibold text-text-primary tabular-nums">
            ${(tenant.mrr / 100).toLocaleString()}
          </p>
          <p className="text-2xs text-text-muted uppercase tracking-wider">MRR</p>
        </div>
        <div>
          <p className="text-lg font-semibold text-text-primary tabular-nums">
            {tenant.deploymentCount}
          </p>
          <p className="text-2xs text-text-muted uppercase tracking-wider">Deploys</p>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-border-subtle">
        <span className="text-xs text-text-muted">
          Created {new Date(tenant.createdAt).toLocaleDateString()}
        </span>
        <Link
          href={`/tenants/${tenant.id}`}
          className="text-xs text-accent hover:text-accent-hover font-medium inline-flex items-center gap-1"
        >
          View Details <ExternalLink className="w-3 h-3" />
        </Link>
      </div>
    </div>
  );
}

function TenantList({ tenants }: { tenants: Tenant[] }) {
  const statusConfig = {
    active: { class: "status-badge--success", label: "Active" },
    trial: { class: "status-badge--warning", label: "Trial" },
    suspended: { class: "status-badge--error", label: "Suspended" },
    inactive: { class: "bg-surface-overlay text-text-muted", label: "Inactive" },
  };

  return (
    <div className="card overflow-hidden">
      <table className="data-table">
        <thead>
          <tr>
            <th>Organization</th>
            <th>Status</th>
            <th>Plan</th>
            <th>Users</th>
            <th>MRR</th>
            <th>Created</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {tenants.map((tenant) => {
            const config = statusConfig[tenant.status] || statusConfig.inactive;
            return (
              <tr key={tenant.id} className="group">
                <td>
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-md bg-gradient-to-br from-accent/20 to-highlight/20 flex items-center justify-center">
                      <Building2 className="w-4 h-4 text-accent" />
                    </div>
                    <div>
                      <Link
                        href={`/tenants/${tenant.id}`}
                        className="font-medium text-text-primary hover:text-accent"
                      >
                        {tenant.name}
                      </Link>
                      <p className="text-xs text-text-muted">{tenant.slug}</p>
                    </div>
                  </div>
                </td>
                <td>
                  <span className={cn("status-badge", config.class)}>
                    {config.label}
                  </span>
                </td>
                <td>
                  <span className="text-sm text-text-secondary">{tenant.plan}</span>
                </td>
                <td>
                  <span className="text-sm text-text-primary tabular-nums">
                    {tenant.userCount}
                  </span>
                </td>
                <td>
                  <span className="text-sm font-medium text-text-primary tabular-nums">
                    ${(tenant.mrr / 100).toLocaleString()}
                  </span>
                </td>
                <td>
                  <span className="text-sm text-text-muted tabular-nums">
                    {new Date(tenant.createdAt).toLocaleDateString()}
                  </span>
                </td>
                <td>
                  <TenantActions tenant={tenant} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function TenantActions({ tenant }: { tenant: Tenant }) {
  return (
    <div className="relative group/actions">
      <button className="p-1.5 rounded-md text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors">
        <MoreHorizontal className="w-4 h-4" />
      </button>
      {/* Dropdown would go here - simplified for now */}
    </div>
  );
}

function TenantGridSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="card p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg skeleton" />
            <div className="space-y-2">
              <div className="h-4 w-32 skeleton" />
              <div className="h-3 w-20 skeleton" />
            </div>
          </div>
          <div className="flex gap-2 mb-4">
            <div className="h-5 w-16 skeleton rounded-full" />
            <div className="h-5 w-20 skeleton rounded-full" />
          </div>
          <div className="grid grid-cols-3 gap-4 pt-4 border-t border-border">
            {[1, 2, 3].map((j) => (
              <div key={j}>
                <div className="h-5 w-12 skeleton mb-1" />
                <div className="h-3 w-10 skeleton" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
