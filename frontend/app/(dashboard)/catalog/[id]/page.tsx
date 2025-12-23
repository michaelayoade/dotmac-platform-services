"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Loader2 } from "lucide-react";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { PageHeader } from "@/components/shared/page-header";
import {
  useProduct,
  useUpdateProduct,
  useCategories,
  type CreateProductData,
  type ProductType,
} from "@/lib/hooks/api/use-catalog";

export default function EditProductPage() {
  const router = useRouter();
  const params = useParams();
  const productId = params.id as string;
  const { toast } = useToast();

  const { data: product, isLoading } = useProduct(productId);
  const updateProduct = useUpdateProduct();
  const { data: categories } = useCategories();

  const [formData, setFormData] = useState<CreateProductData>({
    sku: "",
    name: "",
    description: "",
    category: "",
    productType: "fixed_price",
    basePrice: 0,
    currency: "USD",
    taxClass: "",
    usageType: undefined,
    usageUnitName: "",
  });

  useEffect(() => {
    if (product) {
      setFormData({
        sku: product.sku,
        name: product.name,
        description: product.description || "",
        category: product.category || "",
        productType: product.productType,
        basePrice: product.basePrice,
        currency: product.currency,
        taxClass: product.taxClass || "",
        usageType: product.usageType || undefined,
        usageUnitName: product.usageUnitName || "",
      });
    }
  }, [product]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.sku || !formData.name) {
      toast({ title: "SKU and Name are required", variant: "error" });
      return;
    }

    try {
      await updateProduct.mutateAsync({ id: productId, data: formData });
      toast({ title: "Product updated successfully" });
      router.push("/catalog");
    } catch {
      toast({ title: "Failed to update product", variant: "error" });
    }
  };

  const updateField = <K extends keyof CreateProductData>(
    field: K,
    value: CreateProductData[K]
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const showUsageFields = formData.productType === "usage_based" || formData.productType === "hybrid";

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    );
  }

  if (!product) {
    return (
      <div className="text-center py-12">
        <h2 className="text-lg font-semibold text-text-primary mb-2">Product not found</h2>
        <Link href="/catalog">
          <Button variant="outline">Back to Catalog</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-up">
      <PageHeader
        title="Edit Product"
        description={`Editing ${product.name}`}
        actions={
          <Link href="/catalog">
            <Button variant="ghost">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          </Link>
        }
      />

      <form onSubmit={handleSubmit}>
        <Card className="p-6">
          <div className="space-y-6">
            {/* Basic Information */}
            <div>
              <h3 className="text-lg font-semibold text-text-primary mb-4">Basic Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1.5">
                    SKU <span className="text-status-error">*</span>
                  </label>
                  <Input
                    value={formData.sku}
                    onChange={(e) => updateField("sku", e.target.value)}
                    placeholder="e.g., PROD-001"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1.5">
                    Name <span className="text-status-error">*</span>
                  </label>
                  <Input
                    value={formData.name}
                    onChange={(e) => updateField("name", e.target.value)}
                    placeholder="Product name"
                    required
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-text-primary mb-1.5">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => updateField("description", e.target.value)}
                    placeholder="Product description"
                    rows={3}
                    className="w-full px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm resize-none focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1.5">
                    Category
                  </label>
                  <select
                    value={formData.category}
                    onChange={(e) => updateField("category", e.target.value)}
                    className="w-full px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
                  >
                    <option value="">Select category</option>
                    {categories?.map((cat) => (
                      <option key={cat.categoryId} value={cat.categoryId}>
                        {cat.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1.5">
                    Tax Class
                  </label>
                  <Input
                    value={formData.taxClass}
                    onChange={(e) => updateField("taxClass", e.target.value)}
                    placeholder="e.g., standard, reduced"
                  />
                </div>
              </div>
            </div>

            {/* Pricing */}
            <div className="border-t border-border-subtle pt-6">
              <h3 className="text-lg font-semibold text-text-primary mb-4">Pricing</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1.5">
                    Product Type <span className="text-status-error">*</span>
                  </label>
                  <select
                    value={formData.productType}
                    onChange={(e) => updateField("productType", e.target.value as ProductType)}
                    className="w-full px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
                  >
                    <option value="fixed_price">Fixed Price</option>
                    <option value="usage_based">Usage Based</option>
                    <option value="hybrid">Hybrid</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1.5">
                    Base Price <span className="text-status-error">*</span>
                  </label>
                  <Input
                    type="number"
                    value={formData.basePrice}
                    onChange={(e) => updateField("basePrice", parseFloat(e.target.value) || 0)}
                    min={0}
                    step={0.01}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1.5">
                    Currency
                  </label>
                  <select
                    value={formData.currency}
                    onChange={(e) => updateField("currency", e.target.value)}
                    className="w-full px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
                  >
                    <option value="USD">USD</option>
                    <option value="EUR">EUR</option>
                    <option value="GBP">GBP</option>
                    <option value="NGN">NGN</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Usage Settings */}
            {showUsageFields && (
              <div className="border-t border-border-subtle pt-6">
                <h3 className="text-lg font-semibold text-text-primary mb-4">Usage Settings</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-text-primary mb-1.5">
                      Usage Type
                    </label>
                    <select
                      value={formData.usageType || ""}
                      onChange={(e) => updateField("usageType", e.target.value as CreateProductData["usageType"])}
                      className="w-full px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
                    >
                      <option value="">Select usage type</option>
                      <option value="seat_based">Seat Based</option>
                      <option value="consumption">Consumption</option>
                      <option value="tiered">Tiered</option>
                      <option value="volume">Volume</option>
                      <option value="flat_rate">Flat Rate</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-primary mb-1.5">
                      Usage Unit Name
                    </label>
                    <Input
                      value={formData.usageUnitName}
                      onChange={(e) => updateField("usageUnitName", e.target.value)}
                      placeholder="e.g., user, GB, API call"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-6 border-t border-border-subtle">
              <Link href="/catalog">
                <Button variant="ghost">Cancel</Button>
              </Link>
              <Button type="submit" disabled={updateProduct.isPending}>
                {updateProduct.isPending ? "Saving..." : "Save Changes"}
              </Button>
            </div>
          </div>
        </Card>
      </form>
    </div>
  );
}
