/**
 * Webhook Form Schemas
 *
 * Zod validation schemas for webhook create/edit forms
 */

import { z } from "zod";

// Create webhook schema
export const createWebhookSchema = z.object({
  url: z
    .string()
    .min(1, "URL is required")
    .url("Must be a valid URL")
    .refine((url) => url.startsWith("https://"), {
      message: "Webhook URL must use HTTPS",
    }),
  description: z.string().max(255, "Description too long").optional(),
  events: z.array(z.string()).min(1, "Select at least one event"),
  headers: z.record(z.string()).optional().default({}),
  isActive: z.boolean().default(true),
  retryEnabled: z.boolean().default(true),
  maxRetries: z.number().int().min(0).max(10).default(3),
  timeoutSeconds: z.number().int().min(5).max(60).default(30),
});

// Update webhook schema
export const updateWebhookSchema = z.object({
  url: z
    .string()
    .url("Must be a valid URL")
    .refine((url) => url.startsWith("https://"), {
      message: "Webhook URL must use HTTPS",
    })
    .optional(),
  description: z.string().max(255, "Description too long").optional(),
  events: z.array(z.string()).min(1, "Select at least one event").optional(),
  headers: z.record(z.string()).optional(),
  isActive: z.boolean().optional(),
  retryEnabled: z.boolean().optional(),
  maxRetries: z.number().int().min(0).max(10).optional(),
  timeoutSeconds: z.number().int().min(5).max(60).optional(),
});

// Type exports
export type CreateWebhookData = z.infer<typeof createWebhookSchema>;
export type UpdateWebhookData = z.infer<typeof updateWebhookSchema>;
