"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, User, Mail, Shield, Send } from "lucide-react";
import { Button, Card, Input, Select } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { createUserSchema, userRoles, type CreateUserData } from "@/lib/schemas/users";
import { useCreateUser } from "@/lib/hooks/api/use-users";

export default function NewUserPage() {
  const router = useRouter();
  const { toast } = useToast();
  const createUser = useCreateUser();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setValue,
    watch,
  } = useForm<CreateUserData>({
    resolver: zodResolver(createUserSchema),
    mode: "onBlur",
    defaultValues: {
      email: "",
      name: "",
      role: "member",
      sendInvite: true,
    },
  });

  const selectedRole = watch("role");
  const sendInvite = watch("sendInvite");

  const onSubmit = async (data: CreateUserData) => {
    try {
      const result = await createUser.mutateAsync({
        email: data.email,
        name: data.name,
        role: data.role,
        sendInvite: data.sendInvite,
      });

      toast({
        title: "User created",
        description: data.sendInvite
          ? `An invitation has been sent to ${data.email}.`
          : `${data.name} has been added successfully.`,
      });

      router.push(`/users/${result.id}`);
    } catch {
      toast({
        title: "Error",
        description: "Failed to create user. Please try again.",
        variant: "error",
      });
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="Invite User"
        breadcrumbs={[{ label: "Users", href: "/users" }, { label: "Invite User" }]}
        actions={
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        }
      />

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* User Information */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <User className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">User Information</h3>
              <p className="text-sm text-text-muted">Basic details for the new user</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-text-primary mb-1.5">
                <Mail className="w-4 h-4 inline mr-1" aria-hidden="true" />
                Email Address <span className="text-status-error" aria-hidden="true">*</span>
              </label>
              <Input
                {...register("email")}
                id="email"
                type="email"
                placeholder="user@example.com"
                aria-required="true"
                aria-invalid={!!errors.email}
                aria-describedby={errors.email ? "email-error" : undefined}
                className={cn(errors.email && "border-status-error")}
              />
              {errors.email && (
                <p id="email-error" className="text-xs text-status-error mt-1" role="alert">{errors.email.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="name" className="block text-sm font-medium text-text-primary mb-1.5">
                Full Name <span className="text-status-error" aria-hidden="true">*</span>
              </label>
              <Input
                {...register("name")}
                id="name"
                placeholder="John Doe"
                aria-required="true"
                aria-invalid={!!errors.name}
                aria-describedby={errors.name ? "name-error" : undefined}
                className={cn(errors.name && "border-status-error")}
              />
              {errors.name && (
                <p id="name-error" className="text-xs text-status-error mt-1" role="alert">{errors.name.message}</p>
              )}
            </div>
          </div>
        </Card>

        {/* Role & Permissions */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
              <Shield className="w-5 h-5 text-highlight" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Role & Permissions</h3>
              <p className="text-sm text-text-muted">Assign access level to this user</p>
            </div>
          </div>

          <div>
            <label id="role-label" className="block text-sm font-medium text-text-primary mb-1.5">
              Role <span className="text-status-error" aria-hidden="true">*</span>
            </label>
            <Select
              value={selectedRole}
              onValueChange={(value) => setValue("role", value as CreateUserData["role"])}
              options={userRoles.map((r) => ({ value: r.value, label: r.label }))}
              placeholder="Select role"
              aria-labelledby="role-label"
              aria-required="true"
            />
            {errors.role && (
              <p className="text-xs text-status-error mt-1" role="alert">{errors.role.message}</p>
            )}

            <div className="mt-4 p-4 rounded-lg bg-surface-secondary border border-border-default">
              <h4 className="text-sm font-medium text-text-primary mb-2">Role Permissions</h4>
              <div className="text-xs text-text-muted space-y-1">
                {selectedRole === "owner" && (
                  <>
                    <p>Full access to all features and settings</p>
                    <p>Can manage billing, users, and organization settings</p>
                    <p>Can delete the organization</p>
                  </>
                )}
                {selectedRole === "admin" && (
                  <>
                    <p>Full access to all features</p>
                    <p>Can manage users and most settings</p>
                    <p>Cannot access billing or delete organization</p>
                  </>
                )}
                {selectedRole === "member" && (
                  <>
                    <p>Can view and edit most resources</p>
                    <p>Can create and manage own content</p>
                    <p>Cannot manage users or settings</p>
                  </>
                )}
                {selectedRole === "viewer" && (
                  <>
                    <p>Read-only access to resources</p>
                    <p>Cannot create, edit, or delete content</p>
                    <p>Can view reports and dashboards</p>
                  </>
                )}
              </div>
            </div>
          </div>
        </Card>

        {/* Invitation Options */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
              <Send className="w-5 h-5 text-status-info" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Invitation</h3>
              <p className="text-sm text-text-muted">How to notify the user</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <input
              type="checkbox"
              id="sendInvite"
              checked={sendInvite}
              onChange={(e) => setValue("sendInvite", e.target.checked)}
              className="rounded mt-0.5"
            />
            <label htmlFor="sendInvite" className="cursor-pointer">
              <span className="text-sm font-medium text-text-primary">Send invitation email</span>
              <p className="text-xs text-text-muted">
                The user will receive an email with instructions to set up their account and
                password.
              </p>
            </label>
          </div>
        </Card>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-4">
          <Button type="button" variant="ghost" onClick={() => router.back()}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting || createUser.isPending}>
            {isSubmitting || createUser.isPending ? "Creating..." : "Invite User"}
          </Button>
        </div>
      </form>
    </div>
  );
}
