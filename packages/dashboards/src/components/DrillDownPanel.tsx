/**
 * Drill Down Panel Component
 *
 * Slide-out panel for detailed data exploration
 */

"use client";

import { X, ChevronLeft, ExternalLink } from "lucide-react";
import { useEffect, type ReactNode } from "react";

import { cn } from "../utils/cn";

// ============================================================================
// Types
// ============================================================================

export interface DrillDownPanelProps {
  /** Panel is open */
  open: boolean;
  /** On close callback */
  onClose: () => void;
  /** Panel title */
  title?: string;
  /** Panel subtitle */
  subtitle?: string;
  /** Breadcrumb items */
  breadcrumbs?: Array<{ label: string; onClick?: () => void }>;
  /** Panel content */
  children: ReactNode;
  /** Panel width */
  width?: "sm" | "md" | "lg" | "xl" | "full";
  /** Panel position */
  position?: "right" | "left";
  /** Show overlay */
  overlay?: boolean;
  /** Header actions */
  actions?: ReactNode;
  /** Footer content */
  footer?: ReactNode;
  /** External link */
  externalLink?: { label: string; href: string };
  /** CSS class name */
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

export function DrillDownPanel({
  open,
  onClose,
  title,
  subtitle,
  breadcrumbs,
  children,
  width = "md",
  position = "right",
  overlay = true,
  actions,
  footer,
  externalLink,
  className,
}: DrillDownPanelProps) {
  // Lock body scroll when open
  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (open) {
      window.addEventListener("keydown", handleEscape);
    }
    return () => window.removeEventListener("keydown", handleEscape);
  }, [open, onClose]);

  const widthClasses = {
    sm: "w-full max-w-sm",
    md: "w-full max-w-lg",
    lg: "w-full max-w-2xl",
    xl: "w-full max-w-4xl",
    full: "w-full",
  };

  const positionClasses = {
    right: "right-0",
    left: "left-0",
  };

  const slideClasses = {
    right: open ? "translate-x-0" : "translate-x-full",
    left: open ? "translate-x-0" : "-translate-x-full",
  };

  if (!open) return null;

  return (
    <>
      {/* Overlay */}
      {overlay && (
        <div
          className={cn(
            "fixed inset-0 z-40 bg-black/50 transition-opacity",
            open ? "opacity-100" : "opacity-0 pointer-events-none"
          )}
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Panel */}
      <div
        className={cn(
          "fixed inset-y-0 z-50 flex flex-col bg-white shadow-xl",
          "transition-transform duration-300 ease-in-out",
          widthClasses[width],
          positionClasses[position],
          slideClasses[position],
          className
        )}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? "panel-title" : undefined}
      >
        {/* Header */}
        <div className="flex-shrink-0 border-b border-gray-200">
          {/* Breadcrumbs */}
          {breadcrumbs && breadcrumbs.length > 0 && (
            <div className="flex items-center gap-1 px-4 py-2 text-sm text-gray-500 border-b border-gray-100">
              {breadcrumbs.map((crumb, index) => (
                <span key={index} className="flex items-center gap-1">
                  {index > 0 && <span>/</span>}
                  {crumb.onClick ? (
                    <button
                      onClick={crumb.onClick}
                      className="hover:text-gray-900 hover:underline"
                    >
                      {crumb.label}
                    </button>
                  ) : (
                    <span className="text-gray-900 font-medium">{crumb.label}</span>
                  )}
                </span>
              ))}
            </div>
          )}

          {/* Title Bar */}
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-3">
              <button
                onClick={onClose}
                className="p-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100"
                aria-label="Close panel"
              >
                {position === "right" ? (
                  <ChevronLeft className="h-5 w-5" />
                ) : (
                  <X className="h-5 w-5" />
                )}
              </button>
              <div>
                {title && (
                  <h2 id="panel-title" className="text-lg font-semibold text-gray-900">
                    {title}
                  </h2>
                )}
                {subtitle && (
                  <p className="text-sm text-gray-500">{subtitle}</p>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2">
              {externalLink && (
                <a
                  href={externalLink.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
                >
                  {externalLink.label}
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}
              {actions}
              <button
                onClick={onClose}
                className="p-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100"
                aria-label="Close panel"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">{children}</div>

        {/* Footer */}
        {footer && (
          <div className="flex-shrink-0 border-t border-gray-200 px-4 py-3">
            {footer}
          </div>
        )}
      </div>
    </>
  );
}

export default DrillDownPanel;
