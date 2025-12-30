/**
 * Feature Flag Form Schemas
 *
 * Zod validation schemas for feature flag create/edit forms
 */

import { z } from "zod";

// Targeting rule operators
export const targetingOperators = [
  { value: "eq", label: "Equals" },
  { value: "neq", label: "Not Equals" },
  { value: "contains", label: "Contains" },
  { value: "in", label: "In List" },
  { value: "not_in", label: "Not In List" },
  { value: "gt", label: "Greater Than" },
  { value: "lt", label: "Less Than" },
  { value: "gte", label: "Greater Than or Equal" },
  { value: "lte", label: "Less Than or Equal" },
] as const;

// Targeting rule schema
export const targetingRuleSchema = z.object({
  attribute: z.string().min(1, "Attribute is required"),
  operator: z.enum(["eq", "neq", "contains", "in", "not_in", "gt", "lt", "gte", "lte"]),
  value: z.unknown().refine((val) => val !== undefined, { message: "Value is required" }),
  enabled: z.boolean().default(true),
});

// Create feature flag schema
export const createFeatureFlagSchema = z.object({
  name: z
    .string()
    .min(2, "Name must be at least 2 characters")
    .max(100, "Name too long")
    .regex(/^[a-z0-9_-]+$/i, "Only letters, numbers, underscores, and hyphens allowed"),
  description: z.string().max(500, "Description too long").optional(),
  enabled: z.boolean().default(false),
  rolloutPercentage: z.number().int().min(0).max(100).optional(),
  targetingRules: z.array(targetingRuleSchema).optional().default([]),
});

// Update feature flag schema
export const updateFeatureFlagSchema = z.object({
  description: z.string().max(500, "Description too long").optional(),
  enabled: z.boolean().optional(),
  rolloutPercentage: z.number().int().min(0).max(100).optional(),
  targetingRules: z.array(targetingRuleSchema).optional(),
});

// Type exports - TargetingRule explicitly typed to match API expectations
export interface TargetingRule {
  attribute: string;
  operator: "eq" | "neq" | "contains" | "in" | "not_in" | "gt" | "lt" | "gte" | "lte";
  value: unknown;
  enabled: boolean;
}
export type CreateFeatureFlagData = Omit<z.infer<typeof createFeatureFlagSchema>, "targetingRules"> & {
  targetingRules?: TargetingRule[];
};
export type UpdateFeatureFlagData = Omit<z.infer<typeof updateFeatureFlagSchema>, "targetingRules"> & {
  targetingRules?: TargetingRule[];
};
