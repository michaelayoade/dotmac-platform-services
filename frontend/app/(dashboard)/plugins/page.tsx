"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Puzzle,
  Plus,
  Search,
  Filter,
  RefreshCcw,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Settings,
  Play,
  Pause,
  Trash2,
  Download,
  ExternalLink,
  Shield,
  Zap,
  Database,
  Mail,
  Cloud,
  CreditCard,
} from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";
import { Button, Card, Input, Modal } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { ConfirmDialog, useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  usePlugins,
  usePluginCategories,
  useAvailablePlugins,
  useEnablePlugin,
  useDisablePlugin,
  useRefreshPlugins,
  useTestPlugin,
} from "@/lib/hooks/api/use-plugins";

type PluginStatus = "enabled" | "disabled" | "error" | "outdated";

const statusConfig: Record<PluginStatus, { label: string; color: string; icon: React.ElementType }> = {
  enabled: { label: "Enabled", color: "bg-status-success/15 text-status-success", icon: CheckCircle2 },
  disabled: { label: "Disabled", color: "bg-surface-overlay text-text-muted", icon: XCircle },
  error: { label: "Error", color: "bg-status-error/15 text-status-error", icon: AlertCircle },
  outdated: { label: "Update Available", color: "bg-status-warning/15 text-status-warning", icon: Download },
};

const categoryIcons: Record<string, React.ElementType> = {
  authentication: Shield,
  integrations: Zap,
  database: Database,
  email: Mail,
  cloud: Cloud,
  payment: CreditCard,
  default: Puzzle,
};

