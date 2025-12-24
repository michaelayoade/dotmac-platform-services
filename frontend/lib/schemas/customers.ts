/**
 * Customer Form Schemas
 *
 * Zod validation schemas for customer create/edit forms
 */

import { z } from "zod";

// Address schema (reusable)
export const addressSchema = z.object({
  line1: z.string().min(1, "Address line 1 is required"),
  line2: z.string().optional(),
  city: z.string().min(1, "City is required"),
  state: z.string().min(1, "State is required"),
  postalCode: z.string().min(1, "Postal code is required"),
  country: z.string().min(1, "Country is required"),
});

// Customer create schema
export const createCustomerSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Please enter a valid email address"),
  phone: z.string().optional(),
  company: z.string().optional(),
  type: z.enum(["individual", "business", "enterprise"], {
    required_error: "Please select a customer type",
  }),
  billingAddress: addressSchema.optional(),
  tags: z.array(z.string()).optional().default([]),
  metadata: z.record(z.unknown()).optional(),
});

// Customer update schema (all fields optional except for validation)
export const updateCustomerSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters").optional(),
  email: z.string().email("Please enter a valid email address").optional(),
  phone: z.string().optional(),
  company: z.string().optional(),
  status: z.enum(["active", "inactive", "churned", "lead", "prospect"]).optional(),
  type: z.enum(["individual", "business", "enterprise"]).optional(),
  billingAddress: addressSchema.optional(),
  tags: z.array(z.string()).optional(),
  metadata: z.record(z.unknown()).optional(),
});

// Customer note schema
export const customerNoteSchema = z.object({
  content: z.string().min(1, "Note content is required").max(5000, "Note is too long"),
});

// Tag schema
export const customerTagSchema = z.object({
  tag: z.string().min(1, "Tag is required").max(50, "Tag is too long"),
});

// Type exports
export type CreateCustomerData = z.infer<typeof createCustomerSchema>;
export type UpdateCustomerData = z.infer<typeof updateCustomerSchema>;
export type CustomerNoteData = z.infer<typeof customerNoteSchema>;
export type CustomerTagData = z.infer<typeof customerTagSchema>;
export type AddressData = z.infer<typeof addressSchema>;
