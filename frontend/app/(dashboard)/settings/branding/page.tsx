"use client";

import { useState, useEffect, type ChangeEvent } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  ArrowLeft,
  Palette,
  Upload,
  Check,
  RefreshCw,
  ImageIcon,
  Type,
} from "lucide-react";
import { Button, useToast } from "@/lib/dotmac/core";
import { cn } from "@/lib/utils";
import {
  useCurrentTenant,
  useBranding,
  useUpdateBranding,
  useUploadBrandingLogo,
} from "@/lib/hooks/api/use-tenants";
import type { TenantBranding } from "@/lib/api/tenants";

export default function BrandingSettingsPage() {
  const { toast } = useToast();
  const { data: tenant } = useCurrentTenant();
  const { data: branding, isLoading } = useBranding(tenant?.id || "");
  const updateBranding = useUpdateBranding();
  const uploadLogo = useUploadBrandingLogo();

  const [formData, setFormData] = useState<Partial<TenantBranding>>({
    productName: "",
    tagline: "",
    primaryColor: "#00d4ff",
    secondaryColor: "#1a1a2e",
    accentColor: "#ffd700",
    supportEmail: "",
  });

  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const [faviconPreview, setFaviconPreview] = useState<string | null>(null);

  useEffect(() => {
    if (branding) {
      setFormData({
        productName: branding.productName || "",
        tagline: branding.tagline || "",
        primaryColor: branding.primaryColor || "#00d4ff",
        secondaryColor: branding.secondaryColor || "#1a1a2e",
        accentColor: branding.accentColor || "#ffd700",
        supportEmail: branding.supportEmail || "",
      });
      if (branding.logoUrl) setLogoPreview(branding.logoUrl);
      if (branding.faviconUrl) setFaviconPreview(branding.faviconUrl);
    }
  }, [branding]);

  const handleInputChange = (field: keyof TenantBranding, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleFileChange = async (
    e: ChangeEvent<HTMLInputElement>,
    type: "logo" | "favicon"
  ) => {
    const file = e.target.files?.[0];
    if (!file || !tenant?.id) return;

    // Preview
    const reader = new FileReader();
    reader.onloadend = () => {
      if (type === "logo") {
        setLogoPreview(reader.result as string);
      } else {
        setFaviconPreview(reader.result as string);
      }
    };
    reader.readAsDataURL(file);

    // Upload
    try {
      const result = await uploadLogo.mutateAsync({
        tenantId: tenant.id,
        file,
        type,
      });

      setFormData((prev) => ({
        ...prev,
        [type === "logo" ? "logoUrl" : "faviconUrl"]: result.url,
      }));

      toast({
        title: "Image uploaded",
        description: `${type === "logo" ? "Logo" : "Favicon"} has been uploaded.`,
        variant: "success",
      });
    } catch {
      toast({
        title: "Upload failed",
        description: `Failed to upload ${type}.`,
        variant: "error",
      });
    }
  };

  const handleSave = async () => {
    if (!tenant?.id) return;

    try {
      await updateBranding.mutateAsync({
        tenantId: tenant.id,
        data: formData,
      });

      toast({
        title: "Branding updated",
        description: "Your branding settings have been saved.",
        variant: "success",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to update branding settings.",
        variant: "error",
      });
    }
  };

  const handleReset = () => {
    if (branding) {
      setFormData({
        productName: branding.productName || "",
        tagline: branding.tagline || "",
        primaryColor: branding.primaryColor || "#00d4ff",
        secondaryColor: branding.secondaryColor || "#1a1a2e",
        accentColor: branding.accentColor || "#ffd700",
        supportEmail: branding.supportEmail || "",
      });
      if (branding.logoUrl) setLogoPreview(branding.logoUrl);
      if (branding.faviconUrl) setFaviconPreview(branding.faviconUrl);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        href="/settings"
        className="inline-flex items-center gap-2 text-sm text-text-muted hover:text-text-secondary transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Settings
      </Link>

      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary">
            Branding
          </h1>
          <p className="text-text-muted mt-1">
            Customize the look and feel of your platform
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={handleReset}>
            Reset
          </Button>
          <Button
            onClick={handleSave}
            disabled={updateBranding.isPending}
            className="shadow-glow-sm"
          >
            {updateBranding.isPending ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Check className="w-4 h-4 mr-2" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Settings Column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Logo Upload */}
          <div className="card p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
                <ImageIcon className="w-5 h-5 text-accent" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-text-primary">
                  Logos
                </h2>
                <p className="text-xs text-text-muted">
                  Upload your brand logos
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Primary Logo */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Primary Logo
                </label>
                <div className="relative group">
                  <div className="w-full h-32 rounded-lg border-2 border-dashed border-border bg-surface-overlay flex items-center justify-center overflow-hidden">
                    {logoPreview ? (
                      <Image
                        src={logoPreview}
                        alt="Logo preview"
                        width={200}
                        height={100}
                        className="max-w-full max-h-full object-contain"
                        unoptimized
                      />
                    ) : (
                      <div className="text-center">
                        <Upload className="w-8 h-8 mx-auto text-text-muted mb-2" />
                        <p className="text-xs text-text-muted">
                          PNG, JPG up to 2MB
                        </p>
                      </div>
                    )}
                  </div>
                  <label className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-lg opacity-0 group-hover:opacity-100 cursor-pointer transition-opacity">
                    <Upload className="w-6 h-6 text-white" />
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => handleFileChange(e, "logo")}
                      className="sr-only"
                    />
                  </label>
                </div>
              </div>

              {/* Favicon */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Favicon
                </label>
                <div className="relative group">
                  <div className="w-full h-32 rounded-lg border-2 border-dashed border-border bg-surface-overlay flex items-center justify-center overflow-hidden">
                    {faviconPreview ? (
                      <Image
                        src={faviconPreview}
                        alt="Favicon preview"
                        width={64}
                        height={64}
                        className="w-16 h-16 object-contain"
                        unoptimized
                      />
                    ) : (
                      <div className="text-center">
                        <Upload className="w-8 h-8 mx-auto text-text-muted mb-2" />
                        <p className="text-xs text-text-muted">
                          32x32 or 64x64 PNG
                        </p>
                      </div>
                    )}
                  </div>
                  <label className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-lg opacity-0 group-hover:opacity-100 cursor-pointer transition-opacity">
                    <Upload className="w-6 h-6 text-white" />
                    <input
                      type="file"
                      accept="image/png"
                      onChange={(e) => handleFileChange(e, "favicon")}
                      className="sr-only"
                    />
                  </label>
                </div>
              </div>
            </div>
          </div>

          {/* Colors */}
          <div className="card p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
                <Palette className="w-5 h-5 text-accent" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-text-primary">
                  Colors
                </h2>
                <p className="text-xs text-text-muted">
                  Define your brand colors
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Primary Color
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={formData.primaryColor}
                    onChange={(e) =>
                      handleInputChange("primaryColor", e.target.value)
                    }
                    className="w-10 h-10 rounded cursor-pointer border-0"
                  />
                  <input
                    type="text"
                    value={formData.primaryColor}
                    onChange={(e) =>
                      handleInputChange("primaryColor", e.target.value)
                    }
                    className="flex-1 px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary font-mono text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Secondary Color
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={formData.secondaryColor}
                    onChange={(e) =>
                      handleInputChange("secondaryColor", e.target.value)
                    }
                    className="w-10 h-10 rounded cursor-pointer border-0"
                  />
                  <input
                    type="text"
                    value={formData.secondaryColor}
                    onChange={(e) =>
                      handleInputChange("secondaryColor", e.target.value)
                    }
                    className="flex-1 px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary font-mono text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Accent Color
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={formData.accentColor}
                    onChange={(e) =>
                      handleInputChange("accentColor", e.target.value)
                    }
                    className="w-10 h-10 rounded cursor-pointer border-0"
                  />
                  <input
                    type="text"
                    value={formData.accentColor}
                    onChange={(e) =>
                      handleInputChange("accentColor", e.target.value)
                    }
                    className="flex-1 px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary font-mono text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Text */}
          <div className="card p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
                <Type className="w-5 h-5 text-accent" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-text-primary">
                  Text & Labels
                </h2>
                <p className="text-xs text-text-muted">
                  Customize text throughout the platform
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Product Name
                </label>
                <input
                  type="text"
                  value={formData.productName}
                  onChange={(e) =>
                    handleInputChange("productName", e.target.value)
                  }
                  placeholder="Your Product Name"
                  className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Tagline
                </label>
                <input
                  type="text"
                  value={formData.tagline}
                  onChange={(e) => handleInputChange("tagline", e.target.value)}
                  placeholder="Your product tagline"
                  className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Support Email
                </label>
                <input
                  type="email"
                  value={formData.supportEmail}
                  onChange={(e) =>
                    handleInputChange("supportEmail", e.target.value)
                  }
                  placeholder="support@yourcompany.com"
                  className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Preview Column */}
        <div className="lg:col-span-1">
          <div className="card p-6 sticky top-6">
            <h3 className="text-sm font-semibold text-text-primary mb-4">
              Preview
            </h3>

            {/* Mini App Preview */}
            <div
              className="rounded-lg overflow-hidden border border-border"
              style={{
                backgroundColor: formData.secondaryColor,
              }}
            >
              {/* Header */}
              <div
                className="p-3 flex items-center gap-2"
                style={{ borderBottom: "1px solid rgba(255,255,255,0.1)" }}
              >
                {logoPreview ? (
                  <Image
                    src={logoPreview}
                    alt="Logo"
                    width={24}
                    height={24}
                    className="w-6 h-6 object-contain"
                    unoptimized
                  />
                ) : (
                  <div
                    className="w-6 h-6 rounded"
                    style={{ backgroundColor: formData.primaryColor }}
                  />
                )}
                <span className="text-white text-sm font-medium">
                  {formData.productName || "Your Product"}
                </span>
              </div>

              {/* Content */}
              <div className="p-4 space-y-3">
                <div
                  className="h-2 rounded"
                  style={{
                    backgroundColor: formData.primaryColor,
                    width: "60%",
                  }}
                />
                <div
                  className="h-2 rounded opacity-50"
                  style={{
                    backgroundColor: formData.primaryColor,
                    width: "80%",
                  }}
                />
                <div
                  className="h-2 rounded opacity-30"
                  style={{
                    backgroundColor: formData.primaryColor,
                    width: "40%",
                  }}
                />

                <button
                  className="mt-4 px-3 py-1.5 rounded text-xs font-medium text-white"
                  style={{ backgroundColor: formData.accentColor }}
                >
                  Action Button
                </button>
              </div>
            </div>

            {/* Color Swatches */}
            <div className="mt-4 flex items-center gap-2">
              <div
                className="w-8 h-8 rounded-full border-2 border-white/20"
                style={{ backgroundColor: formData.primaryColor }}
                title="Primary"
              />
              <div
                className="w-8 h-8 rounded-full border-2 border-white/20"
                style={{ backgroundColor: formData.secondaryColor }}
                title="Secondary"
              />
              <div
                className="w-8 h-8 rounded-full border-2 border-white/20"
                style={{ backgroundColor: formData.accentColor }}
                title="Accent"
              />
            </div>

            {formData.tagline && (
              <p className="mt-4 text-xs text-text-muted italic">
                &ldquo;{formData.tagline}&rdquo;
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
