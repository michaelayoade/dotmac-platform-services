"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, Shield, Users, Building2, Activity, Settings } from "lucide-react"
import { PlatformStatsOverview } from "./components/PlatformStatsOverview"
import { TenantManagement } from "./components/TenantManagement"
import { SystemConfiguration } from "./components/SystemConfiguration"
import { AuditLogViewer } from "./components/AuditLogViewer"
import { CrossTenantSearch } from "./components/CrossTenantSearch"

interface PlatformAdminHealth {
  status: string
  user_id: string
  is_platform_admin: boolean
  permissions: string[]
}

export default function PlatformAdminDashboard() {
  const [health, setHealth] = useState<PlatformAdminHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    checkPlatformAdminAccess()
  }, [])

  const checkPlatformAdminAccess = async () => {
    try {
      const response = await fetch("/api/v1/admin/platform/health", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
      })

      if (!response.ok) {
        if (response.status === 403) {
          setError("Access denied. Platform administrator privileges required.")
        } else {
          setError("Failed to verify platform admin access.")
        }
        return
      }

      const data = await response.json()
      setHealth(data)
    } catch (err) {
      setError("Failed to connect to platform admin API.")
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Activity className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Verifying platform admin access...</p>
        </div>
      </div>
    )
  }

  if (error || !health) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error || "Platform admin access not available"}</AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Shield className="h-8 w-8" />
            Platform Administration
          </h1>
          <p className="text-muted-foreground mt-1">
            Cross-tenant system management and monitoring
          </p>
        </div>
        <Badge variant="outline" className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-green-500 dark:bg-green-400" />
          System Healthy
        </Badge>
      </div>

      {/* Admin Info Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Admin Session</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">User ID</p>
              <p className="font-mono text-sm">{health.user_id}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Admin Status</p>
              <Badge variant={health.is_platform_admin ? "default" : "secondary"}>
                {health.is_platform_admin ? "Platform Admin" : "Limited Access"}
              </Badge>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Permissions</p>
              <p className="text-sm">{health.permissions.length} active</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="tenants" className="flex items-center gap-2">
            <Building2 className="h-4 w-4" />
            Tenants
          </TabsTrigger>
          <TabsTrigger value="search" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Search
          </TabsTrigger>
          <TabsTrigger value="audit" className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Audit Log
          </TabsTrigger>
          <TabsTrigger value="system" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            System
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <PlatformStatsOverview />
        </TabsContent>

        <TabsContent value="tenants" className="space-y-4">
          <TenantManagement />
        </TabsContent>

        <TabsContent value="search" className="space-y-4">
          <CrossTenantSearch />
        </TabsContent>

        <TabsContent value="audit" className="space-y-4">
          <AuditLogViewer />
        </TabsContent>

        <TabsContent value="system" className="space-y-4">
          <SystemConfiguration />
        </TabsContent>
      </Tabs>
    </div>
  )
}
