/**
 * Contact Form Schemas
 *
 * Zod validation schemas for contact create/edit forms
 */

import { z } from "zod";

// Contact status options
export const contactStatuses = [
  { value: "active", label: "Active" },
  { value: "inactive", label: "Inactive" },
  { value: "archived", label: "Archived" },
  { value: "blocked", label: "Blocked" },
  { value: "pending", label: "Pending" },
] as const;

// Contact stage options
export const contactStages = [
  { value: "prospect", label: "Prospect" },
  { value: "lead", label: "Lead" },
  { value: "opportunity", label: "Opportunity" },
  { value: "account", label: "Account" },
  { value: "partner", label: "Partner" },
  { value: "vendor", label: "Vendor" },
  { value: "other", label: "Other" },
] as const;

// Contact method type options
export const contactMethodTypes = [
  { value: "email", label: "Email" },
  { value: "phone", label: "Phone" },
  { value: "mobile", label: "Mobile" },
  { value: "fax", label: "Fax" },
  { value: "website", label: "Website" },
  { value: "social_linkedin", label: "LinkedIn" },
  { value: "social_twitter", label: "Twitter" },
  { value: "social_facebook", label: "Facebook" },
  { value: "social_instagram", label: "Instagram" },
  { value: "address", label: "Address" },
  { value: "other", label: "Other" },
] as const;

// Contact method schema
export const contactMethodSchema = z.object({
  type: z.enum([
    "email",
    "phone",
    "mobile",
    "fax",
    "website",
    "social_linkedin",
    "social_twitter",
    "social_facebook",
    "social_instagram",
    "address",
    "other",
  ]),
  value: z.string().min(1, "Value is required"),
  label: z.string().optional(),
  isPrimary: z.boolean().optional().default(false),
});

// Contact create schema
export const createContactSchema = z.object({
  firstName: z.string().min(1, "First name is required"),
  lastName: z.string().optional(),
  displayName: z.string().optional(),
  company: z.string().optional(),
  jobTitle: z.string().optional(),
  department: z.string().optional(),
  email: z.string().email("Please enter a valid email address").optional().or(z.literal("")),
  phone: z.string().optional(),
  status: z.enum(["active", "inactive", "archived", "blocked", "pending"]).default("active"),
  stage: z
    .enum(["prospect", "lead", "opportunity", "account", "partner", "vendor", "other"])
    .default("prospect"),
  notes: z.string().optional(),
  tags: z.array(z.string()).optional().default([]),
  isPrimary: z.boolean().optional().default(false),
  isDecisionMaker: z.boolean().optional().default(false),
  isBillingContact: z.boolean().optional().default(false),
  isTechnicalContact: z.boolean().optional().default(false),
  preferredLanguage: z.string().optional(),
  timezone: z.string().optional(),
});

// Contact update schema (all fields optional)
export const updateContactSchema = z.object({
  firstName: z.string().min(1, "First name is required").optional(),
  lastName: z.string().optional(),
  displayName: z.string().optional(),
  company: z.string().optional(),
  jobTitle: z.string().optional(),
  department: z.string().optional(),
  email: z.string().email("Please enter a valid email address").optional().or(z.literal("")),
  phone: z.string().optional(),
  status: z.enum(["active", "inactive", "archived", "blocked", "pending"]).optional(),
  stage: z
    .enum(["prospect", "lead", "opportunity", "account", "partner", "vendor", "other"])
    .optional(),
  notes: z.string().optional(),
  tags: z.array(z.string()).optional(),
  isPrimary: z.boolean().optional(),
  isDecisionMaker: z.boolean().optional(),
  isBillingContact: z.boolean().optional(),
  isTechnicalContact: z.boolean().optional(),
  preferredLanguage: z.string().optional(),
  timezone: z.string().optional(),
});

// Type exports
export type CreateContactData = z.infer<typeof createContactSchema>;
export type UpdateContactData = z.infer<typeof updateContactSchema>;
export type ContactMethodData = z.infer<typeof contactMethodSchema>;
