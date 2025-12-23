import { redirect } from "next/navigation";
import { getServerSession } from "next-auth";
import type { ReactNode } from "react";

import { authOptions } from "@/lib/auth/config";
import { PortalShell } from "@/components/layout/portal-shell";
import { tenantPortalConfig } from "@/lib/config/tenant-portal";

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
  const session = await getServerSession(authOptions);

  if (!session) {
    redirect("/portal/login");
  }

  const roles = session.user?.roles ?? [];
  const hasTenantRole =
    roles.some((role) => TENANT_ROLES.has(role)) ||
    (session.user?.role ? TENANT_ROLES.has(session.user.role) : false);
  const isAdminRole =
    roles.some((role) => ADMIN_ROLES.has(role)) ||
    (session.user?.role ? ADMIN_ROLES.has(session.user.role) : false);
  const hasTenantContext = Boolean(session.user?.tenantId);
  const isPlatformAdmin = Boolean(session.user?.isPlatformAdmin) || isAdminRole;

  if (!isPlatformAdmin && !hasTenantContext && !hasTenantRole) {
    redirect("/portal/login?error=unauthorized");
  }

  return (
    <PortalShell session={session} config={tenantPortalConfig}>
      {children}
    </PortalShell>
  );
}
