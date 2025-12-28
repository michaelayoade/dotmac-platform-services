"use client";

import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { X, Loader2 } from "lucide-react";

import { cn } from "@/lib/utils";
import { useCreateReferral, useUpdateReferral } from "@/lib/hooks/api/use-partner-portal";
import type { Referral } from "@/types/partner-portal";

const referralSchema = z.object({
  companyName: z.string().min(2, "Company name is required"),
  contactName: z.string().min(2, "Contact name is required"),
  contactEmail: z.string().email("Valid email is required"),
  contactPhone: z.string().optional(),
  estimatedValue: z.coerce.number().min(0).optional(),
  notes: z.string().optional(),
});

type ReferralFormData = z.infer<typeof referralSchema>;

interface ReferralFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
  editReferral?: Referral | null;
}

export function ReferralForm({ isOpen, onClose, onSuccess, editReferral }: ReferralFormProps) {
  const createReferral = useCreateReferral();
  const updateReferral = useUpdateReferral();
  const [submitError, setSubmitError] = useState<string | null>(null);

  const isEditMode = !!editReferral;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ReferralFormData>({
    resolver: zodResolver(referralSchema),
    defaultValues: {
      companyName: "",
      contactName: "",
      contactEmail: "",
      contactPhone: "",
      estimatedValue: undefined,
      notes: "",
    },
  });

  // Populate form when editing
  useEffect(() => {
    if (editReferral) {
      reset({
        companyName: editReferral.companyName,
        contactName: editReferral.contactName,
        contactEmail: editReferral.contactEmail,
        contactPhone: editReferral.contactPhone || "",
        estimatedValue: editReferral.estimatedValue || undefined,
        notes: editReferral.notes || "",
      });
    } else {
      reset({
        companyName: "",
        contactName: "",
        contactEmail: "",
        contactPhone: "",
        estimatedValue: undefined,
        notes: "",
      });
    }
  }, [editReferral, reset]);

  const onSubmit = async (data: ReferralFormData) => {
    setSubmitError(null);
    try {
      if (isEditMode && editReferral) {
        await updateReferral.mutateAsync({ id: editReferral.id, data });
      } else {
        await createReferral.mutateAsync(data);
      }
      reset();
      onSuccess?.();
      onClose();
    } catch (error) {
      const message = error instanceof Error ? error.message : `Failed to ${isEditMode ? "update" : "create"} referral.`;
      setSubmitError(message);
    }
  };

  const handleClose = () => {
    reset();
    setSubmitError(null);
    onClose();
  };

  if (!isOpen) return null;

  const isPending = createReferral.isPending || updateReferral.isPending;
  const hasError = createReferral.isError || updateReferral.isError;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-overlay/50 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-lg mx-4 bg-surface-elevated rounded-xl border border-border shadow-xl animate-scale-in">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div>
            <h2 className="text-lg font-semibold text-text-primary">
              {isEditMode ? "Edit Referral" : "Submit New Referral"}
            </h2>
            <p className="text-sm text-text-muted mt-1">
              {isEditMode ? "Update referral details" : "Add a potential tenant referral"}
            </p>
          </div>
          <button
            onClick={handleClose}
            className="p-2 rounded-md text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
          {submitError && (
            <div className="p-3 rounded-md bg-status-error/10 text-status-error text-sm">
              {submitError}
            </div>
          )}
          {/* Company Name */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">
              Company Name <span className="text-status-error">*</span>
            </label>
            <input
              {...register("companyName")}
              type="text"
              placeholder="Acme Corporation"
              className={cn(
                "w-full px-3 py-2 rounded-md border bg-surface text-text-primary placeholder:text-text-muted",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-inset",
                errors.companyName
                  ? "border-status-error"
                  : "border-border"
              )}
            />
            {errors.companyName && (
              <p className="text-xs text-status-error">
                {errors.companyName.message}
              </p>
            )}
          </div>

          {/* Contact Name */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">
              Contact Name <span className="text-status-error">*</span>
            </label>
            <input
              {...register("contactName")}
              type="text"
              placeholder="John Smith"
              className={cn(
                "w-full px-3 py-2 rounded-md border bg-surface text-text-primary placeholder:text-text-muted",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-inset",
                errors.contactName
                  ? "border-status-error"
                  : "border-border"
              )}
            />
            {errors.contactName && (
              <p className="text-xs text-status-error">
                {errors.contactName.message}
              </p>
            )}
          </div>

          {/* Contact Email & Phone */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-text-secondary">
                Email <span className="text-status-error">*</span>
              </label>
              <input
                {...register("contactEmail")}
                type="email"
                placeholder="john@acme.com"
                className={cn(
                  "w-full px-3 py-2 rounded-md border bg-surface text-text-primary placeholder:text-text-muted",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-inset",
                  errors.contactEmail
                    ? "border-status-error"
                    : "border-border"
                )}
              />
              {errors.contactEmail && (
                <p className="text-xs text-status-error">
                  {errors.contactEmail.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-text-secondary">
                Phone
              </label>
              <input
                {...register("contactPhone")}
                type="tel"
                placeholder="+1 (555) 000-0000"
                className="w-full px-3 py-2 rounded-md border border-border bg-surface text-text-primary placeholder:text-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-inset"
              />
            </div>
          </div>

          {/* Estimated Value */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">
              Estimated Monthly Value
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">
                $
              </span>
              <input
                {...register("estimatedValue")}
                type="number"
                placeholder="0"
                className="w-full pl-7 pr-3 py-2 rounded-md border border-border bg-surface text-text-primary placeholder:text-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-inset"
              />
            </div>
          </div>

          {/* Notes */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">
              Notes
            </label>
            <textarea
              {...register("notes")}
              rows={3}
              placeholder="Any additional context about this referral..."
              className="w-full px-3 py-2 rounded-md border border-border bg-surface text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent resize-none"
            />
          </div>

          {/* Error Message */}
          {hasError && (
            <div className="p-3 rounded-lg bg-status-error/15 border border-status-error/20 text-status-error text-sm">
              Failed to {isEditMode ? "update" : "submit"} referral. Please try again.
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 rounded-md text-text-secondary hover:text-text-primary hover:bg-surface-overlay transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || isPending}
              className="px-4 py-2 rounded-md bg-accent text-text-inverse hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors inline-flex items-center gap-2"
            >
              {(isSubmitting || isPending) && (
                <Loader2 className="w-4 h-4 animate-spin" />
              )}
              {isEditMode ? "Update Referral" : "Submit Referral"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
