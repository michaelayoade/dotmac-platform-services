"use client"

import { useEffect, useState, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { useToast } from "@/components/ui/use-toast"
import { Search, Eye, Key, ChevronLeft, ChevronRight } from "lucide-react"

interface Tenant {
  tenant_id: string
  name: string
  created_at: string | null
  is_active: boolean
  user_count: number
  resource_count: number
}

interface TenantListResponse {
  tenants: Tenant[]
  total: number
  page: number
  page_size: number
}

export function TenantManagement() {
  const [data, setData] = useState<TenantListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const [searchQuery, setSearchQuery] = useState("")
  const [impersonateDialog, setImpersonateDialog] = useState<string | null>(null)
  const [impersonateDuration, setImpersonateDuration] = useState(60)
  const { toast } = useToast()

  const fetchTenants = useCallback(async () => {
    setLoading(true)
    try {
      const response = await fetch(
        `/api/v1/admin/platform/tenants?page=${page}&page_size=${pageSize}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          },
        }
      )

      if (response.ok) {
        const result = await response.json()
        setData(result)
      }
    } catch (error) {
      console.error("Failed to fetch tenants:", error)
      toast({
        title: "Error",
        description: "Failed to load tenants",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, toast])

  useEffect(() => {
    fetchTenants()
  }, [fetchTenants])

  const handleImpersonate = async (tenantId: string) => {
    try {
      const response = await fetch(
        `/api/v1/admin/platform/tenants/${tenantId}/impersonate?duration_minutes=${impersonateDuration}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          },
        }
      )

      if (response.ok) {
        const result = await response.json()

        // Store the impersonation token
        localStorage.setItem("impersonation_token", result.access_token)
        localStorage.setItem("impersonating_tenant", tenantId)

        toast({
          title: "Impersonation Active",
          description: `Now viewing as tenant: ${tenantId}. Token expires in ${impersonateDuration} minutes.`,
        })

        setImpersonateDialog(null)

        // Optionally redirect to a tenant view
        // window.location.href = "/dashboard"
      } else {
        throw new Error("Failed to create impersonation token")
      }
    } catch (error) {
      toast({
        title: "Impersonation Failed",
        description: "Could not create impersonation token",
        variant: "destructive",
      })
    }
  }

  const filteredTenants = data?.tenants.filter(tenant =>
    tenant.tenant_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    tenant.name?.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Tenant Management</CardTitle>
              <CardDescription>
                View and manage all tenants across the platform
              </CardDescription>
            </div>
            <Badge variant="outline">
              {data?.total || 0} Total Tenants
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {/* Search */}
          <div className="flex items-center gap-2 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search tenants..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {/* Table */}
          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tenant ID</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Users</TableHead>
                  <TableHead>Resources</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8">
                      Loading tenants...
                    </TableCell>
                  </TableRow>
                ) : filteredTenants.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                      No tenants found
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredTenants.map((tenant) => (
                    <TableRow key={tenant.tenant_id}>
                      <TableCell className="font-mono text-sm">
                        {tenant.tenant_id}
                      </TableCell>
                      <TableCell>{tenant.name}</TableCell>
                      <TableCell>
                        {tenant.created_at
                          ? new Date(tenant.created_at).toLocaleDateString()
                          : "N/A"}
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{tenant.user_count}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{tenant.resource_count}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={tenant.is_active ? "default" : "outline"}>
                          {tenant.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              // View tenant details
                              toast({
                                title: "Tenant Details",
                                description: `Tenant: ${tenant.tenant_id}`,
                              })
                            }}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setImpersonateDialog(tenant.tenant_id)}
                          >
                            <Key className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {data && data.total > pageSize && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-muted-foreground">
                Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, data.total)} of {data.total} tenants
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => p + 1)}
                  disabled={page * pageSize >= data.total}
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Impersonate Dialog */}
      <Dialog open={!!impersonateDialog} onOpenChange={() => setImpersonateDialog(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Impersonate Tenant</DialogTitle>
            <DialogDescription>
              Create a temporary access token to impersonate this tenant
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <p className="text-sm font-medium mb-2">Target Tenant</p>
              <p className="text-sm font-mono bg-muted p-2 rounded">{impersonateDialog}</p>
            </div>
            <div>
              <p className="text-sm font-medium mb-2">Duration (minutes)</p>
              <Input
                type="number"
                min={1}
                max={480}
                value={impersonateDuration}
                onChange={(e) => setImpersonateDuration(Number(e.target.value))}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Maximum 480 minutes (8 hours)
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setImpersonateDialog(null)}>
              Cancel
            </Button>
            <Button onClick={() => impersonateDialog && handleImpersonate(impersonateDialog)}>
              Create Token
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
