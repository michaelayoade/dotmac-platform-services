"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/components/ui/use-toast"
import { Settings, Database, Trash2, CheckCircle2 } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"

interface SystemConfig {
  environment: string
  multi_tenant_mode: boolean
  features_enabled: {
    rbac: boolean
    audit_logging: boolean
    platform_admin: boolean
  }
}

export function SystemConfiguration() {
  const [config, setConfig] = useState<SystemConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    fetchSystemConfig()
  }, [])

  const fetchSystemConfig = async () => {
    try {
      const response = await fetch("/api/v1/admin/platform/system/config", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setConfig(data)
      }
    } catch (error) {
      console.error("Failed to fetch system config:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleClearCache = async (cacheType: string = "all") => {
    try {
      const response = await fetch(
        `/api/v1/admin/platform/system/cache/clear${cacheType !== "all" ? `?cache_type=${cacheType}` : ""}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          },
        }
      )

      if (response.ok) {
        const result = await response.json()
        toast({
          title: "Cache Cleared",
          description: `${result.cache_type || cacheType} cache cleared successfully`,
        })
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to clear cache",
        variant: "destructive",
      })
    }
  }

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
