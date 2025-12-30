/**
 * Partner/Referral Form Schemas
 *
 * Zod validation schemas for partner and referral forms
 */

import { z } from "zod";

// Partner status options
export const partnerStatuses = [
  { value: "pending", label: "Pending" },
  { value: "active", label: "Active" },
  { value: "inactive", label: "Inactive" },
  { value: "suspended", label: "Suspended" },
] as const;

// Partner tier options
export const partnerTiers = [
  { value: "bronze", label: "Bronze" },
  { value: "silver", label: "Silver" },
  { value: "gold", label: "Gold" },
  { value: "platinum", label: "Platinum" },
] as const;

// Referral status options
export const referralStatuses = [
  { value: "pending", label: "Pending" },
  { value: "contacted", label: "Contacted" },
  { value: "qualified", label: "Qualified" },
  { value: "converted", label: "Converted" },
  { value: "lost", label: "Lost" },
] as const;

// Partner create schema
export const createPartnerSchema = z.object({
  name: z
    .string()
    .min(2, "Name must be at least 2 characters")
    .max(100, "Name must be at most 100 characters"),
  email: z.string().email("Please enter a valid email address"),
  phone: z.string().optional(),
  company: z.string().optional(),
  website: z.string().url("Please enter a valid URL").optional().or(z.literal("")),
  tier: z.enum(["bronze", "silver", "gold", "platinum"]).default("bronze"),
  commissionRate: z.coerce
    .number()
    .min(0, "Commission rate must be 0 or greater")
    .max(100, "Commission rate cannot exceed 100%")
    .default(10),
  notes: z.string().max(2000, "Notes are too long").optional(),
});

// Referral create schema
export const createReferralSchema = z.object({
  firstName: z.string().min(1, "First name is required"),
  lastName: z.string().min(1, "Last name is required"),
  email: z.string().email("Please enter a valid email address"),
  phone: z.string().optional(),
  company: z.string().optional(),
  jobTitle: z.string().optional(),
  estimatedValue: z.coerce
    .number()
    .min(0, "Value must be 0 or greater")
    .optional(),
  notes: z.string().max(2000, "Notes are too long").optional(),
  source: z.string().optional(),
});

// Referral update schema
export const updateReferralSchema = z.object({
  firstName: z.string().min(1, "First name is required").optional(),
  lastName: z.string().min(1, "Last name is required").optional(),
  email: z.string().email("Please enter a valid email address").optional(),
  phone: z.string().optional(),
  company: z.string().optional(),
  jobTitle: z.string().optional(),
  status: z.enum(["pending", "contacted", "qualified", "converted", "lost"]).optional(),
  estimatedValue: z.coerce.number().min(0, "Value must be 0 or greater").optional(),
  notes: z.string().max(2000, "Notes are too long").optional(),
});

// Type exports
export type CreatePartnerData = z.infer<typeof createPartnerSchema>;
export type CreateReferralData = z.infer<typeof createReferralSchema>;
export type UpdateReferralData = z.infer<typeof updateReferralSchema>;
