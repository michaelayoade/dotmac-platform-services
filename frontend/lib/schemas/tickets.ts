/**
 * Ticket Form Schemas
 *
 * Zod validation schemas for ticket create/edit forms
 */

import { z } from "zod";

// Ticket category options
export const ticketCategories = [
  { value: "support", label: "Support" },
  { value: "billing", label: "Billing" },
  { value: "technical", label: "Technical" },
  { value: "feature_request", label: "Feature Request" },
  { value: "bug", label: "Bug Report" },
  { value: "other", label: "Other" },
] as const;

// Ticket priority options
export const ticketPriorities = [
  { value: "low", label: "Low" },
  { value: "normal", label: "Normal" },
  { value: "high", label: "High" },
  { value: "urgent", label: "Urgent" },
] as const;

// Ticket status options
export const ticketStatuses = [
  { value: "open", label: "Open" },
  { value: "in_progress", label: "In Progress" },
  { value: "waiting", label: "Waiting" },
  { value: "resolved", label: "Resolved" },
  { value: "closed", label: "Closed" },
] as const;

// Ticket create schema
export const createTicketSchema = z.object({
  subject: z
    .string()
    .min(5, "Subject must be at least 5 characters")
    .max(200, "Subject must be at most 200 characters"),
  description: z
    .string()
    .min(20, "Please provide more detail (at least 20 characters)")
    .max(10000, "Description is too long"),
  priority: z.enum(["low", "normal", "high", "urgent"]).default("normal"),
  category: z
    .enum(["support", "billing", "technical", "feature_request", "bug", "other"])
    .default("support"),
  customerId: z.string().uuid("Invalid tenant ID").optional().or(z.literal("")),
  tags: z.array(z.string()).optional().default([]),
});

// Ticket update schema
export const updateTicketSchema = z.object({
  subject: z
    .string()
    .min(5, "Subject must be at least 5 characters")
    .max(200, "Subject must be at most 200 characters")
    .optional(),
  description: z
    .string()
    .min(20, "Please provide more detail (at least 20 characters)")
    .max(10000, "Description is too long")
    .optional(),
  priority: z.enum(["low", "normal", "high", "urgent"]).optional(),
  category: z
    .enum(["support", "billing", "technical", "feature_request", "bug", "other"])
    .optional(),
  status: z.enum(["open", "in_progress", "waiting", "resolved", "closed"]).optional(),
  tags: z.array(z.string()).optional(),
});

// Ticket message schema
export const ticketMessageSchema = z.object({
  message: z
    .string()
    .min(1, "Message is required")
    .max(10000, "Message is too long"),
  isInternal: z.boolean().default(false),
});

// Type exports
export type CreateTicketData = z.infer<typeof createTicketSchema>;
export type UpdateTicketData = z.infer<typeof updateTicketSchema>;
export type TicketMessageData = z.infer<typeof ticketMessageSchema>;
