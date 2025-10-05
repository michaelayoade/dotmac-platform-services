"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/components/ui/use-toast"
import { Search, Filter } from "lucide-react"

interface SearchResult {
  id: string
  type: string
  tenant_id: string
  data: Record<string, any>
}

export function CrossTenantSearch() {
  const [query, setQuery] = useState("")
  const [resourceType, setResourceType] = useState<string>("all")
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [totalResults, setTotalResults] = useState(0)
  const { toast } = useToast()

  const handleSearch = async () => {
    if (!query.trim()) {
      toast({
        title: "Search Query Required",
        description: "Please enter a search term",
        variant: "destructive",
      })
      return
    }

    setLoading(true)
    try {
      const response = await fetch("/api/v1/admin/platform/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
        body: JSON.stringify({
          query,
          resource_type: resourceType === "all" ? null : resourceType,
          limit: 50,
        }),
      })

      if (response.ok) {
        const data = await response.json()
        setResults(data.results || [])
        setTotalResults(data.total || 0)

        if (data.total === 0) {
          toast({
            title: "No Results",
            description: `No resources found matching "${query}"`,
          })
        }
      }
    } catch (error) {
      toast({
        title: "Search Failed",
        description: "Failed to perform cross-tenant search",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Cross-Tenant Search
          </CardTitle>
          <CardDescription>
            Search for resources across all tenants in the platform
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Search Form */}
          <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-3">
              <div className="md:col-span-2">
                <Label htmlFor="search-query">Search Query</Label>
                <Input
                  id="search-query"
                  placeholder="Search users, customers, resources..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                />
              </div>
              <div>
                <Label htmlFor="resource-type">Resource Type</Label>
                <select
                  id="resource-type"
                  value={resourceType}
                  onChange={(e) => setResourceType(e.target.value)}
                  className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                >
                  <option value="all">All Resources</option>
                  <option value="user">Users</option>
                  <option value="customer">Customers</option>
                  <option value="invoice">Invoices</option>
                  <option value="subscription">Subscriptions</option>
                </select>
              </div>
            </div>

            <Button onClick={handleSearch} disabled={loading} className="w-full md:w-auto">
              <Search className="h-4 w-4 mr-2" />
              {loading ? "Searching..." : "Search"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {totalResults > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Search Results</CardTitle>
              <Badge variant="outline">{totalResults} results</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {results.map((result) => (
                <div
                  key={result.id}
                  className="border rounded-lg p-4 hover:bg-accent/50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge>{result.type}</Badge>
                        <Badge variant="outline" className="font-mono text-xs">
                          {result.tenant_id}
                        </Badge>
                      </div>
                      <pre className="text-xs bg-muted p-2 rounded overflow-auto max-h-32">
                        {JSON.stringify(result.data, null, 2)}
                      </pre>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty State (when search hasn't been performed) */}
      {!loading && results.length === 0 && !totalResults && query && (
        <Card>
          <CardContent className="py-12">
            <div className="text-center text-muted-foreground">
              <Filter className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">No results found</p>
              <p className="text-sm mt-1">
                Try adjusting your search query or resource type filter
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
