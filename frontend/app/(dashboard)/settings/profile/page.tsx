"use client";

import { useState, type ChangeEvent } from "react";
import Link from "next/link";
import { useSession } from "next-auth/react";
import { ArrowLeft, Camera, Check } from "lucide-react";
import { Form, FormField, FormSubmitButton, FormResetButton, FormActions } from "@dotmac/forms";
import { Input, Button, useToast } from "@dotmac/core";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { cn } from "@/lib/utils";

const profileSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Please enter a valid email"),
  phone: z.string().optional(),
  timezone: z.string(),
  language: z.string(),
  bio: z.string().max(500, "Bio must be less than 500 characters").optional(),
});

type ProfileFormData = z.infer<typeof profileSchema>;

const timezones = [
  { value: "America/New_York", label: "Eastern Time (ET)" },
  { value: "America/Chicago", label: "Central Time (CT)" },
  { value: "America/Denver", label: "Mountain Time (MT)" },
  { value: "America/Los_Angeles", label: "Pacific Time (PT)" },
  { value: "Europe/London", label: "Greenwich Mean Time (GMT)" },
  { value: "Europe/Paris", label: "Central European Time (CET)" },
  { value: "Asia/Tokyo", label: "Japan Standard Time (JST)" },
];

const languages = [
  { value: "en", label: "English" },
  { value: "es", label: "Español" },
  { value: "fr", label: "Français" },
  { value: "de", label: "Deutsch" },
  { value: "ja", label: "日本語" },
];

export default function ProfileSettingsPage() {
  const { data: session } = useSession();
  const { toast } = useToast();
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);

  const form = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      name: session?.user?.name || "",
      email: session?.user?.email || "",
      phone: "",
      timezone: "America/New_York",
      language: "en",
      bio: "",
    },
  });

  const onSubmit = async (data: ProfileFormData) => {
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));

    toast({
      title: "Profile updated",
      description: "Your profile has been saved successfully.",
      variant: "success",
    });
  };

  const handleAvatarChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setAvatarPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="max-w-2xl space-y-6">
      {/* Back link */}
      <Link
        href="/settings"
        className="inline-flex items-center gap-2 text-sm text-text-muted hover:text-text-secondary transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Settings
      </Link>

      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-semibold text-text-primary">Profile Settings</h1>
        <p className="text-text-muted mt-1">
          Manage your personal information and preferences
        </p>
      </div>

      {/* Avatar Section */}
      <div className="card p-6">
        <h2 className="text-sm font-semibold text-text-primary mb-4">Profile Photo</h2>
        <div className="flex items-center gap-6">
          <div className="relative group">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-accent to-highlight flex items-center justify-center text-2xl font-semibold text-text-inverse overflow-hidden">
              {avatarPreview ? (
                <img
                  src={avatarPreview}
                  alt="Avatar preview"
                  className="w-full h-full object-cover"
                />
              ) : (
                session?.user?.name?.charAt(0).toUpperCase() || "U"
              )}
            </div>
            <label className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-full opacity-0 group-hover:opacity-100 cursor-pointer transition-opacity">
              <Camera className="w-5 h-5 text-white" />
              <input
                type="file"
                accept="image/*"
                onChange={handleAvatarChange}
                className="sr-only"
              />
            </label>
          </div>
          <div>
            <p className="text-sm text-text-primary font-medium">Upload a new photo</p>
            <p className="text-xs text-text-muted mt-1">
              JPG, PNG or GIF. Max size 2MB.
            </p>
          </div>
        </div>
      </div>

      {/* Profile Form */}
      <div className="card p-6">
        <h2 className="text-sm font-semibold text-text-primary mb-4">Personal Information</h2>

        <Form form={form} onSubmit={onSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField name="name" label="Full Name" required>
              <Input
                {...form.register("name")}
                placeholder="John Doe"
              />
            </FormField>

            <FormField name="email" label="Email Address" required>
              <Input
                {...form.register("email")}
                type="email"
                placeholder="john@example.com"
              />
            </FormField>
          </div>

          <FormField name="phone" label="Phone Number">
            <Input
              {...form.register("phone")}
              type="tel"
              placeholder="+1 (555) 123-4567"
            />
          </FormField>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField name="timezone" label="Timezone">
              <select
                {...form.register("timezone")}
                className="w-full h-10 px-3 rounded-md bg-surface-overlay border border-border text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
              >
                {timezones.map((tz) => (
                  <option key={tz.value} value={tz.value}>
                    {tz.label}
                  </option>
                ))}
              </select>
            </FormField>

            <FormField name="language" label="Language">
              <select
                {...form.register("language")}
                className="w-full h-10 px-3 rounded-md bg-surface-overlay border border-border text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
              >
                {languages.map((lang) => (
                  <option key={lang.value} value={lang.value}>
                    {lang.label}
                  </option>
                ))}
              </select>
            </FormField>
          </div>

          <FormField name="bio" label="Bio" description="A short description about yourself">
            <textarea
              {...form.register("bio")}
              rows={3}
              placeholder="Tell us a bit about yourself..."
              className="w-full px-3 py-2 rounded-md bg-surface-overlay border border-border text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent resize-none"
            />
          </FormField>

          <FormActions>
            <FormResetButton>Cancel</FormResetButton>
            <FormSubmitButton loadingText="Saving...">
              <Check className="w-4 h-4 mr-2" />
              Save Changes
            </FormSubmitButton>
          </FormActions>
        </Form>
      </div>

      {/* Danger Zone */}
      <div className="card p-6 border-status-error/30">
        <h2 className="text-sm font-semibold text-status-error mb-2">Danger Zone</h2>
        <p className="text-sm text-text-muted mb-4">
          Once you delete your account, there is no going back. Please be certain.
        </p>
        <Button variant="destructive" size="sm">
          Delete Account
        </Button>
      </div>
    </div>
  );
}
