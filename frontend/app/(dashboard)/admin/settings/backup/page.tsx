"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ChevronLeft,
  Database,
  Plus,
  RotateCcw,
  Trash2,
  Calendar,
  User,
  AlertCircle,
  CheckCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useSettingsHealth, useRestoreBackup } from "@/lib/hooks/api/use-admin-settings";
import { getCategoryConfig } from "@/lib/config/admin-settings";
import { BackupModal } from "@/components/features/admin-settings/backup-modal";
import type { SettingsCategory } from "@/lib/api/admin-settings";

// Mock backup data - in real app this would come from API
interface Backup {
  id: string;
  name: string;
  description: string | null;
  createdAt: string;
  createdBy: string;
  categories: SettingsCategory[];
}

export default function BackupPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [restoringId, setRestoringId] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const { data: health, refetch } = useSettingsHealth();
  const restoreMutation = useRestoreBackup();

  // Mock data - replace with actual API call
  const backups: Backup[] = [];

  const handleRestore = async (backupId: string) => {
    if (!confirm("Are you sure you want to restore this backup? This will overwrite current settings.")) {
      return;
    }

    setRestoringId(backupId);
    try {
      await restoreMutation.mutateAsync(backupId);
      setSuccessMessage("Backup restored successfully");
      setTimeout(() => setSuccessMessage(null), 5000);
    } finally {
      setRestoringId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="page-header border-0 pb-0 mb-0">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-4">
            <Link
              href="/admin/settings"
              className="text-sm text-text-muted hover:text-accent transition-colors flex items-center gap-1"
            >
              <ChevronLeft className="w-4 h-4" />
              System Settings
            </Link>
            <span className="text-text-muted">/</span>
            <span className="text-sm text-text-primary">Backups</span>
          </div>

          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-accent-subtle">
              <Database className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h1 className="page-title">Settings Backups</h1>
              <p className="page-description">
                Create and restore configuration backups
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="btn btn--primary"
        >
          <Plus className="w-4 h-4" />
          Create Backup
        </button>
      </div>

      {/* Stats */}
      {health && (
        <div className="card p-4 bg-surface-overlay/50">
          <div className="flex items-center gap-6">
            <div>
              <p className="text-sm text-text-muted">Total Backups</p>
              <p className="text-2xl font-semibold text-text-primary">
                {health.backupsCount}
              </p>
            </div>
            <div className="h-10 w-px bg-border" />
            <div>
              <p className="text-sm text-text-muted">Categories Available</p>
              <p className="text-2xl font-semibold text-text-primary">
                {health.categoriesAvailable}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Success Message */}
      {successMessage && (
        <div className="card p-4 border-success/50 bg-success-subtle">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-success" />
            <span className="text-sm font-medium text-success">
              {successMessage}
            </span>
          </div>
        </div>
      )}

      {/* Backups List */}
      {backups.length === 0 ? (
        <div className="card p-12 text-center">
          <Database className="w-12 h-12 text-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-medium text-text-primary mb-2">
            No backups yet
          </h3>
          <p className="text-text-muted mb-6 max-w-md mx-auto">
            Create your first backup to save a snapshot of your current configuration.
            Backups can be restored later if needed.
          </p>
          <button
            onClick={() => setIsModalOpen(true)}
            className="btn btn--primary"
          >
            <Plus className="w-4 h-4" />
            Create Your First Backup
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {backups.map((backup) => (
            <div key={backup.id} className="card p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-text-primary truncate">
                    {backup.name}
                  </h3>
                  {backup.description && (
                    <p className="text-sm text-text-muted mt-1">
                      {backup.description}
                    </p>
                  )}

                  <div className="flex items-center gap-4 mt-3 text-sm text-text-muted">
                    <span className="flex items-center gap-1.5">
                      <Calendar className="w-4 h-4" />
                      {new Date(backup.createdAt).toLocaleString()}
                    </span>
                    <span className="flex items-center gap-1.5">
                      <User className="w-4 h-4" />
                      {backup.createdBy}
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {backup.categories.map((cat) => {
                      const config = getCategoryConfig(cat);
                      return (
                        <span
                          key={cat}
                          className="text-2xs px-2 py-0.5 rounded-full bg-surface-overlay text-text-muted"
                        >
                          {config.label}
                        </span>
                      );
                    })}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleRestore(backup.id)}
                    disabled={restoringId === backup.id}
                    className={cn(
                      "btn btn--secondary btn--sm",
                      restoringId === backup.id && "opacity-50 cursor-not-allowed"
                    )}
                  >
                    {restoringId === backup.id ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current" />
                    ) : (
                      <RotateCcw className="w-4 h-4" />
                    )}
                    Restore
                  </button>
                  <button
                    className="btn btn--ghost btn--sm text-danger hover:bg-danger-subtle"
                    title="Delete backup"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Backup Modal */}
      <BackupModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={() => refetch()}
      />
    </div>
  );
}
