"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Shield, Clock } from "lucide-react"

interface AuditAction {
  id: string
  user_id: string
  action: string
  timestamp: string
  target_tenant?: string
  details?: Record<string, any>
}

export function AuditLogViewer() {
  const [actions, setActions] = useState<AuditAction[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAuditLog()
    // Refresh every 30 seconds
    const interval = setInterval(fetchAuditLog, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchAuditLog = async () => {
    try {
      const response = await fetch("/api/v1/admin/platform/audit/recent?limit=50", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        // For now, the endpoint returns empty array
        // In production, this would contain real audit data
        setActions(data.actions || [])
      }
    } catch (error) {
      console.error("Failed to fetch audit log:", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Platform Audit Log
            </CardTitle>
            <CardDescription>
              Recent platform administrator actions across all tenants
            </CardDescription>
          </div>
          <Badge variant="outline">{actions.length} actions</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[600px] pr-4">
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">
              Loading audit log...
            </div>
          ) : actions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Shield className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No audit actions recorded yet</p>
              <p className="text-sm mt-1">
                Platform admin actions will be logged here for compliance
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {actions.map((action) => (
                <div
                  key={action.id}
                  className="border rounded-lg p-4 hover:bg-accent/50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline">{action.action}</Badge>
                        {action.target_tenant && (
                          <Badge variant="secondary" className="font-mono text-xs">
                            {action.target_tenant}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        User: <span className="font-mono">{action.user_id}</span>
                      </p>
                      {action.details && Object.keys(action.details).length > 0 && (
                        <pre className="mt-2 text-xs bg-muted p-2 rounded overflow-auto">
                          {JSON.stringify(action.details, null, 2)}
                        </pre>
                      )}
                    </div>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      {new Date(action.timestamp).toLocaleString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
