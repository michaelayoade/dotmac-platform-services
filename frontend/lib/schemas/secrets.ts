/**
 * Secrets Form Schemas
 *
 * Zod validation schemas for secrets create/edit forms
 */

import { z } from "zod";

// Secret key-value pair schema
export const secretKeyValueSchema = z.object({
  key: z.string().min(1, "Key is required"),
  value: z.string(),
});

// Create secret schema
export const createSecretSchema = z.object({
  path: z
    .string()
    .min(1, "Path is required")
    .max(255, "Path too long")
    .regex(
      /^[a-z0-9]([a-z0-9._/-]*[a-z0-9])?$/i,
      "Path must start and end with alphanumeric characters"
    ),
  data: z.array(secretKeyValueSchema).min(1, "At least one key-value pair is required"),
  metadata: z.record(z.unknown()).optional(),
});

// Update secret schema
export const updateSecretSchema = z.object({
  data: z.array(secretKeyValueSchema).min(1, "At least one key-value pair is required"),
  metadata: z.record(z.unknown()).optional(),
});

// Rotation policy schema
export const rotationPolicySchema = z.object({
  rotationPeriodDays: z.number().int().min(1).max(365),
  isEnabled: z.boolean().default(true),
});

// Type exports
export type SecretKeyValue = z.infer<typeof secretKeyValueSchema>;
export type CreateSecretData = z.infer<typeof createSecretSchema>;
export type UpdateSecretData = z.infer<typeof updateSecretSchema>;
export type RotationPolicyData = z.infer<typeof rotationPolicySchema>;
