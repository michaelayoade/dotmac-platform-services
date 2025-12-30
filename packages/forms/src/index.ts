/**
 * @dotmac/forms
 *
 * Form components with pluggable validation (Zod/Yup),
 * controlled/uncontrolled APIs, and async submission
 *
 * @example
 * ```tsx
 * import { Form, ControlledInput, FormSubmitButton } from '@dotmac/forms';
 * import { zodResolver } from '@dotmac/forms/zod';
 * import { z } from 'zod';
 *
 * const schema = z.object({
 *   email: z.string().email(),
 *   password: z.string().min(8),
 * });
 *
 * function LoginForm() {
 *   const handleSubmit = async (data) => {
 *     await login(data.email, data.password);
 *   };
 *
 *   return (
 *     <Form resolver={zodResolver(schema)} onSubmit={handleSubmit}>
 *       <ControlledInput name="email" label="Email" type="email" />
 *       <ControlledInput name="password" label="Password" type="password" />
 *       <FormSubmitButton>Sign In</FormSubmitButton>
 *     </Form>
 *   );
 * }
 * ```
 */

// ============================================================================
// Form Components
// ============================================================================

export {
  Form,
  FormField,
  FormActions,
  FormSubmitButton,
  FormResetButton,
  useFormStatus,
  type FormProps,
  type FormFieldProps,
  type FormActionsProps,
  type FormSubmitButtonProps,
  type FormResetButtonProps,
} from "./Form";

// ============================================================================
// Input Components
// ============================================================================

export {
  ControlledInput,
  UncontrolledInput,
  FormTextarea,
  FormSelect,
  FormCheckbox,
  type ControlledInputProps,
  type UncontrolledInputProps,
  type FormTextareaProps,
  type FormSelectProps,
  type FormCheckboxProps,
} from "./components/FormInput";

// ============================================================================
// Re-exports from react-hook-form
// ============================================================================

export {
  useForm,
  useFormContext,
  useWatch,
  useFieldArray,
  useFormState,
  Controller,
  FormProvider,
} from "react-hook-form";

export type {
  UseFormReturn,
  FieldValues,
  SubmitHandler,
  SubmitErrorHandler,
  DefaultValues,
  Resolver,
  RegisterOptions,
  FieldError,
  FieldErrors,
} from "react-hook-form";

// ============================================================================
// Utilities
// ============================================================================

export { cn } from "./utils/cn";

// ============================================================================
// Version
// ============================================================================

export const version = "1.0.0";
