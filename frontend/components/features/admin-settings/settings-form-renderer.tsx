"use client";

import { useState, useCallback, useMemo } from "react";
import { Save, RotateCcw, CheckCircle, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import { SettingField } from "./setting-field";
import { ValidationErrors } from "./validation-errors";
import { useUpdateSettings, useValidateSettings } from "@/lib/hooks/api/use-admin-settings";
import type { SettingsResponse, SettingsCategory } from "@/lib/api/admin-settings";

interface SettingsFormRendererProps {
  settings: SettingsResponse;
  onSaveSuccess?: () => void;
}

export function SettingsFormRenderer({
  settings,
  onSaveSuccess,
}: SettingsFormRendererProps) {
  // Initial values from API
  const initialValues = useMemo(() => {
    const values: Record<string, unknown> = {};
    settings.fields.forEach((field) => {
      values[field.name] = field.value;
    });
    return values;
  }, [settings.fields]);

  const [formValues, setFormValues] = useState<Record<string, unknown>>(initialValues);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [validationWarnings, setValidationWarnings] = useState<Record<string, string>>({});
  const [showSuccess, setShowSuccess] = useState(false);

  const updateMutation = useUpdateSettings();
  const validateMutation = useValidateSettings();

  // Track which fields have been modified
  const modifiedFields = useMemo(() => {
    const modified: Set<string> = new Set();
    Object.entries(formValues).forEach(([key, value]) => {
      if (JSON.stringify(value) !== JSON.stringify(initialValues[key])) {
        modified.add(key);
      }
    });
    return modified;
  }, [formValues, initialValues]);

  const hasChanges = modifiedFields.size > 0;

  // Check if any modified field requires restart
  const restartRequired = useMemo(() => {
    // This would ideally come from the field metadata
    // For now, we'll check if the category has restart_required flag
    return settings.fields.some(
      (f) => modifiedFields.has(f.name) && f.validationRules?.restartRequired
    );
  }, [settings.fields, modifiedFields]);

  const handleFieldChange = useCallback((name: string, value: unknown) => {
    setFormValues((prev) => ({ ...prev, [name]: value }));
    // Clear any validation error for this field
    setValidationErrors((prev) => {
      const next = { ...prev };
      delete next[name];
      return next;
    });
  }, []);

  const handleReset = useCallback(() => {
    setFormValues(initialValues);
    setValidationErrors({});
    setValidationWarnings({});
  }, [initialValues]);

  const handleValidate = useCallback(async () => {
    const updates: Record<string, unknown> = {};
    modifiedFields.forEach((field) => {
      updates[field] = formValues[field];
    });

    if (Object.keys(updates).length === 0) return;

    try {
      const result = await validateMutation.mutateAsync({
        category: settings.category,
        updates,
      });

      setValidationErrors(result.errors);
      setValidationWarnings(result.warnings);

      return result.valid;
    } catch {
      return false;
    }
  }, [settings.category, formValues, modifiedFields, validateMutation]);

  const handleSave = useCallback(async () => {
    // First validate
    const isValid = await handleValidate();
    if (!isValid) return;

    const updates: Record<string, unknown> = {};
    modifiedFields.forEach((field) => {
      updates[field] = formValues[field];
    });

    try {
      await updateMutation.mutateAsync({
        category: settings.category,
        data: {
          updates,
          restartRequired,
        },
      });

      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
      onSaveSuccess?.();
    } catch (error) {
      // Handle error - the mutation hook will handle toast/notification
      console.error("Failed to save settings:", error);
    }
  }, [
    settings.category,
    formValues,
    modifiedFields,
    restartRequired,
    handleValidate,
    updateMutation,
    onSaveSuccess,
  ]);

  return (
    <div className="space-y-6">
      {/* Validation Errors */}
      <ValidationErrors
        errors={validationErrors}
        warnings={validationWarnings}
        onDismiss={() => {
          setValidationErrors({});
          setValidationWarnings({});
        }}
      />

      {/* Success Message */}
      {showSuccess && (
        <div className="card p-4 border-success/50 bg-success-subtle">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-success" />
            <span className="text-sm font-medium text-success">
              Settings saved successfully
            </span>
          </div>
        </div>
      )}

      {/* Restart Warning */}
      {restartRequired && hasChanges && (
        <div className="card p-4 border-warning/50 bg-warning-subtle">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-warning" />
            <span className="text-sm text-warning">
              Some changes require a service restart to take effect
            </span>
          </div>
        </div>
      )}

      {/* Form Fields */}
      <div className="card">
        <div className="p-4 border-b border-border">
          <h3 className="font-medium text-text-primary">
            {settings.displayName}
          </h3>
          {settings.lastUpdated && (
            <p className="text-sm text-text-muted mt-1">
              Last updated: {new Date(settings.lastUpdated).toLocaleString()}
              {settings.updatedBy && ` by ${settings.updatedBy}`}
            </p>
          )}
        </div>

        <div className="p-4">
          {settings.fields.map((field) => (
            <SettingField
              key={field.name}
              field={field}
              value={formValues[field.name]}
              onChange={handleFieldChange}
              error={validationErrors[field.name]}
              modified={modifiedFields.has(field.name)}
              restartRequired={Boolean(field.validationRules?.restartRequired)}
            />
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-text-muted">
          {hasChanges ? (
            <span className="text-warning">
              {modifiedFields.size} field{modifiedFields.size > 1 ? "s" : ""} modified
            </span>
          ) : (
            <span>No changes</span>
          )}
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleReset}
            disabled={!hasChanges}
            className={cn(
              "btn btn--secondary",
              !hasChanges && "opacity-50 cursor-not-allowed"
            )}
          >
            <RotateCcw className="w-4 h-4" />
            Reset
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={!hasChanges || updateMutation.isPending}
            className={cn(
              "btn btn--primary",
              (!hasChanges || updateMutation.isPending) && "opacity-50 cursor-not-allowed"
            )}
          >
            {updateMutation.isPending ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                Save Changes
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
