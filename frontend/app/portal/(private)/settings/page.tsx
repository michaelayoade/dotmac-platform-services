"use client";

import { useEffect, useState, type ChangeEvent } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import Image from "next/image";
import {
  Building2,
  Shield,
  Key,
  Bell,
  Save,
  Loader2,
  Plus,
  Trash2,
  Copy,
  Eye,
  EyeOff,
  AlertTriangle,
  Upload,
  ImageIcon,
  Palette,
} from "lucide-react";

import { PageHeader } from "@/components/shared";
import {
  useTenantSettings,
  useUpdateTenantSettings,
  useApiKeys,
  useCreateApiKey,
  useDeleteApiKey,
  useUploadTenantLogo,
} from "@/lib/hooks/api/use-tenant-portal";
import { useConfirmDialog } from "@/components/shared/confirm-dialog";
import { cn } from "@/lib/utils";

const generalSchema = z.object({
  name: z.string().min(2, "Organization name is required"),
  timezone: z.string(),
  dateFormat: z.string(),
  language: z.string(),
});

type GeneralFormData = z.infer<typeof generalSchema>;

const emptySettings = {
  general: {
    name: "",
    slug: "",
    industry: "",
    timezone: "UTC",
    dateFormat: "YYYY-MM-DD",
    language: "en",
  },
  branding: {
    logoUrl: undefined,
    primaryColor: "",
    accentColor: "",
  },
  security: {
    mfaRequired: false,
    sessionTimeout: 0,
    ipWhitelist: [] as string[],
    allowedDomains: [] as string[],
  },
  features: {
    advancedAnalytics: false,
    customIntegrations: false,
    apiAccess: false,
  },
};

