/**
 * @dotmac/forms - Form Component
 *
 * Main form wrapper with:
 * - Pluggable validation (Zod/Yup via adapters)
 * - Controlled and uncontrolled modes
 * - Async submission with loading states
 * - Error handling and display
 */

"use client";

import {
  useForm,
  FormProvider,
  useFormContext,
  type UseFormReturn,
  type FieldValues,
  type SubmitHandler,
  type SubmitErrorHandler,
  type DefaultValues,
  type Resolver,
} from "react-hook-form";
import { createContext, useContext, forwardRef, type FormHTMLAttributes, type ReactNode } from "react";

import { cn } from "./utils/cn";

// ============================================================================
// Types
// ============================================================================

export interface FormProps<TFieldValues extends FieldValues>
  extends Omit<FormHTMLAttributes<HTMLFormElement>, "onSubmit" | "onError" | "children"> {
  /** Form methods from useForm or useFormContext */
  form?: UseFormReturn<TFieldValues>;
  /** Default values for uncontrolled mode */
  defaultValues?: DefaultValues<TFieldValues>;
  /** Validation resolver (from @hookform/resolvers) */
  resolver?: Resolver<TFieldValues>;
  /** Submit handler */
  onSubmit: SubmitHandler<TFieldValues>;
  /** Error handler */
  onError?: SubmitErrorHandler<TFieldValues>;
  /** Async submit - shows loading state */
  asyncSubmit?: boolean;
  /** Children render prop or ReactNode */
  children: ReactNode | ((form: UseFormReturn<TFieldValues>) => ReactNode);
  /** Disable form during submission */
  disableOnSubmit?: boolean;
  /** Reset form after successful submit */
  resetOnSuccess?: boolean;
}

// ============================================================================
// Form Status Context
// ============================================================================

interface FormStatusContextValue {
  isSubmitting: boolean;
  isSubmitSuccessful: boolean;
  submitCount: number;
  isValid: boolean;
  isDirty: boolean;
  errors: Record<string, unknown>;
}

const FormStatusContext = createContext<FormStatusContextValue | null>(null);

export function useFormStatus(): FormStatusContextValue {
  const context = useContext(FormStatusContext);
  if (!context) {
    throw new Error("useFormStatus must be used within a Form component");
  }
  return context;
}

// ============================================================================
// Form Component
// ============================================================================

export function Form<TFieldValues extends FieldValues = FieldValues>({
  form: externalForm,
  defaultValues,
  resolver,
  onSubmit,
  onError,
  asyncSubmit = true,
  children,
  disableOnSubmit = true,
  resetOnSuccess = false,
  className,
  ...props
}: FormProps<TFieldValues>) {
  // Create internal form if not provided
  const internalForm = useForm<TFieldValues>({
    defaultValues,
    resolver,
  });

  const form = externalForm ?? internalForm;
  const { handleSubmit, formState, reset } = form;
  const { isSubmitting, isSubmitSuccessful, submitCount, isValid, isDirty, errors } = formState;

  // Wrapped submit handler with async support
  const wrappedSubmit: SubmitHandler<TFieldValues> = async (data) => {
    try {
      await onSubmit(data);
      if (resetOnSuccess) {
        reset();
      }
    } catch (error) {
      // Re-throw for react-hook-form to handle
      throw error;
    }
  };

  const statusValue: FormStatusContextValue = {
    isSubmitting,
    isSubmitSuccessful,
    submitCount,
    isValid,
    isDirty,
    errors: errors as Record<string, unknown>,
  };

  return (
    <FormProvider {...form}>
      <FormStatusContext.Provider value={statusValue}>
        <form
          onSubmit={handleSubmit(wrappedSubmit, onError)}
          className={cn(
            disableOnSubmit && isSubmitting && "pointer-events-none opacity-70",
            className
          )}
          noValidate
          {...props}
        >
          {typeof children === "function" ? children(form) : children}
        </form>
      </FormStatusContext.Provider>
    </FormProvider>
  );
}

// ============================================================================
// Form Field Component
// ============================================================================

export interface FormFieldProps {
  name: string;
  label?: string;
  description?: string;
  required?: boolean;
  children: ReactNode;
  className?: string;
}

export function FormField({
  name,
  label,
  description,
  required,
  children,
  className,
}: FormFieldProps) {
  const { formState } = useFormContext();
  const error = formState.errors[name];

  return (
    <div className={cn("space-y-2", className)}>
      {label && (
        <label
          htmlFor={name}
          className="text-sm font-medium text-gray-700"
        >
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      {children}
      {description && !error && (
        <p className="text-sm text-gray-500">{description}</p>
      )}
      {error && (
        <p className="text-sm text-red-600" role="alert">
          {error.message as string}
        </p>
      )}
    </div>
  );
}

// ============================================================================
// Form Actions (Submit/Reset buttons container)
// ============================================================================

export interface FormActionsProps {
  children: ReactNode;
  className?: string;
  align?: "left" | "center" | "right" | "between";
}

export function FormActions({ children, className, align = "right" }: FormActionsProps) {
  const alignClasses = {
    left: "justify-start",
    center: "justify-center",
    right: "justify-end",
    between: "justify-between",
  };

  return (
    <div className={cn("flex items-center gap-3 pt-4", alignClasses[align], className)}>
      {children}
    </div>
  );
}

// ============================================================================
// Form Submit Button
// ============================================================================

export interface FormSubmitButtonProps {
  children?: ReactNode;
  loadingText?: string;
  className?: string;
  disabled?: boolean;
}

export const FormSubmitButton = forwardRef<HTMLButtonElement, FormSubmitButtonProps>(
  ({ children = "Submit", loadingText = "Submitting...", className, disabled }, ref) => {
    const { isSubmitting, isValid, isDirty } = useFormStatus();
    const isDisabled = disabled || isSubmitting || (!isValid && isDirty);

    return (
      <button
        ref={ref}
        type="submit"
        disabled={isDisabled}
        className={cn(
          "inline-flex items-center justify-center",
          "h-10 px-4 rounded-md",
          "bg-blue-600 text-white font-medium text-sm",
          "hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          "transition-colors",
          className
        )}
      >
        {isSubmitting ? (
          <>
            <svg
              className="animate-spin -ml-1 mr-2 h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            {loadingText}
          </>
        ) : (
          children
        )}
      </button>
    );
  }
);

FormSubmitButton.displayName = "FormSubmitButton";

// ============================================================================
// Form Reset Button
// ============================================================================

export interface FormResetButtonProps {
  children?: ReactNode;
  className?: string;
}

export const FormResetButton = forwardRef<HTMLButtonElement, FormResetButtonProps>(
  ({ children = "Reset", className }, ref) => {
    const { reset } = useFormContext();
    const { isSubmitting } = useFormStatus();

    return (
      <button
        ref={ref}
        type="button"
        onClick={() => reset()}
        disabled={isSubmitting}
        className={cn(
          "inline-flex items-center justify-center",
          "h-10 px-4 rounded-md",
          "bg-gray-100 text-gray-700 font-medium text-sm",
          "hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          "transition-colors",
          className
        )}
      >
        {children}
      </button>
    );
  }
);

FormResetButton.displayName = "FormResetButton";

export default Form;
