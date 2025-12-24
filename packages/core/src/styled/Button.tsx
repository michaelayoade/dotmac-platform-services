/**
 * Styled Button
 *
 * Pre-styled button component with DotMac design system
 */

"use client";

import { forwardRef } from "react";

import { Button as ButtonPrimitive, buttonVariants, type ButtonProps } from "../primitives/Button";
import { cn } from "../utils/cn";

// ============================================================================
// Styled Variants (extending primitive variants with theme colors)
// ============================================================================

const styledVariantClasses = {
  default:
    "bg-primary text-primary-foreground hover:bg-primary/90 focus-visible:ring-primary",
  primary:
    "bg-primary text-primary-foreground hover:bg-primary/90 focus-visible:ring-primary",
  secondary:
    "bg-secondary text-secondary-foreground hover:bg-secondary/80 focus-visible:ring-secondary",
  destructive:
    "bg-destructive text-destructive-foreground hover:bg-destructive/90 focus-visible:ring-destructive",
  outline:
    "border border-input bg-background hover:bg-accent hover:text-accent-foreground focus-visible:ring-ring",
  ghost: "hover:bg-accent hover:text-accent-foreground focus-visible:ring-ring",
  link: "text-primary hover:text-primary/80 focus-visible:ring-primary",
};

// ============================================================================
// Styled Button Component
// ============================================================================

export const StyledButton = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", ...props }, ref) => {
    return (
      <ButtonPrimitive
        ref={ref}
        variant={variant}
        className={cn(
          styledVariantClasses[variant || "default"],
          className
        )}
        {...props}
      />
    );
  }
);

StyledButton.displayName = "StyledButton";

// ============================================================================
// Portal-specific Button Variants
// ============================================================================

export interface PortalButtonProps extends ButtonProps {
  portal?: "admin" | "customer" | "reseller" | "technician" | "management";
}

const portalButtonClasses = {
  admin: "bg-blue-600 hover:bg-blue-700 text-white",
  customer: "bg-green-600 hover:bg-green-700 text-white",
  reseller: "bg-purple-600 hover:bg-purple-700 text-white",
  technician: "bg-orange-600 hover:bg-orange-700 text-white",
  management: "bg-gray-800 hover:bg-gray-900 text-white",
};

export const PortalButton = forwardRef<HTMLButtonElement, PortalButtonProps>(
  ({ className, portal = "admin", variant, ...props }, ref) => {
    // If a variant is specified, use styled button behavior
    if (variant && variant !== "default") {
      return (
        <StyledButton ref={ref} className={className} variant={variant} {...props} />
      );
    }

    return (
      <ButtonPrimitive
        ref={ref}
        className={cn(
          buttonVariants({ size: props.size, fullWidth: props.fullWidth }),
          portalButtonClasses[portal],
          "focus-visible:ring-2 focus-visible:ring-offset-2",
          className
        )}
        {...props}
      />
    );
  }
);

PortalButton.displayName = "PortalButton";

// ============================================================================
// Icon Button
// ============================================================================

export interface IconButtonProps extends Omit<ButtonProps, "leftIcon" | "rightIcon"> {
  icon: React.ReactNode;
  "aria-label": string;
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ className, icon, size = "icon", ...props }, ref) => {
    return (
      <StyledButton
        ref={ref}
        size={size}
        className={cn("p-0", className)}
        {...props}
      >
        {icon}
      </StyledButton>
    );
  }
);

IconButton.displayName = "IconButton";

export { buttonVariants };
export type { ButtonProps };
export default StyledButton;
