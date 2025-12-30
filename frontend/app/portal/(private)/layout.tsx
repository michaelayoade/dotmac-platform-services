import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { PortalShellWithConfig } from "@/components/layout/portal-shell";
import { getCurrentUserFromRequest } from "@/lib/auth/server";

const TENANT_ROLES = new Set([
  "tenant_admin",
  "manager",
  "operator",
  "viewer",
  "member",
]);
const ADMIN_ROLES = new Set(["admin", "platform_admin", "super_admin"]);

export default async function TenantPrivateLayout({
  children,
}: {
  children: ReactNode;
}) {
  const user = await getCurrentUserFromRequest();

  if (!user) {
    redirect("/portal/login");
  }

  const roles = user.roles ?? [];
  const hasTenantRole =
    roles.some((role) => TENANT_ROLES.has(role)) ||
    (user.roles?.[0] ? TENANT_ROLES.has(user.roles[0]) : false);
  const isAdminRole =
    roles.some((role) => ADMIN_ROLES.has(role)) ||
    (user.roles?.[0] ? ADMIN_ROLES.has(user.roles[0]) : false);
  const hasTenantContext = Boolean(user.tenantId);
  const isPlatformAdmin = Boolean(user.isPlatformAdmin) || isAdminRole;

  if (!isPlatformAdmin && !hasTenantContext && !hasTenantRole) {
    redirect("/portal/login?error=unauthorized");
  }

  return (
    <PortalShellWithConfig user={user} configKey="tenant">
      {children}
    </PortalShellWithConfig>
  );
}
