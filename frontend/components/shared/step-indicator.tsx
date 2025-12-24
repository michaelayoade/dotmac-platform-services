"use client";

import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export interface Step {
  id: string;
  title: string;
  description?: string;
}

interface StepIndicatorProps {
  steps: Step[];
  currentStep: number;
  className?: string;
  variant?: "horizontal" | "vertical";
}

export function StepIndicator({
  steps,
  currentStep,
  className,
  variant = "horizontal",
}: StepIndicatorProps) {
  if (variant === "vertical") {
    return (
      <div className={cn("space-y-4", className)}>
        {steps.map((step, index) => {
          const isCompleted = index < currentStep;
          const isCurrent = index === currentStep;

          return (
            <div key={step.id} className="flex gap-4">
              {/* Step indicator */}
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    "w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-all duration-300",
                    isCompleted && "bg-accent text-white",
                    isCurrent && "bg-accent/20 text-accent border-2 border-accent",
                    !isCompleted && !isCurrent && "bg-surface-overlay text-text-muted border border-border"
                  )}
                >
                  {isCompleted ? (
                    <Check className="w-4 h-4" />
                  ) : (
                    index + 1
                  )}
                </div>
                {index < steps.length - 1 && (
                  <div
                    className={cn(
                      "w-0.5 h-12 mt-2 transition-all duration-300",
                      isCompleted ? "bg-accent" : "bg-border"
                    )}
                  />
                )}
              </div>

              {/* Step content */}
              <div className="pt-1">
                <p
                  className={cn(
                    "font-medium transition-colors",
                    isCurrent ? "text-text-primary" : "text-text-muted"
                  )}
                >
                  {step.title}
                </p>
                {step.description && (
                  <p className="text-sm text-text-muted mt-0.5">
                    {step.description}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <div className={cn("flex items-center justify-center", className)}>
      {steps.map((step, index) => {
        const isCompleted = index < currentStep;
        const isCurrent = index === currentStep;

        return (
          <div key={step.id} className="flex items-center">
            {/* Step */}
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  "w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold transition-all duration-300",
                  isCompleted && "bg-accent text-white shadow-glow-sm",
                  isCurrent && "bg-accent/20 text-accent border-2 border-accent",
                  !isCompleted && !isCurrent && "bg-surface-overlay text-text-muted border border-border"
                )}
              >
                {isCompleted ? (
                  <Check className="w-5 h-5" />
                ) : (
                  index + 1
                )}
              </div>
              <span
                className={cn(
                  "mt-2 text-xs font-medium transition-colors whitespace-nowrap",
                  isCurrent ? "text-text-primary" : "text-text-muted"
                )}
              >
                {step.title}
              </span>
            </div>

            {/* Connector */}
            {index < steps.length - 1 && (
              <div
                className={cn(
                  "w-16 h-0.5 mx-2 transition-all duration-300",
                  isCompleted ? "bg-accent" : "bg-border"
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
