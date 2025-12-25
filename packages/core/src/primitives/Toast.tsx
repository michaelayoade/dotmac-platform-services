/**
 * Toast System (Radix-based)
 *
 * Provides a simple provider + hook for firing transient toasts.
 */

"use client";

import React, { createContext, useContext, useState, forwardRef } from "react";
import * as ToastPrimitive from "@radix-ui/react-toast";
import { cva, type VariantProps } from "class-variance-authority";
import { X, CheckCircle2, AlertTriangle, Info } from "lucide-react";

import { cn } from "../utils/cn";

// ============================================================================//
// Variants
// ============================================================================//

const toastVariants = cva(
  [
    "relative flex w-[360px] max-w-full items-start gap-3 overflow-hidden rounded-lg border p-4 shadow-lg",
    "bg-card text-card-foreground",
    "data-[state=open]:animate-in data-[state=closed]:animate-out",
    "data-[state=open]:slide-in-from-right data-[state=closed]:slide-out-to-right",
  ],
  {
    variants: {
      variant: {
        default: "border-border text-foreground",
        success:
          "border-success/30 bg-success/10 text-success",
        warning:
          "border-warning/30 bg-warning/10 text-warning",
        error:
          "border-destructive/30 bg-destructive/10 text-destructive",
        info: "border-info/30 bg-info/10 text-info",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

// ============================================================================//
// Types
// ============================================================================//

export type ToastVariant = NonNullable<VariantProps<typeof toastVariants>["variant"]>;

export interface ToastMessage {
  id?: string;
  title?: string;
  description?: string;
  variant?: ToastVariant;
  duration?: number;
  actionLabel?: string;
  onAction?: () => void;
}

interface ToastContextValue {
  toast: (message: ToastMessage) => void;
  dismiss: (id: string) => void;
}

// ============================================================================//
// Context + Provider
// ============================================================================//

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const toast = (message: ToastMessage) => {
    const id = message.id ?? Math.random().toString(36).slice(2);
    setToasts((prev) => [...prev, { ...message, id }]);
  };

  const dismiss = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastPrimitive.Provider swipeDirection="right">
      <ToastContext.Provider value={{ toast, dismiss }}>
        {children}
        {toasts.map((t) => (
          <ToastPrimitive.Root
            key={t.id}
            duration={t.duration ?? 4000}
            className={cn(toastVariants({ variant: t.variant }))}
            onOpenChange={(open) => {
              if (!open && t.id) dismiss(t.id);
            }}
          >
            <div className="mt-0.5 text-base">
              {t.variant === "success" && <CheckCircle2 className="h-5 w-5" aria-hidden />}
              {t.variant === "warning" && <AlertTriangle className="h-5 w-5" aria-hidden />}
              {t.variant === "error" && <AlertTriangle className="h-5 w-5" aria-hidden />}
              {(!t.variant || t.variant === "info" || t.variant === "default") && (
                <Info className="h-5 w-5" aria-hidden />
              )}
            </div>
            <div className="space-y-1 pr-6 text-sm">
              {t.title && <div className="font-semibold leading-none">{t.title}</div>}
              {t.description && <div className="text-muted-foreground text-xs leading-snug">{t.description}</div>}
              {t.actionLabel && t.onAction && (
                <button
                  onClick={() => t.onAction?.()}
                  className="text-xs font-semibold text-primary hover:text-primary/80"
                >
                  {t.actionLabel}
                </button>
              )}
            </div>
            <ToastPrimitive.Close asChild>
              <button
                aria-label="Close"
                className="absolute right-2 top-2 rounded p-1 text-muted-foreground transition hover:bg-muted hover:text-foreground"
                onClick={() => t.id && dismiss(t.id)}
              >
                <X className="h-4 w-4" />
              </button>
            </ToastPrimitive.Close>
          </ToastPrimitive.Root>
        ))}
        <ToastViewport />
      </ToastContext.Provider>
    </ToastPrimitive.Provider>
  );
}

// ============================================================================//
// Hook
// ============================================================================//

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return ctx;
}

// ============================================================================//
// Primitives
// ============================================================================//

export const ToastViewport = forwardRef<
  React.ElementRef<typeof ToastPrimitive.Viewport>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitive.Viewport>
>(({ className, ...props }, ref) => (
  <ToastPrimitive.Viewport
    ref={ref}
    className={cn(
      "fixed right-4 top-4 z-[9999] flex max-h-screen w-full max-w-md flex-col gap-3",
      className
    )}
    {...props}
  />
));
ToastViewport.displayName = ToastPrimitive.Viewport.displayName;
