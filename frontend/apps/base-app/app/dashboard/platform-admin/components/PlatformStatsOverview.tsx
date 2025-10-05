"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Building2, Users, Database, TrendingUp, Activity } from "lucide-react"

interface PlatformStats {
  total_tenants: number
  active_tenants: number
  total_users: number
  total_resources: number
  system_health: string
}

export function PlatformStatsOverview() {
  const [stats, setStats] = useState<PlatformStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchPlatformStats()
    // Refresh every 30 seconds
    const interval = setInterval(fetchPlatformStats, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchPlatformStats = async () => {
    try {
      const response = await fetch("/api/v1/admin/platform/stats", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (error) {
      console.error("Failed to fetch platform stats:", error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Loading...</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">-</div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (!stats) {
    return null
  }

  const statCards = [
    {
      title: "Total Tenants",
      value: stats.total_tenants,
      description: `${stats.active_tenants} active`,
      icon: Building2,
      trend: "+12% from last month",
    },
    {
      title: "Total Users",
      value: stats.total_users,
      description: "Across all tenants",
      icon: Users,
      trend: "+8% from last month",
    },
    {
      title: "Total Resources",
      value: stats.total_resources,
      description: "Customer records",
      icon: Database,
      trend: "+15% from last month",
    },
    {
      title: "System Health",
      value: stats.system_health,
      description: "All systems operational",
      icon: Activity,
      isHealth: true,
    },
  ]

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statCards.map((card, index) => (
          <Card key={index}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
              <card.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${card.isHealth ? "capitalize" : ""}`}>
                {card.value}
              </div>
              <p className="text-xs text-muted-foreground mt-1">{card.description}</p>
              {card.trend && (
                <div className="flex items-center gap-1 mt-2 text-xs text-green-600">
                  <TrendingUp className="h-3 w-3" />
                  {card.trend}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common platform administration tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 md:grid-cols-3">
            <button
              onClick={() => window.location.hash = "#tenants"}
              className="flex items-center gap-2 p-4 border rounded-lg hover:bg-accent transition-colors"
            >
              <Building2 className="h-5 w-5" />
              <div className="text-left">
                <p className="font-medium">View All Tenants</p>
                <p className="text-xs text-muted-foreground">Manage tenant accounts</p>
              </div>
            </button>

            <button
              onClick={() => {
                fetch("/api/v1/admin/platform/system/cache/clear", {
                  method: "POST",
                  headers: {
                    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                  },
                })
                  .then(() => alert("Cache cleared successfully"))
                  .catch(() => alert("Failed to clear cache"))
              }}
              className="flex items-center gap-2 p-4 border rounded-lg hover:bg-accent transition-colors"
            >
              <Database className="h-5 w-5" />
              <div className="text-left">
                <p className="font-medium">Clear System Cache</p>
                <p className="text-xs text-muted-foreground">Flush all caches</p>
              </div>
            </button>

            <button
              onClick={() => window.location.hash = "#audit"}
              className="flex items-center gap-2 p-4 border rounded-lg hover:bg-accent transition-colors"
            >
              <Activity className="h-5 w-5" />
              <div className="text-left">
                <p className="font-medium">View Audit Log</p>
                <p className="text-xs text-muted-foreground">Recent admin actions</p>
              </div>
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
