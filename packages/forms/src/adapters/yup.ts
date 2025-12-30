/**
 * Yup Validation Adapter
 *
 * @example
 * ```tsx
 * import * as yup from 'yup';
 * import { Form } from '@dotmac/forms';
 * import { yupResolver } from '@dotmac/forms/yup';
 *
 * const schema = yup.object({
 *   email: yup.string().email().required(),
 *   password: yup.string().min(8).required(),
 * });
 *
 * <Form resolver={yupResolver(schema)} onSubmit={handleSubmit}>
 *   ...
 * </Form>
 * ```
 */

import { yupResolver as hookformYupResolver } from "@hookform/resolvers/yup";

export { hookformYupResolver as yupResolver };

// ============================================================================
// Common Yup Schemas
// ============================================================================

/**
 * Create common validation schemas for Yup
 * Usage: const schemas = createYupSchemas(yup);
 */
export function createYupSchemas(yup: typeof import("yup")) {
  return {
    email: yup
      .string()
      .email("Please enter a valid email address")
      .required("Email is required"),

    password: yup
      .string()
      .min(8, "Password must be at least 8 characters")
      .matches(/[A-Z]/, "Password must contain at least one uppercase letter")
      .matches(/[a-z]/, "Password must contain at least one lowercase letter")
      .matches(/[0-9]/, "Password must contain at least one number")
      .required("Password is required"),

    phone: yup
      .string()
      .matches(/^\+?[1-9]\d{1,14}$/, "Please enter a valid phone number"),

    url: yup.string().url("Please enter a valid URL"),

    requiredString: yup.string().required("This field is required"),

    optionalString: yup.string().notRequired(),

    positiveNumber: yup
      .number()
      .typeError("Please enter a valid number")
      .positive("Must be a positive number")
      .required("This field is required"),

    date: yup.date().typeError("Please enter a valid date").required("Date is required"),

    futureDate: yup
      .date()
      .min(new Date(), "Date must be in the future")
      .required("Date is required"),

    pastDate: yup
      .date()
      .max(new Date(), "Date must be in the past")
      .required("Date is required"),
  };
}

// ============================================================================
// Validation Helpers
// ============================================================================

/**
 * Create a confirmation field schema (e.g., password confirmation)
 */
export function createYupConfirmationSchema(
  yup: typeof import("yup"),
  fieldName: string,
  confirmFieldName: string,
  baseValidation: import("yup").StringSchema
) {
  return yup.object({
    [fieldName]: baseValidation,
    [confirmFieldName]: yup
      .string()
      .oneOf([yup.ref(fieldName)], `Must match ${fieldName}`)
      .required(`Please confirm ${fieldName}`),
  });
}