export default function PluginsPage() {
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [activeTab, setActiveTab] = useState<"installed" | "marketplace">("installed");

  const { data: plugins, isLoading, refetch } = usePlugins();
  const { data: categories } = usePluginCategories();
  const { data: availablePlugins } = useAvailablePlugins();

  const enablePlugin = useEnablePlugin();
  const disablePlugin = useDisablePlugin();
  const refreshPlugins = useRefreshPlugins();
  const testPlugin = useTestPlugin();

  const installedPlugins = plugins || [];
  const marketplacePlugins = availablePlugins || [];

  const resolvePluginStatus = (plugin: { enabled?: boolean; isEnabled?: boolean }): PluginStatus =>
    plugin.enabled ?? plugin.isEnabled ? "enabled" : "disabled";

  const filteredInstalled = installedPlugins.filter((plugin) => {
    if (searchQuery && !plugin.name.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    if (categoryFilter !== "all" && plugin.category !== categoryFilter) {
      return false;
    }
    if (statusFilter !== "all" && resolvePluginStatus(plugin) !== statusFilter) {
      return false;
    }
    return true;
  });

  const filteredMarketplace = marketplacePlugins.filter((plugin) => {
    if (searchQuery && !plugin.name.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    if (categoryFilter !== "all" && plugin.category !== categoryFilter) {
      return false;
    }
    return true;
  });

  const handleTogglePlugin = async (name: string, isEnabled: boolean) => {
    try {
      if (isEnabled) {
        await disablePlugin.mutateAsync(name);
        toast({ title: "Plugin disabled" });
      } else {
        await enablePlugin.mutateAsync(name);
        toast({ title: "Plugin enabled" });
      }
    } catch {
      toast({ title: "Failed to update plugin", variant: "error" });
    }
  };

  const handleTest = async (name: string) => {
    try {
      const result = await testPlugin.mutateAsync(name);
      if (result.success) {
        toast({ title: "Plugin test passed", description: result.message });
      } else {
        toast({ title: "Plugin test failed", description: result.message, variant: "error" });
      }
    } catch {
      toast({ title: "Failed to test plugin", variant: "error" });
    }
  };

  const handleRefresh = async () => {
    try {
      await refreshPlugins.mutateAsync();
      toast({ title: "Plugins refreshed" });
    } catch {
      toast({ title: "Failed to refresh plugins", variant: "error" });
    }
  };

  if (isLoading) {
    return <PluginsSkeleton />;
  }

  return (
    <div className="space-y-6 animate-fade-up">
      {dialog}

      <PageHeader
        title="Plugins"
        description="Extend platform functionality with plugins"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={() => refetch()}>
              <RefreshCcw className="w-4 h-4" />
            </Button>
            <Button variant="outline" onClick={handleRefresh}>
              <Download className="w-4 h-4 mr-2" />
              Check Updates
            </Button>
          </div>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Installed</p>
          <p className="text-2xl font-semibold text-text-primary">
            {installedPlugins.length}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Enabled</p>
          <p className="text-2xl font-semibold text-status-success">
            {installedPlugins.filter((plugin) => resolvePluginStatus(plugin) === "enabled").length}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Updates Available</p>
          <p className="text-2xl font-semibold text-status-warning">
            {installedPlugins.filter((plugin) => resolvePluginStatus(plugin) === "outdated").length}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Marketplace</p>
          <p className="text-2xl font-semibold text-accent">
            {marketplacePlugins.length}
          </p>
        </Card>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 p-1 bg-surface-overlay rounded-lg w-fit">
        {[
          { id: "installed", label: "Installed Plugins" },
          { id: "marketplace", label: "Marketplace" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            className={cn(
              "px-4 py-2 rounded-md text-sm font-medium transition-colors",
              activeTab === tab.id
                ? "bg-surface-primary text-text-primary shadow-sm"
                : "text-text-muted hover:text-text-secondary"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search plugins..."
            className="pl-10"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-text-muted" />
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
          >
            <option value="all">All Categories</option>
            {categories?.map((cat) => (
              <option key={cat.name} value={cat.name}>
                {cat.name}
              </option>
            ))}
          </select>
          {activeTab === "installed" && (
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
            >
              <option value="all">All Status</option>
              <option value="enabled">Enabled</option>
              <option value="disabled">Disabled</option>
              <option value="error">Error</option>
              <option value="outdated">Update Available</option>
            </select>
          )}
        </div>
      </div>

      {/* Installed Plugins */}
      {activeTab === "installed" && (
        <>
          {filteredInstalled.length === 0 ? (
            <Card className="p-12 text-center">
              <Puzzle className="w-12 h-12 text-text-muted mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-text-primary mb-2">No plugins found</h3>
              <p className="text-text-muted mb-6">
                {searchQuery || categoryFilter !== "all" || statusFilter !== "all"
                  ? "Try adjusting your filters"
                  : "Browse the marketplace to install plugins"}
              </p>
              <Button onClick={() => setActiveTab("marketplace")}>
                Browse Marketplace
              </Button>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredInstalled.map((plugin) => {
                const pluginStatus = resolvePluginStatus(plugin);
                const status = statusConfig[pluginStatus] || statusConfig.disabled;
                const StatusIcon = status.icon;
                const categoryKey = plugin.category?.toLowerCase() ?? "default";
                const CategoryIcon = categoryIcons[categoryKey] || categoryIcons.default;
                const isEnabled = plugin.enabled ?? plugin.isEnabled ?? false;

                return (
                  <Card key={plugin.name} className="p-6 hover:border-border-strong transition-colors">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-lg bg-accent-subtle flex items-center justify-center">
                          <CategoryIcon className="w-6 h-6 text-accent" />
                        </div>
                        <div>
                          <h4 className="font-semibold text-text-primary">{plugin.name}</h4>
                          <p className="text-xs text-text-muted">v{plugin.version}</p>
                        </div>
                      </div>
                      <span className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium", status.color)}>
                        <StatusIcon className="w-3 h-3" />
                        {status.label}
                      </span>
                    </div>

                    {plugin.description && (
                      <p className="text-sm text-text-muted mb-4 line-clamp-2">{plugin.description}</p>
                    )}

                    <div className="flex items-center gap-4 text-xs text-text-muted mb-4">
                      {plugin.category && (
                        <span className="px-2 py-0.5 rounded bg-surface-overlay">
                          {plugin.category}
                        </span>
                      )}
                      {plugin.instanceCount !== undefined && (
                        <span>{plugin.instanceCount} instance{plugin.instanceCount !== 1 ? "s" : ""}</span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 pt-4 border-t border-border-subtle">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleTogglePlugin(plugin.name, isEnabled)}
                      >
                        {isEnabled ? (
                          <>
                            <Pause className="w-3.5 h-3.5 mr-1" />
                            Disable
                          </>
                        ) : (
                          <>
                            <Play className="w-3.5 h-3.5 mr-1" />
                            Enable
                          </>
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleTest(plugin.name)}
                      >
                        Test
                      </Button>
                      <Link href={`/plugins/${plugin.name}`}>
                        <Button variant="ghost" size="sm">
                          <Settings className="w-4 h-4" />
                        </Button>
                      </Link>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* Marketplace */}
      {activeTab === "marketplace" && (
        <>
          {filteredMarketplace.length === 0 ? (
            <Card className="p-12 text-center">
              <Puzzle className="w-12 h-12 text-text-muted mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-text-primary mb-2">No plugins available</h3>
              <p className="text-text-muted">
                {searchQuery || categoryFilter !== "all"
                  ? "Try adjusting your filters"
                  : "Check back later for new plugins"}
              </p>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredMarketplace.map((plugin) => {
                const CategoryIcon = categoryIcons[plugin.category?.toLowerCase()] || categoryIcons.default;
                const isInstalled = installedPlugins.some((p) => p.name === plugin.name);

                return (
                  <Card key={plugin.name} className="p-6 hover:border-border-strong transition-colors">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-lg bg-accent-subtle flex items-center justify-center">
                          <CategoryIcon className="w-6 h-6 text-accent" />
                        </div>
                        <div>
                          <h4 className="font-semibold text-text-primary">{plugin.name}</h4>
                          <p className="text-xs text-text-muted">v{plugin.version}</p>
                        </div>
                      </div>
                      {isInstalled && (
                        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-status-success/15 text-status-success">
                          Installed
                        </span>
                      )}
                    </div>

                    {plugin.description && (
                      <p className="text-sm text-text-muted mb-4 line-clamp-2">{plugin.description}</p>
                    )}

                    <div className="flex items-center gap-4 text-xs text-text-muted mb-4">
                      {plugin.category && (
                        <span className="px-2 py-0.5 rounded bg-surface-overlay">
                          {plugin.category}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 pt-4 border-t border-border-subtle">
                      {!isInstalled ? (
                        <Button size="sm">
                          <Download className="w-3.5 h-3.5 mr-1" />
                          Install
                        </Button>
                      ) : (
                        <Button variant="outline" size="sm" disabled>
                          Installed
                        </Button>
                      )}
                      {plugin.homepage && (
                        <a href={plugin.homepage} target="_blank" rel="noopener noreferrer">
                          <Button variant="ghost" size="sm">
                            <ExternalLink className="w-4 h-4" />
                          </Button>
                        </a>
                      )}
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function PluginsSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 w-48 bg-surface-overlay rounded" />
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card p-4 h-20" />
        ))}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="card p-6 h-56" />
        ))}
      </div>
    </div>
  );
}
