"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Package,
  Plus,
  Search,
  Filter,
  RefreshCcw,
  CheckCircle2,
  XCircle,
  DollarSign,
  Layers,
  Edit,
  Trash2,
  BarChart3,
} from "lucide-react";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { ConfirmDialog, useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useProducts,
  useCategories,
  useDeleteProduct,
  type Product,
  type ProductType,
} from "@/lib/hooks/api/use-catalog";

const productTypeConfig: Record<ProductType, { label: string; color: string }> = {
  fixed_price: { label: "Fixed Price", color: "bg-accent-subtle text-accent" },
  usage_based: { label: "Usage Based", color: "bg-status-info/15 text-status-info" },
  hybrid: { label: "Hybrid", color: "bg-highlight-subtle text-highlight" },
};

const statusConfig = {
  active: { label: "Active", color: "bg-status-success/15 text-status-success", icon: CheckCircle2 },
  inactive: { label: "Inactive", color: "bg-status-error/15 text-status-error", icon: XCircle },
};

export default function CatalogPage() {
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [page, setPage] = useState(1);

  const { data, isLoading, refetch } = useProducts({
    page,
    pageSize: 20,
    search: searchQuery || undefined,
    productType: typeFilter !== "all" ? (typeFilter as ProductType) : undefined,
    category: categoryFilter !== "all" ? categoryFilter : undefined,
    isActive: statusFilter !== "all" ? statusFilter === "active" : undefined,
  });
  const { data: categories } = useCategories();

  const deleteProduct = useDeleteProduct();

  const products = data?.products || [];
  const totalPages = data?.pageCount || 1;
  const totalCount = data?.totalCount || 0;

  const activeCount = products.filter((p) => p.isActive).length;
  const usageBasedCount = products.filter((p) => p.productType === "usage_based" || p.productType === "hybrid").length;

  const handleDelete = async (product: Product) => {
    const confirmed = await confirm({
      title: "Delete Product",
      description: `Are you sure you want to delete "${product.name}"? This will deactivate the product.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deleteProduct.mutateAsync(product.productId);
        toast({ title: "Product deleted" });
      } catch {
        toast({ title: "Failed to delete product", variant: "error" });
      }
    }
  };

  const formatPrice = (price: number, currency: string) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency || "USD",
    }).format(price);
  };

  if (isLoading) {
    return <CatalogSkeleton />;
  }

  return (
    <div className="space-y-6 animate-fade-up">
      {dialog}

      <PageHeader
        title="Product Catalog"
        description="Manage products and pricing for your platform"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={() => refetch()}>
              <RefreshCcw className="w-4 h-4" />
            </Button>
            <Link href="/catalog/new">
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                Add Product
              </Button>
            </Link>
          </div>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <Package className="w-5 h-5 text-accent" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Total Products</p>
              <p className="text-2xl font-semibold text-text-primary">
                {totalCount.toLocaleString()}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5 text-status-success" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Active</p>
              <p className="text-2xl font-semibold text-status-success">
                {activeCount}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-status-info" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Usage-Based</p>
              <p className="text-2xl font-semibold text-text-primary">
                {usageBasedCount}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
              <Layers className="w-5 h-5 text-highlight" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Categories</p>
              <p className="text-2xl font-semibold text-text-primary">
                {categories?.length || 0}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <Input
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setPage(1);
            }}
            placeholder="Search by name or SKU..."
            className="pl-10"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-text-muted" />
          <select
            value={typeFilter}
            onChange={(e) => {
              setTypeFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
          >
            <option value="all">All Types</option>
            <option value="fixed_price">Fixed Price</option>
            <option value="usage_based">Usage Based</option>
            <option value="hybrid">Hybrid</option>
          </select>
          <select
            value={categoryFilter}
            onChange={(e) => {
              setCategoryFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
          >
            <option value="all">All Categories</option>
            {categories?.map((cat) => (
              <option key={cat.categoryId} value={cat.categoryId}>
                {cat.name}
              </option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>

      {/* Products Table */}
      {products.length === 0 ? (
        <Card className="p-12 text-center">
          <Package className="w-12 h-12 text-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">No products found</h3>
          <p className="text-text-muted mb-6">
            {searchQuery || typeFilter !== "all" || categoryFilter !== "all" || statusFilter !== "all"
              ? "Try adjusting your filters"
              : "Create your first product to get started"}
          </p>
          <Link href="/catalog/new">
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Add Product
            </Button>
          </Link>
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border-subtle">
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Product</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">SKU</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Type</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Category</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Price</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Status</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {products.map((product) => {
                  const type = productTypeConfig[product.productType] || productTypeConfig.fixed_price;
                  const status = product.isActive ? statusConfig.active : statusConfig.inactive;
                  const StatusIcon = status.icon;

                  return (
                    <tr key={product.productId} className="border-b border-border-subtle hover:bg-surface-overlay/50">
                      <td className="px-4 py-3">
                        <div>
                          <p className="font-medium text-text-primary">{product.name}</p>
                          {product.description && (
                            <p className="text-sm text-text-muted line-clamp-1">
                              {product.description}
                            </p>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <code className="text-sm font-mono text-text-secondary">
                          {product.sku}
                        </code>
                      </td>
                      <td className="px-4 py-3">
                        <span className={cn("px-2 py-0.5 rounded-full text-xs font-medium", type.color)}>
                          {type.label}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm text-text-secondary">
                          {product.category || "—"}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <DollarSign className="w-3 h-3 text-text-muted" />
                          <span className="text-sm font-medium text-text-primary">
                            {formatPrice(product.basePrice, product.currency)}
                          </span>
                          {product.usageUnitName && (
                            <span className="text-xs text-text-muted">
                              /{product.usageUnitName}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium", status.color)}>
                          <StatusIcon className="w-3 h-3" />
                          {status.label}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <Link href={`/catalog/${product.productId}`}>
                            <Button variant="ghost" size="sm">
                              <Edit className="w-4 h-4" />
                            </Button>
                          </Link>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(product)}
                            className="text-status-error hover:text-status-error"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-border-subtle">
              <p className="text-sm text-text-muted">
                Page {page} of {totalPages}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

function CatalogSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 w-48 bg-surface-overlay rounded" />
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card p-4 h-20" />
        ))}
      </div>
      <div className="card">
        <div className="p-4 space-y-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-12 bg-surface-overlay rounded" />
          ))}
        </div>
      </div>
    </div>
  );
}
