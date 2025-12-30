"use client";

import { useState } from "react";
import { X, Download, Upload, Check, AlertCircle, FileJson, FileCode, FileText } from "lucide-react";
import { cn } from "@/lib/utils";
import { useExportSettings, useImportSettings } from "@/lib/hooks/api/use-admin-settings";
import { categoryOrder, getCategoryConfig } from "@/lib/config/admin-settings";
import type { SettingsCategory } from "@/lib/api/admin-settings";

type Mode = "export" | "import";
type ExportFormat = "json" | "yaml" | "env";

interface ImportExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialMode?: Mode;
  onSuccess?: () => void;
}

export function ImportExportModal({
  isOpen,
  onClose,
  initialMode = "export",
  onSuccess,
}: ImportExportModalProps) {
  const [mode, setMode] = useState<Mode>(initialMode);
  const [format, setFormat] = useState<ExportFormat>("json");
  const [selectedCategories, setSelectedCategories] = useState<SettingsCategory[]>([]);
  const [selectAll, setSelectAll] = useState(true);
  const [includeSensitive, setIncludeSensitive] = useState(false);
  const [importData, setImportData] = useState("");
  const [validateOnly, setValidateOnly] = useState(true);
  const [validationResult, setValidationResult] = useState<{
    imported: string[];
    errors: Record<string, unknown>;
  } | null>(null);

  const exportMutation = useExportSettings();
  const importMutation = useImportSettings();

  const handleToggleCategory = (category: SettingsCategory) => {
    setSelectedCategories((prev) =>
      prev.includes(category)
        ? prev.filter((c) => c !== category)
        : [...prev, category]
    );
    setSelectAll(false);
  };

  const handleToggleAll = () => {
    if (selectAll) {
      setSelectedCategories([]);
      setSelectAll(false);
    } else {
      setSelectedCategories([...categoryOrder]);
      setSelectAll(true);
    }
  };

  const handleExport = async () => {
    try {
      const result = await exportMutation.mutateAsync({
        categories: selectAll ? undefined : selectedCategories,
        includeSensitive,
        format,
      });

      // Download the exported data
      const dataStr = typeof result.data === "string"
        ? result.data
        : JSON.stringify(result.data, null, 2);

      const blob = new Blob([dataStr], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `settings-export-${new Date().toISOString().split("T")[0]}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      onSuccess?.();
      onClose();
    } catch {
      // Error handled by mutation hook
    }
  };

  const handleImport = async () => {
    try {
      const data = JSON.parse(importData);
      const result = await importMutation.mutateAsync({
        data,
        categories: selectAll ? undefined : selectedCategories,
        validateOnly,
      });

      setValidationResult(result);

      if (!validateOnly && result.imported.length > 0) {
        onSuccess?.();
        // Don't close - show success message
      }
    } catch (e) {
      if (e instanceof SyntaxError) {
        setValidationResult({
          imported: [],
          errors: { _parse: "Invalid JSON format" },
        });
      }
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      setImportData(event.target?.result as string);
      setValidationResult(null);
    };
    reader.readAsText(file);
  };

  const resetState = () => {
    setImportData("");
    setValidationResult(null);
    setValidateOnly(true);
  };

  if (!isOpen) return null;

  const formatIcons: Record<ExportFormat, typeof FileJson> = {
    json: FileJson,
    yaml: FileCode,
    env: FileText,
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-surface-base border border-border rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-accent-subtle">
              {mode === "export" ? (
                <Download className="w-5 h-5 text-accent" />
              ) : (
                <Upload className="w-5 h-5 text-accent" />
              )}
            </div>
            <h2 className="text-lg font-semibold text-text-primary">
              {mode === "export" ? "Export Settings" : "Import Settings"}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded hover:bg-surface-overlay transition-colors"
          >
            <X className="w-5 h-5 text-text-muted" />
          </button>
        </div>

        {/* Mode Toggle */}
        <div className="p-4 border-b border-border">
          <div className="flex rounded-lg bg-surface-overlay p-1">
            <button
              onClick={() => { setMode("export"); resetState(); }}
              className={cn(
                "flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-md text-sm font-medium transition-colors",
                mode === "export"
                  ? "bg-surface-base text-text-primary shadow-sm"
                  : "text-text-muted hover:text-text-primary"
              )}
            >
              <Download className="w-4 h-4" />
              Export
            </button>
            <button
              onClick={() => { setMode("import"); resetState(); }}
              className={cn(
                "flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-md text-sm font-medium transition-colors",
                mode === "import"
                  ? "bg-surface-base text-text-primary shadow-sm"
                  : "text-text-muted hover:text-text-primary"
              )}
            >
              <Upload className="w-4 h-4" />
              Import
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4 overflow-y-auto max-h-[calc(90vh-220px)]">
          {mode === "export" ? (
            <>
              {/* Format Selection */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Export Format
                </label>
                <div className="flex gap-2">
                  {(["json", "yaml", "env"] as ExportFormat[]).map((f) => {
                    const Icon = formatIcons[f];
                    return (
                      <button
                        key={f}
                        onClick={() => setFormat(f)}
                        className={cn(
                          "flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg border text-sm font-medium transition-colors",
                          format === f
                            ? "border-accent bg-accent-subtle text-accent"
                            : "border-border hover:border-text-muted"
                        )}
                      >
                        <Icon className="w-4 h-4" />
                        {f.toUpperCase()}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Include Sensitive */}
              <label className="flex items-center gap-3 p-3 rounded-lg border border-border hover:bg-surface-overlay transition-colors cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeSensitive}
                  onChange={(e) => setIncludeSensitive(e.target.checked)}
                  className="sr-only peer"
                />
                <div className={cn(
                  "w-5 h-5 rounded border-2 flex items-center justify-center transition-colors",
                  includeSensitive ? "bg-accent border-accent" : "border-text-muted"
                )}>
                  {includeSensitive && <Check className="w-3 h-3 text-white" />}
                </div>
                <div>
                  <p className="text-sm font-medium text-text-primary">
                    Include sensitive values
                  </p>
                  <p className="text-xs text-text-muted">
                    Export actual values for API keys, passwords, etc.
                  </p>
                </div>
              </label>

              {/* Categories */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-text-primary">
                    Categories
                  </label>
                  <button
                    type="button"
                    onClick={handleToggleAll}
                    className="text-sm text-accent hover:underline"
                  >
                    {selectAll ? "Deselect all" : "Select all"}
                  </button>
                </div>
                <div className="border border-border rounded-lg divide-y divide-border max-h-40 overflow-y-auto">
                  {categoryOrder.map((category) => {
                    const config = getCategoryConfig(category);
                    const Icon = config.icon;
                    const isSelected = selectAll || selectedCategories.includes(category);

                    return (
                      <label
                        key={category}
                        className={cn(
                          "flex items-center gap-3 p-2 cursor-pointer hover:bg-surface-overlay transition-colors",
                          isSelected && "bg-accent-subtle/30"
                        )}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => handleToggleCategory(category)}
                          className="sr-only"
                        />
                        <div className={cn(
                          "w-4 h-4 rounded border flex items-center justify-center transition-colors",
                          isSelected ? "bg-accent border-accent" : "border-text-muted"
                        )}>
                          {isSelected && <Check className="w-2.5 h-2.5 text-white" />}
                        </div>
                        <Icon className={cn("w-3.5 h-3.5", config.color)} />
                        <span className="text-sm text-text-primary">{config.label}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            </>
          ) : (
            <>
              {/* File Upload */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Upload Settings File
                </label>
                <input
                  type="file"
                  accept=".json,.yaml,.yml"
                  onChange={handleFileUpload}
                  className="block w-full text-sm text-text-muted
                    file:mr-4 file:py-2 file:px-4
                    file:rounded-lg file:border-0
                    file:text-sm file:font-medium
                    file:bg-accent file:text-white
                    hover:file:bg-accent/90
                    file:cursor-pointer"
                />
              </div>

              {/* Or paste JSON */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Or paste JSON data
                </label>
                <textarea
                  value={importData}
                  onChange={(e) => {
                    setImportData(e.target.value);
                    setValidationResult(null);
                  }}
                  placeholder='{"email": {"smtp_host": "smtp.example.com", ...}}'
                  rows={6}
                  className="input w-full font-mono text-sm resize-none"
                />
              </div>

              {/* Validate Only */}
              <label className="flex items-center gap-3 p-3 rounded-lg border border-border hover:bg-surface-overlay transition-colors cursor-pointer">
                <input
                  type="checkbox"
                  checked={validateOnly}
                  onChange={(e) => setValidateOnly(e.target.checked)}
                  className="sr-only peer"
                />
                <div className={cn(
                  "w-5 h-5 rounded border-2 flex items-center justify-center transition-colors",
                  validateOnly ? "bg-accent border-accent" : "border-text-muted"
                )}>
                  {validateOnly && <Check className="w-3 h-3 text-white" />}
                </div>
                <div>
                  <p className="text-sm font-medium text-text-primary">
                    Validate only (dry run)
                  </p>
                  <p className="text-xs text-text-muted">
                    Check for errors without applying changes
                  </p>
                </div>
              </label>

              {/* Validation Result */}
              {validationResult && (
                <div className={cn(
                  "p-4 rounded-lg border",
                  Object.keys(validationResult.errors).length > 0
                    ? "border-danger/50 bg-danger-subtle"
                    : "border-success/50 bg-success-subtle"
                )}>
                  {Object.keys(validationResult.errors).length > 0 ? (
                    <div className="flex items-start gap-3">
                      <AlertCircle className="w-5 h-5 text-danger flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-danger mb-2">
                          Validation failed
                        </p>
                        <ul className="text-sm text-danger/80 space-y-1">
                          {Object.entries(validationResult.errors).map(([key, val]) => (
                            <li key={key}>
                              <strong>{key}:</strong> {String(val)}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-start gap-3">
                      <Check className="w-5 h-5 text-success flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-success">
                          {validateOnly ? "Validation passed" : "Import successful"}
                        </p>
                        <p className="text-sm text-success/80">
                          {validationResult.imported.length} categories{" "}
                          {validateOnly ? "ready to import" : "imported"}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-4 border-t border-border bg-surface-overlay/30">
          <button type="button" onClick={onClose} className="btn btn--secondary">
            Cancel
          </button>
          {mode === "export" ? (
            <button
              onClick={handleExport}
              disabled={exportMutation.isPending || (!selectAll && selectedCategories.length === 0)}
              className={cn(
                "btn btn--primary",
                (exportMutation.isPending || (!selectAll && selectedCategories.length === 0)) &&
                  "opacity-50 cursor-not-allowed"
              )}
            >
              {exportMutation.isPending ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                  Exporting...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  Export
                </>
              )}
            </button>
          ) : (
            <button
              onClick={handleImport}
              disabled={importMutation.isPending || !importData}
              className={cn(
                "btn btn--primary",
                (importMutation.isPending || !importData) && "opacity-50 cursor-not-allowed"
              )}
            >
              {importMutation.isPending ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                  {validateOnly ? "Validating..." : "Importing..."}
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  {validateOnly ? "Validate" : "Import"}
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
