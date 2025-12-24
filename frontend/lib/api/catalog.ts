/**
 * Product Catalog API
 *
 * API client for product catalog management
 */

import { api, normalizePaginatedResponse } from "./client";

// ============================================================================
// Types
// ============================================================================

export type ProductType = "fixed_price" | "usage_based" | "hybrid";
export type UsageType = "seat_based" | "consumption" | "tiered" | "volume" | "flat_rate";

export interface ProductCategory {
  categoryId: string;
  name: string;
  description: string | null;
  defaultTaxClass: string | null;
  sortOrder: number;
  createdAt: string;
  updatedAt: string;
}

export interface Product {
  productId: string;
  sku: string;
  name: string;
  description: string | null;
  category: string | null;
  productType: ProductType;
  basePrice: number;
  currency: string;
  taxClass: string | null;
  usageType: UsageType | null;
  usageUnitName: string | null;
  isActive: boolean;
  metadata: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

// ============================================================================
// Parameters
// ============================================================================

export interface GetProductsParams {
  page?: number;
  pageSize?: number;
  category?: string;
  productType?: ProductType;
  usageType?: UsageType;
  isActive?: boolean;
  search?: string;
}

export interface CreateProductData {
  sku: string;
  name: string;
  description?: string;
  category?: string;
  productType: ProductType;
  basePrice: number;
  currency?: string;
  taxClass?: string;
  usageType?: UsageType;
  usageUnitName?: string;
  metadata?: Record<string, unknown>;
}

export interface CreateCategoryData {
  name: string;
  description?: string;
  defaultTaxClass?: string;
  sortOrder?: number;
}

// ============================================================================
// Products CRUD
// ============================================================================

export async function getProducts(params: GetProductsParams = {}): Promise<{
  products: Product[];
  totalCount: number;
  pageCount: number;
}> {
  const response = await api.get<unknown>("/api/v1/billing/catalog/products", {
    params: {
      page: params.page ?? 1,
      limit: params.pageSize ?? 50,
      category: params.category,
      product_type: params.productType,
      usage_type: params.usageType,
      is_active: params.isActive,
      search: params.search,
    },
  });
  const normalized = normalizePaginatedResponse<Product>(response);
  return {
    products: normalized.items,
    totalCount: normalized.total,
    pageCount: normalized.totalPages,
  };
}

export async function getProduct(id: string): Promise<Product> {
  return api.get<Product>(`/api/v1/billing/catalog/products/${id}`);
}

export async function getUsageBasedProducts(): Promise<Product[]> {
  return api.get<Product[]>("/api/v1/billing/catalog/products/usage-based");
}

export async function createProduct(data: CreateProductData): Promise<Product> {
  return api.post<Product>("/api/v1/billing/catalog/products", {
    sku: data.sku,
    name: data.name,
    description: data.description,
    category: data.category,
    product_type: data.productType,
    base_price: data.basePrice,
    currency: data.currency ?? "USD",
    tax_class: data.taxClass,
    usage_type: data.usageType,
    usage_unit_name: data.usageUnitName,
    metadata: data.metadata,
  });
}

export async function updateProduct(
  id: string,
  data: Partial<CreateProductData>
): Promise<Product> {
  return api.put<Product>(`/api/v1/billing/catalog/products/${id}`, {
    sku: data.sku,
    name: data.name,
    description: data.description,
    category: data.category,
    product_type: data.productType,
    base_price: data.basePrice,
    currency: data.currency,
    tax_class: data.taxClass,
    usage_type: data.usageType,
    usage_unit_name: data.usageUnitName,
    metadata: data.metadata,
  });
}

export async function deleteProduct(id: string): Promise<void> {
  return api.delete(`/api/v1/billing/catalog/products/${id}`);
}

// ============================================================================
// Categories CRUD
// ============================================================================

export async function getCategories(): Promise<ProductCategory[]> {
  return api.get<ProductCategory[]>("/api/v1/billing/catalog/categories");
}

export async function getCategory(id: string): Promise<ProductCategory> {
  return api.get<ProductCategory>(`/api/v1/billing/catalog/categories/${id}`);
}

export async function createCategory(
  data: CreateCategoryData
): Promise<ProductCategory> {
  return api.post<ProductCategory>("/api/v1/billing/catalog/categories", {
    name: data.name,
    description: data.description,
    default_tax_class: data.defaultTaxClass,
    sort_order: data.sortOrder ?? 0,
  });
}

export async function getProductsByCategory(
  categoryId: string
): Promise<Product[]> {
  return api.get<Product[]>(
    `/api/v1/billing/catalog/categories/${categoryId}/products`
  );
}
