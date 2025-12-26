/**
 * Form Input Components
 *
 * Pre-wired input components for react-hook-form
 */

"use client";

import { useFormContext, Controller, type RegisterOptions } from "react-hook-form";
import { forwardRef, type InputHTMLAttributes, type TextareaHTMLAttributes } from "react";

import { cn } from "../utils/cn";
import { FormField } from "../Form";

// ============================================================================
// Controlled Text Input
// ============================================================================

export interface ControlledInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "name"> {
  name: string;
  label?: string;
  description?: string;
  rules?: RegisterOptions;
}

export const ControlledInput = forwardRef<HTMLInputElement, ControlledInputProps>(
  ({ name, label, description, rules, className, type = "text", ...props }, ref) => {
    const { control, formState } = useFormContext();
    const error = formState.errors[name];

    return (
      <Controller
        name={name}
        control={control}
        rules={rules}
        render={({ field }) => (
          <FormField
            name={name}
            label={label}
            description={description}
            required={!!rules?.required}
          >
            <input
              {...field}
              {...props}
              ref={ref}
              id={name}
              type={type}
              aria-invalid={!!error}
              aria-describedby={error ? `${name}-error` : description ? `${name}-desc` : undefined}
              className={cn(
                "w-full h-10 px-3 rounded-md border text-sm",
                "bg-background text-foreground placeholder:text-muted-foreground",
                "focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent",
                "disabled:bg-muted disabled:text-muted-foreground disabled:cursor-not-allowed",
                error ? "border-destructive" : "border-input",
                className
              )}
            />
          </FormField>
        )}
      />
    );
  }
);

ControlledInput.displayName = "ControlledInput";

// ============================================================================
// Uncontrolled Text Input (uses register)
// ============================================================================

export interface UncontrolledInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "name"> {
  name: string;
  label?: string;
  description?: string;
  rules?: RegisterOptions;
}

export const UncontrolledInput = forwardRef<HTMLInputElement, UncontrolledInputProps>(
  ({ name, label, description, rules, className, type = "text", ...props }, _ref) => {
    const { register, formState } = useFormContext();
    const error = formState.errors[name];
    const registration = register(name, rules);

    return (
      <FormField
        name={name}
        label={label}
        description={description}
        required={!!rules?.required}
      >
        <input
          {...registration}
          {...props}
          id={name}
          type={type}
          aria-invalid={!!error}
          className={cn(
            "w-full h-10 px-3 rounded-md border text-sm",
            "bg-background text-foreground placeholder:text-muted-foreground",
            "focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent",
            "disabled:bg-muted disabled:text-muted-foreground disabled:cursor-not-allowed",
            error ? "border-destructive" : "border-input",
            className
          )}
        />
      </FormField>
    );
  }
);

UncontrolledInput.displayName = "UncontrolledInput";

// ============================================================================
// Textarea
// ============================================================================

export interface FormTextareaProps extends Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "name"> {
  name: string;
  label?: string;
  description?: string;
  rules?: RegisterOptions;
  controlled?: boolean;
}

export const FormTextarea = forwardRef<HTMLTextAreaElement, FormTextareaProps>(
  ({ name, label, description, rules, controlled = false, className, ...props }, ref) => {
    const { register, control, formState } = useFormContext();
    const error = formState.errors[name];

    const textareaClasses = cn(
      "w-full min-h-[80px] px-3 py-2 rounded-md border text-sm",
      "bg-background text-foreground placeholder:text-muted-foreground",
      "focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent",
      "disabled:bg-muted disabled:text-muted-foreground disabled:cursor-not-allowed",
      "resize-y",
      error ? "border-destructive" : "border-input",
      className
    );

    if (controlled) {
      return (
        <Controller
          name={name}
          control={control}
          rules={rules}
          render={({ field }) => (
            <FormField
              name={name}
              label={label}
              description={description}
              required={!!rules?.required}
            >
              <textarea
                {...field}
                {...props}
                ref={ref}
                id={name}
                aria-invalid={!!error}
                className={textareaClasses}
              />
            </FormField>
          )}
        />
      );
    }

    return (
      <FormField
        name={name}
        label={label}
        description={description}
        required={!!rules?.required}
      >
        <textarea
          {...register(name, rules)}
          {...props}
          id={name}
          aria-invalid={!!error}
          className={textareaClasses}
        />
      </FormField>
    );
  }
);

FormTextarea.displayName = "FormTextarea";

// ============================================================================
// Select
// ============================================================================

export interface FormSelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "name"> {
  name: string;
  label?: string;
  description?: string;
  rules?: RegisterOptions;
  options: Array<{ value: string; label: string }>;
  placeholder?: string;
}

export const FormSelect = forwardRef<HTMLSelectElement, FormSelectProps>(
  ({ name, label, description, rules, options, placeholder, className, ...props }, _ref) => {
    const { register, formState } = useFormContext();
    const error = formState.errors[name];

    return (
      <FormField
        name={name}
        label={label}
        description={description}
        required={!!rules?.required}
      >
        <select
          {...register(name, rules)}
          {...props}
          id={name}
          aria-invalid={!!error}
          className={cn(
            "w-full h-10 px-3 rounded-md border text-sm",
            "bg-background text-foreground",
            "focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent",
            "disabled:bg-muted disabled:text-muted-foreground disabled:cursor-not-allowed",
            error ? "border-destructive" : "border-input",
            className
          )}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </FormField>
    );
  }
);

FormSelect.displayName = "FormSelect";

// ============================================================================
// Checkbox
// ============================================================================

export interface FormCheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "name" | "type"> {
  name: string;
  label: string;
  description?: string;
  rules?: RegisterOptions;
}

export const FormCheckbox = forwardRef<HTMLInputElement, FormCheckboxProps>(
  ({ name, label, description, rules, className, ...props }, _ref) => {
    const { register, formState } = useFormContext();
    const error = formState.errors[name];

    return (
      <div className={cn("flex items-start gap-3", className)}>
        <input
          {...register(name, rules)}
          {...props}
          id={name}
          type="checkbox"
          aria-invalid={!!error}
          className={cn(
            "h-4 w-4 rounded border-input text-primary",
            "focus:ring-2 focus:ring-ring",
            "disabled:opacity-50",
            error && "border-destructive"
          )}
        />
        <div className="flex flex-col">
          <label htmlFor={name} className="text-sm font-medium text-foreground">
            {label}
          </label>
          {description && (
            <p className="text-sm text-muted-foreground">{description}</p>
          )}
          {error && (
            <p className="text-sm text-destructive">{error.message as string}</p>
          )}
        </div>
      </div>
    );
  }
);

FormCheckbox.displayName = "FormCheckbox";
