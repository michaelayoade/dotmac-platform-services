"use client";

import { ReactNode } from "react";
import { usePermission } from "@/lib/hooks/use-permission";
import { Lock } from "lucide-react";

interface AdminSettingsLayoutProps {
  children: ReactNode;
}

export default function AdminSettingsLayout({ children }: AdminSettingsLayoutProps) {
  const { hasPermission, isLoading } = usePermission();
  const canReadSettings = hasPermission("settings.read");

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent" />
      </div>
    );
  }

  if (!canReadSettings) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <div className="p-4 rounded-full bg-danger-subtle">
          <Lock className="w-8 h-8 text-danger" />
        </div>
        <div className="text-center">
          <h2 className="text-lg font-semibold text-text-primary mb-2">
            Access Denied
          </h2>
          <p className="text-text-muted max-w-md">
            You do not have permission to access system settings.
            Please contact your administrator if you believe this is an error.
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
