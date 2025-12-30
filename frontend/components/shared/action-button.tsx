"use client";

import { forwardRef } from "react";
import { Button, type ButtonProps } from "@dotmac/core";

export interface ActionButtonProps extends ButtonProps {
  /** Whether the action is currently pending (shows loading state) */
  isPending?: boolean;
  /** Text to show while loading (replaces children) */
  loadingText?: string;
}

/**
 * Action button for mutations with built-in loading state support.
 * Wraps the base Button component with convenience props for async actions.
 *
 * @example
 * ```tsx
 * const deleteMutation = useDeleteUser();
 *
 * <ActionButton
 *   variant="destructive"
 *   isPending={deleteMutation.isPending}
 *   loadingText="Deleting..."
 *   onClick={() => deleteMutation.mutate(userId)}
 * >
 *   Delete User
 * </ActionButton>
 * ```
 */
export const ActionButton = forwardRef<HTMLButtonElement, ActionButtonProps>(
  ({ isPending = false, loadingText, disabled, children, ...props }, ref) => {
    return (
      <Button
        ref={ref}
        disabled={disabled || isPending}
        loading={isPending}
        {...props}
      >
        {isPending && loadingText ? loadingText : children}
      </Button>
    );
  }
);

ActionButton.displayName = "ActionButton";
