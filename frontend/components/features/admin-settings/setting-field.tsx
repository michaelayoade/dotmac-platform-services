"use client";

import { useState } from "react";
import { Info, AlertTriangle, Lock } from "lucide-react";
import { cn } from "@/lib/utils";
import { getFieldInputType } from "@/lib/config/admin-settings";
import { SensitiveField } from "./sensitive-field";
import { RestartWarningBadge } from "./restart-warning-badge";
import type { SettingField as SettingFieldType } from "@/lib/api/admin-settings";

interface SettingFieldProps {
  field: SettingFieldType;
  value: unknown;
  onChange: (name: string, value: unknown) => void;
  error?: string;
  modified?: boolean;
  disabled?: boolean;
  restartRequired?: boolean;
}

export function SettingField({
  field,
  value,
  onChange,
  error,
  modified = false,
  disabled = false,
  restartRequired = false,
}: SettingFieldProps) {
  const inputType = getFieldInputType(field.type, field.sensitive);
  const [jsonError, setJsonError] = useState<string | null>(null);

  const handleChange = (newValue: unknown) => {
    onChange(field.name, newValue);
  };

  const renderInput = () => {
    // Sensitive field (password, API key, etc.)
    if (field.sensitive) {
      return (
        <SensitiveField
          name={field.name}
          value={String(value ?? "")}
          onChange={(v) => handleChange(v)}
          disabled={disabled}
          placeholder={field.default ? `Default: ${field.default}` : undefined}
        />
      );
    }

    // Boolean toggle
    if (inputType === "toggle") {
      return (
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={Boolean(value)}
            onChange={(e) => handleChange(e.target.checked)}
            disabled={disabled}
            className="sr-only peer"
          />
          <div className={cn(
            "w-11 h-6 bg-surface-overlay rounded-full peer",
            "peer-checked:bg-accent peer-checked:after:translate-x-full",
            "after:content-[''] after:absolute after:top-0.5 after:left-[2px]",
            "after:bg-white after:rounded-full after:h-5 after:w-5",
            "after:transition-all peer-disabled:opacity-50",
            disabled && "cursor-not-allowed"
          )} />
        </label>
      );
    }

    // JSON/Dict/List field
    if (inputType === "json") {
      const jsonValue = typeof value === "string" ? value : JSON.stringify(value, null, 2);
      return (
        <div className="space-y-1">
          <textarea
            name={field.name}
            value={jsonValue}
            onChange={(e) => {
              const newValue = e.target.value;
              try {
                JSON.parse(newValue);
                setJsonError(null);
                handleChange(JSON.parse(newValue));
              } catch {
                setJsonError("Invalid JSON");
                handleChange(newValue);
              }
            }}
            disabled={disabled}
            rows={4}
            className={cn(
              "input font-mono text-sm resize-y min-h-[100px]",
              jsonError && "border-danger",
              disabled && "opacity-50 cursor-not-allowed"
            )}
          />
          {jsonError && (
            <p className="text-xs text-danger">{jsonError}</p>
          )}
        </div>
      );
    }

    // Number field
    if (inputType === "number") {
      return (
        <input
          type="number"
          name={field.name}
          value={value as number ?? ""}
          onChange={(e) => handleChange(e.target.value === "" ? null : Number(e.target.value))}
          disabled={disabled}
          placeholder={field.default !== null ? `Default: ${field.default}` : undefined}
          className={cn(
            "input",
            error && "border-danger",
            disabled && "opacity-50 cursor-not-allowed"
          )}
        />
      );
    }

    // URL field
    if (inputType === "url") {
      return (
        <input
          type="url"
          name={field.name}
          value={String(value ?? "")}
          onChange={(e) => handleChange(e.target.value)}
          disabled={disabled}
          placeholder={field.default ? `Default: ${field.default}` : "https://..."}
          className={cn(
            "input",
            error && "border-danger",
            disabled && "opacity-50 cursor-not-allowed"
          )}
        />
      );
    }

    // Email field
    if (inputType === "email") {
      return (
        <input
          type="email"
          name={field.name}
          value={String(value ?? "")}
          onChange={(e) => handleChange(e.target.value)}
          disabled={disabled}
          placeholder={field.default ? `Default: ${field.default}` : "email@example.com"}
          className={cn(
            "input",
            error && "border-danger",
            disabled && "opacity-50 cursor-not-allowed"
          )}
        />
      );
    }

    // Default text field
    return (
      <input
        type="text"
        name={field.name}
        value={String(value ?? "")}
        onChange={(e) => handleChange(e.target.value)}
        disabled={disabled}
        placeholder={field.default ? `Default: ${field.default}` : undefined}
        className={cn(
          "input",
          error && "border-danger",
          disabled && "opacity-50 cursor-not-allowed"
        )}
      />
    );
  };

  return (
    <div className={cn(
      "py-4 border-b border-border last:border-b-0",
      modified && "bg-accent-subtle/30 -mx-4 px-4"
    )}>
      {/* Label Row */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <label
            htmlFor={field.name}
            className="text-sm font-medium text-text-primary"
          >
            {field.name}
          </label>
          {field.required && (
            <span className="text-danger text-xs">*</span>
          )}
          {field.sensitive && (
            <span title="Sensitive field">
              <Lock className="w-3.5 h-3.5 text-warning" />
            </span>
          )}
          {restartRequired && <RestartWarningBadge />}
          {modified && (
            <span className="text-2xs px-1.5 py-0.5 rounded bg-accent text-white">
              Modified
            </span>
          )}
        </div>
        <span className="text-2xs text-text-muted bg-surface-overlay px-1.5 py-0.5 rounded">
          {field.type}
        </span>
      </div>

      {/* Description */}
      {field.description && (
        <p className="text-sm text-text-muted mb-3 flex items-start gap-1.5">
          <Info className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
          {field.description}
        </p>
      )}

      {/* Input */}
      <div className="max-w-xl">
        {renderInput()}
      </div>

      {/* Error */}
      {error && (
        <p className="text-sm text-danger mt-2 flex items-center gap-1.5">
          <AlertTriangle className="w-4 h-4" />
          {error}
        </p>
      )}
    </div>
  );
}
