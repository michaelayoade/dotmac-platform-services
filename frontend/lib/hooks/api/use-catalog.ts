"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getProducts,
  getProduct,
  getUsageBasedProducts,
  createProduct,
  updateProduct,
  deleteProduct,
  getCategories,
  getCategory,
  createCategory,
  getProductsByCategory,
  type GetProductsParams,
  type ProductType,
  type Product,
  type CreateProductData,
  type ProductCategory,
  type CreateCategoryData,
} from "@/lib/api/catalog";
import { queryKeys } from "@/lib/api/query-keys";

// ============================================================================
// Products Hooks
// ============================================================================

export function useProducts(params?: GetProductsParams) {
  return useQuery({
    queryKey: queryKeys.catalog.products.list(params),
    queryFn: () => getProducts(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useProduct(id: string) {
  return useQuery({
    queryKey: queryKeys.catalog.products.detail(id),
    queryFn: () => getProduct(id),
    enabled: !!id,
  });
}

export function useUsageBasedProducts() {
  return useQuery({
    queryKey: [...queryKeys.catalog.products.all(), "usage-based"],
    queryFn: getUsageBasedProducts,
  });
}

export function useCreateProduct() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createProduct,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.catalog.products.all(),
      });
    },
  });
}

export function useUpdateProduct() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
      data: Partial<CreateProductData>;
    }) => updateProduct(id, data),
    onSuccess: (data) => {
      queryClient.setQueryData(
        queryKeys.catalog.products.detail(data.productId),
        data
      );
      queryClient.invalidateQueries({
        queryKey: queryKeys.catalog.products.all(),
      });
    },
  });
}

export function useDeleteProduct() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteProduct,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.catalog.products.all(),
      });
    },
  });
}

// ============================================================================
// Categories Hooks
// ============================================================================

export function useCategories() {
  return useQuery({
    queryKey: queryKeys.catalog.categories.list(),
    queryFn: getCategories,
  });
}

export function useCategory(id: string) {
  return useQuery({
    queryKey: queryKeys.catalog.categories.detail(id),
    queryFn: () => getCategory(id),
    enabled: !!id,
  });
}

export function useCreateCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createCategory,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.catalog.categories.all(),
      });
    },
  });
}

export function useProductsByCategory(categoryId: string) {
  return useQuery({
    queryKey: [...queryKeys.catalog.categories.detail(categoryId), "products"],
    queryFn: () => getProductsByCategory(categoryId),
    enabled: !!categoryId,
  });
}

// ============================================================================
// Re-export types
// ============================================================================

export type {
  GetProductsParams,
  ProductType,
  Product,
  CreateProductData,
  ProductCategory,
  CreateCategoryData,
};
