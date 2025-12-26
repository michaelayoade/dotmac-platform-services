/**
 * Branding Settings Form Schemas
 *
 * Zod validation schemas for organization branding settings
 */

import { z } from "zod";

// Color validation helper (hex color)
const hexColorSchema = z
  .string()
  .regex(/^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/, "Please enter a valid hex color (e.g., #FF5500)")
  .optional()
  .or(z.literal(""));

// Simple branding form schema (matches existing form)
export const brandingFormSchema = z.object({
  productName: z.string().max(100, "Product name is too long").optional().default(""),
  tagline: z.string().max(200, "Tagline is too long").optional().default(""),
  primaryColor: hexColorSchema,
  secondaryColor: hexColorSchema,
  accentColor: hexColorSchema,
  supportEmail: z.string().email("Please enter a valid email").optional().or(z.literal("")).default(""),
  // URLs for uploaded assets (not validated as part of form, set separately)
  logoUrl: z.string().optional(),
  faviconUrl: z.string().optional(),
});

// Font options (for extended branding)
export const fontFamilies = [
  { value: "inter", label: "Inter" },
  { value: "system", label: "System Default" },
  { value: "roboto", label: "Roboto" },
  { value: "open-sans", label: "Open Sans" },
  { value: "lato", label: "Lato" },
  { value: "poppins", label: "Poppins" },
] as const;

// Type exports
export type BrandingFormData = z.infer<typeof brandingFormSchema>;
