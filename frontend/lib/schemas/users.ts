/**
 * User Form Schemas
 *
 * Zod validation schemas for user create/edit forms
 */

import { z } from "zod";

// User role options
export const userRoles = [
  { value: "owner", label: "Owner" },
  { value: "admin", label: "Admin" },
  { value: "member", label: "Member" },
  { value: "viewer", label: "Viewer" },
] as const;

// User status options
export const userStatuses = [
  { value: "active", label: "Active" },
  { value: "pending", label: "Pending" },
  { value: "suspended", label: "Suspended" },
  { value: "inactive", label: "Inactive" },
] as const;

// User create schema
export const createUserSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  name: z.string().min(2, "Name must be at least 2 characters"),
  role: z.enum(["owner", "admin", "member", "viewer"], {
    required_error: "Please select a role",
  }),
  sendInvite: z.boolean().default(true),
});

// User update schema
export const updateUserSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters").optional(),
  role: z.enum(["owner", "admin", "member", "viewer"]).optional(),
  status: z.enum(["active", "pending", "suspended", "inactive"]).optional(),
});

// Type exports
export type CreateUserData = z.infer<typeof createUserSchema>;
export type UpdateUserData = z.infer<typeof updateUserSchema>;
