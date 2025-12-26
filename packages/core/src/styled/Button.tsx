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
  portal?: "admin" | "tenant" | "reseller" | "technician" | "management";
}

const portalButtonClasses = {
  admin: "bg-portal-admin hover:bg-portal-admin/90 text-text-inverse",
  tenant: "bg-portal-tenant hover:bg-portal-tenant/90 text-text-inverse",
  reseller: "bg-portal-reseller hover:bg-portal-reseller/90 text-text-inverse",
  technician: "bg-portal-technician hover:bg-portal-technician/90 text-text-inverse",
  management: "bg-portal-management hover:bg-portal-management/90 text-text-inverse",
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
