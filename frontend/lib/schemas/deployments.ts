/**
 * Deployment Form Schemas
 *
 * Zod validation schemas for deployment create/edit forms
 */

import { z } from "zod";

// Resource configuration schema
export const resourcesSchema = z.object({
  cpu: z.string().min(1, "CPU allocation is required"),
  memory: z.string().min(1, "Memory allocation is required"),
  storage: z.string().optional(),
});

// Deployment create schema
export const createDeploymentSchema = z.object({
  name: z
    .string()
    .min(3, "Name must be at least 3 characters")
    .max(63, "Name must be at most 63 characters")
    .regex(
      /^[a-z0-9][a-z0-9-]*[a-z0-9]$/,
      "Name must be lowercase, start and end with alphanumeric, and can contain hyphens"
    ),
  environment: z.enum(["production", "staging", "development"], {
    required_error: "Please select an environment",
  }),
  region: z.string().min(1, "Region is required"),
  version: z.string().min(1, "Version is required"),
  replicas: z.coerce
    .number()
    .min(1, "At least 1 replica is required")
    .max(10, "Maximum 10 replicas allowed")
    .default(1),
  resources: resourcesSchema,
  config: z.record(z.unknown()).optional(),
});

// Deployment update schema
export const updateDeploymentSchema = z.object({
  name: z
    .string()
    .min(3, "Name must be at least 3 characters")
    .max(63, "Name must be at most 63 characters")
    .regex(/^[a-z0-9][a-z0-9-]*[a-z0-9]$/, "Invalid name format")
    .optional(),
  version: z.string().optional(),
  replicas: z.coerce.number().min(1).max(10).optional(),
  resources: resourcesSchema.optional(),
  config: z.record(z.unknown()).optional(),
});

// Scale deployment schema
export const scaleDeploymentSchema = z.object({
  replicas: z.coerce
    .number()
    .min(1, "At least 1 replica is required")
    .max(10, "Maximum 10 replicas allowed"),
});

// Rollback deployment schema
export const rollbackDeploymentSchema = z.object({
  targetVersion: z.string().min(1, "Target version is required"),
});

// Redeploy schema
export const redeploySchema = z.object({
  version: z.string().optional(),
});

// Available regions
export const REGIONS = [
  { value: "us-east-1", label: "US East (N. Virginia)" },
  { value: "us-east-2", label: "US East (Ohio)" },
  { value: "us-west-1", label: "US West (N. California)" },
  { value: "us-west-2", label: "US West (Oregon)" },
  { value: "eu-west-1", label: "Europe (Ireland)" },
  { value: "eu-west-2", label: "Europe (London)" },
  { value: "eu-central-1", label: "Europe (Frankfurt)" },
  { value: "ap-southeast-1", label: "Asia Pacific (Singapore)" },
  { value: "ap-northeast-1", label: "Asia Pacific (Tokyo)" },
] as const;

// CPU options
export const CPU_OPTIONS = [
  { value: "0.5", label: "0.5 vCPU" },
  { value: "1", label: "1 vCPU" },
  { value: "2", label: "2 vCPU" },
  { value: "4", label: "4 vCPU" },
  { value: "8", label: "8 vCPU" },
] as const;

// Memory options
export const MEMORY_OPTIONS = [
  { value: "512MB", label: "512 MB" },
  { value: "1GB", label: "1 GB" },
  { value: "2GB", label: "2 GB" },
  { value: "4GB", label: "4 GB" },
  { value: "8GB", label: "8 GB" },
  { value: "16GB", label: "16 GB" },
] as const;

// Storage options
export const STORAGE_OPTIONS = [
  { value: "10GB", label: "10 GB" },
  { value: "20GB", label: "20 GB" },
  { value: "50GB", label: "50 GB" },
  { value: "100GB", label: "100 GB" },
] as const;

// Type exports
export type CreateDeploymentData = z.infer<typeof createDeploymentSchema>;
export type UpdateDeploymentData = z.infer<typeof updateDeploymentSchema>;
export type ScaleDeploymentData = z.infer<typeof scaleDeploymentSchema>;
export type RollbackDeploymentData = z.infer<typeof rollbackDeploymentSchema>;
export type ResourcesData = z.infer<typeof resourcesSchema>;
