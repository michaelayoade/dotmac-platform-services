/**
 * Zod Validation Adapter
 *
 * @example
 * ```tsx
 * import { z } from 'zod';
 * import { Form } from '@dotmac/forms';
 * import { zodResolver } from '@dotmac/forms/zod';
 *
 * const schema = z.object({
 *   email: z.string().email(),
 *   password: z.string().min(8),
 * });
 *
 * <Form resolver={zodResolver(schema)} onSubmit={handleSubmit}>
 *   ...
 * </Form>
 * ```
 */

import { zodResolver as hookformZodResolver } from "@hookform/resolvers/zod";
import type { z } from "zod";

export { hookformZodResolver as zodResolver };

// ============================================================================
// Common Zod Schemas
// ============================================================================

/**
 * Create common validation schemas
 * Usage: const schemas = createValidationSchemas(z);
 */
export function createValidationSchemas(zod: typeof z) {
  return {
    email: zod.string().email("Please enter a valid email address"),

    password: zod
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
      .regex(/[a-z]/, "Password must contain at least one lowercase letter")
      .regex(/[0-9]/, "Password must contain at least one number"),

    phone: zod
      .string()
      .regex(/^\+?[1-9]\d{1,14}$/, "Please enter a valid phone number"),

    url: zod.string().url("Please enter a valid URL"),

    requiredString: zod.string().min(1, "This field is required"),

    optionalString: zod.string().optional(),

    positiveNumber: zod
      .number({ invalid_type_error: "Please enter a valid number" })
      .positive("Must be a positive number"),

    date: zod.coerce.date({ invalid_type_error: "Please enter a valid date" }),

    futureDate: zod.coerce.date().refine((date) => date > new Date(), {
      message: "Date must be in the future",
    }),

    pastDate: zod.coerce.date().refine((date) => date < new Date(), {
      message: "Date must be in the past",
    }),
  };
}

// ============================================================================
// Validation Helpers
// ============================================================================

/**
 * Create a confirmation field schema (e.g., password confirmation)
 */
export function createConfirmationSchema<T extends z.ZodTypeAny>(
  zod: typeof z,
  field: T,
  fieldName: string,
  confirmFieldName: string
) {
  return zod
    .object({
      [fieldName]: field,
      [confirmFieldName]: field,
    })
    .refine((data) => data[fieldName] === data[confirmFieldName], {
      message: `${confirmFieldName} must match ${fieldName}`,
      path: [confirmFieldName],
    });
}

/**
 * Create async validation schema
 */
export function createAsyncValidation<T>(
  _zod: typeof z,
  baseSchema: z.ZodType<T>,
  asyncValidator: (value: T) => Promise<boolean>,
  errorMessage: string
) {
  return baseSchema.refine(asyncValidator, { message: errorMessage });
}
