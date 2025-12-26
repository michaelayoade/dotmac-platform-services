import {
  useMutation,
  type UseMutationOptions,
  type UseMutationResult,
} from "@tanstack/react-query";
import { useToast } from "@dotmac/core";

type MutationMessages<TData, TError> = {
  /** Success message - string or function that receives the mutation result */
  successMessage?: string | ((data: TData) => string);
  /** Error message - string or function that receives the error */
  errorMessage?: string | ((error: TError) => string);
  /** Whether to show success toast (default: true if successMessage provided) */
  showSuccessToast?: boolean;
  /** Whether to show error toast (default: true) */
  showErrorToast?: boolean;
};

type UseMutationWithToastOptions<
  TData = unknown,
  TError = Error,
  TVariables = void,
  TContext = unknown,
> = UseMutationOptions<TData, TError, TVariables, TContext> &
  MutationMessages<TData, TError>;

/**
 * Extract a human-readable error message from various error types
 */
function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  if (
    typeof error === "object" &&
    error !== null &&
    "message" in error &&
    typeof error.message === "string"
  ) {
    return error.message;
  }
  if (typeof error === "string") {
    return error;
  }
  return "An unexpected error occurred. Please try again.";
}

/**
 * Wrapper around useMutation that automatically shows toast notifications
 * on success and error.
 *
 * @example
 * ```tsx
 * const deleteUser = useMutationWithToast({
 *   mutationFn: (id: string) => api.deleteUser(id),
 *   successMessage: "User deleted successfully",
 *   errorMessage: (error) => `Failed to delete user: ${error.message}`,
 *   onSuccess: () => {
 *     queryClient.invalidateQueries({ queryKey: ["users"] });
 *   },
 * });
 * ```
 */
export function useMutationWithToast<
  TData = unknown,
  TError = Error,
  TVariables = void,
  TContext = unknown,
>(
  options: UseMutationWithToastOptions<TData, TError, TVariables, TContext>
): UseMutationResult<TData, TError, TVariables, TContext> {
  const { toast } = useToast();

  const {
    successMessage,
    errorMessage,
    showSuccessToast = !!successMessage,
    showErrorToast = true,
    onSuccess,
    onError,
    ...mutationOptions
  } = options;

  return useMutation({
    ...mutationOptions,
    onSuccess: (data, variables, context, mutation) => {
      if (showSuccessToast && successMessage) {
        const message =
          typeof successMessage === "function"
            ? successMessage(data)
            : successMessage;

        toast({
          title: "Success",
          description: message,
          variant: "success",
        });
      }
      onSuccess?.(data, variables, context, mutation);
    },
    onError: (error, variables, context, mutation) => {
      if (showErrorToast) {
        const message = errorMessage
          ? typeof errorMessage === "function"
            ? errorMessage(error)
            : errorMessage
          : getErrorMessage(error);

        toast({
          title: "Error",
          description: message,
          variant: "error",
        });
      }
      onError?.(error, variables, context, mutation);
    },
  });
}
