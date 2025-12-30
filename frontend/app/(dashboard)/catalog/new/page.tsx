"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft } from "lucide-react";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { PageHeader } from "@/components/shared/page-header";
import {
  useCreateProduct,
  useCategories,
  type ProductType,
} from "@/lib/hooks/api/use-catalog";
import {
  createProductSchema,
  type CreateProductFormData,
} from "@/lib/schemas/catalog";

export default function NewProductPage() {
  const router = useRouter();
  const { toast } = useToast();
  const createProduct = useCreateProduct();
  const { data: categories } = useCategories();

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<CreateProductFormData>({
    resolver: zodResolver(createProductSchema),
    defaultValues: {
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
    },
  });

  const productType = watch("productType");
  const showUsageFields = productType === "usage_based" || productType === "hybrid";

  const onSubmit = async (data: CreateProductFormData) => {
    try {
      await createProduct.mutateAsync(data);
      toast({ title: "Product created successfully" });
      router.push("/catalog");
    } catch {
      toast({ title: "Failed to create product", variant: "error" });
    }
  };

  return (
    <div className="space-y-6 animate-fade-up">
      <PageHeader
        title="New Product"
        description="Add a new product to your catalog"
        actions={
          <Link href="/catalog">
            <Button variant="ghost">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          </Link>
        }
      />

      <form onSubmit={handleSubmit(onSubmit)}>
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
                    {...register("sku")}
                    placeholder="e.g., PROD-001"
                    aria-invalid={!!errors.sku}
                  />
                  {errors.sku && (
                    <p className="text-xs text-status-error mt-1">{errors.sku.message}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1.5">
                    Name <span className="text-status-error">*</span>
                  </label>
                  <Input
                    {...register("name")}
                    placeholder="Product name"
                    aria-invalid={!!errors.name}
                  />
                  {errors.name && (
                    <p className="text-xs text-status-error mt-1">{errors.name.message}</p>
                  )}
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-text-primary mb-1.5">
                    Description
                  </label>
                  <textarea
                    {...register("description")}
                    placeholder="Product description"
                    rows={3}
                    className="w-full px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm resize-none focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                  {errors.description && (
                    <p className="text-xs text-status-error mt-1">{errors.description.message}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1.5">
                    Category
                  </label>
                  <select
                    {...register("category")}
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
                    {...register("taxClass")}
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
                    {...register("productType")}
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
                    {...register("basePrice", { valueAsNumber: true })}
                    min={0}
                    step={0.01}
                    aria-invalid={!!errors.basePrice}
                  />
                  {errors.basePrice && (
                    <p className="text-xs text-status-error mt-1">{errors.basePrice.message}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1.5">
                    Currency
                  </label>
                  <select
                    {...register("currency")}
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
                      {...register("usageType")}
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
                      {...register("usageUnitName")}
                      placeholder="e.g., user, GB, API call"
                    />
                    {errors.usageUnitName && (
                      <p className="text-xs text-status-error mt-1">{errors.usageUnitName.message}</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-6 border-t border-border-subtle">
              <Link href="/catalog">
                <Button variant="ghost">Cancel</Button>
              </Link>
              <Button type="submit" disabled={createProduct.isPending}>
                {createProduct.isPending ? "Creating..." : "Create Product"}
              </Button>
            </div>
          </div>
        </Card>
      </form>
    </div>
  );
}
