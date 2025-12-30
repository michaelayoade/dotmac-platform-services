import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { PortalShellWithConfig } from "@/components/layout/portal-shell";
import { getCurrentUserFromRequest } from "@/lib/auth/server";

const ADMIN_ROLES = new Set(["admin", "platform_admin", "super_admin"]);

export default async function PartnerPrivateLayout({
  children,
}: {
  children: ReactNode;
}) {
  const user = await getCurrentUserFromRequest();

  if (!user) {
    redirect("/partner/login");
  }

  const roles = user.roles ?? [];
  const permissions = user.permissions ?? [];
  const hasPartnerRole =
    roles.some((role) => role.startsWith("partner_")) ||
    (user.roles?.[0] ? user.roles[0].startsWith("partner_") : false);
  const isAdminRole =
    roles.some((role) => ADMIN_ROLES.has(role)) ||
    (user.roles?.[0] ? ADMIN_ROLES.has(user.roles[0]) : false);
  const hasPartnerPermission = permissions.some((permission) =>
    permission.startsWith("partner.")
  );
  const hasPartnerContext = Boolean(user.partnerId);
  const isPlatformAdmin = Boolean(user.isPlatformAdmin) || isAdminRole;

  if (!isPlatformAdmin && !hasPartnerContext && !hasPartnerRole && !hasPartnerPermission) {
    redirect("/partner/login?error=unauthorized");
  }

  return (
    <PortalShellWithConfig user={user} configKey="partner">
      {children}
    </PortalShellWithConfig>
  );
}
