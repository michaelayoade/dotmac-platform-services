"use client"

import { useCallback, useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/components/ui/use-toast"
import { Settings, Database, Trash2, CheckCircle2 } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { platformAdminService, type SystemConfig } from "@/lib/services/platform-admin-service"

export function SystemConfiguration() {
  const [config, setConfig] = useState<SystemConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  const fetchSystemConfig = useCallback(async () => {
    try {
      const data = await platformAdminService.getSystemConfig()
      setConfig(data)
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load system configuration"
      toast({ title: "Unable to load config", description: message, variant: "destructive" })
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => {
    void fetchSystemConfig()
  }, [fetchSystemConfig])

  const handleClearCache = useCallback(async (cacheType: string = "all") => {
    try {
      const result = await platformAdminService.clearCache(cacheType)
      toast({
        title: "Cache cleared",
        description:
          typeof result.cache_type === "string"
            ? `${result.cache_type} cache cleared successfully`
            : "Cache cleared successfully",
      })
      void fetchSystemConfig()
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to clear cache"
      toast({ title: "Error", description: message, variant: "destructive" })
    }
  }, [fetchSystemConfig, toast])

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>System Configuration</CardTitle>
          <CardDescription>Loading configuration...</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  if (!config) {
    return (
      <Alert>
        <AlertDescription>Failed to load system configuration</AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-4">
      {/* Configuration Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            System Configuration
          </CardTitle>
          <CardDescription>
            View current platform configuration (non-sensitive values only)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Environment</p>
              <Badge variant="outline" className="mt-1">
                {config.environment.toUpperCase()}
              </Badge>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Multi-Tenant Mode</p>
              <div className="flex items-center gap-2 mt-1">
                {config.multi_tenant_mode ? (
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                ) : (
                  <div className="h-4 w-4" />
                )}
                <span className="text-sm">
                  {config.multi_tenant_mode ? "Enabled" : "Disabled"}
                </span>
              </div>
            </div>
          </div>

          <div>
            <p className="text-sm font-medium text-muted-foreground mb-2">Features Enabled</p>
            <div className="grid grid-cols-3 gap-2">
              {Object.entries(config.features_enabled).map(([feature, enabled]) => (
                <div key={feature} className="flex items-center gap-2">
                  {enabled && <CheckCircle2 className="h-4 w-4 text-green-500" />}
                  <span className="text-sm capitalize">{feature.replace(/_/g, " ")}</span>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Cache Management */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Cache Management
          </CardTitle>
          <CardDescription>
            Clear system caches for troubleshooting or after configuration changes
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2">
            <Button
              variant="outline"
              className="justify-start"
              onClick={() => handleClearCache("permissions")}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Clear Permission Cache
            </Button>
            <Button
              variant="outline"
              className="justify-start"
              onClick={() => handleClearCache("all")}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Clear All Caches
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Platform Permissions */}
      <Card>
        <CardHeader>
          <CardTitle>Platform Permissions</CardTitle>
          <CardDescription>
            Available platform-level permissions for administrators
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 md:grid-cols-2">
            {[
              { key: "platform:admin", desc: "Full platform administration" },
              { key: "platform:tenants:read", desc: "View all tenants" },
              { key: "platform:tenants:write", desc: "Manage all tenants" },
              { key: "platform:users:read", desc: "View all users" },
              { key: "platform:users:write", desc: "Manage all users" },
              { key: "platform:billing:read", desc: "View billing data" },
              { key: "platform:analytics", desc: "Cross-tenant analytics" },
              { key: "platform:audit", desc: "Access audit logs" },
              { key: "platform:impersonate", desc: "Impersonate tenants" },
            ].map((perm) => (
              <div key={perm.key} className="border rounded-lg p-3">
                <p className="font-mono text-sm font-medium">{perm.key}</p>
                <p className="text-xs text-muted-foreground mt-1">{perm.desc}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
