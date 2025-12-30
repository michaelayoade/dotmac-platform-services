"use client";

import { useState, useEffect, type ChangeEvent } from "react";
import Image from "next/image";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
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
import { brandingFormSchema, type BrandingFormData } from "@/lib/schemas/branding";
import type { TenantBranding } from "@/lib/api/tenants";

export default function BrandingSettingsPage() {
  const { toast } = useToast();
  const { data: tenant } = useCurrentTenant();
  const { data: branding, isLoading } = useBranding(tenant?.id || "");
  const updateBranding = useUpdateBranding();
  const uploadLogo = useUploadBrandingLogo();

  const {
    register,
    handleSubmit,
    watch,
    reset,
    setValue,
    formState: { errors },
  } = useForm<BrandingFormData>({
    resolver: zodResolver(brandingFormSchema),
    defaultValues: {
      productName: "",
      tagline: "",
      primaryColor: "",
      secondaryColor: "",
      accentColor: "",
      supportEmail: "",
    },
  });

  const formData = watch();
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const [faviconPreview, setFaviconPreview] = useState<string | null>(null);
  const [themeDefaults, setThemeDefaults] = useState({
    primaryColor: "",
    secondaryColor: "",
    accentColor: "",
  });

  useEffect(() => {
    const hslToHex = (h: number, s: number, l: number) => {
      const hNorm = h / 360;
      const sNorm = s / 100;
      const lNorm = l / 100;
      const hueToRgb = (p: number, q: number, t: number) => {
        let value = t;
        if (value < 0) value += 1;
        if (value > 1) value -= 1;
        if (value < 1 / 6) return p + (q - p) * 6 * value;
        if (value < 1 / 2) return q;
        if (value < 2 / 3) return p + (q - p) * (2 / 3 - value) * 6;
        return p;
      };

      let r = lNorm;
      let g = lNorm;
      let b = lNorm;

      if (sNorm !== 0) {
        const q = lNorm < 0.5 ? lNorm * (1 + sNorm) : lNorm + sNorm - lNorm * sNorm;
        const p = 2 * lNorm - q;
        r = hueToRgb(p, q, hNorm + 1 / 3);
        g = hueToRgb(p, q, hNorm);
        b = hueToRgb(p, q, hNorm - 1 / 3);
      }

      const toHex = (value: number) => {
        const hex = Math.round(value * 255).toString(16).padStart(2, "0");
        return hex;
      };

      return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
    };

    const cssVarToHex = (value: string) => {
      const cleaned = value.split("/")[0]?.trim();
      if (!cleaned) return "";
      const parts = cleaned.split(/\s+/);
      if (parts.length < 3) return "";
      const h = Number(parts[0]);
      const s = Number(parts[1].replace("%", ""));
      const l = Number(parts[2].replace("%", ""));
      if (Number.isNaN(h) || Number.isNaN(s) || Number.isNaN(l)) return "";
      return hslToHex(h, s, l);
    };

    const computed = getComputedStyle(document.documentElement);
    const primary = cssVarToHex(computed.getPropertyValue("--color-accent"));
    const secondary = cssVarToHex(computed.getPropertyValue("--color-surface"));
    const accent = cssVarToHex(computed.getPropertyValue("--color-highlight"));

    setThemeDefaults({
      primaryColor: primary,
      secondaryColor: secondary,
      accentColor: accent,
    });
  }, []);

  const previewColors = {
    primaryColor: formData.primaryColor || themeDefaults.primaryColor,
    secondaryColor: formData.secondaryColor || themeDefaults.secondaryColor,
    accentColor: formData.accentColor || themeDefaults.accentColor,
  };

  useEffect(() => {
    if (branding) {
      reset({
        productName: branding.productName || "",
        tagline: branding.tagline || "",
        primaryColor: branding.primaryColor || "",
        secondaryColor: branding.secondaryColor || "",
        accentColor: branding.accentColor || "",
        supportEmail: branding.supportEmail || "",
      });
      if (branding.logoUrl) setLogoPreview(branding.logoUrl);
      if (branding.faviconUrl) setFaviconPreview(branding.faviconUrl);
    }
  }, [branding, reset]);

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

      setValue(type === "logo" ? "logoUrl" : "faviconUrl", result.url);

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

  const onSubmit = async (data: BrandingFormData) => {
    if (!tenant?.id) return;

    try {
      await updateBranding.mutateAsync({
        tenantId: tenant.id,
        data,
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
      reset({
        productName: branding.productName || "",
        tagline: branding.tagline || "",
        primaryColor: branding.primaryColor || "",
        secondaryColor: branding.secondaryColor || "",
        accentColor: branding.accentColor || "",
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
            onClick={handleSubmit(onSubmit)}
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
                  <label className="absolute inset-0 flex items-center justify-center bg-overlay/50 rounded-lg opacity-0 group-hover:opacity-100 cursor-pointer transition-opacity">
                    <Upload className="w-6 h-6 text-text-inverse" />
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
                  <label className="absolute inset-0 flex items-center justify-center bg-overlay/50 rounded-lg opacity-0 group-hover:opacity-100 cursor-pointer transition-opacity">
                    <Upload className="w-6 h-6 text-text-inverse" />
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
                    value={previewColors.primaryColor}
                    onChange={(e) => setValue("primaryColor", e.target.value)}
                    className="w-10 h-10 rounded cursor-pointer border-0"
                  />
                  <input
                    type="text"
                    {...register("primaryColor")}
                    className={cn(
                      "flex-1 px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary font-mono text-sm focus:outline-none focus:ring-2 focus:ring-accent",
                      errors.primaryColor && "border-status-error"
                    )}
                  />
                </div>
                {errors.primaryColor && (
                  <p className="text-xs text-status-error mt-1">{errors.primaryColor.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Secondary Color
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={previewColors.secondaryColor}
                    onChange={(e) => setValue("secondaryColor", e.target.value)}
                    className="w-10 h-10 rounded cursor-pointer border-0"
                  />
                  <input
                    type="text"
                    {...register("secondaryColor")}
                    className={cn(
                      "flex-1 px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary font-mono text-sm focus:outline-none focus:ring-2 focus:ring-accent",
                      errors.secondaryColor && "border-status-error"
                    )}
                  />
                </div>
                {errors.secondaryColor && (
                  <p className="text-xs text-status-error mt-1">{errors.secondaryColor.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Accent Color
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={previewColors.accentColor}
                    onChange={(e) => setValue("accentColor", e.target.value)}
                    className="w-10 h-10 rounded cursor-pointer border-0"
                  />
                  <input
                    type="text"
                    {...register("accentColor")}
                    className={cn(
                      "flex-1 px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary font-mono text-sm focus:outline-none focus:ring-2 focus:ring-accent",
                      errors.accentColor && "border-status-error"
                    )}
                  />
                </div>
                {errors.accentColor && (
                  <p className="text-xs text-status-error mt-1">{errors.accentColor.message}</p>
                )}
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
                  {...register("productName")}
                  placeholder="Your Product Name"
                  className={cn(
                    "w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent",
                    errors.productName && "border-status-error"
                  )}
                />
                {errors.productName && (
                  <p className="text-xs text-status-error mt-1">{errors.productName.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Tagline
                </label>
                <input
                  type="text"
                  {...register("tagline")}
                  placeholder="Your product tagline"
                  className={cn(
                    "w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent",
                    errors.tagline && "border-status-error"
                  )}
                />
                {errors.tagline && (
                  <p className="text-xs text-status-error mt-1">{errors.tagline.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Support Email
                </label>
                <input
                  type="email"
                  {...register("supportEmail")}
                  placeholder="support@yourcompany.com"
                  className={cn(
                    "w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent",
                    errors.supportEmail && "border-status-error"
                  )}
                />
                {errors.supportEmail && (
                  <p className="text-xs text-status-error mt-1">{errors.supportEmail.message}</p>
                )}
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
                backgroundColor: previewColors.secondaryColor,
              }}
            >
              {/* Header */}
              <div
                className="p-3 flex items-center gap-2 border-b border-border"
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
                    style={{ backgroundColor: previewColors.primaryColor }}
                  />
                )}
                <span className="text-text-inverse text-sm font-medium">
                  {formData.productName || "Your Product"}
                </span>
              </div>

              {/* Content */}
              <div className="p-4 space-y-3">
                <div
                  className="h-2 rounded"
                  style={{
                    backgroundColor: previewColors.primaryColor,
                    width: "60%",
                  }}
                />
                <div
                  className="h-2 rounded opacity-50"
                  style={{
                    backgroundColor: previewColors.primaryColor,
                    width: "80%",
                  }}
                />
                <div
                  className="h-2 rounded opacity-30"
                  style={{
                    backgroundColor: previewColors.primaryColor,
                    width: "40%",
                  }}
                />

                <button
                  className="mt-4 px-3 py-1.5 rounded text-xs font-medium text-text-inverse"
                  style={{ backgroundColor: previewColors.accentColor }}
                >
                  Action Button
                </button>
              </div>
            </div>

            {/* Color Swatches */}
            <div className="mt-4 flex items-center gap-2">
              <div
                className="w-8 h-8 rounded-full border-2 border-text-inverse/20"
                style={{ backgroundColor: previewColors.primaryColor }}
                title="Primary"
              />
              <div
                className="w-8 h-8 rounded-full border-2 border-text-inverse/20"
                style={{ backgroundColor: previewColors.secondaryColor }}
                title="Secondary"
              />
              <div
                className="w-8 h-8 rounded-full border-2 border-text-inverse/20"
                style={{ backgroundColor: previewColors.accentColor }}
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
