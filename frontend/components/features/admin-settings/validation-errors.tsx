"use client";

import { AlertCircle, AlertTriangle, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ValidationErrorsProps {
  errors: Record<string, string>;
  warnings?: Record<string, string>;
  onDismiss?: () => void;
  className?: string;
}

export function ValidationErrors({
  errors,
  warnings = {},
  onDismiss,
  className,
}: ValidationErrorsProps) {
  const hasErrors = Object.keys(errors).length > 0;
  const hasWarnings = Object.keys(warnings).length > 0;

  if (!hasErrors && !hasWarnings) {
    return null;
  }

  return (
    <div className={cn("space-y-3", className)}>
      {hasErrors && (
        <div className="card p-4 border-danger/50 bg-danger-subtle">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-danger flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-medium text-danger mb-2">
                  Validation Errors ({Object.keys(errors).length})
                </h4>
                <ul className="space-y-1">
                  {Object.entries(errors).map(([field, message]) => (
                    <li key={field} className="text-sm text-danger/90">
                      <span className="font-medium">{field}:</span> {message}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            {onDismiss && (
              <button
                onClick={onDismiss}
                className="p-1 rounded hover:bg-danger/20 transition-colors"
              >
                <X className="w-4 h-4 text-danger" />
              </button>
            )}
          </div>
        </div>
      )}

      {hasWarnings && (
        <div className="card p-4 border-warning/50 bg-warning-subtle">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-medium text-warning mb-2">
                Warnings ({Object.keys(warnings).length})
              </h4>
              <ul className="space-y-1">
                {Object.entries(warnings).map(([field, message]) => (
                  <li key={field} className="text-sm text-warning/90">
                    <span className="font-medium">{field}:</span> {message}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
