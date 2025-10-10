"use client"

import { ReactNode, useEffect, useMemo, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import {
  AlertCircle,
  Shield,
  Building2,
  Activity,
  Settings,
  LayoutDashboard,
  Search,
  type LucideIcon,
} from "lucide-react"
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

type NavigationSection = {
  value: string
  label: string
  description: string
  icon: LucideIcon
  content: ReactNode
  anchor?: string
}

export default function PlatformAdminDashboard() {
  const [health, setHealth] = useState<PlatformAdminHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const navigationSections = useMemo<NavigationSection[]>(
    () => [
      {
        value: "overview",
        label: "Dashboard & Stats",
        description: "Monitor platform health and quick actions",
        icon: LayoutDashboard,
        content: <PlatformStatsOverview />,
        anchor: "overview",
      },
      {
        value: "tenants",
        label: "Tenant Administration",
        description: "Manage tenants, status, and impersonation",
        icon: Building2,
        content: <TenantManagement />,
        anchor: "tenants",
      },
      {
        value: "search",
        label: "Cross-Tenant Search",
        description: "Find users and resources across tenants",
        icon: Search,
        content: <CrossTenantSearch />,
        anchor: "search",
      },
      {
        value: "audit",
        label: "Audit Activity",
        description: "Review privileged administrator activity",
        icon: Shield,
        content: <AuditLogViewer />,
        anchor: "audit",
      },
      {
        value: "system",
        label: "System Configuration",
        description: "Feature flags and global configuration",
        icon: Settings,
        content: <SystemConfiguration />,
        anchor: "system",
      },
    ],
    []
  )
  const [activeSection, setActiveSection] = useState(() => navigationSections[0]?.value ?? "overview")

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

  useEffect(() => {
    const syncTabWithHash = () => {
      if (typeof window === "undefined") {
        return
      }
      const hash = window.location.hash.replace("#", "")
      if (!hash) {
        return
      }
      const matched = navigationSections.find(
        (section) => section.anchor === hash || section.value === hash
      )
      if (matched) {
        setActiveSection(matched.value)
      }
    }

    syncTabWithHash()
    window.addEventListener("hashchange", syncTabWithHash)

    return () => {
      window.removeEventListener("hashchange", syncTabWithHash)
    }
  }, [navigationSections])

  const handleSectionChange = (value: string) => {
    setActiveSection(value)
    if (typeof window === "undefined") {
      return
    }
    const matched = navigationSections.find((section) => section.value === value)
    if (matched?.anchor) {
      window.history.replaceState(null, "", `#${matched.anchor}`)
    } else {
      window.history.replaceState(null, "", window.location.pathname + window.location.search)
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
      <Tabs
        value={activeSection}
        onValueChange={handleSectionChange}
        className="lg:grid lg:grid-cols-[280px_1fr] lg:items-start lg:gap-6"
      >
        {/* Mobile navigation */}
        <div className="lg:hidden">
          <TabsList className="grid w-full grid-cols-2 gap-2 bg-transparent p-0">
            {navigationSections.map((section) => (
              <TabsTrigger
                key={section.value}
                value={section.value}
                className="justify-center gap-1 rounded-md border border-border px-3 py-2 text-xs font-medium data-[state=active]:border-primary data-[state=active]:bg-primary/10"
              >
                {section.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </div>

        {/* Desktop side navigation */}
        <aside className="hidden lg:block">
          <TabsList className="flex h-full w-full flex-col items-stretch gap-2 rounded-lg bg-transparent p-0">
            {navigationSections.map((section) => (
              <TabsTrigger
                key={section.value}
                value={section.value}
                className="justify-start gap-3 rounded-lg border border-transparent px-4 py-3 text-left text-sm font-semibold transition-colors data-[state=active]:border-primary data-[state=active]:bg-primary/10 data-[state=active]:text-primary"
              >
                <section.icon className="h-4 w-4" />
                <div className="flex flex-col">
                  <span>{section.label}</span>
                  <span className="text-xs font-normal text-muted-foreground">
                    {section.description}
                  </span>
                </div>
              </TabsTrigger>
            ))}
          </TabsList>
        </aside>

        {/* Content */}
        <div className="space-y-6 lg:col-start-2">
          {navigationSections.map((section) => (
            <TabsContent
              key={section.value}
              value={section.value}
              id={section.anchor}
              className="mt-0 space-y-6"
            >
              {section.content}
            </TabsContent>
          ))}
        </div>
      </Tabs>
    </div>
  )
}
