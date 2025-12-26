/**
 * Workflow Form Schemas
 *
 * Zod validation schemas for workflow create/edit forms
 */

import { z } from "zod";

// Trigger types
export const triggerTypes = [
  { value: "manual", label: "Manual" },
  { value: "scheduled", label: "Scheduled" },
  { value: "webhook", label: "Webhook" },
  { value: "event", label: "Event" },
] as const;

// Step types
export const stepTypes = [
  { value: "action", label: "Action" },
  { value: "condition", label: "Condition" },
  { value: "delay", label: "Delay" },
  { value: "webhook", label: "Webhook" },
  { value: "email", label: "Email" },
  { value: "script", label: "Script" },
] as const;

// Trigger schema
export const triggerSchema = z.object({
  type: z.enum(["manual", "scheduled", "webhook", "event"]),
  config: z.record(z.unknown()).optional(),
});

// Step schema
export const stepSchema = z.object({
  name: z.string().min(1, "Step name is required"),
  type: z.enum(["action", "condition", "delay", "webhook", "email", "script"]),
  config: z.record(z.unknown()).optional(),
  dependencies: z.array(z.string()).optional(),
});

// Workflow create schema
export const createWorkflowSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  description: z.string().optional(),
  triggers: z.array(triggerSchema).min(1, "At least one trigger is required"),
  steps: z.array(stepSchema).optional(),
  tags: z.array(z.string()).optional().default([]),
  isActive: z.boolean().default(false),
});

// Workflow update schema
export const updateWorkflowSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters").optional(),
  description: z.string().optional(),
  triggers: z.array(triggerSchema).optional(),
  steps: z.array(stepSchema).optional(),
  tags: z.array(z.string()).optional(),
  isActive: z.boolean().optional(),
});

// Type exports
export type CreateWorkflowData = z.infer<typeof createWorkflowSchema>;
export type UpdateWorkflowData = z.infer<typeof updateWorkflowSchema>;
export type WorkflowTrigger = z.infer<typeof triggerSchema>;
export type WorkflowStep = z.infer<typeof stepSchema>;
