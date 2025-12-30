"use client";

import { useState } from "react";
import { X, Database, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { useCreateBackup } from "@/lib/hooks/api/use-admin-settings";
import { categoryOrder, getCategoryConfig } from "@/lib/config/admin-settings";
import type { SettingsCategory } from "@/lib/api/admin-settings";

interface BackupModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function BackupModal({ isOpen, onClose, onSuccess }: BackupModalProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [selectedCategories, setSelectedCategories] = useState<SettingsCategory[]>([]);
  const [selectAll, setSelectAll] = useState(true);

  const createBackup = useCreateBackup();

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await createBackup.mutateAsync({
        name,
        description: description || undefined,
        categories: selectAll ? undefined : selectedCategories,
      });
      onSuccess?.();
      onClose();
      // Reset form
      setName("");
      setDescription("");
      setSelectedCategories([]);
      setSelectAll(true);
    } catch {
      // Error handled by mutation hook
    }
  };

  if (!isOpen) return null;

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
              <Database className="w-5 h-5 text-accent" />
            </div>
            <h2 className="text-lg font-semibold text-text-primary">
              Create Backup
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded hover:bg-surface-overlay transition-colors"
          >
            <X className="w-5 h-5 text-text-muted" />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-4 space-y-4 overflow-y-auto max-h-[calc(90vh-140px)]">
          {/* Name */}
          <div>
            <label htmlFor="backup-name" className="block text-sm font-medium text-text-primary mb-1">
              Backup Name <span className="text-danger">*</span>
            </label>
            <input
              id="backup-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Pre-migration backup"
              required
              className="input w-full"
            />
          </div>

          {/* Description */}
          <div>
            <label htmlFor="backup-description" className="block text-sm font-medium text-text-primary mb-1">
              Description
            </label>
            <textarea
              id="backup-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description for this backup"
              rows={2}
              className="input w-full resize-none"
            />
          </div>

          {/* Categories */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-text-primary">
                Categories to backup
              </label>
              <button
                type="button"
                onClick={handleToggleAll}
                className="text-sm text-accent hover:underline"
              >
                {selectAll ? "Deselect all" : "Select all"}
              </button>
            </div>

            <div className="border border-border rounded-lg divide-y divide-border max-h-48 overflow-y-auto">
              {categoryOrder.map((category) => {
                const config = getCategoryConfig(category);
                const Icon = config.icon;
                const isSelected = selectAll || selectedCategories.includes(category);

                return (
                  <label
                    key={category}
                    className={cn(
                      "flex items-center gap-3 p-3 cursor-pointer hover:bg-surface-overlay transition-colors",
                      isSelected && "bg-accent-subtle/30"
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleToggleCategory(category)}
                      className="sr-only"
                    />
                    <div
                      className={cn(
                        "w-5 h-5 rounded border-2 flex items-center justify-center transition-colors",
                        isSelected
                          ? "bg-accent border-accent"
                          : "border-text-muted"
                      )}
                    >
                      {isSelected && <Check className="w-3 h-3 text-white" />}
                    </div>
                    <Icon className={cn("w-4 h-4", config.color)} />
                    <span className="text-sm text-text-primary">{config.label}</span>
                  </label>
                );
              })}
            </div>
          </div>
        </form>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-4 border-t border-border bg-surface-overlay/30">
          <button
            type="button"
            onClick={onClose}
            className="btn btn--secondary"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!name || createBackup.isPending}
            className={cn(
              "btn btn--primary",
              (!name || createBackup.isPending) && "opacity-50 cursor-not-allowed"
            )}
          >
            {createBackup.isPending ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                Creating...
              </>
            ) : (
              <>
                <Database className="w-4 h-4" />
                Create Backup
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
