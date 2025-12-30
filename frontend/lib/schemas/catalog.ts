/**
 * Product Catalog Form Schemas
 *
 * Zod validation schemas for product catalog create/edit forms
 */

import { z } from "zod";

// Product type options (for billing model)
export const productTypes = [
  { value: "fixed_price", label: "Fixed Price" },
  { value: "usage_based", label: "Usage Based" },
  { value: "hybrid", label: "Hybrid" },
] as const;

// Usage type options
export const usageTypes = [
  { value: "seat_based", label: "Seat Based" },
  { value: "consumption", label: "Consumption" },
  { value: "tiered", label: "Tiered" },
  { value: "volume", label: "Volume" },
  { value: "flat_rate", label: "Flat Rate" },
] as const;

// Currency options
export const currencies = [
  { value: "USD", label: "USD" },
  { value: "EUR", label: "EUR" },
  { value: "GBP", label: "GBP" },
  { value: "NGN", label: "NGN" },
] as const;

// Product create schema (matches existing form)
export const createProductSchema = z.object({
  sku: z
    .string()
    .min(1, "SKU is required")
    .max(50, "SKU must be at most 50 characters")
    .regex(/^[A-Za-z0-9-_]+$/, "SKU can only contain letters, numbers, hyphens, and underscores"),
  name: z
    .string()
    .min(2, "Name must be at least 2 characters")
    .max(100, "Name must be at most 100 characters"),
  description: z.string().max(2000, "Description is too long").optional().default(""),
  category: z.string().optional().default(""),
  productType: z.enum(["fixed_price", "usage_based", "hybrid"]).default("fixed_price"),
  basePrice: z.coerce
    .number()
    .min(0, "Price must be 0 or greater")
    .max(10000000, "Price exceeds maximum"),
  currency: z.enum(["USD", "EUR", "GBP", "NGN"]).default("USD"),
  taxClass: z.string().optional().default(""),
  usageType: z.enum(["seat_based", "consumption", "tiered", "volume", "flat_rate"]).optional(),
  usageUnitName: z.string().max(50, "Unit name is too long").optional().default(""),
});

// Product update schema
export const updateProductSchema = createProductSchema.partial();

// Type exports
export type CreateProductFormData = z.infer<typeof createProductSchema>;
export type UpdateProductFormData = z.infer<typeof updateProductSchema>;
