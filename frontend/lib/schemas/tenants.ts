/**
 * Tenant Form Schemas
 *
 * Zod validation schemas for tenant create/edit forms
 */

import { z } from "zod";

// Tenant plan options
export const tenantPlans = [
  { value: "Free", label: "Free" },
  { value: "Starter", label: "Starter" },
  { value: "Professional", label: "Professional" },
  { value: "Enterprise", label: "Enterprise" },
] as const;

// Tenant status options
export const tenantStatuses = [
  { value: "active", label: "Active" },
  { value: "trial", label: "Trial" },
  { value: "suspended", label: "Suspended" },
  { value: "inactive", label: "Inactive" },
] as const;

// Slug validation regex
const slugRegex = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

// Tenant create schema
export const createTenantSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  slug: z
    .string()
    .min(3, "Slug must be at least 3 characters")
    .max(50, "Slug must be at most 50 characters")
    .regex(slugRegex, "Slug must contain only lowercase letters, numbers, and hyphens"),
  plan: z.enum(["Free", "Starter", "Professional", "Enterprise"], {
    required_error: "Please select a plan",
  }),
  ownerEmail: z.string().email("Please enter a valid email address"),
  ownerName: z.string().min(2, "Owner name must be at least 2 characters"),
});

// Tenant update schema
export const updateTenantSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters").optional(),
  plan: z.enum(["Free", "Starter", "Professional", "Enterprise"]).optional(),
  status: z.enum(["active", "trial", "suspended", "inactive"]).optional(),
});

// Type exports
export type CreateTenantData = z.infer<typeof createTenantSchema>;
export type UpdateTenantData = z.infer<typeof updateTenantSchema>;