function GeneralSettingsSection() {
  const { data: settings } = useTenantSettings();
  const updateSettings = useUpdateTenantSettings();
  const [isEditing, setIsEditing] = useState(false);

  const currentSettings = settings ?? emptySettings;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<GeneralFormData>({
    resolver: zodResolver(generalSchema),
    defaultValues: {
      name: currentSettings.general.name,
      timezone: currentSettings.general.timezone,
      dateFormat: currentSettings.general.dateFormat,
      language: currentSettings.general.language,
    },
  });

  useEffect(() => {
    if (settings) {
      reset({
        name: settings.general.name,
        timezone: settings.general.timezone,
        dateFormat: settings.general.dateFormat,
        language: settings.general.language,
      });
    }
  }, [settings, reset]);

  const onSubmit = async (data: GeneralFormData) => {
    try {
      await updateSettings.mutateAsync({
        general: data,
      });
      setIsEditing(false);
    } catch (error) {
      console.error("Failed to update settings:", error);
    }
  };

  if (!settings) {
    return (
      <div className="bg-surface-elevated rounded-lg border border-border p-6">
        <h2 className="font-semibold text-text-primary">General Settings</h2>
        <p className="text-sm text-text-muted mt-2">
          Organization settings are not available yet.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-surface-elevated rounded-lg border border-border">
      <div className="p-6 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-accent/15 text-accent">
            <Building2 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-semibold text-text-primary">General Settings</h2>
            <p className="text-sm text-text-muted">Organization preferences</p>
          </div>
        </div>
        {!isEditing && (
          <button
            onClick={() => setIsEditing(true)}
            className="px-4 py-2 rounded-md text-sm font-medium text-accent hover:bg-accent/15 transition-colors"
          >
            Edit
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">
              Organization Name
            </label>
            <input
              {...register("name")}
              disabled={!isEditing}
              className={cn(
                "w-full px-3 py-2 rounded-md border bg-surface text-text-primary",
                "focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent",
                "disabled:bg-surface-overlay disabled:cursor-not-allowed",
                errors.name ? "border-status-error" : "border-border"
              )}
            />
            {errors.name && (
              <p className="text-xs text-status-error">{errors.name.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">
              Slug
            </label>
            <input
              value={currentSettings.general.slug}
              disabled
              className="w-full px-3 py-2 rounded-md border border-border bg-surface-overlay text-text-muted cursor-not-allowed"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">
              Timezone
            </label>
            <select
              {...register("timezone")}
              disabled={!isEditing}
              className="w-full px-3 py-2 rounded-md border border-border bg-surface text-text-primary focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent disabled:bg-surface-overlay disabled:cursor-not-allowed"
            >
              <option value="America/New_York">Eastern Time (ET)</option>
              <option value="America/Chicago">Central Time (CT)</option>
              <option value="America/Denver">Mountain Time (MT)</option>
              <option value="America/Los_Angeles">Pacific Time (PT)</option>
              <option value="UTC">UTC</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">
              Date Format
            </label>
            <select
              {...register("dateFormat")}
              disabled={!isEditing}
              className="w-full px-3 py-2 rounded-md border border-border bg-surface text-text-primary focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent disabled:bg-surface-overlay disabled:cursor-not-allowed"
            >
              <option value="MM/DD/YYYY">MM/DD/YYYY</option>
              <option value="DD/MM/YYYY">DD/MM/YYYY</option>
              <option value="YYYY-MM-DD">YYYY-MM-DD</option>
            </select>
          </div>
        </div>

        {isEditing && (
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={() => setIsEditing(false)}
              className="px-4 py-2 rounded-md text-text-secondary hover:text-text-primary hover:bg-surface-overlay transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 rounded-md bg-accent text-text-inverse hover:bg-accent-hover disabled:opacity-50 inline-flex items-center gap-2"
            >
              {isSubmitting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              Save Changes
            </button>
          </div>
        )}
      </form>
    </div>
  );
}

function SecuritySettingsSection() {
  const { data: settings } = useTenantSettings();
  const updateSettings = useUpdateTenantSettings();

  const currentSettings = settings ?? emptySettings;
  const [securitySettings, setSecuritySettings] = useState(currentSettings.security);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (settings) {
      setSecuritySettings(settings.security);
    }
  }, [settings]);

  const handleToggleMfa = async () => {
    const newValue = !securitySettings.mfaRequired;
    setSecuritySettings({ ...securitySettings, mfaRequired: newValue });
    setIsSaving(true);

    try {
      await updateSettings.mutateAsync({
        security: { mfaRequired: newValue },
      });
    } catch (error) {
      setSecuritySettings(securitySettings);
    } finally {
      setIsSaving(false);
    }
  };

  if (!settings) {
    return (
      <div className="bg-surface-elevated rounded-lg border border-border p-6">
        <h2 className="font-semibold text-text-primary">Security Settings</h2>
        <p className="text-sm text-text-muted mt-2">
          Security settings are not available yet.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-surface-elevated rounded-lg border border-border">
      <div className="p-6 border-b border-border flex items-center gap-3">
        <div className="p-2 rounded-lg bg-status-warning/15 text-status-warning">
          <Shield className="w-5 h-5" />
        </div>
        <div>
          <h2 className="font-semibold text-text-primary">Security Settings</h2>
          <p className="text-sm text-text-muted">Authentication and access control</p>
        </div>
      </div>

      <div className="divide-y divide-border">
        <div className="p-6 flex items-center justify-between">
          <div>
            <p className="font-medium text-text-primary">
              Require Two-Factor Authentication
            </p>
            <p className="text-sm text-text-muted">
              All team members must enable 2FA to access the platform
            </p>
          </div>
          <button
            onClick={handleToggleMfa}
            disabled={isSaving}
            className={cn(
              "relative w-11 h-6 rounded-full transition-colors",
              securitySettings.mfaRequired ? "bg-accent" : "bg-surface-overlay"
            )}
          >
            <span
              className={cn(
                "absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-surface shadow transition-transform",
                securitySettings.mfaRequired && "translate-x-5"
              )}
            />
          </button>
        </div>

        <div className="p-6 flex items-center justify-between">
          <div>
            <p className="font-medium text-text-primary">Session Timeout</p>
            <p className="text-sm text-text-muted">
              Automatically log out users after inactivity
            </p>
          </div>
          <span className="text-text-secondary">
            {securitySettings.sessionTimeout} minutes
          </span>
        </div>

        <div className="p-6">
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="font-medium text-text-primary">Allowed Email Domains</p>
              <p className="text-sm text-text-muted">
                Only emails from these domains can be invited
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {securitySettings.allowedDomains.map((domain) => (
              <span
                key={domain}
                className="px-3 py-1 rounded-full bg-surface-overlay text-sm text-text-secondary"
              >
                @{domain}
              </span>
            ))}
            {securitySettings.allowedDomains.length === 0 && (
              <span className="text-sm text-text-muted">
                Any email domain allowed
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function ApiKeysSection() {
  const { data: apiKeys, refetch } = useApiKeys();
  const createApiKey = useCreateApiKey();
  const deleteApiKey = useDeleteApiKey();
  const confirmDialog = useConfirmDialog();

  const [isCreating, setIsCreating] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [newKeySecret, setNewKeySecret] = useState<string | null>(null);
  const [showSecret, setShowSecret] = useState(false);

  const keys = apiKeys ?? [];

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const handleCreateKey = async () => {
    if (!newKeyName) return;

    try {
      const response = await createApiKey.mutateAsync({ name: newKeyName });
      setNewKeySecret(response.secretKey);
      setNewKeyName("");
      refetch();
    } catch (error) {
      console.error("Failed to create API key:", error);
    }
  };

  const handleDeleteKey = async (id: string) => {
    const key = keys.find((k) => k.id === id);
    const confirmed = await confirmDialog.confirm({
      title: "Delete API Key",
      description: `Are you sure you want to delete "${key?.name}"? This action cannot be undone and will immediately invalidate the key.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deleteApiKey.mutateAsync(id);
      } catch (error) {
        console.error("Failed to delete API key:", error);
      }
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="bg-surface-elevated rounded-lg border border-border">
      <div className="p-6 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-highlight/15 text-highlight">
            <Key className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-semibold text-text-primary">API Keys</h2>
            <p className="text-sm text-text-muted">
              Manage API access to your organization
            </p>
          </div>
        </div>
        <button
          onClick={() => setIsCreating(true)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-accent text-text-inverse hover:bg-accent-hover transition-colors"
        >
          <Plus className="w-4 h-4" />
          Create Key
        </button>
      </div>

      {/* New Key Created Banner */}
      {newKeySecret && (
        <div className="p-4 bg-status-warning/15 border-b border-status-warning/20">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-status-warning flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-medium text-text-primary mb-1">
                Save your API key now
              </p>
              <p className="text-sm text-text-muted mb-3">
                This is the only time you&apos;ll see this key. Copy it to a secure location.
              </p>
              <div className="flex items-center gap-2">
                <code className="flex-1 px-3 py-2 rounded-md bg-surface border border-border text-sm font-mono">
                  {showSecret ? newKeySecret : "••••••••••••••••••••••••••••••••"}
                </code>
                <button
                  onClick={() => setShowSecret(!showSecret)}
                  className="p-2 rounded-md hover:bg-surface-overlay transition-colors"
                >
                  {showSecret ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
                <button
                  onClick={() => copyToClipboard(newKeySecret)}
                  className="p-2 rounded-md hover:bg-surface-overlay transition-colors"
                >
                  <Copy className="w-4 h-4" />
                </button>
              </div>
              <button
                onClick={() => setNewKeySecret(null)}
                className="mt-3 text-sm text-accent hover:text-accent-hover"
              >
                I&apos;ve saved this key
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Key Form */}
      {isCreating && (
        <div className="p-6 border-b border-border">
          <div className="flex items-end gap-3">
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium text-text-secondary">
                Key Name
              </label>
              <input
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="e.g., Production API Key"
                className="w-full px-3 py-2 rounded-md border border-border bg-surface text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent"
              />
            </div>
            <button
              onClick={handleCreateKey}
              disabled={!newKeyName || createApiKey.isPending}
              className="px-4 py-2 rounded-md bg-accent text-text-inverse hover:bg-accent-hover disabled:opacity-50 transition-colors"
            >
              {createApiKey.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                "Create"
              )}
            </button>
            <button
              onClick={() => {
                setIsCreating(false);
                setNewKeyName("");
              }}
              className="px-4 py-2 rounded-md text-text-secondary hover:text-text-primary hover:bg-surface-overlay transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Keys List */}
      <div className="divide-y divide-border">
        {keys.map((key) => (
          <div
            key={key.id}
            className="p-6 flex items-center justify-between"
          >
            <div>
              <div className="flex items-center gap-2 mb-1">
                <p className="font-medium text-text-primary">{key.name}</p>
                <code className="px-2 py-0.5 rounded bg-surface-overlay text-xs font-mono text-text-muted">
                  {key.prefix}••••••••
                </code>
              </div>
              <p className="text-sm text-text-muted">
                Created {formatDate(key.createdAt)} by {key.createdBy}
                {key.lastUsedAt && ` • Last used ${formatDate(key.lastUsedAt)}`}
              </p>
            </div>
            <button
              onClick={() => handleDeleteKey(key.id)}
              className="p-2 rounded-md text-text-muted hover:text-status-error hover:bg-status-error/15 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>

      {confirmDialog.dialog}
    </div>
  );
}

function BrandingSettingsSection() {
  const { data: settings } = useTenantSettings();
  const updateSettings = useUpdateTenantSettings();
  const uploadLogo = useUploadTenantLogo();

  const currentSettings = settings ?? emptySettings;
  const [logoPreview, setLogoPreview] = useState<string | null>(
    currentSettings.branding.logoUrl ?? null
  );
  const [primaryColor, setPrimaryColor] = useState(
    currentSettings.branding.primaryColor || "#6366f1"
  );
  const [accentColor, setAccentColor] = useState(
    currentSettings.branding.accentColor || "#8b5cf6"
  );
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (settings) {
      if (settings.branding.logoUrl) setLogoPreview(settings.branding.logoUrl);
      if (settings.branding.primaryColor) setPrimaryColor(settings.branding.primaryColor);
      if (settings.branding.accentColor) setAccentColor(settings.branding.accentColor);
    }
  }, [settings]);

  const handleFileChange = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setLogoPreview(reader.result as string);
    };
    reader.readAsDataURL(file);

    // Upload
    try {
      await uploadLogo.mutateAsync({ file, type: "logo" });
    } catch (error) {
      console.error("Failed to upload logo:", error);
    }
  };

  const handleSaveColors = async () => {
    setIsSaving(true);
    try {
      await updateSettings.mutateAsync({
        branding: {
          primaryColor,
          accentColor,
        },
      });
    } catch (error) {
      console.error("Failed to save branding:", error);
    } finally {
      setIsSaving(false);
    }
  };

  if (!settings) {
    return (
      <div className="bg-surface-elevated rounded-lg border border-border p-6">
        <h2 className="font-semibold text-text-primary">Branding</h2>
        <p className="text-sm text-text-muted mt-2">
          Branding settings are not available yet.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-surface-elevated rounded-lg border border-border">
      <div className="p-6 border-b border-border flex items-center gap-3">
        <div className="p-2 rounded-lg bg-accent/15 text-accent">
          <ImageIcon className="w-5 h-5" />
        </div>
        <div>
          <h2 className="font-semibold text-text-primary">Branding</h2>
          <p className="text-sm text-text-muted">Customize your organization&apos;s appearance</p>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Logo Upload */}
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-3">
            Organization Logo
          </label>
          <div className="flex items-start gap-6">
            <div className="relative group">
              <div className="w-32 h-32 rounded-lg border-2 border-dashed border-border bg-surface-overlay flex items-center justify-center overflow-hidden">
                {logoPreview ? (
                  <Image
                    src={logoPreview}
                    alt="Logo preview"
                    width={128}
                    height={128}
                    className="max-w-full max-h-full object-contain"
                    unoptimized
                  />
                ) : (
                  <div className="text-center p-4">
                    <Upload className="w-8 h-8 mx-auto text-text-muted mb-2" />
                    <p className="text-xs text-text-muted">
                      Upload logo
                    </p>
                  </div>
                )}
              </div>
              <label className="absolute inset-0 flex items-center justify-center bg-overlay/50 rounded-lg opacity-0 group-hover:opacity-100 cursor-pointer transition-opacity">
                <Upload className="w-6 h-6 text-text-inverse" />
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  className="sr-only"
                />
              </label>
            </div>
            <div className="flex-1">
              <p className="text-sm text-text-secondary mb-2">
                Upload your organization&apos;s logo
              </p>
              <p className="text-xs text-text-muted">
                Recommended: PNG or JPG, at least 256x256 pixels, max 2MB
              </p>
              {uploadLogo.isPending && (
                <div className="flex items-center gap-2 mt-3 text-sm text-accent">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Uploading...
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Colors */}
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-3">
            Brand Colors
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-text-muted mb-2">
                Primary Color
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  value={primaryColor}
                  onChange={(e) => setPrimaryColor(e.target.value)}
                  className="w-10 h-10 rounded cursor-pointer border-0"
                />
                <input
                  type="text"
                  value={primaryColor}
                  onChange={(e) => setPrimaryColor(e.target.value)}
                  className="flex-1 px-3 py-2 bg-surface border border-border rounded-md text-text-primary font-mono text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs text-text-muted mb-2">
                Accent Color
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  value={accentColor}
                  onChange={(e) => setAccentColor(e.target.value)}
                  className="w-10 h-10 rounded cursor-pointer border-0"
                />
                <input
                  type="text"
                  value={accentColor}
                  onChange={(e) => setAccentColor(e.target.value)}
                  className="flex-1 px-3 py-2 bg-surface border border-border rounded-md text-text-primary font-mono text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end pt-4">
          <button
            onClick={handleSaveColors}
            disabled={isSaving}
            className="px-4 py-2 rounded-md bg-accent text-text-inverse hover:bg-accent-hover disabled:opacity-50 inline-flex items-center gap-2"
          >
            {isSaving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            Save Branding
          </button>
        </div>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        description="Manage your organization settings"
      />

      <div className="space-y-6">
        <GeneralSettingsSection />
        <BrandingSettingsSection />
        <SecuritySettingsSection />
        <ApiKeysSection />
      </div>
    </div>
  );
}
